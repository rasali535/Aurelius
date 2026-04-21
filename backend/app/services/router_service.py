from app.services.gemini_service import gemini_service
from app.services.featherless_service import featherless_service, FEATHERLESS_MODELS
from app.services.circle_service import circle_service
from app.services.x402_service import x402_service
from app.utils import generate_id, utc_now
import json
import logging

logger = logging.getLogger(__name__)

class RouterService:
    async def route_and_execute(self, db, task_prompt: str):
        """
        1. Analyzes task to pick the best Featherless model.
        2. Prices the request and triggers USDC settlement on Arc.
        3. Executes inference on Featherless.
        """
        # --- Step 1: Reasoning with Gemini to pick the model ---
        catalog_str = json.dumps(FEATHERLESS_MODELS, indent=2)
        routing_prompt = (
            f"Given the following task, select the most suitable specialized model from the catalog.\n"
            f"Catalog:\n{catalog_str}\n\n"
            f"Task: {task_prompt}\n\n"
            "Return a JSON object with: 'selected_model_id', 'reasoning', 'price_usdc'."
        )
        
        try:
            routing_decision_str = await gemini_service.chat_with_tools(routing_prompt)
            # Cleanup JSON string
            json_str = routing_decision_str.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
                
            decision = json.loads(json_str)
            model_id = decision["selected_model_id"]
            price_usdc = decision["price_usdc"]
        except Exception as e:
            logger.warning(f"Routing failed, falling back to Llama-3-8B: {e}")
            model_id = "meta-llama/Llama-3-8B-Instruct"
            price_usdc = 0.0001
            decision = {"reasoning": "Fallback due to routing error"}

        # --- Step 2: Settlement ---
        provider_wallet = await db.config.find_one({"_id": "provider_wallet"})
        if not provider_wallet:
            wallet_set = await circle_service.create_wallet_set("Aurelius Provider")
            wallets = await circle_service.create_wallets(wallet_set["id"], blockchain="ARC-TESTNET")
            provider_wallet = {
                "_id": "provider_wallet",
                "wallet_id": wallets[0]["id"],
                "wallet_address": wallets[0]["address"]
            }
            await db.config.insert_one(provider_wallet)

        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
             wallet_set = await circle_service.create_wallet_set("Aurelius Requester")
             wallets = await circle_service.create_wallets(wallet_set["id"], blockchain="ARC-TESTNET")
             requester = {
                 "_id": "requester_wallet",
                 "wallet_id": wallets[0]["id"],
                 "wallet_address": wallets[0]["address"]
             }
             await db.config.insert_one(requester)

        challenge = x402_service.generate_challenge(price_usdc, provider_wallet["wallet_address"])
        signing_payload = x402_service.construct_eip712_payload(challenge, requester["wallet_address"])
        
        # Sign 
        signature = await circle_service.sign_typed_data(requester["wallet_id"], signing_payload)
        
        # --- Step 3: Execute Inference ---
        output = await featherless_service.run_inference(model_id, task_prompt)

        # --- Log the event ---
        inference_log = {
            "_id": generate_id("inf"),
            "model_id": model_id,
            "task": task_prompt,
            "output": output,
            "price_usdc": price_usdc,
            "settlement_sig": signature,
            "routing_reasoning": decision.get("reasoning"),
            "created_at": utc_now()
        }
        await db.inference_logs.insert_one(inference_log)

        return {
            "model_id": model_id,
            "output": output,
            "price_usdc": price_usdc,
            "status": "settled",
            "log_id": inference_log["_id"],
            "reasoning": decision.get("reasoning")
        }

router_service = RouterService()
