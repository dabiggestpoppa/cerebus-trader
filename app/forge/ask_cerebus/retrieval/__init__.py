"""Book IV / Bloc IV.2 — hybrid retrieval and evidence routing."""

from app.forge.ask_cerebus.retrieval.bundle import AuthorizedRetrievalBundle
from app.forge.ask_cerebus.retrieval.claims import ClaimEvidenceJoiner, ClaimJoin
from app.forge.ask_cerebus.retrieval.conflicts import ConflictAssessment, assess
from app.forge.ask_cerebus.retrieval.enums import (
    EvidenceJoinStatus,
    LimitationCode,
    PrecedenceTier,
    RefusalCode,
    RejectionClass,
    RetrievalOutcome,
    TraceClass,
)
from app.forge.ask_cerebus.retrieval.intelligence import (
    IntelligenceRoute,
    NotConfiguredSnapshotProvider,
    SnapshotContext,
    SnapshotProviderPort,
    build_request,
    route_intelligence,
)
from app.forge.ask_cerebus.retrieval.lineage import (
    build_lineage_refs,
    lineage_limitations,
)
from app.forge.ask_cerebus.retrieval.negative import (
    build_negative_refs,
    is_negative,
    negative_limitations,
)
from app.forge.ask_cerebus.retrieval.precedence import (
    ordering_key,
    semantic_tier,
    tier_for_object_type,
)
from app.forge.ask_cerebus.retrieval.query_builder import ResolverTargets, build_targets
from app.forge.ask_cerebus.retrieval.refs import (
    CanonicalRef,
    ClaimRef,
    EvidenceRef,
    IntelligenceRef,
    Limitation,
    LineageRef,
    NegativeRef,
    Refusal,
    SemanticPassage,
)
from app.forge.ask_cerebus.retrieval.semantic import (
    DeterministicFakeSemanticIndex,
    EmptySemanticIndex,
    SemanticCandidate,
    SemanticIndexPort,
)
from app.forge.ask_cerebus.retrieval.service import AskCerebusRetrievalService
from app.forge.ask_cerebus.retrieval.structured import (
    StructuredResolution,
    StructuredResolver,
)
from app.forge.ask_cerebus.retrieval.trace import RetrievalTrace, rejection_counts
from app.forge.ask_cerebus.retrieval.versions import (
    RETRIEVAL_CONTRACT_V1,
    SUPPORTED_RETRIEVAL_CONTRACT_VERSIONS,
)

__all__ = [
    "RETRIEVAL_CONTRACT_V1",
    "SUPPORTED_RETRIEVAL_CONTRACT_VERSIONS",
    "AuthorizedRetrievalBundle",
    "CanonicalRef",
    "ClaimRef",
    "EvidenceRef",
    "IntelligenceRef",
    "LineageRef",
    "SemanticPassage",
    "NegativeRef",
    "Limitation",
    "Refusal",
    "LimitationCode",
    "RefusalCode",
    "RejectionClass",
    "EvidenceJoinStatus",
    "PrecedenceTier",
    "RetrievalOutcome",
    "TraceClass",
    "RetrievalTrace",
    "rejection_counts",
    "ResolverTargets",
    "build_targets",
    "StructuredResolver",
    "StructuredResolution",
    "SemanticIndexPort",
    "SemanticCandidate",
    "DeterministicFakeSemanticIndex",
    "EmptySemanticIndex",
    "ClaimEvidenceJoiner",
    "ClaimJoin",
    "SnapshotContext",
    "SnapshotProviderPort",
    "NotConfiguredSnapshotProvider",
    "IntelligenceRoute",
    "build_request",
    "route_intelligence",
    "build_lineage_refs",
    "lineage_limitations",
    "build_negative_refs",
    "is_negative",
    "negative_limitations",
    "assess",
    "ConflictAssessment",
    "tier_for_object_type",
    "semantic_tier",
    "ordering_key",
    "AskCerebusRetrievalService",
]
