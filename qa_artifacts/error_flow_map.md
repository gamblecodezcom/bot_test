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
1. User-facing deterministic message.
2. Internal structured log entry.
3. Recovery hint or retry behavior.
