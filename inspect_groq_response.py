import requests
import json
import os
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv("backend/.env")
key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

payload = {
    "model": "openai/gpt-oss-120b",
    "messages": [{"role": "user", "content": "Say hi in 3 words"}],
    "max_tokens": 50
}
r = requests.post(url, headers=headers, json=payload, timeout=30)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2)[:1000])
