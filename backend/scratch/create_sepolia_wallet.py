import asyncio
import os
from dotenv import load_dotenv
from app.services.circle_service import CircleService
import httpx
import uuid

load_dotenv()

async def create_sepolia_wallet():
    s = CircleService()
    async with httpx.AsyncClient() as client:
        # Generate idempotent key
        idempotency_key = str(uuid.uuid4())
        
        # The Wallet Set ID we found:
        wallet_set_id = "9bd61386-3d84-5c7b-b0d9-c673339a1072"
        
        payload = {
            "idempotencyKey": idempotency_key,
            "blockchains": ["ETH-SEPOLIA"],
            "count": 1,
            "walletSetId": wallet_set_id,
            "entitySecretCiphertext": s._get_ciphertext()
        }
        
        resp = await client.post(
            f"{s.base_url}/v1/w3s/developer/wallets", 
            headers=s.headers, 
            json=payload
        )
        print("Create Wallet Status:", resp.status_code)
        print("Create Wallet Response:", resp.text)

if __name__ == "__main__":
    asyncio.run(create_sepolia_wallet())
