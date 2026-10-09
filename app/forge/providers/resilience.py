"""Circuit and fallback policy (Book II / Bloc II.5, Ch II.5.8).

Ch II.5.8 laws:

- Fallback must be explicit per provider type.
- LLM fallback may select another model/provider.
- Commerce must not fabricate success when unavailable.
- Authorization never fails open because a provider is down.

`run_with_fallback` is structurally incapable of synthesizing a success: on
failure it either delegates to the caller's explicit failure handler (record
policy) or raises. There is no code path that returns a success-shaped object
built from a failure.

Time is injected (`clock: Callable[[], float]`) so every circuit transition is
deterministic under a simulated clock — no sleeping, no flakiness.
"""

from __future__ import annotations

from enum import Enum
from time import monotonic
from typing import Any, Callable, TypeVar

from app.forge.providers.errors import ProviderError, ProviderUnavailableError

T = TypeVar("T")

# Explicit per-port fallback modes (frozen).
FALLBACK_MODES: dict[str, str] = {
    "llm": "alternate",  # may select another model/provider
    "commerce": "none",  # never fabricate success when unavailable
    "notification": "record",  # outage recorded as failed, never delivered
    "storage": "none",  # artifacts: fail closed, no substitutes
}


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FallbackPolicy:
    """Explicit, per-port fallback decision. Constructed via `for_port`."""

    def __init__(self, port: str, mode: str) -> None:
        if port not in FALLBACK_MODES:
            raise ValueError(f"unknown provider port {port!r}")
        if mode not in {"alternate", "none", "record"}:
            raise ValueError(f"unknown fallback mode {mode!r}")
        self.port = port
        self.mode = mode

    @classmethod
    def for_port(cls, port: str) -> "FallbackPolicy":
        return cls(port, FALLBACK_MODES[port])

    def __repr__(self) -> str:
        return f"FallbackPolicy(port={self.port!r}, mode={self.mode!r})"


def run_with_fallback(
    policy: FallbackPolicy,
    primary: Callable[[], T],
    *,
    alternate: Callable[[], T] | None = None,
    on_failure: Callable[[ProviderError], Any] | None = None,
) -> T | Any:
    """Execute `primary` under an explicit fallback policy.

    - mode="alternate": a retryable ProviderError may be delegated to
      `alternate` (LLM model/provider switch). Alternate failures propagate.
    - mode="record": a failure is converted ONLY through the caller's explicit
      `on_failure` handler (e.g. NotificationResult(status="failed")); without
      a handler it raises. The handler is the sole failure-shape constructor.
    - mode="none": failures always raise (commerce/storage).

    No path returns a success-shaped object synthesized from a failure.
    """

    try:
        return primary()
    except ProviderError as exc:
        if policy.mode == "alternate" and alternate is not None and exc.retryable:
            return alternate()
        if policy.mode == "record" and on_failure is not None:
            return on_failure(exc)
        raise


class CircuitBreaker:
    """Consecutive-failure circuit for one provider call site.

    - CLOSED: calls pass through.
    - OPEN: retryable failures counted; at `failure_threshold` consecutive
      failures the circuit opens and short-circuits with
      `ProviderUnavailableError` WITHOUT invoking the call.
    - After `recovery_seconds` on the injected clock: HALF_OPEN — one probe is
      allowed; success closes the circuit, failure re-opens it.

    Only retryable failure classes (timeout/unavailable/rate_limited) count as
    circuit failures: caller errors (invalid_request, authentication_failed,
    malformed_response) are not availability signals.
    """

    def __init__(
        self,
        *,
        name: str,
        failure_threshold: int,
        recovery_seconds: float,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_seconds < 0:
            raise ValueError("recovery_seconds must be >= 0")
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        self._maybe_half_open()
        return self._state

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def _maybe_half_open(self) -> None:
        if (
            self._state is CircuitState.OPEN
            and self._opened_at is not None
            and self._clock() - self._opened_at >= self.recovery_seconds
        ):
            self._state = CircuitState.HALF_OPEN

    def call(self, fn: Callable[[], T]) -> T:
        state = self.state
        if state is CircuitState.OPEN:
            raise ProviderUnavailableError(
                f"circuit open: {self.name}",
                provider_type="circuit",
                provider_name=self.name,
            )
        try:
            result = fn()
        except ProviderError as exc:
            if exc.retryable:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = self._clock()
            # non-retryable classes leave the circuit state untouched
            raise
        else:
            self._consecutive_failures = 0
            self._state = CircuitState.CLOSED
            self._opened_at = None
            return result
