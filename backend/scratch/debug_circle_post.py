import asyncio
import os
import httpx
import uuid
from dotenv import load_dotenv

load_dotenv()

async def test_post():
    api_key = os.getenv("CIRCLE_API_KEY")
    url = "https://api.circle.com/v1/w3s/developer/transactions/contractExecution"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple approve call to see response structure
    payload = {
        "idempotencyKey": str(uuid.uuid4()),
        "walletId": "758638cd-f47f-55ae-b2d7-2a57763a1cc5", # Sepolia
        "contractAddress": "0x1c7d4b196cb0c7b01d743fbc6116a902379c7238", # USDC
        "abiFunctionSignature": "approve(address,uint256)",
        "abiParameters": ["0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA", "1000"],
        "entitySecretCiphertext": os.getenv("CIRCLE_ENTITY_SECRET_CIPHERTEXT"),
        "feeLevel": "LOW"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(test_post())
