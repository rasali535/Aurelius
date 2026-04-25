import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def list_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(list_models())
