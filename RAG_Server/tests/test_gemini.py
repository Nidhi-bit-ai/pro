from google import genai
from dotenv import load_dotenv
import os

load_dotenv(".env")

client = genai.Client(api_key=os.getenv("GEMINI1"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello"
)

print(response.text)