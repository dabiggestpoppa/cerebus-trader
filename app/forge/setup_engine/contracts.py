"""Immutable setup contract (Ch III.5 "Common setup contract").

The record is the frozen field set of PLAN.md §7.2: identity and version,
execution class and exposure verbatim, the four-way eligibility verdict
with bounded reasons, a typed side and location, one declared trigger
requirement, three **separate** invalidations, ordered targets with
promotion conditions, no-go/transition/evidence references, parent model
states, the manual-status projection, the automation flag, ordered
explanation facts and a deterministic evaluation hash.

Structurally absent, therefore impossible to emit: probability,
confidence, confluence, win rate, expectancy, risk/reward, position size
or order intent.

Discipline: ``Decimal`` only, bounded identifiers only, injected
evaluation time, no wall clock, no I/O.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable

from app.forge.canonical import EvidenceStatus, ProductExposure, SetupClass
from app.forge.measurements.anchors import AnchorEligibility
from app.forge.model_runtime.contract import (
    DirectionBias,
    ExplanationFact,
    Layer,
    ModelOutput,
    NoGoReason,
    TypedLevel,
)
from app.forge.state_engine.stand_down import StandDownRecord

from .errors import SetupContractError, SetupRefusalCode
from .versions import SETUP_CONTRACT_VERSION, SETUP_ENGINE_VERSION, SETUP_ID_PATTERN

__all__ = [
    "EvidenceReference",
    "InvalidationKind",
    "ParameterBinding",
    "ParameterMaterialization",
    "ParentStateRef",
    "PriceInvalidation",
    "PromotionCondition",
    "SEVERITY_ORDER",
    "SETUP_RECORD_FIELDS",
    "SetupEligibility",
    "SetupRecord",
    "SetupSurface",
    "SetupTarget",
    "StructuralInvalidation",
    "TemporalInvalidation",
    "TransitionRef",
    "TriggerCombination",
    "TriggerLiteral",
    "TriggerRequirement",
    "TriggerType",
    "payload_hash",
    "worst_verdict",
]

_IDENT = re.compile(r"^[A-Za-z0-9_.:+/=#\-]+$")
_SETUP_ID = re.compile(SETUP_ID_PATTERN)
_STATE = re.compile(r"^[A-Z][A-Z0-9_.]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _ident(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _IDENT.match(value):
        raise SetupContractError(f"{name} must be a bounded identifier: {value!r}")
    return value


def _decimal(value: Any, name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise SetupContractError(f"{name} must be Decimal (never float): {value!r}")
    return value


def _dec_text(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _dec(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def payload_hash(payload: dict[str, Any]) -> str:
    """Deterministic sha256 over a canonical JSON encoding (LF, no spaces)."""

    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Bounded vocabularies
# ---------------------------------------------------------------------------


class SetupEligibility(str, Enum):
    """The exact four-valued setup eligibility vocabulary (A6)."""

    ELIGIBLE = "ELIGIBLE"
    WATCH = "WATCH"
    BLOCKED = "BLOCKED"
    UNRESOLVED = "UNRESOLVED"

    @property
    def severity(self) -> int:
        return _SEVERITY[self]


_SEVERITY: dict[SetupEligibility, int] = {
    SetupEligibility.ELIGIBLE: 0,
    SetupEligibility.WATCH: 1,
    SetupEligibility.UNRESOLVED: 2,
    SetupEligibility.BLOCKED: 3,
}

#: Total precedence: BLOCKED > UNRESOLVED > WATCH > ELIGIBLE (C1).
SEVERITY_ORDER: tuple[SetupEligibility, ...] = (
    SetupEligibility.BLOCKED,
    SetupEligibility.UNRESOLVED,
    SetupEligibility.WATCH,
    SetupEligibility.ELIGIBLE,
)


def worst_verdict(verdicts: Iterable[SetupEligibility]) -> SetupEligibility:
    """The most severe verdict in a set — the only aggregation rule."""

    values = tuple(verdicts)
    if not values:
        return SetupEligibility.ELIGIBLE
    return max(values, key=lambda verdict: verdict.severity)


class SetupSurface(str, Enum):
    """The surface a setup evaluation was requested for."""

    PRODUCTION = "PRODUCTION"
    OPERATOR = "OPERATOR"
    RESEARCH = "RESEARCH"
    AUTOMATION = "AUTOMATION"


class ParameterMaterialization(str, Enum):
    """How far a numeric parameter is materialized (gate 9)."""

    CANONICAL = "CANONICAL"
    DECLARED = "DECLARED"
    ABSENT = "ABSENT"


class InvalidationKind(str, Enum):
    """The three independent invalidation kinds (E1)."""

    PRICE = "PRICE"
    STRUCTURAL = "STRUCTURAL"
    TEMPORAL = "TEMPORAL"


class TriggerType(str, Enum):
    """The exact seven-type trigger vocabulary (D1)."""

    TOUCH = "TOUCH"
    EXCURSION = "EXCURSION"
    REJECTION = "REJECTION"
    ACCEPTANCE = "ACCEPTANCE"
    CLOSE = "CLOSE"
    SR_FLIP = "SR_FLIP"
    OCC = "OCC"


class TriggerCombination(str, Enum):
    """How a declared trigger requirement combines its literals."""

    ALL = "ALL"
    ANY = "ANY"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParameterBinding:
    """One numeric parameter the card requires, with its materialization."""

    name: str
    materialization: ParameterMaterialization
    value: Decimal | None = None
    source_ref: str = ""

    def __post_init__(self) -> None:
        _ident(self.name, "parameter name")
        if not isinstance(self.materialization, ParameterMaterialization):
            raise SetupContractError(
                "parameter materialization uses the frozen vocabulary"
            )
        if self.value is not None:
            _decimal(self.value, "parameter value")
        if self.materialization is ParameterMaterialization.ABSENT:
            if self.value is not None:
                raise SetupContractError("an absent parameter carries no value")
        else:
            _ident(self.source_ref, "parameter source_ref")

    def to_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "materialization": self.materialization.value,
            "value": _dec_text(self.value),
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class EvidenceReference:
    """An ``EV.*``/``CL.*`` reference with its status — never a bare number."""

    evidence_id: str
    status: EvidenceStatus
    claim_id: str | None = None
    population_key: str | None = None
    relationship: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.startswith("EV."):
            raise SetupContractError(
                f"an evidence reference is an EV.* id: {self.evidence_id!r}"
            )
        if self.claim_id is not None and (
            not isinstance(self.claim_id, str) or not self.claim_id.startswith("CL.")
        ):
            raise SetupContractError(f"a claim reference is a CL.* id: {self.claim_id!r}")
        if not isinstance(self.status, EvidenceStatus):
            raise SetupContractError(
                "an evidence reference carries the frozen EvidenceStatus"
            )
        if self.population_key is not None:
            _ident(self.population_key, "population_key")

    def to_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "status": self.status.value,
            "claim_id": self.claim_id,
            "population_key": self.population_key,
            "relationship": self.relationship,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EvidenceReference":
        return cls(
            evidence_id=payload["evidence_id"],
            status=EvidenceStatus(payload["status"]),
            claim_id=payload.get("claim_id"),
            population_key=payload.get("population_key"),
            relationship=bool(payload.get("relationship", False)),
        )


@dataclass(frozen=True)
class ParentStateRef:
    """A parent model's identity and state, carried verbatim (A13)."""

    model_id: str
    model_version: str
    model_state: str
    layer: Layer
    output_hash: str = ""
    snapshot_ref: str = ""

    def __post_init__(self) -> None:
        _ident(self.model_id, "parent model_id")
        _ident(self.model_version, "parent model_version")
        if not isinstance(self.model_state, str) or not _STATE.match(self.model_state):
            raise SetupContractError(f"model_state is bounded: {self.model_state!r}")
        if not isinstance(self.layer, Layer):
            raise SetupContractError("a parent state carries a bounded layer")
        if self.output_hash and not _SHA256.match(self.output_hash):
            raise SetupContractError("output_hash is a sha256 hex digest")

    def to_payload(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "model_state": self.model_state,
            "layer": self.layer.value,
            "output_hash": self.output_hash,
            "snapshot_ref": self.snapshot_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ParentStateRef":
        return cls(
            model_id=payload["model_id"],
            model_version=payload["model_version"],
            model_state=payload["model_state"],
            layer=Layer(payload["layer"]),
            output_hash=payload.get("output_hash", ""),
            snapshot_ref=payload.get("snapshot_ref", ""),
        )


@dataclass(frozen=True)
class TransitionRef:
    """A III.4 transition/observation reference, carried verbatim."""

    transition_id: str
    from_state: str
    to_state: str
    event_ref: str

    def __post_init__(self) -> None:
        _ident(self.transition_id, "transition_id")
        _ident(self.event_ref, "event_ref")
        for name in ("from_state", "to_state"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _STATE.match(value):
                raise SetupContractError(f"{name} is a bounded state: {value!r}")

    def to_payload(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "event_ref": self.event_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TransitionRef":
        return cls(
            transition_id=payload["transition_id"],
            from_state=payload["from_state"],
            to_state=payload["to_state"],
            event_ref=payload["event_ref"],
        )


@dataclass(frozen=True)
class PromotionCondition:
    """What promotes a target, and who authorized that condition."""

    condition_id: str
    required_transition: str
    source_ref: str
    authority_ref: str

    def __post_init__(self) -> None:
        _ident(self.condition_id, "promotion condition_id")
        _ident(self.required_transition, "required_transition")
        _ident(self.source_ref, "promotion source_ref")
        _ident(self.authority_ref, "promotion authority_ref")

    def to_payload(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "required_transition": self.required_transition,
            "source_ref": self.source_ref,
            "authority_ref": self.authority_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PromotionCondition":
        return cls(
            condition_id=payload["condition_id"],
            required_transition=payload["required_transition"],
            source_ref=payload["source_ref"],
            authority_ref=payload["authority_ref"],
        )


@dataclass(frozen=True)
class SetupTarget:
    """One declared target, in canonical order, with its promotion rule."""

    target_id: str
    declared_order_index: int
    source_ref: str
    coordinate: Decimal | None = None
    confirmation_only: bool = False
    promotion: PromotionCondition | None = None
    active: bool = False
    transition_ref: str | None = None
    range_left_conditioned_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _ident(self.target_id, "target_id")
        if not isinstance(self.declared_order_index, int) or self.declared_order_index < 0:
            raise SetupContractError("declared_order_index must be a non-negative int")
        _ident(self.source_ref, "target source_ref")
        if self.coordinate is not None:
            _decimal(self.coordinate, "target coordinate")
        if self.promotion is not None and not isinstance(
            self.promotion, PromotionCondition
        ):
            raise SetupContractError("a target promotion is a PromotionCondition")
        if self.active and self.promotion is None:
            raise SetupContractError("an active target requires a declared promotion")
        if self.active and not self.transition_ref:
            raise SetupContractError("an active target requires its transition ref")
        if self.confirmation_only and self.active:
            raise SetupContractError(
                "a confirmation/evidence state is never an active core target"
            )
        for item in self.range_left_conditioned_on:
            _ident(item, "range_left condition")

    def to_payload(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "declared_order_index": self.declared_order_index,
            "source_ref": self.source_ref,
            "coordinate": _dec_text(self.coordinate),
            "confirmation_only": self.confirmation_only,
            "promotion": None if self.promotion is None else self.promotion.to_payload(),
            "active": self.active,
            "transition_ref": self.transition_ref,
            "range_left_conditioned_on": list(self.range_left_conditioned_on),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SetupTarget":
        promotion = payload.get("promotion")
        return cls(
            target_id=payload["target_id"],
            declared_order_index=int(payload["declared_order_index"]),
            source_ref=payload["source_ref"],
            coordinate=_dec(payload.get("coordinate")),
            confirmation_only=bool(payload.get("confirmation_only", False)),
            promotion=(
                None if promotion is None else PromotionCondition.from_payload(promotion)
            ),
            active=bool(payload.get("active", False)),
            transition_ref=payload.get("transition_ref"),
            range_left_conditioned_on=tuple(payload.get("range_left_conditioned_on", ())),
        )


@dataclass(frozen=True)
class TriggerLiteral:
    """One declared trigger alternative/gate, with optional tolerance."""

    trigger_type: TriggerType
    tolerance: Decimal | None = None
    bar_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.trigger_type, TriggerType):
            raise SetupContractError("a trigger literal uses the frozen vocabulary")
        if self.tolerance is not None:
            _decimal(self.tolerance, "trigger tolerance")

    def to_payload(self) -> dict[str, Any]:
        return {
            "trigger_type": self.trigger_type.value,
            "tolerance": _dec_text(self.tolerance),
            "bar_ref": self.bar_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TriggerLiteral":
        return cls(
            trigger_type=TriggerType(payload["trigger_type"]),
            tolerance=_dec(payload.get("tolerance")),
            bar_ref=payload.get("bar_ref"),
        )


@dataclass(frozen=True)
class TriggerRequirement:
    """The card's declared requirement: all of ``literals``, plus one of ``any_of``."""

    source_ref: str
    literals: tuple[TriggerLiteral, ...] = ()
    any_of: tuple[TriggerLiteral, ...] = ()
    combination: TriggerCombination = TriggerCombination.ALL

    def __post_init__(self) -> None:
        _ident(self.source_ref, "trigger requirement source_ref")
        if not isinstance(self.combination, TriggerCombination):
            raise SetupContractError("a trigger combination uses the frozen vocabulary")
        if not self.literals and not self.any_of:
            raise SetupContractError("a trigger requirement declares at least one literal")
        for literal in self.literals + self.any_of:
            if not isinstance(literal, TriggerLiteral):
                raise SetupContractError("trigger literals are typed")

    @property
    def declared_types(self) -> tuple[TriggerType, ...]:
        return tuple(
            literal.trigger_type for literal in self.literals + self.any_of
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "literals": [literal.to_payload() for literal in self.literals],
            "any_of": [literal.to_payload() for literal in self.any_of],
            "combination": self.combination.value,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TriggerRequirement":
        return cls(
            source_ref=payload["source_ref"],
            literals=tuple(
                TriggerLiteral.from_payload(item) for item in payload.get("literals", ())
            ),
            any_of=tuple(
                TriggerLiteral.from_payload(item) for item in payload.get("any_of", ())
            ),
            combination=TriggerCombination(payload.get("combination", "ALL")),
        )


@dataclass(frozen=True)
class PriceInvalidation:
    """A typed price/native-magnitude invalidation with its source."""

    value: Decimal
    magnitude_unit: str
    materialization: ParameterMaterialization
    source_ref: str
    active: bool = False

    def __post_init__(self) -> None:
        _decimal(self.value, "price invalidation value")
        _ident(self.magnitude_unit, "magnitude_unit")
        _ident(self.source_ref, "invalidation source_ref")
        if not isinstance(self.materialization, ParameterMaterialization):
            raise SetupContractError(
                "invalidation materialization uses the frozen vocabulary"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "value": _dec_text(self.value),
            "magnitude_unit": self.magnitude_unit,
            "materialization": self.materialization.value,
            "source_ref": self.source_ref,
            "active": self.active,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PriceInvalidation":
        return cls(
            value=Decimal(str(payload["value"])),
            magnitude_unit=payload["magnitude_unit"],
            materialization=ParameterMaterialization(payload["materialization"]),
            source_ref=payload["source_ref"],
            active=bool(payload.get("active", False)),
        )


@dataclass(frozen=True)
class StructuralInvalidation:
    """The model/state condition that voids the setup — typed, not prose."""

    condition_id: str
    state_ref: str
    source_ref: str
    active: bool = False

    def __post_init__(self) -> None:
        _ident(self.condition_id, "structural condition_id")
        _ident(self.state_ref, "structural state_ref")
        _ident(self.source_ref, "structural source_ref")

    def to_payload(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "state_ref": self.state_ref,
            "source_ref": self.source_ref,
            "active": self.active,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StructuralInvalidation":
        return cls(
            condition_id=payload["condition_id"],
            state_ref=payload["state_ref"],
            source_ref=payload["source_ref"],
            active=bool(payload.get("active", False)),
        )


@dataclass(frozen=True)
class TemporalInvalidation:
    """A session/checkpoint/expiry bound — never a price level."""

    bound_id: str
    checkpoint: str
    source_ref: str
    active: bool = False

    def __post_init__(self) -> None:
        _ident(self.bound_id, "temporal bound_id")
        _ident(self.checkpoint, "temporal checkpoint")
        _ident(self.source_ref, "temporal source_ref")

    def to_payload(self) -> dict[str, Any]:
        return {
            "bound_id": self.bound_id,
            "checkpoint": self.checkpoint,
            "source_ref": self.source_ref,
            "active": self.active,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TemporalInvalidation":
        return cls(
            bound_id=payload["bound_id"],
            checkpoint=payload["checkpoint"],
            source_ref=payload["source_ref"],
            active=bool(payload.get("active", False)),
        )


# ---------------------------------------------------------------------------
# The frozen record
# ---------------------------------------------------------------------------

#: The exact frozen field set (A4), in canonical order.
SETUP_RECORD_FIELDS: tuple[str, ...] = (
    "setup_id",
    "setup_version",
    "setup_contract_version",
    "engine_version",
    "source_card_ref",
    "execution_class",
    "product_exposure",
    "eligibility",
    "eligibility_reasons",
    "side",
    "location",
    "trigger_requirement",
    "invalidation_price",
    "invalidation_structural",
    "invalidation_temporal",
    "targets",
    "promotion_conditions",
    "no_go_refs",
    "parent_states",
    "transition_refs",
    "evidence_refs",
    "manual_status",
    "automation_permitted",
    "explanation_facts",
    "evaluation_time",
)

_CLASS_RANK: dict[SetupClass, int] = {
    SetupClass.RESEARCH_ONLY: 0,
    SetupClass.MANUAL_OPERATOR: 1,
    SetupClass.AUTOMATION_APPROVED: 2,
}


@dataclass(frozen=True)
class SetupRecord:
    """An immutable, version-stamped setup evaluation record."""

    setup_id: str
    setup_version: str
    source_card_ref: str
    execution_class: SetupClass
    product_exposure: ProductExposure
    eligibility: SetupEligibility
    side: DirectionBias
    trigger_requirement: TriggerRequirement
    parent_states: tuple[ParentStateRef, ...] = ()
    eligibility_reasons: tuple[SetupRefusalCode, ...] = ()
    location: TypedLevel | None = None
    invalidation_price: PriceInvalidation | None = None
    invalidation_structural: StructuralInvalidation | None = None
    invalidation_temporal: TemporalInvalidation | None = None
    targets: tuple[SetupTarget, ...] = ()
    promotion_conditions: tuple[PromotionCondition, ...] = ()
    no_go_refs: tuple[NoGoReason, ...] = ()
    transition_refs: tuple[TransitionRef, ...] = ()
    evidence_refs: tuple[EvidenceReference, ...] = ()
    manual_status: SetupClass | None = None
    automation_permitted: bool = False
    explanation_facts: tuple[ExplanationFact, ...] = ()
    evaluation_time: str = "1970-01-01T00:00:00Z"
    setup_contract_version: str = SETUP_CONTRACT_VERSION
    engine_version: str = SETUP_ENGINE_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.setup_id, str) or not _SETUP_ID.match(self.setup_id):
            raise SetupContractError(
                "a setup record requires a canonical corpus setup identity: "
                f"{self.setup_id!r}"
            )
        _ident(self.setup_version, "setup_version")
        _ident(self.source_card_ref, "source_card_ref")
        _ident(self.evaluation_time, "evaluation_time")
        if self.setup_contract_version != SETUP_CONTRACT_VERSION:
            raise SetupContractError("unknown setup contract version — fail closed")
        if self.engine_version != SETUP_ENGINE_VERSION:
            raise SetupContractError("unknown setup engine version — fail closed")
        if not isinstance(self.execution_class, SetupClass):
            raise SetupContractError("execution_class is the Book I vocabulary")
        if not isinstance(self.product_exposure, ProductExposure):
            raise SetupContractError("product_exposure is the Book I vocabulary")
        if not isinstance(self.eligibility, SetupEligibility):
            raise SetupContractError("eligibility is the frozen four-way vocabulary")
        if not isinstance(self.side, DirectionBias):
            raise SetupContractError(
                "side is a typed DirectionBias (or its explicit NONE_DECLARED form)"
            )
        if self.location is not None and not isinstance(self.location, TypedLevel):
            raise SetupContractError(
                "location is a typed level/zone reference or an explicit UNRESOLVED"
            )
        if not isinstance(self.trigger_requirement, TriggerRequirement):
            raise SetupContractError("trigger_requirement is a declared requirement")
        for reason in self.eligibility_reasons:
            if not isinstance(reason, SetupRefusalCode):
                raise SetupContractError(
                    "eligibility reasons are bounded refusal codes, never prose"
                )
        if (
            self.eligibility is not SetupEligibility.ELIGIBLE
            and not self.eligibility_reasons
        ):
            raise SetupContractError(
                "a non-ELIGIBLE record carries at least one bounded reason"
            )
        if self.eligibility is SetupEligibility.ELIGIBLE and self.eligibility_reasons:
            raise SetupContractError(
                "an ELIGIBLE record carries no refusal reason"
            )
        projected = (
            self.execution_class if self.manual_status is None else self.manual_status
        )
        if not isinstance(projected, SetupClass):
            raise SetupContractError("manual_status is the Book I class vocabulary")
        if _CLASS_RANK[projected] > _CLASS_RANK[self.execution_class]:
            raise SetupContractError(
                "manual_status can never exceed the card execution class"
            )
        if self.automation_permitted:
            if self.execution_class is not SetupClass.AUTOMATION_APPROVED:
                raise SetupContractError(
                    "automation is never permitted for a non-approved card"
                )
        for target in self.targets:
            if not isinstance(target, SetupTarget):
                raise SetupContractError("targets are typed SetupTarget values")
        for condition in self.promotion_conditions:
            if not isinstance(condition, PromotionCondition):
                raise SetupContractError("promotion conditions are typed")
        for ref in self.no_go_refs:
            if not isinstance(ref, NoGoReason):
                raise SetupContractError("no-go refs use the frozen III.3 codes")
        for state in self.parent_states:
            if not isinstance(state, ParentStateRef):
                raise SetupContractError("parent states are typed references")
        for transition in self.transition_refs:
            if not isinstance(transition, TransitionRef):
                raise SetupContractError("transition refs are typed references")
        for evidence in self.evidence_refs:
            if not isinstance(evidence, EvidenceReference):
                raise SetupContractError("evidence refs carry their status")
        for fact in self.explanation_facts:
            if not isinstance(fact, ExplanationFact):
                raise SetupContractError(
                    "explanation facts are structured III.3 facts, never prose"
                )
        if self.invalidation_price is not None and not isinstance(
            self.invalidation_price, PriceInvalidation
        ):
            raise SetupContractError("the price invalidation field is price-typed")
        if self.invalidation_structural is not None and not isinstance(
            self.invalidation_structural, StructuralInvalidation
        ):
            raise SetupContractError("the structural invalidation field is typed")
        if self.invalidation_temporal is not None and not isinstance(
            self.invalidation_temporal, TemporalInvalidation
        ):
            raise SetupContractError("the temporal invalidation field is typed")

    # -- projection ---------------------------------------------------------

    @property
    def manual_class(self) -> SetupClass:
        return self.execution_class if self.manual_status is None else self.manual_status

    # -- serialization ------------------------------------------------------

    def body(self) -> dict[str, Any]:
        """The canonical payload, without the hash."""

        return {
            "setup_id": self.setup_id,
            "setup_version": self.setup_version,
            "setup_contract_version": self.setup_contract_version,
            "engine_version": self.engine_version,
            "source_card_ref": self.source_card_ref,
            "execution_class": self.execution_class.value,
            "product_exposure": self.product_exposure.value,
            "eligibility": self.eligibility.value,
            "eligibility_reasons": [reason.value for reason in self.eligibility_reasons],
            "side": self.side.to_payload(),
            "location": None if self.location is None else _level_payload(self.location),
            "trigger_requirement": self.trigger_requirement.to_payload(),
            "invalidation_price": (
                None
                if self.invalidation_price is None
                else self.invalidation_price.to_payload()
            ),
            "invalidation_structural": (
                None
                if self.invalidation_structural is None
                else self.invalidation_structural.to_payload()
            ),
            "invalidation_temporal": (
                None
                if self.invalidation_temporal is None
                else self.invalidation_temporal.to_payload()
            ),
            "targets": [target.to_payload() for target in self.targets],
            "promotion_conditions": [
                condition.to_payload() for condition in self.promotion_conditions
            ],
            "no_go_refs": [ref.value for ref in self.no_go_refs],
            "parent_states": [state.to_payload() for state in self.parent_states],
            "transition_refs": [
                transition.to_payload() for transition in self.transition_refs
            ],
            "evidence_refs": [ref.to_payload() for ref in self.evidence_refs],
            "manual_status": self.manual_class.value,
            "automation_permitted": self.automation_permitted,
            "explanation_facts": [_fact_payload(fact) for fact in self.explanation_facts],
            "evaluation_time": self.evaluation_time,
        }

    @property
    def evaluation_hash(self) -> str:
        return payload_hash(self.body())

    def to_payload(self) -> dict[str, Any]:
        payload = self.body()
        payload["evaluation_hash"] = self.evaluation_hash
        return payload

    def to_json(self) -> str:
        return json.dumps(
            self.to_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SetupRecord":
        """Rebuild an equal record from its canonical payload."""

        if "eligibility" not in payload:
            raise SetupContractError("a setup payload carries its eligibility")
        location = payload.get("location")
        price = payload.get("invalidation_price")
        structural = payload.get("invalidation_structural")
        temporal = payload.get("invalidation_temporal")
        record = cls(
            setup_id=payload["setup_id"],
            setup_version=payload["setup_version"],
            setup_contract_version=payload.get(
                "setup_contract_version", SETUP_CONTRACT_VERSION
            ),
            engine_version=payload.get("engine_version", SETUP_ENGINE_VERSION),
            source_card_ref=payload["source_card_ref"],
            execution_class=SetupClass(payload["execution_class"]),
            product_exposure=ProductExposure(payload["product_exposure"]),
            eligibility=SetupEligibility(payload["eligibility"]),
            eligibility_reasons=tuple(
                SetupRefusalCode(value)
                for value in payload.get("eligibility_reasons", ())
            ),
            side=_direction_from_payload(payload["side"]),
            location=None if location is None else _level_from_payload(location),
            trigger_requirement=TriggerRequirement.from_payload(
                payload["trigger_requirement"]
            ),
            invalidation_price=(
                None if price is None else PriceInvalidation.from_payload(price)
            ),
            invalidation_structural=(
                None
                if structural is None
                else StructuralInvalidation.from_payload(structural)
            ),
            invalidation_temporal=(
                None if temporal is None else TemporalInvalidation.from_payload(temporal)
            ),
            targets=tuple(
                SetupTarget.from_payload(item) for item in payload.get("targets", ())
            ),
            promotion_conditions=tuple(
                PromotionCondition.from_payload(item)
                for item in payload.get("promotion_conditions", ())
            ),
            no_go_refs=tuple(
                NoGoReason(value) for value in payload.get("no_go_refs", ())
            ),
            parent_states=tuple(
                ParentStateRef.from_payload(item)
                for item in payload.get("parent_states", ())
            ),
            transition_refs=tuple(
                TransitionRef.from_payload(item)
                for item in payload.get("transition_refs", ())
            ),
            evidence_refs=tuple(
                EvidenceReference.from_payload(item)
                for item in payload.get("evidence_refs", ())
            ),
            manual_status=SetupClass(payload["manual_status"]),
            automation_permitted=bool(payload.get("automation_permitted", False)),
            explanation_facts=tuple(
                _fact_from_payload(item)
                for item in payload.get("explanation_facts", ())
            ),
            evaluation_time=payload.get("evaluation_time", "1970-01-01T00:00:00Z"),
        )
        if "evaluation_hash" in payload:
            if payload["evaluation_hash"] != record.evaluation_hash:
                raise SetupContractError("replayed evaluation hash does not match")
        return record

    @classmethod
    def from_json(cls, text: str) -> "SetupRecord":
        return cls.from_payload(json.loads(text))


def _level_payload(level: TypedLevel) -> dict[str, Any]:
    return {
        "level_id": level.level_id,
        "level_kind": level.level_kind.value,
        "family": level.family,
        "level": _dec_text(level.level),
        "price": _dec_text(level.price),
        "active": level.active,
        "source_ref": level.source_ref,
    }


def _level_from_payload(payload: dict[str, Any]) -> TypedLevel:
    from app.forge.model_runtime.contract import LevelKind

    return TypedLevel(
        level_id=payload["level_id"],
        level_kind=LevelKind(payload["level_kind"]),
        family=payload["family"],
        level=_dec(payload.get("level")),
        price=_dec(payload.get("price")),
        active=bool(payload.get("active", False)),
        source_ref=payload["source_ref"],
    )


def _direction_from_payload(payload: Any) -> DirectionBias:
    if payload == "NONE_DECLARED":
        return DirectionBias.none()
    from app.forge.model_runtime.contract import DirectionSide

    return DirectionBias(
        side=DirectionSide(payload["side"]),
        basis_fact_id=payload["basis_fact_id"],
        evidence_refs=tuple(payload.get("evidence_refs", ())),
    )


def _fact_payload(fact: ExplanationFact) -> dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "rule_id": fact.rule_id,
        "rule_version": fact.rule_version,
        "source_ref": fact.source_ref,
        "payload": [[key, value] for key, value in fact.payload],
    }


def _fact_from_payload(payload: dict[str, Any]) -> ExplanationFact:
    return ExplanationFact(
        fact_id=payload["fact_id"],
        rule_id=payload["rule_id"],
        rule_version=payload["rule_version"],
        source_ref=payload["source_ref"],
        payload=tuple((item[0], item[1]) for item in payload.get("payload", ())),
    )
