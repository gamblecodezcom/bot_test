# Onboarding Flow Map (Telegram-First)

## New User
1. `/start` or first interaction.
2. Age confirmation.
3. Username/profile validation.
4. Required channel/group membership checks.
5. Profile initialization.
6. Missing-step recovery checks.

## Returning User
1. Detect existing profile.
2. Skip completed onboarding steps.
3. Verify state integrity and repair corrupted progress.

## Invalid User Paths
- Missing username.
- Expired/invalid deep link.
- Wrong context command execution.
- Incomplete required join actions.

> Discord flows are preserved but inactive while `TELEGRAM_DEFAULT = true`.
