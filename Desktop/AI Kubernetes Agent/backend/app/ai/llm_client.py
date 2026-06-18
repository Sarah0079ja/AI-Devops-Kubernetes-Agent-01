import httpx
from loguru import logger

from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60.0

# Status codes that are permanent failures — no point retrying
_NO_RETRY_CODES = {400, 401, 403, 404, 422}


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Send a chat request to OpenRouter and return the assistant message content.

    Retries up to MAX_RETRIES times on transient failures (5xx, timeout).
    Raises on permanent errors (auth, bad request, etc.).
    """
    if not settings.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set — add it to backend/.env"
        )

    model = settings.openrouter_model or DEFAULT_MODEL
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-kubernetes-agent",
        "X-Title": "AI Kubernetes Agent",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
    }

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"LLM call attempt {attempt}/{MAX_RETRIES} — model: {model}")
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                response = client.post(OPENROUTER_URL, headers=headers, json=payload)

            if response.status_code in _NO_RETRY_CODES:
                logger.error(f"LLM permanent error {response.status_code}: {response.text[:300]}")
                response.raise_for_status()

            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            logger.info("LLM call succeeded")
            return content

        except httpx.TimeoutException as e:
            logger.warning(f"LLM timeout on attempt {attempt}")
            last_error = e

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP {e.response.status_code} on attempt {attempt}")
            last_error = e
            if e.response.status_code in _NO_RETRY_CODES:
                raise

        except Exception as e:
            logger.error(f"Unexpected LLM error on attempt {attempt}: {e}")
            last_error = e

    raise RuntimeError(
        f"LLM call failed after {MAX_RETRIES} attempts"
    ) from last_error
