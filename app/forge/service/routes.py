"""FORGE router and FORGE-owned endpoints.

All FORGE routes live under `/forge/v1`.

FORGE imports domain from `app.forge.*`. Domain does NOT import FastAPI.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.forge.config import ForgeConfig
from app.forge.service.correlation import generate_request_id, parse_request_id
from app.forge.service.container import ForgeServiceContainer
from app.forge.service.errors import internal_error_payload
from app.forge.service.health import ForgeHealthService

logger = logging.getLogger("forge")


class ForgeLivenessResponse(BaseModel):
    service: str
    status: str
    request_id: str


class ForgeReadinessResponse(BaseModel):
    service: str
    status: str
    dependencies: dict[str, Any]
    request_id: str


class ForgeMetaResponse(BaseModel):
    service: str
    api_version: str
    application_version: str
    environment: str
    forge_domain_version: str
    request_id: str


def create_forge_router(
    *,
    config: ForgeConfig,
    container: ForgeServiceContainer,
) -> APIRouter:
    """Explicit FORGE router factory so composition is intentional, not implicit.

    Lifecycle is NOT registered here: sub-router `on_event` handlers never fire
    once the router is included into an application. The composition root wires
    `ForgeLifecycle` via `app.router.on_startup/on_shutdown` instead.
    """

    health = ForgeHealthService(container=container)
    router = APIRouter(prefix="/forge/v1", tags=["forge"])

    @router.get("/health", response_model=None)
    async def forge_health(
        request: Request,
        x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    ) -> ForgeLivenessResponse | JSONResponse:
        request_id = _effective_request_id(x_request_id)
        logger.info(
            "FORGE health check: request_id=%s env=%s",
            request_id,
            config.environment,
        )
        try:
            status = health.liveness()["status"]
        except Exception as exc:
            return _safe_internal_response(request_id, exc)
        return ForgeLivenessResponse(
            service=config.service_name,
            status=status,
            request_id=request_id,
        )

    @router.get("/ready", response_model=None)
    async def forge_ready(
        request: Request,
        x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    ) -> ForgeReadinessResponse | JSONResponse:
        request_id = _effective_request_id(x_request_id)
        try:
            readiness = health.readiness()
        except Exception as exc:
            return _safe_internal_response(request_id, exc)
        return ForgeReadinessResponse(
            service=config.service_name,
            status=readiness["status"],
            dependencies=readiness["dependencies"],
            request_id=request_id,
        )

    @router.get("/meta", response_model=None)
    async def forge_meta(
        request: Request,
        x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    ) -> ForgeMetaResponse | JSONResponse:
        request_id = _effective_request_id(x_request_id)
        try:
            meta = health.meta()
        except Exception as exc:
            return _safe_internal_response(request_id, exc)
        return ForgeMetaResponse(
            service=meta["service"],
            api_version=meta["api_version"],
            application_version=meta["application_version"],
            environment=meta["environment"],
            forge_domain_version=meta["forge_domain_version"],
            request_id=request_id,
        )

    return router


def _effective_request_id(inbound: str | None) -> str:
    parsed = parse_request_id(inbound)
    if parsed:
        return parsed
    return generate_request_id()


def _safe_internal_response(request_id: str, exc: Exception) -> JSONResponse:
    """Deterministic safe 500 envelope for FORGE-owned endpoints.

    Never includes the exception text, stack traces, internal paths or secrets
    in the response body. Logs only the exception class name.
    """

    logger.error("FORGE internal error: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=internal_error_payload(request_id=request_id),
    )
