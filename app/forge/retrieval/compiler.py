"""Retrieval object compiler for GLX FORGE Book I / Bloc I.4 (Ch I.4.1-I.4.5).

canonical object (validated, persisted) -> normalized retrieval object.

Laws enforced here:

- **Compile from governed state only.** Input is a `CanonicalObjectRecord`
  plus its provenance (edges + artifacts) as read through the II.2 port. The
  compiler never reads Markdown and never re-derives epistemic status.
- **Status/exposure are copied, never re-evaluated.** A lexical hit, a routing
  weight, or an alias can never promote, merge, or reclassify anything.
- **Facets only from actual schema fields.** Unstated dimensions stay empty —
  uncertainty is preserved, never fabricated.
- **Internal bodies are never indexed.** INTERNAL_METHOD / INTERNAL_CODE
  records compile identity-only (empty text, empty facets), and any code or
  internal-method segment found in generated text is stripped before the
  record can exist (Ch I.4.3).
- **Normalized identity.** Reference order is never treated as identity
  (I.3 limitation A): the governed payload sorts references before hashing,
  without touching the frozen I.1 `content_hash()`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Mapping

from app.forge.canonical import (
    CanonicalId,
    Layer,
    ObjectType,
    ProductExposure,
)
from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
)
from app.forge.provenance import SupportClassification, classify_support
from app.forge.retrieval.aliases import aliases_present, is_not_specified
from app.forge.retrieval.objects import (
    QUOTE_SCOPE_NONE,
    QUOTE_SCOPE_SYNTHESIS,
    RETRIEVAL_OBJECT_TYPES,
    ROUTING_WEIGHTS,
    ConflictMetadata,
    LeakageMetadata,
    ProvenanceLink,
    RelatedLink,
    RetrievalObject,
    RoutingMetadata,
    StructuredFields,
    SupportAssessment,
)

_INTERNAL_EXPOSURES = (ProductExposure.INTERNAL_METHOD, ProductExposure.INTERNAL_CODE)

# Governed qualifier flags (I.5): exact table over the boolean metadata keys
# the I.3 migration preserves from legacy status/type mappings. Unknown flags
# are never projected (no fuzzy carry-over).
QUALIFIER_FLAG_TABLE: dict[str, str] = {
    "small_n": "SMALL_N",
    "research_sample": "RESEARCH_SAMPLE",
    "relationship_statistic": "RELATIONSHIP_STATISTIC",
}

# Code constructs. A retrieval record is generated text; code must never ride
# along (Ch I.4.3 / Product Exposure Rules "internal code ... never retrieved").
_CODE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"```"),
    re.compile(r"//@version"),
    re.compile(r"\b(?:indicator|strategy|plot|alertcondition|request\.security)\s*\(", re.I),
    re.compile(r"(?m)^\s*(?:def|class|import|from)\s+\w"),
    re.compile(r"\bselect\b.+\bfrom\b", re.I),
    re.compile(r"#\s*include"),
)

# Internal-method vocabulary from PRODUCT_EXPOSURE_RULES_V1 "internal method".
_INTERNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bINTERNAL_METHOD\b"),
    re.compile(r"\bINTERNAL_CODE\b"),
    re.compile(r"anti[- ]leakage", re.I),
    re.compile(r"hidden calibration", re.I),
    re.compile(r"unreleased transformation", re.I),
    re.compile(r"\bfeature engineering\b", re.I),
    re.compile(r"model[- ]construction detail", re.I),
)

_SEGMENT_RE = re.compile(r"(?<=[.!?])\s+|\n")


class RetrievalCompileError(Exception):
    """A canonical record could not be compiled safely; nothing is published."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


# ---------------------------------------------------------------------------
# Build context: everything one compile reads (all pre-loaded, governed)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompileContext:
    """Pre-read governed state. The compiler performs no I/O of its own."""

    records: Mapping[str, CanonicalObjectRecord]
    edges: Mapping[str, tuple[ProvenanceEdgeRecord, ...]]
    artifacts: Mapping[str, ArtifactRecord]


# ---------------------------------------------------------------------------
# Normalized identity (I.3 limitation A): reference sets, not reference order
# ---------------------------------------------------------------------------


def normalized_governed_payload(record: CanonicalObjectRecord) -> str:
    """Deterministic governed-content payload with references as a SET.

    Mirrors the persistence-level governed comparison: persistence stores
    references under a (canonical_id, target_id, relation) key, so authored
    reference order is not identity. The frozen I.1 `content_hash()` is left
    untouched (no GAP/ADR needed: this is an index-side normalization only).
    """

    payload = {
        "canonical_id": record.canonical_id,
        "object_type": record.object_type.value,
        "title": record.title,
        "version": record.version,
        "status": record.status.value,
        "exposure": (
            record.exposure.value
            if isinstance(record.exposure, ProductExposure)
            else str(record.exposure)
        ),
        "layer": record.layer.value,
        "references": sorted(
            (
                {
                    "target_id": ref.target_id,
                    "relation": ref.relation,
                    "allow_unresolved_historical": ref.allow_unresolved_historical,
                }
                for ref in record.references
            ),
            key=lambda item: (
                item["target_id"],
                item["relation"],
                item["allow_unresolved_historical"],
            ),
        ),
        "metadata": record.metadata,
        "claim_identity": (
            record.claim_identity.comparison_key()
            if record.claim_identity is not None
            else None
        ),
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def normalized_content_hash(record: CanonicalObjectRecord) -> str:
    return hashlib.sha256(
        normalized_governed_payload(record).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Safe text (Ch I.4.3)
# ---------------------------------------------------------------------------


def sanitize_text(text: str) -> tuple[str, bool, bool]:
    """Strip code / internal-method segments from generated text.

    Returns ``(clean_text, contains_internal_method, contains_code)``.
    Segment granularity: a sentence or line carrying a marker is dropped
    whole — never partially redacted into a misleading statement.
    """

    if not text:
        return "", False, False
    segments = [s.strip() for s in _SEGMENT_RE.split(text) if s.strip()]
    kept: list[str] = []
    hit_internal = False
    hit_code = False
    for segment in segments:
        if any(pattern.search(segment) for pattern in _INTERNAL_PATTERNS):
            hit_internal = True
            continue
        if any(pattern.search(segment) for pattern in _CODE_PATTERNS):
            hit_code = True
            continue
        kept.append(segment)
    return " ".join(kept), hit_internal, hit_code


def _tokens(value: str) -> tuple[str, ...]:
    """Normalized whole-word-ish tokens for the `terms` facet."""

    return tuple(sorted({t for t in re.findall(r"[a-z0-9][a-z0-9_.]*", value.lower())}))


# ---------------------------------------------------------------------------
# Field helpers (actual schema fields only)
# ---------------------------------------------------------------------------


def _card(record: CanonicalObjectRecord) -> dict:
    card = record.metadata.get("card")
    return card if isinstance(card, dict) else {}


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        raw: tuple[str, ...] = (value,)
    elif isinstance(value, (list, tuple)):
        raw = tuple(v for v in value if isinstance(v, str))
    else:
        return ()
    out: list[str] = []
    for item in raw:
        for part in str(item).split(","):
            cleaned = part.strip()
            if cleaned and not is_not_specified(cleaned):
                out.append(cleaned)
    return tuple(out)


def _sentence(value: object) -> str:
    if isinstance(value, str) and not is_not_specified(value):
        return value.strip()
    return ""


def _lines(value: object) -> list[str]:
    """Bulleted governed section as sentences (markers and empties dropped)."""

    if isinstance(value, (list, tuple)):
        return [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip() and not is_not_specified(item)
        ]
    sentence = _sentence(value)
    return [sentence] if sentence else []


def _market_scope(record: CanonicalObjectRecord, card: dict) -> tuple[str, ...]:
    if record.object_type is ObjectType.CLAIM and record.claim_identity is not None:
        return _string_tuple(record.claim_identity.market)
    if record.object_type is ObjectType.EVIDENCE:
        return _string_tuple(card.get("market", ""))
    return _string_tuple(card.get("market_scope", ()))


def _generation(record: CanonicalObjectRecord, card: dict) -> str:
    """Source generation retained verbatim (crosswalk: preserve generation)."""

    for value in (card.get("source_generation"), record.metadata.get("source_generation")):
        if isinstance(value, str) and not is_not_specified(value):
            return value.strip()
    return ""


def _build_text(
    record: CanonicalObjectRecord, card: dict
) -> str:
    """Concise canonical statement from governed card fields only."""

    parts: list[str] = [record.title.strip()] if record.title.strip() else []
    if record.object_type is ObjectType.MODEL:
        # Purpose + known limitations: the governed statement plus the
        # card's own "what this does NOT mean" cautions (Answer Contract).
        parts.append(_sentence(card.get("purpose")))
        parts.extend(_lines(card.get("known_limitations")))
    elif record.object_type is ObjectType.SETUP:
        parts.append(_sentence(card.get("purpose")))
    elif record.object_type is ObjectType.EVIDENCE:
        exact = _sentence(card.get("exact_claim"))
        if exact:
            parts.append(exact)
        result = _sentence(card.get("result"))
        if result:
            parts.append(f"Result: {result}")
        interpretation = _sentence(card.get("interpretation"))
        if interpretation:
            parts.append(interpretation)
    elif record.object_type is ObjectType.CLAIM:
        claim_text = record.metadata.get("claim_text")
        if isinstance(claim_text, str) and claim_text.strip():
            parts = [claim_text.strip()]
    return " ".join(p for p in parts if p)


def _source_type_vocabulary(record: CanonicalObjectRecord, card: dict) -> tuple[str, ...]:
    if record.object_type is ObjectType.MODEL:
        return _tokens(str(card.get("model_type", "")))
    if record.object_type is ObjectType.SETUP:
        return _tokens(str(card.get("execution_class", "")))
    if record.object_type is ObjectType.EVIDENCE:
        return _tokens(str(card.get("evidence_type", "")))
    return _tokens(record.object_type.value)


# ---------------------------------------------------------------------------
# Support assessment (FOUND vs SUPPORTED) — ratified I.2 semantics
# ---------------------------------------------------------------------------


def _typed(value: str) -> ObjectType | None:
    try:
        return CanonicalId.parse(value).object_type
    except (ValueError, AssertionError):
        return None


def _evidence_targets(record: CanonicalObjectRecord) -> tuple[str, ...]:
    return tuple(
        sorted(
            ref.target_id
            for ref in record.references
            if ref.relation == "supported_by"
            and _typed(ref.target_id) is ObjectType.EVIDENCE
        )
    )


def _sources_for(
    object_ids: tuple[str, ...], context: CompileContext
) -> tuple[list[ArtifactRecord], tuple[str, ...]]:
    sources: list[ArtifactRecord] = []
    gaps: list[str] = []
    for object_id in object_ids:
        edges = context.edges.get(object_id, ())
        if not edges:
            gaps.append("EVIDENCE_WITHOUT_SOURCE")
            continue
        for edge in edges:
            artifact = context.artifacts.get(edge.artifact_id)
            if artifact is None:
                gaps.append("SOURCE_ARTIFACT_MISSING")
                continue
            sources.append(artifact)
    return sources, tuple(sorted(set(gaps)))


def evaluate_support(
    record: CanonicalObjectRecord, context: CompileContext
) -> SupportAssessment:
    """Resolve the canonical chain to a support classification.

    CLAIM / MODEL / SETUP route through their linked EVIDENCE objects
    (CLAIM -> EVIDENCE -> SOURCE); EVIDENCE and doctrine-like objects use
    their own provenance edges. Visual and conversation-derived sources never
    count as independent empirical support (ratified I.2 `classify_support`).
    Missing links become explicit gap reason codes — never reconstructed.
    """

    if record.object_type in (ObjectType.EVIDENCE, ObjectType.DOCTRINE, ObjectType.TERM, ObjectType.LINEAGE):
        sources, gaps = _sources_for((record.canonical_id,), context)
        evidence_ids: tuple[str, ...] = ()
        if not sources:
            gaps = tuple(sorted(set(gaps + ("NO_SOURCE_ARTIFACT",))))
    else:
        evidence_ids = _evidence_targets(record)
        if not evidence_ids:
            return SupportAssessment(
                supported=False,
                classification=SupportClassification.NO_SOURCE.value,
                evidence_ids=(),
                gaps=("NO_EVIDENCE_REFERENCE",),
            )
        missing = tuple(e for e in evidence_ids if e not in context.records)
        if missing:
            return SupportAssessment(
                supported=False,
                classification=SupportClassification.NO_SOURCE.value,
                evidence_ids=evidence_ids,
                gaps=tuple(sorted(set(("EVIDENCE_RECORD_MISSING",) + missing))),
            )
        sources, gaps = _sources_for(evidence_ids, context)

    if not sources:
        classification = SupportClassification.NO_SOURCE
        gaps = tuple(sorted(set(gaps)))
    else:
        classification = classify_support(
            [artifact.to_domain() for artifact in sources]
        )
        if classification is not SupportClassification.EMPIRICAL:
            gaps = tuple(sorted(set(gaps + ("NON_EMPIRICAL_SOURCE",))))
        elif gaps:
            gaps = tuple(sorted(set(gaps)))

    return SupportAssessment(
        supported=classification is SupportClassification.EMPIRICAL,
        classification=classification.value,
        evidence_ids=evidence_ids,
        gaps=gaps,
    )


# ---------------------------------------------------------------------------
# The compiler
# ---------------------------------------------------------------------------


def compile_record(
    record: CanonicalObjectRecord,
    context: CompileContext,
    generation: int = 1,
) -> RetrievalObject:
    """Compile one governed canonical record into a retrieval record.

    Raises :class:`RetrievalCompileError` on anything that cannot be compiled
    safely (unknown exposure, non-retrieval object type): the build then fails
    closed and publishes nothing.
    """

    if record.object_type not in RETRIEVAL_OBJECT_TYPES:
        raise RetrievalCompileError(
            "NON_RETRIEVAL_OBJECT_TYPE",
            f"{record.canonical_id} has type {record.object_type.value}, "
            "which is not a retrieval object type",
        )
    if not isinstance(record.exposure, ProductExposure):
        raise RetrievalCompileError(
            "UNKNOWN_EXPOSURE",
            f"{record.canonical_id} carries unrecognized exposure "
            f"{record.exposure!r}",
        )
    if not isinstance(record.layer, Layer):
        raise RetrievalCompileError(
            "UNKNOWN_LAYER", f"{record.canonical_id} carries an invalid layer"
        )

    card = _card(record)
    internal = record.exposure in _INTERNAL_EXPOSURES

    edges = tuple(context.edges.get(record.canonical_id, ()))
    provenance = tuple(
        ProvenanceLink(
            artifact_id=edge.artifact_id,
            relation=edge.relation,
            source_class=(
                context.artifacts[edge.artifact_id].source_class
                if edge.artifact_id in context.artifacts
                else ""
            ),
            source_state=(
                context.artifacts[edge.artifact_id].source_state
                if edge.artifact_id in context.artifacts
                else ""
            ),
            content_identity=(
                context.artifacts[edge.artifact_id].content_identity
                if edge.artifact_id in context.artifacts
                else None
            ),
            locator=(
                context.artifacts[edge.artifact_id].locator
                if edge.artifact_id in context.artifacts
                else ""
            ),
        )
        for edge in edges
    )

    # -- safe semantic text (Ch I.4.3) -------------------------------------
    raw_text = "" if internal else _build_text(record, card)
    clean_text, hit_internal, hit_code = sanitize_text(raw_text)
    if internal:
        # Identity-only record: an internal body is never indexed at all.
        clean_text = ""
        hit_internal = False
        hit_code = False

    # -- structured facets (Ch I.4.2) --------------------------------------
    if internal:
        structured = StructuredFields()
        market_scope: tuple[str, ...] = ()
    else:
        market_scope = _market_scope(record, card)
        sample_n_raw = card.get("sample_n")
        sample_n = (
            int(sample_n_raw)
            if isinstance(sample_n_raw, int) and sample_n_raw > 0
            else None
        )
        structured = StructuredFields(
            terms=tuple(
                sorted(
                    set(_tokens(record.title)) | set(_source_type_vocabulary(record, card))
                )
            ),
            aliases=aliases_present(f"{record.title} {clean_text}"),
            clocks=tuple(
                sorted(
                    set(_string_tuple(card.get("clock_origin", "")))
                    | set(
                        _string_tuple(record.claim_identity.clock_origin)
                        if record.claim_identity is not None
                        else ()
                    )
                    | set(_string_tuple(card.get("clock_mode", "")))
                )
            ),
            states=_string_tuple(card.get("state_space", ())),
            events=tuple(
                sorted(
                    set(_string_tuple(card.get("event_definition", "")))
                    | set(
                        _string_tuple(record.claim_identity.event_definition)
                        if record.claim_identity is not None
                        else ()
                    )
                )
            ),
            levels=tuple(
                sorted(
                    set(
                        _string_tuple(card.get("l3_destination", ""))
                        + _string_tuple(card.get("l2_path", ""))
                        + _string_tuple(card.get("l1_execution", ""))
                    )
                )
            ),
            metrics=_string_tuple(card.get("metric", "")),
            sample_n=sample_n,
            period=(
                card.get("data_period", "").strip()
                if not is_not_specified(card.get("data_period", ""))
                else None
            ),
            implementation_ids=tuple(
                sorted(
                    {
                        edge.artifact_id
                        for edge in edges
                        if edge.relation == "IMPLEMENTS"
                    }
                )
            ),
            claim_identity=record.claim_identity,
        )

    references = tuple(
        RelatedLink(relation=ref.relation, target_id=ref.target_id)
        for ref in record.references
    )
    parent_ids = tuple(
        sorted(
            ref.target_id
            for ref in record.references
            if ref.relation in ("parent", "belongs_to")
        )
    )
    source_artifact_ids = tuple(sorted({edge.artifact_id for edge in edges}))

    # Governed qualifier flags (I.5): exact table over the boolean metadata
    # the I.3 migration preserves — never inferred, never fuzzy.
    qualifiers = tuple(
        sorted(
            QUALIFIER_FLAG_TABLE[flag]
            for flag, enabled in QUALIFIER_FLAG_TABLE.items()
            if record.metadata.get(flag) is True
        )
    )

    beginner, operator, researcher = ROUTING_WEIGHTS[record.object_type]
    has_evidence_ref = bool(_evidence_targets(record))
    requires_evidence = (
        record.object_type in (ObjectType.CLAIM, ObjectType.EVIDENCE)
        or has_evidence_ref
        or structured.sample_n is not None
        or bool(structured.metrics)
    )
    routing = RoutingMetadata(
        beginner_weight=beginner,
        operator_weight=operator,
        researcher_weight=researcher,
        actionable=record.object_type is ObjectType.SETUP,
        requires_setup_card=record.object_type is not ObjectType.SETUP,
        requires_evidence_card=requires_evidence,
    )

    if internal:
        max_quote_scope = QUOTE_SCOPE_NONE
    elif hit_internal or hit_code:
        max_quote_scope = QUOTE_SCOPE_NONE
    else:
        max_quote_scope = QUOTE_SCOPE_SYNTHESIS

    return RetrievalObject(
        object_id=record.canonical_id,
        object_type=record.object_type,
        canonical_version=record.version,
        title=record.title,
        market_scope=market_scope,
        layer=record.layer,
        status=record.status,
        exposure_class=record.exposure,
        parent_ids=parent_ids,
        source_artifact_ids=source_artifact_ids,
        retrieval_text=clean_text,
        structured=structured,
        routing=routing,
        leakage=LeakageMetadata(
            contains_internal_method=hit_internal,
            contains_code=hit_code,
            max_quote_scope=max_quote_scope,
        ),
        conflict=ConflictMetadata(
            supersedes_ids=tuple(
                sorted(
                    ref.target_id
                    for ref in record.references
                    if ref.relation == "supersedes"
                )
            ),
            contradicts_ids=tuple(
                sorted(
                    ref.target_id
                    for ref in record.references
                    if ref.relation == "contradicts"
                )
            ),
            generation=_generation(record, card),
        ),
        support=evaluate_support(record, context),
        qualifiers=qualifiers,
        related_ids=tuple(
            sorted(references, key=lambda item: (item.relation, item.target_id))
        ),
        provenance=tuple(
            sorted(provenance, key=lambda item: (item.artifact_id, item.relation))
        ),
        generation=generation,
    )


__all__ = [
    "RetrievalCompileError",
    "CompileContext",
    "normalized_governed_payload",
    "normalized_content_hash",
    "sanitize_text",
    "evaluate_support",
    "compile_record",
]
