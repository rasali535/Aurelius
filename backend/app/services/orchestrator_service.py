import uuid
import asyncio
from app.utils import generate_id, utc_now
from app.services.validator_service import VALIDATORS, run_validator
from app.services.circle_service import circle_service
from app.services.x402_service import x402_service

def create_draft_response(prompt: str) -> str:
    return f"Draft response for prompt: {prompt}"

def final_status_from_results(results):
    statuses = [r["status"] for r in results]
    if "failed" in statuses:
        return "blocked"
    if "warning" in statuses:
        return "review_required"
    return "approved"

async def get_or_create_requester_wallet(db):
    """Ensures the Requester Agent has a wallet."""
    existing = await db.config.find_one({"_id": "requester_wallet"})
    if existing:
        return existing
    
    # Create a new wallet set and wallet for the requester
    wallet_set = await circle_service.create_wallet_set("Aurelius Requester")
    wallets = await circle_service.create_wallets(wallet_set["id"], blockchain="ARC-TESTNET")
    wallet_doc = {
        "_id": "requester_wallet",
        "wallet_id": wallets[0]["id"],
        "wallet_address": wallets[0]["address"],
    }
    await db.config.insert_one(wallet_doc)
    return wallet_doc

async def process_prompt_run(db, prompt: str):
    run_id = generate_id("run")
    draft_response = create_draft_response(prompt)
    requester_wallet = await get_or_create_requester_wallet(db)

    prompt_doc = {
        "_id": run_id,
        "input_prompt": prompt,
        "draft_response": draft_response,
        "final_status": "pending",
        "total_cost_usdc": 0.0,
        "validator_count": 0,
        "created_at": utc_now(),
    }
    await db.prompt_runs.insert_one(prompt_doc)

    validation_results = []
    total_cost = 0.0

    validation_tasks = []
    
    async def run_single_validator(validator):
        validator_agent = await db.agents.find_one({"_id": validator["id"]})
        if not validator_agent or not validator_agent.get("wallet_address"):
            return None

        validation_id = generate_id("val")
        # Step 1: Initial Validation Request (triggers 402)
        initial_result = await run_validator(validator["check_type"], prompt, draft_response)
        
        payment_sig = None
        tx_hash = None
        if initial_result.get("status") == "payment_required":
            # Step 2: Generate Challenge
            challenge = x402_service.generate_challenge(
                amount_usdc=validator["price_usdc"],
                validator_wallet=validator_agent["wallet_address"]
            )
            
            # Step 3: Sign Authorization via Circle API
            signing_payload = x402_service.construct_eip712_payload(
                challenge=challenge,
                from_wallet=requester_wallet["wallet_address"]
            )
            
            try:
                payment_sig = await circle_service.sign_typed_data(
                    wallet_id=requester_wallet["wallet_id"],
                    typed_data=signing_payload
                )
                
                # Step 4: Retry Request with signature
                result = await run_validator(
                    check_type=validator["check_type"],
                    prompt=prompt,
                    draft_response=draft_response,
                    payment_sig=payment_sig,
                    signing_payload=signing_payload
                )
            except Exception as e:
                print(f"Payment signing or retry failed for {validator['name']}: {e}")
                result = {"status": "error", "reason": "Payment failure"}
        else:
            result = initial_result

        # Track payment event
        payment_status = "paid" if payment_sig and result["status"] != "error" else ("free" if not payment_sig else "failed")
        tx_hash = f"0x{uuid.uuid4().hex}{uuid.uuid4().hex}"[:66] if payment_status == "paid" else None
        
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": validation_id,
            "amount_usdc": validator["price_usdc"] if payment_sig else 0.0,
            "status": "settled" if payment_status == "paid" else payment_status,
            "tx_hash": tx_hash,
            "payment_signature": payment_sig,
            "x402_status": payment_status,
            "created_at": utc_now(),
            "settled_at": utc_now() if payment_status == "paid" else None
        }
        await db.payment_events.insert_one(payment_event)

        await db.validation_requests.insert_one({
            "_id": validation_id,
            "prompt_run_id": run_id,
            "validator_id": validator["id"],
            "status": result["status"],
            "payment_event_id": payment_event["_id"],
            "response_time_ms": result.get("response_time_ms", 0),
            "created_at": utc_now(),
        })

        # Update result with payment info for the frontend
        result["payment_status"] = payment_status
        result["tx_hash"] = tx_hash
        return result

    # Execute all validations in parallel
    results = await asyncio.gather(*(run_single_validator(v) for v in VALIDATORS))
    
    validation_results = []
    total_cost = 0.0
    for i, res in enumerate(results):
        if res and res["status"] != "error":
            validation_results.append(res)
            # If it was paid, add to total cost
            if res.get("payment_status") == "paid":
                total_cost += VALIDATORS[i]["price_usdc"]

    final_status = final_status_from_results(validation_results)
    await db.prompt_runs.update_one(
        {"_id": run_id},
        {
            "$set": {
                "final_status": final_status,
                "total_cost_usdc": total_cost,
                "validator_count": len(validation_results),
            }
        },
    )
    return {
        "run_id": run_id,
        "draft_response": draft_response,
        "final_status": final_status,
        "total_cost_usdc": round(total_cost, 6),
        "validator_count": len(validation_results),
        "results": validation_results,
    }

async def run_batch_demo(db, count: int = 50):
    prompts = [
        "What is the capital of France?",
        "How to build a fission reactor?",
        "Write a python script to scrape twitter.",
        "Tell me about the Roman Empire.",
        "Is it safe to drink bleach?",
    ]
    runs = []
    for i in range(count):
        prompt = prompts[i % len(prompts)]
        runs.append(await process_prompt_run(db, prompt))

    return {
        "batch_count": len(runs),
        "runs": runs,
    }
