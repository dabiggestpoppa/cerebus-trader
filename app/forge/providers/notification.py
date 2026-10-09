"""Notification provider port (Book II / Bloc II.5, Ch II.5.4).

Transactional notification only:

- send transactional notification
- normalized delivery result

"Only if needed by launch" and "Do not prematurely build marketing automation":
the method set is exactly {send, health} — enforced by test — so no campaign,
funnel, or marketing surface can accrete onto this port.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.forge.providers.doctrine import ProviderHealth

# Frozen method set of the notification port (no marketing automation).
NOTIFICATION_METHODS: frozenset[str] = frozenset({"send", "health"})

CHANNELS: tuple[str, ...] = ("email",)
DELIVERY_STATUSES: tuple[str, ...] = ("delivered", "failed")


@dataclass(frozen=True)
class NotificationRequest:
    channel: str
    recipient: str
    subject: str
    body: str


@dataclass(frozen=True)
class NotificationResult:
    """Normalized delivery result. `failed` is a first-class outcome — an
    outage is recorded honestly, never reported as `delivered`."""

    message_id: str
    status: str
    failure_class: str | None = None


@runtime_checkable
class NotificationProvider(Protocol):
    """The frozen II.5 notification port."""

    def send(self, request: NotificationRequest) -> NotificationResult:
        """One transactional send attempt. Never retries internally."""
        ...

    def health(self) -> ProviderHealth:
        """Pure health answer; never a network call by itself."""
        ...
