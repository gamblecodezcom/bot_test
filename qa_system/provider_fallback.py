from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROVIDER_ORDER = ["deepseek", "gemini", "chatgpt"]
RESET_MINUTES = 10
ALL_FAILED_WAIT_SECONDS = 60


@dataclass
class ProviderStatus:
    provider_order: list[str]
    cooldown_until: dict[str, str | None]
    last_reset_at: str
    last_success_provider: str | None
    last_failure_provider: str | None


class ProviderFallbackManager:
    def __init__(self, status_path: Path) -> None:
        self.status_path = status_path
        self.status_path.parent.mkdir(parents=True, exist_ok=True)

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _read_json(self, default: Any) -> Any:
        if not self.status_path.exists():
            return default
        return json.loads(self.status_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        self.status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> ProviderStatus:
        now = self._utc_now().isoformat()
        raw = self._read_json(
            {
                "provider_order": PROVIDER_ORDER,
                "cooldown_until": {p: None for p in PROVIDER_ORDER},
                "last_reset_at": now,
                "last_success_provider": None,
                "last_failure_provider": None,
            }
        )
        status = ProviderStatus(
            provider_order=list(raw.get("provider_order", PROVIDER_ORDER)),
            cooldown_until=dict(raw.get("cooldown_until", {p: None for p in PROVIDER_ORDER})),
            last_reset_at=str(raw.get("last_reset_at", now)),
            last_success_provider=raw.get("last_success_provider"),
            last_failure_provider=raw.get("last_failure_provider"),
        )
        self._periodic_reset(status)
        return status

    def _periodic_reset(self, status: ProviderStatus) -> None:
        last_reset = datetime.fromisoformat(status.last_reset_at)
        if self._utc_now() - last_reset >= timedelta(minutes=RESET_MINUTES):
            status.provider_order = PROVIDER_ORDER.copy()
            status.cooldown_until = {p: None for p in PROVIDER_ORDER}
            status.last_reset_at = self._utc_now().isoformat()
            self.persist(status)

    def persist(self, status: ProviderStatus) -> None:
        self._write(
            {
                "provider_order": status.provider_order,
                "cooldown_until": status.cooldown_until,
                "last_reset_at": status.last_reset_at,
                "last_success_provider": status.last_success_provider,
                "last_failure_provider": status.last_failure_provider,
            }
        )

    def pick_provider(self) -> str | None:
        status = self.load()
        now = self._utc_now()
        for provider in status.provider_order:
            cooldown = status.cooldown_until.get(provider)
            if not cooldown:
                return provider
            if datetime.fromisoformat(cooldown) <= now:
                status.cooldown_until[provider] = None
                self.persist(status)
                return provider
        return None

    def mark_success(self, provider: str) -> None:
        status = self.load()
        status.last_success_provider = provider
        status.last_failure_provider = None
        status.cooldown_until[provider] = None
        self.persist(status)

    def mark_failure(self, provider: str, rate_limited: bool = True) -> None:
        status = self.load()
        status.last_failure_provider = provider
        if rate_limited:
            status.cooldown_until[provider] = (self._utc_now() + timedelta(seconds=ALL_FAILED_WAIT_SECONDS)).isoformat()
        self.persist(status)

    def all_failed_wait(self) -> int:
        status = self.load()
        now = self._utc_now()
        waits = []
        for p in status.provider_order:
            cd = status.cooldown_until.get(p)
            if cd:
                waits.append(max(int((datetime.fromisoformat(cd) - now).total_seconds()), 0))
        return max(waits) if waits else 0
