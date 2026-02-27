from __future__ import annotations

from pathlib import Path


def write_onboarding_flow_map(path: Path) -> None:
    content = """# Onboarding Flow Map (Telegram-First)

## New User
1. `/start` or first interaction.
2. Age confirmation.
3. Username/profile validation.
4. Required channel/group membership checks.
5. Profile initialization.
6. Missing-step recovery checks.

## Returning User
1. Detect existing profile.
2. Skip completed onboarding steps.
3. Verify state integrity and repair corrupted progress.

## Invalid User Paths
- Missing username.
- Expired/invalid deep link.
- Wrong context command execution.
- Incomplete required join actions.

> Discord flows are preserved but inactive while `TELEGRAM_DEFAULT = true`.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_admin_flow_map(path: Path) -> None:
    content = """# Admin Flow Map

1. Authenticate admin role.
2. Open admin panel entrypoint.
3. Validate all menu entries and pagination.
4. Promo controls:
   - Promo Alerts ON/OFF
   - Start/Stop Promo
   - Approve/Deny promo submissions
   - Deny reason assignment
5. Content controls:
   - Edit promo language
   - Edit terminology block list
   - Casino search
   - DB CTA URL update
6. Permission and error checks:
   - Missing role
   - Missing permissions
   - Wrong context
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_error_flow_map(path: Path) -> None:
    content = """# Error Flow Map

Test matrix for each command/button/callback in Telegram DM/group/channel contexts:

- 429 rate limit path
- Missing permissions
- Invalid command
- Wrong context (DM/group/channel)
- Missing onboarding
- Missing admin role
- Invalid callback payload
- Expired callback payload
- DB failure simulation
- Network failure simulation
- Timeout handling

Each error should assert:
1. Stable deterministic `error_code`.
2. User-facing deterministic message.
3. Internal structured log entry.
4. Recovery hint or retry behavior.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
