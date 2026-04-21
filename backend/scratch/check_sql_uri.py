import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_new_uri():
    uri = "mongodb://maplininc_db_user:GtGQkD4Hd4m5tsxh@atlas-sql-69e79f35d686d827070f8707-fa4gj1.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin"
    print(f"Testing new SQL-style URI: {uri}")
    client = AsyncIOMotorClient(uri)
    try:
        await client.admin.command('ismaster')
        print("Success: Connection works!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_new_uri())
