"""Offline streaming buffer (WP-3B).

Events are applied one at a time.  The buffer keeps the latest observation per
canonical key, counts duplicates and revisions, preserves state across a
disconnect, and accepts a replayed window on reconnect.  It never decides
finality — canonicalization does that at the observation cutoff.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

from app.forge.market_data.errors import ConventionViolationError

from .contract import RawCandle


class StreamKind(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    UPDATE = "UPDATE"
    DISCONNECT = "DISCONNECT"
    RECONNECT = "RECONNECT"


class StreamDisconnectedError(ConventionViolationError):
    """A candle arrived while the session was disconnected."""

    code = "STREAM_DISCONNECTED"


@dataclass(frozen=True)
class StreamEvent:
    """One transport event: a candle, a disconnect or a reconnect."""

    kind: StreamKind
    candle: RawCandle | None = None

    def __post_init__(self) -> None:
        if self.kind in (StreamKind.SNAPSHOT, StreamKind.UPDATE):
            if self.candle is None:
                raise ConventionViolationError("candle event requires a candle")
        elif self.candle is not None:
            raise ConventionViolationError("control event cannot carry a candle")


class StreamBuffer:
    """Deterministic replay of an arrival sequence."""

    def __init__(self) -> None:
        self._latest: dict[tuple, RawCandle] = {}
        self.duplicates = 0
        self.revisions = 0
        self.stale_arrivals = 0
        self.connected = True

    def apply(self, event: StreamEvent) -> None:
        if event.kind is StreamKind.DISCONNECT:
            self.connected = False
            return
        if event.kind is StreamKind.RECONNECT:
            self.connected = True
            return
        if not self.connected:
            raise StreamDisconnectedError("candle received while disconnected")
        candle = event.candle
        assert candle is not None
        previous = self._latest.get(candle.key)
        if previous is None:
            self._latest[candle.key] = candle
            return
        if candle.source_timestamp > previous.source_timestamp:
            self._latest[candle.key] = candle
            self.revisions += 1
            return
        if candle.source_timestamp == previous.source_timestamp:
            if candle.digest() == previous.digest():
                self.duplicates += 1
            else:
                self._latest[candle.key] = max(
                    previous, candle, key=lambda item: item.digest()
                )
                self.revisions += 1
            return
        self.stale_arrivals += 1

    def extend(self, events: Iterable[StreamEvent]) -> None:
        for event in events:
            self.apply(event)

    def latest(self) -> tuple[RawCandle, ...]:
        return tuple(
            sorted(self._latest.values(), key=lambda item: item.open_time.timestamp())
        )

    def snapshot(self) -> tuple[RawCandle, ...]:
        """Alias used by tests: the current committed observation set."""
        return self.latest()

    @property
    def size(self) -> int:
        return len(self._latest)


def candle_events(candles: Sequence[RawCandle], *, kind: StreamKind = StreamKind.UPDATE) -> tuple[StreamEvent, ...]:
    return tuple(StreamEvent(kind=kind, candle=candle) for candle in candles)


def replay_events(events: Iterable[StreamEvent]) -> StreamBuffer:
    buffer = StreamBuffer()
    buffer.extend(events)
    return buffer


__all__ = [
    "StreamBuffer",
    "StreamDisconnectedError",
    "StreamEvent",
    "StreamKind",
    "candle_events",
    "replay_events",
]
