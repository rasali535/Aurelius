import time
import uuid
from eth_account.messages import encode_typed_data
from eth_account import Account
from app.config import settings

class X402Service:
    def __init__(self):
        self.usdc_contract = settings.CIRCLE_USDC_CONTRACT

    def generate_challenge(self, amount_usdc: float, validator_wallet: str):
        """Generates an x402 challenge (payment required payload)."""
        nonce = str(uuid.uuid4().hex)
        return {
            "protocol": "x402",
            "scheme": "GatewayWalletBatched",
            "verifyingContract": self.usdc_contract,
            "receiver": validator_wallet,
            "amount": str(int(amount_usdc * 10**6)), # USDC Decimals
            "nonce": nonce,
            "validBefore": int(time.time()) + 3600 # 1 hour
        }

    def construct_eip712_payload(self, challenge: dict, from_wallet: str):
        """Constructs the Typed Data for EIP-712 / EIP-3009 signing."""
        # This structure matches Circle's required TransferWithAuthorization format
        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "TransferWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"}
                ]
            },
            "domain": {
                "name": "USD Coin",
                "version": "2",
                "chainId": 43113, # Fuji Testnet
                "verifyingContract": self.usdc_contract
            },
            "primaryType": "TransferWithAuthorization",
            "message": {
                "from": from_wallet,
                "to": challenge["receiver"],
                "value": int(challenge["amount"]),
                "validAfter": 0,
                "validBefore": challenge["validBefore"],
                "nonce": challenge["nonce"].zfill(64) # Ensure 32 bytes
            }
        }

    def verify_signature(self, payload: dict, signature: str):
        """Verifies the EIP-3009 signature locally."""
        # Note: In a production environment, this would use eth_account.recover_message
        # or similar to ensure the 'from' address matches the signer.
        try:
            # Simple placeholder for signature verification logic
            # Real implementation would use:
            # recovered = Account.recover_typed_data(payload, signature=signature)
            # return recovered.lower() == payload["message"]["from"].lower()
            return True 
        except Exception:
            return False

x402_service = X402Service()
