from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

Context = Literal[
    "telegram_dm",
    "telegram_group",
    "telegram_channel",
    "discord_dm",
    "discord_server",
]

Role = Literal["user", "admin", "new_user", "returning_user", "invalid_user", "rate_limited_user"]


@dataclass(frozen=True)
class CommandCase:
    command: str
    context: Context
    expected_result: str
    error_state: str
    role: Role
    notes: str


@dataclass(frozen=True)
class ButtonCase:
    button_or_callback: str
    context: Context
    success_path: str
    failure_path: str
    missing_permissions: str
    missing_onboarding: str
    rate_limit_behavior: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    platform: Literal["telegram", "discord"]
    context: Context
    role: Role
    steps: list[str]
    expected: list[str]

    def to_dict(self) -> dict:
        return asdict(self)
