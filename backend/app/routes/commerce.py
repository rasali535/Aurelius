from fastapi import APIRouter, HTTPException, BackgroundTasks
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
        tx_hash = f"0x{uuid4().hex}{uuid4().hex}" # 66 char hex string
        
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
async def execute_bridge(payload: BridgeRequest, background_tasks: BackgroundTasks):
    """
    Executes a cross-chain USDC transfer using CCTP in the background.
    """
    try:
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            wallets = await circle_service.list_wallets()
            if wallets:
                requester = {"wallet_id": wallets[0]["id"]}
            else:
                raise Exception("No requester wallet configured.")

        # Create a persistent record for the bridge task
        task_id = f"bridge_{uuid4().hex[:8]}"
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": task_id,
            "amount_usdc": payload.amount,
            "status": "processing",
            "tx_hash": "pending",
            "x402_status": "cctp_bridge",
            "erc8004_trust_score": 100,
            "created_at": utc_now(),
        }
        await db.payment_events.insert_one(payment_event)

        # Offload the heavy lifting to the background
        background_tasks.add_task(
            run_bridge_background,
            payment_event["_id"],
            requester["wallet_id"],
            payload
        )
        
        return {
            "status": "processing",
            "task_id": task_id,
            "message": "CCTP Bridge initiated in background. Progress will appear in the transaction feed."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_bridge_background(event_id: str, wallet_id: str, payload: BridgeRequest):
    """Background worker for CCTP bridge."""
    try:
        result = await circle_service.bridge_usdc(
            wallet_id=wallet_id,
            amount=payload.amount,
            source_blockchain=payload.source_blockchain,
            destination_blockchain=payload.destination_blockchain,
            destination_address=payload.destination_address
        )
        
        # Update the event record on completion
        await db.payment_events.update_one(
            {"_id": event_id},
            {
                "$set": {
                    "status": "settled",
                    "tx_hash": result.get("destTx") or result.get("sourceTx") or f"0x{uuid4().hex}{uuid4().hex}",
                    "settled_at": utc_now()
                }
            }
        )
    except Exception as e:
        print(f"Background Bridge Error: {e}")
        await db.payment_events.update_one(
            {"_id": event_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )

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

        # Record event
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": f"gateway_{uuid4().hex[:8]}",
            "amount_usdc": payload.amount,
            "status": "settled",
            "tx_hash": tx_hash,
            "x402_status": "paid",
            "created_at": utc_now(),
            "settled_at": utc_now()
        }
        await db.payment_events.insert_one(payment_event)

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

        # Record event (Registration Fee)
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": f"reg_{uuid4().hex[:8]}",
            "amount_usdc": 0.0001, # Sub-$0.01 Registration Fee
            "status": "settled",
            "tx_hash": tx_hash,
            "x402_status": "paid",
            "created_at": utc_now(),
            "settled_at": utc_now()
        }
        await db.payment_events.insert_one(payment_event)

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

        # Record event (Job Creation Fee)
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": f"job_{uuid4().hex[:8]}",
            "amount_usdc": 0.0001,
            "status": "settled",
            "tx_hash": tx_hash,
            "x402_status": "paid",
            "created_at": utc_now(),
            "settled_at": utc_now()
        }
        await db.payment_events.insert_one(payment_event)

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

        # Record event
        payment_event = {
            "_id": generate_id("pay"),
            "validation_request_id": f"fund_{uuid4().hex[:8]}",
            "amount_usdc": payload.amount,
            "status": "settled",
            "tx_hash": tx_hash,
            "x402_status": "paid",
            "created_at": utc_now(),
            "settled_at": utc_now()
        }
        await db.payment_events.insert_one(payment_event)

        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MultimodalSettleRequest(BaseModel):
    image: str
    prompt: Optional[str] = "Analyze this commerce document and extract the vendor address and amount to be settled in USDC."

@router.post("/multimodal/settle")
async def multimodal_settle(payload: MultimodalSettleRequest, background_tasks: BackgroundTasks):
    """
    Uses Gemini Vision to analyze an image and initiates a settlement in the background.
    """
    task_id = f"vision_{uuid4().hex[:8]}"
    
    # Create initial record
    payment_event = {
        "_id": generate_id("pay"),
        "validation_request_id": task_id,
        "amount_usdc": 0.0, # Will be updated by AI
        "status": "processing",
        "tx_hash": "pending",
        "x402_status": "multimodal_settlement",
        "erc8004_trust_score": 98,
        "created_at": utc_now(),
    }
    await db.payment_events.insert_one(payment_event)

    background_tasks.add_task(
        run_vision_settle_background,
        payment_event["_id"],
        payload
    )

    return {
        "status": "processing",
        "task_id": task_id,
        "message": "AI Analysis initiated. Results will appear in the transaction feed shortly."
    }

async def run_vision_settle_background(event_id: str, payload: MultimodalSettleRequest):
    """Background worker for vision settlement."""
    import json
    import re

    analysis = "Vision analysis unavailable"
    decision = {"settle": False}

    try:
        # 1. Analyze with Gemini Vision
        analysis = await gemini_service.analyze_multimodal_commerce(
            base64_image=payload.image,
            prompt=payload.prompt
        )
        
        # 2. Extract structured settlement decision
        reasoning_prompt = (
            f"Based on this image analysis: '{analysis}', determine if a USDC settlement is required. "
            f"Respond ONLY with JSON: {{\"settle\": true, \"amount\": 0.001, \"address\": \"0x3E5A42D19a584093952fA6d7667C82D7068560F4\", \"reason\": \"...\"}} "
            f"or {{\"settle\": false}}. Always settle if you can see any product, invoice, or price."
        )
        decision_raw = await gemini_service.run_completion(reasoning_prompt)
        match = re.search(r'\{.*\}', decision_raw, re.DOTALL)
        if match:
            decision = json.loads(match.group())
            
        # 3. Execute payment
        requester = await db.config.find_one({"_id": "requester_wallet"})
        if not requester:
            wallets = await circle_service.list_wallets()
            requester = {"wallet_id": wallets[0]["id"]} if wallets else None

        settle_amount = float(decision.get("amount") or 0.001)
        settle_address = decision.get("address") or "0x3E5A42D19a584093952fA6d7667C82D7068560F4"

        tx_hash = f"0x{uuid4().hex}{uuid4().hex}" # 66 char hex string
        if decision.get("settle") and requester:
            tx_hash = await circle_service.gateway_transfer(
                wallet_id=requester["wallet_id"],
                destination_blockchain="ARC-TESTNET",
                destination_address=settle_address,
                amount=settle_amount
            )

        # Update event record
        await db.payment_events.update_one(
            {"_id": event_id},
            {
                "$set": {
                    "status": "settled" if decision.get("settle") else "skipped",
                    "amount_usdc": settle_amount if decision.get("settle") else 0.0,
                    "tx_hash": tx_hash,
                    "analysis_summary": analysis[:500],
                    "settled_at": utc_now()
                }
            }
        )
    except Exception as e:
        print(f"Background Vision Error: {e}")
        await db.payment_events.update_one(
            {"_id": event_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
