from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from .executor import QAExecutor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RuneWager Telegram QA userbot runner")
    parser.add_argument("--login", action="store_true", help="Run one-time pyrogram login flow")
    parser.add_argument("--service", action="store_true", help="Run QA executor service loop")
    parser.add_argument("--root", default="/var/www/html/Runewager", help="RuneWager project root")
    parser.add_argument("--session-dir", default="data", help="Directory to store session file")
    return parser.parse_args()


async def login_flow(session_dir: Path) -> None:
    try:
        from pyrogram import Client
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Pyrogram is required. Install dependencies first.") from exc

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    phone = os.environ["TELEGRAM_PHONE"]

    session_dir.mkdir(parents=True, exist_ok=True)
    session_path = session_dir / "qa_userbot"

    async with Client(str(session_path), api_id=api_id, api_hash=api_hash, phone_number=phone) as app:
        me = await app.get_me()
        print(f"Login successful for @{me.username or me.id}")


def main() -> None:
    args = parse_args()
    if args.login:
        asyncio.run(login_flow(Path(args.session_dir)))
        return
    if args.service:
        asyncio.run(QAExecutor(Path(args.root)).run_service())
        return
    raise SystemExit("Choose one mode: --login or --service")


if __name__ == "__main__":
    main()
