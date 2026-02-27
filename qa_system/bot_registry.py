from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DEFAULT_BOT_NAME


@dataclass(frozen=True)
class BotConfig:
    name: str
    bot_username: str
    repo_path: Path
    capabilities_path: Path
    md_path: Path
    repo_info_path: Path


class BotRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.registry_path = root / "qa" / "bots" / "bot_list.json"
        self.selection_path = root / "qa" / "state" / "selected_bot.json"

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def list_bots(self) -> dict[str, dict[str, Any]]:
        return self._read_json(self.registry_path, {})

    def ensure_defaults(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.selection_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            self.registry_path.write_text(
                json.dumps(
                    {
                        DEFAULT_BOT_NAME: {
                            "bot_username": "RunewagerBot",
                            "repo_path": str(self.root),
                            "capabilities_path": str(self.root / "qa" / "context" / "bot_capabilities.json"),
                            "md_path": str(self.root / "RUNEWAGER_FUNCTIONALITY_MAP.md"),
                            "repo_info_path": str(self.root / "qa" / "context" / "repo_info.json"),
                        }
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        if not self.selection_path.exists():
            self.selection_path.write_text(json.dumps({"selected_bot": DEFAULT_BOT_NAME}, indent=2), encoding="utf-8")

    def select_bot(self, bot_name: str) -> None:
        bots = self.list_bots()
        if bot_name not in bots:
            raise ValueError(f"Unknown bot: {bot_name}")
        self.selection_path.parent.mkdir(parents=True, exist_ok=True)
        self.selection_path.write_text(json.dumps({"selected_bot": bot_name}, indent=2), encoding="utf-8")

    def selected_bot(self) -> str:
        data = self._read_json(self.selection_path, {"selected_bot": DEFAULT_BOT_NAME})
        return str(data.get("selected_bot", DEFAULT_BOT_NAME))

    def load_bot(self, bot_name: str | None = None) -> BotConfig:
        name = bot_name or self.selected_bot()
        bots = self.list_bots()
        if name not in bots:
            raise ValueError(f"Bot not registered: {name}")
        cfg = bots[name]
        return BotConfig(
            name=name,
            bot_username=cfg["bot_username"],
            repo_path=Path(cfg["repo_path"]),
            capabilities_path=Path(cfg["capabilities_path"]),
            md_path=Path(cfg["md_path"]),
            repo_info_path=Path(cfg.get("repo_info_path", Path(cfg["repo_path"]) / "qa" / "context" / "repo_info.json")),
        )
