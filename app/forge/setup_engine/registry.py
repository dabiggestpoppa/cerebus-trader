"""Canonical Setup Card registry (Ch III.5.1).

Only the three canonically provisioned Setup Cards may be registered, and
their identity, version, lifecycle status, execution class, exposure and
parent model ids are carried **verbatim** from the corpus cards.  Nothing
is normalised upward and no identity is minted: ``register`` refuses an
id outside the frozen set, so a synthesised card can never be served.

Implementation-time reconciliation (``III.5-REC-1``) and defect
(``III.5-DEFECT-1``) arise here and are disclosed in ``EVIDENCE.md``:

* the corpus names setup ids ``SETUP.*`` while Book I's ``CanonicalId``
  kernel requires ``SET.`` — the engine carries the corpus string;
* the corpus card ``status`` values (``CANONICALIZATION_CANDIDATE``,
  ``RESEARCH_OPERATOR_CANDIDATE``) are not members of Book I's
  14-value ``EvidenceStatus``, so ``SetupOperatorCard`` cannot validate
  any canonical card.  The engine carries the verbatim card status in
  :class:`CardStatus` and projects it *downward* to ``EvidenceStatus``
  only for refusal classification — never upward.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum
from typing import Iterable

from app.forge.canonical import EvidenceStatus, ProductExposure, SetupClass
from app.forge.model_runtime.contract import Layer

from .contracts import (
    EvidenceReference,
    ParameterMaterialization,
    PriceInvalidation,
    SetupEligibility,
    SetupSurface,
    SetupTarget,
    StructuralInvalidation,
    TemporalInvalidation,
    TriggerCombination,
    TriggerLiteral,
    TriggerRequirement,
    TriggerType,
)
from .errors import SetupRefusalCode, SetupRegistryError
from .versions import SETUP_ID_PATTERN

__all__ = [
    "CANONICAL_SETUP_CARDS",
    "CANONICAL_SETUP_IDS",
    "CANONICAL_CARD_SOURCES",
    "CardStatus",
    "CanonicalSetupCard",
    "ParentRequirement",
    "REFUSED_CARD_STATUSES",
    "RegistryResolution",
    "SetupRegistry",
    "load_canonical_cards",
    "project_status",
]

_EVIDENCE_NAMES = tuple(status.value for status in EvidenceStatus)


class CardStatus(str, Enum):
    """Card lifecycle status, verbatim as written on the canonical card.

    The two corpus-only values have no ``EvidenceStatus`` member; the
    projection maps both **downward** to ``CANDIDATE`` and is used only
    to classify refusal, never to promote a card.
    """

    CANONICALIZATION_CANDIDATE = "CANONICALIZATION_CANDIDATE"
    RESEARCH_OPERATOR_CANDIDATE = "RESEARCH_OPERATOR_CANDIDATE"
    OBSERVED = "OBSERVED"
    VALIDATED = "VALIDATED"
    FORWARD_OOS = "FORWARD_OOS"
    CANDIDATE = "CANDIDATE"
    RESEARCH_FLAG = "RESEARCH_FLAG"
    DESCRIPTIVE = "DESCRIPTIVE"
    HISTORICAL = "HISTORICAL"
    PARKED = "PARKED"
    SUPERSEDED = "SUPERSEDED"
    FALSIFIED = "FALSIFIED"
    NO_GO = "NO_GO"
    REPRODUCTION_REQUIRED = "REPRODUCTION_REQUIRED"
    INTERNAL_CONTRADICTION = "INTERNAL_CONTRADICTION"
    IMPLEMENTATION_NOT_PARITY_SAFE = "IMPLEMENTATION_NOT_PARITY_SAFE"


#: Statuses that must never be served on a production or operator surface.
REFUSED_CARD_STATUSES: frozenset[CardStatus] = frozenset(
    {
        CardStatus.PARKED,
        CardStatus.IMPLEMENTATION_NOT_PARITY_SAFE,
        CardStatus.INTERNAL_CONTRADICTION,
        CardStatus.FALSIFIED,
        CardStatus.SUPERSEDED,
        CardStatus.NO_GO,
        CardStatus.REPRODUCTION_REQUIRED,
    }
)

_CORPUS_PROJECTION: dict[CardStatus, EvidenceStatus] = {
    CardStatus.CANONICALIZATION_CANDIDATE: EvidenceStatus.CANDIDATE,
    CardStatus.RESEARCH_OPERATOR_CANDIDATE: EvidenceStatus.CANDIDATE,
}


def project_status(status: CardStatus) -> EvidenceStatus:
    """Project a verbatim card status onto Book I's status vocabulary.

    This is deliberately a **downward** projection: a corpus-only
    candidate status becomes ``CANDIDATE``.  No value is ever projected
    upward, and the projection is never used to serve or promote a card.
    """

    if not isinstance(status, CardStatus):
        raise SetupRegistryError("card status uses the bounded card vocabulary")
    if status in _CORPUS_PROJECTION:
        return _CORPUS_PROJECTION[status]
    return EvidenceStatus(status.value)


@dataclass(frozen=True)
class ParentRequirement:
    """A parent model this card requires, with its version and states."""

    model_id: str
    model_version: str
    allowed_states: tuple[str, ...] = ()
    required_layer: Layer | None = None

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_version:
            raise SetupRegistryError(
                "a parent requirement names its model id and version"
            )
        if not self.allowed_states:
            raise SetupRegistryError(
                "a parent requirement declares the states it accepts"
            )
        if self.required_layer is not None and not isinstance(self.required_layer, Layer):
            raise SetupRegistryError("required_layer uses the frozen III.3 layers")


@dataclass(frozen=True)
class CanonicalSetupCard:
    """The frozen, in-code projection of one canonical Setup Card."""

    setup_id: str
    version: str
    status: CardStatus
    execution_class: SetupClass
    exposure: ProductExposure
    parent_model_ids: tuple[str, ...]
    parent_requirements: tuple[ParentRequirement, ...]
    trigger_requirement: TriggerRequirement
    targets: tuple[SetupTarget, ...]
    source_card_ref: str
    required_parameters: tuple[str, ...] = ()
    requires_anchor: bool = False
    requires_native_tier: bool = True
    required_clock_checkpoint: str | None = None
    requires_after_three_context: bool = False
    default_invalidation_price: PriceInvalidation | None = None
    default_invalidation_structural: StructuralInvalidation | None = None
    default_invalidation_temporal: TemporalInvalidation | None = None
    required_invalidation_kinds: tuple[str, ...] = ("PRICE",)
    evidence_refs: tuple[EvidenceReference, ...] = ()
    market_scope: tuple[str, ...] = ()
    entry_zone_ref: str | None = None
    layer_handoff: tuple[str, str, str] = ("", "", "")

    def __post_init__(self) -> None:
        import re

        if not isinstance(self.setup_id, str) or not re.match(
            SETUP_ID_PATTERN, self.setup_id
        ):
            raise SetupRegistryError(
                f"a card requires a canonical corpus setup identity: {self.setup_id!r}"
            )
        if not isinstance(self.status, CardStatus):
            raise SetupRegistryError("a card carries its verbatim status")
        if not isinstance(self.execution_class, SetupClass):
            raise SetupRegistryError("a card carries the Book I execution class")
        if not isinstance(self.exposure, ProductExposure):
            raise SetupRegistryError("a card carries the Book I exposure")
        if not self.source_card_ref:
            raise SetupRegistryError("a card names its corpus source")
        if not self.targets:
            raise SetupRegistryError("a card declares at least one target")
        indices = [target.declared_order_index for target in self.targets]
        if indices != sorted(indices) or len(set(indices)) != len(indices):
            raise SetupRegistryError(
                "card targets are declared in strict canonical order"
            )
        for kind in self.required_invalidation_kinds:
            if kind not in ("PRICE", "STRUCTURAL", "TEMPORAL"):
                raise SetupRegistryError("invalidation kinds are the frozen trichotomy")

    @property
    def is_automation_approved(self) -> bool:
        return self.execution_class is SetupClass.AUTOMATION_APPROVED

    @property
    def automation_permitted(self) -> bool:
        """Automation is permitted only for a canonical, approved card.

        At this head no canonical card is ``AUTOMATION_APPROVED``, so this
        is ``False`` for every card — by construction, not convention.
        """

        return (
            self.is_automation_approved
            and self.status not in REFUSED_CARD_STATUSES
            and self.execution_class is SetupClass.AUTOMATION_APPROVED
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "setup_id": self.setup_id,
            "version": self.version,
            "status": self.status.value,
            "execution_class": self.execution_class.value,
            "exposure": self.exposure.value,
            "parent_model_ids": list(self.parent_model_ids),
            "source_card_ref": self.source_card_ref,
            "targets": [target.target_id for target in self.targets],
        }


_CARD_SOURCE = "corpus/canonical/setups/"

CANONICAL_CARD_SOURCES: tuple[str, ...] = (
    _CARD_SOURCE + "XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
    _CARD_SOURCE + "FIB_REKEY_OPERATOR_CARD_V1.md",
    _CARD_SOURCE + "JPY_CARRY_ROLE_GATED_OPERATOR_CARD_V1.md",
)

CANONICAL_SETUP_IDS: tuple[str, ...] = (
    "SETUP.XAU.QUARTER_ZONE.V1",
    "SETUP.FIB.REKEY.V1",
    "SETUP.JPY.CARRY_ROLE_GATE.V1",
)


def _promotion(condition_id: str, transition: str, authority: str) -> "object":
    from .contracts import PromotionCondition

    return PromotionCondition(
        condition_id=condition_id,
        required_transition=transition,
        source_ref=CANONICAL_CARD_SOURCES[0],
        authority_ref=authority,
    )


def _card(
    *,
    setup_id: str,
    status: CardStatus,
    execution_class: SetupClass,
    exposure: ProductExposure,
    parent_id: str,
    allowed_states: tuple[str, ...],
    trigger: TriggerRequirement,
    targets: tuple[SetupTarget, ...],
    source_card_ref: str,
    required_parameters: tuple[str, ...] = (),
    requires_anchor: bool = False,
    clock_checkpoint: str | None = None,
    after_three: bool = False,
    price: PriceInvalidation | None = None,
    structural: StructuralInvalidation | None = None,
    temporal: TemporalInvalidation | None = None,
    invalidation_kinds: tuple[str, ...] = ("PRICE",),
    evidence: tuple[EvidenceReference, ...] = (),
    market_scope: tuple[str, ...] = (),
    entry_zone_ref: str | None = None,
    layer_handoff: tuple[str, str, str] = ("", "", ""),
) -> CanonicalSetupCard:
    return CanonicalSetupCard(
        setup_id=setup_id,
        version="1.0",
        status=status,
        execution_class=execution_class,
        exposure=exposure,
        parent_model_ids=(parent_id,),
        parent_requirements=(
            ParentRequirement(
                model_id=parent_id, model_version="1.0", allowed_states=allowed_states
            ),
        ),
        trigger_requirement=trigger,
        targets=targets,
        source_card_ref=source_card_ref,
        required_parameters=required_parameters,
        requires_anchor=requires_anchor,
        required_clock_checkpoint=clock_checkpoint,
        requires_after_three_context=after_three,
        default_invalidation_price=price,
        default_invalidation_structural=structural,
        default_invalidation_temporal=temporal,
        required_invalidation_kinds=invalidation_kinds,
        evidence_refs=evidence,
        market_scope=market_scope,
        entry_zone_ref=entry_zone_ref,
        layer_handoff=layer_handoff,
    )


_XAU_SOURCE = CANONICAL_CARD_SOURCES[0]

CANONICAL_SETUP_CARDS: tuple[CanonicalSetupCard, ...] = (
    _card(
        setup_id="SETUP.XAU.QUARTER_ZONE.V1",
        status=CardStatus.CANONICALIZATION_CANDIDATE,
        execution_class=SetupClass.MANUAL_OPERATOR,
        exposure=ProductExposure.OPERATOR_ONLY,
        parent_id="XAU.GAME.L1_L2_L3.V1",
        allowed_states=(
            "NODE_DECLARED",
            "ROUTE_OPEN",
            "PROMOTION_ELIGIBLE",
            "PROMOTION_RESEARCH",
            "PROMOTION_PENDING",
        ),
        trigger=TriggerRequirement(
            source_ref=_XAU_SOURCE + "#Entry",
            literals=(TriggerLiteral(TriggerType.EXCURSION),),
            any_of=(
                TriggerLiteral(TriggerType.REJECTION),
                TriggerLiteral(TriggerType.CLOSE),
                TriggerLiteral(TriggerType.SR_FLIP),
            ),
            combination=TriggerCombination.ALL,
        ),
        targets=(
            SetupTarget(
                target_id="SETUP.XAU.TARGET.NEXT_QUARTER",
                declared_order_index=0,
                source_ref=_XAU_SOURCE + "#Targets",
                promotion=_promotion(
                    "SETUP.XAU.PROMOTE.NEXT_QUARTER",
                    "L1_CONFIRMED",
                    "SETUP.XAU.QUARTER_ZONE.V1",
                ),
            ),
            SetupTarget(
                target_id="SETUP.XAU.TARGET.NEXT_QUARTER_DISCOUNT_PREMIUM",
                declared_order_index=1,
                source_ref=_XAU_SOURCE + "#Targets",
                promotion=_promotion(
                    "SETUP.XAU.PROMOTE.NEXT_QUARTER_DZ",
                    "L1_CONFIRMED",
                    "SETUP.XAU.QUARTER_ZONE.V1",
                ),
            ),
            SetupTarget(
                target_id="SETUP.XAU.TARGET.CONFIRM_5",
                declared_order_index=2,
                source_ref=_XAU_SOURCE + "#Targets",
                confirmation_only=True,
            ),
            SetupTarget(
                target_id="SETUP.XAU.TARGET.CONFIRM_10",
                declared_order_index=3,
                source_ref=_XAU_SOURCE + "#Targets",
                confirmation_only=True,
            ),
        ),
        source_card_ref=_XAU_SOURCE,
        required_parameters=("QUARTER_ZONE_MAPPING", "LADDER_INVALIDATION"),
        clock_checkpoint="AFTER_0300_NY",
        after_three=True,
        price=PriceInvalidation(
            value=Decimal("5"),
            magnitude_unit="XAU_POINTS",
            materialization=ParameterMaterialization.DECLARED,
            source_ref=_XAU_SOURCE + "#Invalidation",
        ),
        structural=StructuralInvalidation(
            condition_id="XAU.LADDER.80_FAMILY",
            state_ref="XAU.STRUCTURAL.80",
            source_ref=_XAU_SOURCE + "#Invalidation",
        ),
        temporal=None,
        invalidation_kinds=("PRICE", "STRUCTURAL"),
        evidence=(
            EvidenceReference(
                evidence_id="EV.XAU.PROMOTION.68_80.V1",
                status=EvidenceStatus.VALIDATED,
                claim_id="CL.XAU.PROMOTION.68_80",
                population_key="XAU.PROMOTION",
            ),
            EvidenceReference(
                evidence_id="EV.XAU.PROMOTION.120_132.V1",
                status=EvidenceStatus.RESEARCH_FLAG,
                claim_id="CL.XAU.PROMOTION.120_132",
                population_key="XAU.PROMOTION",
            ),
        ),
        market_scope=("XAUUSD",),
        entry_zone_ref="XAU.QUARTER.ZONE",
        layer_handoff=("NEXT_QUARTER", "L2_PATH", "L1_ENTRY"),
    ),
    _card(
        setup_id="SETUP.FIB.REKEY.V1",
        status=CardStatus.RESEARCH_OPERATOR_CANDIDATE,
        execution_class=SetupClass.RESEARCH_ONLY,
        exposure=ProductExposure.RESEARCH_LAB,
        parent_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
        allowed_states=("RANGE_BORN", "RANGE_ACTIVE"),
        trigger=TriggerRequirement(
            source_ref=CANONICAL_CARD_SOURCES[1] + "#Entry",
            literals=(TriggerLiteral(TriggerType.CLOSE),),
        ),
        targets=(
            SetupTarget(
                target_id="SETUP.FIB.TARGET.REKEY_132",
                declared_order_index=0,
                source_ref=CANONICAL_CARD_SOURCES[1] + "#Targets",
                coordinate=Decimal("132"),
                promotion=_promotion(
                    "SETUP.FIB.PROMOTE.REKEY_132",
                    "RANGE_REKEY",
                    "SETUP.FIB.REKEY.V1",
                ),
            ),
            SetupTarget(
                target_id="SETUP.FIB.TARGET.DUAL_ENTRY_168",
                declared_order_index=1,
                source_ref=CANONICAL_CARD_SOURCES[1] + "#Targets",
                coordinate=Decimal("168"),
            ),
            SetupTarget(
                target_id="SETUP.FIB.TARGET.EXTENSION_185",
                declared_order_index=2,
                source_ref=CANONICAL_CARD_SOURCES[1] + "#Targets",
                coordinate=Decimal("185"),
                range_left_conditioned_on=("FIB.REKEY.TRIGGERED",),
            ),
        ),
        source_card_ref=CANONICAL_CARD_SOURCES[1],
        requires_anchor=True,
        price=PriceInvalidation(
            value=Decimal("168"),
            magnitude_unit="FIB_PERCENT",
            materialization=ParameterMaterialization.CANONICAL,
            source_ref=CANONICAL_CARD_SOURCES[1] + "#Invalidation",
        ),
        invalidation_kinds=("PRICE",),
        evidence=(
            EvidenceReference(
                evidence_id="EV.FIB.R11.ANCHOR_OVERGEN.V1",
                status=EvidenceStatus.NO_GO,
                claim_id="CL.FIB.R11.GENERATOR_FAILURE",
                population_key="FIB.R11.ANCHOR",
            ),
        ),
        market_scope=("CROSSASSET",),
        entry_zone_ref="FIB.REKEY.132",
        layer_handoff=("RANGE_REKEY", "L2_PATH", "L1_ENTRY"),
    ),
    _card(
        setup_id="SETUP.JPY.CARRY_ROLE_GATE.V1",
        status=CardStatus.CANONICALIZATION_CANDIDATE,
        execution_class=SetupClass.MANUAL_OPERATOR,
        exposure=ProductExposure.OPERATOR_ONLY,
        parent_id="JPY.CARRY_GAME.L1_L3.V1",
        allowed_states=(
            "BASKET_AGREE_CONFIRM",
            "BASKET_CONFIRM_ABSENT",
            "BASKET_VETO",
            "BASKET_CONFLICT",
        ),
        trigger=TriggerRequirement(
            source_ref=CANONICAL_CARD_SOURCES[2] + "#Entry",
            literals=(TriggerLiteral(TriggerType.EXCURSION),),
            any_of=(
                TriggerLiteral(TriggerType.REJECTION),
                TriggerLiteral(TriggerType.CLOSE),
            ),
            combination=TriggerCombination.ALL,
        ),
        targets=(
            SetupTarget(
                target_id="SETUP.JPY.TARGET.EXPRESSION_CONTINUATION",
                declared_order_index=0,
                source_ref=CANONICAL_CARD_SOURCES[2] + "#Targets",
                promotion=_promotion(
                    "SETUP.JPY.PROMOTE.EXPRESSION",
                    "L1_CONFIRMED",
                    "SETUP.JPY.CARRY_ROLE_GATE.V1",
                ),
            ),
            SetupTarget(
                target_id="SETUP.JPY.TARGET.CARRY_CONTINUATION",
                declared_order_index=1,
                source_ref=CANONICAL_CARD_SOURCES[2] + "#Targets",
            ),
        ),
        source_card_ref=CANONICAL_CARD_SOURCES[2],
        price=PriceInvalidation(
            value=Decimal("25"),
            magnitude_unit="JPY_PIPS",
            materialization=ParameterMaterialization.DECLARED,
            source_ref=CANONICAL_CARD_SOURCES[2] + "#Invalidation",
        ),
        invalidation_kinds=("PRICE", "STRUCTURAL"),
        structural=StructuralInvalidation(
            condition_id="JPY.ROLE.BASKET_VETO",
            state_ref="JPY.STRUCTURAL.BASKET_VETO",
            source_ref=CANONICAL_CARD_SOURCES[2] + "#No-go",
        ),
        evidence=(
            EvidenceReference(
                evidence_id="EV.JPY.CARRY.BASKET_RELATION.V1",
                status=EvidenceStatus.VALIDATED,
                claim_id="CL.JPY.CARRY.ROLE_RELATION",
                population_key="JPY.BASKET.ROLE",
                relationship=True,
            ),
        ),
        market_scope=("USDJPY", "AUDJPY", "EURJPY"),
        entry_zone_ref="JPY.PAIR.L1",
        layer_handoff=("CARRY_DESTINATION", "L3_TO_L2", "L1_ENTRY"),
    ),
)


def load_canonical_cards() -> tuple[CanonicalSetupCard, ...]:
    """The frozen canonical card set, in canonical id order."""

    return tuple(
        sorted(CANONICAL_SETUP_CARDS, key=lambda card: card.setup_id)
    )


@dataclass(frozen=True)
class RegistryResolution:
    """The outcome of resolving an id/version on a surface."""

    setup_id: str
    version_requested: str | None
    verdict: SetupEligibility
    code: SetupRefusalCode | None
    card: CanonicalSetupCard | None

    @property
    def resolved(self) -> bool:
        return self.card is not None


class SetupRegistry:
    """A pure, deterministic registry over canonical Setup Cards only."""

    def __init__(self, cards: Iterable[CanonicalSetupCard] = CANONICAL_SETUP_CARDS) -> None:
        self._cards: dict[str, CanonicalSetupCard] = {}
        for card in cards:
            self.register(card)

    def register(self, card: CanonicalSetupCard) -> None:
        if not isinstance(card, CanonicalSetupCard):
            raise SetupRegistryError("only a CanonicalSetupCard can be registered")
        if card.setup_id not in CANONICAL_SETUP_IDS:
            raise SetupRegistryError(
                f"card id is not canonically provisioned: {card.setup_id}"
            )
        if card.setup_id in self._cards:
            raise SetupRegistryError(f"duplicate canonical setup id: {card.setup_id}")
        self._cards[card.setup_id] = card

    # -- lookup -------------------------------------------------------------

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._cards))

    def cards(self) -> tuple[CanonicalSetupCard, ...]:
        return tuple(self._cards[key] for key in self.ids())

    def card(self, setup_id: str) -> CanonicalSetupCard:
        try:
            return self._cards[setup_id]
        except KeyError:
            raise SetupRegistryError(
                f"unknown canonical setup id: {setup_id}"
            ) from None

    def resolve(
        self,
        setup_id: str,
        version: str | None,
        surface: SetupSurface,
    ) -> RegistryResolution:
        """Resolve an explicit id/version for a surface, failing closed."""

        if not isinstance(surface, SetupSurface):
            raise SetupRegistryError("a surface uses the frozen vocabulary")
        card = self._cards.get(setup_id) if isinstance(setup_id, str) else None
        if card is None:
            return RegistryResolution(
                setup_id=str(setup_id),
                version_requested=version,
                verdict=SetupEligibility.UNRESOLVED,
                code=SetupRefusalCode.SETUP_CARD_UNRESOLVED,
                card=None,
            )
        if version is None:
            return RegistryResolution(
                setup_id=setup_id,
                version_requested=None,
                verdict=SetupEligibility.UNRESOLVED,
                code=SetupRefusalCode.SETUP_VERSION_UNRESOLVED,
                card=None,
            )
        if version != card.version:
            return RegistryResolution(
                setup_id=setup_id,
                version_requested=version,
                verdict=SetupEligibility.BLOCKED,
                code=SetupRefusalCode.SETUP_VERSION_DRIFT,
                card=None,
            )
        if card.status in REFUSED_CARD_STATUSES:
            return RegistryResolution(
                setup_id=setup_id,
                version_requested=version,
                verdict=SetupEligibility.BLOCKED,
                code=SetupRefusalCode.SETUP_NOT_CANONICAL_FOR_SURFACE,
                card=None,
            )
        if (
            card.execution_class is SetupClass.RESEARCH_ONLY
            and surface is not SetupSurface.RESEARCH
        ):
            return RegistryResolution(
                setup_id=setup_id,
                version_requested=version,
                verdict=SetupEligibility.BLOCKED,
                code=SetupRefusalCode.RESEARCH_ONLY_NOT_PRODUCTION,
                card=None,
            )
        if (
            card.execution_class is SetupClass.MANUAL_OPERATOR
            and surface is SetupSurface.AUTOMATION
        ):
            return RegistryResolution(
                setup_id=setup_id,
                version_requested=version,
                verdict=SetupEligibility.BLOCKED,
                code=SetupRefusalCode.AUTOMATION_NOT_APPROVED,
                card=None,
            )
        return RegistryResolution(
            setup_id=setup_id,
            version_requested=version,
            verdict=SetupEligibility.ELIGIBLE,
            code=None,
            card=card,
        )

    def with_status(
        self, setup_id: str, status: CardStatus
    ) -> "SetupRegistry":
        """A registry variant with one card's status replaced (gate probes)."""

        card = self.card(setup_id)
        return SetupRegistry((replace(card, status=status),))

    # -- determinism --------------------------------------------------------

    def snapshot(self) -> tuple[dict[str, object], ...]:
        return tuple(card.to_payload() for card in self.cards())

    def snapshot_hash(self) -> str:
        text = json.dumps(
            list(self.snapshot()), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
