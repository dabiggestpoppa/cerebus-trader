"""Coordinate engine (Ch III.2.3).

A *coordinate* is a projection of an **earned** range onto a declared
Fibonacci / extension family.  Two rules are structural, not advisory:

* **No anchor, no coordinate.**  A projection requires an anchor whose
  state is ``ELIGIBLE`` or ``ACTIVE`` (invariant #3, C2/C4).  There is
  no anchorless or arbitrary-pivot projection anywhere in this package
  — the R11 generic-pivot generator does not exist (C3/D5).
* **No auto-extension.**  A deeper coordinate appears only when the
  model *declares* it and the range *earns* it.  Projecting ``132``
  never yields ``168`` implicitly (C5).

Families are bounded to the canonical set
``50 / 61.8 / 68 / 72 / 80 / 82 / 100 / 120 / 125 / 132 / 168 / 185``
plus model-declared extensions that carry a source reference.  A family
outside the canonical set refuses; a canonical family that the model's
declared set does not contain refuses as *not earned* rather than
guessing.

A coordinate is a *level*, nothing more.  Touching it implies nothing:
the emitted projection carries no acceptance, rekey, promotion or setup
field.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping

from app.forge.market_data import NativePrice, NativeUnit

from .anchors import AnchorRecord, AnchorStatus
from .contracts import (
    Measurement,
    NativeMagnitude,
    Provenance,
    envelope,
)
from .errors import (
    AnchorNotEarnedError,
    CoordinateFamilyNotEarnedError,
    MeasurementContractError,
    ModelVersionUnavailableError,
    UnknownCoordinateFamilyError,
)

__all__ = [
    "COORDINATE_SETS",
    "CANONICAL_FAMILY_LEVELS",
    "CoordinateFamily",
    "CoordinateOrientation",
    "CoordinateProjection",
    "CoordinateSet",
    "RangeEdge",
    "project_coordinates",
]


#: The canonical Fibonacci / extension family levels (C1).
CANONICAL_FAMILY_LEVELS: tuple[Decimal, ...] = (
    Decimal("50"),
    Decimal("61.8"),
    Decimal("68"),
    Decimal("72"),
    Decimal("80"),
    Decimal("82"),
    Decimal("100"),
    Decimal("120"),
    Decimal("125"),
    Decimal("132"),
    Decimal("168"),
    Decimal("185"),
)


class RangeEdge(str, Enum):
    """The range edge a family is measured from."""

    LOW = "LOW"
    HIGH = "HIGH"


class CoordinateOrientation(str, Enum):
    """The orientation a projected coordinate preserves."""

    UP_FROM_LOW = "UP_FROM_LOW"
    DOWN_FROM_LOW = "DOWN_FROM_LOW"
    UP_FROM_HIGH = "UP_FROM_HIGH"
    DOWN_FROM_HIGH = "DOWN_FROM_HIGH"


@dataclass(frozen=True)
class CoordinateFamily:
    """One declared family of one model.

    ``level`` is a signed percentage of the earned range size.  A
    positive level measured from ``LOW`` projects upward from the range
    low; a negative level projects below it.  ``source_ref`` states the
    canonical source that declares the family.
    """

    family_id: str
    level: Decimal
    base: RangeEdge
    source_ref: str
    source_quote: str
    declared_extension: bool = False

    def __post_init__(self) -> None:
        if not self.family_id:
            raise MeasurementContractError("coordinate family requires an id")
        if not self.source_ref:
            raise MeasurementContractError("coordinate family requires a source ref")
        if not self.source_quote:
            raise MeasurementContractError(
                "coordinate family requires the source sentence that names it"
            )
        if not isinstance(self.level, Decimal):
            raise MeasurementContractError("coordinate level must be Decimal")
        if self.level == 0:
            raise MeasurementContractError("coordinate level must not be zero")

    @property
    def orientation(self) -> CoordinateOrientation:
        upward = self.level > 0
        if self.base is RangeEdge.LOW:
            return (
                CoordinateOrientation.UP_FROM_LOW
                if upward
                else CoordinateOrientation.DOWN_FROM_LOW
            )
        return (
            CoordinateOrientation.UP_FROM_HIGH
            if upward
            else CoordinateOrientation.DOWN_FROM_HIGH
        )

    def to_dict(self) -> dict:
        return {
            "family_id": self.family_id,
            "level": str(self.level),
            "base": self.base.value,
            "source_ref": self.source_ref,
            "source_quote": self.source_quote,
            "declared_extension": self.declared_extension,
        }


@dataclass(frozen=True)
class CoordinateSet:
    """The families one model/version declares."""

    model_id: str
    model_version: str
    families: tuple[CoordinateFamily, ...]
    source_ref: str

    def __post_init__(self) -> None:
        if not self.families:
            raise MeasurementContractError("a coordinate set requires families")
        if not self.source_ref:
            raise MeasurementContractError("a coordinate set requires a source ref")

    def family(self, family_id: str) -> CoordinateFamily | None:
        for family in self.families:
            if family.family_id == family_id:
                return family
        return None

    @property
    def family_ids(self) -> tuple[str, ...]:
        return tuple(family.family_id for family in self.families)


def _family(
    family_id: str,
    level: str,
    base: RangeEdge,
    source_ref: str,
    source_quote: str,
    *,
    declared_extension: bool = False,
) -> CoordinateFamily:
    return CoordinateFamily(
        family_id=family_id,
        level=Decimal(level),
        base=base,
        source_ref=source_ref,
        source_quote=source_quote,
        declared_extension=declared_extension,
    )


_FIB_SOURCE = (
    "corpus/canonical/models/FIB_RANGE_BIRTH_MODEL_CARD_V1.md"
)
_EUR_DAILY_SOURCE = (
    "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
)
_XAU_SOURCE = "corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"
_JPY_SOURCE = "corpus/canonical/models/JPY_CARRY_GAME_MODEL_CARD_V1.md"

#: The exact canonical sentences that name each declared family.  A
#: family is declared only when a frozen canonical source names it:
#: the canonical level set is the *bound*, each model declares the
#: subset its own card names (C1).
_FIB_ENTRY_QUOTE = "50-72 entry family."
_FIB_INVALIDATION_QUOTE = "80/82 invalidation family."
_FIB_DELIVERY_QUOTE = "-25/-50 delivery family."
_FIB_REKEY_QUOTE = "132 rekey."
_FIB_DEEPER_QUOTE = "168/185 deeper rekey/invalidation sequence."

_EUR_REKEY_QUOTE = (
    "100 /125 /132 /168 /185 appear in the modern Daily lineage."
)

_XAU_COORDINATE_QUOTE = (
    "Quarter zones; -50 decision node;132 rekey;80 invalidation family;"
    "50-72 Asian-range entry family."
)

_JPY_DT_QUOTE = (
    "JPY12-4PM DT research includes132/168/187.5 structures,"
    "no-132-touch continuation and132-touch+OCC recovery."
)


def _entry_families(
    prefix: str, source_ref: str, quote: str
) -> tuple[CoordinateFamily, ...]:
    """The 50-72 entry family named by a card.

    Family ids carry the level as an underscore token (``FIB_61_8``),
    matching the canonical-level resolver's ``61.8 -> 61_8`` spelling.
    """
    return tuple(
        _family(
            f"{prefix}_{level.replace('.', '_')}",
            level,
            RangeEdge.LOW,
            source_ref,
            quote,
        )
        for level in ("50", "61.8", "68", "72")
    )


#: The declared coordinate sets, keyed by ``(model_id, model_version)``.
#:
#: Each set contains **only** the families its own canonical card names.
#: A canonical level a card does not name is not declared for that
#: model, and asking for it refuses with
#: ``COORDINATE_FAMILY_NOT_EARNED`` (the ladder never auto-extends).
COORDINATE_SETS: Mapping[tuple[str, str], CoordinateSet] = {
    (
        "EUR.DAILY.NEWS_REKEY.V1",
        "PHASE1",
    ): CoordinateSet(
        model_id="EUR.DAILY.NEWS_REKEY.V1",
        model_version="PHASE1",
        families=tuple(
            _family(
                f"EUR_DAILY_{level}",
                level,
                RangeEdge.LOW,
                _EUR_DAILY_SOURCE,
                _EUR_REKEY_QUOTE,
            )
            for level in ("100", "125", "132", "168", "185")
        ),
        source_ref=_EUR_DAILY_SOURCE,
    ),
    (
        "CROSSASSET.FIB.RANGE_BIRTH.V1",
        "R15",
    ): CoordinateSet(
        model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
        model_version="R15",
        families=(
            *_entry_families("FIB", _FIB_SOURCE, _FIB_ENTRY_QUOTE),
            _family(
                "FIB_80", "80", RangeEdge.LOW, _FIB_SOURCE, _FIB_INVALIDATION_QUOTE
            ),
            _family(
                "FIB_82", "82", RangeEdge.LOW, _FIB_SOURCE, _FIB_INVALIDATION_QUOTE
            ),
            _family(
                "FIB_132", "132", RangeEdge.LOW, _FIB_SOURCE, _FIB_REKEY_QUOTE
            ),
            _family(
                "FIB_168", "168", RangeEdge.LOW, _FIB_SOURCE, _FIB_DEEPER_QUOTE
            ),
            _family(
                "FIB_185", "185", RangeEdge.LOW, _FIB_SOURCE, _FIB_DEEPER_QUOTE
            ),
            _family(
                "FIB_NEG_25",
                "-25",
                RangeEdge.LOW,
                _FIB_SOURCE,
                _FIB_DELIVERY_QUOTE,
                declared_extension=True,
            ),
            _family(
                "FIB_NEG_50",
                "-50",
                RangeEdge.LOW,
                _FIB_SOURCE,
                _FIB_DELIVERY_QUOTE,
                declared_extension=True,
            ),
        ),
        source_ref=_FIB_SOURCE,
    ),
    (
        "XAU.GAME.L1_L2_L3.V1",
        "V1",
    ): CoordinateSet(
        model_id="XAU.GAME.L1_L2_L3.V1",
        model_version="V1",
        families=(
            *_entry_families("XAU", _XAU_SOURCE, _XAU_COORDINATE_QUOTE),
            _family(
                "XAU_80", "80", RangeEdge.LOW, _XAU_SOURCE, _XAU_COORDINATE_QUOTE
            ),
            _family(
                "XAU_82", "82", RangeEdge.LOW, _XAU_SOURCE, _XAU_COORDINATE_QUOTE
            ),
            _family(
                "XAU_132", "132", RangeEdge.LOW, _XAU_SOURCE, _XAU_COORDINATE_QUOTE
            ),
            _family(
                "XAU_NEG_50",
                "-50",
                RangeEdge.LOW,
                _XAU_SOURCE,
                _XAU_COORDINATE_QUOTE,
                declared_extension=True,
            ),
        ),
        source_ref=_XAU_SOURCE,
    ),
    (
        "JPY.CARRY_GAME.L1_L3.V1",
        "DT_12_4PM",
    ): CoordinateSet(
        model_id="JPY.CARRY_GAME.L1_L3.V1",
        model_version="DT_12_4PM",
        families=(
            _family(
                "JPY_132", "132", RangeEdge.LOW, _JPY_SOURCE, _JPY_DT_QUOTE
            ),
            _family(
                "JPY_168", "168", RangeEdge.LOW, _JPY_SOURCE, _JPY_DT_QUOTE
            ),
            _family(
                "JPY_187_5",
                "187.5",
                RangeEdge.LOW,
                _JPY_SOURCE,
                _JPY_DT_QUOTE,
                declared_extension=True,
            ),
        ),
        source_ref=_JPY_SOURCE,
    ),
}


@dataclass(frozen=True)
class CoordinateProjection(Measurement):
    """One projected coordinate.

    The record carries the coordinate *level* and nothing else: no
    acceptance, no rekey, no promotion, no setup.  A coordinate that
    price touches means nothing on its own.
    """

    coordinate_id: str
    family_id: str
    level: Decimal
    base: RangeEdge
    orientation: CoordinateOrientation
    anchor_id: str
    model_id: str
    model_version: str
    reference_price: NativePrice
    range_size: NativeMagnitude
    projected_price: NativePrice
    family_source_ref: str

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def _canonical_level(family_id: str) -> Decimal | None:
    """The canonical level of a family id, or ``None`` when unknown.

    A family id carries its level as its trailing token (``EUR_DAILY_72``,
    ``XAU_61_8``).  Only the canonical bound levels resolve; anything
    else — including a model-declared extension — is not canonical.
    """
    tail = family_id.rsplit("_", 1)[-1]
    for level in CANONICAL_FAMILY_LEVELS:
        if str(level) == tail or str(level).replace(".", "_") == tail:
            return level
    return None


def project_coordinates(
    anchor: AnchorRecord,
    family_id: str,
    *,
    provenance: Provenance,
    definition_version: str = "V1",
) -> CoordinateProjection:
    """Project one declared family onto an anchor's earned range.

    Refusals (all explicit, none silent):

    * the anchor is not ``ELIGIBLE``/``ACTIVE`` -> ``ANCHOR_NOT_EARNED``;
    * the model/version declares no coordinate set -> ``MODEL_VERSION_UNAVAILABLE``;
    * the family is outside the canonical set -> ``UNKNOWN_COORDINATE_FAMILY``;
    * the family is canonical but not declared for this model ->
      ``COORDINATE_FAMILY_NOT_EARNED`` (the ladder does not auto-extend).
    """
    if anchor.status not in (AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE):
        raise AnchorNotEarnedError(
            f"anchor {anchor.anchor_id!r} is {anchor.status.value}; "
            "coordinates require an ELIGIBLE or ACTIVE anchor"
        )
    if anchor.earned_range is None:
        raise AnchorNotEarnedError(
            f"anchor {anchor.anchor_id!r} carries no earned range"
        )

    coordinate_set = COORDINATE_SETS.get((anchor.model_id, anchor.model_version))
    if coordinate_set is None:
        raise ModelVersionUnavailableError(
            f"no coordinate set declared for {anchor.model_id}/"
            f"{anchor.model_version}"
        )

    family = coordinate_set.family(family_id)
    if family is None:
        if _canonical_level(family_id) is None:
            raise UnknownCoordinateFamilyError(
                f"unknown coordinate family {family_id!r}"
            )
        raise CoordinateFamilyNotEarnedError(
            f"{family_id!r} is canonical but not declared by "
            f"{anchor.model_id}/{anchor.model_version}"
        )

    earned = anchor.earned_range
    low = earned.low.value
    high = earned.high.value
    span = high - low
    offset = span * family.level / Decimal(100)
    if family.base is RangeEdge.LOW:
        projected_value = low + offset
    else:
        projected_value = high - offset

    unit: NativeUnit = earned.native_unit or earned.low.unit
    reference = earned.low if family.base is RangeEdge.LOW else earned.high
    projected = NativePrice(earned.instrument_id, unit, projected_value)

    context = provenance.context(earned.source_window)
    return CoordinateProjection(
        **envelope(
            context,
            "COORDINATE_PROJECTION",
            definition_version=definition_version,
            native_unit=unit,
        ),
        coordinate_id=f"{anchor.anchor_id}:{family_id}",
        family_id=family.family_id,
        level=family.level,
        base=family.base,
        orientation=family.orientation,
        anchor_id=anchor.anchor_id,
        model_id=anchor.model_id,
        model_version=anchor.model_version,
        reference_price=reference,
        range_size=earned.size,
        projected_price=projected,
        family_source_ref=family.source_ref,
    )
