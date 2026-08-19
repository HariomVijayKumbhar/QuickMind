import requests
import os
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv("backend/.env")
key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {key}"}

r = requests.get(url, headers=headers, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    models = [m["id"] for m in data.get("data", [])]
    print(f"Available models ({len(models)}):")
    for m in sorted(models):
        print(f"  {m}")
else:
    print(r.text[:300])
