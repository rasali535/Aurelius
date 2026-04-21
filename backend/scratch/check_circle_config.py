import asyncio
import httpx
from app.config import settings

async def check_config():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.CIRCLE_API_KEY}"
    }
    
    urls = [
        "https://api.circle.com/v1/w3s/config/entity",
        "https://api-sandbox.circle.com/v1/w3s/config/entity"
    ]
    
    for url in urls:
        print(f"Checking {url}...")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers)
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Response: {resp.text}")
                else:
                    print(f"  Error: {resp.text}")
            except Exception as e:
                print(f"  Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_config())
