import httpx
import uuid
import time
import asyncio
import base64
import codecs
import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from app.config import settings

class CircleService:
    def __init__(self):
        self.api_key = settings.CIRCLE_API_KEY
        self.base_url = settings.CIRCLE_API_URL
        self.entity_secret = settings.CIRCLE_ENTITY_SECRET
        self.public_key_pem = settings.CIRCLE_ENTITY_PUBLIC_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # Support for Modular SDK KIT_KEY
        if self.api_key.startswith("KIT_KEY:"):
            self.headers["X-Kit-Key"] = self.api_key
        else:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _get_ciphertext(self):
        """Generates a fresh ciphertext for the entity secret using the public key."""
        if not self.entity_secret or not self.public_key_pem:
            return settings.CIRCLE_ENTITY_SECRET_CIPHERTEXT
            
        pub_key = serialization.load_pem_public_key(self.public_key_pem.encode())
        ciphertext = pub_key.encrypt(
            bytes.fromhex(self.entity_secret),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(ciphertext).decode()

    async def create_wallet_set(self, name: str):
        url = f"{self.base_url}/v1/w3s/developer/walletSets"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "name": name,
            "entitySecretCiphertext": self._get_ciphertext()
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in create_wallet_set: {resp.text}")
            resp.raise_for_status()
            return resp.json()["data"]["walletSet"]

    async def create_wallets(self, wallet_set_id: str, count: int = 1, blockchain: str = "ARC-TESTNET"):
        url = f"{self.base_url}/v1/w3s/developer/wallets"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletSetId": wallet_set_id,
            "blockchains": [blockchain],
            "count": count,
            "entitySecretCiphertext": self._get_ciphertext()
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in create_wallets: {resp.text}")
            resp.raise_for_status()
            return resp.json()["data"]["wallets"]

    async def get_wallet_address(self, wallet_id: str):
        url = f"{self.base_url}/v1/w3s/developer/wallets/{wallet_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in get_wallet_address: {resp.text}")
            resp.raise_for_status()
            return resp.json()["data"]["wallet"]["address"]

    async def sign_typed_data(self, wallet_id: str, typed_data: dict):
        url = f"{self.base_url}/v1/w3s/developer/sign/typedData"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletId": wallet_id,
            "data": json.dumps(typed_data),
            "entitySecretCiphertext": self._get_ciphertext()
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in sign_typed_data: {resp.text}")
            resp.raise_for_status()
            
            data = resp.json().get("data", {})
            job_id = data.get("id")
            if not job_id:
                print(f"WARNING: No 'id' in Circle sign response. data keys: {list(data.keys())}")
                # For some SDK versions/endpoints, it might be returned directly
                if "signature" in data: return data["signature"]
                raise KeyError(f"Circle API response missing 'id' for job tracking. Full response: {resp.json()}")

            # Poll for the signature result
            status_url = f"{self.base_url}/v1/w3s/developer/transactions/{job_id}"
            max_attempts = 30
            for _ in range(max_attempts):
                status_resp = await client.get(status_url, headers=self.headers)
                status_resp.raise_for_status()
                tx_data = status_resp.json()["data"]["transaction"]
                
                if tx_data["status"] == "COMPLETE":
                    return tx_data["signature"]
                elif tx_data["status"] == "FAILED":
                    raise Exception(f"Signing failed: {tx_data.get('errorMessage', 'Unknown error')}")
                
                await asyncio.sleep(1)
            
            raise Exception("Signing timed out after 30 seconds")

    async def transfer_tokens(self, wallet_id: str, destination_address: str, amount: float, blockchain: str = "ARC-TESTNET"):
        """Executes an on-chain USDC transfer."""
        if settings.MOCK_PAYMENTS:
            mock_tx = f"0x_mock_{uuid.uuid4().hex}"
            print(f"MOCK_PAYMENTS active: Simulating transfer of {amount} USDC to {destination_address}. TX: {mock_tx}")
            return mock_tx

        # Official Circle Token ID for USDC on Arc Testnet
        token_id = "15dc2b5d-0994-58b0-bf8c-3a0501148ee8" 
        
        url = f"{self.base_url}/v1/w3s/developer/transactions/transfer"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletId": wallet_id,
            "destinationAddress": destination_address,
            "amounts": [str(amount)],
            "tokenId": token_id,
            "entitySecretCiphertext": self._get_ciphertext(),
            "feeLevel": "MEDIUM"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in transfer_tokens: {resp.text}")
            resp.raise_for_status()
            job_id = resp.json()["data"]["id"]
            
            status_url = f"{self.base_url}/v1/w3s/developer/transactions/{job_id}"
            max_attempts = 60
            for _ in range(max_attempts):
                status_resp = await client.get(status_url, headers=self.headers)
                status_resp.raise_for_status()
                tx_data = status_resp.json()["data"]["transaction"]
                
                if tx_data["status"] == "COMPLETE":
                    return tx_data.get("txHash", f"0x_mock_{job_id}")
                elif tx_data["status"] == "FAILED":
                    print(f"Transfer failed on-chain: {tx_data.get('errorMessage')}")
                    return f"FAILED: {tx_data.get('errorMessage')}"
                
                await asyncio.sleep(1)
            
            return f"PENDING: {job_id}"

circle_service = CircleService()
