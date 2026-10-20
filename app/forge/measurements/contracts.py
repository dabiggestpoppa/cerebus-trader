"""Measurement contracts for Bloc III.2 (Ch III.2.9 + final-record fields).

Everything this package emits is a *measurement*: a deterministic
transformation of observations with an explicit formula, units, input
frame and clock/session definition.  A measurement is not a model
output, not a claim, not evidence and not a setup.

This module owns:

* :class:`DefinitionSpec` — the registered definition table
  (definition id, version, formula text, unit, input frame, evidence
  references).  An unregistered id or a drifted version refuses.
* :class:`SourceWindow` — the UTC source window plus the input-bar
  content digest the measurement was computed from.
* :class:`Measurement` — the frozen provenance envelope every emitted
  measurement carries (definition id/version, instrument, source window,
  clock/session ids and registry versions, injected calculation
  timestamp, quality state, native unit, schema/engine versions and
  evidence references).
* :class:`NativeMagnitude` — an asset-native *count* of native units
  (pips, points, dollars).  It is deliberately distinct from III.1's
  ``NativePrice``: a price is a price, a magnitude is a distance.  No
  cross-unit arithmetic exists, so an EUR pip count can never be added
  to a BTC dollar count.
* deterministic serialization (:func:`encode_value`) so every
  distinction (touch vs acceptance, ordered path vs terminal outcome)
  survives a round trip unchanged.

Nothing here reads a wall clock, opens a socket or writes to the
corpus.  The calculation timestamp is always injected by the caller.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from app.forge.market_data import (
    CLOCK_REGISTRY_VERSION,
    MARKET_DATA_SCHEMA_VERSION,
    SESSION_REGISTRY_VERSION,
    DataOutcome,
    NativePrice,
    NativeUnit,
)
from app.forge.market_data.bars import Bar, content_digest

from .errors import (
    MeasurementContractError,
    UnitDomainError,
    UnknownDefinitionError,
)
from .versions import MEASUREMENT_ENGINE_VERSION

__all__ = [
    "DEFINITION_REGISTRY",
    "DefinitionSpec",
    "Measurement",
    "MeasurementContext",
    "NativeMagnitude",
    "Provenance",
    "RATIO_QUANTUM",
    "SourceWindow",
    "add_magnitude",
    "definition",
    "encode_value",
    "native_count",
    "native_span",
    "quantize_ratio",
    "require_definition",
    "scale_magnitude",
    "source_window_from_bars",
    "source_window_from_instants",
    "subtract_magnitude",
]


#: Ratios are quantized to this many decimal places (half-even) so that
#: a repeating division is reproducible byte-for-byte across platforms.
RATIO_QUANTUM = Decimal("0.0000000001")

#: Working precision for exact native-unit division (power-of-ten steps).
_NATIVE_PRECISION = 60


# ----------------------------------------------------------------------
# Native magnitudes (asset-native atomic distances)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class NativeMagnitude:
    """An asset-native distance expressed as a count of native units.

    ``value`` counts native units of ``unit`` for ``instrument_id``:
    pips for FX, points for XAU, dollars for BTC.  It is *not* a price
    and never mixes with one.
    """

    instrument_id: str
    unit: NativeUnit
    value: Decimal

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise MeasurementContractError("magnitude requires an instrument id")
        if not isinstance(self.value, Decimal):
            raise MeasurementContractError("magnitude value must be Decimal")
        if self.value < 0:
            raise MeasurementContractError("magnitude value must not be negative")

    def to_dict(self) -> dict:
        return {
            "instrument_id": self.instrument_id,
            "unit": self.unit.value,
            "value": str(self.value),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "NativeMagnitude":
        return cls(
            instrument_id=data["instrument_id"],
            unit=NativeUnit(data["unit"]),
            value=Decimal(data["value"]),
        )


def _require_same_domain(
    first: NativeMagnitude, second: NativeMagnitude
) -> None:
    if first.instrument_id != second.instrument_id or first.unit is not second.unit:
        raise UnitDomainError(
            f"refusing {first.unit.value}/{first.instrument_id} with "
            f"{second.unit.value}/{second.instrument_id}"
        )


def add_magnitude(
    first: NativeMagnitude, second: NativeMagnitude
) -> NativeMagnitude:
    """Add two magnitudes of the same asset-native domain."""
    _require_same_domain(first, second)
    return NativeMagnitude(first.instrument_id, first.unit, first.value + second.value)


def subtract_magnitude(
    first: NativeMagnitude, second: NativeMagnitude
) -> NativeMagnitude:
    """Subtract two magnitudes of the same asset-native domain."""
    _require_same_domain(first, second)
    result = first.value - second.value
    if result < 0:
        raise UnitDomainError("magnitude subtraction produced a negative distance")
    return NativeMagnitude(first.instrument_id, first.unit, result)


def scale_magnitude(magnitude: NativeMagnitude, factor: Decimal) -> NativeMagnitude:
    """Scale a magnitude by a positive exact factor."""
    if not isinstance(factor, Decimal):
        raise MeasurementContractError("scale factor must be Decimal")
    if factor < 0:
        raise MeasurementContractError("scale factor must not be negative")
    return NativeMagnitude(magnitude.instrument_id, magnitude.unit, magnitude.value * factor)


def native_count(
    instrument_id: str,
    unit: NativeUnit,
    native_step: Decimal,
    distance: Decimal,
) -> NativeMagnitude:
    """Express a price distance as a count of asset-native units.

    ``native_step`` is the instrument's own native step (III.1
    ``Instrument.native_step``); no global pip/point constant exists.
    The result counts native units — it is never a price.
    """
    if distance < 0:
        raise MeasurementContractError("native distance must not be negative")
    if native_step <= 0:
        raise MeasurementContractError("native step must be positive")
    with localcontext() as ctx:
        ctx.prec = _NATIVE_PRECISION
        count = distance / native_step
    return NativeMagnitude(instrument_id, unit, count)


def native_span(
    instrument_id: str,
    unit: NativeUnit,
    native_step: Decimal,
    low: Decimal,
    high: Decimal,
) -> NativeMagnitude:
    """Express a price span as a count of asset-native units.

    ``native_step`` is the instrument's own native step (III.1
    ``Instrument.native_step``); no global pip/point constant exists.
    """
    if high < low:
        raise MeasurementContractError("span high must not be below low")
    return native_count(instrument_id, unit, native_step, high - low)


def quantize_ratio(value: Decimal) -> Decimal:
    """Quantize a ratio deterministically (half-even, 10 decimal places)."""
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def source_window_from_bars(bars: Sequence[Bar]) -> SourceWindow:
    """Derive the source window of a bar sequence.

    The digest is III.1's provider-quarantined content digest, so the
    window binds the *content* of the bars and not the feed that
    delivered them.
    """
    if not bars:
        raise MeasurementContractError("source window requires at least one bar")
    ordered = sorted(bars, key=lambda bar: bar.open_time)
    return SourceWindow(
        window_open_utc=ordered[0].open_time,
        window_close_utc=ordered[-1].close_time,
        input_digest=content_digest(ordered),
        bar_count=len(ordered),
    )


def source_window_from_instants(instants: Sequence[datetime]) -> SourceWindow:
    """Derive the source window of a purely temporal computation.

    A time measurement consumes no bars; its window therefore binds the
    *instants* it was computed over.  The digest is a deterministic
    hash of the sorted UTC instants, so the window still identifies its
    inputs exactly and a temporal measurement is never mistaken for a
    bar-derived one.
    """
    if not instants:
        raise MeasurementContractError("source window requires at least one instant")
    ordered = sorted(
        (instant.astimezone(timezone.utc) for instant in instants),
        key=lambda value: value,
    )
    payload = json.dumps(
        [_iso(instant) for instant in ordered], separators=(",", ":")
    )
    import hashlib

    return SourceWindow(
        window_open_utc=ordered[0],
        window_close_utc=ordered[-1],
        input_digest=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        bar_count=0,
    )


# ----------------------------------------------------------------------
# Definition registry
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class DefinitionSpec:
    """One registered measurement definition.

    ``formula`` states exactly what was computed; ``unit`` states the
    unit of the emitted value; ``input_frame`` states the population the
    value was computed over.  ``evidence_refs`` cites canonical evidence
    ids when the definition carries a calibrated constant; a definition
    with a statistical parameter and no reference is not registrable.
    """

    definition_id: str
    definition_version: str
    formula: str
    unit: str
    input_frame: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.definition_id or not self.definition_version:
            raise MeasurementContractError("definition id and version are required")
        if not self.formula or not self.unit or not self.input_frame:
            raise MeasurementContractError(
                "definition requires formula, unit and input frame"
            )
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    def to_dict(self) -> dict:
        return {
            "definition_id": self.definition_id,
            "definition_version": self.definition_version,
            "formula": self.formula,
            "unit": self.unit,
            "input_frame": self.input_frame,
            "evidence_refs": list(self.evidence_refs),
        }


def _spec(
    definition_id: str,
    formula: str,
    unit: str,
    input_frame: str,
    evidence_refs: Iterable[str] = (),
) -> DefinitionSpec:
    return DefinitionSpec(
        definition_id=definition_id,
        definition_version="V1",
        formula=formula,
        unit=unit,
        input_frame=input_frame,
        evidence_refs=tuple(evidence_refs),
    )


DEFINITION_REGISTRY: Mapping[str, DefinitionSpec] = {
    spec.definition_id: spec
    for spec in (
        # -- Ch III.2.1 range engine -----------------------------------
        _spec(
            "RANGE_MEASUREMENT",
            "bundled range measurement: high, low, size, midpoint, direction, "
            "close location, consumed fraction, range-left, breakout/return state",
            "MIXED_NATIVE",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_HIGH",
            "max(high) over the finalized bars of the measured range window",
            "NATIVE_PRICE",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_LOW",
            "min(low) over the finalized bars of the measured range window",
            "NATIVE_PRICE",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_SIZE",
            "(high - low) expressed in the instrument's own native step",
            "NATIVE_MAGNITUDE",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_MIDPOINT",
            "(high + low) / 2 in asset-native price units",
            "NATIVE_PRICE",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_DIRECTION",
            "sign(last_close - first_open) of the measured range window",
            "ENUM",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_CLOSE_LOCATION",
            "(last_close - low) / (high - low), quantized to 10 decimal places",
            "RATIO",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_CONSUMED_FRACTION",
            "clamp(last_close - first_open, 0, size) / size, quantized to 10 dp",
            "RATIO",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_LEFT",
            "size - consumed distance; the unconsumed remainder of the measured range",
            "NATIVE_MAGNITUDE",
            "finalized bars inside the measured range window",
        ),
        _spec(
            "RANGE_BREAKOUT_RETURN_STATE",
            "position of the last post-establishment close relative to the established range",
            "ENUM",
            "finalized bars after the establishing window",
        ),
        # -- Ch III.2.2 calibration -------------------------------------
        _spec(
            "TIER_CLASSIFICATION",
            "band membership of a native magnitude inside one calibration table",
            "ENUM",
            "one asset-native magnitude measured from finalized bars",
        ),
        _spec(
            "AU_SCALE",
            "asset-native atomic distance published by one calibration table",
            "NATIVE_MAGNITUDE",
            "one asset-native magnitude measured from finalized bars",
        ),
        _spec(
            "SPATIAL_BAND_CLASSIFICATION",
            "narrowest matching declared band of one spatial-band table",
            "ENUM",
            "one asset-native magnitude measured from finalized bars",
        ),
        _spec(
            "THRESHOLD_LEVELS",
            "published threshold constants of one calibration, in asset-native units",
            "NATIVE_MAGNITUDE",
            "one asset-native magnitude measured from finalized bars",
        ),
        _spec(
            "DENSITY_ZONES",
            "published overlap zones of one calibration, in asset-native units",
            "NATIVE_MAGNITUDE",
            "one asset-native magnitude measured from finalized bars",
        ),
        # -- Ch III.2.3 coordinates -------------------------------------
        _spec(
            "COORDINATE_PROJECTION",
            "anchor_point + orientation * size * level / 100 in asset-native price units",
            "NATIVE_PRICE",
            "one earned anchor range plus the declared coordinate family",
        ),
        # -- Ch III.2.4 anchors -----------------------------------------
        _spec(
            "ANCHOR_ELIGIBILITY",
            "declared anchor status with its earned-range reference and rule identity",
            "ENUM",
            "one declared anchor record",
        ),
        _spec(
            "ANCHOR_REKEY",
            "remapping transition from a prior anchor to a successor anchor, "
            "with the mapping that produced it",
            "ENUM",
            "one declared anchor rekey transition",
        ),
        # -- Ch III.2.5 state age ---------------------------------------
        _spec(
            "ELAPSED_SINCE_EVENT",
            "observed_instant - event_instant",
            "DURATION",
            "one injected instant pair",
        ),
        _spec(
            "CHECKPOINT_REACHED",
            "observed_instant >= scheduled checkpoint instant",
            "ENUM",
            "one injected instant pair against a canonical scheduled instant",
        ),
        _spec(
            "ACCEPTANCE_DURATION",
            "end_instant - acceptance_start_instant",
            "DURATION",
            "one injected instant pair",
        ),
        _spec(
            "FAILURE_AGE",
            "observed_instant - failure_instant",
            "DURATION",
            "one injected instant pair",
        ),
        _spec(
            "TIME_TO_DELIVERY",
            "scheduled_boundary_instant - observed_instant; a schedule distance only",
            "DURATION",
            "one injected instant pair against a canonical scheduled boundary",
        ),
        _spec(
            "SESSION_PHASE",
            "membership of the observed instant in a canonical session window",
            "ENUM",
            "one injected instant against the III.1 session registry",
        ),
        _spec(
            "PERIOD_PHASE",
            "calendar period containing the III.1-resolved research day",
            "ENUM",
            "one injected instant against the III.1 research-day lineage",
        ),
        # -- Ch III.2.6 path --------------------------------------------
        _spec(
            "PATH_MEASUREMENT",
            "bundled path measurement: reference price, MAE, MFE, per-level typed "
            "outcomes, first delivery, delivery order and remaining distribution state",
            "MIXED_NATIVE",
            "one finalized bar path",
        ),
        _spec(
            "PATH_MAE",
            "largest adverse excursion of the path from its reference price",
            "NATIVE_MAGNITUDE",
            "one finalized bar path",
        ),
        _spec(
            "PATH_MFE",
            "largest favourable excursion of the path from its reference price",
            "NATIVE_MAGNITUDE",
            "one finalized bar path",
        ),
        _spec(
            "PATH_FIRST_DELIVERY",
            "earliest realized level with its bar index",
            "ENUM",
            "one finalized bar path",
        ),
        _spec(
            "PATH_TARGET_SEQUENCE",
            "ordered sequence of realized levels with their bar indices",
            "ENUM",
            "one finalized bar path",
        ),
        _spec(
            "PATH_TOUCH_STATE",
            "whether the path touched the declared level",
            "ENUM",
            "one finalized bar path",
        ),
        _spec(
            "PATH_ACCEPTANCE_STATE",
            "whether the path accepted the declared level",
            "ENUM",
            "one finalized bar path",
        ),
        _spec(
            "PATH_CLOSE_BEYOND_STATE",
            "whether the path closed beyond the declared level",
            "ENUM",
            "one finalized bar path",
        ),
        _spec(
            "PATH_RE_ENTRY_STATE",
            "whether the path returned inside after closing beyond",
            "ENUM",
            "one finalized bar path",
        ),
        _spec(
            "PATH_REMAINING_DISTRIBUTION",
            "unconsumed remainder of the measured range, or an explicit unresolved state",
            "NATIVE_MAGNITUDE",
            "one finalized bar path bound to one measured range",
        ),
        _spec(
            "PATH_LEVEL_OUTCOME",
            "typed touch/acceptance/close-beyond/re-entry facts for one declared level",
            "ENUM",
            "one finalized bar path and one declared level",
        ),
        _spec(
            "PATH_REJECTION_STATE",
            "whether the path touched the declared level and later closed back on the origin side",
            "ENUM",
            "one finalized bar path and one declared level",
        ),
        _spec(
            "PATH_REMAINING_STATE",
            "whether the remaining distribution is measured or explicitly unresolved",
            "ENUM",
            "one finalized bar path bound to one measured range",
        ),
        # -- Ch III.2.7 events ------------------------------------------
        _spec(
            "EVENT_RELEVANCE",
            "declared currency/asset relevance of one normalized event",
            "ENUM",
            "one normalized event record",
        ),
        _spec(
            "EVENT_FAMILY",
            "declared family of one normalized event record",
            "ENUM",
            "one normalized event record",
        ),
        _spec(
            "EVENT_BUDGET",
            "total event size minus consumed movement, clamped at zero",
            "NATIVE_MAGNITUDE",
            "one normalized event record",
        ),
        # -- Ch III.2.8 higher order ------------------------------------
        _spec(
            "HO_SEED_RANGE",
            "high/low/size of one month, quarter or week seed window",
            "NATIVE_MAGNITUDE",
            "one finalized bar seed window",
        ),
        _spec(
            "HO_D1D3_STATE",
            "declared state of the D1/D2/D3 quarter-day seeds",
            "ENUM",
            "one quarter seed window",
            ("EV.EUR.HO.D3_DIRECTION.V1",),
        ),
        _spec(
            "HO_M1_SCALE",
            "month-1 seed range magnitude used as the higher-order scale feature",
            "NATIVE_MAGNITUDE",
            "one finalized month-1 seed window",
            ("EV.EUR.HO.M1_RANGE_CORR.V1",),
        ),
        _spec(
            "HO_M2_SHAPING",
            "declared month-2 shaping state of the higher-order hierarchy",
            "ENUM",
            "one finalized month-2 seed window",
        ),
        _spec(
            "HO_UNFINISHED_SIDE",
            "declared unfinished side of the higher-order hierarchy",
            "ENUM",
            "one quarter seed window",
            ("EV.EUR.HO.UNFINISHED_M3.V1",),
        ),
        _spec(
            "HO_WEEKLY_SEED",
            "high/low/size of one weekly seed window",
            "NATIVE_MAGNITUDE",
            "one finalized weekly seed window",
        ),
        _spec(
            "HO_WEEKLY_PATH",
            "ordered structural nodes measured inside the weekly seed window",
            "ENUM",
            "one finalized weekly seed window",
        ),
        _spec(
            "HO_CHECKPOINT",
            "whether the observed instant reached a declared higher-order checkpoint",
            "ENUM",
            "one injected instant against a declared checkpoint instant",
        ),
        _spec(
            "HO_LAYER_CONFLICT",
            "declared conflicts between layer facts; no score is emitted",
            "ENUM",
            "one set of layer facts",
        ),
    )
}


def definition(definition_id: str) -> DefinitionSpec:
    """Return a registered definition; an unknown id refuses."""
    try:
        return DEFINITION_REGISTRY[definition_id]
    except KeyError:
        raise UnknownDefinitionError(
            f"unknown measurement definition {definition_id!r}"
        ) from None


def require_definition(definition_id: str, definition_version: str) -> DefinitionSpec:
    """Return a registered definition at the exact version.

    Version drift refuses: a changed formula requires a newly registered
    definition version (core law — downstream may consume, never
    silently redefine).
    """
    spec = definition(definition_id)
    if spec.definition_version != definition_version:
        raise UnknownDefinitionError(
            f"definition {definition_id!r} is at {spec.definition_version!r}, "
            f"not {definition_version!r}"
        )
    return spec


# ----------------------------------------------------------------------
# Source window and provenance envelope
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class SourceWindow:
    """The data window a measurement was computed over.

    ``input_digest`` is III.1's provider-quarantined bar content digest:
    two feeds of the same slice digest identically, so the digest binds
    the *content* and not the feed.
    """

    window_open_utc: datetime
    window_close_utc: datetime
    input_digest: str
    bar_count: int

    def __post_init__(self) -> None:
        for name in ("window_open_utc", "window_close_utc"):
            value = getattr(self, name)
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise MeasurementContractError(
                    f"{name} must be a tz-aware datetime"
                )
            object.__setattr__(
                self, name, value.astimezone(timezone.utc)
            )
        if self.window_close_utc < self.window_open_utc:
            raise MeasurementContractError("source window close precedes open")
        if not self.input_digest:
            raise MeasurementContractError("source window requires an input digest")
        if self.bar_count < 0:
            raise MeasurementContractError("bar count must not be negative")

    def to_dict(self) -> dict:
        return {
            "window_open_utc": _iso(self.window_open_utc),
            "window_close_utc": _iso(self.window_close_utc),
            "input_digest": self.input_digest,
            "bar_count": self.bar_count,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SourceWindow":
        return cls(
            window_open_utc=_parse_iso(data["window_open_utc"]),
            window_close_utc=_parse_iso(data["window_close_utc"]),
            input_digest=data["input_digest"],
            bar_count=int(data["bar_count"]),
        )


@dataclass(frozen=True)
class Provenance:
    """The caller-supplied provenance bits of one computation.

    The source window is *not* part of it: each measurement derives its
    own window from the data it actually consumed, so the digest always
    binds the inputs that produced the value.
    """

    instrument_id: str
    clock_id: str
    session_id: str
    calculation_timestamp: datetime
    clock_registry_version: str = CLOCK_REGISTRY_VERSION
    session_registry_version: str = SESSION_REGISTRY_VERSION
    market_data_schema_version: str = MARKET_DATA_SCHEMA_VERSION
    measurement_engine_version: str = MEASUREMENT_ENGINE_VERSION

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise MeasurementContractError("provenance requires an instrument id")
        if not self.clock_id or not self.session_id:
            raise MeasurementContractError(
                "provenance requires a clock id and a session id"
            )
        if not isinstance(self.calculation_timestamp, datetime):
            raise MeasurementContractError("calculation timestamp must be a datetime")
        if self.calculation_timestamp.tzinfo is None:
            raise MeasurementContractError("calculation timestamp must be tz-aware")
        object.__setattr__(
            self,
            "calculation_timestamp",
            self.calculation_timestamp.astimezone(timezone.utc),
        )
        if self.measurement_engine_version != MEASUREMENT_ENGINE_VERSION:
            raise MeasurementContractError("unknown measurement engine version")
        if self.market_data_schema_version != MARKET_DATA_SCHEMA_VERSION:
            raise MeasurementContractError("unknown market-data schema version")

    def context(
        self,
        source_window: SourceWindow,
        quality_state: DataOutcome = DataOutcome.OK,
    ) -> "MeasurementContext":
        """Bind this provenance to a derived source window."""
        return MeasurementContext(
            instrument_id=self.instrument_id,
            source_window=source_window,
            clock_id=self.clock_id,
            session_id=self.session_id,
            calculation_timestamp=self.calculation_timestamp,
            clock_registry_version=self.clock_registry_version,
            session_registry_version=self.session_registry_version,
            market_data_schema_version=self.market_data_schema_version,
            measurement_engine_version=self.measurement_engine_version,
            quality_state=quality_state,
        )


@dataclass(frozen=True)
class MeasurementContext:
    """The provenance bits shared by every measurement in one computation."""

    instrument_id: str
    source_window: SourceWindow
    clock_id: str
    session_id: str
    calculation_timestamp: datetime
    clock_registry_version: str = CLOCK_REGISTRY_VERSION
    session_registry_version: str = SESSION_REGISTRY_VERSION
    market_data_schema_version: str = MARKET_DATA_SCHEMA_VERSION
    measurement_engine_version: str = MEASUREMENT_ENGINE_VERSION
    quality_state: DataOutcome = DataOutcome.OK

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise MeasurementContractError("context requires an instrument id")
        if not self.clock_id or not self.session_id:
            raise MeasurementContractError(
                "context requires a clock id and a session id"
            )
        if not isinstance(self.calculation_timestamp, datetime):
            raise MeasurementContractError("calculation timestamp must be a datetime")
        if self.calculation_timestamp.tzinfo is None:
            raise MeasurementContractError("calculation timestamp must be tz-aware")
        object.__setattr__(
            self,
            "calculation_timestamp",
            self.calculation_timestamp.astimezone(timezone.utc),
        )
        if self.measurement_engine_version != MEASUREMENT_ENGINE_VERSION:
            raise MeasurementContractError("unknown measurement engine version")
        if self.market_data_schema_version != MARKET_DATA_SCHEMA_VERSION:
            raise MeasurementContractError("unknown market-data schema version")

    def with_quality(self, quality_state: DataOutcome) -> "MeasurementContext":
        return MeasurementContext(
            instrument_id=self.instrument_id,
            source_window=self.source_window,
            clock_id=self.clock_id,
            session_id=self.session_id,
            calculation_timestamp=self.calculation_timestamp,
            clock_registry_version=self.clock_registry_version,
            session_registry_version=self.session_registry_version,
            market_data_schema_version=self.market_data_schema_version,
            measurement_engine_version=self.measurement_engine_version,
            quality_state=quality_state,
        )


@dataclass(frozen=True)
class Measurement:
    """The frozen provenance envelope carried by every emitted measurement.

    Subclasses add the measured quantities.  Nothing here is mutable:
    redefinition requires a new definition version.
    """

    definition_id: str
    definition_version: str
    instrument_id: str
    source_window: SourceWindow
    clock_id: str
    clock_registry_version: str
    session_id: str
    session_registry_version: str
    calculation_timestamp: datetime
    quality_state: DataOutcome
    native_unit: NativeUnit | None
    market_data_schema_version: str
    measurement_engine_version: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        require_definition(self.definition_id, self.definition_version)
        if not self.instrument_id:
            raise MeasurementContractError("measurement requires an instrument id")
        if not self.clock_id or not self.session_id:
            raise MeasurementContractError(
                "measurement requires a clock id and a session id"
            )
        if not isinstance(self.calculation_timestamp, datetime):
            raise MeasurementContractError("calculation timestamp must be a datetime")
        if self.calculation_timestamp.tzinfo is None:
            raise MeasurementContractError("calculation timestamp must be tz-aware")
        object.__setattr__(
            self,
            "calculation_timestamp",
            self.calculation_timestamp.astimezone(timezone.utc),
        )
        if self.quality_state is not DataOutcome.OK and self.quality_state is not (
            DataOutcome.DEGRADED
        ):
            raise MeasurementContractError(
                "a blocked measurement is refused, not emitted"
            )
        if self.measurement_engine_version != MEASUREMENT_ENGINE_VERSION:
            raise MeasurementContractError("unknown measurement engine version")
        if self.market_data_schema_version != MARKET_DATA_SCHEMA_VERSION:
            raise MeasurementContractError("unknown market-data schema version")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    # -- serialization -------------------------------------------------
    def to_dict(self) -> dict:
        return encode_value(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @property
    def definition(self) -> DefinitionSpec:
        return require_definition(self.definition_id, self.definition_version)


def envelope(
    context: MeasurementContext,
    definition_id: str,
    *,
    definition_version: str = "V1",
    native_unit: NativeUnit | None = None,
    evidence_refs: Iterable[str] = (),
    quality_state: DataOutcome | None = None,
) -> dict:
    """Build the provenance keyword arguments for a measurement."""
    require_definition(definition_id, definition_version)
    return {
        "definition_id": definition_id,
        "definition_version": definition_version,
        "instrument_id": context.instrument_id,
        "source_window": context.source_window,
        "clock_id": context.clock_id,
        "clock_registry_version": context.clock_registry_version,
        "session_id": context.session_id,
        "session_registry_version": context.session_registry_version,
        "calculation_timestamp": context.calculation_timestamp,
        "quality_state": quality_state or context.quality_state,
        "native_unit": native_unit,
        "market_data_schema_version": context.market_data_schema_version,
        "measurement_engine_version": context.measurement_engine_version,
        "evidence_refs": tuple(evidence_refs),
    }


# ----------------------------------------------------------------------
# Deterministic serialization
# ----------------------------------------------------------------------


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def encode_value(value: Any) -> Any:
    """Encode a measurement graph deterministically.

    Enums become their value, Decimals their exact string, datetimes
    UTC ISO-8601, and dataclasses plain dictionaries.  The encoding is
    lossless for every type the package emits, so a round trip preserves
    typed distinctions exactly.
    """
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _iso(value)
    if isinstance(value, NativePrice):
        return {
            "instrument_id": value.instrument_id,
            "unit": value.unit.value,
            "value": str(value.value),
        }
    if isinstance(value, NativeMagnitude):
        return value.to_dict()
    if isinstance(value, SourceWindow):
        return value.to_dict()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: encode_value(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, (tuple, list)):
        return [encode_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(encode_value(item) for item in value)
    if isinstance(value, Mapping):
        return {str(key): encode_value(item) for key, item in sorted(value.items())}
    return value


def decode_value(anchor: Any, data: Any) -> Any:
    """Rebuild a measurement graph from :func:`encode_value` output.

    ``anchor`` is a dataclass whose field types drive the rebuild; enum
    fields are rebuilt from their value, ``Decimal`` from its string.
    """
    if isinstance(anchor, Enum):
        return anchor.__class__(data)
    if isinstance(anchor, bool) or anchor is None:
        return data
    if isinstance(anchor, Decimal):
        return Decimal(data)
    if isinstance(anchor, datetime):
        return _parse_iso(data)
    if isinstance(anchor, NativePrice):
        return NativePrice(
            instrument_id=data["instrument_id"],
            unit=NativeUnit(data["unit"]),
            value=Decimal(data["value"]),
        )
    if isinstance(anchor, NativeMagnitude):
        return NativeMagnitude.from_dict(data)
    if isinstance(anchor, SourceWindow):
        return SourceWindow.from_dict(data)
    if isinstance(anchor, (tuple, list)):
        return tuple(
            decode_value(item, value)
            for item, value in zip(anchor, data)
        )
    if is_dataclass(anchor) and not isinstance(anchor, type):
        kwargs = {}
        for item in fields(anchor):
            if item.name not in data:
                continue
            kwargs[item.name] = decode_value(
                getattr(anchor, item.name), data[item.name]
            )
        return anchor.__class__(**kwargs)
    return data
