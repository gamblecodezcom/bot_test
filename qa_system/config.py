from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QAConfig:
    repo_root: Path
    output_dir: Path
    dry_run: bool = True

    @classmethod
    def from_args(cls, repo_root: str, output_dir: str, dry_run: bool = True) -> "QAConfig":
        return cls(repo_root=Path(repo_root).resolve(), output_dir=Path(output_dir).resolve(), dry_run=dry_run)
