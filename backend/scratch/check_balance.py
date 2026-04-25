import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def check_balance():
    wallet_id = "758638cd-f47f-55ae-b2d7-2a57763a1cc5"
    api_key = os.getenv("CIRCLE_API_KEY")
    url = f"https://api.circle.com/v1/w3s/wallets/{wallet_id}/balances"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(check_balance())
