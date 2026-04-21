import asyncio
import json
import httpx
from app.config import settings

async def audit_wallet_sets():
    print(f"Auditing wallet sets on {settings.CIRCLE_API_URL}...")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.CIRCLE_API_KEY}"
    }
    url = f"{settings.CIRCLE_API_URL}/v1/w3s/walletSets"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                sets = resp.json()["data"]["walletSets"]
                print(f"Found {len(sets)} wallet sets:")
                for s in sets:
                    print(f"Set ID: {s['id']} | Name: {s['name']}")
                    # List wallets for this set
                    w_url = f"{settings.CIRCLE_API_URL}/v1/w3s/developer/wallets?walletSetId={s['id']}"
                    w_resp = await client.get(w_url, headers=headers)
                    if w_resp.status_code == 200:
                        wallets = w_resp.json()["data"]["wallets"]
                        for w in wallets:
                            print(f"  Wallet ID: {w['id']} | Address: {w['address']}")
            else:
                print(f"Error: {resp.text}")
        except Exception as e:
            print(f"Audit failed: {e}")

if __name__ == "__main__":
    asyncio.run(audit_wallet_sets())
