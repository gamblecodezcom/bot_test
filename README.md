# bot_test

Deterministic AI QA scaffolding for Telegram + Discord bot testing is available in `qa_system/`.

## Run artifact generator

```bash
python -m qa_system.main --repo-root . --output qa_artifacts --dry-run --ai-provider openai
```

Supported `--ai-provider` values: `openai`, `anthropic`, `groq`, `openrouter`.

## Guided selfbot setup (interactive)

A guided setup script is included to:

1. Ask for Telegram login details (phone, 2FA password, OTP),
2. Ask for AI provider and API key,
3. Install dependencies,
4. Run one-time Telegram login,
5. Install + enable a `systemd` service.

```bash
bash scripts/setup_selfbot.sh
```
