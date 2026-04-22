import httpx
import json
import logging
from app.config import settings
from app.services.circle_service import circle_service
from app.services.x402_service import x402_service

logger = logging.getLogger(__name__)

# --- Tool Definitions ---

async def create_user_wallet(user_name: str):
    try:
        wallet_set = await circle_service.create_wallet_set(f"Aurelius-{user_name}")
        wallets = await circle_service.create_wallets(wallet_set["id"], blockchain="ARC-TESTNET")
        return {
            "status": "success",
            "wallet_id": wallets[0]["id"],
            "wallet_address": wallets[0]["address"],
            "blockchain": "ARC-TESTNET"
        }
    except Exception as e:
        logger.error(f"Failed to create wallet: {e}")
        return {"status": "error", "message": str(e)}

async def initiate_payment(amount_usdc: float, to_address: str, from_wallet_id: str, from_wallet_address: str):
    if amount_usdc > 0.01:
        raise ValueError("Per‑action amount must be ≤ 0.01 USDC")
    try:
        challenge = x402_service.generate_challenge(
            amount_usdc=amount_usdc,
            validator_wallet=to_address
        )
        signing_payload = x402_service.construct_eip712_payload(
            challenge=challenge,
            from_wallet=from_wallet_address
        )
        signature = await circle_service.sign_typed_data(
            wallet_id=from_wallet_id,
            typed_data=signing_payload
        )
        return {
            "status": "settled",
            "amount": amount_usdc,
            "recipient": to_address,
            "signature": signature,
            "blockchain": "ARC-TESTNET"
        }
    except Exception as e:
        logger.error(f"Payment initiation failed: {e}")
        return {"status": "error", "message": str(e)}

class GeminiService:
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.aiml_api_key = settings.AIML_API_KEY
        self.aiml_base_url = settings.AIML_API_URL
        self.default_model = "google/gemini-2.0-flash" if self.aiml_api_key else "gemini-1.5-flash"

    async def chat_with_tools(self, prompt: str, chat_history=None):
        """Uses Google Direct if available, else falls back to AI/ML API."""
        if self.google_api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.google_api_key}"
                    resp = await client.post(url, json={
                        "contents": [{"parts": [{"text": prompt}]}]
                    })
                    if resp.status_code == 200:
                        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.warning(f"Google direct call failed: {e}")

        if not self.aiml_api_key:
            return await self._fallback(prompt)

        # AI/ML API (OpenAI-compatible) logic
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_user_wallet",
                    "description": "Creates a new Circle Developer-Controlled wallet for a user or agent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_name": {"type": "string"}
                        },
                        "required": ["user_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "initiate_payment",
                    "description": "Initiates a USDC settlement on the Arc network.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount_usdc": {"type": "number"},
                            "to_address": {"type": "string"},
                            "from_wallet_id": {"type": "string"},
                            "from_wallet_address": {"type": "string"}
                        },
                        "required": ["amount_usdc", "to_address", "from_wallet_id", "from_wallet_address"]
                    }
                }
            }
        ]

        messages = [
            {"role": "system", "content": "You are Aurelius, an AI orchestrator for the autonomous agent economy."}
        ]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.aiml_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.aiml_api_key}"},
                    json={
                        "model": "google/gemini-2.0-flash",
                        "messages": messages,
                        "tools": tools
                    }
                )
                if response.status_code == 200:
                    resp_json = response.json()
                    message = resp_json["choices"][0]["message"]
                    if message.get("tool_calls"):
                        tool_call = message["tool_calls"][0]
                        func_name = tool_call["function"]["name"]
                        func_args = json.loads(tool_call["function"]["arguments"])
                        
                        if func_name == "create_user_wallet":
                            res = await create_user_wallet(**func_args)
                        elif func_name == "initiate_payment":
                            res = await initiate_payment(**func_args)
                        else:
                            res = {"status": "error"}
                            
                        return f"Tool Execution: {func_name} completed with result: {json.dumps(res)}"
                    return message["content"]
        except Exception as e:
            logger.error(f"AI/ML API failed: {e}")
            
        return await self._fallback(prompt)

    async def run_completion(self, prompt: str, model: str = None, system_prompt: str = None):
        if self.google_api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.google_api_key}"
                    payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt}]}]}
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                logger.warning(f"Google completion failed: {e}")

        if not self.aiml_api_key:
            return await self._fallback(prompt)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.aiml_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.aiml_api_key}"},
                    json={
                        "model": model or "google/gemini-2.0-flash",
                        "messages": [
                            {"role": "system", "content": system_prompt or ""},
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"AI/ML API completion failed: {e}")

        return await self._fallback(prompt)

    async def _fallback(self, prompt: str):
        from app.services.featherless_service import featherless_service
        try:
            return await featherless_service.run_inference(
                model_id="mistralai/Mistral-7B-Instruct-v0.2",
                prompt=prompt
            )
        except:
            return "Fallback reasoning failed."

gemini_service = GeminiService()
