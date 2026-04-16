import random
import time

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

from app.services.circle_service import circle_service

VALIDATORS = [
    # ... (same validator definitions)
]

async def seed_validators(db):
    # Check if we have a wallet set for validators
    wallet_set_id = None
    existing_sets = await db.config.find_one({"_id": "circle_validator_wallet_set"})
    if not existing_sets:
        # Note: This requires a valid entity secret ciphertext in .env
        try:
            new_set = await circle_service.create_wallet_set("Aurelius Validators")
            wallet_set_id = new_set["id"]
            await db.config.insert_one({"_id": "circle_validator_wallet_set", "id": wallet_set_id})
        except Exception as e:
            print(f"Failed to create wallet set: {e}")
            return

    wallet_set_id = existing_sets["id"] if existing_sets else wallet_set_id

    for validator in VALIDATORS:
        existing = db.agents.find_one({"_id": validator["id"]})
        if not existing or not existing.get("wallet_id"):
            # Create a real developer-controlled wallet for this validator
            try:
                wallets = await circle_service.create_wallets(wallet_set_id)
                wallet_info = wallets[0]
                db.agents.update_one(
                    {"_id": validator["id"]},
                    {
                        "$set": {
                            "_id": validator["id"],
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
            except Exception as e:
                print(f"Failed to seed wallet for {validator['name']}: {e}")

async def run_validator(check_type: str, prompt: str, draft_response: str, payment_sig: str = None):
    # If no payment signature is provided, return a 402 challenge
    if not payment_sig:
        return {"status": "payment_required", "challenge": True}
    
    # ... (logic for check types)
    start = time.time()

    if check_type in ["hallucination", "hallucination_premium"]:
        risky = any(word in draft_response.lower() for word in ["always", "guaranteed", "cure"])
        status = "warning" if risky else "passed"
        # Premium validator has a different risk score logic (simulated accuracy)
        if check_type == "hallucination_premium":
            risk_score = 0.85 if risky else round(random.uniform(0.01, 0.10), 2)
        else:
            risk_score = 0.72 if risky else round(random.uniform(0.05, 0.25), 2)
        reason = "Potential factual overclaim detected" if risky else "No strong hallucination indicators found"

    elif check_type == "pii":
        risky = any(token in draft_response.lower() for token in ["ssn", "passport", "credit card"])
        status = "failed" if risky else "passed"
        risk_score = 0.91 if risky else round(random.uniform(0.01, 0.15), 2)
        reason = "Possible PII leakage detected" if risky else "No PII leakage detected"

    elif check_type == "safety":
        risky = any(word in draft_response.lower() for word in ["self-harm", "illegal", "weapon"])
        status = "warning" if risky else "passed"
        risk_score = 0.79 if risky else round(random.uniform(0.05, 0.30), 2)
        reason = "Potential unsafe content detected" if risky else "No major safety issues found"

    elif check_type == "compliance":
        risky = any(word in draft_response.lower() for word in ["tax evasion", "money laundering", "insider trading"])
        status = "blocked" if risky else "passed"
        risk_score = 0.98 if risky else round(random.uniform(0.02, 0.20), 2)
        reason = "Compliance violation detected" if risky else "No compliance issues found"

    else:
        status = "passed"
        risk_score = 0.1
        reason = "Unknown validator type fallback"

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
