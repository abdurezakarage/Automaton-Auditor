from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI  # type: ignore[import]


def get_llm() -> ChatOpenAI:
    """
    Return a configured ChatOpenAI client.

    Prefers OpenRouter if OPENROUTER_API_KEY is set; otherwise falls back to OpenAI.
    Raises RuntimeError if no suitable API key is found.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        # Use a simple default model ID; users can override via OPENROUTER_MODEL.
        model = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            api_key=openrouter_key,
            base_url=base_url,
            model=model,
            temperature=0,
        )

    if openai_key:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(
            api_key=openai_key,
            model=model,
            temperature=0,
        )

    raise RuntimeError(
        "No LLM API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY in your environment."
    )

