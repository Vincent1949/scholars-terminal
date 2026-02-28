# Test this separately to check your OpenAI key:
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

try:
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input="test"
    )
    print("OpenAI key works!")
except Exception as e:
    print(f"OpenAI key error: {e}")