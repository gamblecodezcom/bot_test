from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

AIProvider = Literal["openai", "anthropic", "groq", "openrouter"]


@dataclass(frozen=True)
class ProviderConfig:
    provider: AIProvider
    model: str
    api_key_env: str


DEFAULT_MODELS: dict[AIProvider, str] = {
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "groq": "llama-3.1-70b-versatile",
    "openrouter": "openai/gpt-4o-mini",
}

API_KEY_ENV: dict[AIProvider, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def resolve_provider(provider: str, model: str | None = None) -> ProviderConfig:
    normalized = provider.strip().lower()
    if normalized not in DEFAULT_MODELS:
        raise ValueError(f"Unsupported ai provider: {provider}")
    p = cast(AIProvider, normalized)
    return ProviderConfig(
        provider=p,
        model=model or DEFAULT_MODELS[p],
        api_key_env=API_KEY_ENV[p],
    )
