import asyncio
import httpx
from app.config import settings

async def probe_endpoints():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.CIRCLE_API_KEY}"
    }
    
    variations = [
        "v1/w3s/walletSets",
        "v1/w3s/developer/walletSets",
        "v1/w3s/wallets",
        "v1/w3s/developer/wallets"
    ]
    
    for v in variations:
        url = f"{settings.CIRCLE_API_URL}/{v}"
        print(f"Probing {url}...")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  SUCCESS! Found {len(resp.json().get('data', {}).get('wallets', []))} items (if wallets)")

if __name__ == "__main__":
    asyncio.run(probe_endpoints())
