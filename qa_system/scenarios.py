from __future__ import annotations

from typing import Literal

from .models import Context, Role, Scenario


def generate_scenarios() -> list[Scenario]:
    contexts: list[tuple[Literal["telegram", "discord"], Context]] = [
        ("telegram", "telegram_dm"),
        ("telegram", "telegram_group"),
        ("telegram", "telegram_channel"),
        ("discord", "discord_dm"),
        ("discord", "discord_server"),
    ]
    roles: list[Role] = ["new_user", "returning_user", "user", "admin", "invalid_user", "rate_limited_user"]

    scenarios: list[Scenario] = []
    counter = 1
    for platform, context in contexts:
        for role in roles:
            sid = f"SCN-{counter:04d}"
            counter += 1
            scenarios.append(
                Scenario(
                    scenario_id=sid,
                    platform=platform,
                    context=context,
                    role=role,
                    steps=(
                        "Open target context",
                        "Run baseline onboarding or profile check",
                        "Execute all discovered commands in deterministic order",
                        "Press all discovered buttons/callbacks in deterministic order",
                        "Trigger error injections: permission, context, callback expiry, timeout, rate-limit",
                    ),
                    expected=(
                        "All success paths return expected response",
                        "All failure paths return explicit actionable error",
                        "Admin/user restrictions enforced",
                        "Logs include structured records for every step",
                    ),
                )
            )
    return scenarios
