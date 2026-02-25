# Onboarding Flow Map (Telegram + Discord)

## New User
1. `/start` or first interaction.
2. Age confirmation.
3. Username/linking validation.
4. Discord link step (if originated on Telegram) / Telegram link step (if originated on Discord).
5. Channel + group/server membership checks.
6. WebApp/profile initialization.
7. Missing-step recovery checks.

## Returning User
1. Detect existing profile.
2. Skip completed onboarding steps.
3. Verify state integrity and repair corrupted progress.

## Invalid User Paths
- Missing username.
- Missing linked account.
- Expired/invalid deep link.
- Wrong context command execution.
- Incomplete required join actions.
