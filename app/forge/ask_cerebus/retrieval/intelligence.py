"""Typed Book III routing without inventing required fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.forge.ask_cerebus.interpreter.enums import TimeScope
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.requests import HistoricalRequest, SnapshotRequest
from app.forge.model_runtime.contract import Layer

from .enums import LimitationCode, RefusalCode
from .refs import IntelligenceRef, Limitation, Refusal


@dataclass(frozen=True)
class SnapshotContext:
    """Governed, already-authorized fields supplied by an upstream context."""

    instrument_id: str
    model_id: str
    model_version: str
    as_of: str
    data_cutoff: str
    calculation_version: str
    layer: Layer | None = None
    clock_id: str | None = None
    session_id: str | None = None
    provider_configured: bool = False
    quality: str = "UNKNOWN"


class SnapshotProviderPort(Protocol):
    def read(
        self, request: SnapshotRequest | HistoricalRequest, context: SnapshotContext
    ) -> IntelligenceRef: ...


class NotConfiguredSnapshotProvider:
    def read(self, request, context: SnapshotContext) -> IntelligenceRef:
        kind = (
            "HISTORICAL"
            if isinstance(request, HistoricalRequest)
            else "CURRENT"
        )
        return IntelligenceRef(
            request_kind=kind,
            snapshot_id="",
            snapshot_hash="",
            view="UNAVAILABLE",
            quality=context.quality,
            model_id=context.model_id,
            model_version=context.model_version,
            refusal="PROVIDER_NOT_CONFIGURED",
        )


@dataclass
class IntelligenceRoute:
    refs: tuple[IntelligenceRef, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    refusals: tuple[Refusal, ...] = ()
    request: SnapshotRequest | HistoricalRequest | None = None


def build_request(
    plan, context: SnapshotContext | None
) -> tuple[SnapshotRequest | HistoricalRequest | None, Limitation | None, Refusal | None]:
    if context is None:
        return (
            None,
            Limitation(LimitationCode.REQUIRED_FIELDS_UNRESOLVED, plan.plan_id),
            Refusal(RefusalCode.REQUIRED_FIELDS_UNRESOLVED, "SNAPSHOT_CONTEXT_MISSING"),
        )
    layer = context.layer or plan.layer
    if layer is None:
        return (
            None,
            Limitation(LimitationCode.REQUIRED_FIELDS_UNRESOLVED, plan.plan_id),
            Refusal(RefusalCode.REQUIRED_FIELDS_UNRESOLVED, "LAYER_MISSING"),
        )
    try:
        if plan.time_scope is TimeScope.CURRENT:
            request = SnapshotRequest(
                instrument_id=context.instrument_id,
                model_id=context.model_id,
                model_version=context.model_version,
                layer=layer,
                as_of=context.as_of,
                data_cutoff=context.data_cutoff,
                calculation_version=context.calculation_version,
                clock_id=context.clock_id,
                session_id=context.session_id,
            )
        else:
            request = HistoricalRequest(
                instrument_id=context.instrument_id,
                model_id=context.model_id,
                model_version=context.model_version,
                layer=layer,
                as_of=context.as_of,
                data_cutoff=context.data_cutoff,
                calculation_version=context.calculation_version,
                clock_id=context.clock_id,
                session_id=context.session_id,
                retention_acknowledged=True,
            )
    except RefusalError as exc:
        return (
            None,
            Limitation(LimitationCode.REQUIRED_FIELDS_UNRESOLVED, plan.plan_id, exc.code),
            Refusal(RefusalCode.REQUIRED_FIELDS_UNRESOLVED, exc.code),
        )
    return request, None, None


def route_intelligence(
    plan,
    context: SnapshotContext | None,
    provider: SnapshotProviderPort | None,
    *,
    correlation_id: str = "",
) -> IntelligenceRoute:
    out = IntelligenceRoute()
    request, limitation, refusal = build_request(plan, context)
    if request is None:
        out.limitations = (limitation,) if limitation else ()
        out.refusals = (refusal,) if refusal else ()
        return out
    out.request = request

    if context is None or not context.provider_configured:
        if isinstance(request, HistoricalRequest):
            out.refs = (
                IntelligenceRef(
                    request_kind="HISTORICAL",
                    snapshot_id="",
                    snapshot_hash="",
                    view="UNAVAILABLE",
                    quality=context.quality if context else "UNKNOWN",
                    model_id=context.model_id if context else "",
                    model_version=context.model_version if context else "",
                    refusal="HISTORICAL_UNAVAILABLE",
                ),
            )
            out.limitations = (
                Limitation(LimitationCode.HISTORICAL_UNAVAILABLE, plan.plan_id),
            )
            out.refusals = (
                Refusal(RefusalCode.HISTORICAL_UNAVAILABLE, "HISTORICAL_RETENTION_UNAVAILABLE"),
            )
            return out
        out.refs = (
            IntelligenceRef(
                request_kind="HISTORICAL" if isinstance(request, HistoricalRequest) else "CURRENT",
                snapshot_id="",
                snapshot_hash="",
                view="UNAVAILABLE",
                quality=context.quality if context else "UNKNOWN",
                model_id=context.model_id if context else "",
                model_version=context.model_version if context else "",
                refusal="PROVIDER_NOT_CONFIGURED",
            ),
        )
        out.limitations = (
            Limitation(LimitationCode.PROVIDER_NOT_CONFIGURED, plan.plan_id),
        )
        out.refusals = (
            Refusal(RefusalCode.PROVIDER_NOT_CONFIGURED, "MARKET_DATA_NOT_CONFIGURED"),
        )
        return out

    if provider is None:
        provider = NotConfiguredSnapshotProvider()
    ref = provider.read(request, context)
    out.refs = (ref,)
    if ref.refusal:
        out.limitations = (
            Limitation(LimitationCode.PROVIDER_NOT_CONFIGURED, plan.plan_id, ref.refusal),
        )
        out.refusals = (
            Refusal(RefusalCode.PROVIDER_NOT_CONFIGURED, ref.refusal),
        )
    return out


__all__ = [
    "SnapshotContext",
    "SnapshotProviderPort",
    "NotConfiguredSnapshotProvider",
    "IntelligenceRoute",
    "build_request",
    "route_intelligence",
]
