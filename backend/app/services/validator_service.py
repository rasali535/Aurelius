import random
import time
from app.services.circle_service import circle_service
from app.services.gemini_service import gemini_service
import json

VALIDATORS = [
    {
        "id": "validator_hallucination_1",
        "name": "Hallucination Validator",
        "check_type": "hallucination",
        "price_usdc": 0.001,
        "reputation_score": 82,
    },
    {
        "id": "validator_hallucination_premium",
        "name": "Hallucination Premium",
        "check_type": "hallucination_premium",
        "price_usdc": 0.005,
        "reputation_score": 96,
    },
    {
        "id": "validator_pii_1",
        "name": "PII Validator",
        "check_type": "pii",
        "price_usdc": 0.001,
        "reputation_score": 88,
    },
    {
        "id": "validator_safety_1",
        "name": "Safety Validator",
        "check_type": "safety",
        "price_usdc": 0.002,
        "reputation_score": 90,
    },
    {
        "id": "validator_compliance_1",
        "name": "Compliance Validator",
        "check_type": "compliance",
        "price_usdc": 0.003,
        "reputation_score": 85,
    },
]

async def seed_validators(db):
    # Check if we have a wallet set for validators
    wallet_set_id = None
    existing_sets = await db.config.find_one({"_id": "circle_validator_wallet_set"})
    if not existing_sets:
        try:
            new_set = await circle_service.create_wallet_set("Aurelius Validators")
            wallet_set_id = new_set["id"]
            await db.config.insert_one({"_id": "circle_validator_wallet_set", "id": wallet_set_id})
        except Exception as e:
            print(f"Failed to create wallet set: {e}")
            return

    wallet_set_id = existing_sets["id"] if existing_sets else wallet_set_id

    for validator in VALIDATORS:
        existing = await db.agents.find_one({"_id": validator["id"]})
        if not existing or not existing.get("wallet_id"):
            try:
                wallets = await circle_service.create_wallets(wallet_set_id, blockchain="ARC-TESTNET")
                wallet_info = wallets[0]
                await db.agents.update_one(
                    {"_id": validator["id"]},
                    {
                        "$set": {
                            "name": validator["name"],
                            "role": "validator",
                            "wallet_id": wallet_info["id"],
                            "wallet_address": wallet_info["address"],
                            "supported_checks": [validator["check_type"]],
                            "price_usdc": validator["price_usdc"],
                            "reputation_score": validator["reputation_score"],
                        }
                    },
                    upsert=True,
                )
                print(f"Seeded Dev-Controlled wallet for {validator['name']}: {wallet_info['address']}")
            except Exception as e:
                print(f"Failed to seed wallet for {validator['name']}: {e}")

from app.services.x402_service import x402_service

async def run_validator(check_type: str, prompt: str, draft_response: str, payment_sig: str = None, signing_payload: dict = None):
    # If no payment signature is provided, return a 402 challenge
    if not payment_sig:
        return {"status": "payment_required", "challenge": True}
    
    # Verify the signature
    if not signing_payload or not x402_service.verify_signature(signing_payload, payment_sig):
        return {"status": "error", "reason": "Invalid payment signature"}
    
    start = time.time()
    
    # Gemini-based validation logic
    system_prompts = {
        "hallucination": "Verify if the draft response contains factual errors or 'hallucinations' for the given prompt.",
        "pii": "Scan for Personal Identifiable Information (PII) leakage like SSNs, passport numbers, or credit card details.",
        "safety": "Identify unsafe content, self-harm instructions, or illegal weapon manufacturing details.",
        "compliance": "Check for financial compliance violations like tax evasion advice or money laundering schemes."
    }
    
    prompt_for_gemini = (
        f"Role: Specialized Validator Agent ({check_type})\n"
        f"Task: {system_prompts.get(check_type, 'Verify content safety and accuracy')}\n"
        f"User Prompt: {prompt}\n"
        f"Draft Response: {draft_response}\n\n"
        "Return a JSON object with: 'status' (passed/warning/failed/blocked), 'risk_score' (0.0 to 1.0), and 'reason' (string)."
    )
    
    try:
        gemini_raw_resp = await gemini_service.chat_with_tools(prompt_for_gemini)
        # Attempt to parse JSON from Gemini's text response
        # Gemini often wraps code in triple backticks
        json_str = gemini_raw_resp.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        analysis = json.loads(json_str)
        status = analysis.get("status", "passed")
        risk_score = analysis.get("risk_score", 0.1)
        reason = analysis.get("reason", "Analysis complete")
    except Exception as e:
        print(f"Gemini validation failed, falling back to simple rules: {e}")
        # Fallback to simple rule-based simulation if Gemini fails
        if check_type in ["hallucination", "hallucination_premium"]:
            risky = any(word in draft_response.lower() for word in ["always", "guaranteed", "cure"])
            status = "warning" if risky else "passed"
            risk_score = 0.85 if risky else round(random.uniform(0.01, 0.10), 2)
            reason = "Potential factual overclaim (Rule Fallback)" if risky else "No strong indicators (Rule Fallback)"
        else:
            status = "passed"
            risk_score = 0.1
            reason = "Standard pass (Fallback)"

    # Simulated delay
    time.sleep(random.uniform(0.05, 0.2))
    response_time_ms = int((time.time() - start) * 1000)

    validator = next(v for v in VALIDATORS if v["check_type"] == check_type)

    return {
        "validator_id": validator["id"],
        "check_type": check_type,
        "status": status,
        "risk_score": risk_score,
        "reason": reason,
        "response_time_ms": response_time_ms,
        "unit_price": validator["price_usdc"],
    }
