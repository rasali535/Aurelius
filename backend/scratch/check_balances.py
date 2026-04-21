import asyncio
import httpx
from app.services.circle_service import circle_service
from app.config import settings

async def check_balances():
    print(f"Checking balances on {settings.CIRCLE_API_URL}...")
    try:
        wallets = await circle_service.list_wallets()
        print(f"Found {len(wallets)} wallets. Fetching balances...")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.CIRCLE_API_KEY}"
        }
        
        for w in wallets:
            url = f"{settings.CIRCLE_API_URL}/v1/w3s/wallets/{w['id']}/balances"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    balances = resp.json()["data"]["tokenBalances"]
                    print(f"Wallet ID: {w['id']} | Address: {w['address']}")
                    if not balances:
                        print("  (Empty)")
                    for b in balances:
                        print(f"  - {b['amount']} {b['token']['symbol']} ({b['token']['blockchain']})")
                else:
                    print(f"  Error fetching balance for {w['id']}: {resp.text}")
    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_balances())
