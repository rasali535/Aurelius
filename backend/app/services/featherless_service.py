import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# FEATHERLESS_MODELS defines the suitability and pricing (in USDC)
FEATHERLESS_MODELS = [
    {
        "id": "mistralai/Mistral-7B-Instruct-v0.2",
        "category": "general",
        "price_per_inference_usdc": 0.0001,
        "description": "Fast, reliable model for common tasks."
    },
    {
        "id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "category": "reasoning",
        "price_per_inference_usdc": 0.0005,
        "description": "High intelligence for complex reasoning."
    },
    {
        "id": "microsoft/Phi-3-mini-4k-instruct",
        "category": "fast",
        "price_per_inference_usdc": 0.00005,
        "description": "Ultra-fast, lowest cost."
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

    async def run_inference(self, model_id: str, prompt: str):
        """Runs inference via Featherless API (OpenAI compatible)."""
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
                resp.raise_for_status()
            
            data = resp.json()
            return data["choices"][0]["message"]["content"]

featherless_service = FeatherlessService()
