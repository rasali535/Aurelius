import asyncio
import sys
import os

# Add the root directory to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import init_db, db
from app.services.validator_service import seed_validators
from app.services.orchestrator_service import process_prompt_run

async def main():
    print("Starting Aurelius Settlement Verification (Developer-Controlled)...")
    
    # Initialize DB
    initialized_db = await init_db()
    db.set_db(initialized_db)
    
    print("Database initialized.")
    
    # Seed Validators
    print("Seeding validators with Developer-Controlled wallets...")
    await seed_validators(db)
    
    # Run a test prompt
    test_prompt = "Tell me about the Roman Empire."
    print(f"Processing test prompt: '{test_prompt}'")
    
    try:
        result = await process_prompt_run(db, test_prompt)
        
        print("\n--- TEST RESULTS ---")
        print(f"Run ID: {result['run_id']}")
        print(f"Status: {result['final_status']}")
        print(f"Total Cost: {result['total_cost_usdc']} USDC")
        
        print("\n--- VALIDATION & PAYMENT DETAILS ---")
        for r in result['results']:
            pay_icon = "[PAID]" if r['payment_status'] == "paid" else "[FREE]"
            print(f"{pay_icon} {r['check_type']} ({r['validator_id']}): {r['status']}")
            if r['tx_hash']:
                print(f"    TX Hash: {r['tx_hash']}")
    except Exception as e:
        print(f"\nExecution Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
