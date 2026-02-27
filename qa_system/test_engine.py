from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_test_plan(capabilities: dict[str, Any]) -> dict[str, Any]:
    contexts = capabilities.get("contexts", ["telegram_dm", "telegram_group", "telegram_channel"])
    commands = capabilities.get("commands", {})
    callbacks = capabilities.get("callbacks", [])
    menus = capabilities.get("menus", [])
    onboarding = capabilities.get("onboarding_steps", [])
    pending_actions = capabilities.get("pending_actions", [])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": {
            "dm_tests": [c for c in contexts if "dm" in c],
            "group_tests": [c for c in contexts if "group" in c],
            "channel_tests": [c for c in contexts if "channel" in c],
            "admin_tests": commands.get("admin", []),
            "user_tests": commands.get("user", []),
            "onboarding_tests": onboarding,
            "callback_tests": callbacks,
            "menu_tests": menus,
            "error_tests": capabilities.get("error_messages", []),
            "pending_action_tests": pending_actions,
        },
    }


def evaluate_message(text: str, capabilities: dict[str, Any]) -> dict[str, Any]:
    expected_success = set(capabilities.get("expected_success_messages", []))
    expected_failure = set(capabilities.get("expected_failure_messages", []))
    known_errors = set(capabilities.get("error_messages", []))

    bugs: list[str] = []
    missing_behavior: list[str] = []
    unexpected_errors: list[str] = []

    if expected_success and all(msg not in text for msg in expected_success):
        missing_behavior.append("missing_expected_success_message")
    if expected_failure and "error" in text.lower() and all(msg not in text for msg in expected_failure):
        missing_behavior.append("missing_expected_failure_message")
    if "error" in text.lower() and known_errors and all(err not in text for err in known_errors):
        unexpected_errors.append("undocumented_error")

    if "pending_action" in text and "error" in text.lower():
        bugs.append("pending_action_state_error")

    return {
        "bugs": bugs,
        "missing_behavior": missing_behavior,
        "unexpected_errors": unexpected_errors,
    }
