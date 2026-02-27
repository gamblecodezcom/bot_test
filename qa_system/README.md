# RuneWager QA System (Telegram-First, Multi-Bot Ready)

This package implements a lightweight VPS executor + external AI brain architecture with a universal multi-bot design.

## Key guarantees

- `TELEGRAM_DEFAULT = true` and Telegram is the only active target.
- Discord structures are preserved but inactive.
- No AI models run on the VPS executor.
- QA executor is independent from `runewager.service`.
- Capability contract is loaded from `/qa/context/bot_capabilities.json` for each test cycle.

## Multi-bot architecture

- Bot registry: `/qa/bots/bot_list.json`
- Bot selector command: `/qa/select_bot <bot_name>`
- Universal action queue: `/qa/actions/<bot_name>/queue.json`
- Universal logs: `/qa/logs/<bot_name>/YYYY-MM-DD/*.json`

## Provider fallback architecture

Provider state file: `/qa/state/provider_status.json`

Fallback order and behavior:
1. deepseek
2. gemini
3. chatgpt
4. if all unavailable: wait 60s and retry
5. every 10 minutes: cooldown reset + order restore

Use `qa_system.brain_sync` to update provider status after each success/failure.

## Components

1. **VPS EXECUTOR** (`qa_system.executor`)
   - Pyrogram userbot runner.
   - Reads selected bot from registry/state.
   - Handles `/qa_on`, `/qa_off`, `/qa_mode user|admin`, `/qa_status`, `/qa/select_bot <bot_name>`.
   - Captures deterministic debug metadata in responses (menu/callback/pending/error identifiers).

2. **EXTERNAL AI BRAIN SYNC** (`qa_system.brain_sync`)
   - Exports logs + state + provider status bundle.
   - Queues AI-decided actions back to per-bot queue.
   - Applies provider fallback updates.

3. **Artifact/Test planning generator** (`qa_system.main`)
   - Loads `bot_capabilities.json` and `repo_info.json`.
   - Produces test plan scaffolding and `final_report.json` categories.

## CLI

Generate deterministic QA artifacts with capabilities contract:

```bash
python -m qa_system.main --repo-root . --output qa_artifacts --dry-run --bot-name runewager
```

Run executor service:

```bash
python -m qa_system.executor --service --root /var/www/html/Runewager
```

Select a bot and inspect state:

```bash
python -m qa_system.executor --select-bot runewager --root /var/www/html/Runewager
python -m qa_system.executor --state --root /var/www/html/Runewager
```

Export latest logs for AI brain:

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --bot runewager --export qa_artifacts/brain_export.json
```

Pick fallback provider:

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --pick-provider
```

Apply provider result:

```bash
python -m qa_system.brain_sync --root /var/www/html/Runewager --provider-result deepseek:failure
```

## Systemd

Install `deploy/runewager-qa.service` as `runewager-qa.service` and set environment values in `/etc/runewager-qa.env`.
