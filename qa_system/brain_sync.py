from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync QA logs/actions between VPS executor and external AI brain")
    parser.add_argument("--root", default="/var/www/html/Runewager", help="RuneWager project root")
    parser.add_argument("--export", default=None, help="Write export bundle JSON to this path")
    parser.add_argument("--queue", default=None, help="Queue action JSON file produced by AI brain")
    return parser.parse_args()


def _latest_log_dir(root: Path) -> Path | None:
    base = root / "qa" / "logs"
    if not base.exists():
        return None
    folders = sorted([p for p in base.iterdir() if p.is_dir()])
    return folders[-1] if folders else None


def _read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def export_bundle(root: Path, output: Path) -> None:
    log_dir = _latest_log_dir(root)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "log_dir": str(log_dir) if log_dir else None,
        "action_log": _read_json((log_dir / "action_log.json") if log_dir else root / "missing", []),
        "message_log": _read_json((log_dir / "message_log.json") if log_dir else root / "missing", []),
        "error_log": _read_json((log_dir / "error_log.json") if log_dir else root / "missing", []),
        "state": _read_json(root / "qa" / "state.json", {"qa_enabled": False, "mode": "user", "telegram_default": True}),
        "protocol": {
            "queue_action": {"type": "send_command|press_callback|set_mode", "payload": "object"},
            "required_commands": ["/qa_on", "/qa_off", "/qa_mode admin", "/qa_mode user"],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def queue_actions(root: Path, action_file: Path) -> None:
    queue_path = root / "qa" / "action_queue.jsonl"
    actions = json.loads(action_file.read_text(encoding="utf-8"))
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        for action in actions:
            f.write(json.dumps(action) + "\n")


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    if args.export:
        export_bundle(root, Path(args.export))
    if args.queue:
        queue_actions(root, Path(args.queue))


if __name__ == "__main__":
    main()
