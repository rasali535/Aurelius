import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    db_url = os.getenv("DATABASE_URL")
    print(f"Testing connection to: {db_url.split('@')[-1]}")
    try:
        conn = await asyncpg.connect(
            dsn=db_url,
            ssl='require',
            timeout=10
        )
        print("SUCCESS: Connected to database!")
        await conn.close()
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
