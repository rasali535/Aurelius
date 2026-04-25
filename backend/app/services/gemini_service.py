import httpx
import json
import logging
from app.config import settings
from app.services.circle_service import circle_service
from app.services.x402_service import x402_service
from app.db import db

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

async def bridge_usdc(amount: float, source_blockchain: str, destination_blockchain: str, wallet_id: str, destination_address: str):
    try:
        result = await circle_service.bridge_usdc(
            wallet_id=wallet_id,
            amount=amount,
            source_blockchain=source_blockchain,
            destination_blockchain=destination_blockchain,
            destination_address=destination_address
        )
        return result
    except Exception as e:
        logger.error(f"Bridge tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def register_ai_agent(metadata_uri: str, wallet_id: str):
    try:
        tx_hash = await circle_service.register_agent(wallet_id, metadata_uri)
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        logger.error(f"Register agent tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def create_agent_job(provider: str, evaluator: str, description: str, wallet_id: str):
    try:
        tx_hash = await circle_service.create_job(wallet_id, provider, evaluator, description)
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        logger.error(f"Create job tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def get_crypto_price(symbol: str):
    """Fetches real-time price data for a crypto symbol."""
    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "usdc": "usd-coin"
    }
    coin_id = mapping.get(symbol.lower(), symbol.lower())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            data = res.json()
            if coin_id in data:
                price = data[coin_id]["usd"]
                change = data[coin_id].get("usd_24h_change", 0)
                return {
                    "status": "success",
                    "symbol": symbol.upper(),
                    "price_usd": price,
                    "change_24h": f"{change:.2f}%"
                }
            return {"status": "error", "message": f"Symbol {symbol} not found."}
    except Exception as e:
        logger.error(f"Price tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def gateway_nanopayment(destination_blockchain: str, destination_address: str, amount: float, wallet_id: str):
    try:
        tx_hash = await circle_service.gateway_transfer(wallet_id, destination_blockchain, destination_address, amount)
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        logger.error(f"Gateway tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def get_dashboard_summary():
    """Returns the global metrics for the Aurelius platform."""
    try:
        total_prompt_runs = await db.prompt_runs.count_documents({})
        total_validations = await db.validation_requests.count_documents({})
        
        # Aggregate settled payments
        agg = db.payment_events.aggregate([
            {"$match": {"status": "settled"}},
            {"$group": {"_id": None, "total_spend": {"$sum": "$amount_usdc"}, "count": {"$sum": 1}}}
        ])
        res = await agg.to_list(length=1)
        stats = res[0] if res else {"total_spend": 0, "count": 0}
        
        return {
            "total_runs": total_prompt_runs,
            "total_validations": total_validations,
            "total_settled_payments": stats.get("count", 0),
            "total_spend_usdc": round(stats.get("total_spend", 0), 4)
        }
    except Exception as e:
        logger.error(f"Dashboard summary tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def get_agents_list():
    """Retrieves the list of active validator agents and their current status."""
    try:
        agents = await db.agents.find().to_list(length=50)
        # Simplify for AI context
        agent_list = []
        for a in agents:
            agent_list.append({
                "name": a.get("name"),
                "type": a.get("type"),
                "status": "online",
                "price_usdc": a.get("price_usdc", 0.0),
                "reputation": a.get("reputation_score", 0)
            })
        return {"agents": agent_list}
    except Exception as e:
        logger.error(f"Agents list tool failed: {e}")
        return {"status": "error", "message": str(e)}

async def get_requester_wallet_info():
    """Retrieves the Requester Agent's wallet ID and address."""
    try:
        wallet = await db.config.find_one({"_id": "requester_wallet"})
        if not wallet:
            return {"status": "error", "message": "Requester wallet not initialized."}
        return {
            "wallet_id": wallet.get("wallet_id"),
            "wallet_address": wallet.get("wallet_address")
        }
    except Exception as e:
        logger.error(f"Wallet info tool failed: {e}")
        return {"status": "error", "message": str(e)}

class GeminiService:
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.aiml_api_key = settings.AIML_API_KEY
        self.aiml_base_url = settings.AIML_API_URL
        self.default_model = "google/gemini-2.0-flash" if self.aiml_api_key else "gemini-1.5-flash"

    @property
    def available_models(self):
        return [
            {"id": "google/gemini-2.0-flash", "category": "fast", "price_usdc": 0.0001, "description": "Optimized for transactional speed."},
            {"id": "google/gemini-2.0-pro-exp-02-05", "category": "reasoning", "price_usdc": 0.0005, "description": "Deep reasoning and treasury management."},
            {"id": "anthropic/claude-3.5-sonnet", "category": "reasoning", "price_usdc": 0.0008, "description": "Highly nuanced legal and architectural reasoning."}
        ]

    async def chat_with_tools(self, prompt: str, chat_history=None):
        """
        Uses AI/ML API (OpenAI-compatible) as the primary provider for tool-enabled chat.
        Falls back to Google Direct if AI/ML API is unavailable.
        """
        if self.aiml_api_key:
            try:
                # Move AI/ML logic to a private helper or keep it here
                return await self._call_aiml_chat(prompt, chat_history)
            except Exception as e:
                logger.warning(f"AI/ML API tool call failed, attempting Google fallback: {e}")

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
                logger.warning(f"Google direct fallback failed: {e}")

        return await self._fallback(prompt)

    async def _call_aiml_chat(self, prompt: str, chat_history=None):
        """Helper to call AI/ML API with full tool definitions."""

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
            },
            {
                "type": "function",
                "function": {
                    "name": "bridge_usdc",
                    "description": "Bridges native USDC across blockchains using CCTP.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                            "source_blockchain": {"type": "string", "enum": ["ARC-TESTNET", "ETH-SEPOLIA"]},
                            "destination_blockchain": {"type": "string", "enum": ["ARC-TESTNET", "ETH-SEPOLIA"]},
                            "wallet_id": {"type": "string"},
                            "destination_address": {"type": "string"}
                        },
                        "required": ["amount", "source_blockchain", "destination_blockchain", "wallet_id", "destination_address"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "register_ai_agent",
                    "description": "Registers an AI agent on the Arc Network (ERC-8004) to establish identity and reputation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metadata_uri": {"type": "string", "description": "URI pointing to agent metadata (JSON)."},
                            "wallet_id": {"type": "string", "description": "The Circle wallet ID of the agent."}
                        },
                        "required": ["metadata_uri", "wallet_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_agent_job",
                    "description": "Creates a task-based commerce job (ERC-8183) with automated escrow.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string", "description": "Wallet address of the service provider agent."},
                            "evaluator": {"type": "string", "description": "Wallet address of the independent evaluator agent."},
                            "description": {"type": "string", "description": "Task description."},
                            "wallet_id": {"type": "string", "description": "The Circle wallet ID of the requester."}
                        },
                        "required": ["provider", "evaluator", "description", "wallet_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "gateway_nanopayment",
                    "description": "Facilitates sub-cent payments using unified Gateway balances across chains.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination_blockchain": {"type": "string", "enum": ["ETH-SEPOLIA", "AVALANCHE-FUJI", "BASE-SEPOLIA"]},
                            "destination_address": {"type": "string", "description": "Recipient address."},
                            "amount": {"type": "number", "description": "USDC amount (can be very small)."},
                            "wallet_id": {"type": "string", "description": "The Circle wallet ID."}
                        },
                        "required": ["destination_blockchain", "destination_address", "amount", "wallet_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "request_settlement_from_image",
                    "description": "Analyzes a commerce document (invoice/receipt) and requests settlement on Arc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "document_type": {"type": "string", "enum": ["invoice", "receipt", "contract"]},
                            "amount": {"type": "number"},
                            "vendor_address": {"type": "string"}
                        },
                        "required": ["document_type", "amount", "vendor_address"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_crypto_price",
                    "description": "Fetches the current market price of a cryptocurrency (e.g. BTC, ETH, SOL, USDC).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "The crypto symbol or ID (e.g. btc, eth, solana)."}
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_dashboard_summary",
                    "description": "Provides global statistics about the Aurelius platform, including total runs and spend.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_agents_list",
                    "description": "Lists all active AI validator agents, their services, and their prices.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_requester_wallet_info",
                    "description": "Retrieves the main system wallet used by the orchestrator for payments.",
                    "parameters": {"type": "object", "properties": {}}
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
                        elif func_name == "bridge_usdc":
                            res = await bridge_usdc(**func_args)
                        elif func_name == "register_ai_agent":
                            res = await register_ai_agent(**func_args)
                        elif func_name == "create_agent_job":
                            res = await create_agent_job(**func_args)
                        elif func_name == "gateway_nanopayment":
                            res = await gateway_nanopayment(**func_args)
                        elif func_name == "get_crypto_price":
                            res = await get_crypto_price(**func_args)
                        elif func_name == "get_dashboard_summary":
                            res = await get_dashboard_summary()
                        elif func_name == "get_agents_list":
                            res = await get_agents_list()
                        elif func_name == "get_requester_wallet_info":
                            res = await get_requester_wallet_info()
                        else:
                            res = {"status": "error", "message": "Unknown tool"}
                            
                        return f"Tool Execution: {func_name} completed with result: {json.dumps(res)}"
                    return message.get("content", "")
                else:
                    logger.error(f"AI/ML API Error ({response.status_code}): {response.text}")
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

    async def analyze_multimodal_commerce(self, prompt: str, base64_image: str):
        """Analyzes a document using Gemini via AI/ML API (primary) or Google Direct (fallback)."""
        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        try:
            # 1. Try AI/ML API (Primary Choice for 2.0 and Quota Stability)
            if self.aiml_api_key:
                url = f"{self.aiml_base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.aiml_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "google/gemini-2.0-flash",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ]
                }
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"]
                    else:
                        logger.warning(f"AI/ML API Vision failed ({resp.status_code}): {resp.text}")
            
            # 2. Fallback to Google Direct
            if self.google_api_key:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={self.google_api_key}"
                    payload = {
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": "image/jpeg",
                                        "data": base64_image
                                    }
                                }
                            ]
                        }]
                    }
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        logger.error(f"Google Direct Vision failed: {resp.text}")

            return "Failed to analyze document. No valid API provider responded."
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return f"Error: {str(e)}"

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
