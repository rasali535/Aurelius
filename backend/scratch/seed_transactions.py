import asyncio
import os
import json
from datetime import datetime, timedelta, timezone
import random
from uuid import uuid4
import asyncpg
from dotenv import load_dotenv

# Load env from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Mimic the app's generate_id and utc_now
def generate_id(prefix):
    return f"{prefix}_{uuid4().hex[:12]}"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

# Shared validators list for realistic seeding
VALIDATORS = [
    {"id": "validator_hallucination_1", "check_type": "hallucination", "price": 0.001},
    {"id": "validator_pii_1", "check_type": "pii", "price": 0.001},
    {"id": "validator_safety_1", "check_type": "safety", "price": 0.002},
    {"id": "validator_compliance_1", "check_type": "compliance", "price": 0.003},
    {"id": "validator_multimodal_1", "check_type": "multimodal", "price": 0.008},
]

PROMPT_SAMPLES = [
    "Validate smart contract security for DeFi protocol",
    "Check PII leakage in user support transcript",
    "Analyze cross-chain arbitrage opportunity on Arc",
    "Verify identity of agent V-9 and check reputation",
    "Route 1000 USDC to optimal liquidity pool",
    "Analyze Multimodal invoice for commerce settlement",
    "Audit compliance for agent-to-agent job escrow",
]

async def seed_dashboard_data():
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        print("Error: DATABASE_URL not set")
        return

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to DB to seed comprehensive dashboard data...")
    conn = await asyncpg.connect(db_url, ssl='require', statement_cache_size=0)

    # Ensure tables exist
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS prompt_runs (id TEXT PRIMARY KEY, data JSONB NOT NULL DEFAULT '{}'::jsonb);
        CREATE TABLE IF NOT EXISTS validation_requests (id TEXT PRIMARY KEY, data JSONB NOT NULL DEFAULT '{}'::jsonb);
        CREATE TABLE IF NOT EXISTS payment_events (id TEXT PRIMARY KEY, data JSONB NOT NULL DEFAULT '{}'::jsonb);
    """)

    # 1. Seed Prompt Runs & Validation Requests
    print("Seeding 20+ Prompt Runs and associated Validations...")
    for i in range(22):
        run_id = generate_id("run")
        prompt = random.choice(PROMPT_SAMPLES)
        timestamp = (datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 120))).isoformat()
        
        prompt_doc = {
            "input_prompt": prompt,
            "draft_response": f"AI response for: {prompt[:30]}...",
            "final_status": random.choice(["approved", "approved", "approved", "review_required"]),
            "total_cost_usdc": 0.0,
            "validator_count": 5,
            "created_at": timestamp
        }
        
        await conn.execute(
            "INSERT INTO prompt_runs (id, data) VALUES ($1, $2::jsonb)",
            run_id, json.dumps(prompt_doc)
        )
        
        run_total_cost = 0.0
        for val in VALIDATORS:
            val_id = generate_id("val")
            pay_id = generate_id("pay")
            
            # Payment Event
            pay_doc = {
                "validation_request_id": val_id,
                "amount_usdc": val["price"],
                "status": "settled",
                "tx_hash": f"0x{uuid4().hex}{uuid4().hex[:32]}",
                "x402_status": "paid",
                "created_at": timestamp,
                "settled_at": timestamp
            }
            await conn.execute(
                "INSERT INTO payment_events (id, data) VALUES ($1, $2::jsonb)",
                pay_id, json.dumps(pay_doc)
            )
            
            # Validation Request
            val_doc = {
                "prompt_run_id": run_id,
                "validator_id": val["id"],
                "status": "passed",
                "payment_event_id": pay_id,
                "response_time_ms": random.randint(200, 1500),
                "created_at": timestamp
            }
            await conn.execute(
                "INSERT INTO validation_requests (id, data) VALUES ($1, $2::jsonb)",
                val_id, json.dumps(val_doc)
            )
            
            run_total_cost += val["price"]
            
        # Update run with final cost
        prompt_doc["total_cost_usdc"] = round(run_total_cost, 4)
        await conn.execute(
            "UPDATE prompt_runs SET data = $1::jsonb WHERE id = $2",
            json.dumps(prompt_doc), run_id
        )

    # 2. Seed Extra Commerce Events (Swaps, Bridges, Jobs)
    print("Seeding extra commerce events (Swaps, Bridges, Jobs)...")
    commerce_types = ["swap", "cctp_bridge", "job_fee", "reg_fee", "settlement"]
    
    for i in range(45):
        pay_id = generate_id("pay")
        c_type = random.choice(commerce_types)
        amount = random.choice([0.0001, 0.0005, 0.01, 0.05, 0.1, 1.0, 5.0])
        timestamp = (datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 180))).isoformat()
        
        tx_hash = f"0x{uuid4().hex}{uuid4().hex[:32]}"
        if i % 15 == 0: tx_hash = "indexing_on_chain" # Some pending look
        
        pay_doc = {
            "validation_request_id": f"comm_{uuid4().hex[:8]}",
            "amount_usdc": amount,
            "status": "settled" if not tx_hash.startswith("ind") else "processing",
            "tx_hash": tx_hash,
            "x402_status": c_type,
            "created_at": timestamp,
            "settled_at": timestamp if not tx_hash.startswith("ind") else None
        }
        await conn.execute(
            "INSERT INTO payment_events (id, data) VALUES ($1, $2::jsonb)",
            pay_id, json.dumps(pay_doc)
        )

    print("Successfully seeded 20+ runs, 100+ validations, and 65+ total settlements.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_dashboard_data())
