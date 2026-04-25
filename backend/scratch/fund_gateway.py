import asyncio
import os
from app.services.circle_service import CircleService
from app.db import db
from dotenv import load_dotenv

load_dotenv()

async def fund_gateway():
    from app.db import init_db
    database = await init_db()
    db.set_db(database)
    print("Database connected.")
    circle_service = CircleService()
    
    requester = await db.config.find_one({"_id": "requester_wallet"})
    if not requester:
        wallets = await circle_service.list_wallets()
        if wallets:
            requester = {
                "wallet_id": wallets[0]["id"],
                "wallet_address": wallets[0]["address"]
            }
            await db.config.update_one(
                {"_id": "requester_wallet"},
                {"$set": requester},
                upsert=True
            )
        else:
            print("No wallets found")
            return

    wallet_id = requester["wallet_id"]
    print(f"Using wallet ID: {wallet_id}")
    
    amount = 5.0
    print(f"Depositing {amount} USDC to Gateway...")
    try:
        tx_hash = await circle_service.gateway_deposit(wallet_id, amount)
        print(f"Gateway deposit successful! TX: {tx_hash}")
    except Exception as e:
        print(f"Error during deposit: {e}")

if __name__ == "__main__":
    asyncio.run(fund_gateway())
