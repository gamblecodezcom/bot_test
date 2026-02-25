from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram selfbot bootstrap/service runner")
    parser.add_argument("--login", action="store_true", help="Run one-time login flow")
    parser.add_argument("--service", action="store_true", help="Run long-lived service loop")
    parser.add_argument("--session-dir", default="data", help="Directory to store session file")
    return parser.parse_args()


async def login_flow(session_dir: Path) -> None:
    try:
        from telethon import TelegramClient
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Telethon is required. Install dependencies first.") from exc

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    phone = os.environ["TELEGRAM_PHONE"]
    password = os.environ.get("TELEGRAM_PASSWORD")

    session_dir.mkdir(parents=True, exist_ok=True)
    session_path = session_dir / "telegram_selfbot"
    client = TelegramClient(str(session_path), api_id, api_hash)

    otp = os.environ.get("TELEGRAM_OTP")

    async with client:
        if otp:
            await client.start(phone=phone, code_callback=lambda: otp, password=lambda: password)
        else:
            await client.start(phone=phone, password=lambda: password)

        me = await client.get_me()
        print(f"Login successful for @{me.username or me.id}")


async def service_loop() -> None:
    provider = os.getenv("AI_PROVIDER", "openai")
    model = os.getenv("AI_MODEL", "gpt-4.1-mini")
    print(f"Selfbot service running with AI provider={provider}, model={model}")
    while True:
        await asyncio.sleep(60)


def main() -> None:
    args = parse_args()
    session_dir = Path(args.session_dir)

    if args.login:
        asyncio.run(login_flow(session_dir))
        return

    if args.service:
        asyncio.run(service_loop())
        return

    raise SystemExit("Choose one mode: --login or --service")


if __name__ == "__main__":
    main()
