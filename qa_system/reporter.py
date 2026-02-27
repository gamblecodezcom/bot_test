from __future__ import annotations

import json
from pathlib import Path

from .models import Scenario


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    tmp.replace(path)


def _error_type_for_role(role: str) -> str:
    if role == "invalid_user":
        return "invalid_user_state"
    if role == "rate_limited_user":
        return "rate_limit"
    return "none"


def write_logs(output_dir: Path, scenarios: list[Scenario], dry_run: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    action_log = []
    message_log = []
    error_log = []

    for scn in scenarios:
        if not scn.active:
            continue
        action_log.append(
            {
                "scenario_id": scn.scenario_id,
                "platform": scn.platform,
                "context": scn.context,
                "role": scn.role,
                "status": "simulated_pass" if dry_run else "pending_executor",
            }
        )
        message_log.append(
            {
                "scenario_id": scn.scenario_id,
                "messages": ["placeholder: connector response capture"],
            }
        )
        if scn.role in {"invalid_user", "rate_limited_user"}:
            error_log.append(
                {
                    "scenario_id": scn.scenario_id,
                    "context": scn.context,
                    "role": scn.role,
                    "error_type": _error_type_for_role(scn.role),
                    "reason": "Negative-path validation target",
                    "expected_behavior": "Explicit error + recovery guidance",
                }
            )

    _atomic_write_json(output_dir / "action_log.json", action_log)
    _atomic_write_json(output_dir / "message_log.json", message_log)
    _atomic_write_json(output_dir / "error_log.json", error_log)


def write_summary(output_dir: Path, scenario_count: int, command_count: int, button_count: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "summary": {
            "scenarios_generated": scenario_count,
            "commands_covered": command_count,
            "buttons_covered": button_count,
            "telegram_default": True,
            "discord_active": False,
        },
        "bugs_found": [],
        "broken_flows": [],
        "missing_error_messages": [],
        "ux_issues": [],
        "recommended_fixes": [],
    }
    _atomic_write_json(output_dir / "final_report.json", summary)


def write_improvements(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    content = """# Suggested Improvements

1. Standardize all error messages with action hints.
2. Add callback data versioning to prevent stale interactions.
3. Add strict context guards for DM/group/channel misuse.
4. Add adaptive retry/jitter for rate-limited endpoints.
5. Ensure admin flows have explicit unauthorized responses.
6. Add snapshot-based UI text consistency checks.
7. Add structured telemetry for onboarding drop-off diagnostics.
"""
    (output_dir / "improvements.md").write_text(content, encoding="utf-8")
