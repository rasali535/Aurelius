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
    wallets = await circle_service.create_wallets(wallet_set["id"])
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
    db.prompt_runs.insert_one(prompt_doc)

    validation_results = []
    total_cost = 0.0

    for validator in VALIDATORS:
        validator_agent = db.agents.find_one({"_id": validator["id"]})
        if not validator_agent or not validator_agent.get("wallet_address"):
            continue

        validation_id = generate_id("val")
        # Step 1: Initial Validation Request (triggers 402)
        initial_result = await run_validator(validator["check_type"], prompt, draft_response)
        
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
            
            payment_sig = await circle_service.sign_typed_data(
                wallet_id=requester_wallet["wallet_id"],
                typed_data=signing_payload
            )
            
            # Step 4: Retry Request with signature
            result = await run_validator(
                check_type=validator["check_type"],
                prompt=prompt,
                draft_response=draft_response,
                payment_sig=payment_sig
            )
        else:
            result = initial_result

        # Track payment event with real signature
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": validation_id,
            "amount_usdc": validator["price_usdc"],
            "status": "settling",
            "payment_signature": payment_sig if 'payment_sig' in locals() else None,
            "x402_status": "paid",
            "created_at": utc_now(),
        }
        db.payment_events.insert_one(payment_event)

        db.validation_requests.insert_one({
            "_id": validation_id,
            "prompt_run_id": run_id,
            "validator_id": validator["id"],
            "status": result["status"],
            "payment_event_id": payment_event["_id"],
            "response_time_ms": result.get("response_time_ms", 0),
            "created_at": utc_now(),
        })

        total_cost += validator["price_usdc"]
        validation_results.append(result)

    final_status = final_status_from_results(validation_results)
    db.prompt_runs.update_one(
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
