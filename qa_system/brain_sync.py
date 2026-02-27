from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .bot_registry import BotRegistry
from .provider_fallback import ProviderFallbackManager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync QA logs/actions between VPS executor and external AI brain")
    parser.add_argument("--root", default="/var/www/html/Runewager", help="Project root")
    parser.add_argument("--bot", default=None, help="Bot name override")
    parser.add_argument("--export", default=None, help="Write export bundle JSON to this path")
    parser.add_argument("--queue", default=None, help="Queue action JSON file produced by AI brain")
    parser.add_argument("--provider-result", default=None, help="Mark provider result: deepseek:success|gemini:failure|chatgpt:failure")
    parser.add_argument("--pick-provider", action="store_true", help="Pick next provider by fallback policy")
    return parser.parse_args()


def _latest_log_dir(root: Path, bot_name: str) -> Path | None:
    base = root / "qa" / "logs" / bot_name
    if not base.exists():
        return None
    folders = sorted([p for p in base.iterdir() if p.is_dir()])
    return folders[-1] if folders else None


def _read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def export_bundle(root: Path, bot_name: str, output: Path) -> None:
    log_dir = _latest_log_dir(root, bot_name)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "bot": bot_name,
        "log_dir": str(log_dir) if log_dir else None,
        "action_log": _read_json((log_dir / "action_log.json") if log_dir else root / "missing", []),
        "message_log": _read_json((log_dir / "message_log.json") if log_dir else root / "missing", []),
        "error_log": _read_json((log_dir / "error_log.json") if log_dir else root / "missing", []),
        "state": _read_json(root / "qa" / "state" / "executor_state.json", {"qa_enabled": False, "mode": "user", "telegram_default": True}),
        "provider_status": _read_json(root / "qa" / "state" / "provider_status.json", {}),
        "protocol": {
            "queue_action": {"type": "send_command|press_callback|set_mode", "payload": "object", "bot_name": bot_name},
            "required_commands": ["/qa_on", "/qa_off", "/qa_mode admin", "/qa_mode user", f"/qa/select_bot {bot_name}"],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def queue_actions(root: Path, bot_name: str, action_file: Path) -> None:
    queue_path = root / "qa" / "actions" / bot_name / "queue.json"
    actions = json.loads(action_file.read_text(encoding="utf-8"))
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    current = _read_json(queue_path, [])
    for action in actions:
        if "bot_name" not in action:
            action["bot_name"] = bot_name
        current.append(action)
    queue_path.write_text(json.dumps(current, indent=2), encoding="utf-8")


def apply_provider_result(root: Path, result: str) -> None:
    manager = ProviderFallbackManager(root / "qa" / "state" / "provider_status.json")
    provider, status = result.split(":", maxsplit=1)
    if status == "success":
        manager.mark_success(provider)
    else:
        manager.mark_failure(provider, rate_limited=True)


def pick_provider(root: Path) -> str:
    manager = ProviderFallbackManager(root / "qa" / "state" / "provider_status.json")
    provider = manager.pick_provider()
    if provider:
        return provider
    wait_for = manager.all_failed_wait() or 60
    time.sleep(wait_for)
    return manager.pick_provider() or "deepseek"


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    registry = BotRegistry(root)
    registry.ensure_defaults()
    bot_name = args.bot or registry.selected_bot()

    if args.export:
        export_bundle(root, bot_name, Path(args.export))
    if args.queue:
        queue_actions(root, bot_name, Path(args.queue))
    if args.provider_result:
        apply_provider_result(root, args.provider_result)
    if args.pick_provider:
        print(pick_provider(root))


if __name__ == "__main__":
    main()
