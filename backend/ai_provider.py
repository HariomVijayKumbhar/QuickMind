import base64
import os
import time
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

TIMEOUT = 60
MAX_RETRIES = 1

VISION_MODEL_PREFIXES = (
    "google/gemini",
    "openai/",
    "anthropic/",
    "meta-llama/llama-3.2",
    "qwen/",
    "microsoft/",
)


def _is_vision_model(model: str) -> bool:
    lowered = model.lower()
    return any(lowered.startswith(prefix.lower()) for prefix in VISION_MODEL_PREFIXES)


def _encode_image_to_base64(image_bytes: bytes, mime_type: str = "image/png") -> str:
    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"


def _build_body(prompt: str, system: str = "", image_bytes: bytes = None, mime_type: str = None) -> dict:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    if image_bytes and _is_vision_model(OPENROUTER_MODEL):
        content = [{"type": "text", "text": prompt}]
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": _encode_image_to_base64(image_bytes, mime_type or "image/png")
                },
            }
        )
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": prompt})

    return {
        "model": OPENROUTER_MODEL,
        "max_tokens": 3000,
        "messages": messages,
    }


def _call_openrouter(prompt: str, system: str = "", image_bytes: bytes = None, mime_type: str = None) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set. Please set it in your .env file.")
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    body = _build_body(prompt, system, image_bytes, mime_type)
    last_error = None
    for attempt in range(1 + MAX_RETRIES):
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(url, json=body, headers=headers)
                if resp.status_code == 404:
                    raise RuntimeError(
                        f"Model '{OPENROUTER_MODEL}' not found on OpenRouter. "
                        f"Please check OPENROUTER_MODEL in your .env file."
                    )
                if resp.status_code == 400 and image_bytes is not None:
                    try:
                        data = resp.json()
                        err_msg = str(data)
                        if "image" in err_msg.lower() or "vision" in err_msg.lower():
                            raise RuntimeError(
                                "The selected AI model does not support image input. "
                                "Please switch to a vision-capable model."
                            )
                    except Exception:
                        pass
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if not content or not content.strip():
                    raise RuntimeError("AI returned an empty response. Please try again.")
                return content
        except RuntimeError:
            raise
        except Exception as e:
            last_error = e
            if attempt == MAX_RETRIES:
                break
            time.sleep(1)

    msg = str(last_error)
    if "does not support image" in msg.lower() or "does not support" in msg.lower():
        raise RuntimeError(
            "The selected AI model does not support image input. "
            "Please switch to a vision-capable model."
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


def generate(prompt: str, system: str = "", image_bytes: bytes = None, mime_type: str = None) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")
    return _call_openrouter(prompt, system, image_bytes, mime_type)
