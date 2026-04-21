import asyncio
from app.db import init_db, db

async def seed_config():
    initialized_db = await init_db()
    db.set_db(initialized_db)
    
    # Existing set IDs found in audit
    requester_set = "9bd61386-3d84-5c7b-b0d9-c673339a1072"
    validator_set = "f9256fab-063f-5b64-85c4-de2aca7a27c1"
    
    print(f"Seeding DB config with existing Circle sets...")
    
    # Clean up existing to force use of these
    await db.config.delete_many({"_id": {"$in": ["circle_requester_wallet_set", "circle_validator_wallet_set"]}})
    
    await db.config.insert_one({"_id": "circle_requester_wallet_set", "id": requester_set})
    await db.config.insert_one({"_id": "circle_validator_wallet_set", "id": validator_set})
    
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_config())
