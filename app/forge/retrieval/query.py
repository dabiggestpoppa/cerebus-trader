"""Structured + lexical retrieval query for GLX FORGE Book I / Bloc I.4 (Ch I.4.2).

Exact governed lookup over safe headers first, then body-level filters, then a
TOTAL deterministic ranking. Two laws:

- **Exact structured identity outranks textual similarity.** Structured
  filters and the identity tier always precede lexical hits.
- **Determinism.** Ranking key is
  ``(identity_tier, -structured_hits, -lexical_hits, object_id)`` — no clock,
  no randomness, no iteration-order dependence. Same query + same generation
  ⇒ byte-identical result order and identities.

An unrecognized filter value matches NOTHING (fail closed); it is never
coerced to a nearest enum value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.forge.canonical import (
    ClaimIdentity,
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
    compare_claim_identity,
)
from app.forge.retrieval.aliases import expand_query_text
from app.forge.retrieval.objects import (
    RetrievalHeader,
    RetrievalObject,
    model_family_of,
)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.]*")


def tokenize(text: str) -> frozenset[str]:
    if not text:
        return frozenset()
    return frozenset(_TOKEN_RE.findall(text.lower()))


@dataclass(frozen=True)
class RetrievalQuery:
    """All filters are optional and exact; `text` is the only fuzzy signal."""

    canonical_id: str | None = None
    object_type: ObjectType | str | None = None
    market: str | None = None
    model_family: str | None = None
    status: EvidenceStatus | str | None = None
    exposure: ProductExposure | str | None = None
    layer: Layer | str | None = None
    source_artifact: str | None = None
    provenance_relation: str | None = None
    claim_identity: ClaimIdentity | None = None
    text: str | None = None
    include_quarantine: bool = False
    limit: int | None = None


@dataclass(frozen=True)
class NormalizedQuery:
    """Coerced query. `valid is False` ⇒ the query matches nothing (fail closed)."""

    raw: RetrievalQuery
    valid: bool
    tokens: frozenset[str]
    expanded_tokens: frozenset[str]

    @property
    def all_tokens(self) -> frozenset[str]:
        return self.tokens | self.expanded_tokens


def _coerce(value: object, enum_cls) -> object | None:
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            return _INVALID
    return _INVALID


_INVALID = object()


def normalize_query(query: RetrievalQuery) -> NormalizedQuery:
    text = (query.text or "").strip()
    tokens = tokenize(text)
    expanded = tokenize(" ".join(expand_query_text(text))) if text else frozenset()

    valid = True
    for value, enum_cls in (
        (query.object_type, ObjectType),
        (query.status, EvidenceStatus),
        (query.exposure, ProductExposure),
        (query.layer, Layer),
    ):
        if value is not None and _coerce(value, enum_cls) is _INVALID:
            valid = False
    if query.claim_identity is not None and not isinstance(
        query.claim_identity, ClaimIdentity
    ):
        valid = False
    if query.limit is not None and (not isinstance(query.limit, int) or query.limit < 1):
        valid = False
    return NormalizedQuery(
        raw=query, valid=valid, tokens=tokens, expanded_tokens=expanded
    )


# ---------------------------------------------------------------------------
# Safe-header filters (candidate selection — no body load required)
# ---------------------------------------------------------------------------


def filter_headers(
    headers: Iterable[RetrievalHeader], query: NormalizedQuery
) -> tuple[RetrievalHeader, ...]:
    if not query.valid:
        return ()
    raw = query.raw
    selected: list[RetrievalHeader] = []
    for header in headers:
        if raw.canonical_id is not None and header.object_id != raw.canonical_id:
            continue
        if raw.object_type is not None and header.object_type != _coerce(
            raw.object_type, ObjectType
        ):
            continue
        if raw.status is not None and header.status != _coerce(raw.status, EvidenceStatus):
            continue
        if raw.exposure is not None and header.exposure != _coerce(
            raw.exposure, ProductExposure
        ):
            continue
        if raw.layer is not None and header.layer != _coerce(raw.layer, Layer):
            continue
        if raw.model_family is not None and header.model_family.lower() != str(
            raw.model_family
        ).lower():
            continue
        if raw.market is not None and str(raw.market).upper() not in tuple(
            market.upper() for market in header.market_scope
        ):
            continue
        if raw.source_artifact is not None and raw.source_artifact not in (
            header.source_artifact_ids
        ):
            continue
        selected.append(header)
    return tuple(sorted(selected, key=lambda header: header.object_id))


# ---------------------------------------------------------------------------
# Body filters (applied ONLY to policy-allowed records)
# ---------------------------------------------------------------------------


def filter_records(
    records: Iterable[RetrievalObject], query: NormalizedQuery
) -> tuple[RetrievalObject, ...]:
    if not query.valid:
        return ()
    raw = query.raw
    selected: list[RetrievalObject] = []
    for record in records:
        if raw.provenance_relation is not None and not any(
            link.relation == raw.provenance_relation for link in record.provenance
        ):
            continue
        if raw.claim_identity is not None:
            identity = record.structured.claim_identity
            if identity is None or compare_claim_identity(
                identity, raw.claim_identity
            ).value != "SAME_POPULATION":
                continue
        selected.append(record)
    return tuple(sorted(selected, key=lambda record: record.object_id))


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

_STRUCTURED_ENUM_FIELDS = (
    "status",
    "exposure_class",
    "layer",
    "object_type",
)


@dataclass(frozen=True)
class ScoredResult:
    record: RetrievalObject
    exact_identity: bool
    structured_hits: int
    lexical_hits: int

    @property
    def rank_key(self) -> tuple[int, int, int, str]:
        return (
            0 if self.exact_identity else 1,
            -self.structured_hits,
            -self.lexical_hits,
            self.record.object_id,
        )


def _structured_values(record: RetrievalObject) -> tuple[str, ...]:
    structured = record.structured
    values: list[str] = []
    values.extend(market for market in record.market_scope)
    family = model_family_of(record.object_id)
    if family:
        values.append(family)
    for field_name in _STRUCTURED_ENUM_FIELDS:
        enum_value = getattr(record, field_name)
        if enum_value is None:
            continue
        values.append(getattr(enum_value, "value", str(enum_value)))
    values.extend(structured.metrics)
    values.extend(structured.states)
    values.extend(structured.events)
    values.extend(structured.clocks)
    values.extend(structured.levels)
    if structured.period:
        values.append(structured.period)
    if structured.sample_n is not None:
        values.append(str(structured.sample_n))
    values.append(record.canonical_version)
    return tuple(value.lower() for value in values if value)


def score_record(query: NormalizedQuery, record: RetrievalObject) -> ScoredResult:
    text = (query.raw.text or "").strip()
    exact_identity = bool(text) and text.lower() == record.object_id.lower()
    if query.raw.canonical_id is not None:
        exact_identity = query.raw.canonical_id == record.object_id

    tokens = query.all_tokens
    structured_values = set(_structured_values(record))
    structured_hits = len(tokens & structured_values)

    haystack = tokenize(
        " ".join(
            (
                record.title,
                record.retrieval_text,
                " ".join(record.structured.terms),
                " ".join(record.structured.aliases),
                record.object_id,
            )
        )
    )
    lexical_hits = len(tokens & haystack)
    return ScoredResult(
        record=record,
        exact_identity=exact_identity,
        structured_hits=structured_hits,
        lexical_hits=lexical_hits,
    )


def rank(
    query: NormalizedQuery, records: Iterable[RetrievalObject]
) -> tuple[ScoredResult, ...]:
    """Total deterministic ordering. A text query with no signal matches nothing."""

    scored = [score_record(query, record) for record in records]
    has_text = bool((query.raw.text or "").strip())
    if has_text:
        scored = [
            result
            for result in scored
            if result.exact_identity
            or result.structured_hits > 0
            or result.lexical_hits > 0
        ]
    ordered = tuple(sorted(scored, key=lambda result: result.rank_key))
    if query.raw.limit is not None:
        ordered = ordered[: query.raw.limit]
    return ordered


__all__ = [
    "RetrievalQuery",
    "NormalizedQuery",
    "ScoredResult",
    "tokenize",
    "normalize_query",
    "filter_headers",
    "filter_records",
    "score_record",
    "rank",
]
