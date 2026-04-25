import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def check_allowance():
    # Sepolia Wallet
    wallet_id = "758638cd-f47f-55ae-b2d7-2a57763a1cc5"
    usdc_address = "0x1c7d4b196cb0c7b01d743fbc6116a902379c7238"
    token_messenger = "0x8fe6b999dc680ccfdd5bf7eb0974218be2542daa"
    
    api_key = os.getenv("CIRCLE_API_KEY")
    # Circle doesn't have a direct "allowance" API, but we can check if a contract execution for allowance would work
    # or just look at the wallet's transaction history to see if the approve was successful.
    
    url = f"https://api.circle.com/v1/w3s/wallets/{wallet_id}/transactions?blockchain=ETH-SEPOLIA&pageSize=5"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(check_allowance())
