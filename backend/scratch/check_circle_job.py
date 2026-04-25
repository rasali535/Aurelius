import asyncio
import os
import httpx
import sys
from dotenv import load_dotenv

load_dotenv()

async def check_job_with_id(job_id):
    api_key = os.getenv("CIRCLE_API_KEY")
    url = f"https://api.circle.com/v1/w3s/transactions/{job_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        asyncio.run(check_job_with_id(job_id))
    else:
        print("Usage: python scratch/check_circle_job.py <job_id>")
