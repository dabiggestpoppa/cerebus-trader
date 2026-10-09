"""Retrieval service for GLX FORGE Book I / Bloc I.4 — policy before content.

The ONLY release surface of the index. It executes the frozen sequence:

    principal -> trusted authorization context -> resource metadata (header)
    -> policy decision (II.4 kernel via ForgePolicyEnforcementService)
    -> protected content loading (record body) -> retrieval result

Every per-record load goes through the ratified deny-before-load `guard()`
primitive: on DENY the loader is never invoked, so unauthorized content never
enters any buffer — not a result, not a snippet, not a ranking explanation, not
a log line. Denials are content-free entries (id, exposure, reason code).

This module adds no route and no provider: I.4 is an in-process service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.forge.canonical import ProductExposure
from app.forge.identity import ForgePrincipal
from app.forge.policy import (
    AuthorizationContext,
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyEngine,
    PolicyResourceType,
    ResourcePolicyMetadata,
)
from app.forge.retrieval.index import IndexGeneration, RetrievalIndex
from app.forge.retrieval.objects import RetrievalObject
from app.forge.retrieval.query import (
    RetrievalQuery,
    filter_headers,
    filter_records,
    normalize_query,
    rank,
)
from app.forge.service.policy_enforcement import ForgePolicyEnforcementService

RecordLoader = Callable[[IndexGeneration, str], RetrievalObject | None]

_INTERNAL_EXPOSURES = (ProductExposure.INTERNAL_METHOD, ProductExposure.INTERNAL_CODE)


# ---------------------------------------------------------------------------
# Result / response shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetrievalResult:
    """What was found — never an answer, never an assertion of truth."""

    object_id: str
    object_type: str
    title: str
    canonical_version: str
    status: str
    exposure: str
    layer: str
    market_scope: tuple[str, ...]
    model_family: str
    retrieval_text: str
    generation: int
    found: bool
    supported: bool
    support_classification: str
    support_gaps: tuple[str, ...]
    exact_identity: bool
    structured_hits: int
    lexical_hits: int
    max_quote_scope: str

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "object_type": self.object_type,
            "title": self.title,
            "canonical_version": self.canonical_version,
            "status": self.status,
            "exposure": self.exposure,
            "layer": self.layer,
            "market_scope": list(self.market_scope),
            "model_family": self.model_family,
            "retrieval_text": self.retrieval_text,
            "generation": self.generation,
            "found": self.found,
            "supported": self.supported,
            "support_classification": self.support_classification,
            "support_gaps": list(self.support_gaps),
            "structured_hits": self.structured_hits,
            "lexical_hits": self.lexical_hits,
            "max_quote_scope": self.max_quote_scope,
        }


@dataclass(frozen=True)
class DeniedResult:
    """Content-free denial entry: identity + exposure + reason, nothing else."""

    object_id: str
    exposure: str
    reason_code: str


@dataclass(frozen=True)
class QuarantineNotice:
    """Safe quarantine metadata (source path + reason). No body, ever."""

    source_path: str
    reason: str
    quarantined: bool = True


@dataclass(frozen=True)
class RetrievalResponse:
    results: tuple[RetrievalResult, ...]
    denied: tuple[DeniedResult, ...]
    quarantined: tuple[QuarantineNotice, ...]
    generation: int
    index_hash: str
    candidates: int

    def to_dict(self) -> dict:
        return {
            "results": [result.to_dict() for result in self.results],
            "denied": [
                {
                    "object_id": denied.object_id,
                    "exposure": denied.exposure,
                    "reason_code": denied.reason_code,
                }
                for denied in self.denied
            ],
            "quarantined": [
                {
                    "source_path": notice.source_path,
                    "reason": notice.reason,
                    "quarantined": notice.quarantined,
                }
                for notice in self.quarantined
            ],
            "generation": self.generation,
            "index_hash": self.index_hash,
            "candidates": self.candidates,
        }


# ---------------------------------------------------------------------------
# Provenance navigation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MissingLink:
    from_id: str
    to_id: str
    relation: str
    reason: str


@dataclass(frozen=True)
class ChainHop:
    from_id: str
    relation: str
    to_id: str
    kind: str  # OBJECT | EVIDENCE | ARTIFACT


@dataclass(frozen=True)
class ArtifactTrace:
    artifact_id: str
    relation: str
    source_class: str
    source_state: str
    content_identity: str
    locator: str


@dataclass(frozen=True)
class ProvenanceChain:
    """Claim -> Evidence -> Source Artifact, or an honest report of what is missing."""

    object_id: str
    found: bool
    allowed: bool
    supported: bool
    support_classification: str
    support_gaps: tuple[str, ...]
    status: str = ""
    exposure: str = ""
    generation: int = 0
    hops: tuple[ChainHop, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    artifacts: tuple[ArtifactTrace, ...] = ()
    missing: tuple[MissingLink, ...] = ()
    denied: tuple[DeniedResult, ...] = ()

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "found": self.found,
            "allowed": self.allowed,
            "supported": self.supported,
            "support_classification": self.support_classification,
            "support_gaps": list(self.support_gaps),
            "status": self.status,
            "exposure": self.exposure,
            "generation": self.generation,
            "hops": [
                {"from": h.from_id, "relation": h.relation, "to": h.to_id, "kind": h.kind}
                for h in self.hops
            ],
            "evidence_ids": list(self.evidence_ids),
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "relation": a.relation,
                    "source_class": a.source_class,
                    "source_state": a.source_state,
                    "content_identity": a.content_identity,
                    "locator": a.locator,
                }
                for a in self.artifacts
            ],
            "missing": [
                {
                    "from": m.from_id,
                    "to": m.to_id,
                    "relation": m.relation,
                    "reason": m.reason,
                }
                for m in self.missing
            ],
            "denied": [
                {
                    "object_id": d.object_id,
                    "exposure": d.exposure,
                    "reason_code": d.reason_code,
                }
                for d in self.denied
            ],
        }


# ---------------------------------------------------------------------------
# The service
# ---------------------------------------------------------------------------


class RetrievalService:
    """Governed retrieval over one published index generation."""

    def __init__(
        self,
        index: RetrievalIndex,
        enforcement: ForgePolicyEnforcementService | None = None,
        *,
        engine: PolicyEngine | None = None,
        record_loader: RecordLoader | None = None,
    ) -> None:
        if not isinstance(index, RetrievalIndex):
            raise TypeError("index must be a RetrievalIndex")
        self._index = index
        self._enforcement = enforcement or ForgePolicyEnforcementService(
            engine or DefaultDenyPolicyEngine()
        )
        self._loader: RecordLoader = record_loader or (
            lambda generation, object_id: generation.record(object_id)
        )

    @property
    def index(self) -> RetrievalIndex:
        return self._index

    @property
    def enforcement(self) -> ForgePolicyEnforcementService:
        return self._enforcement

    # -- release primitives -------------------------------------------------

    def _load(self, generation: IndexGeneration, object_id: str) -> RetrievalObject | None:
        """The protected loader invoked ONLY after an ALLOW decision."""

        return self._loader(generation, object_id)

    @staticmethod
    def _object_resource(
        exposure: ProductExposure | None, object_id: str
    ) -> ResourcePolicyMetadata:
        return ResourcePolicyMetadata(
            resource_type=PolicyResourceType.CANONICAL_OBJECT,
            resource_id=object_id,
            exposure=exposure,
        )

    def _authorize_record(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        generation: IndexGeneration,
        object_id: str,
        correlation_id: str,
    ):
        header = generation.header(object_id)
        if header is None:
            return None, None
        resource = self._object_resource(header.exposure, object_id)
        access = self._enforcement.guard(
            principal,
            context,
            PolicyAction.QUERY,
            resource,
            self._load,
            generation,
            object_id,
            correlation_id=correlation_id,
        )
        return access, resource

    # -- retrieval ----------------------------------------------------------

    def retrieve(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        query: RetrievalQuery | None = None,
        *,
        correlation_id: str = "",
    ) -> RetrievalResponse:
        """Frozen sequence: metadata -> decision -> body load -> result."""

        query = query if query is not None else RetrievalQuery()
        normalized = normalize_query(query)
        generation = self._index.require()

        # 1. Safe headers only: candidate selection needs no protected body.
        candidates = filter_headers(generation.headers, normalized)

        # 2. Policy decision per candidate, then (only if allowed) body load.
        allowed: list[RetrievalObject] = []
        denied: list[DeniedResult] = []
        for header in candidates:
            access, _resource = self._authorize_record(
                principal, context, generation, header.object_id, correlation_id
            )
            if access is None:
                continue
            if not access.allowed:
                denied.append(
                    DeniedResult(
                        object_id=header.object_id,
                        exposure=(
                            header.exposure.value
                            if header.exposure is not None
                            else "UNKNOWN"
                        ),
                        reason_code=access.decision.reason_code.value,
                    )
                )
                continue
            if access.payload is not None:
                allowed.append(access.payload)

        # 3. Body-level filters and deterministic ranking over released records.
        filtered = filter_records(allowed, normalized)
        ordered = rank(normalized, filtered)
        results = tuple(_to_result(scored.record, scored) for scored in ordered)

        # 4. Quarantine discovery (explicit, policy-gated, metadata only).
        notices = (
            self._quarantine_notices(principal, context, correlation_id)
            if query.include_quarantine
            else ()
        )

        return RetrievalResponse(
            results=results,
            denied=tuple(
                sorted(denied, key=lambda entry: entry.object_id)
            ),
            quarantined=notices,
            generation=generation.generation,
            index_hash=generation.index_hash,
            candidates=len(candidates),
        )

    def exact(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        canonical_id: str,
        *,
        correlation_id: str = "",
    ) -> RetrievalResult | None:
        """Exact governed lookup by canonical id. None ⇒ not in the index."""

        response = self.retrieve(
            principal,
            context,
            RetrievalQuery(canonical_id=canonical_id),
            correlation_id=correlation_id,
        )
        return response.results[0] if response.results else None

    def load_record(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        canonical_id: str,
        *,
        correlation_id: str = "",
    ) -> "RetrievalObject | None":
        """Policy-guarded full-record load (I.5 answer-quality seam).

        Deny-before-load is preserved: the record loader runs only inside the
        ratified II.4 ``guard()`` primitive after an ALLOW decision on this
        exact resource. A missing header, a denied decision, or an unloaded
        record yields ``None`` — the body is never touched.
        """

        generation = self._index.require()
        access, _resource = self._authorize_record(
            principal, context, generation, canonical_id, correlation_id
        )
        if access is None or not access.allowed:
            return None
        return access.payload

    # -- quarantine ---------------------------------------------------------

    def _quarantine_notices(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        correlation_id: str,
    ) -> tuple[QuarantineNotice, ...]:
        generation = self._index.require()
        notices: list[QuarantineNotice] = []
        for entry in generation.quarantine:
            # Research gaps are research material (PRODUCT_EXPOSURE_RULES_V1).
            # Metadata-only decision: there is no body to load.
            decision = self._enforcement.authorize(
                principal,
                context,
                PolicyAction.QUERY,
                ResourcePolicyMetadata(
                    resource_type=PolicyResourceType.ARTIFACT,
                    resource_id=entry.source_path,
                    exposure=ProductExposure.RESEARCH_LAB,
                ),
                correlation_id=correlation_id,
            )
            if decision.allowed:
                notices.append(
                    QuarantineNotice(
                        source_path=entry.source_path, reason=entry.reason
                    )
                )
        return tuple(notices)

    # -- provenance navigation ---------------------------------------------

    def navigate(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        canonical_id: str,
        *,
        correlation_id: str = "",
    ) -> ProvenanceChain:
        """FOUND vs SUPPORTED with guarded hops: Claim -> Evidence -> Artifact.

        Missing links are reported as missing; a denied hop stops the chain
        and contributes a content-free denial entry.
        """

        generation = self._index.require()
        header = generation.header(canonical_id)
        if header is None:
            return ProvenanceChain(
                object_id=canonical_id,
                found=False,
                allowed=False,
                supported=False,
                support_classification="NO_SOURCE",
                support_gaps=("NOT_IN_INDEX",),
                missing=(
                    MissingLink(
                        from_id="", to_id=canonical_id, relation="", reason="NOT_IN_INDEX"
                    ),
                ),
            )

        access, _resource = self._authorize_record(
            principal, context, generation, canonical_id, correlation_id
        )
        if access is None or not access.allowed:
            decision = access.decision if access is not None else None
            return ProvenanceChain(
                object_id=canonical_id,
                found=True,
                allowed=False,
                supported=False,
                support_classification="NO_SOURCE",
                support_gaps=("POLICY_DENIED",),
                exposure=(
                    header.exposure.value if header.exposure is not None else "UNKNOWN"
                ),
                denied=(
                    DeniedResult(
                        object_id=canonical_id,
                        exposure=(
                            header.exposure.value
                            if header.exposure is not None
                            else "UNKNOWN"
                        ),
                        reason_code=(
                            decision.reason_code.value
                            if decision is not None
                            else "POLICY_UNKNOWN"
                        ),
                    ),
                ),
            )

        root = access.payload
        assert root is not None

        hops: list[ChainHop] = []
        missing: list[MissingLink] = []
        denied: list[DeniedResult] = []
        artifacts: list[ArtifactTrace] = []
        evidence_ids = list(root.support.evidence_ids)

        for link in root.related_ids:
            if link.relation != "supported_by":
                continue
            target_header = generation.header(link.target_id)
            if target_header is None:
                missing.append(
                    MissingLink(
                        from_id=canonical_id,
                        to_id=link.target_id,
                        relation=link.relation,
                        reason="NOT_IN_INDEX",
                    )
                )
                continue

            target_access, _ = self._authorize_record(
                principal, context, generation, link.target_id, correlation_id
            )
            if target_access is None or not target_access.allowed:
                decision = target_access.decision if target_access is not None else None
                denied.append(
                    DeniedResult(
                        object_id=link.target_id,
                        exposure=(
                            target_header.exposure.value
                            if target_header.exposure is not None
                            else "UNKNOWN"
                        ),
                        reason_code=(
                            decision.reason_code.value
                            if decision is not None
                            else "POLICY_UNKNOWN"
                        ),
                    )
                )
                missing.append(
                    MissingLink(
                        from_id=canonical_id,
                        to_id=link.target_id,
                        relation=link.relation,
                        reason="POLICY_DENIED",
                    )
                )
                continue

            evidence_record = target_access.payload
            hops.append(
                ChainHop(
                    from_id=canonical_id,
                    relation=link.relation,
                    to_id=link.target_id,
                    kind="EVIDENCE",
                )
            )
            if not evidence_record.provenance:
                missing.append(
                    MissingLink(
                        from_id=link.target_id,
                        to_id="",
                        relation="SUPPORTS",
                        reason="NO_SOURCE_ARTIFACT",
                    )
                )
                continue

            for provenance in evidence_record.provenance:
                artifact_resource = ResourcePolicyMetadata(
                    resource_type=PolicyResourceType.ARTIFACT,
                    resource_id=provenance.artifact_id,
                    exposure=target_header.exposure,
                )
                artifact_decision = self._enforcement.authorize(
                    principal,
                    context,
                    PolicyAction.QUERY,
                    artifact_resource,
                    correlation_id=correlation_id,
                )
                if not artifact_decision.allowed:
                    denied.append(
                        DeniedResult(
                            object_id=provenance.artifact_id,
                            exposure=(
                                target_header.exposure.value
                                if target_header.exposure is not None
                                else "UNKNOWN"
                            ),
                            reason_code=artifact_decision.reason_code.value,
                        )
                    )
                    missing.append(
                        MissingLink(
                            from_id=link.target_id,
                            to_id=provenance.artifact_id,
                            relation=provenance.relation,
                            reason="POLICY_DENIED",
                        )
                    )
                    continue
                hops.append(
                    ChainHop(
                        from_id=link.target_id,
                        relation=provenance.relation,
                        to_id=provenance.artifact_id,
                        kind="ARTIFACT",
                    )
                )
                artifacts.append(
                    ArtifactTrace(
                        artifact_id=provenance.artifact_id,
                        relation=provenance.relation,
                        source_class=provenance.source_class,
                        source_state=provenance.source_state,
                        content_identity=provenance.content_identity or "",
                        locator=provenance.locator,
                    )
                )

        return ProvenanceChain(
            object_id=canonical_id,
            found=True,
            allowed=True,
            supported=root.support.supported,
            support_classification=root.support.classification,
            support_gaps=root.support.gaps,
            status=root.status.value,
            exposure=(
                root.exposure_class.value
                if root.exposure_class is not None
                else "UNKNOWN"
            ),
            generation=generation.generation,
            hops=tuple(hops),
            evidence_ids=tuple(evidence_ids),
            artifacts=tuple(
                sorted(artifacts, key=lambda a: (a.artifact_id, a.relation))
            ),
            missing=tuple(missing),
            denied=tuple(denied),
        )


def _to_result(record: RetrievalObject, scored) -> RetrievalResult:
    return RetrievalResult(
        object_id=record.object_id,
        object_type=record.object_type.value,
        title=record.title,
        canonical_version=record.canonical_version,
        status=record.status.value,
        exposure=(
            record.exposure_class.value
            if record.exposure_class is not None
            else "UNKNOWN"
        ),
        layer=record.layer.value,
        market_scope=record.market_scope,
        model_family=record.header().model_family,
        retrieval_text=record.retrieval_text,
        generation=record.generation,
        found=True,
        supported=record.support.supported,
        support_classification=record.support.classification,
        support_gaps=record.support.gaps,
        exact_identity=scored.exact_identity,
        structured_hits=scored.structured_hits,
        lexical_hits=scored.lexical_hits,
        max_quote_scope=record.leakage.max_quote_scope,
    )


__all__ = [
    "RetrievalResult",
    "DeniedResult",
    "QuarantineNotice",
    "RetrievalResponse",
    "MissingLink",
    "ChainHop",
    "ArtifactTrace",
    "ProvenanceChain",
    "RetrievalService",
]
