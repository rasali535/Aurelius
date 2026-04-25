import asyncio
import json
from app.services.circle_service import CircleService

async def main():
    s = CircleService()
    try:
        tx = await s.gateway_transfer('d38ee612-64a3-501e-be68-a55019fce9b1', 'ARC-TESTNET', '0x3E5A42D19a584093952fA6d7667C82D7068560F4', 0.001)
        print("Success:", tx)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
