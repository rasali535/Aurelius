from fastapi import APIRouter
from app.db import db

router = APIRouter()

@router.get("/dashboard/summary")
async def dashboard_summary():
    total_prompt_runs = db.prompt_runs.count_documents({})
    total_validations = db.validation_requests.count_documents({})
    total_payments = db.payment_events.count_documents({})
    
    payments = list(db.payment_events.find(
        {}, 
        {"_id": 1, "amount_usdc": 1, "status": 1, "tx_hash": 1, "settled_at": 1}
    ).sort("settled_at", -1).limit(20))

    total_spend_pipeline = list(db.payment_events.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount_usdc"}}}
    ]))
    total_spend_usdc = total_spend_pipeline[0]["total"] if total_spend_pipeline else 0.0

    for p in payments:
        p["id"] = str(p.pop("_id"))

    return {
        "total_prompt_runs": total_prompt_runs,
        "total_validations": total_validations,
        "total_payments": total_payments,
        "total_spend_usdc": round(total_spend_usdc, 6),
        "latest_transactions": payments,
    }

@router.get("/dashboard/validators")
async def dashboard_validators():
    items = list(db.validation_requests.find({}).sort("created_at", -1).limit(50))
    for item in items:
        item["id"] = str(item.pop("_id"))
    return items
