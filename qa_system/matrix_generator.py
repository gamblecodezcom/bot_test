from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import ButtonCase, CommandCase

# Match slash-commands while avoiding URLs and markdown links.
_COMMAND_PATTERNS = [
    re.compile(r"(?<!:)\B/(?:[a-z][a-z0-9_]{1,63})\b", re.IGNORECASE),
    re.compile(r"\bslash\s*[:=]\s*[\"']([^\"']+)[\"']", re.IGNORECASE),
    re.compile(r"\bcommand\s*[:=]\s*[\"']([^\"']+)[\"']", re.IGNORECASE),
]

_BUTTON_PATTERNS = [
    re.compile(r"callback_data\s*=\s*[\"']([^\"']+)[\"']"),
    re.compile(r"custom_id\s*=\s*[\"']([^\"']+)[\"']"),
    re.compile(r"InlineKeyboardButton\([^\)]*text\s*=\s*[\"']([^\"']+)[\"']"),
]

_SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "qa_artifacts",
    "__pycache__",
}

_SOURCE_EXTS = {".py", ".js", ".ts", ".go", ".rs"}


def _iter_source_files(repo_root: Path):
    for path in sorted(repo_root.rglob("*")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in _SOURCE_EXTS:
            yield path


def _normalize_command(token: str) -> str | None:
    cmd = token.strip()
    if not cmd:
        return None
    cmd = cmd if cmd.startswith("/") else f"/{cmd}"
    return cmd.lower()


def discover_commands(repo_root: Path) -> list[str]:
    found: set[str] = set()
    for file in _iter_source_files(repo_root):
        text = file.read_text(errors="ignore")
        for pattern in _COMMAND_PATTERNS:
            for match in pattern.findall(text):
                token = match if isinstance(match, str) else match[0]
                cmd = _normalize_command(token)
                if cmd:
                    found.add(cmd)
    if not found:
        found.update({"/start", "/help", "/admin"})
    return sorted(found)


def discover_buttons(repo_root: Path) -> list[str]:
    found: set[str] = set()
    for file in _iter_source_files(repo_root):
        text = file.read_text(errors="ignore")
        for pattern in _BUTTON_PATTERNS:
            for match in pattern.findall(text):
                token = match if isinstance(match, str) else match[0]
                token = token.strip()
                if token:
                    found.add(token)
    if not found:
        found.update({"btn_onboarding_continue", "cb_admin_promo_on", "cb_admin_promo_off"})
    return sorted(found)


def build_command_matrix(commands: list[str]) -> list[CommandCase]:
    contexts = ["telegram_dm", "telegram_group", "telegram_channel", "discord_dm", "discord_server"]
    rows: list[CommandCase] = []
    for command in commands:
        for context in contexts:
            rows.append(
                CommandCase(
                    command=command,
                    context=context,
                    expected_result="Command executes with success response in valid context",
                    error_state="Shows context/permission/onboarding/rate-limit aware error",
                    role="user",
                    notes="Also execute with admin, invalid user, and rate-limited variants",
                )
            )
    return rows


def build_button_matrix(buttons: list[str]) -> list[ButtonCase]:
    contexts = ["telegram_dm", "telegram_group", "telegram_channel", "discord_dm", "discord_server"]
    rows: list[ButtonCase] = []
    for button in buttons:
        for context in contexts:
            rows.append(
                ButtonCase(
                    button_or_callback=button,
                    context=context,
                    success_path="Target action completes and UI updates",
                    failure_path="Invalid state returns deterministic error",
                    missing_permissions="Permission denied message with remediation",
                    missing_onboarding="Prompt user to complete missing onboarding steps",
                    rate_limit_behavior="429-safe backoff + user-visible retry hint",
                )
            )
    return rows


def write_command_matrix(path: Path, rows: list[CommandCase]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["command", "context", "expected_result", "error_state", "role", "notes"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_button_matrix(path: Path, rows: list[ButtonCase]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "button_or_callback",
                "context",
                "success_path",
                "failure_path",
                "missing_permissions",
                "missing_onboarding",
                "rate_limit_behavior",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
