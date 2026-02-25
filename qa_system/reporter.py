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

    test_log = []
    failure_log = []

    for scn in scenarios:
        entry = {
            "scenario_id": scn.scenario_id,
            "platform": scn.platform,
            "context": scn.context,
            "role": scn.role,
            "status": "simulated_pass" if dry_run else "pending_connector",
        }
        test_log.append(entry)
        if scn.role in {"invalid_user", "rate_limited_user"}:
            failure_log.append(
                {
                    "scenario_id": scn.scenario_id,
                    "platform": scn.platform,
                    "context": scn.context,
                    "role": scn.role,
                    "error_type": _error_type_for_role(scn.role),
                    "reason": "Negative-path validation target",
                    "expected_behavior": "Explicit error + recovery guidance",
                }
            )

    _atomic_write_json(output_dir / "test_log.json", test_log)
    _atomic_write_json(output_dir / "failure_log.json", failure_log)


def write_summary(output_dir: Path, scenario_count: int, command_count: int, button_count: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = f"""# QA Summary Report

- Scenarios generated: **{scenario_count}**
- Commands covered: **{command_count}**
- Buttons/callbacks covered: **{button_count}**
- Context coverage: Telegram DM/Group/Channel + Discord DM/Server
- Role coverage: user/admin/new/returning/invalid/rate-limited

## Bug list policy
Use `failure_log.json` for confirmed and expected negative-path failures.

## Improvement policy
Use `improvements.md` for UX and reliability recommendations.
"""
    (output_dir / "summary_report.md").write_text(summary, encoding="utf-8")


def write_improvements(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    content = """# Suggested Improvements

1. Standardize all error messages with action hints.
2. Add callback data versioning to prevent stale interactions.
3. Add strict context guards for DM/group/channel/server misuse.
4. Add adaptive retry/jitter for rate-limited endpoints.
5. Ensure admin flows have explicit unauthorized responses.
6. Add snapshot-based UI text consistency checks.
7. Add structured telemetry for onboarding drop-off diagnostics.
"""
    (output_dir / "improvements.md").write_text(content, encoding="utf-8")
