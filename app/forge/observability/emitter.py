"""Event emitter and sinks (Book II / Bloc II.6, Ch II.6.2 / II.6.10).

The emitter is the single funnel: it assigns seq, stamps the timestamp from
an injected clock, applies correlation fallback, validates via `ForgeEvent`
construction (which redacts) and fans out to sinks.

Laws:

- Deterministic: injected clock + monotonic gapless seq ⇒ identical scripts
  produce identical event streams.
- Sink failure never breaks the caller: a raising sink drops that delivery
  and increments `dropped_events` (core execution never depends on
  telemetry — directive item 25 / ACCEPTANCE K3).
- Malformed events are refused deterministically at construction;
  `safe_emit` converts that refusal into a bounded counter, never a crash.
- No sink ever sees an unredacted value: redaction happened in ForgeEvent's
  constructor, before any sink is touched (ACCEPTANCE J4).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol

from app.forge.observability.correlation import UNATTRIBUTED, current_request_id
from app.forge.observability.events import ForgeEvent

logger = logging.getLogger("forge.observability")

# Bounded diagnostics counters.
MAX_RECORDED_EVENTS = 512


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventSink(Protocol):
    """A destination for fully-built, already-redacted events."""

    def deliver(self, event: ForgeEvent) -> None: ...


class InMemoryEventSink:
    """Bounded deterministic sink for tests and in-process inspection."""

    def __init__(self, capacity: int = MAX_RECORDED_EVENTS) -> None:
        if capacity < 1:
            raise ValueError("sink capacity must be >= 1")
        self._capacity = capacity
        self._events: list[ForgeEvent] = []

    def deliver(self, event: ForgeEvent) -> None:
        self._events.append(event)
        if len(self._events) > self._capacity:
            del self._events[: len(self._events) - self._capacity]

    def events(self) -> tuple[ForgeEvent, ...]:
        return tuple(self._events)

    def clear(self) -> None:
        self._events.clear()


class StructuredLogSink:
    """Stdlib logging sink: one sorted-key JSON line per event.

    This is the 'standard log' surface the frozen acceptance clause N2
    (secrets/protected corpus absent from standard logs) is proven against.
    """

    def __init__(self, log: logging.Logger | None = None) -> None:
        self._log = log or logger

    def deliver(self, event: ForgeEvent) -> None:
        level = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }[event.severity]
        # Redaction already applied at construction; this line carries only
        # bounded, scrubbed fields.
        self._log.log(
            level,
            json.dumps(event.to_dict(), sort_keys=True, default=str),
        )


class ForgeEventEmitter:
    """Deterministic event emitter with sink isolation."""

    def __init__(
        self,
        *,
        environment: str,
        sinks: tuple[EventSink, ...] = (),
        clock: Callable[[], str] = utc_now_iso,
    ) -> None:
        self._environment = environment
        self._sinks = tuple(sinks)
        self._clock = clock
        self._seq = 0
        self._dropped_events = 0
        self._rejected_events = 0

    @property
    def seq(self) -> int:
        """Last assigned sequence number (events recorded so far)."""

        return self._seq

    @property
    def dropped_events(self) -> int:
        """Deliveries lost to a failing sink (never a caller crash)."""

        return self._dropped_events

    @property
    def rejected_events(self) -> int:
        """Malformed events refused by safe_emit (bounded counter)."""

        return self._rejected_events

    def emit(
        self,
        *,
        severity: str = "INFO",
        stream: str = "telemetry",
        component: str = "",
        operation: str = "",
        outcome: str = "success",
        request_id: str | None = None,
        job_id: str = "",
        actor_class: str = "",
        actor_id: str = "",
        object_type: str = "",
        object_id: str = "",
        capability: str = "",
        reason_code: str = "",
        duration_ms: float | None = None,
        provider_type: str = "",
        provider_name: str = "",
        model_id: str = "",
        error_class: str = "",
        provider_failure_class: str = "",
        attributes: Mapping[str, Any] | None = None,
    ) -> ForgeEvent:
        """Build, redact, order and deliver one event.

        Correlation fallback: explicit request_id > active scope > the
        frozen UNATTRIBUTED token (never a fabricated id).
        """

        active = current_request_id()
        effective_request_id = request_id or active or UNATTRIBUTED
        self._seq += 1
        event = ForgeEvent(
            seq=self._seq,
            timestamp=self._clock(),
            environment=self._environment,
            stream=stream,
            severity=severity,
            request_id=effective_request_id,
            job_id=job_id,
            actor_class=actor_class,
            actor_id=actor_id,
            component=component,
            operation=operation,
            object_type=object_type,
            object_id=object_id,
            capability=capability,
            outcome=outcome,
            reason_code=reason_code,
            duration_ms=duration_ms,
            provider_type=provider_type,
            provider_name=provider_name,
            model_id=model_id,
            error_class=error_class,
            provider_failure_class=provider_failure_class,
            attributes=attributes or {},
        )
        for sink in self._sinks:
            try:
                sink.deliver(event)
            except Exception:  # NOSONAR: telemetry must never break the caller
                self._dropped_events += 1
        return event

    def safe_emit(self, **kwargs: Any) -> ForgeEvent | None:
        """Emit, converting a malformed event into a bounded counter."""

        try:
            return self.emit(**kwargs)
        except Exception:  # NOSONAR: deterministic refusal, counted not raised
            self._rejected_events += 1
            return None


__all__ = [
    "EventSink",
    "ForgeEventEmitter",
    "InMemoryEventSink",
    "MAX_RECORDED_EVENTS",
    "StructuredLogSink",
    "utc_now_iso",
]
