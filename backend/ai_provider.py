import os
import time
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()

TIMEOUT = 30
MAX_RETRIES = 1


def _call_anthropic(prompt: str, system: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not set")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }
    for attempt in range(1 + MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["content"][0]["text"]
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Anthropic API error: {e}") from e
            time.sleep(1)


def _call_openai(prompt: str, system: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": "gpt-4o-mini",
        "max_tokens": 1024,
        "messages": messages,
    }
    for attempt in range(1 + MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"OpenAI API error: {e}") from e
            time.sleep(1)


def _call_gemini(prompt: str, system: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    contents = []
    if system:
        contents.append({"role": "user", "parts": [{"text": system}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    body = {"contents": contents}
    for attempt in range(1 + MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(url, json=body)
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Gemini API error: {e}") from e
            time.sleep(1)


def _call_openrouter(prompt: str, system: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": "google/gemini-2.0-flash-exp:free",
        "max_tokens": 1024,
        "messages": messages,
    }
    for attempt in range(1 + MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"OpenRouter API error: {e}") from e
            time.sleep(1)


def generate(prompt: str, system: str = "") -> str:
    provider = AI_PROVIDER
    if provider == "anthropic":
        return _call_anthropic(prompt, system)
    if provider == "openai":
        return _call_openai(prompt, system)
    if provider == "gemini":
        return _call_gemini(prompt, system)
    if provider == "openrouter":
        return _call_openrouter(prompt, system)
    raise ValueError(f"Unsupported AI_PROVIDER: {provider}. Use anthropic, openai, gemini, or openrouter.")
