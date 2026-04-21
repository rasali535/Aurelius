import asyncio
import httpx
from app.services.circle_service import circle_service
from app.config import settings

async def check_detailed_balance(wallet_id):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.CIRCLE_API_KEY}"
    }
    url = f"{settings.CIRCLE_API_URL}/v1/w3s/wallets/{wallet_id}/balances"
    print(f"Checking wallet {wallet_id}...")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()["data"]
            balances = data.get("tokenBalances", [])
            print(f"Found {len(balances)} tokens:")
            for b in balances:
                print(f"  - {b['amount']} {b['token']['symbol']} on {b['token']['blockchain']}")
        else:
            print(f"  Error: {resp.text}")

async def main():
    # The wallet ID inside the set 9bd6...
    wallet_id = "d38ee612-64a3-501e-be68-a55019fce9b1"
    await check_detailed_balance(wallet_id)

if __name__ == "__main__":
    asyncio.run(main())
