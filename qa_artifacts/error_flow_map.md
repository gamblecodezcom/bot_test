# Error Flow Map

Test matrix for each command/button/callback in each context:

- 429 rate limit path
- Missing permissions
- Invalid command
- Wrong context (DM/group/channel/server)
- Missing onboarding
- Missing admin role
- Invalid callback payload
- Expired callback payload
- DB failure simulation
- Network failure simulation
- Timeout handling

Each error should assert:
1. Stable deterministic `error_code` (e.g., `response.error_code`).
2. User-facing deterministic message.
3. Internal structured log entry.
4. Recovery hint or retry behavior.

Shared assertion helpers (for example `assertErrorStructure`) should validate `error_code` first, then message/log/recovery fields.
