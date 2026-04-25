import asyncio
import json
from app.services.circle_service import CircleService
async def main():
    s = CircleService()
    wallets = await s.list_wallets()
    print(json.dumps(wallets, indent=2))
if __name__ == "__main__":
    asyncio.run(main())
