import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def verify_atlas():
    print(f"Connecting to Atlas: {settings.MONGODB_URI}")
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        # The ismaster command is cheap and does not require auth.
        await client.admin.command('ismaster')
        print("Success: MongoDB Atlas connection established!")
    except Exception as e:
        print(f"Error: Could not connect to Atlas: {e}")

if __name__ == "__main__":
    asyncio.run(verify_atlas())
