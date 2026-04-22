import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def check_db():
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "sample_mflix")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    config = await db.config.find_one({"_id": "requester_wallet"})
    print(f"Requester Wallet: {config}")
    
    runs = await db.prompt_runs.count_documents({})
    print(f"Prompt Runs: {runs}")
    
    agents = await db.agents.count_documents({})
    print(f"Agents: {agents}")

if __name__ == "__main__":
    asyncio.run(check_db())
