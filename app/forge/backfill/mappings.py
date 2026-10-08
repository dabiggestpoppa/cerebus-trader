"""Explicit migration mapping registry (Book I / Bloc I.3).

Every mapping is a bounded, typed, reason-carrying registry entry. There is NO
fuzzy matching, NO string-prefix inference, NO title-based object typing, and
NO epistemic promotion: a mapping may only preserve or demote authority, and
unknown values quarantine (ACCEPTANCE clauses B and C).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.forge.canonical import EvidenceStatus, EvidenceType, ObjectType, ProductExposure


class MigrationClass(str, Enum):
    """Deterministic inventory classification (migration dimension, distinct
    from EvidenceStatus — never used as an evidence status)."""

    READY = "READY"
    MAPPING_REQUIRED = "MAPPING_REQUIRED"
    QUARANTINED = "QUARANTINED"
    MISSING_SOURCE = "MISSING_SOURCE"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    GOVERNANCE_CONTRACT = "GOVERNANCE_CONTRACT"


# The claim registry is an in-scope I.3 source artifact (ACCEPTANCE A1): it is
# inventoried and registered as an artifact with DEFINES edges to every
# registry CLAIM (ACCEPTANCE I1), but it is NOT canonicalized into a domain
# object itself (it is the rule source for claims, not a card).
CLAIM_REGISTRY_PATH = "corpus/canonical/CLAIM_REGISTRY_V1.md"


@dataclass(frozen=True)
class LegacyIdMapping:
    legacy_id: str
    canonical_id: str
    expected_type: ObjectType
    reason: str


# ---------------------------------------------------------------------------
# Legacy ID -> canonical ID (explicit; type-validated at use; no string rules)
# ---------------------------------------------------------------------------

LEGACY_ID_MAPPINGS: tuple[LegacyIdMapping, ...] = (
    LegacyIdMapping(
        "EUR.DAILY.NEWS_REKEY.V1", "MOD.EUR.DAILY.NEWS_REKEY.V1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix (I.1 _ID_PREFIX)",
    ),
    LegacyIdMapping(
        "EUR.HIGHER_ORDER.V1", "MOD.EUR.HIGHER_ORDER.V1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix",
    ),
    LegacyIdMapping(
        "EUR.WEEKLY.V1_1", "MOD.EUR.WEEKLY.V1_1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix",
    ),
    LegacyIdMapping(
        "XAU.GAME.L1_L2_L3.V1", "MOD.XAU.GAME.L1_L2_L3.V1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix",
    ),
    LegacyIdMapping(
        "BTC.TRACKER.DWM.V1", "MOD.BTC.TRACKER.DWM.V1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix",
    ),
    LegacyIdMapping(
        "CROSSASSET.FIB.RANGE_BIRTH.V1", "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix",
    ),
    LegacyIdMapping(
        "JPY.CARRY_GAME.L1_L3.V1", "MOD.JPY.CARRY_GAME.L1_L3.V1",
        ObjectType.MODEL, "legacy model id lacks frozen MOD prefix",
    ),
    LegacyIdMapping(
        "SETUP.XAU.QUARTER_ZONE.V1", "SET.XAU.QUARTER_ZONE.V1",
        ObjectType.SETUP, "SETUP is not a canonical prefix; frozen setup prefix is SET",
    ),
    LegacyIdMapping(
        "SETUP.FIB.REKEY.V1", "SET.FIB.REKEY.V1",
        ObjectType.SETUP, "SETUP is not a canonical prefix; frozen setup prefix is SET",
    ),
    LegacyIdMapping(
        "SETUP.JPY.CARRY_ROLE_GATE.V1", "SET.JPY.CARRY_ROLE_GATE.V1",
        ObjectType.SETUP, "SETUP is not a canonical prefix; frozen setup prefix is SET",
    ),
)

# Evidence/claim ids already parse as canonical; recorded as validated
# passthrough, not string-matched.
_EVIDENCE_PASSTHROUGH: tuple[str, ...] = (
    "EV.EUR.DAILY.PHASE1_TIERS.V1",
    "EV.EUR.HO.D3_DIRECTION.V1",
    "EV.EUR.HO.M1_RANGE_CORR.V1",
    "EV.EUR.HO.UNFINISHED_M3.V1",
    "EV.EUR.DAILY.NEWS_AUC.V1",
    "EV.EUR.WEEKLY.TIER_RANGE.V1",
    "EV.XAU.PROMOTION.68_80.V1",
    "EV.XAU.PROMOTION.120_132.V1",
    "EV.JPY.CARRY.BASKET_RELATION.V1",
    "EV.FIB.R11.ANCHOR_OVERGEN.V1",
)

_CLAIM_PASSTHROUGH: tuple[str, ...] = (
    "CL.EUR.HO.D3_DIRECTION",
    "CL.EUR.HO.UNFINISHED_M3",
    "CL.EUR.HO.M1_RANGE_CORR",
    "CL.EUR.DAILY.TIER_CALIBRATION",
    "CL.EUR.DAILY.NEWS_INCREMENT",
    "CL.EUR.WEEKLY.TIER_RANGE",
    "CL.XAU.PROMOTION.68_80",
    "CL.XAU.PROMOTION.120_132",
    "CL.JPY.CARRY.ROLE_RELATION",
    "CL.FIB.R11.GENERATOR_FAILURE",
)

_LEGACY_ID_INDEX: dict[str, LegacyIdMapping] = {
    m.legacy_id: m for m in LEGACY_ID_MAPPINGS
}

_CANONICAL_TARGETS: dict[str, str] = {}
for _m in LEGACY_ID_MAPPINGS:
    _prior = _CANONICAL_TARGETS.get(_m.canonical_id)
    if _prior is not None and _prior != _m.legacy_id:
        raise ValueError(
            f"two legacy ids map to {_m.canonical_id}: {_prior} and {_m.legacy_id}"
        )
    _CANONICAL_TARGETS[_m.canonical_id] = _m.legacy_id


def resolve_canonical_id(legacy_id: str, expected_type: ObjectType) -> str:
    """Resolve a legacy id to its canonical id via the explicit registry.

    Raises ValueError for unknown legacy ids or type mismatches — never
    fuzzy-maps and never infers the object type from the id or title.
    """
    mapping = _LEGACY_ID_INDEX.get(legacy_id)
    if mapping is None:
        # Passthrough families: the id must already be a canonical id of the
        # expected type (validated, not assumed).
        from app.forge.canonical import CanonicalId

        parsed = CanonicalId.parse(legacy_id)  # raises on malformed
        if parsed.object_type is not expected_type:
            raise ValueError(
                f"legacy id {legacy_id} does not have expected type {expected_type.value}"
            )
        return legacy_id
    if mapping.expected_type is not expected_type:
        raise ValueError(
            f"mapping for {legacy_id} expects {mapping.expected_type.value}, "
            f"caller expected {expected_type.value}"
        )
    return mapping.canonical_id


# ---------------------------------------------------------------------------
# Legacy status -> EvidenceStatus (explicit; preserve-or-demote only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StatusMapping:
    legacy_status: str
    canonical_status: EvidenceStatus
    reason: str
    metadata_flags: tuple[tuple[str, object], ...] = ()


STATUS_MAPPINGS: tuple[StatusMapping, ...] = (
    StatusMapping("VALIDATED", EvidenceStatus.VALIDATED, "passthrough"),
    StatusMapping("FORWARD_OOS", EvidenceStatus.FORWARD_OOS, "passthrough"),
    StatusMapping("CANDIDATE", EvidenceStatus.CANDIDATE, "passthrough"),
    StatusMapping(
        "VALIDATED_RESEARCH", EvidenceStatus.VALIDATED,
        "validated within recovered research sample; research qualifier preserved "
        "as metadata, never upgraded to forward-OOS",
        (("research_sample", True),),
    ),
    StatusMapping(
        "VALIDATED_SMALL_N", EvidenceStatus.VALIDATED,
        "validated in source sample; small-N governance preserved as metadata",
        (("small_n", True),),
    ),
    StatusMapping(
        "VALIDATED_RELATIONSHIP", EvidenceStatus.VALIDATED,
        "relationship statistic validated; never a trade win rate",
        (("relationship_statistic", True),),
    ),
    StatusMapping(
        "RESEARCH_FLAG_SMALL_N", EvidenceStatus.RESEARCH_FLAG,
        "small-N research flag stays a research flag despite high observed rate",
        (("small_n", True),),
    ),
    StatusMapping(
        "NEGATIVE_EVIDENCE", EvidenceStatus.FALSIFIED,
        "the approach this negative card concerns is falsified; evidence_type "
        "remains NEGATIVE_EVIDENCE so the negative dimension survives first-class",
    ),
    StatusMapping(
        "CANONICALIZATION_CANDIDATE", EvidenceStatus.CANDIDATE,
        "canonicalization-stage candidate; no promotion",
    ),
    StatusMapping(
        "CORE_CANDIDATE", EvidenceStatus.CANDIDATE, "candidate; no promotion",
    ),
    StatusMapping(
        "SCIENTIFIC_CORE_CANDIDATE", EvidenceStatus.CANDIDATE,
        "scientific core candidate; no promotion",
    ),
    StatusMapping(
        "RESEARCH_OPERATOR_CANDIDATE", EvidenceStatus.RESEARCH_FLAG,
        "operator-research candidate stays research-gated until R15 eligibility "
        "is materialized",
    ),
    StatusMapping(
        "CANONICAL_FROZEN_FAMILY", EvidenceStatus.DESCRIPTIVE,
        "family-level frozen architecture; per-claim epistemic status lives in "
        "Evidence Cards; frozen fact preserved as metadata, NOT promoted",
        (("frozen_family", True),),
    ),
    StatusMapping(
        "ACTIVE_RESEARCH_IMPLEMENTED", EvidenceStatus.RESEARCH_FLAG,
        "active research implemented as indicator; implementation is not "
        "validation",
        (("implemented", True),),
    ),
    StatusMapping(
        "MODERN_RESEARCH_FRAMEWORK", EvidenceStatus.RESEARCH_FLAG,
        "research framework; not validated",
    ),
)

_STATUS_INDEX: dict[str, StatusMapping] = {m.legacy_status: m for m in STATUS_MAPPINGS}

# Promotion boundary guard: statuses that must never be REACHED by mapping a
# lower-authority legacy status. VALIDATED is reachable only from legacy
# statuses already asserting validation.
_PROMOTION_SOURCES_VALIDATED = {
    "VALIDATED", "VALIDATED_RESEARCH", "VALIDATED_SMALL_N", "VALIDATED_RELATIONSHIP",
}
for _m in STATUS_MAPPINGS:
    if _m.canonical_status is EvidenceStatus.VALIDATED and (
        _m.legacy_status not in _PROMOTION_SOURCES_VALIDATED
    ):
        raise ValueError(f"status mapping promotes authority: {_m.legacy_status}")


def resolve_status(
    legacy_status: str,
) -> tuple[EvidenceStatus, StatusMapping] | None:
    """Resolve a legacy status to (canonical status, mapping); None means
    unknown ⇒ quarantine (no coercion)."""
    if legacy_status is None:
        return None
    mapping = _STATUS_INDEX.get(legacy_status.strip())
    return None if mapping is None else (mapping.canonical_status, mapping)


# ---------------------------------------------------------------------------
# Legacy evidence type -> EvidenceType
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceTypeMapping:
    legacy_type: str
    canonical_type: EvidenceType
    reason: str
    metadata_flags: tuple[tuple[str, object], ...] = ()


EVIDENCE_TYPE_MAPPINGS: tuple[EvidenceTypeMapping, ...] = (
    EvidenceTypeMapping("SCIENTIFIC_RETEST", EvidenceType.SCIENTIFIC_RETEST, "passthrough"),
    EvidenceTypeMapping(
        "SCIENTIFIC_RETEST + FORWARD_OOS", EvidenceType.FORWARD_OOS,
        "compound collapses to its strongest frozen member; historical component "
        "preserved as metadata",
        (("historical_component", "SCIENTIFIC_RETEST"),),
    ),
    EvidenceTypeMapping(
        "SCIENTIFIC_RESEARCH_RESULT", EvidenceType.SCIENTIFIC_RETEST,
        "recovered scientific research result; scientific-retest class",
    ),
    EvidenceTypeMapping(
        "RAW_RESEARCH_LEDGER", EvidenceType.RAW_BACKTEST,
        "raw research/backtest ledger class",
    ),
    EvidenceTypeMapping(
        "OPERATOR_RESEARCH", EvidenceType.HISTORICAL_REPORT,
        "operator research record; NOT live trade-log proof",
        (("operator_research", True),),
    ),
)

_EVIDENCE_TYPE_INDEX = {m.legacy_type: m for m in EVIDENCE_TYPE_MAPPINGS}

# Per-card explicit override (the corpus's negative-evidence card).
EVIDENCE_TYPE_OVERRIDES: dict[str, EvidenceTypeMapping] = {
    "EV.FIB.R11.ANCHOR_OVERGEN.V1": EvidenceTypeMapping(
        "SCIENTIFIC_RESEARCH_RESULT", EvidenceType.NEGATIVE_EVIDENCE,
        "explicit per-card override: this IS the corpus negative-evidence card; "
        "frozen NEGATIVE_EVIDENCE type preserves the negative dimension",
    ),
}


def resolve_evidence_type(
    legacy_type: str, evidence_id: str
) -> tuple[EvidenceType, EvidenceTypeMapping] | None:
    mapping = EVIDENCE_TYPE_OVERRIDES.get(evidence_id)
    if mapping is None:
        mapping = _EVIDENCE_TYPE_INDEX.get(legacy_type.strip())
    return None if mapping is None else (mapping.canonical_type, mapping)


# ---------------------------------------------------------------------------
# Layer normalization (explicit legacy table; detail preserved)
# ---------------------------------------------------------------------------

LAYER_MAPPINGS: dict[str, tuple[str, str | None]] = {
    # legacy layer string -> (canonical Layer value, preserved detail or None)
    "L1": ("L1", None),
    "L2": ("L2", None),
    "L3": ("L3", None),
    "CROSS_LAYER": ("CROSS_LAYER", None),
    "L1 / local distribution-execution context": ("L1", "local distribution-execution context"),
    "L3 + cross-layer routing": ("L3", "cross-layer routing"),
    "CROSS_LAYER_CONTEXT": ("CROSS_LAYER", "context"),
    "L1_L2": ("CROSS_LAYER", "L1_L2"),
    "L1_L3": ("CROSS_LAYER", "L1_L3"),
    "L1_L2_L3": ("CROSS_LAYER", "L1_L2_L3"),
}


def resolve_layer(legacy_layer: str) -> tuple[str, str | None] | None:
    legacy_layer = legacy_layer.strip()
    if legacy_layer in LAYER_MAPPINGS:
        return LAYER_MAPPINGS[legacy_layer]
    # Deterministic leading-token rule for compound strings (recorded, not fuzzy).
    token = legacy_layer.split()[0].rstrip("/")
    if token in LAYER_MAPPINGS:
        return LAYER_MAPPINGS[token]
    return None


# ---------------------------------------------------------------------------
# Exposure stamping for evidence cards (frozen Product Exposure Rules)
# ---------------------------------------------------------------------------

EVIDENCE_EXPOSURE: dict[str, ProductExposure] = {
    "EV.EUR.DAILY.PHASE1_TIERS.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.EUR.HO.D3_DIRECTION.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.EUR.HO.M1_RANGE_CORR.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.EUR.HO.UNFINISHED_M3.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.EUR.DAILY.NEWS_AUC.V1": ProductExposure.RESEARCH_LAB,
    "EV.EUR.WEEKLY.TIER_RANGE.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.XAU.PROMOTION.68_80.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.XAU.PROMOTION.120_132.V1": ProductExposure.RESEARCH_LAB,
    "EV.JPY.CARRY.BASKET_RELATION.V1": ProductExposure.SUBSCRIBER_MODEL,
    "EV.FIB.R11.ANCHOR_OVERGEN.V1": ProductExposure.RESEARCH_LAB,
}
_EVIDENCE_EXPOSURE_REASON = (
    "validated evidence-backed statistics -> SUBSCRIBER_MODEL; candidate / "
    "small-N-flag / negative-evidence research material -> RESEARCH_LAB "
    "(PRODUCT_EXPOSURE_RULES_V1)"
)

# ---------------------------------------------------------------------------
# Model -> evidence links (derived from the frozen Claim Registry; model cards
# historically carried no evidence_card_ids field)
# ---------------------------------------------------------------------------

MODEL_EVIDENCE_LINKS: dict[str, tuple[str, ...]] = {
    "MOD.EUR.HIGHER_ORDER.V1": (
        "EV.EUR.HO.D3_DIRECTION.V1",
        "EV.EUR.HO.M1_RANGE_CORR.V1",
        "EV.EUR.HO.UNFINISHED_M3.V1",
    ),
    "MOD.EUR.DAILY.NEWS_REKEY.V1": (
        "EV.EUR.DAILY.PHASE1_TIERS.V1",
        "EV.EUR.DAILY.NEWS_AUC.V1",
    ),
    "MOD.EUR.WEEKLY.V1_1": ("EV.EUR.WEEKLY.TIER_RANGE.V1",),
    "MOD.XAU.GAME.L1_L2_L3.V1": (
        "EV.XAU.PROMOTION.68_80.V1",
        "EV.XAU.PROMOTION.120_132.V1",
    ),
    "MOD.JPY.CARRY_GAME.L1_L3.V1": ("EV.JPY.CARRY.BASKET_RELATION.V1",),
    "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1": ("EV.FIB.R11.ANCHOR_OVERGEN.V1",),
    "MOD.BTC.TRACKER.DWM.V1": (),  # honest gap: no evidence card exists
}

# Registry claim -> model + evidence (CLAIM_REGISTRY_V1 table, verbatim).
REGISTRY_CLAIMS: tuple[dict[str, str], ...] = (
    {
        "claim_id": "CL.EUR.HO.D3_DIRECTION",
        "model": "MOD.EUR.HIGHER_ORDER.V1",
        "claim": "D3 state informs eventual quarter close direction",
        "evidence": "EV.EUR.HO.D3_DIRECTION.V1",
        "status": "FORWARD_OOS",
        "layer": "L3",
    },
    {
        "claim_id": "CL.EUR.HO.UNFINISHED_M3",
        "model": "MOD.EUR.HIGHER_ORDER.V1",
        "claim": "unfinished side often completes in M3",
        "evidence": "EV.EUR.HO.UNFINISHED_M3.V1",
        "status": "FORWARD_OOS",
        "layer": "L3",
    },
    {
        "claim_id": "CL.EUR.HO.M1_RANGE_CORR",
        "model": "MOD.EUR.HIGHER_ORDER.V1",
        "claim": "M1 range magnitude informs final quarter range magnitude",
        "evidence": "EV.EUR.HO.M1_RANGE_CORR.V1",
        "status": "VALIDATED",
        "layer": "L3",
    },
    {
        "claim_id": "CL.EUR.DAILY.TIER_CALIBRATION",
        "model": "MOD.EUR.DAILY.NEWS_REKEY.V1",
        "claim": "Phase1 Asian-range tiers calibrate daily distribution",
        "evidence": "EV.EUR.DAILY.PHASE1_TIERS.V1",
        "status": "VALIDATED",
        "layer": "L1",
    },
    {
        "claim_id": "CL.EUR.DAILY.NEWS_INCREMENT",
        "model": "MOD.EUR.DAILY.NEWS_REKEY.V1",
        "claim": "residual event field adds incremental classification information",
        "evidence": "EV.EUR.DAILY.NEWS_AUC.V1",
        "status": "CANDIDATE",
        "layer": "L1",
    },
    {
        "claim_id": "CL.EUR.WEEKLY.TIER_RANGE",
        "model": "MOD.EUR.WEEKLY.V1_1",
        "claim": "weekly tier conditions final range distribution",
        "evidence": "EV.EUR.WEEKLY.TIER_RANGE.V1",
        "status": "VALIDATED_RESEARCH",
        "layer": "L2",
    },
    {
        "claim_id": "CL.XAU.PROMOTION.68_80",
        "model": "MOD.XAU.GAME.L1_L2_L3.V1",
        "claim": "68+8h state promotes path toward80",
        "evidence": "EV.XAU.PROMOTION.68_80.V1",
        "status": "VALIDATED_SMALL_N",
        "layer": "L2",
    },
    {
        "claim_id": "CL.XAU.PROMOTION.120_132",
        "model": "MOD.XAU.GAME.L1_L2_L3.V1",
        "claim": "120+8h state promotes path toward132",
        "evidence": "EV.XAU.PROMOTION.120_132.V1",
        "status": "RESEARCH_FLAG_SMALL_N",
        "layer": "L2",
    },
    {
        "claim_id": "CL.JPY.CARRY.ROLE_RELATION",
        "model": "MOD.JPY.CARRY_GAME.L1_L3.V1",
        "claim": "primary pair agreement and EURJPY confirmation support role architecture",
        "evidence": "EV.JPY.CARRY.BASKET_RELATION.V1",
        "status": "VALIDATED_RELATIONSHIP",
        "layer": "CROSS_LAYER",
    },
    {
        "claim_id": "CL.FIB.R11.GENERATOR_FAILURE",
        "model": "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1",
        "claim": "generic local pivot generator overproduced anchors",
        "evidence": "EV.FIB.R11.ANCHOR_OVERGEN.V1",
        "status": "NEGATIVE_EVIDENCE",
        "layer": "L1_L2",
    },
)

# ---------------------------------------------------------------------------
# Named implementation / support / visualization artifacts (in-repo paths the
# cards themselves name). Registered only if present; else MISSING_SOURCE.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NamedArtifactEdge:
    path: str
    source_class: str
    relation: str  # ProvenanceRelation value
    target_object: str
    note: str


NAMED_ARTIFACT_EDGES: tuple[NamedArtifactEdge, ...] = (
    NamedArtifactEdge(
        "corpus/research/eur/daily_range_tracker/PHASE_1_LEDGER.md", "MARKDOWN",
        "SUPPORTS", "EV.EUR.DAILY.PHASE1_TIERS.V1",
        "named as source_artifact by the evidence card",
    ),
    NamedArtifactEdge(
        "corpus/indicators/eur/CEREBUS_Daily_News_Rekey_Engine_V1_1_P90_MERGED_FIX1.pine",
        "PINE", "IMPLEMENTS", "MOD.EUR.DAILY.NEWS_REKEY.V1",
        "named implementation in model card",
    ),
    NamedArtifactEdge(
        "corpus/indicators/xau/CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine",
        "PINE", "IMPLEMENTS", "MOD.XAU.GAME.L1_L2_L3.V1",
        "named implementation in model card",
    ),
    NamedArtifactEdge(
        "corpus/indicators/btc/CEREBUS_BTC_Daily_Weekly_Monthly_Tracker_V1.pine",
        "PINE", "IMPLEMENTS", "MOD.BTC.TRACKER.DWM.V1",
        "named implementation in model card",
    ),
    NamedArtifactEdge(
        "corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1.pine",
        "PINE", "VISUALIZES", "MOD.EUR.HIGHER_ORDER.V1",
        "visualizer lineage; visual is never empirical proof",
    ),
    NamedArtifactEdge(
        "corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1_2.pine",
        "PINE", "VISUALIZES", "MOD.EUR.HIGHER_ORDER.V1",
        "visualizer lineage; visual is never empirical proof",
    ),
    NamedArtifactEdge(
        "corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1_6_1_COMPILE_FIX.pine",
        "PINE", "VISUALIZES", "MOD.EUR.HIGHER_ORDER.V1",
        "visualizer lineage; visual is never empirical proof",
    ),
    NamedArtifactEdge(
        "corpus/indicators/eur/CEREBUS_EUR_QUARTER_MONTH_TRACKER_V1_6_4_STYLE_COLORS.pine",
        "PINE", "VISUALIZES", "MOD.EUR.HIGHER_ORDER.V1",
        "visualizer lineage; visual is never empirical proof",
    ),
)

# Honest NOT_SPECIFIED marker for structured dimensions the historical card
# format never carried (uncertainty preserved, nothing fabricated).
NOT_SPECIFIED = "NOT_SPECIFIED_IN_SOURCE"
