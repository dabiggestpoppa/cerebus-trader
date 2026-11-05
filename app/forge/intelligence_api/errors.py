"""Bounded intelligence-side errors. No prose, no payloads, one dialect."""

from __future__ import annotations

from typing import Any

from app.forge.intelligence_api.versions import REFUSAL_CODES, REFUSAL_TO_SERVICE_CODE


class IntelligenceError(Exception):
    """Base error for the intelligence API."""


class RefusalError(IntelligenceError):
    """A governed, bounded refusal. Carries a closed code and no payload."""

    def __init__(self, code: str, *, detail: str = "") -> None:
        if code not in REFUSAL_CODES:
            raise ValueError(f"unlisted refusal code: {code}")
        if detail and not _bounded(detail):
            raise ValueError("detail must be a bounded token, not prose")
        self.code = code
        self.detail = detail
        super().__init__(code)

    def to_payload(self) -> dict[str, str]:
        payload = {"code": self.code}
        if self.detail:
            payload["detail"] = self.detail
        return payload

    def service_code(self) -> str:
        return REFUSAL_TO_SERVICE_CODE[self.code]


class SchemaIncompatibleError(RefusalError):
    """The requested projection needs a machine-valid Book I card."""

    def __init__(self, *, detail: str = "") -> None:
        super().__init__("SCHEMA_INCOMPATIBLE", detail=detail)


def _bounded(value: str) -> bool:
    return 0 < len(value) <= 64 and all(
        ch.isalnum() or ch in "_.:/-" for ch in value
    )


def refusal_payload(code: str, *, detail: str = "") -> dict[str, str]:
    """Validate and build a refusal payload without raising a refusal."""

    return RefusalError(code, detail=detail).to_payload()


def error_detail(code: str, *, request_id: str | None = None) -> dict[str, Any]:
    """Map a bounded refusal onto the existing Book II error envelope."""

    payload: dict[str, Any] = {
        "code": REFUSAL_TO_SERVICE_CODE[code],
        "message": code,
    }
    if request_id:
        payload["request_id"] = request_id
    return payload


def is_refusal_code(code: str) -> bool:
    return code in REFUSAL_CODES


__all__ = [
    "IntelligenceError",
    "RefusalError",
    "SchemaIncompatibleError",
    "refusal_payload",
    "error_detail",
    "is_refusal_code",
]
