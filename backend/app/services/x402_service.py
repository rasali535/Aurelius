import time
import uuid
from eth_account.messages import encode_typed_data
from eth_account import Account
from app.config import settings

class X402Service:
    def __init__(self):
        self.usdc_contract = settings.CIRCLE_USDC_CONTRACT
        self.arc_chain_id = 5042002

    def generate_challenge(self, amount_usdc: float, validator_wallet: str):
        """Generates an x402 challenge (payment required payload)."""
        # x402 standard headers usually expect these fields
        nonce = str(uuid.uuid4().hex)
        return {
            "protocol": "x402",
            "scheme": "exact", # Using 'exact' for nanopayments
            "verifyingContract": self.usdc_contract,
            "receiver": validator_wallet,
            "amount": str(int(amount_usdc * 10**6)), # USDC Decimals (6 for ERC20 interface)
            "nonce": nonce,
            "validBefore": int(time.time()) + 3600, # 1 hour
            "network": "Arc Testnet",
            "chainId": self.arc_chain_id
        }

    def construct_eip712_payload(self, challenge: dict, from_wallet: str):
        """Constructs the Typed Data for EIP-712 / EIP-3009 signing."""
        # This structure matches Circle's required TransferWithAuthorization format
        # Reference: EIP-3009 TransferWithAuthorization
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
                "chainId": self.arc_chain_id,
                "verifyingContract": self.usdc_contract
            },
            "primaryType": "TransferWithAuthorization",
            "message": {
                "from": from_wallet,
                "to": challenge["receiver"],
                "value": int(challenge["amount"]),
                "validAfter": 0,
                "validBefore": challenge["validBefore"],
                "nonce": "0x" + challenge["nonce"].zfill(64) # Ensure 32 bytes hex
            }
        }

    def verify_signature(self, payload: dict, signature: str):
        """Verifies the EIP-3009 signature locally."""
        try:
            # Recover the signer address from the signature
            message = encode_typed_data(full_message=payload)
            recovered = Account.recover_message(message, signature=signature)
            return recovered.lower() == payload["message"]["from"].lower()
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False

x402_service = X402Service()
