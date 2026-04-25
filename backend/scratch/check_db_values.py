import asyncio
import os
import json
from dotenv import load_dotenv
import asyncpg

load_dotenv(os.path.join("backend", ".env"))

async def check():
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    conn = await asyncpg.connect(db_url, ssl='require', statement_cache_size=0)
    rows = await conn.fetch("SELECT data FROM payment_events ORDER BY id DESC LIMIT 5")
    for r in rows:
        data = json.loads(r['data'])
        print(f"Amount: {data.get('amount_usdc')}, Hash: {data.get('tx_hash')}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
