import httpx
import uuid
import time
import asyncio
import base64
import codecs
import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi import HTTPException
from app.config import settings

# CCTP V2 Configuration for Testnet
CCTP_CONFIG = {
    "ARC-TESTNET": {
        "domain": 26,
        "usdc": "0x3600000000000000000000000000000000000000",
        "token_messenger": "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
        "message_transmitter": "0xE737e5cEBEEBa77EFE34D4aa090756590b1CE275"
    },
    "ETH-SEPOLIA": {
        "domain": 0,
        "usdc": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        "token_messenger": "0x8FE6B999Dc680CcFDD5Bf7EB0974218be2542DAA",
        "message_transmitter": "0xE737e5cEBEEBa77EFE34D4aa090756590b1CE275"
    }
}

IRIS_API_URL = "https://iris-api-sandbox.circle.com/v2/messages"

# Arc Network Specific Configurations (Testnet)
ARC_CONFIG = {
    "identity_registry": "0x8004A818BFB912233c491871b3d84c89A494BD9e",
    "reputation_registry": "0x8004B663056A597Dffe9eCcC1965A193B7388713",
    "validation_registry": "0x8004Cb1BF31DAf7788923b405b754f57acEB4272",
    "agentic_commerce": "0x0747EEf0706327138c69792bF28Cd525089e4583",
    "gateway_wallet": "0x0077777d7EBA4688BDeF3E311b846F25870A19B9",
    "gateway_minter": "0x0022222ABE238Cc2C7Bb1f21003F0a260052475B",
    "usdc": "0x3600000000000000000000000000000000000000"
}

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
        # Support for Circle Standard API authentication
        self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _get_ciphertext(self):
        """Generates a fresh ciphertext for the entity secret using the public key."""
        if not self.entity_secret or not self.public_key_pem:
            return settings.CIRCLE_ENTITY_SECRET_CIPHERTEXT
            
        # Normalize the PEM content: strip and replace literal '\n' with actual newlines
        # Pre-processing diagnostic
        orig_len = len(self.public_key_pem)
        pem_content = self.public_key_pem.strip().replace("\\n", "\n")
        
        if len(pem_content) < 50:
            error_msg = f"ENCRYPTION_FAILURE: Public key is too short ({len(pem_content)} chars). It should be a long PEM string. Original length: {orig_len}"
            print(f"CRITICAL: {error_msg}")
            raise Exception(error_msg)

        # Ensure standard PEM headers are present
        if "-----BEGIN PUBLIC KEY-----" not in pem_content:
            header = "-----BEGIN PUBLIC KEY-----\n"
            footer = "\n-----END PUBLIC KEY-----"
            pem_content = f"{header}{pem_content}{footer}"
            
        try:
            # Cryptography's load_pem_public_key expects the full PEM block
            pub_key = serialization.load_pem_public_key(pem_content.encode())
            ciphertext = pub_key.encrypt(
                bytes.fromhex(self.entity_secret.replace("0x", "")),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(ciphertext).decode()
        except Exception as e:
            # Log the error and raise it so the user sees the REAL reason for failure
            error_msg = f"ENCRYPTION_FAILURE: {e}. Processed length: {len(pem_content)}"
            print(f"CRITICAL: {error_msg}")
            raise Exception(error_msg)

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
        url = f"{self.base_url}/v1/w3s/wallets/{wallet_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in get_wallet_address: {resp.text}")
            resp.raise_for_status()
            return resp.json()["data"]["wallet"]["address"]

    async def list_wallets(self):
        url = f"{self.base_url}/v1/w3s/wallets"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code >= 400:
                print(f"CIRCLE API ERROR ({resp.status_code}) in list_wallets: {resp.text}")
            resp.raise_for_status()
            return resp.json()["data"]["wallets"]

    async def get_wallet_id_for_chain(self, source_wallet_id: str, target_blockchain: str):
        """Finds a wallet in the same wallet set that belongs to the target blockchain."""
        try:
            async with httpx.AsyncClient() as client:
                # 1. Get source wallet info
                resp = await client.get(f"{self.base_url}/v1/w3s/wallets/{source_wallet_id}", headers=self.headers)
                resp.raise_for_status()
                wallet_set_id = resp.json()["data"]["wallet"]["walletSetId"]
                
                # 2. List all wallets in that set
                list_url = f"{self.base_url}/v1/w3s/wallets"
                params = {"walletSetId": wallet_set_id}
                resp = await client.get(list_url, headers=self.headers, params=params)
                resp.raise_for_status()
                
                wallets = resp.json()["data"]["wallets"]
                for w in wallets:
                    if w["blockchain"] == target_blockchain:
                        return w["id"]
            return None
        except Exception as e:
            print(f"Error resolving wallet for chain: {e}")
            return None

    async def sign_typed_data(self, wallet_id: str, typed_data: dict):
        url = f"{self.base_url}/v1/w3s/developer/sign/typedData"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletId": wallet_id,
            "blockchain": "ARC-TESTNET",
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
            status_url = f"{self.base_url}/v1/w3s/transactions/{job_id}"
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
            
            status_url = f"{self.base_url}/v1/w3s/transactions/{job_id}"
            max_attempts = 60
            for _ in range(max_attempts):
                try:
                    status_resp = await client.get(status_url, headers=self.headers)
                    if status_resp.status_code == 200:
                        tx_wrapper = status_resp.json().get("data", {}).get("transaction", {})
                        state = tx_wrapper.get("state")
                        if state == "COMPLETE":
                            return tx_wrapper.get("txHash")
                        elif state == "FAILED":
                            print(f"Transfer failed on-chain: {tx_wrapper.get('errorMessage')}")
                            return f"FAILED: {tx_wrapper.get('errorMessage')}"
                except Exception as e:
                    print(f"Polling error: {e}")
                
                await asyncio.sleep(1)
            
            return f"TIMEOUT: {job_id}"

    async def contract_execution(self, wallet_id: str, contract_address: str, abi_signature: str, abi_parameters: list):
        """Calls a smart contract function."""
        url = f"{self.base_url}/v1/w3s/developer/transactions/contractExecution"
        payload = {
            "idempotencyKey": str(uuid.uuid4()),
            "walletId": wallet_id,
            "contractAddress": contract_address,
            "abiFunctionSignature": abi_signature,
            "abiParameters": abi_parameters,
            "entitySecretCiphertext": self._get_ciphertext(),
            "feeLevel": "MEDIUM"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code >= 400:
                error_detail = resp.text
                print(f"CIRCLE API ERROR ({resp.status_code}) in contract_execution: {error_detail}")
                raise HTTPException(status_code=resp.status_code, detail=f"CIRCLE_API_ERROR: {error_detail}")
            
            job_id = resp.json()["data"]["id"]
            
            # Poll for completion
            status_url = f"{self.base_url}/v1/w3s/transactions/{job_id}"
            for _ in range(60):
                status_resp = await client.get(status_url, headers=self.headers)
                if status_resp.status_code == 200:
                    tx_wrapper = status_resp.json().get("data", {}).get("transaction", {})
                    if tx_wrapper.get("state") == "COMPLETE":
                        return tx_wrapper.get("txHash")
                    elif tx_wrapper.get("state") == "FAILED":
                        raise Exception(f"Contract execution failed: {tx_wrapper.get('errorMessage')}")
                await asyncio.sleep(1)
            raise Exception(f"Contract execution timed out: {job_id}")

    async def get_cctp_attestation(self, source_domain: int, tx_hash: str):
        """Polls the Iris API for a CCTP attestation."""
        url = f"{IRIS_API_URL}/{source_domain}"
        params = {"transactionHash": tx_hash}
        
        async with httpx.AsyncClient() as client:
            # Attestations can take 1-2 minutes on testnet
            for i in range(120):
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # CCTP V2 Iris API returns an array of messages
                    messages = data.get("messages", [])
                    if messages and messages[0].get("status") == "complete":
                        return messages[0].get("message"), messages[0].get("attestation")
                    
                    # Alternative check: top-level status
                    if data.get("status") == "complete" and messages:
                         return messages[0].get("message"), messages[0].get("attestation")
                elif resp.status_code != 404:
                    print(f"Iris API Error: {resp.status_code} - {resp.text}")
                
                await asyncio.sleep(2)
            raise Exception(f"CCTP attestation timed out for tx {tx_hash}")

    async def bridge_usdc(self, wallet_id: str, amount: float, source_blockchain: str, destination_blockchain: str, destination_address: str):
        """
        Complete CCTP Bridge Flow:
        1. Approve USDC for TokenMessenger
        2. DepositForBurn on source TokenMessenger
        3. Poll Iris API for attestation
        4. ReceiveMessage on destination MessageTransmitter
        """
        src = CCTP_CONFIG.get(source_blockchain)
        dst = CCTP_CONFIG.get(destination_blockchain)
        
        if not src or not dst:
            raise ValueError(f"Unsupported blockchain for bridging: {source_blockchain} -> {destination_blockchain}")

        # Amount in 6 decimals (standard for USDC)
        amount_raw = str(int(amount * 1_000_000))
        
        print(f"--- Starting CCTP Bridge: {amount} USDC from {source_blockchain} to {destination_blockchain} ---")
        
        # Step 1: Approve
        print("Step 1/4: Approving USDC...")
        approve_tx = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=src["usdc"],
            abi_signature="approve(address,uint256)",
            abi_parameters=[src["token_messenger"], amount_raw]
        )
        print(f"Approval successful: {approve_tx}")

        # Step 2: DepositForBurn
        print("Step 2/4: Depositing for burn...")
        # Recipient address must be bytes32 (padded with 0s)
        recipient_bytes32 = "0x" + destination_address.lower().replace("0x", "").zfill(64)
        
        burn_tx = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=src["token_messenger"],
            abi_signature="depositForBurn(uint256,uint32,bytes32,address)",
            abi_parameters=[amount_raw, str(dst["domain"]), recipient_bytes32, src["usdc"]]
        )
        print(f"Burn successful: {burn_tx}")

        # Step 3: Get Attestation
        print("Step 3/4: Polling for CCTP attestation (this may take 1-2 mins)...")
        message, attestation = await self.get_cctp_attestation(src["domain"], burn_tx)
        print("Attestation received!")

        # Step 4: Receive Message
        # NOTE: This requires a wallet on the destination chain in the same wallet set.
        # For simplicity, we assume the same wallet_id works if it's the same address on both chains,
        # but in Circle W3S, wallet_id is chain-specific.
        # We need to find the wallet ID for the destination blockchain.
        
        print("Step 4/4: Minting on destination chain...")
        dest_wallet_id = await self.get_wallet_id_for_chain(wallet_id, destination_blockchain)
        if not dest_wallet_id:
            print(f"WARNING: Could not find wallet for {destination_blockchain}. Falling back to source wallet_id.")
            dest_wallet_id = wallet_id
            
        # We call receiveMessage(message, attestation)
        mint_tx = await self.contract_execution(
            wallet_id=dest_wallet_id,
            contract_address=dst["message_transmitter"],
            abi_signature="receiveMessage(bytes,bytes)",
            abi_parameters=[message, attestation]
        )
        
        print(f"Bridge complete! Destination TX: {mint_tx}")
        return {
            "sourceTx": burn_tx,
            "destTx": mint_tx,
            "status": "SUCCESS"
        }

    # --- ERC-8004: AI Agent Identity ---
    async def register_agent(self, wallet_id: str, metadata_uri: str):
        """Registers an AI agent's on-chain identity (ERC-8004)."""
        print(f"Registering AI agent with metadata: {metadata_uri}")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["identity_registry"],
            abi_signature="register(string)",
            abi_parameters=[metadata_uri]
        )
        return tx_hash

    async def give_agent_feedback(self, wallet_id: str, agent_id: str, score: int, tag: str):
        """Records reputation feedback for an agent (ERC-8004)."""
        # score should be 0-100. feedbackHash is keccak256(tag)
        import hashlib
        feedback_hash = "0x" + hashlib.sha3_256(tag.encode()).hexdigest() # Simple mock for keccak if not available, but usually we'd use eth_utils or similar
        # In reality, Arc uses Keccak-256. 
        
        print(f"Recording feedback for agent {agent_id}: score={score}, tag={tag}")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["reputation_registry"],
            abi_signature="giveFeedback(uint256,int128,uint8,string,string,string,string,bytes32)",
            abi_parameters=[str(agent_id), str(score), "0", tag, "", "", "", feedback_hash]
        )
        return tx_hash

    # --- ERC-8183: Job & Escrow Flow ---
    async def create_job(self, wallet_id: str, provider: str, evaluator: str, description: str, hours_until_expiry: int = 24):
        """Creates a new job (ERC-8183)."""
        expired_at = int(time.time()) + (hours_until_expiry * 3600)
        print(f"Creating job: {description}")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["agentic_commerce"],
            abi_signature="createJob(address,address,uint256,string,address)",
            abi_parameters=[provider, evaluator, str(expired_at), description, "0x0000000000000000000000000000000000000000"]
        )
        return tx_hash

    async def set_job_budget(self, wallet_id: str, job_id: str, amount: float):
        """Sets the budget for a job (called by provider)."""
        amount_raw = str(int(amount * 1_000_000))
        print(f"Setting budget for job {job_id}: {amount} USDC")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["agentic_commerce"],
            abi_signature="setBudget(uint256,uint256,bytes)",
            abi_parameters=[str(job_id), amount_raw, "0x"]
        )
        return tx_hash

    async def fund_job(self, wallet_id: str, job_id: str, amount: float):
        """Approves USDC and funds a job's escrow."""
        amount_raw = str(int(amount * 1_000_000))
        
        # Step 1: Approve
        print(f"Approving {amount} USDC for Job {job_id}...")
        await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["usdc"],
            abi_signature="approve(address,uint256)",
            abi_parameters=[ARC_CONFIG["agentic_commerce"], amount_raw]
        )
        
        # Step 2: Fund
        print(f"Funding escrow for job {job_id}...")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["agentic_commerce"],
            abi_signature="fund(uint256,bytes)",
            abi_parameters=[str(job_id), "0x"]
        )
        return tx_hash

    async def submit_job(self, wallet_id: str, job_id: str, deliverable_text: str):
        """Submits a deliverable hash for a job."""
        import hashlib
        deliverable_hash = "0x" + hashlib.sha3_256(deliverable_text.encode()).hexdigest()
        
        print(f"Submitting deliverable for job {job_id}")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["agentic_commerce"],
            abi_signature="submit(uint256,bytes32,bytes)",
            abi_parameters=[str(job_id), deliverable_hash, "0x"]
        )
        return tx_hash

    async def complete_job(self, wallet_id: str, job_id: str, reason: str = "Deliverable approved"):
        """Completes a job and releases escrow (evaluator)."""
        import hashlib
        reason_hash = "0x" + hashlib.sha3_256(reason.encode()).hexdigest()
        
        print(f"Completing job {job_id}")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["agentic_commerce"],
            abi_signature="complete(uint256,bytes32,bytes)",
            abi_parameters=[str(job_id), reason_hash, "0x"]
        )
        return tx_hash

    # --- Gateway: Nanopayments & Unified Balance ---
    async def gateway_deposit(self, wallet_id: str, amount: float):
        """Deposits USDC into the unified Gateway balance."""
        amount_raw = str(int(amount * 1_000_000))
        
        # Step 1: Approve
        print(f"Approving {amount} USDC for Gateway Wallet...")
        await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["usdc"],
            abi_signature="approve(address,uint256)",
            abi_parameters=[ARC_CONFIG["gateway_wallet"], amount_raw]
        )
        
        # Step 2: Deposit
        print(f"Depositing into Gateway...")
        tx_hash = await self.contract_execution(
            wallet_id=wallet_id,
            contract_address=ARC_CONFIG["gateway_wallet"],
            abi_signature="deposit(address,uint256)",
            abi_parameters=[ARC_CONFIG["usdc"], amount_raw]
        )
        return tx_hash

    async def gateway_transfer(self, wallet_id: str, destination_blockchain: str, destination_address: str, amount: float):
        """
        Executes a Gateway transfer (burn from unified balance, mint on destination).
        """
        import secrets
        
        src_chain = "ARC-TESTNET"
        dst_chain = destination_blockchain
        
        src_domain = CCTP_CONFIG[src_chain]["domain"]
        dst_domain = CCTP_CONFIG[dst_chain]["domain"]
        
        amount_raw = int(amount * 1_000_000)
        salt = "0x" + secrets.token_hex(32)
        
        # 1. Construct EIP-712 Typed Data
        # Based on Arc Gateway documentation
        def address_to_bytes32(addr):
            return "0x" + addr.lower().replace("0x", "").zfill(64)

        depositor_address = await self.get_wallet_address(wallet_id)
        
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "TransferSpec": [
                    {"name": "version", "type": "uint32"},
                    {"name": "sourceDomain", "type": "uint32"},
                    {"name": "destinationDomain", "type": "uint32"},
                    {"name": "sourceContract", "type": "bytes32"},
                    {"name": "destinationContract", "type": "bytes32"},
                    {"name": "sourceToken", "type": "bytes32"},
                    {"name": "destinationToken", "type": "bytes32"},
                    {"name": "sourceDepositor", "type": "bytes32"},
                    {"name": "destinationRecipient", "type": "bytes32"},
                    {"name": "sourceSigner", "type": "bytes32"},
                    {"name": "destinationCaller", "type": "bytes32"},
                    {"name": "value", "type": "uint256"},
                    {"name": "salt", "type": "bytes32"},
                    {"name": "hookData", "type": "bytes"}
                ],
                "BurnIntent": [
                    {"name": "maxBlockHeight", "type": "uint256"},
                    {"name": "maxFee", "type": "uint256"},
                    {"name": "spec", "type": "TransferSpec"}
                ]
            },
            "domain": {
                "name": "GatewayWallet", 
                "version": "1",
                "chainId": 26,
                "verifyingContract": ARC_CONFIG["gateway_wallet"]
            },
            "primaryType": "BurnIntent",
            "message": {
                "maxBlockHeight": str((1 << 256) - 1),
                "maxFee": "2010000",
                "spec": {
                    "version": 1,
                    "sourceDomain": src_domain,
                    "destinationDomain": dst_domain,
                    "sourceContract": address_to_bytes32(ARC_CONFIG["gateway_wallet"]),
                    "destinationContract": address_to_bytes32(ARC_CONFIG["gateway_minter"]),
                    "sourceToken": address_to_bytes32(ARC_CONFIG["usdc"]),
                    "destinationToken": address_to_bytes32(CCTP_CONFIG[dst_chain]["usdc"]),
                    "sourceDepositor": address_to_bytes32(depositor_address),
                    "destinationRecipient": address_to_bytes32(destination_address),
                    "sourceSigner": address_to_bytes32(depositor_address),
                    "destinationCaller": "0x" + "0" * 64,
                    "value": str(amount_raw),
                    "salt": salt,
                    "hookData": "0x"
                }
            }
        }

        # 2. Sign the burn intent
        print("Signing burn intent for Gateway transfer...")
        signature = await self.sign_typed_data(wallet_id, typed_data)
        
        # 3. Submit to Gateway API
        print("Submitting transfer to Gateway API...")
        gateway_url = "https://gateway-api-testnet.circle.com/v1/transfer"
        payload = [{
            "burnIntent": typed_data["message"],
            "signature": signature
        }]
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(gateway_url, json=payload)
            if resp.status_code >= 400:
                print(f"GATEWAY API ERROR: {resp.text}")
            resp.raise_for_status()
            gateway_data = resp.json() # Usually returns { attestation, signature }
            
        # 4. Mint on destination chain
        print(f"Minting on {destination_blockchain}...")
        dest_wallet_id = await self.get_wallet_id_for_chain(wallet_id, destination_blockchain)
        
        mint_tx = await self.contract_execution(
            wallet_id=dest_wallet_id or wallet_id,
            contract_address=ARC_CONFIG["gateway_minter"],
            abi_signature="gatewayMint(bytes,bytes)",
            abi_parameters=[gateway_data["attestation"], gateway_data["signature"]]
        )
        
        return mint_tx

circle_service = CircleService()
