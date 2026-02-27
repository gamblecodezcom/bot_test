# bot_test

Telegram-first QA automation scaffold for RuneWager is available in `qa_system/`.

## Generate artifacts

```bash
python -m qa_system.main --repo-root . --output qa_artifacts --dry-run --ai-provider termux_qwen
```

## Run executor service

```bash
python -m qa_system.executor --service --root /var/www/html/Runewager
```

## Sync logs for external AI brain

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --export qa_artifacts/brain_export.json
```

Supported external AI options:
- Termux + Qwen 1.5B
- Termux + DeepSeek R1 1.5B
- DeepSeek Chat (free cloud)
- Gemini Free
- ChatGPT Free
