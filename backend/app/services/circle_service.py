import httpx
import uuid
import time
import asyncio
from app.config import settings

class CircleService:
    def __init__(self):
        self.api_key = settings.CIRCLE_API_KEY
        self.base_url = settings.CIRCLE_API_URL
        self.entity_secret_ciphertext = settings.CIRCLE_ENTITY_SECRET_CIPHERTEXT
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def create_wallet_set(self, name: str):
        """Creates a new Wallet Set for developer-controlled wallets."""
        url = f"{self.base_url}/v1/developer/walletSets"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "name": name,
            "entitySecretCiphertext": self.entity_secret_ciphertext
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()["data"]["walletSet"]

    async def create_wallets(self, wallet_set_id: str, count: int = 1, blockchain: str = "ARC-TESTNET"):
        """Creates Developer-Controlled wallets in a wallet set."""
        url = f"{self.base_url}/v1/developer/wallets"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletSetId": wallet_set_id,
            "blockchain": blockchain,
            "count": count,
            "entitySecretCiphertext": self.entity_secret_ciphertext
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()["data"]["wallets"]

    async def sign_typed_data(self, wallet_id: str, typed_data: dict):
        """Signs EIP-712 typed data using the developer signing API with polling."""
        url = f"{self.base_url}/v1/developer/sign/typedData"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletId": wallet_id,
            "data": typed_data,
            "entitySecretCiphertext": self.entity_secret_ciphertext
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()
            job_id = resp.json()["data"]["id"]
            
            # Poll for the signature result
            status_url = f"{self.base_url}/v1/developer/transactions/{job_id}"
            max_attempts = 30
            for _ in range(max_attempts):
                status_resp = await client.get(status_url, headers=self.headers)
                status_resp.raise_for_status()
                data = status_resp.json()["data"]["transaction"]
                
                if data["status"] == "COMPLETE":
                    return data["signature"]
                elif data["status"] == "FAILED":
                    raise Exception(f"Signing failed: {data.get('errorMessage', 'Unknown error')}")
                
                await asyncio.sleep(1) # Wait 1 second before polling again
            
            raise Exception("Signing timed out after 30 seconds")

circle_service = CircleService()
