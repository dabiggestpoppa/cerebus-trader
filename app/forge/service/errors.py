"""FORGE HTTP error envelope.

FORGE-owned error responses use a stable, safe shape. They deliberately do
NOT include stack traces, secrets, internal paths, or raw provider payloads.

FORGE does not rewrite the existing Signal Guard error behavior; it only
defines the envelope for FORGE-owned endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class ForgeErrorDetail(BaseModel):
    """Safe, deterministic FORGE error body for FORGE-owned endpoints."""

    code: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


FORGE_ERROR_CODES = {
    "CLIENT_ERROR": "FORGE_CLIENT_ERROR",
    "NOT_FOUND": "FORGE_NOT_FOUND",
    "INTERNAL_ERROR": "FORGE_INTERNAL_ERROR",
    "DEPENDENCY_UNAVAILABLE": "FORGE_DEPENDENCY_UNAVAILABLE",
    "CONFIGURATION_ERROR": "FORGE_CONFIGURATION_ERROR",
}

_INTERNAL_MESSAGE = "internal service error"


def internal_error_payload(request_id: str | None = None) -> dict[str, Any]:
    """Safe 500 body for FORGE-owned endpoints. Never carries internals."""

    return ForgeErrorDetail(
        code=FORGE_ERROR_CODES["INTERNAL_ERROR"],
        message=_INTERNAL_MESSAGE,
        request_id=request_id,
    ).model_dump(mode="json")


def client_error(
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """FORGE client/input error (4xx)."""

    return HTTPException(
        status_code=422,
        detail=ForgeErrorDetail(
            code=FORGE_ERROR_CODES["CLIENT_ERROR"],
            message=message,
            request_id=request_id,
            details=details,
        ).model_dump(mode="json"),
    )


def not_found(
    message: str,
    request_id: str | None = None,
) -> HTTPException:
    """FORGE not-found error."""

    return HTTPException(
        status_code=404,
        detail=ForgeErrorDetail(
            code=FORGE_ERROR_CODES["NOT_FOUND"],
            message=message,
            request_id=request_id,
        ).model_dump(mode="json"),
    )


def internal_error(request_id: str | None = None) -> HTTPException:
    """FORGE internal error. Safe message only; never leak internals."""

    return HTTPException(
        status_code=500,
        detail=internal_error_payload(request_id=request_id),
    )


def dependency_unavailable(
    dependency: str,
    request_id: str | None = None,
) -> HTTPException:
    """FORGE dependency unavailable (e.g. readiness refusal)."""

    return HTTPException(
        status_code=503,
        detail=ForgeErrorDetail(
            code=FORGE_ERROR_CODES["DEPENDENCY_UNAVAILABLE"],
            message=f"dependency unavailable: {dependency}",
            request_id=request_id,
        ).model_dump(mode="json"),
    )
