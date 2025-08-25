import asyncio
import google.generativeai as genai
import traceback
from aioconsole import ainput
# Set your Gemini API key (you can also use os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key="AIzaSyDPFuKK3jZ_WfVruA1aeUcALsrylL-cl9w")
# Define an async wrapper (Gemini's SDK is sync, so use asyncio.to_thread)
async def get_match_percentage(prompt: str):
    await ainput("press enter if working")
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Run sync Gemini call in a background thread
        response = await asyncio.to_thread(model.generate_content, prompt)

        # Extract and return the cleaned response
        response_text = response.text.strip()
        return response_text

    except Exception as e:
        print("\nError:", e)
        print(traceback.format_exc())
        return None

for _ in range(10):
    asyncio.run(get_match_percentage("Hi"))

