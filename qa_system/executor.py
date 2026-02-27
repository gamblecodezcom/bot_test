from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class QAState:
    qa_enabled: bool = False
    mode: str = "user"
    telegram_default: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {"qa_enabled": self.qa_enabled, "mode": self.mode, "telegram_default": self.telegram_default}


class QAExecutor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.queue_file = root / "qa" / "action_queue.jsonl"
        self.state_file = root / "qa" / "state.json"
        self.runtime_dir = root / "qa" / "runtime"
        self.state = self._load_state()
        self._processed_actions = 0

    def _today_dir(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.root / "qa" / "logs" / day

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_state(self) -> QAState:
        raw = self._read_json(self.state_file, {"qa_enabled": False, "mode": "user", "telegram_default": True})
        return QAState(
            qa_enabled=bool(raw.get("qa_enabled", False)),
            mode=str(raw.get("mode", "user")),
            telegram_default=bool(raw.get("telegram_default", True)),
        )

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state.as_dict(), indent=2), encoding="utf-8")

    def write_log(self, log_name: str, entry: dict[str, Any]) -> None:
        day_dir = self._today_dir()
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / log_name
        logs = self._read_json(path, [])
        logs.append(entry)
        path.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    def queue_action(self, action_type: str, payload: dict[str, Any]) -> None:
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action_id": f"act-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{self._processed_actions}",
            "type": action_type,
            "payload": payload,
        }
        with self.queue_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(envelope) + "\n")

    def get_recent_messages(self, limit: int = 10) -> list[dict[str, Any]]:
        messages = self._read_json(self._today_dir() / "message_log.json", [])
        return messages[-limit:]

    def get_buttons(self) -> list[str]:
        messages = self.get_recent_messages(limit=20)
        values: list[str] = []
        for message in messages:
            values.extend(message.get("buttons", []))
        return sorted(set(values))

    def get_callbacks(self) -> list[str]:
        messages = self.get_recent_messages(limit=20)
        values: list[str] = []
        for message in messages:
            values.extend(message.get("callbacks", []))
        return sorted(set(values))

    def get_state(self) -> dict[str, Any]:
        return self.state.as_dict()

    def _apply_toggle_command(self, text: str) -> bool:
        if text.strip() == "/qa_on":
            self.state.qa_enabled = True
        elif text.strip() == "/qa_off":
            self.state.qa_enabled = False
        elif text.startswith("/qa_mode"):
            parts = text.split(maxsplit=1)
            if len(parts) == 2 and parts[1].strip() in {"admin", "user"}:
                self.state.mode = parts[1].strip()
        else:
            return False
        self._save_state()
        return True

    def _consume_actions(self) -> list[dict[str, Any]]:
        if not self.queue_file.exists():
            return []
        lines = [line.strip() for line in self.queue_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.queue_file.write_text("", encoding="utf-8")
        parsed = [json.loads(line) for line in lines]
        self._processed_actions += len(parsed)
        return parsed

    async def run_service(self, poll_interval: float = 1.0) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        session_name = str(self.runtime_dir / "qa_userbot")
        target_bot = os.getenv("QA_TARGET_BOT", "")

        try:
            from pyrogram import Client
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("pyrogram is required for executor service") from exc

        app = Client(session_name, api_id=int(api_id) if api_id else None, api_hash=api_hash)
        async with app:
            while True:
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
                    elif action_type == "send_command":
                        text = str(payload.get("text", "")).strip()
                        if self._apply_toggle_command(text):
                            self.write_log("action_log.json", {"timestamp": action["timestamp"], "action": text, "mode": self.state.mode})
                            continue
                        if target_bot and text:
                            sent = await app.send_message(target_bot, text)
                            self.write_log("action_log.json", {"timestamp": action["timestamp"], "action": "send_command", "text": text, "message_id": sent.id, "mode": self.state.mode})
                    elif action_type == "press_callback":
                        self.write_log("action_log.json", {"timestamp": action["timestamp"], "action": "press_callback", "payload": payload, "mode": self.state.mode})
                    else:
                        self.write_log("error_log.json", {"timestamp": action.get("timestamp"), "error": "unsupported_action", "action": action})

                if target_bot:
                    history = []
                    async for msg in app.get_chat_history(target_bot, limit=5):
                        history.append(
                            {
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "message_id": msg.id,
                                "text": msg.text or msg.caption or "",
                                "buttons": [btn.text for row in (msg.reply_markup.inline_keyboard if msg.reply_markup else []) for btn in row],
                                "callbacks": [btn.callback_data for row in (msg.reply_markup.inline_keyboard if msg.reply_markup else []) for btn in row if getattr(btn, "callback_data", None)],
                                "mode": self.state.mode,
                            }
                        )
                    if history:
                        for entry in reversed(history):
                            self.write_log("message_log.json", entry)

                await asyncio.sleep(poll_interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RuneWager Telegram QA executor")
    parser.add_argument("--root", default="/var/www/html/Runewager", help="RuneWager project root")
    parser.add_argument("--service", action="store_true", help="Run long-lived QA executor service")
    parser.add_argument("--queue-action", default=None, help="Queue action type")
    parser.add_argument("--payload", default="{}", help="JSON payload for queued action")
    parser.add_argument("--state", action="store_true", help="Print current state")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    executor = QAExecutor(Path(args.root))
    if args.queue_action:
        executor.queue_action(args.queue_action, json.loads(args.payload))
        return
    if args.state:
        print(json.dumps(executor.get_state(), indent=2))
        return
    if args.service:
        asyncio.run(executor.run_service())
        return
    raise SystemExit("Use one of: --service | --queue-action | --state")


if __name__ == "__main__":
    main()
