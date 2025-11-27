import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def list_models():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Error: {resp.status}")
                print(await resp.text())
                return
            
            data = await resp.json()
            if "models" in data:
                print("Available Models:")
                for model in data["models"]:
                    if "image" in model["name"] or "gemini" in model["name"]:
                        print(f"- {model['name']}")
                        print(f"  Methods: {model.get('supportedGenerationMethods', [])}")
            else:
                print("No models found")

if __name__ == "__main__":
    asyncio.run(list_models())
