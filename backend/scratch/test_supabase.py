import asyncio
import os
from dotenv import load_dotenv
from app.db import init_db

async def test_db():
    load_dotenv()
    print("Initializing DB...")
    db = await init_db()
    
    # Test insert
    print("Testing insert...")
    test_agent = {
        "name": "Test Agent",
        "wallet_address": f"0x{os.urandom(20).hex()}",
        "role": "tester"
    }
    inserted = await db.agents.insert_one(test_agent)
    print(f"Inserted: {inserted}")
    
    # Test find
    print("Testing find...")
    agent = await db.agents.find_one({"_id": inserted.inserted_id})
    print(f"Found: {agent}")
    
    # Test count
    print("Testing count...")
    count = await db.agents.count_documents({})
    print(f"Total agents: {count}")

    # Test aggregate (SUM)
    print("Testing aggregate (SUM)...")
    # First insert a prompt run with cost
    await db.prompt_runs.insert_one({
        "input_prompt": "Test cost",
        "total_cost_usdc": 1.5,
        "final_status": "completed"
    })
    await db.prompt_runs.insert_one({
        "input_prompt": "Test cost 2",
        "total_cost_usdc": 2.5,
        "final_status": "completed"
    })
    
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_cost_usdc"}}}]
    agg_result = await db.prompt_runs.aggregate(pipeline).to_list()
    print(f"Aggregate result: {agg_result}")

if __name__ == "__main__":
    asyncio.run(test_db())
