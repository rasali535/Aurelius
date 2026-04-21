import google.generativeai as genai
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
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY not found. GeminiService will be limited.")
            self.model = None
            return
            
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # We wrap the async functions to be compatible with Gemini's expectation 
        # (Though the Python SDK handles many things, we need to be careful with async)
        
        self.tools = [create_user_wallet, initiate_payment]
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=self.tools,
            system_instruction=(
                "You are Aurelius, an AI orchestrator for the autonomous agent economy. "
                "You coordinate agent workflows and handle value settlement using Circle USDC on the Arc network. "
                "You have access to tools to create wallets and initiate payments. "
                "Always confirm details before settling large amounts."
            )
        )

    async def chat_with_tools(self, prompt: str, chat_history=None):
        """
        Main entry point for agent reasoning and tool usage.
        Fallbacks to Featherless (Llama 3 70B) if Gemini is unavailable.
        """
        if self.model:
            try:
                chat = self.model.start_chat(history=chat_history or [], enable_automatic_function_calling=True)
                response = await chat.send_message_async(prompt)
                return response.text
            except Exception as e:
                logger.warning(f"Gemini call failed, falling back to Featherless: {e}")

        # Fallback to Featherless Llama-3-70B
        from app.services.featherless_service import featherless_service
        try:
            return await featherless_service.run_inference(
                model_id="meta-llama/Meta-Llama-3.1-70B-Instruct",
                prompt=f"System: You are Aurelius, an AI orchestrator for the autonomous agent economy on Arc.\n\nUser: {prompt}"
            )
        except Exception as e:
            logger.error(f"Reasoning fallback failed: {e}")
            return "Execution failed. No reasoning model available."

gemini_service = GeminiService()
