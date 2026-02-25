# AI QA Agent Framework (Telegram + Discord)

This folder contains a deterministic, reproducible QA framework scaffold that covers:

1. Official bot-account architecture (Telegram Bot API + Discord bot integrations)
2. Test runner architecture
3. Scenario generator
4. Command matrix generation from the codebase
5. Button/callback matrix generation from the codebase
6. Onboarding flow map
7. Admin flow map
8. Error flow map
9. Logs + reports (JSON + Markdown)

## Quick start

```bash
python -m qa_system.main --repo-root . --output qa_artifacts --dry-run
```

## Output artifacts

- `command_matrix.csv`
- `button_callback_matrix.csv`
- `onboarding_flow_map.md`
- `admin_flow_map.md`
- `error_flow_map.md`
- `test_log.json`
- `failure_log.json`
- `summary_report.md`
- `improvements.md`

## Notes

- The framework intentionally uses deterministic IDs and ordered scenario generation.
- It does **not** require live Telegram/Discord credentials in `--dry-run` mode.
- Connector stubs are included for integrating official bot-account drivers.
- If user-account automation is explored, treat it as experimental only in isolated test accounts due to platform policy risk.
