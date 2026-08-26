import os
import time
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

TIMEOUT = 30
MAX_RETRIES = 1


def _call_openrouter(prompt: str, system: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set. Please set it in your .env file.")
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": OPENROUTER_MODEL,
        "max_tokens": 3000,
        "messages": messages,
    }
    last_error = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                resp = client.post(url, json=body, headers=headers)
                if resp.status_code == 404:
                    raise RuntimeError(
                        f"Model '{OPENROUTER_MODEL}' not found on OpenRouter. "
                        f"Please check OPENROUTER_MODEL in your .env file."
                    )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if not content or not content.strip():
                    raise RuntimeError("AI returned an empty response. Please try again.")
                return content
        except Exception as e:
            last_error = e
            if attempt == MAX_RETRIES:
                break
            time.sleep(1)

    msg = str(last_error)
    if "does not support image" in msg.lower() or "does not support" in msg.lower():
        raise RuntimeError(
            "The selected AI model does not support image input. "
            "Please use a text-only model or upload a text-based file."
        )
    if "401" in msg or "Unauthorized" in msg:
        raise RuntimeError(
            "AI service authentication failed. Please check your OPENROUTER_API_KEY."
        )
    if "429" in msg or "rate limit" in msg.lower():
        raise RuntimeError(
            "AI service rate limit reached. Please wait a moment and try again."
        )
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        raise RuntimeError(
            "AI service request timed out. Please try again later."
        )
    raise RuntimeError(f"AI service temporarily unavailable. Please try again later. ({msg})")


def generate(prompt: str, system: str = "") -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")
    return _call_openrouter(prompt, system)
