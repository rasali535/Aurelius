import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.services.circle_service import circle_service

async def main():
    try:
        wallet_set = await circle_service.create_wallet_set("TestSet-Bridge")
        wallets = await circle_service.create_wallets(wallet_set["id"], 1, "ARC-TESTNET")
        wallet_id = wallets[0]["id"]
        print(f"Created wallet: {wallet_id}")
        
        destination_address = "0xff17858f41588ec02b7daa20573bd2ac4dc42e7e"
        amount = 1.0
        
        print("Calling gateway_transfer...")
        tx = await circle_service.gateway_transfer(wallet_id, "ETH-SEPOLIA", destination_address, amount)
        print(f"Result: {tx}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
