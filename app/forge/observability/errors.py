"""Error contract (Book II / Bloc II.6, Ch II.6.7 / II.6.8).

Frozen application error taxonomy (Ch II.6.7, exact names):

    AUTHENTICATION, AUTHORIZATION, VALIDATION, NOT_FOUND, CONFLICT,
    RATE_LIMIT, DEPENDENCY, DATA_INTEGRITY, INTERNAL

Laws:

- Provider failures map into this taxonomy WITHOUT losing their origin: a
  mapped error keeps `origin="provider"` plus the II.5 provider type/name/
  failure class, so provider and application failures stay distinguishable
  (frozen Acceptance II.6 clause 3).
- Safe responses (Ch II.6.8) expose exactly: stable code, safe message,
  request ID. No stack traces, SQL, secrets, hidden object existence or
  provider credential detail — messages come from the fixed safe table, never
  from exception text.
- The mapping is total over the frozen II.5 failure classes (PLAN §5),
  exact and test-enforced.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from app.forge.providers.errors import FAILURE_CLASSES, ProviderError

# Frozen Ch II.6.7 taxonomy — exact set and order.
class ForgeErrorClass(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT = "RATE_LIMIT"
    DEPENDENCY = "DEPENDENCY"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    INTERNAL = "INTERNAL"


ERROR_CLASSES: tuple[str, ...] = tuple(cls.value for cls in ForgeErrorClass)

# Frozen mapping: II.5 provider failure class -> II.6 application class
# (PLAN §5). Total over FAILURE_CLASSES; test-enforced exactness.
PROVIDER_FAILURE_TO_ERROR_CLASS: dict[str, ForgeErrorClass] = {
    "unavailable": ForgeErrorClass.DEPENDENCY,
    "timeout": ForgeErrorClass.DEPENDENCY,
    "rate_limited": ForgeErrorClass.RATE_LIMIT,
    "invalid_request": ForgeErrorClass.VALIDATION,
    "authentication_failed": ForgeErrorClass.AUTHENTICATION,
    "upstream_rejected": ForgeErrorClass.DEPENDENCY,
    "malformed_response": ForgeErrorClass.DATA_INTEGRITY,
    "unknown": ForgeErrorClass.DEPENDENCY,
}

# Fixed safe messages (Ch II.6.8): never derived from exception text.
SAFE_MESSAGES: dict[ForgeErrorClass, str] = {
    ForgeErrorClass.AUTHENTICATION: "authentication failed",
    ForgeErrorClass.AUTHORIZATION: "authorization denied",
    ForgeErrorClass.VALIDATION: "invalid request",
    ForgeErrorClass.NOT_FOUND: "resource not found",
    ForgeErrorClass.CONFLICT: "conflict",
    ForgeErrorClass.RATE_LIMIT: "rate limited",
    ForgeErrorClass.DEPENDENCY: "dependency unavailable",
    ForgeErrorClass.DATA_INTEGRITY: "data integrity failure",
    ForgeErrorClass.INTERNAL: "internal service error",
}

# Stable public error codes (Ch II.6.8 "stable code").
ERROR_CODES: dict[ForgeErrorClass, str] = {
    cls: f"FORGE_{cls.value}" for cls in ForgeErrorClass
}

# Deterministic HTTP status mapping for the FORGE envelope.
HTTP_STATUS: dict[ForgeErrorClass, int] = {
    ForgeErrorClass.AUTHENTICATION: 401,
    ForgeErrorClass.AUTHORIZATION: 403,
    ForgeErrorClass.VALIDATION: 422,
    ForgeErrorClass.NOT_FOUND: 404,
    ForgeErrorClass.CONFLICT: 409,
    ForgeErrorClass.RATE_LIMIT: 429,
    ForgeErrorClass.DEPENDENCY: 503,
    ForgeErrorClass.DATA_INTEGRITY: 500,
    ForgeErrorClass.INTERNAL: 500,
}

_MAX_REASON_CODE_LENGTH = 64


class ForgeApplicationError(Exception):
    """A classified, safe FORGE application error.

    `origin` distinguishes provider failures (`provider`) from application
    failures (`application`) — frozen Acceptance II.6 clause 3. Provider
    metadata is ids-only, never payloads or credentials.
    """

    def __init__(
        self,
        error_class: ForgeErrorClass,
        *,
        request_id: str = "",
        origin: str = "application",
        provider_type: str = "",
        provider_name: str = "",
        provider_failure_class: str = "",
        reason_code: str = "",
    ) -> None:
        if not isinstance(error_class, ForgeErrorClass):
            raise ValueError("error_class must be a ForgeErrorClass")
        if origin not in {"application", "provider"}:
            raise ValueError("origin must be 'application' or 'provider'")
        if provider_failure_class and (
            provider_failure_class not in FAILURE_CLASSES
        ):
            raise ValueError("invalid provider_failure_class")
        if len(reason_code) > _MAX_REASON_CODE_LENGTH:
            raise ValueError("reason_code too long")
        self.error_class = error_class
        self.request_id = request_id
        self.origin = origin
        self.provider_type = provider_type
        self.provider_name = provider_name
        self.provider_failure_class = provider_failure_class
        self.reason_code = reason_code
        super().__init__(SAFE_MESSAGES[error_class])

    @property
    def safe_message(self) -> str:
        return SAFE_MESSAGES[self.error_class]

    @property
    def code(self) -> str:
        return ERROR_CODES[self.error_class]

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.error_class]

    def safe_response(self) -> dict[str, Any]:
        """Ch II.6.8 production response: stable code, safe message, id."""

        return safe_error_response(self)


def safe_error_response(
    error: ForgeApplicationError, *, request_id: str | None = None
) -> dict[str, Any]:
    """The ONLY error body shape FORGE returns (Ch II.6.8)."""

    effective = request_id or error.request_id or ""
    return {
        "code": error.code,
        "message": error.safe_message,
        "request_id": effective or None,
    }


def from_provider_error(
    exc: ProviderError, *, request_id: str = ""
) -> ForgeApplicationError:
    """Map a normalized II.5 provider failure into the II.6 taxonomy.

    Origin and provider ids are retained; nothing else about the failure is
    carried (no payloads, no credentials, no exception text).
    """

    if not isinstance(exc, ProviderError):
        raise ValueError("from_provider_error expects a ProviderError")
    failure_class = exc.failure_class or "unknown"
    return ForgeApplicationError(
        PROVIDER_FAILURE_TO_ERROR_CLASS[failure_class],
        request_id=request_id,
        origin="provider",
        provider_type=exc.provider_type,
        provider_name=exc.provider_name,
        provider_failure_class=failure_class,
        reason_code=f"provider_{failure_class}",
    )


def from_exception(
    exc: BaseException, *, request_id: str = ""
) -> ForgeApplicationError:
    """Classify any exception safely.

    ProviderError maps through the frozen table; everything else is INTERNAL
    with origin=application. Exception text is never carried.
    """

    if isinstance(exc, ProviderError):
        return from_provider_error(exc, request_id=request_id)
    return ForgeApplicationError(
        ForgeErrorClass.INTERNAL, request_id=request_id, origin="application"
    )


__all__ = [
    "ERROR_CLASSES",
    "ERROR_CODES",
    "ForgeApplicationError",
    "ForgeErrorClass",
    "HTTP_STATUS",
    "PROVIDER_FAILURE_TO_ERROR_CLASS",
    "SAFE_MESSAGES",
    "from_exception",
    "from_provider_error",
    "safe_error_response",
]
