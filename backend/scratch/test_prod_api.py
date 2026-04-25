import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_api():
    url = "https://aurelius-production-2ec3.up.railway.app/api/commerce/bridge"
    payload = {
        "amount": 5.0,
        "source_blockchain": "ETH-SEPOLIA",
        "destination_blockchain": "ARC-TESTNET",
        "destination_address": "0xcdedbb19bc920690be4e64635f5e0a2f4be894a6"
    }
    
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(url, json=payload)
        print("BRIDGE STATUS:", resp.status_code)
        print("BRIDGE RESPONSE:", resp.text)
        
    url2 = "https://aurelius-production-2ec3.up.railway.app/api/commerce/multimodal/settle"
    payload2 = {
        "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
        "prompt": "Test"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp2 = await client.post(url2, json=payload2)
        print("SETTLE STATUS:", resp2.status_code)
        print("SETTLE RESPONSE:", resp2.text)

if __name__ == "__main__":
    asyncio.run(test_api())
