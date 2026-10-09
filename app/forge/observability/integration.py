"""Provider-call observation (Book II / Bloc II.6, integration Phase 4).

`observe_provider_call` times one provider invocation, emits the classified
provider event, counts metrics and **re-raises**. It is structurally unable
to convert a failure into a success: there is no return path that produces a
success-shaped result from a failure (mirroring the II.5 never-fabricate law
at the observability layer).

Masquerade law (PLAN §5 / ACCEPTANCE M1): a provider failure observed here
can never present as a successful commerce operation, a successful
authorization, a validated empirical claim, a successful canonical write, or
a healthy capability — the exception propagates untouched.
"""

from __future__ import annotations

from time import monotonic
from typing import Any, Callable, TypeVar

from app.forge.observability.errors import from_provider_error
from app.forge.providers.errors import ProviderError

T = TypeVar("T")


def observe_provider_call(
    emit: Callable[..., Any],
    increment: Callable[[str], None],
    observe: Callable[[str, float], None],
    *,
    port: str,
    provider_type: str,
    provider_name: str,
    model_id: str = "",
    operation: str = "",
    request_id: str | None = None,
    clock: Callable[[], float] = monotonic,
    call: Callable[[], T],
) -> T:
    """Run `call` under observation. Success and failure are both recorded;

    failure is always re-raised after recording (never swallowed, never
    reshaped).
    """

    started = clock()
    try:
        result = call()
    except ProviderError as exc:
        latency_ms = (clock() - started) * 1000.0
        summary = exc.redacted_summary()
        mapped = from_provider_error(exc, request_id=request_id or "")
        increment("provider_errors_total")
        if exc.failure_class == "rate_limited":
            increment("provider_rate_limited_total")
        observe("provider_latency_ms", latency_ms)
        emit(
            severity="WARNING",
            component="provider",
            operation=operation or f"{port}.call",
            outcome="failure",
            request_id=request_id,
            provider_type=provider_type,
            provider_name=provider_name,
            model_id=model_id,
            error_class=mapped.error_class.value,
            provider_failure_class=exc.failure_class or "unknown",
            reason_code=mapped.reason_code,
            duration_ms=latency_ms,
            attributes={
                "port": port,
                "retryable": bool(summary["retryable"]),
            },
        )
        raise
    else:
        latency_ms = (clock() - started) * 1000.0
        observe("provider_latency_ms", latency_ms)
        emit(
            severity="INFO",
            component="provider",
            operation=operation or f"{port}.call",
            outcome="success",
            request_id=request_id,
            provider_type=provider_type,
            provider_name=provider_name,
            model_id=model_id,
            duration_ms=latency_ms,
            attributes={"port": port},
        )
        return result


__all__ = ["observe_provider_call"]
