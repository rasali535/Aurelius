import httpx
from app.config import settings
from app.services.circle_service import circle_service
from app.services.x402_service import x402_service
import json
import logging

logger = logging.getLogger(__name__)

# --- Tool Definitions for Gemini ---

async def create_user_wallet(user_name: str):
    """
    Creates a new Circle Developer-Controlled wallet for a user or agent.
    Returns the wallet address and ID.
    """
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
    """
    Initiates a USDC settlement on the Arc network using the X402 gasless protocol.
    Requires the source wallet ID and address.
    """
    # ---- Validation Guard ----
    # Hackathon rule: per‑action price must stay ≤ 0.01 USDC.
    if amount_usdc > 0.01:
        raise ValueError("Per‑action amount must be ≤ 0.01 USDC")
    try:
        # 1. Generate x402 challenge
        challenge = x402_service.generate_challenge(
            amount_usdc=amount_usdc,
            validator_wallet=to_address
        )
        
        # 2. Construct EIP-712 payload
        signing_payload = x402_service.construct_eip712_payload(
            challenge=challenge,
            from_wallet=from_wallet_address
        )
        
        # 3. Sign via Circle API
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
        self.api_key = settings.AIML_API_KEY
        self.base_url = settings.AIML_API_URL
        # Try a more standard model name if the previous one failed
        self.default_model = "google/gemini-2.0-flash"
        
        if not self.api_key:
            logger.warning("AIML_API_KEY not found. GeminiService will use fallback only.")

    async def chat_with_tools(self, prompt: str, chat_history=None):
        """
        Main entry point for agent reasoning and tool usage via AI/ML API.
        Uses OpenAI-compatible chat completion with tool support.
        """
        if not self.api_key:
            return await self._fallback(prompt)

        # 1. Define tools in OpenAI format
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_user_wallet",
                    "description": "Creates a new Circle Developer-Controlled wallet for a user or agent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_name": {"type": "string", "description": "The name of the user or agent"}
                        },
                        "required": ["user_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "initiate_payment",
                    "description": "Initiates a USDC settlement on the Arc network using the X402 gasless protocol.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount_usdc": {"type": "number", "description": "Amount in USDC (max 0.01)"},
                            "to_address": {"type": "string", "description": "Recipient address"},
                            "from_wallet_id": {"type": "string", "description": "Source wallet ID"},
                            "from_wallet_address": {"type": "string", "description": "Source wallet address"}
                        },
                        "required": ["amount_usdc", "to_address", "from_wallet_id", "from_wallet_address"]
                    }
                }
            }
        ]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Aurelius, an AI orchestrator for the autonomous agent economy. "
                    "You coordinate agent workflows and handle value settlement using Circle USDC on the Arc network. "
                    "You have access to tools to create wallets and initiate payments. "
                    "Always confirm details before settling large amounts."
                )
            }
        ]
        
        if chat_history:
            # Map Gemini history format to OpenAI if needed, but assuming simple history for now
            messages.extend(chat_history)
            
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.default_model,
                        "messages": messages,
                        "tools": tools,
                        "tool_choice": "auto"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"AI/ML API error: {response.text}")
                    return await self._fallback(prompt)
                
                resp_json = response.json()
                message = resp_json["choices"][0]["message"]
                
                # Handle Tool Calls
                if message.get("tool_calls"):
                    tool_call = message["tool_calls"][0]
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])
                    
                    logger.info(f"Executing tool: {func_name} with args: {func_args}")
                    
                    if func_name == "create_user_wallet":
                        result = await create_user_wallet(**func_args)
                    elif func_name == "initiate_payment":
                        result = await initiate_payment(**func_args)
                    else:
                        result = {"status": "error", "message": "Unknown tool"}
                        
                    # Follow up with the tool result (this is a simple 1-step tool execution)
                    messages.append(message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": func_name,
                        "content": json.dumps(result)
                    })
                    
                    final_resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model": self.default_model,
                            "messages": messages
                        }
                    )
                    return final_resp.json()["choices"][0]["message"]["content"]
                
                return message["content"]
                
        except Exception as e:
            logger.warning(f"AI/ML API call failed, falling back: {e}")
            return await self._fallback(prompt)

    async def _fallback(self, prompt: str):
        """Fallback to Featherless Llama 3.1 70B"""
        from app.services.featherless_service import featherless_service
        try:
            logger.info("Using Featherless fallback reasoning engine")
            return await featherless_service.run_inference(
                model_id="mistralai/Mistral-7B-Instruct-v0.2",
                prompt=f"System: You are Aurelius, an AI orchestrator for the autonomous agent economy on Arc.\n\nUser: {prompt}"
            )
        except Exception as e:
            logger.error(f"Reasoning fallback failed: {e}")
            return "Execution failed. No reasoning model available."

gemini_service = GeminiService()
