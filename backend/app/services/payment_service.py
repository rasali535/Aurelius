from app.utils import generate_id, utc_now

def create_payment_event(db, validation_request_id: str, amount_usdc: float):
    payment_id = generate_id("pay")
    payment_doc = {
        "_id": payment_id,
        "validation_request_id": validation_request_id,
        "amount_usdc": amount_usdc,
        "status": "challenge_issued",
        "tx_hash": None,
        "x402_status": "payment_required",
        "created_at": utc_now(),
        "settled_at": None,
    }
    db.payment_events.insert_one(payment_doc)
    return payment_doc

def settle_payment(db, payment_id: str):
    fake_tx_hash = f"0x{payment_id[-10:]}abc123"
    db.payment_events.update_one(
        {"_id": payment_id},
        {
            "$set": {
                "status": "settled",
                "x402_status": "paid",
                "tx_hash": fake_tx_hash,
                "settled_at": utc_now(),
            }
        },
    )
    return db.payment_events.find_one({"_id": payment_id})
