from __future__ import annotations

from typing import Literal

from .models import Context, Role, Scenario


def generate_scenarios() -> list[Scenario]:
    telegram_contexts: list[tuple[Literal["telegram"], Context]] = [
        ("telegram", "telegram_dm"),
        ("telegram", "telegram_group"),
        ("telegram", "telegram_channel"),
    ]
    discord_inactive_contexts: list[tuple[Literal["discord"], Context]] = [
        ("discord", "discord_dm_inactive"),
        ("discord", "discord_server_inactive"),
    ]
    roles: list[Role] = ["new_user", "returning_user", "user", "admin", "invalid_user", "rate_limited_user"]

    scenarios: list[Scenario] = []
    counter = 1

    for platform, context in telegram_contexts:
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
                        "Run onboarding/profile checks by active qa mode",
                        "Execute queued commands in deterministic order",
                        "Press discovered inline buttons and callbacks",
                        "Trigger error injections: permission, context, callback expiry, timeout, rate-limit",
                    ),
                    expected=(
                        "Success paths return expected response",
                        "Failure paths return explicit actionable errors",
                        "Admin/user restrictions enforced",
                        "Logs include structured records for every step",
                    ),
                    active=True,
                )
            )

    for platform, context in discord_inactive_contexts:
        sid = f"SCN-{counter:04d}"
        counter += 1
        scenarios.append(
            Scenario(
                scenario_id=sid,
                platform=platform,
                context=context,
                role="user",
                steps=("Discord preserved for future expansion",),
                expected=("No active execution while TELEGRAM_DEFAULT is true",),
                active=False,
            )
        )

    return scenarios
