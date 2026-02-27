from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bot_registry import BotRegistry
from .capabilities import load_capabilities, load_repo_info
from .config import DEFAULT_ROOT


@dataclass
class QAState:
    qa_enabled: bool = False
    mode: str = "user"
    telegram_default: bool = True
    selected_bot: str = "runewager"

    def as_dict(self) -> dict[str, Any]:
        return {
            "qa_enabled": self.qa_enabled,
            "mode": self.mode,
            "telegram_default": self.telegram_default,
            "selected_bot": self.selected_bot,
        }


class QAExecutor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.registry = BotRegistry(root)
        self.registry.ensure_defaults()
        self.state_file = root / "qa" / "state" / "executor_state.json"
        self.state = self._load_state()
        self._processed_actions = 0

    def _bot_queue_file(self, bot_name: str) -> Path:
        return self.root / "qa" / "actions" / bot_name / "queue.json"

    def _today_dir(self, bot_name: str) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.root / "qa" / "logs" / bot_name / day

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_state(self) -> QAState:
        raw = self._read_json(
            self.state_file,
            {"qa_enabled": False, "mode": "user", "telegram_default": True, "selected_bot": self.registry.selected_bot()},
        )
        return QAState(
            qa_enabled=bool(raw.get("qa_enabled", False)),
            mode=str(raw.get("mode", "user")),
            telegram_default=bool(raw.get("telegram_default", True)),
            selected_bot=str(raw.get("selected_bot", self.registry.selected_bot())),
        )

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state.as_dict(), indent=2), encoding="utf-8")

    def _current_bot_config(self):
        return self.registry.load_bot(self.state.selected_bot)

    def write_log(self, entry: dict[str, Any], log_name: str = "action_log.json") -> None:
        bot_name = self.state.selected_bot
        day_dir = self._today_dir(bot_name)
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / log_name
        logs = self._read_json(path, [])
        logs.append(entry)
        path.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    def queue_action(self, action_type: str, payload: dict[str, Any], bot_name: str | None = None) -> None:
        selected_bot = bot_name or self.state.selected_bot
        queue_file = self._bot_queue_file(selected_bot)
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_id": f"act-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{self._processed_actions}",
            "type": action_type,
            "payload": payload,
            "bot_name": selected_bot,
        }
        queued = self._read_json(queue_file, [])
        queued.append(envelope)
        queue_file.write_text(json.dumps(queued, indent=2), encoding="utf-8")

    def get_recent_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        messages = self._read_json(self._today_dir(self.state.selected_bot) / "message_log.json", [])
        return messages[-limit:]

    def get_buttons(self) -> list[str]:
        values: list[str] = []
        for message in self.get_recent_messages(limit=20):
            values.extend(message.get("buttons", []))
        return sorted(set(values))

    def get_callbacks(self) -> list[str]:
        values: list[str] = []
        for message in self.get_recent_messages(limit=20):
            values.extend(message.get("callbacks", []))
        return sorted(set(values))

    def get_state(self) -> dict[str, Any]:
        cfg = self._current_bot_config()
        capabilities = load_capabilities(cfg.capabilities_path)
        repo_info = load_repo_info(cfg.repo_info_path)
        return {**self.state.as_dict(), "bot_username": cfg.bot_username, "repo_info": repo_info, "capability_sections": sorted(capabilities.keys())}

    def _apply_control_command(self, text: str) -> bool:
        stripped = text.strip()
        if stripped == "/qa_on":
            self.state.qa_enabled = True
        elif stripped == "/qa_off":
            self.state.qa_enabled = False
        elif stripped == "/qa_status":
            self.write_log({"timestamp": datetime.now(timezone.utc).isoformat(), "status": self.get_state()})
        elif stripped.startswith("/qa_mode"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in {"admin", "user"}:
                self.state.mode = parts[1]
            else:
                return False
        elif stripped.startswith("/qa/select_bot"):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                self.registry.select_bot(parts[1].strip())
                self.state.selected_bot = parts[1].strip()
            else:
                return False
        else:
            return False
        self._save_state()
        return True

    def _consume_actions(self) -> list[dict[str, Any]]:
        queue_file = self._bot_queue_file(self.state.selected_bot)
        if not queue_file.exists():
            return []
        parsed = self._read_json(queue_file, [])
        queue_file.write_text("[]", encoding="utf-8")
        self._processed_actions += len(parsed)
        return parsed

    def _extract_debug_metadata(self, message: Any) -> dict[str, Any]:
        text = (message.text or message.caption or "") if message else ""
        metadata = {"menu_id": None, "callback_id": None, "pending_action": None, "error_code": None}
        for key in metadata:
            marker = f"{key}:"
            if marker in text:
                part = text.split(marker, 1)[1].split("\n", 1)[0].strip()
                metadata[key] = part
        return metadata

    async def run_service(self, poll_interval: float = 1.0) -> None:
        bot_cfg = self._current_bot_config()
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        session_name = str(self.root / "qa" / "runtime" / "qa_userbot")

        try:
            from pyrogram import Client
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("pyrogram is required for executor service") from exc

        app = Client(session_name, api_id=int(api_id) if api_id else None, api_hash=api_hash)
        async with app:
            while True:
                bot_cfg = self._current_bot_config()
                capabilities = load_capabilities(bot_cfg.capabilities_path)
                actions = self._consume_actions()

                if not self.state.qa_enabled:
                    await asyncio.sleep(poll_interval)
                    continue

                for action in actions:
                    action_type = action.get("type", "")
                    payload = action.get("payload", {})
                    if action_type == "set_mode":
                        mode = payload.get("mode", "")
                        if mode in {"user", "admin"}:
                            self.state.mode = mode
                            self._save_state()
                            self.write_log({"timestamp": action["timestamp"], "action": "set_mode", "mode": mode})
                    elif action_type == "send_command":
                        text = str(payload.get("text", "")).strip()
                        if self._apply_control_command(text):
                            self.write_log({"timestamp": action["timestamp"], "action": text, "mode": self.state.mode})
                            continue
                        sent = await app.send_message(bot_cfg.bot_username, text)
                        self.write_log({"timestamp": action["timestamp"], "action": "send_command", "text": text, "message_id": sent.id, "mode": self.state.mode})
                    elif action_type == "press_callback":
                        self.write_log({"timestamp": action["timestamp"], "action": "press_callback", "payload": payload, "mode": self.state.mode})
                    else:
                        self.write_log({"timestamp": action.get("timestamp"), "error": "unsupported_action", "action": action}, "error_log.json")

                history = []
                async for msg in app.get_chat_history(bot_cfg.bot_username, limit=5):
                    debug = self._extract_debug_metadata(msg)
                    history.append(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "message_id": msg.id,
                            "text": msg.text or msg.caption or "",
                            "buttons": [btn.text for row in (msg.reply_markup.inline_keyboard if msg.reply_markup else []) for btn in row],
                            "callbacks": [btn.callback_data for row in (msg.reply_markup.inline_keyboard if msg.reply_markup else []) for btn in row if getattr(btn, "callback_data", None)],
                            "mode": self.state.mode,
                            "bot": self.state.selected_bot,
                            "debug_metadata": debug,
                            "expected_success_messages": capabilities.get("expected_success_messages", []),
                            "expected_failure_messages": capabilities.get("expected_failure_messages", []),
                        }
                    )
                if history:
                    for entry in reversed(history):
                        self.write_log(entry, "message_log.json")

                await asyncio.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RuneWager Telegram QA executor")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Project root")
    parser.add_argument("--service", action="store_true", help="Run long-lived QA executor service")
    parser.add_argument("--queue-action", default=None, help="Queue action type")
    parser.add_argument("--payload", default="{}", help="JSON payload for queued action")
    parser.add_argument("--bot-name", default=None, help="Optional bot name for queue actions")
    parser.add_argument("--select-bot", default=None, help="Select active bot")
    parser.add_argument("--list-bots", action="store_true", help="List registered bots")
    parser.add_argument("--state", action="store_true", help="Print current state")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    executor = QAExecutor(Path(args.root))
    if args.list_bots:
        print(json.dumps(executor.registry.list_bots(), indent=2))
        return
    if args.select_bot:
        executor.registry.select_bot(args.select_bot)
        executor.state.selected_bot = args.select_bot
        executor._save_state()
        return
    if args.queue_action:
        executor.queue_action(args.queue_action, json.loads(args.payload), bot_name=args.bot_name)
        return
    if args.state:
        print(json.dumps(executor.get_state(), indent=2))
        return
    if args.service:
        asyncio.run(executor.run_service())
        return
    raise SystemExit("Use one of: --service | --queue-action | --state | --list-bots | --select-bot")


if __name__ == "__main__":
    main()
