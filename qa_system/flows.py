from __future__ import annotations

from pathlib import Path


def write_onboarding_flow_map(path: Path) -> None:
    content = """# Onboarding Flow Map (Telegram + Discord)

## New User
1. `/start` or first interaction.
2. Age confirmation.
3. Username/linking validation.
4. Discord link step (if originated on Telegram) / Telegram link step (if originated on Discord).
5. Channel + group/server membership checks.
6. WebApp/profile initialization.
7. Missing-step recovery checks.

## Returning User
1. Detect existing profile.
2. Skip completed onboarding steps.
3. Verify state integrity and repair corrupted progress.

## Invalid User Paths
- Missing username.
- Missing linked account.
- Expired/invalid deep link.
- Wrong context command execution.
- Incomplete required join actions.
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

Test matrix for each command/button/callback in each context:

- 429 rate limit path
- Missing permissions
- Invalid command
- Wrong context (DM/group/channel/server)
- Missing onboarding
- Missing admin role
- Invalid callback payload
- Expired callback payload
- DB failure simulation
- Network failure simulation
- Timeout handling

Each error should assert:
1. Stable deterministic `error_code` (e.g., `response.error_code`).
2. User-facing deterministic message.
3. Internal structured log entry.
4. Recovery hint or retry behavior.

Shared assertion helpers (for example `assertErrorStructure`) should validate `error_code` first, then message/log/recovery fields.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
