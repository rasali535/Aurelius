import base64
import codecs
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# --- CONFIGURATION ---
# 1. Paste your entity public key here (including BEGIN/END lines)
# You can get this from the Circle Dashboard -> Config -> Entity Secret Management
public_key_string = """
-----BEGIN PUBLIC KEY-----
PASTE_YOUR_PUBLIC_KEY_HERE
-----END PUBLIC KEY-----
"""

# 2. This script will generate a new secret for you using os.urandom(32) as per official docs.
# If you already have one, paste the hex string here:
hex_encoded_entity_secret = "" 
# ---------------------

def main():
    global hex_encoded_entity_secret
    
    # Generate secret if not provided
    if not hex_encoded_entity_secret:
        raw_secret = os.urandom(32)
        hex_encoded_entity_secret = codecs.encode(raw_secret, 'hex').decode()

    if len(hex_encoded_entity_secret) != 64:
        print("Error: hex_encoded_entity_secret must be a 64-character hex string.")
        return

    if "PASTE_YOUR_PUBLIC_KEY_HERE" in public_key_string:
        print("Error: Please paste your Circle Public Key into the 'public_key_string' variable in this script.")
        return

    print("=" * 60)
    print("Circle Official-Style Entity Secret Generator")
    print("=" * 60)

    try:
        # Generate entity secret bytes
        entity_secret = bytes.fromhex(hex_encoded_entity_secret)

        # Load Circle's public key
        public_key = serialization.load_pem_public_key(public_key_string.strip().encode())
        
        # Encrypt using RSA-OAEP with SHA-256 (Matching Circle's official requirements)
        ciphertext = public_key.encrypt(
            entity_secret,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # encode to base64
        encrypted_data_base64 = base64.b64encode(ciphertext).decode()

        print("\n[1] HEX ENCODED ENTITY SECRET (Add to .env as CIRCLE_ENTITY_SECRET):")
        print(f"    {hex_encoded_entity_secret}")
        
        print("\n[2] ENTITY SECRET CIPHERTEXT (Paste into Circle Configurator):")
        print(f"    {encrypted_data_base64}")
        
        print("\n" + "=" * 60)
        print(f"Detected Key Size: {public_key.key_size} bits")
        print(f"Ciphertext Length: {len(encrypted_data_base64)} characters")
        if len(encrypted_data_base64) == 684:
            print("SUCCESS: This matches the 684-character requirement for the Dashboard.")
        else:
            print("WARNING: This is NOT 684 characters. Ensure you are using the 4096-bit public key.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[!] Error: {e}")
        print("Ensure the public_key_string contains the full PEM format (BEGIN/END lines).")

if __name__ == '__main__':
    main()
