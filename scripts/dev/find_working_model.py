import requests
import json
import os
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv("backend/.env")
key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

models_to_try = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

for model in models_to_try:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say hi"}],
        "max_tokens": 10
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            print(f"OK: {model} -> {text.strip()}")
            break
        else:
            print(f"FAIL {model}: HTTP {r.status_code} {r.text[:120]}")
    except Exception as e:
        print(f"ERR {model}: {e}")
