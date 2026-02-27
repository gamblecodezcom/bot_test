from __future__ import annotations

import argparse
import json
from pathlib import Path

from .capabilities import load_capabilities, load_repo_info
from .config import QAConfig, TELEGRAM_DEFAULT
from .flows import write_admin_flow_map, write_error_flow_map, write_onboarding_flow_map
from .matrix_generator import build_button_matrix, build_command_matrix, discover_buttons, discover_commands, write_button_matrix, write_command_matrix
from .providers import resolve_provider
from .reporter import write_improvements, write_logs, write_summary
from .scenarios import generate_scenarios
from .test_engine import build_test_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Telegram-first QA artifacts for RuneWager")
    parser.add_argument("--repo-root", default=".", help="Repository root to analyze")
    parser.add_argument("--output", default="qa_artifacts", help="Output directory for QA artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Generate artifacts without executing platform connectors")
    parser.add_argument("--bot-name", default="runewager", help="Bot name for metadata")
    parser.add_argument("--capabilities", default=None, help="Path to bot_capabilities.json")
    parser.add_argument("--repo-info", default=None, help="Path to repo_info.json")
    parser.add_argument("--ai-provider", default="termux_qwen", help="AI provider: termux_qwen|termux_deepseek_r1|deepseek_chat|gemini_free|chatgpt_free")
    parser.add_argument("--ai-model", default=None, help="Optional model override")
    return parser.parse_args()


def _as_repo_relative(path: Path, repo_root: Path) -> str:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
        return "." if str(rel) == "." else rel.as_posix()
    except ValueError:
        return path.as_posix()


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    tmp.replace(path)


def run(config: QAConfig, bot_name: str = "runewager", capabilities_path: Path | None = None, repo_info_path: Path | None = None, ai_provider: str = "termux_qwen", ai_model: str | None = None) -> dict:
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)

    capabilities = load_capabilities(capabilities_path or (config.repo_root / "qa" / "context" / "bot_capabilities.json"))
    repo_info = load_repo_info(repo_info_path or (config.repo_root / "qa" / "context" / "repo_info.json"))
    test_plan = build_test_plan(capabilities)

    commands = sorted(set(discover_commands(config.repo_root) + capabilities.get("commands", {}).get("user", []) + capabilities.get("commands", {}).get("admin", [])))
    buttons = sorted(set(discover_buttons(config.repo_root) + capabilities.get("callbacks", [])))

    write_command_matrix(output / "command_matrix.csv", build_command_matrix(commands))
    write_button_matrix(output / "button_callback_matrix.csv", build_button_matrix(buttons))

    write_onboarding_flow_map(output / "onboarding_flow_map.md")
    write_admin_flow_map(output / "admin_flow_map.md")
    write_error_flow_map(output / "error_flow_map.md")

    scenarios = generate_scenarios()
    write_logs(output, scenarios, dry_run=config.dry_run)
    write_summary(output, len([s for s in scenarios if s.active]), len(commands), len(buttons), test_plan=test_plan)
    write_improvements(output)

    provider_cfg = resolve_provider(ai_provider, ai_model)
    _atomic_write_json(output / "ai_reasoning_config.json", {"provider": provider_cfg.provider, "model": provider_cfg.model, "api_key_env": provider_cfg.api_key_env, "execution_location": provider_cfg.execution_location, "runs_on_vps": False})

    meta = {
        "bot_name": bot_name,
        "repo_root": _as_repo_relative(config.repo_root, config.repo_root),
        "output": _as_repo_relative(output, config.repo_root),
        "dry_run": config.dry_run,
        "commands": len(commands),
        "buttons": len(buttons),
        "scenarios": len(scenarios),
        "ai_provider": provider_cfg.provider,
        "ai_model": provider_cfg.model,
        "telegram_default": TELEGRAM_DEFAULT,
        "discord_active": False,
        "capabilities_loaded": sorted(capabilities.keys()),
        "repo_info": repo_info,
    }
    _atomic_write_json(output / "run_meta.json", meta)
    return meta


def main() -> None:
    args = parse_args()
    config = QAConfig.from_args(repo_root=args.repo_root, output_dir=args.output, dry_run=args.dry_run)
    meta = run(
        config,
        bot_name=args.bot_name,
        capabilities_path=Path(args.capabilities) if args.capabilities else None,
        repo_info_path=Path(args.repo_info) if args.repo_info else None,
        ai_provider=args.ai_provider,
        ai_model=args.ai_model,
    )
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
