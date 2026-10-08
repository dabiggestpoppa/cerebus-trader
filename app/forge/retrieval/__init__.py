"""Retrieval Object Compiler & index — GLX FORGE Book I / Bloc I.4.

Public surface of the I.4 bloc: compile governed canonical persistence into
frozen-schema retrieval records, publish them as an explicit index generation,
and release them only through the II.4 policy boundary.

No route, no provider, no external index store: retrieval here is in-process,
structured-first and lexical, exactly as the frozen Book I plan specifies.
"""

from app.forge.retrieval.aliases import (
    HISTORICAL_ALIASES,
    AliasEntry,
    aliases_present,
    expand_query_text,
    lookup_alias,
)
from app.forge.retrieval.compiler import (
    CompileContext,
    RetrievalCompileError,
    compile_record,
    evaluate_support,
    normalized_content_hash,
    normalized_governed_payload,
    sanitize_text,
)
from app.forge.retrieval.index import (
    GovernedState,
    IndexBuildError,
    IndexBuildMode,
    IndexBuildOutcome,
    IndexBuildReport,
    IndexGeneration,
    IndexNotBuilt,
    QuarantineCatalog,
    QuarantineEntry,
    RetrievalIndex,
    build_index,
    read_state,
    run_index_build,
)
from app.forge.retrieval.objects import (
    RETRIEVAL_OBJECT_TYPES,
    ConflictMetadata,
    LeakageMetadata,
    ProvenanceLink,
    RelatedLink,
    RetrievalHeader,
    RetrievalObject,
    RoutingMetadata,
    StructuredFields,
    SupportAssessment,
)
from app.forge.retrieval.query import (
    RetrievalQuery,
    ScoredResult,
    filter_headers,
    filter_records,
    normalize_query,
    rank,
    tokenize,
)
from app.forge.retrieval.service import (
    ArtifactTrace,
    ChainHop,
    DeniedResult,
    MissingLink,
    ProvenanceChain,
    QuarantineNotice,
    RetrievalResponse,
    RetrievalResult,
    RetrievalService,
)

__all__ = [
    # aliases
    "AliasEntry",
    "HISTORICAL_ALIASES",
    "aliases_present",
    "expand_query_text",
    "lookup_alias",
    # compiler
    "CompileContext",
    "RetrievalCompileError",
    "compile_record",
    "evaluate_support",
    "normalized_content_hash",
    "normalized_governed_payload",
    "sanitize_text",
    # index
    "GovernedState",
    "IndexBuildError",
    "IndexBuildMode",
    "IndexBuildOutcome",
    "IndexBuildReport",
    "IndexGeneration",
    "IndexNotBuilt",
    "QuarantineCatalog",
    "QuarantineEntry",
    "RetrievalIndex",
    "build_index",
    "read_state",
    "run_index_build",
    # records
    "RETRIEVAL_OBJECT_TYPES",
    "ConflictMetadata",
    "LeakageMetadata",
    "ProvenanceLink",
    "RelatedLink",
    "RetrievalHeader",
    "RetrievalObject",
    "RoutingMetadata",
    "StructuredFields",
    "SupportAssessment",
    # query
    "RetrievalQuery",
    "ScoredResult",
    "filter_headers",
    "filter_records",
    "normalize_query",
    "rank",
    "tokenize",
    # service
    "ArtifactTrace",
    "ChainHop",
    "DeniedResult",
    "MissingLink",
    "ProvenanceChain",
    "QuarantineNotice",
    "RetrievalResponse",
    "RetrievalResult",
    "RetrievalService",
]
