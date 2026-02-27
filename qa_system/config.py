from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TELEGRAM_DEFAULT = True
DEFAULT_BOT_NAME = "runewager"
DEFAULT_ROOT = Path("/var/www/html/Runewager")


@dataclass(frozen=True)
class QAConfig:
    repo_root: Path
    output_dir: Path
    dry_run: bool = True

    @classmethod
    def from_args(cls, repo_root: str, output_dir: str, dry_run: bool = True) -> "QAConfig":
        resolved_root = Path(repo_root).resolve()
        if not resolved_root.exists() or not resolved_root.is_dir():
            raise ValueError(f"repo_root must be an existing directory: {resolved_root}")
        return cls(repo_root=resolved_root, output_dir=Path(output_dir).resolve(), dry_run=dry_run)
