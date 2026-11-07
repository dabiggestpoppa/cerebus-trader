"""IV.2 orchestration: immutable plan -> authorized retrieval bundle."""

from __future__ import annotations

from dataclasses import replace

from app.forge.ask_cerebus.interpreter.enums import (
    AmbiguityOutcome,
    AmbiguityReason,
    EntityKind,
)
from app.forge.ask_cerebus.retrieval.bundle import AuthorizedRetrievalBundle
from app.forge.ask_cerebus.retrieval.claims import ClaimEvidenceJoiner
from app.forge.ask_cerebus.retrieval.conflicts import assess as assess_conflicts
from app.forge.ask_cerebus.retrieval.enums import (
    LimitationCode,
    RejectionClass,
    RetrievalOutcome,
)
from app.forge.ask_cerebus.retrieval.intelligence import (
    SnapshotContext,
    SnapshotProviderPort,
    route_intelligence,
)
from app.forge.ask_cerebus.retrieval.lineage import (
    build_lineage_refs,
    lineage_limitations,
)
from app.forge.ask_cerebus.retrieval.negative import (
    build_negative_refs,
    negative_limitations,
)
from app.forge.ask_cerebus.retrieval.query_builder import build_targets
from app.forge.ask_cerebus.retrieval.refs import (
    IntelligenceRef,
    Limitation,
    NegativeRef,
    Refusal,
    SemanticPassage,
)
from app.forge.ask_cerebus.retrieval.semantic import (
    EmptySemanticIndex,
    SemanticIndexPort,
)
from app.forge.ask_cerebus.retrieval.structured import StructuredResolver
from app.forge.ask_cerebus.retrieval.trace import RetrievalTrace, rejection_counts
from app.forge.ask_cerebus.retrieval.versions import (
    RETRIEVAL_CONTRACT_V1,
    SUPPORTED_RETRIEVAL_CONTRACT_VERSIONS,
)
from app.forge.retrieval.index import IndexNotBuilt, RetrievalIndex
from app.forge.retrieval.service import RetrievalService
from app.forge.service.policy_enforcement import ForgePolicyEnforcementService
from app.forge.setup_engine.registry import SetupRegistry

_AMBIGUITY_LIMITATIONS = {
    AmbiguityReason.UNSUPPORTED_IDENTITY: LimitationCode.UNSUPPORTED_IDENTITY,
    AmbiguityReason.UNAVAILABLE_GENERATION: LimitationCode.UNAVAILABLE_GENERATION,
    AmbiguityReason.UNSUPPORTED_STATISTIC: LimitationCode.UNSUPPORTED_STATISTIC,
    AmbiguityReason.DEPTH_CAPPED: LimitationCode.DEPTH_CAPPED,
}


def _plan_limitations(plan) -> tuple[Limitation, ...]:
    out: list[Limitation] = []
    for ambiguity in plan.ambiguities:
        code = _AMBIGUITY_LIMITATIONS.get(ambiguity.code)
        if code is not None:
            if all(
                existing.code is not code or existing.object_id != (ambiguity.candidates[0] if ambiguity.candidates else "")
                for existing in out
            ):
                out.append(
                    Limitation(
                        code,
                        ambiguity.candidates[0] if ambiguity.candidates else "",
                        ambiguity.detail,
                    )
                )
        elif ambiguity.material:
            out.append(Limitation(LimitationCode.MATERIAL_AMBIGUITY, "", ambiguity.code.value))
    return tuple(out)


class AskCerebusRetrievalService:
    """Policy-first retrieval composition over a published Book I generation."""

    def __init__(
        self,
        index: RetrievalIndex,
        *,
        enforcement: ForgePolicyEnforcementService | None = None,
        semantic: SemanticIndexPort | None = None,
        snapshot_provider: SnapshotProviderPort | None = None,
        setup_registry: SetupRegistry | None = None,
    ) -> None:
        if not isinstance(index, RetrievalIndex):
            raise TypeError("index must be a RetrievalIndex")
        self._index = index
        self._enforcement = enforcement or ForgePolicyEnforcementService()
        self._retrieval = RetrievalService(index, self._enforcement)
        self._semantic = semantic or EmptySemanticIndex()
        self._snapshot_provider = snapshot_provider
        self._setup_registry = setup_registry or SetupRegistry()

    @property
    def retrieval(self) -> RetrievalService:
        return self._retrieval

    def retrieve(
        self,
        plan,
        principal,
        context,
        *,
        snapshot_context: SnapshotContext | None = None,
        correlation_id: str = "",
        semantic_limit: int = 8,
    ) -> AuthorizedRetrievalBundle:
        if getattr(plan, "query_contract_version", None) not in (None,):
            # IV.1 only exposes one supported version at this head; reject any
            # foreign contract rather than coercing it.
            pass
        if getattr(plan, "plan_id", "") == "":
            return self._refused(plan, "PLAN_ID_MISSING", "MALFORMED_REQUEST")
        if not isinstance(getattr(plan, "query_contract_version", ""), str):  # pragma: no cover
            return self._refused(plan, "UNSUPPORTED_CONTRACT", "UNSUPPORTED_PLAN_CONTRACT")
        if getattr(plan, "query_contract_version", "") not in SUPPORTED_RETRIEVAL_CONTRACT_VERSIONS:
            # IV.1 uses ASK_QUERY_CONTRACT_V1; the retrieval contract is
            # independent, so only an explicitly mismatched retrieval marker
            # is refused here. Plans without one are valid IV.1 plans.
            if getattr(plan, "query_contract_version", "").startswith("RETRIEVAL_"):
                return self._refused(plan, "UNSUPPORTED_CONTRACT", "UNSUPPORTED_PLAN_CONTRACT")

        try:
            generation = self._index.require()
        except IndexNotBuilt:
            return self._refused(plan, "INDEX_NOT_BUILT", "RETRIEVAL_UNAVAILABLE")

        targets = build_targets(plan)
        try:
            resolver = StructuredResolver(self._retrieval, self._setup_registry)
            structured = resolver.resolve(
                plan, targets, principal, context, correlation_id=correlation_id
            )
        except Exception as exc:  # fail closed, never leak the exception text
            return self._refused(plan, type(exc).__name__, "RETRIEVAL_UNAVAILABLE")

        joiner = ClaimEvidenceJoiner(self._retrieval)
        join = joiner.join(
            structured.claim_ids, principal, context, correlation_id=correlation_id
        )

        limitations = (
            structured.limitations
            + join.limitations
            + lineage_limitations(structured.records)
            + _plan_limitations(plan)
        )
        refusals = structured.refusals

        lineage_refs = build_lineage_refs(structured.records)
        negative_refs = build_negative_refs(structured.records)
        for claim in join.claim_refs:
            if claim.status in (
                "PARKED",
                "SUPERSEDED",
                "FALSIFIED",
                "NO_GO",
                "INTERNAL_CONTRADICTION",
                "IMPLEMENTATION_NOT_PARITY_SAFE",
            ):
                negative_refs = negative_refs + (
                    NegativeRef(claim.claim_id, claim.status, claim.generation),
                )
        for evidence in join.evidence_refs:
            if evidence.status in (
                "PARKED",
                "SUPERSEDED",
                "FALSIFIED",
                "NO_GO",
                "INTERNAL_CONTRADICTION",
                "IMPLEMENTATION_NOT_PARITY_SAFE",
            ):
                negative_refs = negative_refs + (
                    NegativeRef(evidence.evidence_id, evidence.status),
                )
        limitations = limitations + negative_limitations(negative_refs)

        intelligence_refs: tuple[IntelligenceRef, ...] = ()
        if plan.requires_live_intelligence or plan.time_scope.value in (
            "CURRENT",
            "AS_OF",
            "HISTORICAL_RESEARCH",
        ):
            intelligence = route_intelligence(
                plan,
                snapshot_context,
                self._snapshot_provider,
                correlation_id=correlation_id,
            )
            intelligence_refs = intelligence.refs
            limitations = limitations + intelligence.limitations
            refusals = refusals + intelligence.refusals

        conflict = assess_conflicts(join.claim_refs)
        limitations = limitations + conflict.limitations

        allowed_ids = frozenset(
            [ref.object_id for ref in structured.canonical_refs]
            + [ref.claim_id for ref in join.claim_refs]
            + [ref.evidence_id for ref in join.evidence_refs]
        )
        semantic_results = self._semantic.search(
            " ".join(targets.text_terms),
            allowed_ids,
            semantic_limit,
        )
        rejections: list[RejectionClass] = list(structured.rejections)
        semantic_refs: list[SemanticPassage] = []
        for candidate in semantic_results:
            if candidate.object_id not in allowed_ids:
                rejections.append(RejectionClass.SEMANTIC_UNAUTHORIZED)
                limitations = limitations + (
                    Limitation(LimitationCode.POLICY_DENIED, "SEMANTIC"),
                )
                continue
            semantic_refs.append(
                SemanticPassage(
                    object_id=candidate.object_id,
                    text=candidate.text,
                    status="AUTHORIZED",
                    quote_scope=candidate.quote_scope,
                    support_classification="SUPPORT_ONLY",
                    score=candidate.score,
                )
            )
            for record in structured.records:
                if (
                    record.object_id == candidate.object_id
                    and record.retrieval_text
                    and candidate.text.strip() != record.retrieval_text.strip()
                ):
                    limitations = limitations + (
                        Limitation(
                            LimitationCode.SOURCE_DISAGREEMENT,
                            candidate.object_id,
                        ),
                    )
            if candidate.quote_scope == "NONE":
                limitations = limitations + (
                    Limitation(LimitationCode.LIMITED_QUOTE_SCOPE, candidate.object_id),
                )
        limitations = tuple(dict.fromkeys(limitations))

        selected_ids = tuple(
            sorted(
                dict.fromkeys(
                    [ref.object_id for ref in structured.canonical_refs]
                    + [ref.claim_id for ref in join.claim_refs]
                    + [ref.evidence_id for ref in join.evidence_refs]
                    + [ref.object_id for ref in lineage_refs]
                    + [ref.object_id for ref in negative_refs]
                    + [ref.object_id for ref in semantic_refs]
                )
            )
        )
        snapshot_ids = tuple(
            ref.snapshot_id for ref in intelligence_refs if ref.snapshot_id
        )
        generations = tuple(
            sorted(
                {
                    ref.generation
                    for ref in structured.canonical_refs
                    if ref.generation
                }
                | {ref.generation for ref in lineage_refs if ref.generation}
            )
        )

        if not structured.canonical_refs and not semantic_refs and not intelligence_refs:
            if not limitations and not refusals:
                limitations = (
                    Limitation(LimitationCode.RETRIEVAL_UNAVAILABLE, plan.plan_id),
                )
            elif not any(
                limitation.code is LimitationCode.UNRESOLVED_IDENTITY
                for limitation in limitations
            ):
                limitations = limitations + (
                    Limitation(LimitationCode.UNRESOLVED_IDENTITY, plan.plan_id),
                )

        draft = AuthorizedRetrievalBundle(
            query_plan_id=plan.plan_id,
            retrieval_contract_version=RETRIEVAL_CONTRACT_V1,
            canonical_refs=tuple(sorted(structured.canonical_refs, key=lambda r: r.object_id)),
            claim_refs=tuple(sorted(join.claim_refs, key=lambda r: r.claim_id)),
            evidence_refs=tuple(sorted(join.evidence_refs, key=lambda r: r.evidence_id)),
            intelligence_refs=tuple(
                sorted(intelligence_refs, key=lambda r: (r.request_kind, r.snapshot_id))
            ),
            lineage_refs=lineage_refs,
            semantic_passages=tuple(sorted(semantic_refs, key=lambda r: (-r.score, r.object_id))),
            negative_refs=negative_refs,
            limitations=limitations,
            refusals=tuple(refusals),
            trace=None,
            selected_generation=generation.generation,
            selected_index_hash=generation.index_hash,
        )
        trace = RetrievalTrace(
            plan_id=plan.plan_id,
            contract_version=RETRIEVAL_CONTRACT_V1,
            outcome=draft.outcome,
            index_generation=generation.generation,
            index_hash=generation.index_hash,
            selected_ids=selected_ids,
            claim_ids=tuple(ref.claim_id for ref in draft.claim_refs),
            evidence_ids=tuple(ref.evidence_id for ref in draft.evidence_refs),
            snapshot_ids=snapshot_ids,
            generations=generations,
            rejection_counts=rejection_counts(rejections),
        ).finalized()
        return replace(draft, trace=trace).finalized()

    def _refused(self, plan, detail: str, code: str) -> AuthorizedRetrievalBundle:
        from .enums import RefusalCode

        try:
            refusal_code = RefusalCode(code)
        except ValueError:
            refusal_code = RefusalCode.RETRIEVAL_UNAVAILABLE
        draft = AuthorizedRetrievalBundle(
            query_plan_id=getattr(plan, "plan_id", "") or "PLAN.UNKNOWN",
            retrieval_contract_version=RETRIEVAL_CONTRACT_V1,
            refusals=(Refusal(refusal_code, detail[:64]),),
        )
        trace = RetrievalTrace(
            plan_id=draft.query_plan_id,
            contract_version=RETRIEVAL_CONTRACT_V1,
            outcome=RetrievalOutcome.REFUSED,
        ).finalized()
        return replace(draft, trace=trace).finalized()


__all__ = ["AskCerebusRetrievalService"]
