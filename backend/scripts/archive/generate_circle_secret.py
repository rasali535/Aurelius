import secrets
import base64
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def generate_ciphertext(public_key_pem: str, entity_secret_hex: str):
    """
    Encrypts a 32-byte hex-encoded entity secret using Circle's public key.
    """
    # Load Circle's public key
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    
    # Convert hex secret to bytes
    entity_secret_bytes = bytes.fromhex(entity_secret_hex)
    if len(entity_secret_bytes) != 32:
        raise ValueError("Entity secret must be exactly 32 bytes (64 hex characters).")
    
    # Encrypt using RSA-OAEP
    ciphertext = public_key.encrypt(
        entity_secret_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Return base64 encoded ciphertext
    return base64.b64encode(ciphertext).decode()

if __name__ == "__main__":
    print("=" * 60)
    print("Aurelius - Circle Entity Secret Generator")
    print("=" * 60)
    
    # 1. Generate a random 32-byte secret
    new_secret = secrets.token_hex(32)
    print(f"\n[1] YOUR NEW ENTITY SECRET (SAVE THIS SECURELY!):")
    print(f"    {new_secret}")
    print("\n    --> Action: Add this to your .env as CIRCLE_ENTITY_SECRET")
    
    print("\n" + "-" * 60)
    print("[2] GENERATE ENTITY SECRET CIPHERTEXT")
    print("-" * 60)
    print("Go to Circle Developer Dashboard -> Config -> Entity Secret Management")
    print("Copy the Public Key (PEM format) and paste it below.")
    print("\nInstructions for Windows Users:")
    print("1. Paste the key.")
    print("2. Press ENTER.")
    print("3. Press Ctrl+Z then ENTER to finish.")
    print("-" * 60)
    
    print("\nPASTE PUBLIC KEY HERE:")
    print("(Must start with '-----BEGIN PUBLIC KEY-----')")
    print("(Type 'DONE' on a new line when finished)")
    print("-" * 30)
    
    try:
        public_key_lines = []
        while True:
            try:
                line = input().strip()
                if line.upper() == "DONE":
                    break
                if line:
                    public_key_lines.append(line + "\n")
            except EOFError:
                break
        
        public_key_pem = "".join(public_key_lines).strip()
        
        if not public_key_pem:
            print("\n[!] No public key provided. Ciphertext generation skipped.")
        elif "-----BEGIN PUBLIC KEY-----" not in public_key_pem:
            print("\n" + "!" * 60)
            print("ERROR: INVALID PUBLIC KEY FORMAT")
            print("!" * 60)
            print("You likely pasted the hexadecimal secret from Step 1 by mistake.")
            print("Step 2 requires the PEM PUBLIC KEY from the Circle Dashboard.")
            print("It must include the line '-----BEGIN PUBLIC KEY-----'.")
            print("!" * 60)
        else:
            # Load key to check bit size
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            bit_size = public_key.key_size
            
            print(f"\n[i] Detected Public Key Size: {bit_size} bits")
            
            if bit_size != 4096:
                print("\n" + "!" * 60)
                print("WARNING: CIRCLE REQUIRES A 4096-BIT PUBLIC KEY")
                print("!" * 60)
                print(f"Your currently provided key is {bit_size} bits.")
                print(f"The Circle Dashboard (W3S) will reject anything other than 4096.")
                print("-" * 60)
                print("Solution: Use the public key from the 'Configurator' or")
                print("'Entity Secret Management' section of the dashboard.")
                print("!" * 60 + "\n")

            ciphertext = generate_ciphertext(public_key_pem, new_secret)
            
            print("\n" + "=" * 60)
            print(f"SUCCESS! YOUR ENTITY_SECRET_CIPHERTEXT ({len(ciphertext)} chars):")
            print("=" * 60)
            print(f"\n{ciphertext}\n")
            print("=" * 60)
            print("Action: Add this to your backend/.env as CIRCLE_ENTITY_SECRET_CIPHERTEXT")
            if len(ciphertext) != 684:
                print("\n[!] WARNING: This is NOT 684 characters. It may fail in the dashboard.")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n[!] Error generating ciphertext: {e}")
        print("    Ensure you pasted the entire PEM string including BEGIN/END headers.")

    print("\nDone.")
