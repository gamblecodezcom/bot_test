# bot_test

Telegram-first QA automation scaffold for RuneWager is available in `qa_system/`.

## Universal multi-bot files

- Bot registry: `qa/bots/bot_list.json`
- Selected bot state: `qa/state/selected_bot.json`
- Capabilities contract: `qa/context/bot_capabilities.json`
- Repo metadata: `qa/context/repo_info.json`
- Provider fallback state: `qa/state/provider_status.json`
- Action queue template: `/qa/actions/<bot_name>/queue.json`
- Log directory template: `/qa/logs/<bot_name>/YYYY-MM-DD/`

## Generate artifacts (capability-aware)

```bash
python -m qa_system.main --repo-root . --output qa_artifacts --dry-run --bot-name runewager
```

## Run executor service

```bash
python -m qa_system.executor --service --root /var/www/html/Runewager
```

## External AI sync + provider fallback

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --bot runewager --export qa_artifacts/brain_export.json
python -m qa_system.brain_sync --root /var/www/html/Runewager --pick-provider
python -m qa_system.brain_sync --root /var/www/html/Runewager --provider-result deepseek:success
```

Supported external AI options:
- Termux + Qwen 1.5B
- Termux + DeepSeek R1 1.5B
- DeepSeek Chat (free cloud)
- Gemini Free
- ChatGPT Free
