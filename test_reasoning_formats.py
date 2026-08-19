import requests
import json
import os
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv("backend/.env")
key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

for model in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b"]:
    for rf in [None, "hidden", "parsed"]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hi in 3 words"}],
            "max_tokens": 100
        }
        if rf:
            payload["reasoning_format"] = rf
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        reasoning = data.get("choices", [{}])[0].get("message", {}).get("reasoning", "")
        finish = data.get("choices", [{}])[0].get("finish_reason", "")
        print(f"{model} | reasoning_format={rf} | finish={finish}")
        print(f"  content: {repr(content[:100])}")
        print(f"  reasoning: {repr(reasoning[:100])}")
        print()
