"""Request/job correlation propagation (Book II / Bloc II.6, Ch II.6.1).

Ch II.6.1: every request/job has a correlation/request ID propagated through
API -> identity -> policy -> persistence -> provider call -> response.

This module owns the propagation context. The ID itself still comes from the
II.1 boundary (`app.forge.service.correlation`): inbound ids are parsed with
the frozen safe-bounded rule and generated ids are `fg-` prefixed. This
module never trusts caller input and never fabricates identity.

Missing context is deterministic and disclosed: `current_request_id()`
returns the frozen `UNATTRIBUTED` token and increments the unattributed
counter concept (the emitter records the fallback). Core execution never
depends on correlation context existing.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from app.forge.service.correlation import generate_request_id, parse_request_id

# Frozen token for "no correlation context" (test-deterministic).
UNATTRIBUTED = "unattributed"

_request_id_var: ContextVar[str | None] = ContextVar(
    "forge_request_id", default=None
)


def current_request_id() -> str | None:
    """The active request id, or None when no scope is active."""

    return _request_id_var.get()


def effective_request_id() -> str:
    """Active request id or the deterministic UNATTRIBUTED fallback."""

    return _request_id_var.get() or UNATTRIBUTED


@contextmanager
def correlation_scope(request_id: str | None) -> Iterator[str]:
    """Bind a safe request id for the duration of the scope.

    Inbound values are re-validated with the II.1 safe-bounded rule; an
    absent/invalid value yields a freshly generated id. Nested scopes restore
    the previous id on exit (deterministic propagation).
    """

    parsed = parse_request_id(request_id)
    bound = parsed if parsed is not None else generate_request_id()
    token = _request_id_var.set(bound)
    try:
        yield bound
    finally:
        _request_id_var.reset(token)


__all__ = [
    "UNATTRIBUTED",
    "correlation_scope",
    "current_request_id",
    "effective_request_id",
]
