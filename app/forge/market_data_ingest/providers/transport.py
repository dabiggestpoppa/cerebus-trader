"""Deterministic scripted transport.

WP-3B is forbidden from opening sockets, so every adapter consumes a scripted
sequence of provider-shaped pages and events.  Failures can be injected per
call to exercise the II.5 taxonomy without a network.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from app.forge.providers.errors import ProviderUnavailableError

RawPage = Mapping[str, object]


class ScriptedTransport:
    """Pages and events plus per-call failure injection."""

    def __init__(
        self,
        pages: Sequence[RawPage] = (),
        events: Sequence[RawPage] = (),
        failures: Sequence[Exception | None] = (),
        *,
        provider_name: str = "scripted",
    ) -> None:
        self._pages = tuple(pages)
        self._events = tuple(events)
        self._failures = tuple(failures)
        self._provider_name = provider_name
        self._page_index = 0
        self._event_index = 0
        self.calls = 0
        self.closed = False

    def _maybe_fail(self) -> None:
        self.calls += 1
        if self.calls <= len(self._failures):
            failure = self._failures[self.calls - 1]
            if failure is not None:
                raise failure

    def next_page(self) -> RawPage | None:
        if self.closed:
            raise ProviderUnavailableError(
                "transport is closed",
                provider_type="market_data",
                provider_name=self._provider_name,
            )
        self._maybe_fail()
        if self._page_index >= len(self._pages):
            return None
        page = self._pages[self._page_index]
        self._page_index += 1
        return page

    def next_event(self) -> RawPage | None:
        if self.closed:
            raise ProviderUnavailableError(
                "transport is closed",
                provider_type="market_data",
                provider_name=self._provider_name,
            )
        self._maybe_fail()
        if self._event_index >= len(self._events):
            return None
        event = self._events[self._event_index]
        self._event_index += 1
        return event

    def close(self) -> None:
        self.closed = True


__all__ = ["ScriptedTransport"]
