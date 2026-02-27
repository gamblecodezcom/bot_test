from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

AIProvider = Literal["termux_qwen", "termux_deepseek_r1", "deepseek_chat", "gemini_free", "chatgpt_free"]


@dataclass(frozen=True)
class ProviderConfig:
    provider: AIProvider
    model: str
    api_key_env: str
    execution_location: str


DEFAULT_MODELS: dict[AIProvider, str] = {
    "termux_qwen": "qwen2.5-1.5b-instruct",
    "termux_deepseek_r1": "deepseek-r1-1.5b",
    "deepseek_chat": "deepseek-chat",
    "gemini_free": "gemini-2.0-flash-lite",
    "chatgpt_free": "gpt-4o-mini",
}

API_KEY_ENV: dict[AIProvider, str] = {
    "termux_qwen": "",
    "termux_deepseek_r1": "",
    "deepseek_chat": "DEEPSEEK_API_KEY",
    "gemini_free": "GEMINI_API_KEY",
    "chatgpt_free": "OPENAI_API_KEY",
}

EXECUTION_LOCATION: dict[AIProvider, str] = {
    "termux_qwen": "android_termux_local",
    "termux_deepseek_r1": "android_termux_local",
    "deepseek_chat": "external_cloud",
    "gemini_free": "external_cloud",
    "chatgpt_free": "external_cloud",
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
        execution_location=EXECUTION_LOCATION[p],
    )
