"""Mistral AI API client with retry logic and shared rate-limit cooldown."""
import asyncio
import json
import time
from typing import Any

from loguru import logger
from mistralai import Mistral

from app.config import settings

_client: Mistral | None = None
_semaphore = asyncio.Semaphore(1)

# Shared rate-limit state — written on 429, read before every call
_rate_limited_until: float = 0.0   # monotonic timestamp; 0 means no active cooldown
_last_call_at: float = 0.0         # monotonic timestamp of the last successful call
_INTER_CALL_DELAY = 1.5            # minimum seconds between successive Mistral calls


def get_mistral_client() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=settings.mistral_api_key)
    return _client


def _safe_parse_json(raw: str) -> Any:
    """Safely parse Mistral JSON responses, stripping markdown code fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned.strip())


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "rate_limit" in msg.lower() or "Rate limit" in msg


async def call_mistral(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 8192,
    max_retries: int = 5,
    response_format: dict | None = None,
) -> str:
    """
    Call Mistral API with retry logic.

    - Serializes all calls through a semaphore to prevent concurrent requests.
    - Enforces a minimum inter-call delay inside the semaphore.
    - On 429: sets a shared cooldown (30 s × attempt) so every queued task
      waits inside the semaphore instead of immediately hammering the API.
    """
    global _rate_limited_until, _last_call_at

    client = get_mistral_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(1, max_retries + 1):
        try:
            async with _semaphore:
                now = time.monotonic()

                # Wait out any active rate-limit cooldown before calling
                cooldown_remaining = _rate_limited_until - now
                if cooldown_remaining > 0:
                    logger.info(f"Rate-limit cooldown active — waiting {cooldown_remaining:.1f}s")
                    await asyncio.sleep(cooldown_remaining)

                # Enforce minimum spacing between successive calls
                gap = _last_call_at + _INTER_CALL_DELAY - time.monotonic()
                if gap > 0:
                    await asyncio.sleep(gap)

                _last_call_at = time.monotonic()

                kwargs: dict[str, Any] = {
                    "model": settings.mistral_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = await client.chat.complete_async(**kwargs)

            return response.choices[0].message.content

        except Exception as exc:
            logger.warning(f"Mistral API attempt {attempt}/{max_retries} failed: {exc}")
            if attempt == max_retries:
                raise RuntimeError(f"Mistral API failed after {max_retries} attempts") from exc

            if _is_rate_limit_error(exc):
                # Exponential cooldown: 30 s, 60 s, 90 s …
                # Shared globally so every other queued task also waits.
                wait = 30 * attempt
                _rate_limited_until = time.monotonic() + wait
                logger.warning(f"Rate limit hit — shared cooldown set to {wait}s before retry")
                await asyncio.sleep(wait)
            else:
                await asyncio.sleep(2 ** attempt)  # 2 s, 4 s, 8 s … for non-429 errors

    return ""  # unreachable


async def call_mistral_json(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 5,
) -> Any:
    """Call Mistral and return the parsed JSON object."""
    raw = await call_mistral(
        system_prompt,
        user_prompt,
        max_retries=max_retries,
        response_format={"type": "json_object"},
    )
    return _safe_parse_json(raw)
