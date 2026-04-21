import asyncio
import logging
from app.services.gemini_service import gemini_service

logging.basicConfig(level=logging.INFO)

async def test_aiml_integration():
    print("Testing AI/ML API Integration (Gemini 2.0 Flash)")
    
    prompt = "Hello! Who are you and what tools do you have access to?"
    print(f"\nUser: {prompt}")
    
    response = await gemini_service.chat_with_tools(prompt)
    print(f"\nAurelius: {response}")
    
    # Test tool selection (without actual execution if possible, but the mock tools should work)
    prompt_tool = "I need a new wallet for 'Agent-X'. Can you create one for me?"
    print(f"\nUser: {prompt_tool}")
    
    response_tool = await gemini_service.chat_with_tools(prompt_tool)
    print(f"\nAurelius: {response_tool}")

if __name__ == "__main__":
    asyncio.run(test_aiml_integration())
