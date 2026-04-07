"""Mistral AI API client with retry logic."""
import json
import time
from typing import Any

from loguru import logger
from mistralai import Mistral

from app.config import settings

_client: Mistral | None = None


def get_mistral_client() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=settings.mistral_api_key)
    return _client


def _safe_parse_json(raw: str) -> Any:
    """Safely parse Mistral JSON responses, stripping markdown code fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (```json or ```)
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned.strip())


async def call_mistral(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    max_retries: int = 3,
) -> str:
    """
    Call Mistral API with retry logic (3 attempts with exponential back-off).
    Returns the raw text content of the response.
    """
    client = get_mistral_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.complete(
                model=settings.mistral_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.warning(f"Mistral API attempt {attempt}/{max_retries} failed: {exc}")
            if attempt == max_retries:
                raise RuntimeError(f"Mistral API failed after {max_retries} attempts") from exc
            time.sleep(2**attempt)  # exponential back-off: 2s, 4s
    return ""  # unreachable


async def call_mistral_json(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3,
) -> Any:
    """Call Mistral and return the parsed JSON object."""
    raw = await call_mistral(system_prompt, user_prompt, max_retries=max_retries)
    return _safe_parse_json(raw)
