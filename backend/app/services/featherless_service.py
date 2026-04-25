import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

from app.services.circle_service import circle_service
from app.db import db
from app.utils import generate_id, utc_now

# FEATHERLESS_MODELS defines the suitability and pricing (in USDC)
FEATHERLESS_MODELS = [
    {
        "id": "codellama/CodeLlama-7b-Instruct-hf",
        "category": "coding",
        "price_per_inference_usdc": 0.0002,
        "description": "Optimized for specialized coding tasks and technical architecture."
    },
    {
        "id": "BioMistral/BioMistral-7B",
        "category": "scientific",
        "price_per_inference_usdc": 0.0003,
        "description": "Deep scientific and medical domain knowledge."
    },
    {
        "id": "mistralai/Mistral-7B-Instruct-v0.2",
        "category": "general",
        "price_per_inference_usdc": 0.0001,
        "description": "Standard efficiency for common agent reasoning."
    }
]

class FeatherlessService:
    def __init__(self):
        self.api_key = settings.FEATHERLESS_API_KEY
        self.base_url = "https://api.featherless.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def route_task(self, task: str):
        """Intelligently routes task to the best specialized model."""
        task_lower = task.lower()
        if any(w in task_lower for w in ["code", "python", "js", "fix", "debug", "sql"]):
            return FEATHERLESS_MODELS[0]
        if any(w in task_lower for w in ["science", "medical", "patient", "dna", "formula"]):
            return FEATHERLESS_MODELS[1]
        return FEATHERLESS_MODELS[2]

    async def run_inference(self, model_id: str, prompt: str):
        """Runs inference via Featherless API."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code != 200:
                logger.error(f"Featherless API error: {resp.text}")
                return f"Error: {resp.text}"
            
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def process_and_settle(self, task: str, wallet_id: str):
        """Executes the full Routing + Settlement + Inference cycle."""
        # 1. Route
        model_meta = self.route_task(task)
        
        # 2. Settle Value on Arc (USDC)
        # We use Gateway to ensure economically viable sub-cent settlement
        try:
            tx_hash = await circle_service.gateway_transfer(
                wallet_id=wallet_id,
                destination_blockchain="ARC-TESTNET",
                destination_address="0x3E5A42D19a584093952fA6d7667C82D7068560F4", # Provider Wallet
                amount=model_meta["price_per_inference_usdc"]
            )
            
            # 3. Run Inference
            result = await self.run_inference(model_meta["id"], task)
            
            # 4. Record event
            payment_event = {
                "_id": generate_id("pay"),
                "amount_usdc": model_meta["price_per_inference_usdc"],
                "status": "settled",
                "tx_hash": tx_hash,
                "x402_status": "inference_payment",
                "model_used": model_meta["id"],
                "created_at": utc_now()
            }
            await db.payment_events.insert_one(payment_event)
            
            return {
                "result": result,
                "model": model_meta["id"],
                "tx_hash": tx_hash,
                "cost": model_meta["price_per_inference_usdc"]
            }
        except Exception as e:
            logger.error(f"Featherless settlement failed: {e}")
            return {"error": str(e)}

featherless_service = FeatherlessService()

featherless_service = FeatherlessService()
