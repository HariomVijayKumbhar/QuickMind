import requests
import os
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv("backend/.env")
key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

models_to_try = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "groq/compound",
    "groq/compound-mini",
]

for model in models_to_try:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hi in 3 words"}],
        "max_tokens": 20
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            print(f"OK: {model} -> {text.strip()}")
        else:
            print(f"FAIL {model}: HTTP {r.status_code} {r.text[:120]}")
    except Exception as e:
        print(f"ERR {model}: {e}")
