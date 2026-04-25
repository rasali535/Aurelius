import asyncio
from app.services.circle_service import CircleService

async def main():
    s = CircleService()
    try:
        # Check source wallet mapping
        source_id = await s.get_wallet_id_for_chain('d38ee612-64a3-501e-be68-a55019fce9b1', 'ETH-SEPOLIA')
        print("ETH-SEPOLIA wallet id:", source_id)
        
        # What wallets does it have?
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{s.base_url}/v1/w3s/wallets/d38ee612-64a3-501e-be68-a55019fce9b1", headers=s.headers)
            wallet_set_id = resp.json()["data"]["wallet"]["walletSetId"]
            print("WalletSet ID:", wallet_set_id)
            
            resp = await client.get(f"{s.base_url}/v1/w3s/wallets", params={"walletSetId": wallet_set_id}, headers=s.headers)
            print("Wallets:", [w["blockchain"] for w in resp.json()["data"]["wallets"]])
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
