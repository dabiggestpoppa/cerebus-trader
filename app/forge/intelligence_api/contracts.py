"""Immutable III.6 contracts: identity, sections, envelope, views."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable, Mapping

from app.forge.canonical import EvidenceStatus, ProductExposure, SetupClass
from app.forge.intelligence_api.serialization import content_hash
from app.forge.intelligence_api.versions import (
    SNAPSHOT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    VIEW_CURRENT,
)
from app.forge.market_data.quality import DataOutcome, QualityFlag
from app.forge.model_runtime.contract import Layer, LevelKind

SNAPSHOT_KEY_FIELDS = (
    "instrument_id",
    "model_id",
    "model_version",
    "layer",
    "as_of",
    "data_cutoff",
    "calculation_version",
    "clock_id",
    "session_id",
)

MAX_IDENTIFIER = 128


def _ident(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > MAX_IDENTIFIER:
        raise ValueError(f"{name} is too long")
    if any(ch.isspace() for ch in value):
        raise ValueError(f"{name} must not contain whitespace")
    return value


def _timestamp(value: Any, name: str) -> str:
    text = _ident(value, name)
    if "T" not in text:
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"{name} is not an ISO-8601 timestamp") from exc
    return text


def _dec_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise ValueError("price values must be Decimal-backed")
    if not value.is_finite():
        raise ValueError("price values must be finite")
    return format(value, "f")


@dataclass(frozen=True)
class SnapshotKey:
    """Logical snapshot identity. Principal identity is deliberately absent."""

    instrument_id: str
    model_id: str
    model_version: str
    layer: Layer
    as_of: str
    data_cutoff: str
    calculation_version: str
    clock_id: str | None = None
    session_id: str | None = None

    def __post_init__(self) -> None:
        _ident(self.instrument_id, "instrument_id")
        _ident(self.model_id, "model_id")
        _ident(self.model_version, "model_version")
        if not isinstance(self.layer, Layer):
            raise ValueError("layer must be a Layer")
        _timestamp(self.as_of, "as_of")
        _timestamp(self.data_cutoff, "data_cutoff")
        _ident(self.calculation_version, "calculation_version")
        if self.clock_id is not None:
            _ident(self.clock_id, "clock_id")
        if self.session_id is not None:
            _ident(self.session_id, "session_id")

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return SNAPSHOT_KEY_FIELDS

    def payload(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "layer": self.layer.value,
            "as_of": self.as_of,
            "data_cutoff": self.data_cutoff,
            "calculation_version": self.calculation_version,
            "clock_id": self.clock_id,
            "session_id": self.session_id,
        }


@dataclass(frozen=True)
class TimeFacts:
    as_of: str
    data_cutoff: str
    calculation_timestamp: str
    source_cutoffs: tuple[str, ...] = ()


@dataclass(frozen=True)
class LineageFacts:
    prior_snapshot_id: str | None = None
    transition_refs: tuple[str, ...] = ()
    genesis_snapshot_id: str | None = None
    history_hash: str | None = None
    replay_of_snapshot_id: str | None = None


@dataclass(frozen=True)
class QualityFacts:
    outcome: DataOutcome
    flags: tuple[QualityFlag, ...] = ()
    source_window_digest: str | None = None
    stale_label: str | None = None
    provider_status: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, DataOutcome):
            raise ValueError("quality outcome must be a DataOutcome")
        for flag in self.flags:
            if not isinstance(flag, QualityFlag):
                raise ValueError("quality flags must be QualityFlag members")


@dataclass(frozen=True)
class CurrentStatePayload:
    state: str
    layer: Layer
    direction: dict[str, Any] | None
    active_ranges: tuple[str, ...]
    active_anchor_states: tuple[dict[str, Any], ...]
    clock: dict[str, Any]
    quality: dict[str, Any]
    no_go: tuple[str, ...]
    stand_down: dict[str, Any] | None
    warnings: tuple[str, ...]
    production_authorization: str


@dataclass(frozen=True)
class LevelView:
    level_id: str
    level_kind: str
    family: str
    level: str | None
    price: str | None
    active: bool
    source_ref: str
    source_model_id: str
    source_model_version: str
    layer: Layer

    def __post_init__(self) -> None:
        if not self.source_ref or any(ch.isspace() for ch in self.source_ref):
            raise ValueError("a level view requires a bounded source reference")
        if not self.source_model_id or not self.source_model_version:
            raise ValueError("a level view requires its source model identity")

    @classmethod
    def from_level(
        cls,
        level: Any,
        *,
        model_id: str,
        model_version: str,
        layer: Layer,
    ) -> "LevelView":
        kind = getattr(level.level_kind, "value", str(level.level_kind))
        return cls(
            level_id=level.level_id,
            level_kind=kind,
            family=level.family,
            level=_dec_text(level.level),
            price=_dec_text(level.price),
            active=bool(level.active),
            source_ref=level.source_ref,
            source_model_id=model_id,
            source_model_version=model_version,
            layer=layer,
        )


@dataclass(frozen=True)
class PathPayload:
    clock_id: str
    targets: tuple[dict[str, Any], ...]
    deliveries: tuple[dict[str, Any], ...]
    first_delivery: dict[str, Any] | None
    terminal_reach: str
    ambiguous: bool
    unresolved_ordering: bool
    range_left: dict[str, Any] | None
    transition_summary: tuple[dict[str, Any], ...]
    layer: Layer


@dataclass(frozen=True)
class EvidenceLink:
    claim_id: str | None
    evidence_id: str
    status: EvidenceStatus
    relationship: bool = False
    population_key: str | None = None
    view_label: str = "CURRENT"
    exposure: ProductExposure | None = None

    def __post_init__(self) -> None:
        if self.claim_id is None and self.evidence_id == "":
            raise ValueError("evidence link needs an id")
        if not isinstance(self.status, EvidenceStatus):
            raise ValueError("evidence status must be an EvidenceStatus")


@dataclass(frozen=True)
class SetupContextPayload:
    setup_id: str
    setup_version: str | None
    surface: str
    eligibility: str
    reasons: tuple[str, ...]
    gates: tuple[dict[str, Any], ...]
    record: dict[str, Any] | None
    card: dict[str, Any] | None
    card_schema_status: str
    no_go_refs: tuple[str, ...]
    evidence: tuple[EvidenceLink, ...]
    automation_permitted: bool
    execution_class: str | None
    exposure: str | None

    def __post_init__(self) -> None:
        if self.automation_permitted:
            raise ValueError("automation_permitted is registry-wide false")
        if self.eligibility not in ("ELIGIBLE", "WATCH", "BLOCKED", "UNRESOLVED"):
            raise ValueError("unknown eligibility value")


@dataclass(frozen=True)
class Classifications:
    execution_class: str | None
    exposure: str | None
    research_only: bool
    manual_only: bool
    automation_permitted: bool = False


@dataclass(frozen=True)
class Provenance:
    engine_versions: tuple[tuple[str, str], ...] = ()
    registry_versions: tuple[tuple[str, str], ...] = ()
    component_hashes: tuple[tuple[str, str], ...] = ()
    fixture_identity: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_versions": dict(self.engine_versions),
            "registry_versions": dict(self.registry_versions),
            "component_hashes": dict(self.component_hashes),
            "fixture_identity": self.fixture_identity,
        }


@dataclass(frozen=True)
class UnavailableSection:
    section: str
    reason: str

    def __post_init__(self) -> None:
        if self.section not in ("state", "levels", "path", "setup", "evidence"):
            raise ValueError("unknown section")
        if not self.reason or any(ch.isspace() for ch in self.reason):
            raise ValueError("reason must be a bounded code")

    def payload(self) -> dict[str, str]:
        return {"status": "UNAVAILABLE", "reason": self.reason}


def _without_projection_labels(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_projection_labels(item)
            for key, item in value.items()
            if key != "view_label"
        }
    if isinstance(value, list):
        return [_without_projection_labels(item) for item in value]
    return value


SCHEMA_DESCRIPTOR: dict[str, Any] = {
    "schema_version": SNAPSHOT_SCHEMA_VERSION,
    "envelope": (
        "schema_version",
        "snapshot_id",
        "snapshot_hash",
        "view",
        "identity",
        "time",
        "lineage",
        "quality",
        "sections",
        "classifications",
        "provenance",
        "explanation_facts",
        "warnings",
        "unresolved",
        "refusals",
    ),
    "key": SNAPSHOT_KEY_FIELDS,
    "sections": ("state", "levels", "path", "setup", "evidence"),
    "views": ("CURRENT", "HISTORICAL", "UNAVAILABLE"),
}


@dataclass(frozen=True)
class Snapshot:
    key: SnapshotKey
    time: TimeFacts
    quality: QualityFacts
    classifications: Classifications
    provenance: Provenance
    state: CurrentStatePayload | None = None
    levels: tuple[LevelView, ...] | None = None
    path: PathPayload | None = None
    setup: SetupContextPayload | None = None
    evidence: tuple[EvidenceLink, ...] | None = None
    lineage: LineageFacts = field(default_factory=LineageFacts)
    explanation_facts: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()
    unresolved: tuple[UnavailableSection, ...] = ()
    refusals: tuple[dict[str, str], ...] = ()
    view: str = VIEW_CURRENT
    schema_version: str = SNAPSHOT_SCHEMA_VERSION
    snapshot_id: str = ""
    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError("unknown schema version")
        if self.view not in ("CURRENT", "HISTORICAL", "UNAVAILABLE"):
            raise ValueError("unknown view")
        for section in self.unresolved:
            if section.section not in ("state", "levels", "path", "setup", "evidence"):
                raise ValueError("unknown section")
        for entry in self.refusals:
            if not isinstance(entry, dict) or "code" not in entry:
                raise ValueError("refusals must carry a code")

    # -- section access ------------------------------------------------
    def section_map(self) -> dict[str, Any]:
        unavailable = {entry.section: entry for entry in self.unresolved}
        out: dict[str, Any] = {}
        for name in ("state", "levels", "path", "setup", "evidence"):
            value = getattr(self, name)
            if value is None:
                entry = unavailable.get(name)
                out[name] = (
                    entry.payload()
                    if entry is not None
                    else {"status": "UNAVAILABLE", "reason": "UNRESOLVED_SECTION"}
                )
            else:
                out[name] = value
        return out

    def payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "view": self.view,
            "identity": self.key.payload(),
            "time": {
                "as_of": self.time.as_of,
                "data_cutoff": self.time.data_cutoff,
                "calculation_timestamp": self.time.calculation_timestamp,
                "source_cutoffs": self.time.source_cutoffs,
            },
            "lineage": self.lineage,
            "quality": self.quality,
            "sections": self.section_map(),
            "classifications": self.classifications,
            "provenance": self.provenance.as_dict(),
            "explanation_facts": self.explanation_facts,
            "warnings": self.warnings,
            "unresolved": self.unresolved,
            "refusals": self.refusals,
        }
        if include_hash:
            payload["snapshot_hash"] = self.snapshot_hash
        return payload

    def _hash_payload(self) -> dict[str, Any]:
        from app.forge.intelligence_api.serialization import to_primitive

        payload = to_primitive(self.payload(include_hash=False))
        # Projection labels are not market content: a historical replay of the
        # same pinned inputs must reproduce the same hash.
        payload.pop("view", None)
        return _without_projection_labels(payload)

    def compute_hash(self) -> str:
        return content_hash(self._hash_payload())

    def finalized(self) -> "Snapshot":
        return replace(self, snapshot_hash=self.compute_hash())

    def as_current(self) -> "Snapshot":
        return replace(self, view=VIEW_CURRENT)


@dataclass(frozen=True)
class LayerSection:
    layer: Layer
    snapshot_id: str
    snapshot_hash: str
    model_id: str
    model_version: str
    state: str
    direction: dict[str, Any] | None
    active_ranges: tuple[str, ...]
    no_go: tuple[str, ...]
    quality: str


@dataclass(frozen=True)
class InstrumentView:
    instrument_id: str
    sections: tuple[LayerSection, ...]
    conflicts: tuple[dict[str, Any], ...]
    unresolved: tuple[UnavailableSection, ...]
    classifications: Classifications
    schema_version: str
    view_id: str = ""
    view_hash: str = ""

    def payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "view_id": self.view_id,
            "instrument_id": self.instrument_id,
            "sections": self.sections,
            "conflicts": self.conflicts,
            "unresolved": self.unresolved,
            "classifications": self.classifications,
        }
        if include_hash:
            out["view_hash"] = self.view_hash
        return out

    def compute_hash(self) -> str:
        return content_hash(self.payload(include_hash=False))

    def finalized(self) -> "InstrumentView":
        return replace(self, view_hash=self.compute_hash())


@dataclass(frozen=True)
class BasketPair:
    pair: str
    role: str
    snapshot_id: str
    snapshot_hash: str
    state: str
    direction: dict[str, Any] | None
    no_go: tuple[str, ...]
    exposure: str | None
    confirmation_only: bool = False


@dataclass(frozen=True)
class BasketView:
    basket_id: str
    pairs: tuple[BasketPair, ...]
    unresolved: tuple[UnavailableSection, ...]
    classifications: Classifications
    schema_version: str
    view_id: str = ""
    view_hash: str = ""

    def payload(self, *, include_hash: bool = True) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "view_id": self.view_id,
            "basket_id": self.basket_id,
            "pairs": self.pairs,
            "unresolved": self.unresolved,
            "classifications": self.classifications,
        }
        if include_hash:
            out["view_hash"] = self.view_hash
        return out

    def compute_hash(self) -> str:
        return content_hash(self.payload(include_hash=False))

    def finalized(self) -> "BasketView":
        return replace(self, view_hash=self.compute_hash())


def ids_text(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in values)


__all__ = [
    "SNAPSHOT_KEY_FIELDS",
    "SCHEMA_DESCRIPTOR",
    "MAX_IDENTIFIER",
    "SnapshotKey",
    "TimeFacts",
    "LineageFacts",
    "QualityFacts",
    "CurrentStatePayload",
    "LevelView",
    "PathPayload",
    "EvidenceLink",
    "SetupContextPayload",
    "Classifications",
    "Provenance",
    "UnavailableSection",
    "Snapshot",
    "LayerSection",
    "InstrumentView",
    "BasketPair",
    "BasketView",
    "ids_text",
]
