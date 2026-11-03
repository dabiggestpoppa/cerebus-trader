"""Immutable, versioned state snapshots (Ch III.4.1).

A snapshot is the *recorded* model state at an instant.  It is built from
a finalized III.3 ``ModelOutput`` and carries that output's identity
verbatim: model key, layer, active state, quality vocabulary,
production-authorization classification, evidence references and the
source output hash.  Measurement inputs are carried **by reference**
(definition id + version + source-window digest), never as recomputed
values: III.4 does not re-measure.

Invariant #1 (data clock is part of model identity) is enforced by
carrying the market-data / clock / session / measurement-engine versions
on every snapshot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Iterable

from app.forge.market_data import DataOutcome
from app.forge.measurements import Measurement
from app.forge.model_runtime import (
    Layer,
    ModelOutput,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    TypedLevel,
    WarningCode,
    compute_hash,
    resolve,
)

from .errors import (
    PriorStateMismatchError,
    SourceLineageMissingError,
    StateContractError,
)
from .versions import STATE_ENGINE_VERSION

__all__ = [
    "MeasurementRef",
    "StateSnapshot",
    "finalize_snapshot",
    "snapshot_payload",
]

_HASH = re.compile(r"^[0-9a-f]{64}$")
_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


@dataclass(frozen=True)
class MeasurementRef:
    """A reference to an upstream III.2 measurement — never its value."""

    definition_id: str
    definition_version: str
    source_window_digest: str
    bar_count: int
    quality_state: DataOutcome

    def __post_init__(self) -> None:
        if not self.definition_id or not self.definition_version:
            raise StateContractError(
                "a measurement reference requires a definition id and version"
            )
        if not self.source_window_digest:
            raise StateContractError("a measurement reference requires its window")
        if self.bar_count < 0:
            raise StateContractError("a measurement reference carries a bar count")
        if not isinstance(self.quality_state, DataOutcome):
            raise StateContractError(
                "measurement references use the frozen III.1 quality vocabulary"
            )

    @classmethod
    def from_measurement(cls, measurement: Measurement) -> "MeasurementRef":
        if not isinstance(measurement, Measurement):
            raise StateContractError("expected a III.2 Measurement")
        return cls(
            definition_id=measurement.definition_id,
            definition_version=measurement.definition_version,
            source_window_digest=measurement.source_window.input_digest,
            bar_count=measurement.source_window.bar_count,
            quality_state=measurement.quality_state,
        )


@dataclass(frozen=True)
class StateSnapshot:
    """The immutable recorded state (Ch III.4.1 frozen field set)."""

    snapshot_id: str
    model_id: str
    model_version: str
    model_runtime_version: str
    state_engine_version: str
    instrument_id: str
    layer: Layer
    event_time: datetime
    calculation_timestamp: datetime
    active_state: str
    measurements: tuple[MeasurementRef, ...]
    active_ranges: tuple[str, ...]
    levels: tuple[TypedLevel, ...]
    range_left: RangeLeftField
    quality_state: DataOutcome
    evidence_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]
    production_authorization: ProductionAuthorization
    no_go: tuple[NoGoReason, ...]
    warnings: tuple[WarningCode, ...]
    source_output_hash: str
    prior_snapshot_id: str | None
    clock_id: str | None
    session_id: str | None
    market_data_schema_version: str
    clock_registry_version: str
    session_registry_version: str
    measurement_engine_version: str
    snapshot_hash: str = ""

    def __post_init__(self) -> None:
        if not self.snapshot_id or not _IDENT.match(self.snapshot_id):
            raise StateContractError(f"snapshot_id must be a bounded id: {self.snapshot_id!r}")
        if not self.model_id or not self.model_version:
            raise StateContractError("a snapshot carries its model key")
        if self.model_runtime_version and not self.model_runtime_version:
            raise StateContractError("a snapshot carries its runtime version")
        if self.state_engine_version != STATE_ENGINE_VERSION:
            raise StateContractError(
                f"snapshots are stamped by {STATE_ENGINE_VERSION}, got "
                f"{self.state_engine_version!r}"
            )
        if not isinstance(self.layer, Layer):
            raise StateContractError("a snapshot carries the frozen III.3 layer")
        for name in ("event_time", "calculation_timestamp"):
            value = getattr(self, name)
            if not isinstance(value, datetime):
                raise StateContractError(f"{name} must be a datetime")
            if value.tzinfo is None:
                raise StateContractError(f"{name} must be timezone-aware (injected)")
        if not self.active_state:
            raise StateContractError("a snapshot carries its active state")
        if not self.source_output_hash or not _HASH.match(self.source_output_hash):
            raise SourceLineageMissingError(
                "a snapshot requires the finalized source output hash"
            )
        if self.snapshot_hash and not _HASH.match(self.snapshot_hash):
            raise StateContractError("snapshot_hash is a sha256 hex digest")
        if not isinstance(self.range_left, RangeLeftField):
            raise StateContractError("range_left uses the frozen III.3 field")
        if not isinstance(self.quality_state, DataOutcome):
            raise StateContractError(
                "quality_state uses the frozen III.1 vocabulary"
            )
        if not isinstance(
            self.production_authorization, ProductionAuthorization
        ):
            raise StateContractError(
                "production_authorization is a bounded III.3 classification"
            )
        if self.claim_refs:
            raise StateContractError(
                "the state engine never creates or references claims"
            )
        for reason in self.no_go:
            if not isinstance(reason, NoGoReason):
                raise StateContractError("no_go carries bounded codes only")
        for warning in self.warnings:
            if not isinstance(warning, WarningCode):
                raise StateContractError("warnings carry bounded codes only")
        for name in (
            "market_data_schema_version",
            "clock_registry_version",
            "session_registry_version",
            "measurement_engine_version",
        ):
            if not getattr(self, name):
                raise StateContractError(f"a snapshot asserts {name}")

    # -- construction ------------------------------------------------------

    @classmethod
    def from_output(
        cls,
        output: ModelOutput,
        *,
        event_time: datetime,
        snapshot_id: str,
        measurements: Iterable[Measurement] = (),
        prior_snapshot: "StateSnapshot | None" = None,
    ) -> "StateSnapshot":
        """Build a snapshot from a finalized III.3 model output.

        The output must be *finalized* (it carries its replay hash) and
        registered; both are lineage gates, not conveniences.
        """

        if not isinstance(output, ModelOutput):
            raise StateContractError("a snapshot is built from a ModelOutput")
        if not output.output_hash or not _HASH.match(output.output_hash):
            raise SourceLineageMissingError(
                "the source model output is not finalized (no output hash)"
            )
        # Exact registration: an unknown/absent model key fails closed.
        resolve(output.model_id, output.model_version)

        if prior_snapshot is not None:
            if not isinstance(prior_snapshot, StateSnapshot):
                raise StateContractError("prior_snapshot must be a StateSnapshot")
            if (
                prior_snapshot.model_id != output.model_id
                or prior_snapshot.model_version != output.model_version
            ):
                raise PriorStateMismatchError(
                    f"prior snapshot is {prior_snapshot.model_id}@"
                    f"{prior_snapshot.model_version}, output is "
                    f"{output.model_id}@{output.model_version}"
                )

        refs: list[MeasurementRef] = []
        seen: set[tuple[str, str, str]] = set()
        for measurement in measurements:
            ref = MeasurementRef.from_measurement(measurement)
            key = (ref.definition_id, ref.definition_version, ref.source_window_digest)
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)

        identity = output.identity
        snapshot = cls(
            snapshot_id=snapshot_id,
            model_id=output.model_id,
            model_version=output.model_version,
            model_runtime_version=output.model_runtime_version,
            state_engine_version=STATE_ENGINE_VERSION,
            instrument_id=identity.instrument_id,
            layer=output.layer,
            event_time=event_time,
            calculation_timestamp=identity.calculation_timestamp,
            active_state=output.model_state,
            measurements=tuple(refs),
            active_ranges=output.active_ranges,
            levels=output.levels,
            range_left=output.range_left,
            quality_state=output.quality_state,
            evidence_refs=output.evidence_refs,
            claim_refs=output.claim_refs,
            production_authorization=output.production_authorization,
            no_go=output.no_go,
            warnings=output.warnings,
            source_output_hash=output.output_hash,
            prior_snapshot_id=(
                prior_snapshot.snapshot_id if prior_snapshot is not None else None
            ),
            clock_id=identity.clock_id,
            session_id=identity.session_id,
            market_data_schema_version=identity.market_data_schema_version,
            clock_registry_version=identity.clock_registry_version,
            session_registry_version=identity.session_registry_version,
            measurement_engine_version=identity.measurement_engine_version,
        )
        return finalize_snapshot(snapshot)


def snapshot_payload(snapshot: StateSnapshot) -> dict:
    """The snapshot payload minus the self-referential hash field."""

    return {
        name: getattr(snapshot, name)
        for name in snapshot.__dataclass_fields__
        if name != "snapshot_hash"
    }


def finalize_snapshot(snapshot: StateSnapshot) -> StateSnapshot:
    """Stamp the deterministic snapshot hash (III.3 canonical serialization)."""

    digest = compute_hash(snapshot_payload(snapshot))
    if snapshot.snapshot_hash == digest:
        return snapshot
    return replace(snapshot, snapshot_hash=digest)
