from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.circle_service import circle_service
from app.db import db
from app.services.gemini_service import gemini_service
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
        # Mocking the swap logic for the demo
        tx_hash = f"0x_swap_{uuid4().hex}"
        
        # In a real scenario, this would call Circle's smart contract or a DEX aggregator
        # For now, we'll just log it and return success
        print(f"SWAP: {payload.amount} {payload.from_token} -> {payload.to_token}")
        
        return {
            "status": "success", 
            "tx_hash": tx_hash,
            "received_amount": payload.amount * 0.995, # Mock 0.5% slippage/fee
            "from_token": payload.from_token,
            "to_token": payload.to_token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
