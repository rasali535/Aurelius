from fastapi import APIRouter
from app.db import db

router = APIRouter()

@router.get("/dashboard/summary")
async def dashboard_summary():
    try:
        total_prompt_runs = await db.prompt_runs.count_documents({})
        total_validations = await db.validation_requests.count_documents({})
        total_payments = await db.payment_events.count_documents({})
        
        payments = await db.payment_events.find(
            {"amount_usdc": {"$gt": 0}}, 
            {"_id": 1, "amount_usdc": 1, "status": 1, "tx_hash": 1, "settled_at": 1}
        ).sort("settled_at", -1).limit(20).to_list(length=20)

        _agg_cursor = db.payment_events.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$amount_usdc"}}}
        ])
        total_spend_pipeline = await _agg_cursor.to_list(length=1)
        total_spend_usdc = total_spend_pipeline[0]["total"] if total_spend_pipeline else 0.0

        for p in payments:
            if "_id" in p:
                p["id"] = str(p.pop("_id"))
            elif "id" in p:
                p["_id"] = p["id"]

        requester_wallet = await db.config.find_one({"_id": "requester_wallet"})
        wallet_address = requester_wallet.get("wallet_address") if requester_wallet else "0x_NOT_CONFIGURED"
        wallet_id = requester_wallet.get("wallet_id") if requester_wallet else "NONE"

        return {
            "total_prompt_runs": total_prompt_runs,
            "total_validations": total_validations,
            "total_payments": total_payments,
            "total_spend_usdc": round(total_spend_usdc, 6),
            "latest_transactions": payments,
            "wallet_address": wallet_address,
            "wallet_id": wallet_id
        }
    except Exception as e:
        print(f"Dashboard summary error: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Database error in summary")

@router.get("/dashboard/validators")
async def dashboard_validators():
    try:
        items = await db.validation_requests.find({}).sort("created_at", -1).limit(50).to_list(length=50)
        for item in items:
            item["id"] = str(item.pop("_id"))
        return items
    except Exception as e:
        print(f"Dashboard validators error: {e}")
        return []
