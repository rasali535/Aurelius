import httpx
import uuid
import time
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

    async def create_wallets(self, wallet_set_id: str, count: int = 1, blockchain: str = "AVAX-FUJI"):
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
        """Signs EIP-712 typed data using the developer signing API."""
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
            # This returns a signing job ID; we may need to poll for the result
            return resp.json()["data"]["signature"]

circle_service = CircleService()
