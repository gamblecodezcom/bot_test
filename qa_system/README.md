# RuneWager QA System (Telegram-First)

This package implements a lightweight VPS executor + external AI brain architecture.

## Key guarantees

- `TELEGRAM_DEFAULT = true` and Telegram is the only active target.
- Discord is preserved as inactive placeholders for future expansion.
- No AI models run on the VPS executor.
- QA executor is independent from `runewager.service`.

## Components

1. **VPS EXECUTOR** (`qa_system.executor`)
   - Pyrogram userbot runner.
   - JSON queue protocol for actions.
   - Handles `/qa_on`, `/qa_off`, `/qa_mode admin`, `/qa_mode user`.
   - Writes structured logs under:
     - `/var/www/html/Runewager/qa/logs/YYYY-MM-DD/action_log.json`
     - `/var/www/html/Runewager/qa/logs/YYYY-MM-DD/message_log.json`
     - `/var/www/html/Runewager/qa/logs/YYYY-MM-DD/error_log.json`

2. **EXTERNAL AI BRAIN** (`qa_system.brain_sync` protocol)
   - Runs on Android 15 + Termux or free cloud AI.
   - Pulls logs and state from the VPS.
   - Sends back JSON action list.

3. **Artifact generator** (`qa_system.main`)
   - Generates command/button matrices and `final_report.json` scaffold.

## CLI

Generate deterministic QA artifacts:

```bash
python -m qa_system.main --repo-root . --output qa_artifacts --dry-run --ai-provider termux_qwen
```

Run executor service:

```bash
python -m qa_system.executor --service --root /var/www/html/Runewager
```

Queue an action:

```bash
python -m qa_system.executor --queue-action send_command --payload '{"text":"/qa_on"}'
```

Export latest logs for AI brain:

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --export qa_artifacts/brain_export.json
```

Queue AI brain generated actions:

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --queue ai_actions.json
```

## Systemd

Install `deploy/runewager-qa.service` as `runewager-qa.service` and set environment values in `/etc/runewager-qa.env`.
