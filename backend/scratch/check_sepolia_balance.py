"""
Fund the ETH-SEPOLIA wallet with Sepolia USDC from the Circle faucet,
and check the balance.
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SEPOLIA_WALLET_ID = "758638cd-f47f-55ae-b2d7-2a57763a1cc5"
SEPOLIA_WALLET_ADDR = "0xa9d0fb5f1abd959714579994324b77c36b3c53af"
CIRCLE_API_KEY = os.environ.get("CIRCLE_API_KEY")
CIRCLE_API_URL = os.environ.get("CIRCLE_API_URL", "https://api.circle.com")

headers = {
    "Authorization": f"Bearer {CIRCLE_API_KEY}",
    "Content-Type": "application/json"
}

async def check_sepolia_balance():
    async with httpx.AsyncClient() as client:
        # Check wallet balance
        resp = await client.get(
            f"{CIRCLE_API_URL}/v1/w3s/wallets/{SEPOLIA_WALLET_ID}/balances",
            headers=headers
        )
        print("Sepolia Wallet Balance Status:", resp.status_code)
        print("Sepolia Wallet Balance:", resp.text[:500])
        
        # Check the ETH-SEPOLIA USDC token ID
        resp2 = await client.get(
            f"{CIRCLE_API_URL}/v1/w3s/tokens?blockchain=ETH-SEPOLIA",
            headers=headers
        )
        print("\nETH-SEPOLIA Tokens Status:", resp2.status_code)
        import json
        tokens = resp2.json().get("data", {}).get("tokens", [])
        for t in tokens:
            print(f"  {t.get('symbol')} -> id={t.get('id')} standard={t.get('standard')}")

if __name__ == "__main__":
    asyncio.run(check_sepolia_balance())
