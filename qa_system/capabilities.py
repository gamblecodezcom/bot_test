from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_capabilities(path: Path) -> dict[str, Any]:
    return load_json(
        path,
        {
            "commands": {"user": ["/start"], "admin": ["/admin"]},
            "callbacks": ["admin_menu"],
            "menus": ["main"],
            "onboarding_steps": ["start"],
            "pending_actions": [],
            "error_messages": [],
            "eligibility_rules": [],
            "rate_limits": [],
            "contexts": ["telegram_dm", "telegram_group", "telegram_channel"],
            "expected_success_messages": [],
            "expected_failure_messages": [],
            "debug_metadata": ["menu_id", "callback_id", "pending_action", "error_code"],
        },
    )


def load_repo_info(path: Path) -> dict[str, Any]:
    return load_json(path, {"name": "unknown", "version": "unknown", "default_branch": "main"})
