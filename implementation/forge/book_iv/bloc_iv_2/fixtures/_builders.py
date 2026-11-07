"""Deterministic builders shared by IV.2 tests and fixture generation."""

from __future__ import annotations

from dataclasses import replace

from app.forge.ask_cerebus.interpreter.entities import EntityRef
from app.forge.ask_cerebus.interpreter.enums import (
    AmbiguityReason,
    Depth,
    EntityKind,
    Intent,
    PlanConfidence,
    TimeScope,
)
from app.forge.ask_cerebus.interpreter.plan import AskCerebusQueryPlan
from app.forge.ask_cerebus.retrieval import (
    AskCerebusRetrievalService,
    DeterministicFakeSemanticIndex,
    SnapshotContext,
    SemanticCandidate,
)
from app.forge.canonical import (
    CanonicalReference,
    ClaimIdentity,
    EvidenceStatus,
    Layer as CanonicalLayer,
    ObjectType,
    ProductExposure,
)
from app.forge.identity import ForgePrincipal
from app.forge.model_runtime.contract import Layer
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
)
from app.forge.policy import (
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_MODEL_READ_OPERATOR,
    AuthorizationContext,
)
from app.forge.retrieval import (
    IndexBuildMode,
    RetrievalIndex,
    build_index as build_retrieval_index,
)

ARTIFACT_READ = "sha256:" + "a" * 64
ARTIFACT_SECOND = "sha256:" + "b" * 64


def identity(market: str = "XAUUSD", event: str = "close outside band") -> ClaimIdentity:
    return ClaimIdentity(
        market=market,
        event_definition=event,
        conditioning_event="retest",
        clock_origin="NY",
        horizon="D1",
        tolerance="5",
        eligibility="operator",
        implementation_semantics="v1",
    )


def artifact(artifact_id: str, locator: str, content: str = ARTIFACT_READ) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=artifact_id,
        source_class="MARKDOWN",
        title=artifact_id,
        locator=locator,
        content_identity=content,
        source_state="READ",
    )


def record(
    object_id: str,
    object_type: ObjectType,
    title: str,
    *,
    status: EvidenceStatus = EvidenceStatus.CANDIDATE,
    exposure: ProductExposure = ProductExposure.SUBSCRIBER_MODEL,
    layer: CanonicalLayer = CanonicalLayer.NONE,
    references=(),
    metadata=None,
    claim_identity=None,
) -> CanonicalObjectRecord:
    return CanonicalObjectRecord(
        canonical_id=object_id,
        object_type=object_type,
        title=title,
        version="V1",
        status=status,
        exposure=exposure,
        layer=layer,
        references=tuple(references),
        metadata=metadata or {},
        claim_identity=claim_identity,
    )


def _ref(target: str, relation: str) -> CanonicalReference:
    return CanonicalReference(target_id=target, relation=relation)


def default_artifacts() -> tuple[ArtifactRecord, ...]:
    return (
        artifact("ART.MARKDOWN." + "A" * 24, "corpus/research/xau.md"),
        artifact("ART.MARKDOWN." + "B" * 24, "corpus/research/btc.md", ARTIFACT_SECOND),
        artifact("ART.MARKDOWN." + "C" * 24, "corpus/research/fib.md", ARTIFACT_SECOND),
    )


def default_records() -> tuple[CanonicalObjectRecord, ...]:
    ev_supported = record(
        "EV.XAU.SUPPORTED.V1", ObjectType.EVIDENCE, "Supported XAU evidence",
        status=EvidenceStatus.VALIDATED, exposure=ProductExposure.RESEARCH_LAB,
        metadata={"card": {"exact_claim": "XAU promotion 68 to 80", "market": "XAUUSD"}},
    )
    ev_conflict = record(
        "EV.XAU.CONFLICT.V1", ObjectType.EVIDENCE, "Conflicting XAU evidence",
        status=EvidenceStatus.VALIDATED, exposure=ProductExposure.RESEARCH_LAB,
        metadata={"card": {"exact_claim": "XAU promotion 72 to 80", "market": "XAUUSD"}},
    )
    ev_negative = record(
        "EV.FIB.NEGATIVE.V1", ObjectType.EVIDENCE, "Fib failed hypothesis",
        status=EvidenceStatus.FALSIFIED, exposure=ProductExposure.RESEARCH_LAB,
        metadata={"card": {"exact_claim": "Fib anchor overgeneralized", "market": "CROSSASSET"}},
    )
    claims = (
        record(
            "CL.XAU.GAME.SUPPORTED.V1", ObjectType.CLAIM, "Supported claim",
            status=EvidenceStatus.VALIDATED, exposure=ProductExposure.RESEARCH_LAB,
            references=(_ref("EV.XAU.SUPPORTED.V1", "supported_by"),),
            metadata={"claim_text": "68 percent promotion", "result": "68%"},
            claim_identity=identity(),
        ),
        record(
            "CL.XAU.GAME.NOEV.V1", ObjectType.CLAIM, "No evidence claim",
            status=EvidenceStatus.RESEARCH_FLAG, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"claim_text": "unverified 99 percent", "result": "99%"},
            claim_identity=identity(event="no evidence event"),
        ),
        record(
            "CL.XAU.GAME.CONFLICT.V1", ObjectType.CLAIM, "Conflicting claim",
            status=EvidenceStatus.VALIDATED, exposure=ProductExposure.RESEARCH_LAB,
            references=(_ref("EV.XAU.CONFLICT.V1", "supported_by"),),
            metadata={"claim_text": "72 percent promotion", "result": "72%"},
            claim_identity=identity(),
        ),
        record(
            "CL.XAU.GAME.INCOMPARABLE.V1", ObjectType.CLAIM, "Incomparable claim",
            status=EvidenceStatus.RESEARCH_FLAG, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"claim_text": "different population", "result": "41%"},
            claim_identity=identity(event="different event"),
        ),
        record(
            "CL.BTC.GAME.V1", ObjectType.CLAIM, "BTC game claim",
            status=EvidenceStatus.CANDIDATE, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"claim_text": "btc game research"}, claim_identity=identity("BTCUSD"),
        ),
        record(
            "CL.BTC.TRACKER.V1", ObjectType.CLAIM, "BTC tracker claim",
            status=EvidenceStatus.CANDIDATE, exposure=ProductExposure.SUBSCRIBER_MODEL,
            metadata={"claim_text": "btc tracker current"}, claim_identity=identity("BTCUSD", "tracker"),
        ),
        record(
            "CL.P90.V1", ObjectType.CLAIM, "P90 claim",
            status=EvidenceStatus.HISTORICAL, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"claim_text": "historical p90"}, claim_identity=identity("XAUUSD", "p90"),
        ),
        record(
            "CL.FIB.NEGATIVE.V1", ObjectType.CLAIM, "Fib negative claim",
            status=EvidenceStatus.FALSIFIED, exposure=ProductExposure.RESEARCH_LAB,
            references=(_ref("EV.FIB.NEGATIVE.V1", "supported_by"),),
            metadata={"claim_text": "fib failed"}, claim_identity=identity("CROSSASSET", "fib"),
        ),
    )
    models = (
        record(
            "MOD.XAU.GAME.V1", ObjectType.MODEL, "Gold Game", layer=CanonicalLayer.L3,
            references=(_ref("CL.XAU.GAME.SUPPORTED.V1", "has_claim"),),
            metadata={"card": {"purpose": "Gold game model", "source_generation": "XAU.GAME"}},
        ),
        record(
            "MOD.XAU.GAME_V2.V1", ObjectType.MODEL, "Gold Game V2", layer=CanonicalLayer.L3,
            metadata={"card": {"purpose": "Gold game V2"}},
        ),
        record(
            "MOD.XAU.NOEV.V1", ObjectType.MODEL, "Gold no evidence",
            references=(_ref("CL.XAU.GAME.NOEV.V1", "has_claim"),),
            metadata={"card": {"purpose": "No evidence model"}},
        ),
        record(
            "MOD.XAU.COMPARE.V1", ObjectType.MODEL, "Gold comparison",
            references=(
                _ref("CL.XAU.GAME.SUPPORTED.V1", "has_claim"),
                _ref("CL.XAU.GAME.CONFLICT.V1", "has_claim"),
                _ref("CL.XAU.GAME.INCOMPARABLE.V1", "has_claim"),
            ),
            metadata={"card": {"purpose": "Comparison model"}},
        ),
        record(
            "MOD.XAU.CONFLICT.V1", ObjectType.MODEL, "Gold matched-identity comparison",
            references=(
                _ref("CL.XAU.GAME.SUPPORTED.V1", "has_claim"),
                _ref("CL.XAU.GAME.CONFLICT.V1", "has_claim"),
            ),
            metadata={"card": {"purpose": "Matched-identity comparison"}},
        ),
        record(
            "MOD.XAU.INCOMPARABLE.V1", ObjectType.MODEL, "Gold different-identity comparison",
            references=(
                _ref("CL.XAU.GAME.SUPPORTED.V1", "has_claim"),
                _ref("CL.XAU.GAME.INCOMPARABLE.V1", "has_claim"),
            ),
            metadata={"card": {"purpose": "Different-identity comparison"}},
        ),
        record(
            "MOD.BTC.GAME.V1", ObjectType.MODEL, "BTC Game",
            exposure=ProductExposure.RESEARCH_LAB,
            references=(_ref("CL.BTC.GAME.V1", "has_claim"),),
            metadata={"card": {"purpose": "BTC game research", "source_generation": "RESEARCH_ARTIFACT"}},
        ),
        record(
            "MOD.BTC.TRACKER.V1", ObjectType.MODEL, "BTC Tracker",
            references=(_ref("CL.BTC.TRACKER.V1", "has_claim"),),
            metadata={"card": {"purpose": "BTC tracker"}},
        ),
        record(
            "MOD.P90.V1", ObjectType.MODEL, "P90 historical",
            status=EvidenceStatus.HISTORICAL, exposure=ProductExposure.RESEARCH_LAB,
            references=(_ref("CL.P90.V1", "has_claim"),),
            metadata={"card": {"purpose": "P90 original", "source_generation": "P90.ORIGINAL"}},
        ),
        record(
            "MOD.ST.MANUAL.V1", ObjectType.MODEL, "ST manual",
            status=EvidenceStatus.HISTORICAL, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"card": {"purpose": "ST manual", "source_generation": "ST.MANUAL"}},
        ),
        record(
            "MOD.BASE80.V1", ObjectType.MODEL, "Base80",
            status=EvidenceStatus.HISTORICAL, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"card": {"purpose": "Base80", "source_generation": "BASE80"}},
        ),
        record(
            "MOD.MARKOV.LEGACY.V1", ObjectType.MODEL, "Markov legacy",
            status=EvidenceStatus.HISTORICAL, exposure=ProductExposure.RESEARCH_LAB,
            metadata={"card": {"purpose": "Markov legacy", "source_generation": "MARKOV.LEGACY"}},
        ),
        record(
            "MOD.FIB.RANGE_BIRTH.V1", ObjectType.MODEL, "Fib range birth",
            status=EvidenceStatus.RESEARCH_FLAG, exposure=ProductExposure.RESEARCH_LAB,
            references=(_ref("CL.FIB.NEGATIVE.V1", "has_claim"),),
            metadata={"card": {"purpose": "Fib", "source_generation": "FIB.R15"}},
        ),
        record(
            "MOD.XAU.SECRET.V1", ObjectType.MODEL, "Internal secret",
            exposure=ProductExposure.INTERNAL_METHOD,
            metadata={"card": {"purpose": "internal method text"}},
        ),
        record(
            "MOD.LEGACY.SUPERSEDED.V1", ObjectType.MODEL, "Superseded model",
            status=EvidenceStatus.SUPERSEDED,
            references=(_ref("MOD.XAU.GAME.V1", "supersedes"),),
            metadata={"card": {"purpose": "superseded"}},
        ),
        record(
            "MOD.PARKED.V1", ObjectType.MODEL, "Parked model",
            status=EvidenceStatus.PARKED,
            metadata={"card": {"purpose": "parked"}},
        ),
        record(
            "SET.XAU.QUARTER_ZONE.V1", ObjectType.SETUP, "XAU quarter zone",
            layer=CanonicalLayer.L1, exposure=ProductExposure.OPERATOR_ONLY,
            metadata={"card": {"purpose": "XAU setup", "market_scope": ["XAUUSD"]}},
        ),
        record(
            "SET.FIB.REKEY.V1", ObjectType.SETUP, "Fib rekey",
            exposure=ProductExposure.RESEARCH_LAB,
            metadata={"card": {"purpose": "Fib research", "market_scope": ["CROSSASSET"]}},
        ),
        record(
            "SET.JPY.CARRY_ROLE_GATE.V1", ObjectType.SETUP, "JPY carry",
            exposure=ProductExposure.OPERATOR_ONLY,
            metadata={"card": {"purpose": "JPY manual", "market_scope": ["USDJPY", "AUDJPY", "EURJPY"]}},
        ),
        record(
            "TERM.CONSTRAINT_DEFICIT", ObjectType.TERM, "Constraint Deficit",
            exposure=ProductExposure.PUBLIC_TEACHING,
            metadata={"card": {"purpose": "historical term"}},
        ),
    )
    return (ev_supported, ev_conflict, ev_negative) + claims + models


def build_index(*, nogo: bool = False) -> RetrievalIndex:
    records = list(default_records())
    if nogo:
        records = [
            replace(rec, status=EvidenceStatus.NO_GO)
            if rec.canonical_id == "SET.XAU.QUARTER_ZONE.V1"
            else rec
            for rec in records
        ]
    gateway = InMemoryPersistenceGateway()
    with gateway.transaction():
        for rec in default_artifacts():
            gateway.create_artifact(rec)
        for rec in records:
            gateway.create_object(rec)
        for artifact_id, object_id, relation in (
            ("ART.MARKDOWN." + "A" * 24, "EV.XAU.SUPPORTED.V1", "SUPPORTS"),
            ("ART.MARKDOWN." + "B" * 24, "EV.XAU.CONFLICT.V1", "SUPPORTS"),
            ("ART.MARKDOWN." + "C" * 24, "EV.FIB.NEGATIVE.V1", "SUPPORTS"),
            ("ART.MARKDOWN." + "C" * 24, "CL.FIB.NEGATIVE.V1", "SUPPORTS"),
        ):
            gateway.add_provenance_edge(
                ProvenanceEdgeRecord(artifact_id, object_id, relation)
            )
    index = RetrievalIndex()
    build_retrieval_index(gateway, index=index, mode=IndexBuildMode.APPLY)
    return index


def plan(
    *,
    model_ids: tuple[str, ...] = (),
    setup_ids: tuple[str, ...] = (),
    intent: Intent = Intent.DEFINITION,
    scope: TimeScope = TimeScope.GENERAL,
    depth: Depth = Depth.OPERATOR,
    evidence: bool = False,
    entities=(),
    ambiguities=(),
) -> AskCerebusQueryPlan:
    entities = tuple(entities) or tuple(
        EntityRef(EntityKind.MODEL, model, model) for model in model_ids
    ) + tuple(
        EntityRef(EntityKind.SETUP, setup, setup) for setup in setup_ids
    )
    return AskCerebusQueryPlan(
        intent=intent,
        entities=entities,
        model_ids=model_ids,
        setup_ids=setup_ids,
        market="XAUUSD" if any("XAU" in m for m in model_ids) else None,
        layer=Layer.L3,
        time_scope=scope,
        requested_depth=depth,
        effective_depth=depth,
        requires_live_intelligence=scope is TimeScope.CURRENT,
        requires_evidence=evidence,
        requires_lineage=any(token in ("P90", "MARKOV", "FIB") for token in model_ids),
        requires_setup_context=bool(setup_ids),
        actionable=intent in (Intent.SETUP_CONTEXT, Intent.CURRENT_STATE),
        requested_fields=("state",) if scope is TimeScope.CURRENT else ("definition",),
        confidence=PlanConfidence.CERTAIN,
        ambiguities=tuple(ambiguities),
    ).finalized()


def operator() -> ForgePrincipal:
    return ForgePrincipal(
        authenticated=True, forge_user_id="user-iv2", session_id="session-iv2"
    )


def operator_context() -> AuthorizationContext:
    return AuthorizationContext.of(
        CAPABILITY_MODEL_READ_OPERATOR, CAPABILITY_EVIDENCE_READ_RESEARCH
    )


def public_context() -> AuthorizationContext:
    return AuthorizationContext.empty()


def snapshot_context(*, current: bool = True, complete: bool = True) -> SnapshotContext:
    return SnapshotContext(
        instrument_id="XAUUSD",
        model_id="XAU.GAME",
        model_version="V1" if complete else "",
        as_of="2026-01-01T00:00:00Z" if complete else "",
        data_cutoff="2026-01-01T00:00:00Z" if complete else "",
        calculation_version="1.0" if complete else "",
        layer=Layer.L3,
        provider_configured=False,
        quality="NOT_CONFIGURED",
    )


def service(
    *,
    semantic=None,
    index: RetrievalIndex | None = None,
) -> AskCerebusRetrievalService:
    return AskCerebusRetrievalService(
        index or build_index(),
        semantic=semantic,
    )


def fake_semantic(
    object_id: str = "MOD.XAU.GAME.V1",
    text: str = "supporting context",
    score: float = 0.9,
) -> DeterministicFakeSemanticIndex:
    return DeterministicFakeSemanticIndex(
        (SemanticCandidate(object_id, text, score),)
    )


__all__ = [
    "build_index",
    "plan",
    "operator",
    "operator_context",
    "public_context",
    "snapshot_context",
    "service",
    "fake_semantic",
    "default_records",
    "record",
    "artifact",
    "identity",
    "replace",
    "AmbiguityReason",
    "Depth",
    "Intent",
    "TimeScope",
]
