"""I.5 deterministic QA kernel (PLAN §4–§9).

``QAService.ask`` turns a question into a validated, bounded, deterministic
``Answer`` — through the I.4 retrieval boundary ONLY:

- one input seam: ``RetrievalService.retrieve / load_record / navigate``;
- deny-before-load preserved (II.4 guard runs inside every call);
- no gateway, no corpus file, no Markdown, no backfill import, no provider;
- abstention is a first-class successful outcome.

The kernel never invents: every numeral, status, identity dimension, citation
and qualification it emits is copied from governed retrieval records or their
policy-guarded chains.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.forge.canonical import ObjectType, compare_claim_identity
from app.forge.identity import ForgePrincipal
from app.forge.policy import AuthorizationContext
from app.forge.qa.authority import (
    ACTION_GAP_TEXT,
    identity_qualification,
)
from app.forge.qa.contract import (
    Answer,
    AnswerClass,
    AnswerOutcome,
    Assertion,
    AssertionVerdict,
    Citation,
    ConflictKind,
    ConflictNote,
    ConflictResolution,
    DenialEntry,
    FollowUp,
    Gap,
    GapCode,
    Ladder,
    Qualification,
    QualificationCode,
    validate_answer,
)
from app.forge.qa.question import QuestionClass, classify_question
from app.forge.retrieval import RetrievalQuery, RetrievalResponse, RetrievalService

MAX_SCOPE_CLAIM_LOADS = 10

IDENTITY_DIMENSIONS = (
    "market",
    "event_definition",
    "conditioning_event",
    "clock_origin",
    "horizon",
    "tolerance",
    "eligibility",
    "implementation_semantics",
)

ACTIONABLE_LIMITATION = (
    "actionable answers are research/operator context, not personalized "
    "financial advice"
)
PARALLEL_POPULATIONS_LIMITATION = (
    "parallel populations are presented separately and never merged"
)
DOCTRINE_GAP_DETAIL = (
    "model doctrine/research context rather than a verified numerical claim"
)


@dataclass(frozen=True)
class _Target:
    result: object  # RetrievalResult
    record: object  # RetrievalObject


class QAService:
    """Deterministic answer quality over one published index generation."""

    def __init__(self, retrieval: RetrievalService) -> None:
        if not isinstance(retrieval, RetrievalService):
            raise TypeError("retrieval must be a RetrievalService")
        self._retrieval = retrieval

    @property
    def retrieval(self) -> RetrievalService:
        return self._retrieval

    # -- seam helpers -------------------------------------------------------

    def _load(self, principal, context, object_id, correlation_id):
        return self._retrieval.load_record(
            principal, context, object_id, correlation_id=correlation_id
        )

    def _merge_exact(self, principal, context, canonical_ids, correlation_id):
        """Multi-id questions: exact lookup per id, merged deterministically."""
        merged_results = []
        merged_denied = []
        seen: set[str] = set()
        denied_seen: set[str] = set()
        generation = 0
        index_hash = ""
        for canonical_id in canonical_ids:
            response = self._retrieval.retrieve(
                principal,
                context,
                RetrievalQuery(canonical_id=canonical_id),
                correlation_id=correlation_id,
            )
            generation = response.generation
            index_hash = response.index_hash
            for result in response.results:
                if result.object_id not in seen:
                    seen.add(result.object_id)
                    merged_results.append(result)
            for denied in response.denied:
                if denied.object_id not in denied_seen:
                    denied_seen.add(denied.object_id)
                    merged_denied.append(denied)
        return RetrievalResponse(
            results=tuple(merged_results),
            denied=tuple(sorted(merged_denied, key=lambda d: d.object_id)),
            quarantined=(),
            generation=generation,
            index_hash=index_hash,
            candidates=len(merged_results),
        )

    # -- public entry -------------------------------------------------------

    def ask(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        question: str,
        *,
        correlation_id: str = "",
    ) -> Answer:
        cq = classify_question(question or "")
        answer_class = AnswerClass(cq.question_class.value)
        scope = tuple(sorted({v for v in (cq.market, cq.model_family) if v}))

        if cq.canonical_id is None and not cq.tokens:
            # nothing was asked: abstain before touching the index (B5/A5)
            return validate_answer(
                Answer(
                    outcome=AnswerOutcome.OUT_OF_CORPUS,
                    ladder=Ladder(),
                    answer_class=answer_class,
                    scope=scope,
                    gaps=(
                        Gap(
                            code=GapCode.NOT_IN_INDEX,
                            detail="no governed object resolves this question",
                        ),
                    ),
                )
            )

        if len(cq.canonical_ids) > 1:
            response = self._merge_exact(
                principal, context, cq.canonical_ids, correlation_id
            )
        else:
            query = RetrievalQuery(
                canonical_id=cq.canonical_id,
                text=None if cq.canonical_id else (question or None) or None,
                market=cq.market,
                model_family=cq.model_family,
            )
            response = self._retrieval.retrieve(
                principal, context, query, correlation_id=correlation_id
            )
        denials = tuple(
            DenialEntry(
                object_id=d.object_id,
                exposure=d.exposure,
                reason_code=d.reason_code,
            )
            for d in response.denied
        )
        base = dict(
            answer_class=answer_class,
            scope=scope,
            denials=denials,
            generation=response.generation,
            index_hash=response.index_hash,
        )

        # -- no results: abstention paths (PLAN §6) -------------------------
        if not response.results:
            if response.denied:
                return validate_answer(
                    Answer(
                        outcome=AnswerOutcome.RESTRICTED,
                        ladder=Ladder(),
                        gaps=(
                            Gap(
                                code=GapCode.DENIED,
                                detail="withheld by exposure policy",
                            ),
                        ),
                        **base,
                    )
                )
            return validate_answer(
                Answer(
                    outcome=AnswerOutcome.OUT_OF_CORPUS,
                    ladder=Ladder(),
                    gaps=(
                        Gap(
                            code=GapCode.NOT_IN_INDEX,
                            detail="no governed object resolves this question",
                        ),
                    ),
                    **base,
                )
            )

        # -- load authorized candidates (deny ⇒ never loaded) ---------------
        targets: list[_Target] = []
        gaps: list[Gap] = []
        for result in response.results[:3]:
            record = self._load(
                principal, context, result.object_id, correlation_id
            )
            if record is None:
                gaps.append(
                    Gap(
                        code=GapCode.DENIED,
                        detail="record not loadable under this context",
                        object_id=result.object_id,
                    )
                )
                continue
            targets.append(_Target(result=result, record=record))

        if answer_class is AnswerClass.ACTIONABLE:
            # setup gate + Action Safety; claim route is handled inside when
            # the question carries an empirical signal
            outcome_bundle = self._actionable_bundle(
                principal, context, cq, targets, correlation_id, gaps
            )
        elif answer_class is AnswerClass.EMPIRICAL:
            claims = self._collect_claims(
                principal, context, cq, targets, correlation_id
            )
            if claims:
                outcome_bundle = self._with_model_context(
                    self._empirical_bundle(
                        principal, context, claims, correlation_id, gaps
                    ),
                    targets,
                )
            else:
                outcome_bundle = self._doctrine_fallback(targets, gaps)
        else:  # DESCRIPTIVE / COMPARATIVE without empirical signal
            outcome_bundle = self._descriptive_bundle(
                targets, cq, answer_class, gaps
            )

        return self._finalize(
            base=base,
            answer_class=answer_class,
            cq=cq,
            bundle=outcome_bundle,
            response=response,
            denials=denials,
        )

    # -- claim collection ----------------------------------------------------

    def _collect_claims(self, principal, context, cq, targets, correlation_id):
        """Resolve the CLAIM records this question may speak about.

        Candidate CLAIMs are always in scope. A MODEL/SETUP/EVIDENCE candidate
        pulls the claims that reference it (parent model, or evidence link) —
        never claims from an unrelated population.
        """
        claims: dict[str, _Target] = {}
        for target in targets:
            if target.record.object_type is ObjectType.CLAIM:
                claims[target.record.object_id] = target

        wanted_model = {
            t.record.object_id
            for t in targets
            if t.record.object_type is ObjectType.MODEL
        }
        wanted_evidence = {
            t.record.object_id
            for t in targets
            if t.record.object_type is ObjectType.EVIDENCE
        }
        for t in targets:
            if t.record.object_type is ObjectType.SETUP:
                wanted_model.update(t.record.parent_ids)

        if claims and not wanted_model and not wanted_evidence:
            return [claims[key] for key in sorted(claims)]

        response = self._retrieval.retrieve(
            principal,
            context,
            RetrievalQuery(
                object_type="CLAIM",
                market=cq.market,
                model_family=cq.model_family,
            ),
            correlation_id=correlation_id,
        )
        loaded = 0
        for result in response.results:
            if loaded >= MAX_SCOPE_CLAIM_LOADS:
                break
            if result.object_id in claims:
                continue
            record = self._load(principal, context, result.object_id, correlation_id)
            loaded += 1
            if record is None:
                continue
            claim_target = _Target(result=result, record=record)
            if wanted_model and set(record.parent_ids) & wanted_model:
                claims[record.object_id] = claim_target
            elif wanted_evidence and (
                set(record.support.evidence_ids) & wanted_evidence
                or any(
                    link.relation == "evidence_for"
                    and link.target_id in wanted_evidence
                    for link in record.related_ids
                )
            ):
                claims[record.object_id] = claim_target
        return [claims[key] for key in sorted(claims)]

    # -- bundles -------------------------------------------------------------
    # Each bundle: (assertions, claim_refs, evidence_refs, citations,
    #               qualifications, conflicts, gaps, limitations)

    def _with_model_context(self, bundle, targets):
        """Frozen retrieval order: canonical object → model card → claim.

        After the claim assertions (the substance), append the authorized
        MODEL/SETUP doctrine context when the bound allows it — the model's
        governed statement (lineage, layer ownership, limitations) travels
        with the answer.
        """
        if len(bundle.assertions) >= 3:
            return bundle
        existing = {a.object_id for a in bundle.assertions}
        extra_assertions = []
        extra_citations = []
        extra_qualifications = []
        extra_refs = []
        for target in targets:
            if len(bundle.assertions) + len(extra_assertions) >= 3:
                break
            record = target.record
            if record.object_type not in (ObjectType.MODEL, ObjectType.SETUP):
                continue
            if record.object_id in existing:
                continue
            assertion, citation, quals = self._descriptive_assertion(record)
            extra_assertions.append(assertion)
            if citation is not None:
                extra_citations.append(citation)
            extra_qualifications.extend(quals)
            extra_refs.append(record.object_id)
        if not extra_assertions:
            return bundle
        return _Bundle(
            assertions=bundle.assertions + tuple(extra_assertions),
            claim_refs=bundle.claim_refs + tuple(extra_refs),
            evidence_refs=bundle.evidence_refs,
            citations=tuple((bundle.citations + tuple(extra_citations))[:6]),
            qualifications=bundle.qualifications + tuple(extra_qualifications),
            conflicts=bundle.conflicts,
            gaps=bundle.gaps,
            limitations=bundle.limitations,
        )

    def _descriptive_bundle(self, targets, cq, answer_class, gaps):
        assertions = []
        citations = []
        qualifications = []
        limitations: list[str] = []
        claim_refs = []
        evidence_refs: list[str] = []
        for target in targets[:3]:
            record = target.record
            assertion, citation, quals = self._descriptive_assertion(record)
            assertions.append(assertion)
            claim_refs.append(record.object_id)
            if citation is not None:
                citations.append(citation)
            qualifications.extend(quals)
        if answer_class is AnswerClass.COMPARATIVE and len(assertions) >= 2:
            limitations.append(PARALLEL_POPULATIONS_LIMITATION)
        return _Bundle(
            assertions=tuple(assertions),
            claim_refs=tuple(claim_refs),
            evidence_refs=tuple(evidence_refs),
            citations=tuple(citations),
            qualifications=tuple(qualifications),
            conflicts=(),
            gaps=tuple(gaps),
            limitations=tuple(sorted(set(limitations))),
        )

    def _descriptive_assertion(self, record):
        from app.forge.qa.authority import (
            no_label_qualification,
            qualifier_qualifications,
            status_qualification,
        )

        label = label_for_status(record.status)
        verdict_name = _verdict_for(record.status, numerical=False)
        verdict = AssertionVerdict(verdict_name)
        quals: list[Qualification] = []
        if verdict is AssertionVerdict.QUALIFY:
            status_q = status_qualification(record.status)
            if status_q is not None:
                quals.append(status_q.model_copy(update={"object_id": record.object_id}))
        no_label = no_label_qualification(record.status)
        if no_label is not None:
            quals.append(no_label.model_copy(update={"object_id": record.object_id}))
        quals.extend(
            qualifier_qualifications(
                record.qualifiers,
                object_id=record.object_id,
                sample_n=record.structured.sample_n,
            )
        )

        citation = None
        for prov in sorted(
            record.provenance, key=lambda p: (p.relation, p.artifact_id)
        ):
            if prov.relation == "DEFINES":
                citation = Citation(
                    claim_id=record.object_id,
                    evidence_id="",
                    artifact_id=prov.artifact_id,
                    relation=prov.relation,
                    source_class=prov.source_class,
                    source_state=prov.source_state,
                    content_identity=prov.content_identity,
                    locator=prov.locator,
                )
                break
        assertion = Assertion(
            object_id=record.object_id,
            object_type=record.object_type.value,
            layer=record.layer.value,
            market_scope=record.market_scope,
            status=record.status.value,
            epistemic_label=label,
            text=record.retrieval_text,
            numerical=False,
            verdict=verdict,
            verdict_reason="" if verdict is AssertionVerdict.ASSERT else (
                quals[0].code.value if quals else ""
            ),
            claim_identity=record.structured.claim_identity,
            supported=record.support.supported,
            support_classification=record.support.classification,
            evidence_ids=record.support.evidence_ids,
            sample_n=record.structured.sample_n,
            qualifiers=record.qualifiers,
            generation=0,
            index_generation=record.generation,
        )
        return assertion, citation, tuple(quals)

    def _doctrine_fallback(self, targets, gaps):
        """Empirical question, no claim route: doctrine context + honest gap."""
        gaps.append(
            Gap(code=GapCode.NO_CLAIM_ROUTE, detail=DOCTRINE_GAP_DETAIL)
        )
        assertions = []
        citations = []
        qualifications = []
        claim_refs = []
        for target in targets[:3]:
            assertion, citation, quals = self._descriptive_assertion(
                target.record
            )
            assertions.append(assertion)
            claim_refs.append(target.record.object_id)
            if citation is not None:
                citations.append(citation)
            qualifications.extend(quals)
        return _Bundle(
            assertions=tuple(assertions),
            claim_refs=tuple(claim_refs),
            evidence_refs=(),
            citations=tuple(citations),
            qualifications=tuple(qualifications),
            conflicts=(),
            gaps=tuple(gaps),
            limitations=(),
        )

    def _actionable_bundle(
        self, principal, context, cq, targets, correlation_id, gaps
    ):
        limitations: list[str] = [ACTIONABLE_LIMITATION]
        setup_response = self._retrieval.retrieve(
            principal,
            context,
            RetrievalQuery(
                object_type="SETUP",
                market=cq.market,
                model_family=cq.model_family,
            ),
            correlation_id=correlation_id,
        )
        setup_found = False
        setup_targets: list[_Target] = []
        for result in setup_response.results[:1]:
            record = self._load(
                principal, context, result.object_id, correlation_id
            )
            if record is not None:
                setup_found = True
                setup_targets.append(_Target(result=result, record=record))

        qualifications: list[Qualification] = []
        if not setup_found:
            qualifications.append(
                Qualification(
                    code=QualificationCode.ACTION_GAP, text=ACTION_GAP_TEXT
                )
            )

        if cq.empirical_signal:
            claims = self._collect_claims(
                principal, context, cq, targets, correlation_id
            )
            if claims:
                bundle = self._with_model_context(
                    self._empirical_bundle(
                        principal, context, claims, correlation_id, gaps
                    ),
                    targets,
                )
                return _Bundle(
                    assertions=bundle.assertions,
                    claim_refs=bundle.claim_refs,
                    evidence_refs=bundle.evidence_refs,
                    citations=bundle.citations,
                    qualifications=tuple(qualifications)
                    + bundle.qualifications,
                    conflicts=bundle.conflicts,
                    gaps=bundle.gaps,
                    limitations=tuple(
                        sorted(set(limitations) | set(bundle.limitations))
                    ),
                )

        # no empirical route: setup + doctrine context, always qualified
        descriptive_targets = setup_targets or targets
        bundle = self._descriptive_bundle(
            descriptive_targets, cq, AnswerClass.DESCRIPTIVE, gaps
        )
        return _Bundle(
            assertions=bundle.assertions,
            claim_refs=bundle.claim_refs,
            evidence_refs=bundle.evidence_refs,
            citations=bundle.citations,
            qualifications=tuple(qualifications) + bundle.qualifications,
            conflicts=bundle.conflicts,
            gaps=bundle.gaps,
            limitations=tuple(sorted(set(limitations) | set(bundle.limitations))),
        )

    def _empirical_bundle(self, principal, context, claims, correlation_id, gaps):
        from app.forge.qa.authority import (
            no_label_qualification,
            qualifier_qualifications,
            status_qualification,
        )

        assertions: list[Assertion] = []
        citations: list[Citation] = []
        qualifications: list[Qualification] = []
        claim_refs: list[str] = []
        evidence_refs: list[str] = []
        evidence_cache: dict[str, object] = {}

        for target in claims:
            record = target.record
            chain = self._retrieval.navigate(
                principal, context, record.object_id, correlation_id=correlation_id
            )
            supported = bool(
                record.support.supported
                and chain.allowed
                and chain.supported
            )

            if not chain.allowed or chain.denied:
                assertions.append(
                    self._claim_assertion(
                        record, AssertionVerdict.GAP, label=None, quals=()
                    )
                )
                gaps.append(
                    Gap(
                        code=GapCode.DENIED,
                        detail="provenance chain denied under this context",
                        object_id=record.object_id,
                    )
                )
                continue

            if not supported:
                code = GapCode.NOT_SUPPORTED
                for gap_name in record.support.gaps:
                    if gap_name == "NO_EVIDENCE_REFERENCE":
                        code = GapCode.NO_EVIDENCE_REFERENCE
                        break
                    if gap_name == "NO_SOURCE_ARTIFACT":
                        code = GapCode.NO_SOURCE_ARTIFACT
                        break
                detail = (
                    "; ".join(record.support.gaps)
                    if record.support.gaps
                    else f"support classification {record.support.classification}"
                )
                if record.support.classification == "NON_EMPIRICAL_SOURCE":
                    detail = (
                        "visual or conversation-derived source cannot "
                        "establish empirical support"
                    )
                assertions.append(
                    self._claim_assertion(
                        record, AssertionVerdict.GAP, label=None, quals=()
                    )
                )
                gaps.append(
                    Gap(code=code, detail=detail, object_id=record.object_id)
                )
                continue

            # supported: status authority + qualifications
            verdict_name = _verdict_for(record.status, numerical=True)
            verdict = AssertionVerdict(verdict_name)
            label = label_for_status(record.status)
            claim_quals: list[Qualification] = []
            if verdict is AssertionVerdict.QUALIFY:
                status_q = status_qualification(record.status)
                if status_q is not None:
                    claim_quals.append(
                        status_q.model_copy(update={"object_id": record.object_id})
                    )
            no_label = no_label_qualification(record.status)
            if no_label is not None:
                claim_quals.append(
                    no_label.model_copy(update={"object_id": record.object_id})
                )

            # supporting evidence records (sample_n + citation triples)
            sample_n = None
            claim_citations: list[Citation] = []
            missing_evidence: list[str] = []
            for evidence_id in sorted(set(record.support.evidence_ids)):
                evidence = evidence_cache.get(evidence_id)
                if evidence is None:
                    evidence = self._load(
                        principal, context, evidence_id, correlation_id
                    )
                    evidence_cache[evidence_id] = evidence
                if evidence is None:
                    # the governed evidence id does not resolve to a
                    # loadable record: disclose, never cite by similarity
                    missing_evidence.append(evidence_id)
                    continue
                if sample_n is None and evidence.structured.sample_n is not None:
                    sample_n = evidence.structured.sample_n
                for prov in evidence.provenance:
                    claim_citations.append(
                        Citation(
                            claim_id=record.object_id,
                            evidence_id=evidence_id,
                            artifact_id=prov.artifact_id,
                            relation=prov.relation,
                            source_class=prov.source_class,
                            source_state=prov.source_state,
                            content_identity=prov.content_identity,
                            locator=prov.locator,
                        )
                    )
            if missing_evidence:
                # missing source/evidence is a disclosed gap (F5), never a
                # citation to a merely similar retrieved document (F6)
                assertions.append(
                    self._claim_assertion(
                        record, AssertionVerdict.GAP, label=None, quals=()
                    )
                )
                gaps.append(
                    Gap(
                        code=GapCode.NO_SOURCE_ARTIFACT,
                        detail=(
                            "supporting evidence id does not resolve to a "
                            "loadable governed record"
                        ),
                        object_id=record.object_id,
                    )
                )
                continue
            claim_citations.sort(
                key=lambda c: (
                    0 if c.relation == "DEFINES" else 1,
                    c.evidence_id,
                    c.artifact_id,
                )
            )

            claim_quals.extend(
                qualifier_qualifications(
                    record.qualifiers,
                    object_id=record.object_id,
                    sample_n=sample_n,
                )
            )
            identity = record.structured.claim_identity
            if identity is not None and any(
                getattr(identity, dim) == "NOT_SPECIFIED_IN_SOURCE"
                for dim in ("market", "event_definition")
            ):
                claim_quals.append(identity_qualification())

            if verdict is AssertionVerdict.GAP:
                assertions.append(
                    self._claim_assertion(
                        record, verdict, label=label, quals=claim_quals
                    )
                )
                gaps.append(
                    Gap(
                        code=GapCode.NOT_SUPPORTED,
                        detail="descriptive status cannot support a numerical assertion",
                        object_id=record.object_id,
                    )
                )
                continue

            assertions.append(
                self._claim_assertion(
                    record, verdict, label=label, quals=claim_quals
                )
            )
            claim_refs.append(record.object_id)
            evidence_refs.extend(sorted(set(record.support.evidence_ids)))
            citations.extend(claim_citations)
            qualifications.extend(claim_quals)

        conflicts = self._detect_conflicts(claims)
        return _Bundle(
            assertions=tuple(assertions),
            claim_refs=tuple(sorted(set(claim_refs))),
            evidence_refs=tuple(sorted(set(evidence_refs))),
            citations=tuple(citations[:6]),
            qualifications=tuple(qualifications),
            conflicts=tuple(conflicts),
            gaps=tuple(gaps),
            limitations=(),
        )

    def _claim_assertion(self, record, verdict, *, label, quals):
        identity = record.structured.claim_identity
        verdict_reason = ""
        if verdict is AssertionVerdict.QUALIFY and quals:
            verdict_reason = quals[0].code.value
        elif verdict is AssertionVerdict.GAP:
            verdict_reason = GapCode.NOT_SUPPORTED.value
        return Assertion(
            object_id=record.object_id,
            object_type=record.object_type.value,
            layer=record.layer.value,
            market_scope=record.market_scope,
            status=record.status.value,
            epistemic_label=label,
            text=record.retrieval_text,
            numerical=True,
            verdict=verdict,
            verdict_reason=verdict_reason,
            claim_identity=identity,
            supported=record.support.supported,
            support_classification=record.support.classification,
            evidence_ids=record.support.evidence_ids,
            sample_n=record.structured.sample_n,
            qualifiers=record.qualifiers,
            generation=0,
            index_generation=record.generation,
        )

    # -- conflicts (PLAN §7) -------------------------------------------------

    def _detect_conflicts(self, claims) -> list[ConflictNote]:
        notes: list[ConflictNote] = []
        ids = sorted(t.record.object_id for t in claims)
        by_id = {t.record.object_id: t.record for t in claims}
        for i, left_id in enumerate(ids):
            for right_id in ids[i + 1:]:
                left, right = by_id[left_id], by_id[right_id]
                if left.conflict.contradicts_ids and right_id in left.conflict.contradicts_ids:
                    notes.append(
                        self._conflict_note(
                            left, right, ConflictKind.DECLARED_CONTRADICTS,
                            "contradicts_ids",
                        )
                    )
                    continue
                if right.conflict.contradicts_ids and left_id in right.conflict.contradicts_ids:
                    notes.append(
                        self._conflict_note(
                            right, left, ConflictKind.DECLARED_CONTRADICTS,
                            "contradicts_ids",
                        )
                    )
                    continue
                li, ri = left.structured.claim_identity, right.structured.claim_identity
                if li is None or ri is None:
                    continue
                comparison = compare_claim_identity(li, ri)
                if (
                    comparison.value == "SAME_POPULATION"
                    and left.status.value != right.status.value
                ):
                    notes.append(
                        self._conflict_note(
                            left, right,
                            ConflictKind.MATCHED_IDENTITY_DIVERGENCE,
                            "SAME_POPULATION",
                        )
                    )
        return notes

    @staticmethod
    def _conflict_note(left, right, kind, basis) -> ConflictNote:
        claim_ids = tuple(sorted((left.object_id, right.object_id)))
        status_by_id = {
            left.object_id: left.status.value,
            right.object_id: right.status.value,
        }
        generation_by_id = {
            left.object_id: left.conflict.generation or left.canonical_version,
            right.object_id: right.conflict.generation or right.canonical_version,
        }
        return ConflictNote(
            kind=kind,
            basis=basis,
            claim_ids=claim_ids,
            # statuses/generations parallel claim_ids (auditable)
            statuses=tuple(status_by_id[cid] for cid in claim_ids),
            generations=tuple(generation_by_id[cid] for cid in claim_ids),
            evidence_ids=tuple(
                sorted(
                    set(left.support.evidence_ids)
                    | set(right.support.evidence_ids)
                )
            ),
            resolution=ConflictResolution.DOWNGRADE_AND_EXPOSE_BOTH,
            matched_dimensions=IDENTITY_DIMENSIONS
            if basis == "SAME_POPULATION"
            else (),
        )

    # -- aggregation ---------------------------------------------------------

    def _finalize(self, *, base, answer_class, cq, bundle, response, denials):
        assertions = bundle.assertions
        gaps = list(bundle.gaps)
        qualifications = list(bundle.qualifications)
        conflicts = list(bundle.conflicts)

        non_gap = [a for a in assertions if a.verdict is not AssertionVerdict.GAP]
        gap_assertions = [a for a in assertions if a.verdict is AssertionVerdict.GAP]

        # Doctrine-context disclosure: an assertion without an independent
        # empirical chain can be stated only as doctrine — disclose the gap.
        for assertion in non_gap:
            if not assertion.supported and not assertion.numerical:
                gaps.append(
                    Gap(
                        code=GapCode.NO_EVIDENCE_REFERENCE,
                        detail=(
                            "no independent empirical source links this "
                            "object; doctrine context only"
                        ),
                        object_id=assertion.object_id,
                    )
                )

        # outcome decision (PLAN §6, first match wins)
        if conflicts and non_gap:
            outcome = AnswerOutcome.CONTRADICTED
        elif not non_gap:
            outcome = AnswerOutcome.UNSUPPORTED
        elif gaps or gap_assertions:
            outcome = AnswerOutcome.PARTIAL
        elif qualifications or any(
            a.verdict is AssertionVerdict.QUALIFY for a in assertions
        ) or any(a.epistemic_label is None for a in assertions):
            outcome = AnswerOutcome.ANSWERABLE_QUALIFIED
        else:
            outcome = AnswerOutcome.ANSWERABLE

        # ladder
        retrieved = True
        supported = any(a.supported for a in non_gap)
        assertable = (
            bool(non_gap)
            and supported
            and outcome
            in (
                AnswerOutcome.ANSWERABLE,
                AnswerOutcome.ANSWERABLE_QUALIFIED,
                AnswerOutcome.PARTIAL,
                AnswerOutcome.CONTRADICTED,
            )
        )
        if any(a.numerical for a in non_gap):
            # empirical rung: every asserted numerical statement must cite
            explainable = assertable and all(
                any(c.claim_id == a.object_id for c in bundle.citations)
                for a in non_gap
            )
        else:
            explainable = assertable and bool(bundle.citations or not non_gap)
        ladder = Ladder(
            retrieved=retrieved,
            supported=supported,
            assertable=assertable,
            explainable=explainable,
        )

        # epistemic label
        if outcome is AnswerOutcome.UNSUPPORTED:
            label = "INSUFFICIENT_EVIDENCE"
        elif outcome in (AnswerOutcome.OUT_OF_CORPUS, AnswerOutcome.RESTRICTED):
            label = None
        else:
            label = next(
                (a.epistemic_label for a in assertions if a.epistemic_label),
                None,
            )

        # follow-ups: authorized titles only
        asserted = {a.object_id for a in assertions}
        follow_ups = tuple(
            FollowUp(object_id=r.object_id, text=r.title)
            for r in response.results
            if r.object_id not in asserted
        )[:3]

        answer = Answer(
            outcome=outcome,
            answer_class=answer_class,
            ladder=ladder,
            epistemic_label=label,
            scope=base["scope"],
            assertions=assertions,
            claim_refs=bundle.claim_refs,
            evidence_refs=bundle.evidence_refs,
            citations=bundle.citations,
            qualifications=tuple(qualifications),
            conflicts=tuple(conflicts),
            gaps=tuple(gaps),
            limitations=bundle.limitations,
            denials=denials,
            follow_ups=follow_ups,
            generation=base["generation"],
            index_hash=base["index_hash"],
        )
        return validate_answer(answer)


@dataclass(frozen=True)
class _Bundle:
    assertions: tuple
    claim_refs: tuple
    evidence_refs: tuple
    citations: tuple
    qualifications: tuple
    conflicts: tuple
    gaps: tuple
    limitations: tuple


def _verdict_for(status, *, numerical: bool) -> str:
    from app.forge.qa.authority import status_authority_verdict

    return status_authority_verdict(status, numerical=numerical)


def label_for_status(status):
    from app.forge.qa.contract import label_for_status as _impl

    return _impl(status)


__all__ = ["QAService", "IDENTITY_DIMENSIONS"]
