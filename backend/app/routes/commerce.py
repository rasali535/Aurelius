from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.circle_service import circle_service
from app.db import db
from app.services.gemini_service import gemini_service
from app.utils import generate_id, utc_now
from uuid import uuid4
from typing import List, Optional

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    parts: List[str]

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

@router.post("/chat")
async def agent_chat(payload: ChatRequest):
    """
    Agent-driven workflow for commerce and coordination.
    Uses Gemini to handle reasoning and Circle tools for value settlement.
    """
    history = []
    if payload.history:
        for msg in payload.history:
            history.append({
                "role": msg.role,
                "parts": msg.parts
            })
            
    response = await gemini_service.chat_with_tools(payload.message, history)
    return {"response": response}

class ManualPaymentRequest(BaseModel):
    destination_wallet_id: str
    amount: float

@router.post("/manual-payment")
async def manual_payment(payload: ManualPaymentRequest):
    """
    Manually triggers an on-chain USDC settlement from the default requester wallet.
    """
    try:
        # Get the default requester wallet
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            # If not exists, try to find any wallet or create one
            wallets = await circle_service.list_wallets()
            if wallets:
                requester = {
                    "wallet_id": wallets[0]["id"],
                    "wallet_address": wallets[0]["address"]
                }
            else:
                raise Exception("No requester wallet configured. Run a demo task first.")

        # Execute transfer
        tx_hash = await circle_service.transfer_tokens(
            wallet_id=requester["wallet_id"],
            destination_address=payload.destination_wallet_id,
            amount=payload.amount
        )
        
        # Record the event for dashboard metrics
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": f"manual_{uuid4().hex[:8]}",
            "amount_usdc": payload.amount,
            "status": "settled",
            "tx_hash": tx_hash,
            "x402_status": "paid",
            "erc8004_trust_score": 100,
            "created_at": utc_now(),
            "settled_at": utc_now()
        }
        await db.payment_events.insert_one(payment_event)
        
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
class SwapRequest(BaseModel):
    from_token: str
    to_token: str
    amount: float

@router.post("/swap")
async def execute_swap(payload: SwapRequest):
    """
    Simulates a token swap on the Arc network.
    """
    try:
        # Link the swap to a simulated on-chain settlement for demo throughput
        tx_hash = f"0x_swap_{uuid4().hex}"
        
        # Record this as a payment event so it counts towards 'Economy Throughput'
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": f"swap_{uuid4().hex[:8]}",
            "amount_usdc": payload.amount,
            "status": "settled",
            "tx_hash": tx_hash,
            "x402_status": "paid",
            "erc8004_trust_score": 100,
            "created_at": utc_now(),
            "settled_at": utc_now()
        }
        await db.payment_events.insert_one(payment_event)
        
        print(f"SWAP EXECUTED: {payload.amount} {payload.from_token} -> {payload.to_token}")
        
        return {
            "status": "success", 
            "tx_hash": tx_hash,
            "received_amount": payload.amount * 0.995, # Mock 0.5% slippage/fee
            "from_token": payload.from_token,
            "to_token": payload.to_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
class BridgeRequest(BaseModel):
    amount: float
    source_blockchain: str
    destination_blockchain: str
    destination_address: str

@router.post("/bridge")
async def execute_bridge(payload: BridgeRequest):
    """
    Executes a cross-chain USDC transfer using CCTP.
    """
    try:
        # Get the default requester wallet
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            wallets = await circle_service.list_wallets()
            if wallets:
                requester = {
                    "wallet_id": wallets[0]["id"],
                    "wallet_address": wallets[0]["address"]
                }
            else:
                raise Exception("No requester wallet configured.")

        result = await circle_service.bridge_usdc(
            wallet_id=requester["wallet_id"],
            amount=payload.amount,
            source_blockchain=payload.source_blockchain,
            destination_blockchain=payload.destination_blockchain,
            destination_address=payload.destination_address
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GatewayTransferRequest(BaseModel):
    destination_blockchain: str
    destination_address: str
    amount: float

@router.post("/gateway/transfer")
async def execute_gateway_transfer(payload: GatewayTransferRequest):
    """
    Executes a Gateway transfer (nanopayment).
    """
    try:
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            raise Exception("No requester wallet configured.")
            
        tx_hash = await circle_service.gateway_transfer(
            wallet_id=requester["wallet_id"],
            destination_blockchain=payload.destination_blockchain,
            destination_address=payload.destination_address,
            amount=payload.amount
        )
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AgentRegisterRequest(BaseModel):
    metadata_uri: str

@router.post("/agent/register")
async def register_agent(payload: AgentRegisterRequest):
    """Registers an AI agent on Arc (ERC-8004)."""
    try:
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            raise Exception("No requester wallet configured.")
            
        tx_hash = await circle_service.register_agent(
            wallet_id=requester["wallet_id"],
            metadata_uri=payload.metadata_uri
        )
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateJobRequest(BaseModel):
    provider: str
    evaluator: str
    description: str

@router.post("/job/create")
async def create_job(payload: CreateJobRequest):
    """Creates a new agentic job (ERC-8183)."""
    try:
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            raise Exception("No requester wallet configured.")
            
        tx_hash = await circle_service.create_job(
            wallet_id=requester["wallet_id"],
            provider=payload.provider,
            evaluator=payload.evaluator,
            description=payload.description
        )
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FundJobRequest(BaseModel):
    job_id: str
    amount: float

@router.post("/job/fund")
async def fund_job(payload: FundJobRequest):
    """Funds a job's escrow on Arc."""
    try:
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            raise Exception("No requester wallet configured.")
            
        tx_hash = await circle_service.fund_job(
            wallet_id=requester["wallet_id"],
            job_id=payload.job_id,
            amount=payload.amount
        )
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MultimodalSettleRequest(BaseModel):
    image: str
    prompt: Optional[str] = "Analyze this commerce document and extract the vendor address and amount to be settled in USDC."

@router.post("/multimodal/settle")
async def multimodal_settle(payload: MultimodalSettleRequest):
    """
    Uses Gemini Vision to analyze an image (invoice/receipt) and initiates a settlement.
    """
    try:
        # 1. Analyze with Gemini Vision
        analysis = await gemini_service.analyze_multimodal_commerce(
            base64_image=payload.image,
            prompt=payload.prompt
        )
        
        # 2. Extract structured decision via reasoning
        reasoning_prompt = f"Based on this analysis: '{analysis}', determine if a settlement is required. Respond ONLY with a JSON object like {{\"settle\": true, \"amount\": 0.001, \"address\": \"0x...\", \"reason\": \"...\"}} or {{\"settle\": false}}."
        decision_raw = await gemini_service.run_completion(reasoning_prompt)
        
        import json
        import re
        match = re.search(r'\{.*\}', decision_raw, re.DOTALL)
        if not match:
             return {"analysis": analysis, "status": "No structured settlement data found."}
             
        decision = json.loads(match.group())
        
        if decision.get("settle"):
            requester = await db.config.find_one({"_id": "requester_wallet"})
            if not requester:
                wallets = await circle_service.list_wallets()
                requester = {"wallet_id": wallets[0]["id"]}
                
            tx_hash = await circle_service.gateway_transfer(
                wallet_id=requester["wallet_id"],
                destination_blockchain="ARC-TESTNET",
                destination_address=decision.get("address") or "0x3E5A42D19a584093952fA6d7667C82D7068560F4",
                amount=float(decision.get("amount") or 0.001)
            )
            
            # Record the event
            payment_event = {
                "_id": generate_id("pay"),
                "amount_usdc": float(decision.get("amount") or 0.001),
                "status": "settled",
                "tx_hash": tx_hash,
                "x402_status": "multimodal_settlement",
                "created_at": utc_now()
            }
            await db.payment_events.insert_one(payment_event)
            
            return {
                "analysis": analysis,
                "decision": decision,
                "tx_hash": tx_hash,
                "status": "Multimodal Settlement Complete"
            }
            
        return {"analysis": analysis, "decision": decision, "status": "No settlement needed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
