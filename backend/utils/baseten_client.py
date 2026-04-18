import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY", "")
BASETEN_MODEL_ID = os.getenv("BASETEN_MODEL_ID", "openai/gpt-oss-120b")
BASETEN_BASE_URL = os.getenv("BASETEN_BASE_URL", "https://inference.baseten.co/v1")


def _client() -> AsyncOpenAI:
    if not BASETEN_API_KEY:
        raise RuntimeError(
            "BASETEN_API_KEY is not set. Either set it in .env or run with "
            "USE_MOCK_PIPELINE=true."
        )
    return AsyncOpenAI(api_key=BASETEN_API_KEY, base_url=BASETEN_BASE_URL)


async def complete(prompt: str, max_tokens: int = 4000) -> str:
    """Single-shot chat completion. Returns the raw assistant text.

    GPT-OSS 120B reserves budget for `reasoning_content` on top of visible
    `content`. We set `reasoning_effort="low"` to keep the reasoning trace
    short, and fall back to `reasoning_content` if `content` is empty.
    """
    client = _client()
    response = await client.chat.completions.create(
        model=BASETEN_MODEL_ID,
        max_tokens=max_tokens,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
        extra_body={"reasoning_effort": "low"},
    )
    msg = response.choices[0].message
    text = (msg.content or "").strip()
    if not text:
        # Fallback: some deployments emit the answer in reasoning_content.
        rc = getattr(msg, "reasoning_content", None) or ""
        text = rc.strip()
    return text


async def chat(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 1500,
    temperature: float = 0.2,
) -> Any:
    """Lower-level chat call used by the Veris tool-use agents."""
    client = _client()
    kwargs: Dict[str, Any] = {
        "model": BASETEN_MODEL_ID,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "extra_body": {"reasoning_effort": "low"},
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return await client.chat.completions.create(**kwargs)
