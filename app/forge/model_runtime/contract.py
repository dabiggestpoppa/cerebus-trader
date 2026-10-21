"""Common model runtime contract (Ch III.3 "Common model contract").

Frozen envelopes, bounded enums and shared evaluation helpers for every
Bloc III.3 family runtime.  The contract follows PLAN.md §7.2 exactly:

* ``ModelRequest`` — canonical model id + explicit version (no
  defaults), instrument scope, a family-typed bundle of III.2
  measurements, the previous model state where applicable, an injected
  calculation timestamp, the bound calibration key and the asserted
  identity versions (invariant #1: the data clock is part of model
  identity).
* ``ModelOutput`` — an immutable, versioned per-call model state with a
  declared layer, typed direction/levels/sub-states, range-left,
  bounded no-go and warning codes, read-only evidence/claim references,
  the frozen III.1 quality vocabulary, a production-authorization
  *classification* (structurally distinct from the descriptive state),
  structured ``ExplanationFact``s (never prose) and the canonical
  replay hash.

Structurally excluded from every output (no field can carry them):
probabilities, confidence or confluence scores, win rates,
expectancy/RR, predictions, signals, prose, and any
entry/trigger/invalidation/target object — those belong to III.5 and
the Book III exclusions.

Cross-cutting discipline: pure functions over frozen dataclasses,
``Decimal`` in asset-native units, injected calculation clocks (never
wall time), no network, no file I/O, no imports outside
``app.forge.market_data`` + ``app.forge.measurements`` + stdlib.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Mapping

from app.forge.market_data import DataOutcome
from app.forge.measurements import (
    AnchorRefusalCode,
    AnchorStatus,
    CalibrationKey,
    Measurement,
    NativeMagnitude,
    RemainingState,
    RuleMaterialization,
)

from .errors import ModelContractError
from .versions import MODEL_RUNTIME_VERSION

__all__ = [
    "AnchorStateRef",
    "DirectionBias",
    "DirectionSide",
    "ExplanationFact",
    "InputIdentity",
    "Layer",
    "LevelKind",
    "ModelOutput",
    "ModelRequest",
    "NoGoReason",
    "ProductionAuthorization",
    "RangeLeftField",
    "SubState",
    "TypedLevel",
    "WarningCode",
    "iter_measurements",
    "make_fact",
    "prior_ref",
    "resolve_quality",
]


# ---------------------------------------------------------------------------
# Bounded enums
# ---------------------------------------------------------------------------


class Layer(str, Enum):
    """Declared model layer of a state (PLAN.md §7.1 — exactly four)."""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    CROSS_LAYER = "CROSS_LAYER"


class ProductionAuthorization(str, Enum):
    """Classification fact, never an eligibility grant (invariants #12/#13).

    ``model_state`` (descriptive) and ``production_authorization``
    (classification) are structurally distinct fields; neither confers
    trade eligibility.
    """

    RESEARCH_ONLY = "RESEARCH_ONLY"
    MANUAL_OPERATOR = "MANUAL_OPERATOR"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class NoGoReason(str, Enum):
    """Bounded no-go reason codes (no free text anywhere)."""

    AR_SOURCE_NO_GO = "AR_SOURCE_NO_GO"
    ASIAN_RANGE_NO_GO = "ASIAN_RANGE_NO_GO"
    NATIVE_TIER_NO_GO = "NATIVE_TIER_NO_GO"
    RULE_NOT_MATERIALIZED = "RULE_NOT_MATERIALIZED"
    PROMOTION_PARKED = "PROMOTION_PARKED"


class WarningCode(str, Enum):
    """Bounded warning codes (no free text anywhere)."""

    RESEARCH_CALIBRATION = "RESEARCH_CALIBRATION"
    SMALL_N_RESEARCH_FLAG = "SMALL_N_RESEARCH_FLAG"
    EVIDENCE_BOUND_PARAMETER = "EVIDENCE_BOUND_PARAMETER"
    DEGRADED_INPUT = "DEGRADED_INPUT"
    GAP_UNRESOLVED = "GAP_UNRESOLVED"
    CONDITIONAL_DESTINATION = "CONDITIONAL_DESTINATION"
    TIMING_UNRESOLVED = "TIMING_UNRESOLVED"


class DirectionSide(str, Enum):
    """Typed side for a canonically declared direction/bias only."""

    UP = "UP"
    DOWN = "DOWN"


class LevelKind(str, Enum):
    """Typed level kinds — coordinates and thresholds, nothing else."""

    COORDINATE = "COORDINATE"
    THRESHOLD = "THRESHOLD"


# ---------------------------------------------------------------------------
# Structured facts (never prose)
# ---------------------------------------------------------------------------

_FACT_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_FACT_VALUE = re.compile(r"^[A-Za-z0-9_.:+/=\-,]*$")
_FACT_ID = re.compile(r"^[A-Z][A-Z0-9_.]*$")
_SOURCE_REF = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


@dataclass(frozen=True)
class ExplanationFact:
    """A structured, machine-checkable explanation fact.

    ``payload`` is an ordered tuple of ``(key, value)`` pairs whose key
    and value match bounded identifier/number patterns — spaces are
    impossible by construction, so a fact can never carry generated
    prose.  Every fact names the rule id, rule version and canonical
    source ref it derives from.
    """

    fact_id: str
    rule_id: str
    rule_version: str
    source_ref: str
    payload: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not _FACT_ID.match(self.fact_id):
            raise ModelContractError(
                f"fact_id must match [A-Z][A-Z0-9_.]*: {self.fact_id!r}"
            )
        if not _FACT_ID.match(self.rule_id):
            raise ModelContractError(
                f"rule_id must match [A-Z][A-Z0-9_.]*: {self.rule_id!r}"
            )
        if not self.rule_version:
            raise ModelContractError("an explanation fact requires a rule version")
        if not _SOURCE_REF.match(self.source_ref):
            raise ModelContractError(
                f"source_ref must be a bounded identifier: {self.source_ref!r}"
            )
        for item in self.payload:
            if not (isinstance(item, tuple) and len(item) == 2):
                raise ModelContractError("fact payload items are (key, value) pairs")
            key, value = item
            if not _FACT_KEY.match(key):
                raise ModelContractError(f"fact payload key invalid: {key!r}")
            if not isinstance(value, str) or not _FACT_VALUE.match(value):
                raise ModelContractError(
                    f"fact payload value must be a bounded identifier/number: "
                    f"{value!r}"
                )


def make_fact(
    fact_id: str,
    rule_id: str,
    source_ref: str,
    payload: Mapping[str, Any] | Iterable[tuple[str, Any]] = (),
    *,
    rule_version: str = "V1",
) -> ExplanationFact:
    """Build an :class:`ExplanationFact` with stringified typed payload."""

    items = payload.items() if isinstance(payload, Mapping) else payload
    encoded: list[tuple[str, str]] = []
    for key, value in items:
        if isinstance(value, bool):
            text = "YES" if value else "NO"
        elif isinstance(value, Enum):
            text = str(value.value)
        elif isinstance(value, Decimal):
            text = str(value)
        else:
            text = str(value)
        encoded.append((str(key), text))
    return ExplanationFact(
        fact_id=fact_id,
        rule_id=rule_id,
        rule_version=rule_version,
        source_ref=source_ref,
        payload=tuple(encoded),
    )


# ---------------------------------------------------------------------------
# Typed output structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DirectionBias:
    """Typed side + basis fact, or the explicit ``NONE_DECLARED`` form.

    Only canonically direction-bearing models populate ``side``; every
    other family (EUR Daily is not a direction oracle) constructs the
    explicit undeclared form via :meth:`none`.
    """

    side: DirectionSide | None
    basis_fact_id: str | None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.side is None:
            if self.basis_fact_id is not None or self.evidence_refs:
                raise ModelContractError(
                    "an undeclared direction carries no basis fact or evidence"
                )
        else:
            if not isinstance(self.side, DirectionSide):
                raise ModelContractError(f"unknown direction side {self.side!r}")
            if not self.basis_fact_id:
                raise ModelContractError("a declared direction requires a basis fact")

    @classmethod
    def none(cls) -> "DirectionBias":
        """The explicit ``NONE_DECLARED`` form."""
        return cls(side=None, basis_fact_id=None, evidence_refs=())

    @property
    def declared(self) -> bool:
        return self.side is not None

    def to_payload(self) -> Any:
        if self.side is None:
            return "NONE_DECLARED"
        return {
            "side": self.side.value,
            "basis_fact_id": self.basis_fact_id,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class TypedLevel:
    """A typed level/coordinate with its canonical source reference.

    Projection authority stays in III.2: this object only *references*
    an already-projected price (or a declared native threshold
    magnitude) with its source.
    """

    level_id: str
    level_kind: LevelKind
    family: str
    level: Decimal | None
    price: Decimal | None
    active: bool
    source_ref: str

    def __post_init__(self) -> None:
        if not self.level_id or not isinstance(self.level_kind, LevelKind):
            raise ModelContractError("a typed level requires an id and a bounded kind")
        if self.level is None and self.price is None:
            raise ModelContractError("a typed level carries level and/or price")
        if self.price is not None and not isinstance(self.price, Decimal):
            raise ModelContractError("level prices are Decimal, never float")
        if not _SOURCE_REF.match(self.source_ref):
            raise ModelContractError(
                f"level source_ref must be a bounded identifier: {self.source_ref!r}"
            )


@dataclass(frozen=True)
class AnchorStateRef:
    """Reference to a III.2 anchor eligibility, status verbatim."""

    anchor_id: str
    status: AnchorStatus
    refusal_code: AnchorRefusalCode

    def __post_init__(self) -> None:
        if not isinstance(self.status, AnchorStatus):
            raise ModelContractError("anchor status uses the frozen III.2 vocabulary")
        if not isinstance(self.refusal_code, AnchorRefusalCode):
            raise ModelContractError("anchor refusal uses the frozen III.2 vocabulary")


@dataclass(frozen=True)
class RangeLeftField:
    """Range-left / remaining distribution, conditioned on consumed states.

    Invariant #10: the field names the consumed-state fact ids it is
    conditioned on; without a source-supported remaining measurement the
    state is the explicit III.2 ``UNRESOLVED`` vocabulary — never a
    fabricated value.
    """

    state: RemainingState
    value: NativeMagnitude | None
    basis_fact_id: str | None
    conditioned_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.state, RemainingState):
            raise ModelContractError("range-left uses the frozen III.2 vocabulary")
        if self.state is RemainingState.UNRESOLVED and self.value is not None:
            raise ModelContractError("an unresolved range-left carries no value")
        if self.state is RemainingState.MEASURED and self.value is None:
            raise ModelContractError("a measured range-left requires its value")

    @classmethod
    def unresolved(
        cls, *, basis_fact_id: str | None = None, conditioned_on: tuple[str, ...] = ()
    ) -> "RangeLeftField":
        return cls(
            state=RemainingState.UNRESOLVED,
            value=None,
            basis_fact_id=basis_fact_id,
            conditioned_on=tuple(conditioned_on),
        )


@dataclass(frozen=True)
class SubState:
    """A per-layer or per-role sub-state (XAU L3/L2/L1, JPY roles, BTC clocks).

    Sub-states are separate entries — layer or role ownership is typed
    on the entry, so a lower-layer input can never populate a
    higher-layer field and a basket role can never be merged into an
    aggregate (invariant #11; equal-vote aggregation is impossible by
    construction because no aggregate field exists).
    """

    label: str
    layer: Layer
    state: str
    fact_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not isinstance(self.layer, Layer):
            raise ModelContractError("a sub-state requires a label and a bounded layer")
        if not self.state or not re.match(r"^[A-Z][A-Z0-9_.]*$", self.state):
            raise ModelContractError(
                f"sub-state values are bounded identifiers: {self.state!r}"
            )


# ---------------------------------------------------------------------------
# Request / identity
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InputIdentity:
    """The asserted input-identity envelope echoed on every output.

    Invariant #1: market-data/clock/session/measurement versions, the
    clock and session ids, the injected calculation timestamp, the
    calibration lineage, the instrument and the prior-state reference
    are all part of model identity and therefore of the replay hash.
    """

    instrument_id: str
    calibration_key: CalibrationKey | None
    clock_id: str | None
    session_id: str | None
    calculation_timestamp: datetime
    market_data_schema_version: str
    clock_registry_version: str
    session_registry_version: str
    measurement_engine_version: str
    model_runtime_version: str
    prior_state_ref: str | None

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise ModelContractError("input identity requires an instrument id")
        for name in (
            "market_data_schema_version",
            "clock_registry_version",
            "session_registry_version",
            "measurement_engine_version",
            "model_runtime_version",
        ):
            if not getattr(self, name):
                raise ModelContractError(f"input identity requires {name}")
        if self.calibration_key is not None and not isinstance(
            self.calibration_key, CalibrationKey
        ):
            raise ModelContractError("calibration_key is a III.2 CalibrationKey")


@dataclass(frozen=True)
class ModelRequest:
    """The frozen request envelope (PLAN.md §7.2 inputs).

    ``model_id`` and ``model_version`` are both required with no
    default anywhere (III.3.8).  ``calculation_timestamp`` is injected,
    never wall time.  Identity versions are asserted, not inferred.
    """

    model_id: str
    model_version: str
    instrument_id: str
    inputs: Any
    calculation_timestamp: datetime
    calibration_key: CalibrationKey | None
    market_data_schema_version: str
    clock_registry_version: str
    session_registry_version: str
    measurement_engine_version: str
    prior_state: "ModelOutput | None" = None
    clock_id: str | None = None
    session_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("model_id", "model_version", "instrument_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ModelContractError(f"request requires a non-empty {name}")
        if not isinstance(self.calculation_timestamp, datetime):
            raise ModelContractError("calculation_timestamp must be a datetime")
        if self.calculation_timestamp.tzinfo is None:
            raise ModelContractError(
                "calculation_timestamp must be timezone-aware (injected clock)"
            )
        if not is_dataclass(self.inputs) or isinstance(self.inputs, type):
            raise ModelContractError("request inputs are a family-typed dataclass")
        if not self.inputs.__dataclass_params__.frozen:
            raise ModelContractError("request inputs must be immutable")
        for name in (
            "market_data_schema_version",
            "clock_registry_version",
            "session_registry_version",
            "measurement_engine_version",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ModelContractError(f"request asserts a non-empty {name}")
        if self.prior_state is not None and not isinstance(self.prior_state, ModelOutput):
            raise ModelContractError("prior_state is a ModelOutput or None")
        for name in ("clock_id", "session_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ModelContractError(f"{name} is a non-empty string or None")

    def identity(self, prior_state_ref: str | None = None) -> InputIdentity:
        """Build the echoed identity envelope for the output."""
        return InputIdentity(
            instrument_id=self.instrument_id,
            calibration_key=self.calibration_key,
            clock_id=self.clock_id,
            session_id=self.session_id,
            calculation_timestamp=self.calculation_timestamp,
            market_data_schema_version=self.market_data_schema_version,
            clock_registry_version=self.clock_registry_version,
            session_registry_version=self.session_registry_version,
            measurement_engine_version=self.measurement_engine_version,
            model_runtime_version=MODEL_RUNTIME_VERSION,
            prior_state_ref=prior_state_ref,
        )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelOutput:
    """The immutable, versioned model output (PLAN.md §7.2 outputs).

    ``output_hash`` is the canonical replay hash over the full payload
    plus the identity envelope; it is stamped by
    ``app.forge.model_runtime.replay.finalize_output``.
    """

    model_id: str
    model_version: str
    model_runtime_version: str
    output_hash: str
    model_state: str
    layer: Layer
    direction_bias: DirectionBias
    active_ranges: tuple[str, ...]
    active_anchor_states: tuple[AnchorStateRef, ...]
    levels: tuple[TypedLevel, ...]
    range_left: RangeLeftField
    no_go: tuple[NoGoReason, ...]
    warnings: tuple[WarningCode, ...]
    claim_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    quality_state: DataOutcome
    production_authorization: ProductionAuthorization
    explanation_facts: tuple[ExplanationFact, ...]
    sub_states: tuple[SubState, ...]
    identity: InputIdentity

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_version:
            raise ModelContractError("an output carries its model key")
        if self.model_runtime_version != MODEL_RUNTIME_VERSION:
            raise ModelContractError(
                f"outputs are stamped by {MODEL_RUNTIME_VERSION}, got "
                f"{self.model_runtime_version!r}"
            )
        if self.output_hash and not re.match(r"^[0-9a-f]{64}$", self.output_hash):
            raise ModelContractError("output_hash is a sha256 hex digest")
        if not self.model_state or not isinstance(self.layer, Layer):
            raise ModelContractError("an output carries a bounded state and a layer")
        if not isinstance(self.direction_bias, DirectionBias):
            raise ModelContractError("direction_bias is typed")
        if not isinstance(self.range_left, RangeLeftField):
            raise ModelContractError("range_left is typed")
        if not isinstance(self.quality_state, DataOutcome):
            raise ModelContractError("quality_state uses the frozen III.1 vocabulary")
        if not isinstance(self.production_authorization, ProductionAuthorization):
            raise ModelContractError("production_authorization is a bounded classification")
        for reason in self.no_go:
            if not isinstance(reason, NoGoReason):
                raise ModelContractError("no_go carries bounded reason codes only")
        for warning in self.warnings:
            if not isinstance(warning, WarningCode):
                raise ModelContractError("warnings carry bounded codes only")
        if self.claim_refs:
            raise ModelContractError(
                "the runtime never creates or references claims (claim_refs empty)"
            )
        for ref in self.evidence_refs:
            if not isinstance(ref, str) or not _SOURCE_REF.match(ref):
                raise ModelContractError(
                    f"evidence refs are canonical ids: {ref!r}"
                )
        if not isinstance(self.identity, InputIdentity):
            raise ModelContractError("an output echoes its input identity")

    # -- derived helpers ---------------------------------------------------

    @property
    def fact_ids(self) -> tuple[str, ...]:
        return tuple(fact.fact_id for fact in self.explanation_facts)

    @property
    def fact_by_id(self) -> Mapping[str, ExplanationFact]:
        return {fact.fact_id: fact for fact in self.explanation_facts}


# ---------------------------------------------------------------------------
# Shared evaluation helpers (used by every family evaluator)
# ---------------------------------------------------------------------------


def iter_measurements(inputs: Any) -> list[Measurement]:
    """Collect every III.2 measurement reachable from a inputs bundle.

    Walks dataclass fields recursively (tuples/lists included), stopping
    at measurement leaves.  Used for quality gates, instrument-scope
    checks, calibration-binding checks and identity-version coherence —
    one implementation, applied uniformly to all seven families.
    """

    found: list[Measurement] = []

    def visit(value: Any) -> None:
        if isinstance(value, Measurement):
            found.append(value)
            return
        if is_dataclass(value) and not isinstance(value, type):
            for item in fields(value):
                visit(getattr(value, item.name))
            return
        if isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    visit(inputs)
    return found


def prior_ref(request: "ModelRequest") -> str | None:
    """The prior-state reference that enters the output identity (J2).

    A supplied prior state must itself be finalized: an unfinalized
    prior is a contract violation, never a silent ``None``.
    """

    prior = request.prior_state
    if prior is None:
        return None
    if not prior.output_hash:
        raise ModelContractError(
            "a prior state must carry its finalized output hash"
        )
    return prior.output_hash


def resolve_quality(measurements: Iterable[Measurement]) -> DataOutcome:
    """Aggregate input quality into one frozen III.1 outcome.

    Blocking and uncalculable states raise at the gate (they never
    become an output); this helper therefore only distinguishes
    ``DEGRADED`` from ``OK`` for outputs that are allowed to exist.
    """

    outcome = DataOutcome.OK
    for measurement in measurements:
        state = measurement.quality_state
        if state is DataOutcome.DEGRADED:
            outcome = DataOutcome.DEGRADED
    return outcome


def evidence_union(measurements: Iterable[Measurement]) -> tuple[str, ...]:
    """Ordered, de-duplicated union of read-only evidence ids."""

    seen: list[str] = []
    for measurement in measurements:
        for ref in measurement.evidence_refs:
            if ref not in seen:
                seen.append(ref)
    return tuple(seen)
