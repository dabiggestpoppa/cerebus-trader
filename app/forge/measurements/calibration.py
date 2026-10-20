"""Tier / AU calibration (Ch III.2.2).

Calibration is **asset- and model-local**.  A table is keyed by
``(model_id, model_version, calibration_id, calibration_version)`` and
each table additionally binds one instrument and one native unit.  A
lookup with any wrong or missing key refuses; a magnitude from another
asset refuses; there is **no global universal tier constant** anywhere
in this package and no nearest-bucket guessing.

The canonical tables below are transcribed from the frozen corpus:

* ``EUR_DAILY_PHASE1_TIERS`` — T1 <20p / T2 20-30p / T3 30-45p / >45p
  no-go, from ``EV.EUR.DAILY.PHASE1_TIERS.V1`` (status
  ``FROZEN_LAUNCH``).  The associated Phase1 *expansion multipliers*
  are deliberately **not** encoded: the evidence card states them
  approximately and they are model-level range-expansion expectations
  (a later Bloc's concern), not measurements.
* ``BTC_TRACKER_DWM_TIERS`` — T1 <$750 / T2 $750-$1,700 / T3 $1,700-$3,000
  / >$3,000 no-go, AU 205/545/1160, threshold levels 246/654/1392 and
  density zones 164-246 / 436-654 / 928-1392, from
  ``BTC.TRACKER.DWM.V1`` (status ``FROZEN_LAUNCH``).  The canonical
  field name ``trigger_levels`` is preserved verbatim from the model
  card: these are threshold constants, not execution triggers.
* ``XAU_SPATIAL_BANDS`` — 25-50 normal / 50-68 failure / 68+ repair /
  100-110 snap, from ``XAU.GAME.L1_L2_L3.V1`` (status ``RESEARCH``).
  XAU has spatial bands, not an EUR-style tier table (III.2-GAP-3).
* ``EUR_WEEKLY_TIER_RANGE`` — weekly tier medians and sample sizes, from
  ``EV.EUR.WEEKLY.TIER_RANGE.V1`` (status ``RESEARCH``).

JPY pair-native tier tables are **not** canonical (III.2-GAP-2): the
only JPY calibration registered here is the coordinate family declared
by the JPY model card, and a JPY tier lookup refuses with
``MODEL_VERSION_UNAVAILABLE`` rather than inventing a table.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping, Sequence

from app.forge.market_data import NativeUnit

from .contracts import (
    Measurement,
    NativeMagnitude,
    Provenance,
    SourceWindow,
    envelope,
)
from .errors import (
    CalibrationTransferRefusedError,
    MeasurementContractError,
    ModelVersionUnavailableError,
    UnclassifiedValueError,
)

__all__ = [
    "AuScale",
    "AuScaleMeasurement",
    "CalibrationKey",
    "CalibrationRegistry",
    "CalibrationStatus",
    "DensityZone",
    "DensityZoneMeasurement",
    "SpatialBand",
    "SpatialBandClassification",
    "SpatialBandState",
    "SpatialBandTable",
    "ThresholdLevels",
    "ThresholdLevelsMeasurement",
    "TierBand",
    "TierClassification",
    "TierTable",
    "WeeklyOuterNodeTable",
    "CALIBRATION_REGISTRY",
    "classify_spatial_band",
    "classify_tier",
    "measure_au_scale",
    "measure_density_zones",
    "measure_threshold_levels",
]


class CalibrationStatus(str, Enum):
    """Declared standing of one calibration.

    ``FROZEN_LAUNCH`` calibrations are the fixed launch tables;
    ``RESEARCH`` calibrations are research claims that travel with every
    output they produce and are never silently promotable.
    """

    FROZEN_LAUNCH = "FROZEN_LAUNCH"
    RESEARCH = "RESEARCH"


@dataclass(frozen=True)
class CalibrationKey:
    """The four-part identity of one calibration."""

    model_id: str
    model_version: str
    calibration_id: str
    calibration_version: str

    def __post_init__(self) -> None:
        for name in (
            "model_id",
            "model_version",
            "calibration_id",
            "calibration_version",
        ):
            if not getattr(self, name):
                raise MeasurementContractError(f"{name} is required")

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "calibration_id": self.calibration_id,
            "calibration_version": self.calibration_version,
        }


@dataclass(frozen=True)
class TierBand:
    """One band of a tier table.

    Bounds carry explicit inclusivity so that every boundary edge is
    decided, not guessed.  A ``no_go`` band is a canonical
    classification (an explicit refusal to act on that magnitude), not
    an unclassified value.
    """

    tier_id: str
    lower: Decimal | None = None
    upper: Decimal | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = False
    no_go: bool = False

    def __post_init__(self) -> None:
        if not self.tier_id:
            raise MeasurementContractError("tier band requires a tier id")
        if (
            self.lower is not None
            and self.upper is not None
            and self.lower > self.upper
        ):
            raise MeasurementContractError("tier band lower bound above upper bound")

    def contains(self, value: Decimal) -> bool:
        if self.lower is not None:
            if value < self.lower or (
                value == self.lower and not self.lower_inclusive
            ):
                return False
        if self.upper is not None:
            if value > self.upper or (
                value == self.upper and not self.upper_inclusive
            ):
                return False
        return True

    def width(self) -> Decimal | None:
        if self.lower is None or self.upper is None:
            return None
        return self.upper - self.lower

    def to_dict(self) -> dict:
        return {
            "tier_id": self.tier_id,
            "lower": str(self.lower) if self.lower is not None else None,
            "upper": str(self.upper) if self.upper is not None else None,
            "lower_inclusive": self.lower_inclusive,
            "upper_inclusive": self.upper_inclusive,
            "no_go": self.no_go,
        }


@dataclass(frozen=True)
class TierTable:
    """One asset/model-native tier table."""

    key: CalibrationKey
    instrument_id: str
    unit: NativeUnit
    status: CalibrationStatus
    bands: tuple[TierBand, ...]
    source_ref: str
    evidence_refs: tuple[str, ...] = ()
    tier_labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.bands:
            raise MeasurementContractError("tier table requires at least one band")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    def band_for(self, value: Decimal) -> TierBand | None:
        for band in self.bands:
            if band.contains(value):
                return band
        return None


@dataclass(frozen=True)
class AuScale:
    """Asset-native atomic distance published by one calibration.

    The crosswalk defines AU as the *native atomic distance*: an EUR AU
    is a pip count, a BTC AU is a dollar count and an XAU AU is a point
    count.  AU values are never transferable between assets.
    """

    key: CalibrationKey
    instrument_id: str
    unit: NativeUnit
    status: CalibrationStatus
    values: tuple[tuple[str, Decimal], ...]
    source_ref: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.values:
            raise MeasurementContractError("AU scale requires at least one value")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    def value_for(self, tier_id: str) -> Decimal:
        for name, value in self.values:
            if name == tier_id:
                return value
        raise UnclassifiedValueError(
            f"calibration declares no AU value for tier {tier_id!r}"
        )


@dataclass(frozen=True)
class ThresholdLevels:
    """Canonical threshold constants of one calibration.

    ``EUR``'s counterpart does not exist; ``BTC``'s canonical model card
    publishes ``trigger_levels`` 246/654/1392.  The canonical name is
    preserved verbatim: these are thresholds, not execution triggers.
    """

    key: CalibrationKey
    instrument_id: str
    unit: NativeUnit
    status: CalibrationStatus
    levels: tuple[Decimal, ...]
    source_ref: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.levels:
            raise MeasurementContractError(
                "threshold levels require at least one level"
            )
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))


@dataclass(frozen=True)
class DensityZone:
    """One AU/threshold overlap zone of a calibration."""

    zone_id: str
    lower: Decimal
    upper: Decimal
    instrument_id: str
    unit: NativeUnit

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise MeasurementContractError("density zone lower bound above upper")


@dataclass(frozen=True)
class WeeklyOuterNodeTable:
    """Research-graded weekly outer-node magnitudes per weekly tier.

    The EUR Weekly research reports a *median weekly range* per tier
    together with its sample size; it does not publish the tier
    boundaries themselves.  A weekly tier is therefore an **input** to
    this table, never a classification produced by it, and no band
    boundaries are invented here.
    """

    key: CalibrationKey
    instrument_id: str
    unit: NativeUnit
    status: CalibrationStatus
    outer_nodes: tuple[tuple[str, Decimal, int], ...]
    source_ref: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.outer_nodes:
            raise MeasurementContractError(
                "weekly outer node table requires at least one entry"
            )
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    def node_for(self, tier_id: str) -> tuple[Decimal, int]:
        for name, magnitude, sample_n in self.outer_nodes:
            if name == tier_id:
                return magnitude, sample_n
        raise UnclassifiedValueError(
            f"calibration declares no weekly outer node for tier {tier_id!r}"
        )


@dataclass(frozen=True)
class SpatialBandState(str, Enum):
    """Declared state of one XAU spatial band."""

    NORMAL = "NORMAL"
    FAILURE = "FAILURE"
    REPAIR = "REPAIR"
    SNAP = "SNAP"


@dataclass(frozen=True)
class SpatialBand:
    """One spatial band of a band table (XAU doctrine, not a tier table)."""

    band_id: str
    state: SpatialBandState
    lower: Decimal | None = None
    upper: Decimal | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = False

    def contains(self, value: Decimal) -> bool:
        if self.lower is not None:
            if value < self.lower or (
                value == self.lower and not self.lower_inclusive
            ):
                return False
        if self.upper is not None:
            if value > self.upper or (
                value == self.upper and not self.upper_inclusive
            ):
                return False
        return True

    def width(self) -> Decimal | None:
        if self.lower is None or self.upper is None:
            return None
        return self.upper - self.lower


@dataclass(frozen=True)
class SpatialBandTable:
    """One spatial-band table.

    Bands may overlap (XAU's ``68+ repair`` contains ``100-110 snap``);
    the narrowest matching band wins, and two equally narrow matches are
    an explicit refusal rather than a guess.
    """

    key: CalibrationKey
    instrument_id: str
    unit: NativeUnit
    status: CalibrationStatus
    bands: tuple[SpatialBand, ...]
    source_ref: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.bands:
            raise MeasurementContractError(
                "spatial band table requires at least one band"
            )
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))


# ----------------------------------------------------------------------
# Registries
# ----------------------------------------------------------------------


class CalibrationRegistry:
    """Versioned lookup of the declared calibrations.

    A key that is not registered refuses with
    ``MODEL_VERSION_UNAVAILABLE``; there is never a silent fallback to
    another model, version or asset.
    """

    def __init__(self) -> None:
        self._tier_tables: dict[CalibrationKey, TierTable] = {}
        self._au_scales: dict[CalibrationKey, AuScale] = {}
        self._threshold_levels: dict[CalibrationKey, ThresholdLevels] = {}
        self._density_zones: dict[CalibrationKey, tuple[DensityZone, ...]] = {}
        self._spatial_tables: dict[CalibrationKey, SpatialBandTable] = {}
        self._weekly_outer_nodes: dict[CalibrationKey, WeeklyOuterNodeTable] = {}

    def add_tier_table(self, table: TierTable) -> None:
        if table.key in self._tier_tables:
            raise MeasurementContractError(f"duplicate tier table {table.key}")
        self._tier_tables[table.key] = table

    def add_au_scale(self, scale: AuScale) -> None:
        if scale.key in self._au_scales:
            raise MeasurementContractError(f"duplicate AU scale {scale.key}")
        self._au_scales[scale.key] = scale

    def add_threshold_levels(self, levels: ThresholdLevels) -> None:
        if levels.key in self._threshold_levels:
            raise MeasurementContractError(f"duplicate threshold levels {levels.key}")
        self._threshold_levels[levels.key] = levels

    def add_density_zones(self, key: CalibrationKey, zones: Sequence[DensityZone]) -> None:
        if key in self._density_zones:
            raise MeasurementContractError(f"duplicate density zones {key}")
        self._density_zones[key] = tuple(zones)

    def add_spatial_table(self, table: SpatialBandTable) -> None:
        if table.key in self._spatial_tables:
            raise MeasurementContractError(f"duplicate spatial table {table.key}")
        self._spatial_tables[table.key] = table

    def add_weekly_outer_nodes(self, table: WeeklyOuterNodeTable) -> None:
        if table.key in self._weekly_outer_nodes:
            raise MeasurementContractError(
                f"duplicate weekly outer node table {table.key}"
            )
        self._weekly_outer_nodes[table.key] = table

    def weekly_outer_nodes(self, key: CalibrationKey) -> WeeklyOuterNodeTable:
        try:
            return self._weekly_outer_nodes[key]
        except KeyError:
            raise ModelVersionUnavailableError(
                "no weekly outer node table registered for "
                f"{key.model_id}/{key.model_version}/"
                f"{key.calibration_id}/{key.calibration_version}"
            ) from None

    def tier_table(self, key: CalibrationKey) -> TierTable:
        try:
            return self._tier_tables[key]
        except KeyError:
            raise ModelVersionUnavailableError(
                "no tier table registered for "
                f"{key.model_id}/{key.model_version}/"
                f"{key.calibration_id}/{key.calibration_version}"
            ) from None

    def au_scale(self, key: CalibrationKey) -> AuScale:
        try:
            return self._au_scales[key]
        except KeyError:
            raise ModelVersionUnavailableError(
                "no AU scale registered for "
                f"{key.model_id}/{key.model_version}/"
                f"{key.calibration_id}/{key.calibration_version}"
            ) from None

    def threshold_levels(self, key: CalibrationKey) -> ThresholdLevels:
        try:
            return self._threshold_levels[key]
        except KeyError:
            raise ModelVersionUnavailableError(
                "no threshold levels registered for "
                f"{key.model_id}/{key.model_version}/"
                f"{key.calibration_id}/{key.calibration_version}"
            ) from None

    def density_zones(self, key: CalibrationKey) -> tuple[DensityZone, ...]:
        try:
            return self._density_zones[key]
        except KeyError:
            raise ModelVersionUnavailableError(
                "no density zones registered for "
                f"{key.model_id}/{key.model_version}/"
                f"{key.calibration_id}/{key.calibration_version}"
            ) from None

    def spatial_table(self, key: CalibrationKey) -> SpatialBandTable:
        try:
            return self._spatial_tables[key]
        except KeyError:
            raise ModelVersionUnavailableError(
                "no spatial band table registered for "
                f"{key.model_id}/{key.model_version}/"
                f"{key.calibration_id}/{key.calibration_version}"
            ) from None

    def keys(self) -> tuple[CalibrationKey, ...]:
        return tuple(
            sorted(
                set(self._tier_tables)
                | set(self._au_scales)
                | set(self._threshold_levels)
            | set(self._density_zones)
            | set(self._spatial_tables)
            | set(self._weekly_outer_nodes),
                key=lambda key: key.to_dict()["model_id"],
            )
        )


CALIBRATION_REGISTRY = CalibrationRegistry()


# ----------------------------------------------------------------------
# Canonical tables
# ----------------------------------------------------------------------

_EUR_TIER_KEY = CalibrationKey(
    model_id="EUR.DAILY.NEWS_REKEY.V1",
    model_version="PHASE1",
    calibration_id="EUR_DAILY_PHASE1_TIERS",
    calibration_version="V1",
)

_BTC_TIER_KEY = CalibrationKey(
    model_id="BTC.TRACKER.DWM.V1",
    model_version="V1",
    calibration_id="BTC_TRACKER_DWM_TIERS",
    calibration_version="V1",
)

_XAU_BAND_KEY = CalibrationKey(
    model_id="XAU.GAME.L1_L2_L3.V1",
    model_version="V1",
    calibration_id="XAU_SPATIAL_BANDS",
    calibration_version="V1",
)

_EUR_WEEKLY_KEY = CalibrationKey(
    model_id="EUR.WEEKLY.V1_1",
    model_version="V1_1",
    calibration_id="EUR_WEEKLY_TIER_RANGE",
    calibration_version="V1",
)

_EUR_TIER_TABLE = TierTable(
    key=_EUR_TIER_KEY,
    instrument_id="EURUSD",
    unit=NativeUnit.PIP,
    status=CalibrationStatus.FROZEN_LAUNCH,
    bands=(
        TierBand(tier_id="T1", lower=None, upper=Decimal("20"), upper_inclusive=False),
        TierBand(
            tier_id="T2",
            lower=Decimal("20"),
            upper=Decimal("30"),
            lower_inclusive=True,
            upper_inclusive=False,
        ),
        TierBand(
            tier_id="T3",
            lower=Decimal("30"),
            upper=Decimal("45"),
            lower_inclusive=True,
            upper_inclusive=True,
        ),
        TierBand(
            tier_id="NO_GO",
            lower=Decimal("45"),
            lower_inclusive=False,
            upper=None,
            no_go=True,
        ),
    ),
    source_ref="corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md",
    evidence_refs=("EV.EUR.DAILY.PHASE1_TIERS.V1",),
    tier_labels=("T1", "T2", "T3", "NO_GO"),
)

_BTC_TIER_TABLE = TierTable(
    key=_BTC_TIER_KEY,
    instrument_id="BTCUSD",
    unit=NativeUnit.DOLLAR,
    status=CalibrationStatus.FROZEN_LAUNCH,
    bands=(
        TierBand(tier_id="T1", lower=None, upper=Decimal("750"), upper_inclusive=False),
        TierBand(
            tier_id="T2",
            lower=Decimal("750"),
            upper=Decimal("1700"),
            lower_inclusive=True,
            upper_inclusive=False,
        ),
        TierBand(
            tier_id="T3",
            lower=Decimal("1700"),
            upper=Decimal("3000"),
            lower_inclusive=True,
            upper_inclusive=True,
        ),
        TierBand(
            tier_id="NO_GO",
            lower=Decimal("3000"),
            lower_inclusive=False,
            upper=None,
            no_go=True,
        ),
    ),
    source_ref="corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md",
    evidence_refs=("BTC.TRACKER.DWM.V1",),
    tier_labels=("T1", "T2", "T3", "NO_GO"),
)

_BTC_AU_SCALE = AuScale(
    key=_BTC_TIER_KEY,
    instrument_id="BTCUSD",
    unit=NativeUnit.DOLLAR,
    status=CalibrationStatus.FROZEN_LAUNCH,
    values=(
        ("T1", Decimal("205")),
        ("T2", Decimal("545")),
        ("T3", Decimal("1160")),
    ),
    source_ref="corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md",
    evidence_refs=("BTC.TRACKER.DWM.V1",),
)

_BTC_THRESHOLD_LEVELS = ThresholdLevels(
    key=_BTC_TIER_KEY,
    instrument_id="BTCUSD",
    unit=NativeUnit.DOLLAR,
    status=CalibrationStatus.FROZEN_LAUNCH,
    levels=(Decimal("246"), Decimal("654"), Decimal("1392")),
    source_ref="corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md",
    evidence_refs=("BTC.TRACKER.DWM.V1",),
)

_BTC_DENSITY_ZONES = (
    DensityZone("T1", Decimal("164"), Decimal("246"), "BTCUSD", NativeUnit.DOLLAR),
    DensityZone("T2", Decimal("436"), Decimal("654"), "BTCUSD", NativeUnit.DOLLAR),
    DensityZone("T3", Decimal("928"), Decimal("1392"), "BTCUSD", NativeUnit.DOLLAR),
)

_XAU_SPATIAL_TABLE = SpatialBandTable(
    key=_XAU_BAND_KEY,
    instrument_id="XAUUSD",
    unit=NativeUnit.POINT,
    status=CalibrationStatus.RESEARCH,
    bands=(
        SpatialBand("XAU_NORMAL", SpatialBandState.NORMAL, Decimal("25"), Decimal("50")),
        SpatialBand("XAU_FAILURE", SpatialBandState.FAILURE, Decimal("50"), Decimal("68")),
        SpatialBand("XAU_REPAIR", SpatialBandState.REPAIR, Decimal("68"), None),
        SpatialBand("XAU_SNAP", SpatialBandState.SNAP, Decimal("100"), Decimal("110")),
    ),
    source_ref="corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md",
    evidence_refs=("XAU.GAME.L1_L2_L3.V1",),
)

_EUR_WEEKLY_OUTER_NODE_TABLE = WeeklyOuterNodeTable(
    key=_EUR_WEEKLY_KEY,
    instrument_id="EURUSD",
    unit=NativeUnit.PIP,
    status=CalibrationStatus.RESEARCH,
    outer_nodes=(
        ("T1", Decimal("126.8"), 45),
        ("T2", Decimal("133.5"), 69),
        ("T3", Decimal("168.95"), 60),
    ),
    source_ref="corpus/canonical/evidence/EUR_WEEKLY_TIER_RANGE_EVIDENCE_V1.md",
    evidence_refs=("EV.EUR.WEEKLY.TIER_RANGE.V1",),
)

CALIBRATION_REGISTRY.add_tier_table(_EUR_TIER_TABLE)
CALIBRATION_REGISTRY.add_tier_table(_BTC_TIER_TABLE)
CALIBRATION_REGISTRY.add_au_scale(_BTC_AU_SCALE)
CALIBRATION_REGISTRY.add_threshold_levels(_BTC_THRESHOLD_LEVELS)
CALIBRATION_REGISTRY.add_density_zones(_BTC_TIER_KEY, _BTC_DENSITY_ZONES)
CALIBRATION_REGISTRY.add_spatial_table(_XAU_SPATIAL_TABLE)
CALIBRATION_REGISTRY.add_weekly_outer_nodes(_EUR_WEEKLY_OUTER_NODE_TABLE)


# ----------------------------------------------------------------------
# Classification
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class TierClassification(Measurement):
    """The classification of one native magnitude into one tier band."""

    tier_id: str
    no_go: bool
    magnitude: NativeMagnitude
    calibration_key: CalibrationKey
    calibration_status: CalibrationStatus
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def _require_local(table_instrument: str, table_unit: NativeUnit, magnitude: NativeMagnitude) -> None:
    if magnitude.instrument_id != table_instrument:
        raise CalibrationTransferRefusedError(
            f"calibration is local to {table_instrument}; "
            f"refusing {magnitude.instrument_id}"
        )
    if magnitude.unit is not table_unit:
        raise CalibrationTransferRefusedError(
            f"calibration is local to {table_unit.value}; "
            f"refusing {magnitude.unit.value}"
        )


def classify_tier(
    registry: CalibrationRegistry,
    key: CalibrationKey,
    magnitude: NativeMagnitude,
    *,
    provenance: Provenance,
    source_window: SourceWindow,
    definition_version: str = "V1",
) -> TierClassification:
    """Classify one native magnitude into a tier of one calibration.

    A magnitude from another asset or unit refuses: calibration is
    local unless transfer is explicitly validated (invariant #2).  A
    magnitude that matches no band refuses as unclassified — the engine
    never picks the nearest bucket.
    """
    table = registry.tier_table(key)
    _require_local(table.instrument_id, table.unit, magnitude)
    band = table.band_for(magnitude.value)
    if band is None:
        raise UnclassifiedValueError(
            f"value {magnitude.value} matches no declared band of "
            f"{key.calibration_id}"
        )
    context = provenance.context(source_window)
    return TierClassification(
        **envelope(
            context,
            "TIER_CLASSIFICATION",
            definition_version=definition_version,
            native_unit=magnitude.unit,
            evidence_refs=table.evidence_refs,
        ),
        tier_id=band.tier_id,
        no_go=band.no_go,
        magnitude=magnitude,
        calibration_key=key,
        calibration_status=table.status,
        source_ref=table.source_ref,
    )


@dataclass(frozen=True)
class SpatialBandClassification(Measurement):
    """The classification of one native magnitude into one spatial band."""

    band_id: str
    band_state: SpatialBandState
    magnitude: NativeMagnitude
    calibration_key: CalibrationKey
    calibration_status: CalibrationStatus
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def classify_spatial_band(
    registry: CalibrationRegistry,
    key: CalibrationKey,
    magnitude: NativeMagnitude,
    *,
    provenance: Provenance,
    source_window: SourceWindow,
    definition_version: str = "V1",
) -> SpatialBandClassification:
    """Classify one native magnitude into a spatial band.

    The narrowest matching band wins; two equally narrow matches are an
    explicit refusal rather than a guess.
    """
    table = registry.spatial_table(key)
    _require_local(table.instrument_id, table.unit, magnitude)
    matches = [band for band in table.bands if band.contains(magnitude.value)]
    if not matches:
        raise UnclassifiedValueError(
            f"value {magnitude.value} matches no declared band of "
            f"{key.calibration_id}"
        )
    if len(matches) == 1:
        # A single matching band is unambiguous even when it is
        # open-ended (the canonical XAU "68+ repair" band).
        band = matches[0]
    else:
        widths = [band.width() for band in matches]
        finite = [width for width in widths if width is not None]
        if not finite:
            raise UnclassifiedValueError(
                f"value {magnitude.value} matches only open-ended bands of "
                f"{key.calibration_id}"
            )
        narrowest = min(finite)
        best = [
            band
            for band, width in zip(matches, widths)
            if width is not None and width == narrowest
        ]
        if len(best) != 1:
            raise UnclassifiedValueError(
                f"value {magnitude.value} matches {len(best)} equally narrow bands "
                f"of {key.calibration_id}"
            )
        band = best[0]
    context = provenance.context(source_window)
    return SpatialBandClassification(
        **envelope(
            context,
            "SPATIAL_BAND_CLASSIFICATION",
            definition_version=definition_version,
            native_unit=magnitude.unit,
            evidence_refs=table.evidence_refs,
        ),
        band_id=band.band_id,
        band_state=band.state,
        magnitude=magnitude,
        calibration_key=key,
        calibration_status=table.status,
        source_ref=table.source_ref,
    )


@dataclass(frozen=True)
class AuScaleMeasurement(Measurement):
    """The asset-native atomic distance published for one tier."""

    tier_id: str
    au: NativeMagnitude
    calibration_key: CalibrationKey
    calibration_status: CalibrationStatus
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def measure_au_scale(
    registry: CalibrationRegistry,
    key: CalibrationKey,
    tier_id: str,
    *,
    provenance: Provenance,
    source_window: SourceWindow,
    definition_version: str = "V1",
) -> AuScaleMeasurement:
    """Measure the AU published for one tier of one calibration.

    The AU is the *asset-native atomic distance*: an EUR AU counts
    pips, a BTC AU counts dollars, an XAU AU counts points.  The
    measurement therefore always carries the instrument and the native
    unit — an AU is never transferable between assets.
    """
    scale = registry.au_scale(key)
    value = scale.value_for(tier_id)
    au = NativeMagnitude(scale.instrument_id, scale.unit, value)
    context = provenance.context(source_window)
    return AuScaleMeasurement(
        **envelope(
            context,
            "AU_SCALE",
            definition_version=definition_version,
            native_unit=scale.unit,
            evidence_refs=scale.evidence_refs,
        ),
        tier_id=tier_id,
        au=au,
        calibration_key=key,
        calibration_status=scale.status,
        source_ref=scale.source_ref,
    )


@dataclass(frozen=True)
class ThresholdLevelsMeasurement(Measurement):
    """The published threshold constants of one calibration."""

    levels: tuple[NativeMagnitude, ...]
    calibration_key: CalibrationKey
    calibration_status: CalibrationStatus
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def measure_threshold_levels(
    registry: CalibrationRegistry,
    key: CalibrationKey,
    *,
    provenance: Provenance,
    source_window: SourceWindow,
    definition_version: str = "V1",
) -> ThresholdLevelsMeasurement:
    """Measure the published threshold constants of one calibration.

    The canonical BTC card publishes these under the name
    ``trigger_levels``.  The name is preserved verbatim in the corpus;
    these are threshold constants, never execution triggers.
    """
    levels = registry.threshold_levels(key)
    context = provenance.context(source_window)
    return ThresholdLevelsMeasurement(
        **envelope(
            context,
            "THRESHOLD_LEVELS",
            definition_version=definition_version,
            native_unit=levels.unit,
            evidence_refs=levels.evidence_refs,
        ),
        levels=tuple(
            NativeMagnitude(levels.instrument_id, levels.unit, level)
            for level in levels.levels
        ),
        calibration_key=key,
        calibration_status=levels.status,
        source_ref=levels.source_ref,
    )


@dataclass(frozen=True)
class DensityZoneMeasurement(Measurement):
    """The published overlap zones of one calibration."""

    zones: tuple[DensityZone, ...]
    calibration_key: CalibrationKey
    calibration_status: CalibrationStatus
    source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def measure_density_zones(
    registry: CalibrationRegistry,
    key: CalibrationKey,
    *,
    provenance: Provenance,
    source_window: SourceWindow,
    definition_version: str = "V1",
) -> DensityZoneMeasurement:
    """Measure the published density zones of one calibration."""
    zones = registry.density_zones(key)
    source_ref = registry.threshold_levels(key).source_ref
    context = provenance.context(source_window)
    return DensityZoneMeasurement(
        **envelope(
            context,
            "DENSITY_ZONES",
            definition_version=definition_version,
            native_unit=zones[0].unit if zones else None,
        ),
        zones=zones,
        calibration_key=key,
        calibration_status=CalibrationStatus.FROZEN_LAUNCH,
        source_ref=source_ref,
    )
