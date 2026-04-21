import asyncio
import json
from app.services.circle_service import circle_service
from app.config import settings

async def audit_wallets():
    print(f"Auditing wallets on {settings.CIRCLE_API_URL}...")
    try:
        wallets = await circle_service.list_wallets()
        print(f"Found {len(wallets)} wallets:")
        for w in wallets:
            print(json.dumps(w, indent=2))
    except Exception as e:
        print(f"Audit failed: {e}")

if __name__ == "__main__":
    asyncio.run(audit_wallets())
