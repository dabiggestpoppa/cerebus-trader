"""Transition vocabulary and earned-transition guards (Ch III.4.2).

The vocabulary is frozen at exactly twelve kinds.  Families may
**restrict** it, never extend it: a kind outside a family's declared set
refuses with ``TRANSITION_NOT_IN_FAMILY_VOCABULARY``.

Every transition must be *earned*:

1. valid source lineage (the prior snapshot and its source output are
   finalized and belong to the same model key),
2. a qualifying prior state (declared required/forbidden sets),
3. a canonical rule with a materialization status (a
   ``NOT_MATERIALIZED`` rule can never earn a transition),
4. an injected, ordered event time,
5. a resulting-state identity that actually changes the state.

Cross-family application refuses even when the numbers coincide, because
the rule's ``source_ref`` must be one of the family's canonical sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from app.forge.market_data import DataOutcome
from app.forge.measurements import RuleMaterialization
from app.forge.model_runtime import Layer

from .errors import (
    AcceptWithoutTouchError,
    CompressionWithoutFailureError,
    DataQualityBlockedError,
    NoCalculationError,
    EligibilityWithoutAuthorityError,
    FailureWithoutAcceptanceError,
    ModelVersionUnavailableError,
    PromotionWithoutAuthorityError,
    ReleaseWithoutCompressionError,
    RepairWithoutFailureError,
    RuleNotMaterializedError,
    SourceLineageMissingError,
    StateContractError,
    TransitionAuthorityMismatchError,
    TransitionNoOpError,
    TransitionNotEarnedError,
    TransitionNotInFamilyVocabularyError,
    TransitionOrderAmbiguousError,
    TransitionPairForbiddenError,
)
from .snapshot import StateSnapshot
from .stand_down import STAND_DOWN_STATES, StandDownState

__all__ = [
    "FAMILY_STATES",
    "TRANSITION_AUTHORITY",
    "Condition",
    "QualifyingPriorState",
    "TransitionAuthority",
    "TransitionDecision",
    "TransitionKind",
    "TransitionRequest",
    "TransitionRule",
    "authority_for",
    "evaluate_transition",
]

_HASH = re.compile(r"^[0-9a-f]{64}$")
_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")
_RULE_ID = re.compile(r"^[A-Z][A-Z0-9_.]*$")


class TransitionKind(str, Enum):
    """The frozen twelve-kind transition vocabulary (Ch III.4.2)."""

    ENTER_STATE = "ENTER_STATE"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    FAIL = "FAIL"
    REPAIR = "REPAIR"
    PROMOTE = "PROMOTE"
    DELIVER = "DELIVER"
    REKEY = "REKEY"
    INVALIDATE = "INVALIDATE"
    COMPRESS = "COMPRESS"
    RELEASE = "RELEASE"
    STAND_DOWN = "STAND_DOWN"


class Condition(str, Enum):
    """Bounded facts that can support a transition (never free text)."""

    TOUCHED = "TOUCHED"
    ACCEPTED = "ACCEPTED"
    FAILED = "FAILED"
    REPAIR_ATTEMPTED = "REPAIR_ATTEMPTED"
    REPAIR_CONFIRMED = "REPAIR_CONFIRMED"
    COMPRESSED = "COMPRESSED"
    STRUCTURAL_EVENT = "STRUCTURAL_EVENT"
    DELIVERED = "DELIVERED"
    EXHAUSTED = "EXHAUSTED"
    INVALIDATED = "INVALIDATED"
    PARKED = "PARKED"


#: Kinds that would create downstream eligibility if the guard let them.
ELIGIBILITY_KINDS: frozenset[TransitionKind] = frozenset(
    {TransitionKind.PROMOTE, TransitionKind.ACCEPT}
)

#: Required supporting conditions per kind (alternatives = any one).
_REQUIRED_CONDITIONS: Mapping[TransitionKind, tuple[frozenset[Condition], ...]] = {
    TransitionKind.ACCEPT: (frozenset({Condition.TOUCHED}),),
    TransitionKind.FAIL: (frozenset({Condition.ACCEPTED}),),
    TransitionKind.REPAIR: (frozenset({Condition.FAILED}),),
    # Compression follows a failure *or* an attempted repair (any one).
    TransitionKind.COMPRESS: (
        frozenset({Condition.FAILED}),
        frozenset({Condition.REPAIR_ATTEMPTED}),
    ),
    TransitionKind.RELEASE: (frozenset({Condition.COMPRESSED}),),
    TransitionKind.REKEY: (frozenset({Condition.STRUCTURAL_EVENT}),),
}

_CONDITION_REFUSALS: Mapping[TransitionKind, type[Exception]] = {
    TransitionKind.ACCEPT: AcceptWithoutTouchError,
    TransitionKind.FAIL: FailureWithoutAcceptanceError,
    TransitionKind.REPAIR: RepairWithoutFailureError,
    TransitionKind.COMPRESS: CompressionWithoutFailureError,
    TransitionKind.RELEASE: ReleaseWithoutCompressionError,
    TransitionKind.REKEY: None,  # REKEY uses the structural-rekey refusal below
}


@dataclass(frozen=True)
class TransitionRule:
    """The canonical rule that must earn a transition."""

    rule_id: str
    rule_version: str
    materialization: RuleMaterialization
    source_ref: str

    def __post_init__(self) -> None:
        if not self.rule_id or not _RULE_ID.match(self.rule_id):
            raise StateContractError(
                f"rule_id must be a canonical identifier: {self.rule_id!r}"
            )
        if not self.rule_version:
            raise StateContractError("a transition rule requires a version")
        if not isinstance(self.materialization, RuleMaterialization):
            raise StateContractError(
                "a transition rule carries its materialization status"
            )
        if not self.source_ref or not _IDENT.match(self.source_ref):
            raise StateContractError(
                f"a transition rule requires a canonical source ref: {self.source_ref!r}"
            )


@dataclass(frozen=True)
class QualifyingPriorState:
    """Required/forbidden prior states for one kind (target ``""`` = default)."""

    kind: TransitionKind
    required_states: frozenset[str]
    forbidden_states: frozenset[str] = frozenset()
    target_state: str = ""

    def accepts(self, prior_state: str) -> bool:
        if prior_state in self.forbidden_states:
            return False
        return prior_state in self.required_states


@dataclass(frozen=True)
class TransitionAuthority:
    """Per-family, per-generation transition authority.

    ``unresolved`` is always a subset of ``allowed``: those kinds the family
    permits but whose canonical rule is not materialized (BTC weekly/monthly
    rekey, EUR Weekly compression, ...).  A kind outside ``allowed`` is never
    "unresolved" — it is simply not this family's vocabulary.
    """

    model_id: str
    model_version: str
    family: str
    layer: Layer
    canonical_source_refs: frozenset[str]
    states: frozenset[str]
    allowed: frozenset[TransitionKind]
    restricted: frozenset[TransitionKind]
    unresolved: frozenset[TransitionKind]
    qualifying: tuple[QualifyingPriorState, ...]
    forbidden_pairs: frozenset[tuple[str, str]] = frozenset()
    canonical_only_targets: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_version or not self.family:
            raise StateContractError("a transition authority declares its model key")
        if not isinstance(self.layer, Layer):
            raise StateContractError("a transition authority declares its layer")
        if not self.canonical_source_refs:
            raise StateContractError(
                "a transition authority declares its canonical sources"
            )
        if not self.unresolved <= self.allowed:
            raise StateContractError(
                "unresolved kinds must also be declared allowed: the family "
                "permits the kind but its canonical rule is missing.  A kind "
                "outside the family vocabulary is never unresolved"
            )
        if not self.allowed <= set(TransitionKind):
            raise StateContractError("allowed kinds are vocabulary members")
        if not self.restricted <= self.allowed:
            raise StateContractError("restricted kinds must be allowed")

    def permits(self, kind: TransitionKind) -> bool:
        return kind in self.allowed and kind not in self.unresolved

    def qualifies(self, kind: TransitionKind, target: str, prior_state: str) -> bool:
        candidates = [
            rule
            for rule in self.qualifying
            if rule.kind is kind and rule.target_state in (target, "")
        ]
        if not candidates:
            return False
        # Most specific (target-scoped) rule wins; every match must accept.
        specific = [rule for rule in candidates if rule.target_state]
        relevant = specific or candidates
        return all(rule.accepts(prior_state) for rule in relevant)


@dataclass(frozen=True)
class TransitionRequest:
    """One requested transition, with everything that must earn it."""

    kind: TransitionKind
    prior_snapshot: StateSnapshot
    rule: TransitionRule
    event_time: datetime
    resulting_state: str
    resulting_state_id: str
    conditions: frozenset[Condition] = frozenset()
    evidence_refs: tuple[str, ...] = ()
    stand_down_state: StandDownState | None = None
    order_key: str | None = None
    payload: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TransitionKind):
            raise StateContractError("a request carries a vocabulary kind")
        if not isinstance(self.prior_snapshot, StateSnapshot):
            raise StateContractError("a request carries its prior snapshot")
        if not isinstance(self.rule, TransitionRule):
            raise StateContractError("a request carries its canonical rule")
        if not isinstance(self.event_time, datetime):
            raise StateContractError("event_time must be a datetime")
        if self.event_time.tzinfo is None:
            raise StateContractError("event_time must be timezone-aware (injected)")
        if not self.resulting_state or not _RULE_ID.match(self.resulting_state):
            raise StateContractError(
                f"resulting_state must be a bounded identifier: {self.resulting_state!r}"
            )
        if not self.resulting_state_id or not _IDENT.match(self.resulting_state_id):
            raise StateContractError(
                f"resulting_state_id must be a bounded id: {self.resulting_state_id!r}"
            )
        for condition in self.conditions:
            if not isinstance(condition, Condition):
                raise StateContractError("conditions are bounded enum members")
        for key, value in self.payload:
            if not re.match(r"^[a-z][a-z0-9_]*$", key):
                raise StateContractError(f"payload key invalid: {key!r}")
            if not isinstance(value, str) or not _IDENT.match(value):
                raise StateContractError(
                    f"payload value must be a bounded identifier: {value!r}"
                )


@dataclass(frozen=True)
class TransitionDecision:
    """The earned transition record handed to the history ledger."""

    kind: TransitionKind
    model_id: str
    model_version: str
    prior_snapshot_id: str
    prior_snapshot_hash: str
    source_output_hash: str
    prior_state: str
    resulting_state: str
    resulting_state_id: str
    rule_id: str
    rule_version: str
    rule_source_ref: str
    event_time: datetime
    conditions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    order_key: str | None
    payload: tuple[tuple[str, str], ...]

    def to_payload(self) -> dict:
        return {
            "kind": self.kind.value,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "prior_snapshot_id": self.prior_snapshot_id,
            "prior_snapshot_hash": self.prior_snapshot_hash,
            "source_output_hash": self.source_output_hash,
            "prior_state": self.prior_state,
            "resulting_state": self.resulting_state,
            "resulting_state_id": self.resulting_state_id,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "rule_source_ref": self.rule_source_ref,
            "event_time": self.event_time,
            "conditions": list(self.conditions),
            "evidence_refs": list(self.evidence_refs),
            "order_key": self.order_key,
            "payload": [list(item) for item in self.payload],
        }


# ---------------------------------------------------------------------------
# Family state vocabularies (verbatim from the ratified III.3 family enums,
# plus the structural rekey-coordinate states III.4 must be able to record)
# ---------------------------------------------------------------------------

FAMILY_STATES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "EUR_DAILY": frozenset(
            {
                "SEED_T1",
                "SEED_T2",
                "SEED_T3",
                "SOURCE_NO_GO",
                "REKEY_100",
                "REKEY_125",
                "REKEY_132",
                "REKEY_168",
                "REKEY_185",
                "REKEYED",
            }
        ),
        "EUR_WEEKLY": frozenset({"ROUTE_OPEN", "NODE_PROMOTED", "FROZEN"}),
        "EUR_HIGHER_ORDER": frozenset(
            {
                "UNRESOLVED",
                "PRIOR_DECLARED",
                "COMPLETION_CONDITIONAL",
                "M3_RESOLVED",
            }
        ),
        "XAU": frozenset(
            {
                "PARKED",
                "PROMOTION_ELIGIBLE",
                "PROMOTION_RESEARCH",
                "PROMOTION_PENDING",
                "NODE_DECLARED",
                "ROUTE_OPEN",
                "UNRESOLVED",
                # Structural rekey mappings of the canonical 132/168 coordinate
                # lineage (model card "132 rekey"; 168/185 deeper sequence).
                "REKEY_132",
                "REKEY_168",
            }
        ),
        "BTC_TRACKER": frozenset(
            {"SEED_T1", "SEED_T2", "SEED_T3", "ASIAN_RANGE_NO_GO"}
        ),
        "FIB_RANGE_BIRTH": frozenset(
            {
                "RANGE_BIRTH_UNRESOLVED",
                "RANGE_ACTIVE",
                "REKEY_REMAPPED",
                "ANCHOR_INVALIDATED",
            }
        ),
        "JPY_CARRY": frozenset(
            {
                "BASKET_AGREE_CONFIRM",
                "BASKET_CONFIRM_ABSENT",
                "BASKET_VETO",
                "BASKET_CONFLICT",
                "BASKET_UNRESOLVED",
            }
        ),
    }
)

_EUR_DAILY_CARD = "EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
_EUR_WEEKLY_CARD = "EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md"
_EUR_HO_CARD = "EUR_HIGHER_ORDER_MODEL_CARD_V1.md"
_XAU_CARD = "XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"
_BTC_CARD = "BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"
_FIB_CARD = "FIB_RANGE_BIRTH_MODEL_CARD_V1.md"
_JPY_CARD = "JPY_CARRY_GAME_MODEL_CARD_V1.md"


def _build(
    *,
    model_id: str,
    model_version: str,
    family: str,
    layer: Layer,
    sources: tuple[str, ...],
    allowed: tuple[TransitionKind, ...],
    restricted: tuple[TransitionKind, ...] = (),
    unresolved: tuple[TransitionKind, ...] = (),
    overrides: tuple[tuple[TransitionKind, str, frozenset[str], frozenset[str]], ...] = (),
    forbidden_pairs: tuple[tuple[str, str], ...] = (),
    canonical_only_targets: frozenset[str] = frozenset(),
) -> TransitionAuthority:
    states = FAMILY_STATES[family]
    table: dict[tuple[TransitionKind, str], QualifyingPriorState] = {}
    for kind in tuple(allowed) + tuple(unresolved):
        if kind in allowed:
            table[(kind, "")] = QualifyingPriorState(
                kind=kind, required_states=states
            )
    for kind, target, required, forbidden in overrides:
        table[(kind, target)] = QualifyingPriorState(
            kind=kind,
            required_states=required,
            forbidden_states=forbidden,
            target_state=target,
        )
    return TransitionAuthority(
        model_id=model_id,
        model_version=model_version,
        family=family,
        layer=layer,
        canonical_source_refs=frozenset(sources),
        states=states,
        allowed=frozenset(allowed),
        restricted=frozenset(restricted),
        unresolved=frozenset(unresolved),
        qualifying=tuple(table.values()),
        forbidden_pairs=frozenset(forbidden_pairs),
        canonical_only_targets=canonical_only_targets,
    )


_ALL_KINDS_NEVER = ()

_ENTRIES: tuple[TransitionAuthority, ...] = (
    _build(
        model_id="EUR.DAILY.NEWS_REKEY.V1",
        model_version="PHASE1",
        family="EUR_DAILY",
        layer=Layer.L1,
        sources=(_EUR_DAILY_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.DELIVER,
            TransitionKind.ACCEPT,
            TransitionKind.REJECT,
            TransitionKind.REKEY,
            TransitionKind.FAIL,
            TransitionKind.REPAIR,
            TransitionKind.COMPRESS,
            TransitionKind.RELEASE,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
        restricted=(
            TransitionKind.REKEY,
            TransitionKind.FAIL,
            TransitionKind.REPAIR,
            TransitionKind.COMPRESS,
            TransitionKind.RELEASE,
        ),
        overrides=(
            (
                TransitionKind.DELIVER,
                "",
                FAMILY_STATES["EUR_DAILY"],
                frozenset({"SOURCE_NO_GO"}),
            ),
            (
                TransitionKind.ACCEPT,
                "",
                FAMILY_STATES["EUR_DAILY"],
                frozenset({"SOURCE_NO_GO"}),
            ),
            (
                TransitionKind.REKEY,
                "",
                frozenset(
                    {
                        "SEED_T1",
                        "SEED_T2",
                        "SEED_T3",
                        "REKEY_100",
                        "REKEY_125",
                        "REKEY_132",
                        "REKEY_168",
                    }
                ),
                frozenset({"SOURCE_NO_GO", "REKEY_185"}),
            ),
        ),
    ),
    _build(
        model_id="EUR.WEEKLY.V1_1",
        model_version="V1_1",
        family="EUR_WEEKLY",
        layer=Layer.L2,
        sources=(_EUR_WEEKLY_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.PROMOTE,
            TransitionKind.DELIVER,
            TransitionKind.ACCEPT,
            TransitionKind.REJECT,
            TransitionKind.REKEY,
            TransitionKind.COMPRESS,
            TransitionKind.RELEASE,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
        restricted=(TransitionKind.PROMOTE,),
        unresolved=(TransitionKind.REKEY, TransitionKind.COMPRESS, TransitionKind.RELEASE),
        overrides=(
            (
                TransitionKind.PROMOTE,
                "",
                frozenset({"ROUTE_OPEN"}),
                frozenset({"FROZEN"}),
            ),
            (
                TransitionKind.DELIVER,
                "",
                frozenset({"ROUTE_OPEN", "NODE_PROMOTED"}),
                frozenset({"FROZEN"}),
            ),
        ),
    ),
    _build(
        model_id="EUR.HIGHER_ORDER.V1",
        model_version="V1",
        family="EUR_HIGHER_ORDER",
        layer=Layer.L3,
        sources=(_EUR_HO_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.DELIVER,
            TransitionKind.REKEY,
            TransitionKind.COMPRESS,
            TransitionKind.RELEASE,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
        unresolved=(
            TransitionKind.REKEY,
            TransitionKind.COMPRESS,
            TransitionKind.RELEASE,
        ),
        overrides=(
            (
                TransitionKind.DELIVER,
                "",
                frozenset(
                    {"PRIOR_DECLARED", "COMPLETION_CONDITIONAL", "M3_RESOLVED"}
                ),
                frozenset({"UNRESOLVED"}),
            ),
        ),
    ),
    _build(
        model_id="XAU.GAME.L1_L2_L3.V1",
        model_version="V1",
        family="XAU",
        layer=Layer.CROSS_LAYER,
        sources=(_XAU_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.PROMOTE,
            TransitionKind.ACCEPT,
            TransitionKind.REJECT,
            TransitionKind.REKEY,
            TransitionKind.FAIL,
            TransitionKind.REPAIR,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
        restricted=(
            TransitionKind.PROMOTE,
            TransitionKind.REKEY,
            TransitionKind.FAIL,
            TransitionKind.REPAIR,
        ),
        overrides=(
            (
                TransitionKind.PROMOTE,
                "",
                frozenset(
                    {
                        "PROMOTION_PENDING",
                        "PROMOTION_ELIGIBLE",
                        "PROMOTION_RESEARCH",
                    }
                ),
                frozenset({"PARKED"}),
            ),
            (
                TransitionKind.ACCEPT,
                "",
                FAMILY_STATES["XAU"],
                frozenset({"PARKED"}),
            ),
            (
                TransitionKind.DELIVER,
                "",
                FAMILY_STATES["XAU"],
                frozenset({"PARKED"}),
            ),
            (
                TransitionKind.REKEY,
                "",
                frozenset(
                    {
                        "ROUTE_OPEN",
                        "NODE_DECLARED",
                        "PROMOTION_PENDING",
                        "PROMOTION_ELIGIBLE",
                        "PROMOTION_RESEARCH",
                    }
                ),
                frozenset({"PARKED"}),
            ),
        ),
        # 132 -> 168 is canonically NOT automatic (frozen XAU rule).
        forbidden_pairs=(("REKEY_132", "REKEY_168"),),
    ),
    _build(
        model_id="BTC.TRACKER.DWM.V1",
        model_version="V1",
        family="BTC_TRACKER",
        layer=Layer.CROSS_LAYER,
        sources=(_BTC_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.DELIVER,
            TransitionKind.ACCEPT,
            TransitionKind.REJECT,
            TransitionKind.REKEY,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
        unresolved=(TransitionKind.REKEY,),
        overrides=(
            (
                TransitionKind.DELIVER,
                "",
                FAMILY_STATES["BTC_TRACKER"],
                frozenset({"ASIAN_RANGE_NO_GO"}),
            ),
            (
                TransitionKind.ACCEPT,
                "",
                FAMILY_STATES["BTC_TRACKER"],
                frozenset({"ASIAN_RANGE_NO_GO"}),
            ),
        ),
    ),
    _build(
        model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
        model_version="R15",
        family="FIB_RANGE_BIRTH",
        layer=Layer.CROSS_LAYER,
        sources=(_FIB_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.DELIVER,
            TransitionKind.REKEY,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
        overrides=(
            (
                TransitionKind.REKEY,
                "",
                frozenset({"RANGE_ACTIVE"}),
                frozenset({"RANGE_BIRTH_UNRESOLVED", "ANCHOR_INVALIDATED"}),
            ),
            (
                TransitionKind.DELIVER,
                "",
                frozenset({"RANGE_ACTIVE", "REKEY_REMAPPED"}),
                frozenset({"RANGE_BIRTH_UNRESOLVED", "ANCHOR_INVALIDATED"}),
            ),
        ),
        # Entering an active range requires the materialized R15 rule.
        canonical_only_targets=frozenset({"RANGE_ACTIVE"}),
    ),
    _build(
        model_id="JPY.CARRY_GAME.L1_L3.V1",
        model_version="V1",
        family="JPY_CARRY",
        layer=Layer.CROSS_LAYER,
        sources=(_JPY_CARD,),
        allowed=(
            TransitionKind.ENTER_STATE,
            TransitionKind.DELIVER,
            TransitionKind.INVALIDATE,
            TransitionKind.STAND_DOWN,
        ),
    ),
)

TRANSITION_AUTHORITY: Mapping[tuple[str, str], TransitionAuthority] = MappingProxyType(
    {(entry.model_id, entry.model_version): entry for entry in _ENTRIES}
)


def authority_for(model_id: str, model_version: str) -> TransitionAuthority:
    """Resolve one exact declaration; unknown ⇒ fail closed."""

    if not isinstance(model_id, str) or not model_id:
        raise ModelVersionUnavailableError("a model_id is required")
    if not isinstance(model_version, str) or not model_version:
        raise ModelVersionUnavailableError("a model_version is required")
    try:
        return TRANSITION_AUTHORITY[(model_id, model_version)]
    except KeyError:
        raise ModelVersionUnavailableError(
            f"{model_id}@{model_version} declares no transition authority at "
            "this state-engine version"
        ) from None


def evaluate_transition(
    request: TransitionRequest,
    *,
    authority: TransitionAuthority | None = None,
) -> TransitionDecision:
    """Evaluate one transition request; return the earned decision."""

    if not isinstance(request, TransitionRequest):
        raise StateContractError("evaluate_transition requires a TransitionRequest")

    prior = request.prior_snapshot
    if not prior.source_output_hash or not _HASH.match(prior.source_output_hash):
        raise SourceLineageMissingError(
            "the prior snapshot carries no finalized source output hash"
        )
    if not prior.snapshot_hash or not _HASH.match(prior.snapshot_hash):
        raise SourceLineageMissingError(
            "the prior snapshot is not finalized (no snapshot hash)"
        )

    # A blocked or uncalculable source can never earn a final transition.
    if prior.quality_state is DataOutcome.DATA_QUALITY_BLOCKED:
        raise DataQualityBlockedError(
            "the prior snapshot is quality-blocked; no final transition can be earned"
        )
    if prior.quality_state is DataOutcome.NO_CALCULATION:
        raise NoCalculationError(
            "the prior snapshot reports NO_CALCULATION; no transition can be earned"
        )

    resolved = authority_for(prior.model_id, prior.model_version)
    if authority is not None:
        if not isinstance(authority, TransitionAuthority):
            raise StateContractError("authority must be a TransitionAuthority")
        if (
            authority.model_id != resolved.model_id
            or authority.model_version != resolved.model_version
        ):
            raise TransitionAuthorityMismatchError(
                f"authority {authority.model_id}@{authority.model_version} does not "
                f"own prior snapshot {resolved.model_id}@{resolved.model_version}"
            )

    if request.rule.source_ref not in resolved.canonical_source_refs:
        raise TransitionAuthorityMismatchError(
            f"rule source {request.rule.source_ref!r} is not a canonical source of "
            f"{resolved.model_id}@{resolved.model_version}"
        )

    if request.kind in resolved.unresolved:
        raise RuleNotMaterializedError(
            f"{request.kind.value} is canonically unresolved for "
            f"{resolved.model_id}@{resolved.model_version}"
        )
    if request.kind not in resolved.allowed:
        raise TransitionNotInFamilyVocabularyError(
            f"{request.kind.value} is outside the transition vocabulary of "
            f"{resolved.family}"
        )
    if request.rule.materialization is RuleMaterialization.NOT_MATERIALIZED:
        raise RuleNotMaterializedError(
            f"rule {request.rule.rule_id}@{request.rule.rule_version} is not "
            "materialized; it cannot earn a transition"
        )
    if (
        request.resulting_state in resolved.canonical_only_targets
        and request.rule.materialization is not RuleMaterialization.CANONICAL
    ):
        raise RuleNotMaterializedError(
            f"entering {request.resulting_state} requires a CANONICAL rule; "
            f"{request.rule.rule_id} is {request.rule.materialization.value}"
        )

    # Event-time ordering: injected, monotone, explicit when simultaneous.
    if request.event_time < prior.event_time:
        raise StateContractError(
            "event_time precedes the prior snapshot event time"
        )
    if request.event_time == prior.event_time and request.order_key is None:
        raise TransitionOrderAmbiguousError(
            "two events share one event time and no order key was declared"
        )

    # No-op transitions are refused rather than silently appended.
    if request.resulting_state == prior.active_state:
        raise TransitionNoOpError(
            f"transition would not change state {prior.active_state}"
        )

    # No-go/stand-down locks eligibility (Ch III.4.8).
    if prior.active_state in STAND_DOWN_STATES and request.kind in ELIGIBILITY_KINDS:
        raise EligibilityWithoutAuthorityError(
            f"prior state {prior.active_state} is a stand-down; "
            f"{request.kind.value} would manufacture eligibility"
        )

    if request.kind is TransitionKind.STAND_DOWN:
        if request.stand_down_state is None:
            raise StateContractError(
                "a STAND_DOWN transition requires its bounded stand-down state"
            )

    if (prior.active_state, request.resulting_state) in resolved.forbidden_pairs:
        raise TransitionPairForbiddenError(
            f"{prior.active_state} -> {request.resulting_state} is canonically "
            "forbidden for this family"
        )

    # Required supporting conditions (touch ≠ acceptance, etc.).
    alternatives = _REQUIRED_CONDITIONS.get(request.kind)
    if alternatives:
        satisfied = any(alt <= request.conditions for alt in alternatives)
        if not satisfied:
            if request.kind is TransitionKind.REKEY:
                from .errors import RekeyNotStructuralError

                raise RekeyNotStructuralError(
                    "a rekey requires a qualifying structural event, not a bare "
                    "touch or threshold crossing"
                )
            refusal = _CONDITION_REFUSALS.get(request.kind)
            if refusal is not None:
                raise refusal(
                    f"{request.kind.value} requires "
                    f"{sorted(c.value for c in alternatives[0])}"
                )

    if request.kind is TransitionKind.PROMOTE:
        if not request.evidence_refs:
            raise PromotionWithoutAuthorityError(
                "a promotion requires evidence references"
            )

    if not resolved.qualifies(
        request.kind, request.resulting_state, prior.active_state
    ):
        raise TransitionNotEarnedError(
            f"prior state {prior.active_state} does not qualify for "
            f"{request.kind.value} -> {request.resulting_state}"
        )

    return TransitionDecision(
        kind=request.kind,
        model_id=prior.model_id,
        model_version=prior.model_version,
        prior_snapshot_id=prior.snapshot_id,
        prior_snapshot_hash=prior.snapshot_hash,
        source_output_hash=prior.source_output_hash,
        prior_state=prior.active_state,
        resulting_state=request.resulting_state,
        resulting_state_id=request.resulting_state_id,
        rule_id=request.rule.rule_id,
        rule_version=request.rule.rule_version,
        rule_source_ref=request.rule.source_ref,
        event_time=request.event_time,
        conditions=tuple(sorted(condition.value for condition in request.conditions)),
        evidence_refs=tuple(request.evidence_refs),
        order_key=request.order_key,
        payload=tuple(request.payload),
    )
