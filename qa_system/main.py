from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import QAConfig
from .flows import write_admin_flow_map, write_error_flow_map, write_onboarding_flow_map
from .matrix_generator import (
    build_button_matrix,
    build_command_matrix,
    discover_buttons,
    discover_commands,
    write_button_matrix,
    write_command_matrix,
)
from .reporter import write_improvements, write_logs, write_summary
from .scenarios import generate_scenarios


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AI QA artifacts for Telegram + Discord bot testing")
    parser.add_argument("--repo-root", default=".", help="Repository root to analyze")
    parser.add_argument("--output", default="qa_artifacts", help="Output directory for QA artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Generate artifacts without executing platform connectors")
    return parser.parse_args()


def run(config: QAConfig) -> dict:
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)

    commands = discover_commands(config.repo_root)
    buttons = discover_buttons(config.repo_root)

    command_rows = build_command_matrix(commands)
    button_rows = build_button_matrix(buttons)

    write_command_matrix(output / "command_matrix.csv", command_rows)
    write_button_matrix(output / "button_callback_matrix.csv", button_rows)

    write_onboarding_flow_map(output / "onboarding_flow_map.md")
    write_admin_flow_map(output / "admin_flow_map.md")
    write_error_flow_map(output / "error_flow_map.md")

    scenarios = generate_scenarios()
    write_logs(output, scenarios, dry_run=config.dry_run)
    write_summary(output, len(scenarios), len(commands), len(buttons))
    write_improvements(output)

    meta = {
        "repo_root": str(config.repo_root),
        "output": str(output),
        "dry_run": config.dry_run,
        "commands": len(commands),
        "buttons": len(buttons),
        "scenarios": len(scenarios),
    }
    (output / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    args = parse_args()
    config = QAConfig.from_args(repo_root=args.repo_root, output_dir=args.output, dry_run=args.dry_run)
    meta = run(config)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
