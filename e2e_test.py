import requests
import time
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = 'http://localhost:8000'
email = f'e2e_{int(time.time())}@test.com'

signup = requests.post(f'{BASE}/api/auth/signup', json={'email': email,'password':'testpass123'}, timeout=10).json()
print('Signup:', signup.get('success'))
token = signup['token']
headers = {'Authorization': f'Bearer {token}'}

endpoints = [
    ('/api/summarize', {'text':'AI is transforming productivity tools by enabling intelligent automation, contextual understanding, and personalized assistance for knowledge workers.','length':'short'}),
    ('/api/ask', {'question':'How is AI transforming productivity?','reference_text':'AI is transforming productivity tools by enabling intelligent automation, contextual understanding, and personalized assistance for knowledge workers.'}),
    ('/api/generate', {'content_type':'Email','topic':'Project update','tone':'Professional'}),
    ('/api/analyze', {'text':'AI is transforming productivity tools by enabling intelligent automation, contextual understanding, and personalized assistance for knowledge workers.'}),
]

for ep, payload in endpoints:
    r = requests.post(f'{BASE}{ep}', json=payload, headers=headers, timeout=60)
    data = r.json()
    print(f'{ep}: success={data.get("success")}')
    if data.get('success'):
        d = data.get('data', {})
        if 'result' in d:
            print(f'  result[:100]: {d["result"][:100]}')
        if 'main_topic' in d:
            print(f'  main_topic: {d["main_topic"]}')
        if 'suggestions' in d:
            print(f'  suggestions: {d["suggestions"][:2]}')
    else:
        print(f'  error: {data.get("error","")[:200]}')
    print()

hist = requests.get(f'{BASE}/api/history', headers=headers, timeout=10).json()
print(f'History entries: {len(hist.get("data", []))}')

login = requests.post(f'{BASE}/api/auth/login', json={'email': email,'password':'testpass123'}, timeout=10).json()
print(f'Login success: {login.get("success")}')
