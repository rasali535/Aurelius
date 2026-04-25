"""
Fund the ETH-SEPOLIA wallet via Circle testnet faucet.
Circle provides faucets at: https://faucet.circle.com
We'll also try the Alchemy / Infura Sepolia faucet via HTTP.

Since we can't automate the Google faucet, let's at minimum:
1. Show the wallet address to fund manually
2. Try Circle's developer faucet API endpoint if available
"""
import asyncio
import httpx
import os
import uuid
from dotenv import load_dotenv
from app.services.circle_service import CircleService

load_dotenv()

SEPOLIA_WALLET_ADDR = "0xa9d0fb5f1abd959714579994324b77c36b3c53af"
CIRCLE_API_KEY = os.environ.get("CIRCLE_API_KEY")
CIRCLE_API_URL = os.environ.get("CIRCLE_API_URL", "https://api.circle.com")

headers = {
    "Authorization": f"Bearer {CIRCLE_API_KEY}",
    "Content-Type": "application/json"
}

async def fund_via_faucet():
    """Try Circle's sandbox/testnet faucet endpoint"""
    async with httpx.AsyncClient() as client:
        # Circle has a faucet endpoint for testnet
        payload = {
            "address": SEPOLIA_WALLET_ADDR,
            "blockchain": "ETH-SEPOLIA",
            "nativeToken": True
        }
        resp = await client.post(
            f"{CIRCLE_API_URL}/v1/faucet/drips",
            json=payload,
            headers=headers
        )
        print(f"Faucet (native ETH) Status: {resp.status_code}")
        print(f"Faucet Response: {resp.text}")
        
        # Also try USDC drip
        payload2 = {
            "address": SEPOLIA_WALLET_ADDR,
            "blockchain": "ETH-SEPOLIA",
            "nativeToken": False,
            "usdc": True
        }
        resp2 = await client.post(
            f"{CIRCLE_API_URL}/v1/faucet/drips",
            json=payload2,
            headers=headers
        )
        print(f"\nFaucet (USDC) Status: {resp2.status_code}")
        print(f"Faucet Response: {resp2.text}")

async def transfer_usdc_from_arc_to_sepolia_wallet():
    """
    Since CCTP bridge is the issue, let's try to send SepoliaUSDC
    directly from Circle testnet via developer transfer API.
    """
    s = CircleService()
    
    # First check what USDC token ID is for ETH-SEPOLIA
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{CIRCLE_API_URL}/v1/w3s/tokens",
            headers=headers,
            params={"blockchain": "ETH-SEPOLIA", "includeAll": True}
        )
        print(f"\nAll Tokens Status: {resp.status_code}")
        print(f"Tokens: {resp.text[:1000]}")

if __name__ == "__main__":
    print(f">>> ETH-SEPOLIA wallet address: {SEPOLIA_WALLET_ADDR}")
    print(">>> Please fund with Sepolia ETH from: https://sepoliafaucet.com")
    print(">>> Please fund with Sepolia USDC from: https://faucet.circle.com")
    print()
    asyncio.run(fund_via_faucet())
    asyncio.run(transfer_usdc_from_arc_to_sepolia_wallet())
