
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not key:
    raise SystemExit("GEMINI_API_KEY is missing from .env")

print(f"Testing model: {model}")

try:
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: Gemini connection works."
    )
    print("SUCCESS")
    print(response.text)

except Exception as exc:
    print("FAILED")
    print(type(exc).__name__)
    print(str(exc))
