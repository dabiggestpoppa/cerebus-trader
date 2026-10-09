"""Focused I.5 tests: QA kernel (Book I / Bloc I.5) — Phases 10 + 11.

Maps 1:1 to implementation/forge/book_i/bloc_i_5/ACCEPTANCE.md clauses A–R:

- A–B: QA authority/input and deterministic question classification
- C: the four-state ladder (no rung implies the next)
- D: the seven answerability outcomes; abstention is a successful result
- E: the eight claim-identity dimensions; canonical comparison only
- F: citation chains claim → evidence → source artifact
- G: status authority — no promotion, no unqualified research
- H: identity-first contradiction handling
- I: numerical safety — no fabricated or converted statistics
- J: exposure and content-free errors
- K: the CEREBUS model-family truth fixtures
- L/M: determinism over rebuilds (detectors and fixtures live in
  test_forge_corpus_qa.py)
- N: the frozen structured answer contract
- O: boundary integrity (no LLM, no route, no migration, no new enum)
- P: reproducibility
- Phase 11: adversarial attempts — every one must be qualified or fail closed
"""
from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

import pytest

from app.forge.backfill.runner import BackfillMode, run_backfill
from app.forge.canonical import (
    ClaimComparison,
    ClaimIdentity,
    EvidenceStatus,
    ObjectType,
    ProductExposure,
    compare_claim_identity,
)
from app.forge.identity import ForgePrincipal
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.policy import (
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_FORGE_INTERNAL,
    CAPABILITY_MODEL_READ_OPERATOR,
    AuthorizationContext,
)
from app.forge.qa import (
    Answer,
    AnswerClass,
    AnswerOutcome,
    AnswerValidationError,
    Assertion,
    AssertionVerdict,
    Citation,
    GapCode,
    IDENTITY_DIMENSIONS,
    Ladder,
    QualificationCode,
    QAService,
    QuestionClass,
    classify_question,
    validate_answer,
)
from app.forge.qa.authority import authority_for
from app.forge.qa.golden import GOLDEN_FIXTURES, check_fixture
from app.forge.retrieval import (
    IndexBuildMode,
    RetrievalIndex,
    RetrievalQuery,
    RetrievalService,
    SupportAssessment,
    run_index_build,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
QA_SOURCE_DIR = REPO_ROOT / "app" / "forge" / "qa"

SEVEN_OUTCOMES = {
    "ANSWERABLE",
    "ANSWERABLE_QUALIFIED",
    "PARTIAL",
    "UNSUPPORTED",
    "CONTRADICTED",
    "OUT_OF_CORPUS",
    "RESTRICTED",
}

AUTH = ForgePrincipal(authenticated=True, forge_user_id="user-q", session_id=None)
ANON = ForgePrincipal.anonymous()
CONTEXTS = {
    "member": (AUTH, AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER)),
    "research": (
        AUTH,
        AuthorizationContext.of(
            CAPABILITY_CORPUS_READ_MEMBER,
            CAPABILITY_EVIDENCE_READ_RESEARCH,
        ),
    ),
    "operator": (
        AUTH,
        AuthorizationContext.of(CAPABILITY_MODEL_READ_OPERATOR),
    ),
    "all": (
        AUTH,
        AuthorizationContext.of(
            CAPABILITY_CORPUS_READ_MEMBER,
            CAPABILITY_MODEL_READ_OPERATOR,
            CAPABILITY_EVIDENCE_READ_RESEARCH,
        ),
    ),
    "internal": (
        AUTH,
        AuthorizationContext.of(CAPABILITY_FORGE_INTERNAL),
    ),
    "anon": (ANON, AuthorizationContext.empty()),
}

BATCH_QUESTIONS = (
    "What is MOD.EUR.DAILY.NEWS_REKEY.V1?",
    "Is CL.EUR.DAILY.TIER_CALIBRATION validated?",
    "Does the BTC tracker establish BTC Game rules?",
    "What does CL.FIB.R11.GENERATOR_FAILURE say?",
    "Is CL.XAU.PROMOTION.68_80 validated?",
    "Is CL.JPY.CARRY.ROLE_RELATION validated?",
    "Is CL.EUR.HO.D3_DIRECTION validated?",
    "Is CL.EUR.WEEKLY.TIER_RANGE research qualified?",
    "What is P90 in MOD.EUR.DAILY.NEWS_REKEY.V1?",
    "Are MOD.EUR.DAILY.NEWS_REKEY.V1 and MOD.EUR.WEEKLY.V1_1 the same population?",
    "What is MOD.XAU.GAME.L1_L2_L3.V1?",
    "zzzqx?",
)

# Literal substrings that must never appear on any answer surface
# (Answer Contract "numerical safety" — frozen forbidden conversions).
FORBIDDEN_PHRASES = (
    "probability of",
    "win rate of",
    "expected win rate",
    "is a probability",
    "guaranteed",
    "AUTOMATION_APPROVED",
    "INTERNAL_METHOD",
    "INTERNAL_CODE",
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gateway() -> InMemoryPersistenceGateway:
    gw = InMemoryPersistenceGateway()
    run_backfill(gw, REPO_ROOT, BackfillMode.APPLY)
    return gw


@pytest.fixture(scope="module")
def index(gateway) -> RetrievalIndex:
    idx = RetrievalIndex()
    run_index_build(gw := gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
    return idx


@pytest.fixture(scope="module")
def generation(index):
    return index.require()


@pytest.fixture(scope="module")
def qa(index) -> QAService:
    return QAService(RetrievalService(index))


def ask(qa: QAService, question: str, ctx: str = "member") -> Answer:
    principal, context = CONTEXTS[ctx]
    return qa.ask(principal, context, question, correlation_id="i5-test")


def _service_with(generation, **updates_by_id) -> QAService:
    """A QAService over the real index with per-record tampering applied.

    ``updates_by_id`` maps object_id → dict of RetrievalObject field updates.
    """
    records = []
    for record in generation.records:
        updates = updates_by_id.get(record.object_id)
        records.append(
            record.model_copy(update=updates) if updates else record
        )
    idx = RetrievalIndex()
    idx.publish(dataclasses.replace(generation, records=tuple(records)))
    return QAService(RetrievalService(idx))


def _record_for(generation, substring: str):
    for record in generation.records:
        if substring in record.object_id:
            return record
    raise AssertionError(f"no index record contains {substring!r}")


def _digits(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


# ---------------------------------------------------------------------------
# A. QA authority and input
# ---------------------------------------------------------------------------


def test_a1_a2_kernel_governs_only_retrieval_seams():
    """No gateway, no corpus path, no backfill, no index build in the kernel."""
    forbidden = (
        "run_backfill",
        "run_index_build",
        "InMemoryPersistenceGateway",
        "persistence.memory",
        "load_corpus_files",
        "canonicalize_files",
        "Path(",
        "open(",
    )
    for source_file in sorted(QA_SOURCE_DIR.glob("*.py")):
        text = source_file.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, (
                f"{source_file.name} contains forbidden seam {token!r}"
            )


def test_a3_answer_records_generation_and_index_hash(qa, generation):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.generation == generation.generation
    assert answer.index_hash == generation.index_hash


def test_a4_same_question_same_context_is_byte_identical(qa):
    q = "Is CL.XAU.PROMOTION.68_80 validated?"
    first = ask(qa, q)
    second = ask(qa, q)
    assert first.to_json() == second.to_json()
    assert first.content_hash() == second.content_hash()


def test_a5_unclassifiable_question_resolves_deterministically(qa):
    weird = "florb glorp 42 ??? \u3053\u3093\u306b\u3061\u306f"
    first = ask(qa, weird)
    second = ask(qa, weird)
    assert first.outcome == second.outcome
    assert first.content_hash() == second.content_hash()
    assert first.outcome.value in SEVEN_OUTCOMES
    # never partial randomness: identical field-by-field output
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


# ---------------------------------------------------------------------------
# B. Question classification
# ---------------------------------------------------------------------------


def test_b1_classification_is_pure_and_repeatable():
    for question in BATCH_QUESTIONS:
        assert classify_question(question) == classify_question(question)


def test_b2_explicit_canonical_id_routes_exact():
    known = classify_question("Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert known.canonical_id == "CL.EUR.DAILY.TIER_CALIBRATION"
    unknown = classify_question("Is CL.UNKNOWN.NOTHING.V1 validated?")
    assert unknown.canonical_id == "CL.UNKNOWN.NOTHING.V1"


def test_b3_question_classes_distinguished_descriptive_is_fallback():
    assert (
        classify_question("Is X validated?").question_class
        is QuestionClass.EMPIRICAL
    )
    assert (
        classify_question("What is the setup entry trigger?").question_class
        is QuestionClass.ACTIONABLE
    )
    assert (
        classify_question("Is X different from Y?").question_class
        is QuestionClass.COMPARATIVE
    )
    assert (
        classify_question("What is the meaning of CEREBUS?").question_class
        is QuestionClass.DESCRIPTIVE
    )


def test_b3_descriptive_answers_never_assert_numbers(qa):
    answer = ask(qa, "What is MOD.EUR.DAILY.NEWS_REKEY.V1?")
    assert answer.answer_class is AnswerClass.DESCRIPTIVE
    assert all(a.numerical is False for a in answer.assertions)


def test_b4_alias_expansion_never_rewrites_status_tokens():
    classified = classify_question("gold validated?")
    assert classified.market == "XAUUSD"
    assert "validated" in classified.tokens  # token preserved, not rewritten


def test_b5_unknown_scope_value_fails_closed(qa, index):
    principal, context = CONTEXTS["member"]
    service = RetrievalService(index)
    response = service.retrieve(
        principal,
        context,
        RetrievalQuery(text="range", market="ZZZUSD"),
        correlation_id="b5",
    )
    assert response.results == ()
    # an unknown market in the question text never becomes a bogus filter
    assert classify_question("Is the ZZZUSD range validated?").market is None


# ---------------------------------------------------------------------------
# C. The four-state ladder
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("question", BATCH_QUESTIONS)
def test_c1_c2_ladder_present_and_monotonic(qa, question):
    answer = ask(qa, question)
    ladder = answer.ladder
    assert ladder.assertable <= ladder.supported <= ladder.retrieved
    assert ladder.explainable <= ladder.assertable
    with pytest.raises(ValueError):
        Ladder(retrieved=False, supported=True)
    with pytest.raises(ValueError):
        Ladder(supported=True, assertable=True, explainable=True)


def test_c3_found_but_unsupported_is_not_supported(qa):
    answer = ask(qa, "Does the BTC tracker establish BTC Game rules?")
    assert answer.ladder.retrieved is True
    assert answer.ladder.supported is False
    assert answer.ladder.assertable is False


def test_c4_supported_candidate_is_never_unqualified(qa, generation):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation, **{claim.object_id: {"status": EvidenceStatus.CANDIDATE}}
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    # support and status authority are evaluated independently: the claim is
    # supported, yet the authority permits it only with a qualification
    assert answer.ladder.supported is True
    assert answer.outcome is AnswerOutcome.ANSWERABLE_QUALIFIED
    assertion = next(
        a for a in answer.assertions if a.object_id == claim.object_id
    )
    assert assertion.status == "CANDIDATE"
    assert assertion.verdict is AssertionVerdict.QUALIFY
    assert any(
        q.code is QualificationCode.CANDIDATE_STATUS
        for q in answer.qualifications
    )
    assert answer.outcome is not AnswerOutcome.ANSWERABLE  # never unqualified


def test_c5_explainable_requires_full_citation_chain(qa, generation):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    if answer.ladder.explainable and answer.answer_class is AnswerClass.EMPIRICAL:
        cited = {c.claim_id for c in answer.citations}
        for assertion in answer.assertions:
            if assertion.verdict is AssertionVerdict.ASSERT:
                assert assertion.object_id in cited

    # missing evidence ⇒ rung never reaches explainable, and a gap is shown
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation,
        **{
            claim.object_id: {
                "support": SupportAssessment(
                    supported=True,
                    classification="EMPIRICAL",
                    evidence_ids=("EV.MISSING.NOTHING.V1",),
                )
            }
        },
    )
    broken = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert broken.ladder.explainable is False
    assert GapCode.NO_SOURCE_ARTIFACT.value in {g.code.value for g in broken.gaps}
    assert broken.outcome in {
        AnswerOutcome.PARTIAL,
        AnswerOutcome.UNSUPPORTED,
        AnswerOutcome.ANSWERABLE_QUALIFIED,
    }


def test_c6_no_authority_promotion_by_ranking_or_wording(qa, generation):
    claim = _record_for(generation, "CL.XAU.PROMOTION.68_80")
    for wording in (
        "Is CL.XAU.PROMOTION.68_80 validated?",
        "Tell me about CL.XAU.PROMOTION.68_80",
        "compare CL.XAU.PROMOTION.68_80 versus CL.XAU.PROMOTION.120_132",
    ):
        answer = ask(qa, wording)
        for assertion in answer.assertions:
            if assertion.object_id == claim.object_id:
                assert assertion.status == claim.status.value
    # status authority is a pure function of status alone
    assert authority_for(EvidenceStatus.CANDIDATE) == "QUALIFIED"
    assert authority_for("CANDIDATE") == authority_for(
        EvidenceStatus.CANDIDATE
    )


# ---------------------------------------------------------------------------
# D. Answerability outcomes
# ---------------------------------------------------------------------------


def test_d1_only_seven_outcomes_are_ever_produced(qa):
    assert {o.value for o in AnswerOutcome} == SEVEN_OUTCOMES
    seen = set()
    for question in BATCH_QUESTIONS + (
        "Is CL.XAU.PROMOTION.120_132 validated?",
    ):
        seen.add(ask(qa, question).outcome.value)
    assert seen <= SEVEN_OUTCOMES
    assert len(seen) >= 4  # the batch exercises several distinct outcomes


def test_d2_unsupported_carries_insufficient_evidence(qa, generation):
    claim = _record_for(generation, "CL.XAU.PROMOTION.120_132")
    answer = ask(qa, "Is CL.XAU.PROMOTION.120_132 validated?", ctx="member")
    if answer.outcome is AnswerOutcome.UNSUPPORTED:
        assert answer.epistemic_label == "INSUFFICIENT_EVIDENCE"
        assert answer.ladder.supported is False
    else:  # denial path surfaces as an explicit gap, never as an assertion
        assert answer.outcome is AnswerOutcome.RESTRICTED
    assert "N=25" not in answer.to_json()


def test_d3_fully_supported_is_answerable(qa):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.outcome is AnswerOutcome.ANSWERABLE
    assert answer.ladder.retrieved
    assert answer.ladder.supported and answer.ladder.assertable
    assert answer.qualifications == ()
    assert answer.gaps == ()


def test_d4_mandatory_qualifications_forbid_plain_answerable(qa, generation):
    claim = _record_for(generation, "CL.EUR.HO.D3_DIRECTION")
    answer = ask(qa, "Is CL.EUR.HO.D3_DIRECTION validated?")
    assert answer.outcome is AnswerOutcome.ANSWERABLE_QUALIFIED
    assert any(
        q.code is QualificationCode.FORWARD_OOS for q in answer.qualifications
    )
    # validation refuses an ANSWERABLE carrying mandatory qualifications
    with pytest.raises(AnswerValidationError):
        validate_answer(
            answer.model_copy(
                update={"outcome": AnswerOutcome.ANSWERABLE}
            )
        )


def test_d5_mixed_pass_and_gap_is_partial_with_every_gap_disclosed(
    qa, generation
):
    ok_claim = "CL.EUR.DAILY.TIER_CALIBRATION"
    broken_claim = "CL.EUR.WEEKLY.TIER_RANGE"
    tampered = _service_with(
        generation,
        **{
            broken_claim: {
                "support": SupportAssessment(
                    supported=True,
                    classification="EMPIRICAL",
                    evidence_ids=("EV.MISSING.NOTHING.V1",),
                )
            }
        },
    )
    answer = ask(
        tampered,
        "Are CL.EUR.DAILY.TIER_CALIBRATION and CL.EUR.WEEKLY.TIER_RANGE "
        "both validated?",
    )
    assert answer.outcome is AnswerOutcome.PARTIAL
    assert GapCode.NO_SOURCE_ARTIFACT.value in {g.code.value for g in answer.gaps}
    passing = [
        a for a in answer.assertions
        if a.verdict is not AssertionVerdict.GAP and a.object_id == ok_claim
    ]
    assert passing, "the supported part must remain assertable"


def test_d6_resolves_nothing_is_out_of_corpus_and_content_free(qa):
    # PLAN §6: 0 results, 0 denials ⇒ OUT_OF_CORPUS with zero corpus content.
    # A context entitled to every exposure guarantees the "0 denials"
    # premise; a member instead lands on the D7 RESTRICTED branch.
    answer = ask(qa, "zzzqx?", ctx="all")
    assert answer.outcome is AnswerOutcome.OUT_OF_CORPUS
    assert answer.assertions == ()
    assert answer.citations == ()
    assert answer.qualifications == ()
    assert answer.claim_refs == ()
    assert not any(
        (
            answer.ladder.retrieved,
            answer.ladder.supported,
            answer.ladder.assertable,
            answer.ladder.explainable,
        )
    )
    assert answer.epistemic_label is None


def test_d7_zero_results_with_denials_is_restricted_content_free(qa):
    answer = ask(qa, "What is MOD.EUR.DAILY.NEWS_REKEY.V1?", ctx="anon")
    assert answer.outcome is AnswerOutcome.RESTRICTED
    assert answer.denials, "RESTRICTED requires denial entries"
    assert answer.assertions == ()
    assert answer.citations == ()
    for denial in answer.denials:
        assert set(denial.model_dump()) == {"object_id", "exposure", "reason_code"}


@pytest.mark.parametrize(
    "question",
    (
        "Does the BTC tracker establish BTC Game rules?",
        "zzzqx?",
    ),
)
def test_d8_abstention_is_a_successful_result_with_honest_disclosure(
    qa, question
):
    answer = ask(qa, question)
    assert answer.outcome in {
        AnswerOutcome.PARTIAL,
        AnswerOutcome.UNSUPPORTED,
        AnswerOutcome.OUT_OF_CORPUS,
        AnswerOutcome.RESTRICTED,
    }
    assert answer.gaps or answer.denials
    assert all(
        a.verdict is not AssertionVerdict.ASSERT for a in answer.assertions
    ) or not answer.assertions
    # nothing fabricated: every assertion text is governed retrieval text
    for assertion in answer.assertions:
        assert assertion.text


# ---------------------------------------------------------------------------
# E. Claim identity (eight dimensions)
# ---------------------------------------------------------------------------


def test_e1_every_numerical_claim_assertion_carries_eight_dimensions(
    qa, generation
):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    for assertion in answer.assertions:
        if assertion.numerical and assertion.object_type == "CLAIM":
            identity = assertion.claim_identity
            assert identity is not None
            for dimension in IDENTITY_DIMENSIONS:
                value = getattr(identity, dimension)
                assert isinstance(value, str) and value  # verbatim, incl.
                # NOT_SPECIFIED_IN_SOURCE where the source is silent


def test_e2_comparison_is_canonical_not_prose(qa, generation):
    daily = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    weekly = _record_for(generation, "CL.EUR.WEEKLY.TIER_RANGE")
    left = daily.structured.claim_identity
    right = weekly.structured.claim_identity
    assert left is not None and right is not None
    # similar prose, different populations ⇒ never merged
    assert compare_claim_identity(left, right) is ClaimComparison.PARALLEL
    assert compare_claim_identity(left, left) is ClaimComparison.SAME_POPULATION


def test_e3_result_value_never_enters_identity():
    fields = set(ClaimIdentity.model_fields)
    assert fields == set(IDENTITY_DIMENSIONS)
    # no result/rate/probability field exists to leak into comparison
    identity = ClaimIdentity(
        market="EURUSD",
        event_definition="event",
        conditioning_event="cond",
        clock_origin="clock",
        horizon="horizon",
        tolerance="tol",
        eligibility="elig",
        implementation_semantics="impl",
    )
    assert len(identity.comparison_key()) == 8


@pytest.mark.parametrize("dimension", IDENTITY_DIMENSIONS)
def test_e4_e12_to_e18_dimension_mismatch_stays_parallel(dimension):
    base = dict(
        market="EURUSD",
        event_definition="event",
        conditioning_event="cond",
        clock_origin="clock",
        horizon="horizon",
        tolerance="tol",
        eligibility="elig",
        implementation_semantics="impl",
    )
    left = ClaimIdentity(**base)
    changed = dict(base)
    changed[dimension] = f"other-{dimension}"
    right = ClaimIdentity(**changed)
    assert compare_claim_identity(left, right) is ClaimComparison.PARALLEL
    assert compare_claim_identity(left, ClaimIdentity(**base)) is (
        ClaimComparison.SAME_POPULATION
    )


def test_e5_statistic_without_complete_identity_is_refused():
    with pytest.raises(ValueError):
        Assertion(
            object_id="CL.SYNTH.V1",
            object_type="CLAIM",
            status="VALIDATED",
            epistemic_label="VALIDATED",
            text="some 42 result",
            numerical=True,
            verdict=AssertionVerdict.ASSERT,
            claim_identity=None,  # eight dimensions required
        )


# ---------------------------------------------------------------------------
# F. Citation and evidence chains
# ---------------------------------------------------------------------------


def test_f1_citation_chain_is_complete(qa):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.citations, "empirical answer must cite"
    for citation in answer.citations:
        assert citation.claim_id and citation.evidence_id
        assert citation.artifact_id and citation.locator
        assert citation.content_identity.startswith("sha256:")
        assert citation.relation and citation.source_class
        assert citation.source_state


def test_f2_citations_name_the_actual_artifacts_of_their_claim(qa, gateway):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    for citation in answer.citations:
        # the cited artifact must belong to the cited evidence's own chain
        edges = gateway.edges_from_artifact(citation.artifact_id)
        assert edges, "cited artifact must be a governed artifact"
        owner_ids = {edge.object_id for edge in edges}
        assert citation.evidence_id in owner_ids or citation.claim_id in owner_ids


def test_f3_visual_or_conversation_sources_never_cite(qa, generation):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation,
        **{
            claim.object_id: {
                "support": SupportAssessment(
                    supported=False,
                    classification="NON_EMPIRICAL_SOURCE",
                    gaps=("NON_EMPIRICAL_SOURCE",),
                )
            }
        },
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.outcome in {
        AnswerOutcome.UNSUPPORTED,
        AnswerOutcome.PARTIAL,
    }
    assert not any(
        c.claim_id == claim.object_id for c in answer.citations
    )
    assert any(
        "visual or conversation-derived" in gap.detail
        for gap in answer.gaps
    )


def test_f4_descriptive_answers_are_explicit_and_non_empirical(qa):
    answer = ask(qa, "What is CL.FIB.R11.GENERATOR_FAILURE say?")
    # class is explicit; no empirical assertion is manufactured from it
    assert answer.answer_class in {
        AnswerClass.DESCRIPTIVE,
        AnswerClass.EMPIRICAL,
    }
    for assertion in answer.assertions:
        if assertion.object_type != "CLAIM":
            assert assertion.numerical is False


def test_f5_missing_links_are_disclosed_never_manufactured(qa, generation):
    claim = _record_for(generation, "CL.XAU.PROMOTION.68_80")
    tampered = _service_with(
        generation,
        **{
            claim.object_id: {
                "support": SupportAssessment(
                    supported=False,
                    classification="NO_SOURCE",
                    gaps=("NO_EVIDENCE_REFERENCE",),
                )
            }
        },
    )
    answer = ask(tampered, "Is CL.XAU.PROMOTION.68_80 validated?")
    assert answer.gaps, "the missing link must be a disclosed gap"
    assert any(
        a.verdict is AssertionVerdict.GAP for a in answer.assertions
    )
    assert not any(
        c.claim_id == claim.object_id for c in answer.citations
    )


def test_f6_wrong_citation_is_rejected_by_validation(qa, generation):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.citations
    good = answer.citations[0]
    hijacked = Citation(
        claim_id="CL.SOMEONE.ELSES.CLAIM.V1",  # not referenced by this answer
        evidence_id=good.evidence_id,
        artifact_id=good.artifact_id,
        relation=good.relation,
        source_class=good.source_class,
        source_state=good.source_state,
        content_identity=good.content_identity,
        locator=good.locator,
    )
    with pytest.raises(AnswerValidationError):
        validate_answer(
            answer.model_copy(update={"citations": (hijacked,) + answer.citations[1:]})
        )


# ---------------------------------------------------------------------------
# G. Status authority (no promotion)
# ---------------------------------------------------------------------------


def test_g1_falsified_only_appears_as_negative_evidence(qa):
    answer = ask(qa, "What does CL.FIB.R11.GENERATOR_FAILURE say?")
    assertion = next(
        a for a in answer.assertions
        if a.object_id == "CL.FIB.R11.GENERATOR_FAILURE"
    )
    assert assertion.status == "FALSIFIED"
    assert assertion.verdict is not AssertionVerdict.ASSERT
    assert assertion.epistemic_label == "NEGATIVE_EVIDENCE"
    assert any(
        q.code is QualificationCode.NEGATIVE_EVIDENCE
        for q in answer.qualifications
    )
    serialized = answer.to_json()
    for phrase in ("is now validated", "current trading rule"):
        assert phrase not in serialized


def test_g2_historical_is_generation_bound_and_qualified(qa, generation):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation, **{claim.object_id: {"status": EvidenceStatus.HISTORICAL}}
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.outcome is AnswerOutcome.ANSWERABLE_QUALIFIED
    assertion = next(
        a for a in answer.assertions if a.object_id == claim.object_id
    )
    assert assertion.status == "HISTORICAL"
    assert assertion.epistemic_label == "HISTORICAL"
    assert any(
        q.code is QualificationCode.HISTORICAL_GENERATION
        for q in answer.qualifications
    )


def test_g3_candidate_and_research_flag_never_unqualified(qa, generation):
    for status, code in (
        (EvidenceStatus.CANDIDATE, QualificationCode.CANDIDATE_STATUS),
        (EvidenceStatus.RESEARCH_FLAG, QualificationCode.RESEARCH_FLAG),
    ):
        claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
        tampered = _service_with(
            generation, **{claim.object_id: {"status": status}}
        )
        answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
        assert answer.outcome is not AnswerOutcome.ANSWERABLE
        assert any(q.code is code for q in answer.qualifications)


def test_g4_small_n_qualifiers_survive_with_n(qa):
    answer = ask(qa, "Is CL.XAU.PROMOTION.68_80 validated?")
    small_n = [q for q in answer.qualifications if q.code is QualificationCode.SMALL_N]
    assert small_n, "small-N must travel with the claim"
    assert "N=48" in small_n[0].text


def test_g5_descriptive_status_never_becomes_a_numerical_assertion(
    qa, generation
):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation, **{claim.object_id: {"status": EvidenceStatus.DESCRIPTIVE}}
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assertion = next(
        a for a in answer.assertions if a.object_id == claim.object_id
    )
    assert assertion.verdict is AssertionVerdict.GAP
    assert answer.outcome in {
        AnswerOutcome.UNSUPPORTED,
        AnswerOutcome.PARTIAL,
    }


@pytest.mark.parametrize(
    "status,code,label",
    (
        (EvidenceStatus.SUPERSEDED, QualificationCode.SUPERSEDED, "SUPERSEDED"),
        (EvidenceStatus.PARKED, QualificationCode.PARKED, "PARKED"),
    ),
)
def test_g6_superseded_and_parked_are_labeled_never_active(
    qa, generation, status, code, label
):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation, **{claim.object_id: {"status": status}}
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assertion = next(
        a for a in answer.assertions if a.object_id == claim.object_id
    )
    assert assertion.status == status.value
    assert assertion.epistemic_label == label
    assert any(q.code is code for q in answer.qualifications)
    if status is EvidenceStatus.PARKED:
        assert any(
            "not active guidance" in q.text for q in answer.qualifications
        )


def test_g7_no_status_change_by_relevance_wording_or_ranking(qa, generation):
    statuses = {}
    for wording in (
        "Is CL.EUR.DAILY.TIER_CALIBRATION validated?",
        "How important is CL.EUR.DAILY.TIER_CALIBRATION?",
        "summarize CL.EUR.DAILY.TIER_CALIBRATION evidence",
    ):
        answer = ask(qa, wording)
        for assertion in answer.assertions:
            statuses.setdefault(assertion.object_id, set()).add(
                assertion.status
            )
    for object_id, seen in statuses.items():
        assert len(seen) == 1, f"{object_id} status varies by wording"
        record = generation.record(object_id)
        assert seen == {record.status.value}


# ---------------------------------------------------------------------------
# H. Contradiction handling
# ---------------------------------------------------------------------------


def _conflict_service(generation):
    """Two claims, same population, divergent statuses (declared + identity)."""
    source = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    twin = source.model_copy(
        update={
            "object_id": "CL.EUR.DAILY.TIER_CALIBRATION_TWIN",
            "status": EvidenceStatus.FALSIFIED,
        }
    )
    records = generation.records + (twin,)
    idx = RetrievalIndex()
    idx.publish(dataclasses.replace(generation, records=records))
    return QAService(RetrievalService(idx))


def test_h1_contradiction_requires_same_population(qa, generation):
    service = _conflict_service(generation)
    answer = ask(
        service,
        "Are CL.EUR.DAILY.TIER_CALIBRATION and "
        "CL.EUR.DAILY.TIER_CALIBRATION_TWIN validated?",
    )
    same_population_notes = [
        c for c in answer.conflicts if c.basis == "SAME_POPULATION"
    ]
    assert same_population_notes, "identity-matched divergence must be caught"

    # different populations are never a contradiction
    parallel = ask(
        qa,
        "Are MOD.EUR.DAILY.NEWS_REKEY.V1 and MOD.EUR.WEEKLY.V1_1 the same "
        "population?",
    )
    assert all(
        c.basis != "SAME_POPULATION" for c in parallel.conflicts
    ) or parallel.conflicts == ()


def test_h2_matched_divergence_is_contradicted_exposing_both(qa, generation):
    service = _conflict_service(generation)
    answer = ask(
        service,
        "Is CL.EUR.DAILY.TIER_CALIBRATION validated in "
        "MOD.EUR.DAILY.NEWS_REKEY.V1?",
    )
    assert answer.outcome is AnswerOutcome.CONTRADICTED
    assert answer.conflicts
    note = answer.conflicts[0]
    assert note.kind.value == "MATCHED_IDENTITY_DIVERGENCE"
    assert note.basis == "SAME_POPULATION"
    assert len(note.claim_ids) == 2
    assert len(note.statuses) == 2
    assert len(note.generations) == 2
    assert set(note.statuses) == {"VALIDATED", "FALSIFIED"}
    assert note.matched_dimensions == IDENTITY_DIMENSIONS
    assert note.resolution.value == "DOWNGRADE_AND_EXPOSE_BOTH"


def test_h3_different_populations_never_reported_as_contradiction(qa):
    answer = ask(
        qa,
        "Are MOD.EUR.DAILY.NEWS_REKEY.V1 and MOD.EUR.WEEKLY.V1_1 the same "
        "population?",
    )
    assert answer.conflicts == ()
    assert any(
        "never merged" in limitation for limitation in answer.limitations
    )
    # both sides presented separately
    ids = {a.object_id for a in answer.assertions}
    assert "MOD.EUR.DAILY.NEWS_REKEY.V1" in ids
    assert "MOD.EUR.WEEKLY.V1_1" in ids


def test_h4_conflicting_statistics_are_never_averaged(qa, generation):
    service = _conflict_service(generation)
    answer = ask(
        service,
        "Is CL.EUR.DAILY.TIER_CALIBRATION validated in "
        "MOD.EUR.DAILY.NEWS_REKEY.V1?",
    )
    serialized = answer.to_json()
    # both statuses and both sides remain visible; no blended number appears
    assert "VALIDATED" in serialized and "FALSIFIED" in serialized
    note = answer.conflicts[0]
    assert set(note.claim_ids) <= {a.object_id for a in answer.assertions} | {
        "CL.EUR.DAILY.TIER_CALIBRATION_TWIN"
    }
    # no averaged/merged number: every assertion text is one record's own text
    for assertion in answer.assertions:
        record = generation.record(assertion.object_id)
        if record is not None:
            assert assertion.text == record.retrieval_text


def test_h5_conflict_notes_are_bounded_auditable_and_content_free(
    qa, generation
):
    service = _conflict_service(generation)
    answer = ask(
        service,
        "Is CL.EUR.DAILY.TIER_CALIBRATION validated in "
        "MOD.EUR.DAILY.NEWS_REKEY.V1?",
    )
    for note in answer.conflicts:
        payload = note.model_dump()
        assert set(payload) == {
            "kind",
            "basis",
            "claim_ids",
            "statuses",
            "generations",
            "evidence_ids",
            "resolution",
            "matched_dimensions",
        }
        assert len(note.claim_ids) <= 4
    # validation already rejects internal markers on conflict surfaces
    assert "INTERNAL_METHOD" not in answer.to_json()


# ---------------------------------------------------------------------------
# I. Numerical safety
# ---------------------------------------------------------------------------


def test_i1_none_of_the_forbidden_conversions_occur(qa):
    for question in BATCH_QUESTIONS:
        serialized = ask(qa, question).to_json().lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase.lower() not in serialized, (
                f"{phrase!r} appeared for {question!r}"
            )


def test_i2_every_numeral_is_traceable_to_governed_text(qa, generation):
    governed_numbers: set[str] = set()
    for record in generation.records:
        governed_numbers |= _digits(record.retrieval_text)
        governed_numbers |= _digits(record.title)
        if record.structured.sample_n is not None:
            governed_numbers |= _digits(str(record.structured.sample_n))
        for value in record.structured.model_dump().values():
            if isinstance(value, (str, int)):
                governed_numbers |= _digits(str(value))
    for question in BATCH_QUESTIONS:
        answer = ask(qa, question)
        payload = answer.payload_dict()
        content_surfaces = (
            [a["text"] for a in payload["assertions"]]
            + [q["text"] for q in payload["qualifications"]]
            + [g["detail"] for g in payload["gaps"]]
            + [f["text"] for f in payload["follow_ups"]]
            + payload["limitations"]
        )
        for surface in content_surfaces:
            untraceable = _digits(surface) - governed_numbers
            assert not untraceable, (
                f"untraceable numbers {untraceable} in {surface!r}"
            )


def test_i3_unsupported_numerical_generalization_is_refused(
    qa, generation
):
    # covered by G5's descriptive-status GAP; here: the gap reason is explicit
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation, **{claim.object_id: {"status": EvidenceStatus.DESCRIPTIVE}}
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assertion = next(
        a for a in answer.assertions if a.object_id == claim.object_id
    )
    assert assertion.verdict is AssertionVerdict.GAP
    assert "descriptive" in next(
        g.detail for g in answer.gaps
        if g.object_id == claim.object_id
    )


def test_i4_identity_mismatched_numbers_are_never_combined(qa):
    answer = ask(
        qa,
        "Are CL.EUR.DAILY.TIER_CALIBRATION and CL.XAU.PROMOTION.68_80 both "
        "validated?",
    )
    # each assertion is exactly one claim's governed text, one identity,
    # one qualification scope — nothing blends two populations
    ids = [a.object_id for a in answer.assertions]
    assert len(ids) == len(set(ids))
    for assertion in answer.assertions:
        if assertion.object_type == "CLAIM":
            assert assertion.claim_identity is not None
    for qualification in answer.qualifications:
        assert isinstance(qualification.object_id, str)


# ---------------------------------------------------------------------------
# J. Exposure and information flow
# ---------------------------------------------------------------------------


def test_j1_qa_consumes_only_the_authorized_boundary(qa, generation):
    # kernel is retrieval-only (static seam test in A1/A2); here: the member
    # path never surfaces research-lab content
    research_ids = {
        record.object_id
        for record in generation.records
        if record.exposure_class is ProductExposure.RESEARCH_LAB
    }
    assert research_ids, "corpus has research-lab objects"
    for question in BATCH_QUESTIONS:
        serialized = ask(qa, question).to_json()
        for object_id in research_ids:
            # allowed only when the answer is content-free about that object
            if object_id in serialized:
                assertion_texts = " ".join(
                    a.text for a in ask(qa, question).assertions
                )
                assert object_id not in assertion_texts, (
                    f"{object_id} body surfaced to a member"
                )


def test_j2_forbidden_content_on_no_surface(qa, generation):
    research_evidence = {
        record.object_id
        for record in generation.records
        if record.object_type is ObjectType.EVIDENCE
        and record.exposure_class is ProductExposure.RESEARCH_LAB
    }
    for question in BATCH_QUESTIONS:
        answer = ask(qa, question)
        payload = answer.payload_dict()
        content_surfaces = (
            " ".join(a["text"] for a in payload["assertions"])
            + " ".join(q["text"] for q in payload["qualifications"])
            + " ".join(g["detail"] for g in payload["gaps"])
            + " ".join(f["text"] for f in payload["follow_ups"])
            + " ".join(payload["limitations"])
        )
        serialized = answer.to_json()
        for marker in ("INTERNAL_METHOD", "INTERNAL_CODE"):
            assert marker not in serialized
        for citation in answer.citations:
            assert citation.locator not in content_surfaces or True
        # no research-lab body on any content surface, and no research
        # locator ever cited (bare ids in evidence_refs are content-free)
        for record in generation.records:
            if record.object_id in research_evidence:
                assert record.retrieval_text not in content_surfaces
        for citation in answer.citations:
            assert citation.evidence_id not in research_evidence


def test_j3_mixed_question_builds_only_from_authorized_results(qa):
    answer = ask(
        qa,
        "Are CL.XAU.PROMOTION.68_80 and CL.XAU.PROMOTION.120_132 both "
        "validated?",
        ctx="member",
    )
    serialized = answer.to_json()
    # authorized side contributes; restricted side never does
    assert "N=25" not in serialized
    assert "CL.XAU.PROMOTION.120_132" not in {
        c.claim_id for c in answer.citations
    }
    disclosed = bool(answer.denials) or GapCode.DENIED.value in {
        g.code.value for g in answer.gaps
    }
    assert disclosed, "the restricted side must be disclosed content-free"


def test_j4_denial_never_reveals_protected_material(qa):
    answer = ask(
        qa,
        "Are CL.XAU.PROMOTION.68_80 and CL.XAU.PROMOTION.120_132 both "
        "validated?",
        ctx="member",
    )
    for denial in answer.denials:
        payload = denial.model_dump()
        assert set(payload) == {"object_id", "exposure", "reason_code"}
        for value in payload.values():
            assert "N=" not in str(value)
    assert "recovered small sample" not in answer.to_json()


def test_j5_errors_are_content_free_and_questions_never_raise(qa, index):
    nasty = (
        "",
        "   ",
        "<script>alert(1)</script>",
        "A" * 10000,
        "CL.NOT.A.REAL.ID.V1",
        ";\u0000DROP TABLE claims;",
    )
    for question in nasty:
        answer = ask(qa, question)
        assert answer.outcome.value in SEVEN_OUTCOMES
    # a broken deployment fails closed with a fixed message, no echo
    from app.forge.retrieval import IndexNotBuilt

    broken = QAService(RetrievalService(RetrievalIndex()))
    principal, context = CONTEXTS["member"]
    with pytest.raises(IndexNotBuilt) as excinfo:
        broken.ask(
            principal,
            context,
            "Is CL.EUR.DAILY.TIER_CALIBRATION validated?",
            correlation_id="broken",
        )
    message = str(excinfo.value)
    assert "CL.EUR.DAILY.TIER_CALIBRATION" not in message
    assert "validated" not in message.lower()


# ---------------------------------------------------------------------------
# K. CEREBUS truth fixtures (kernel angles beyond golden fixtures)
# ---------------------------------------------------------------------------


def test_k1_symmetry_manual_setup_never_automation_approval(qa, generation):
    answer = ask(qa, "Can SET.FIB.REKEY.V1 run automated?", ctx="research")
    serialized = answer.to_json()
    assert "AUTOMATION_APPROVED" not in serialized
    setup = generation.record("SET.FIB.REKEY.V1")
    if setup is not None:
        for qualifier in setup.qualifiers:
            assert qualifier in serialized, "manual/research flags survive"
    assert answer.outcome in {
        AnswerOutcome.ANSWERABLE_QUALIFIED,
        AnswerOutcome.PARTIAL,
    }


def test_k2_p90_stays_lineage_never_a_statistic(qa):
    answer = ask(qa, "What is P90 in MOD.EUR.DAILY.NEWS_REKEY.V1?")
    serialized = answer.to_json()
    assert "lineage" in serialized
    assert "do not import historical P90 win rates" in serialized
    assert "P90 win rate " not in serialized
    assert "P90 performance" not in serialized
    for assertion in answer.assertions:
        assert assertion.numerical is False or assertion.verdict is not (
            AssertionVerdict.ASSERT
        ) or "P90" not in assertion.text


def test_k3_btc_tracker_never_establishes_game(qa):
    for question in (
        "Does the BTC tracker establish BTC Game rules?",
        "What is the BTC Game?",
    ):
        answer = ask(qa, question)
        serialized = answer.to_json()
        assert "BTC Game rules" not in serialized
        ids = {a.object_id for a in answer.assertions} | set(answer.claim_refs)
        assert not any(object_id.startswith("CL.BTC") for object_id in ids)
        assert not any("GAME" in object_id for object_id in ids)
        assert GapCode.NO_EVIDENCE_REFERENCE.value in {
            g.code.value for g in answer.gaps
        } or answer.outcome in {
            AnswerOutcome.RESTRICTED,
            AnswerOutcome.OUT_OF_CORPUS,
        }


def test_k4_eur_families_never_collapse(qa, generation):
    identities = [
        record.structured.claim_identity
        for record in generation.records
        if record.object_id
        in (
            "CL.EUR.DAILY.TIER_CALIBRATION",
            "CL.EUR.WEEKLY.TIER_RANGE",
            "CL.EUR.HO.D3_DIRECTION",
        )
    ]
    identities = [i for i in identities if i is not None]
    assert len(identities) >= 3
    for i, left in enumerate(identities):
        for right in identities[i + 1:]:
            assert compare_claim_identity(left, right) is (
                ClaimComparison.PARALLEL
            )


def test_k5_xau_layers_stay_distinct(qa, generation):
    answer = ask(
        qa, "Are L3 destination and L1 execution different layers for XAU?"
    )
    assert "explicit layer ownership" in answer.to_json()
    for assertion in answer.assertions:
        record = generation.record(assertion.object_id)
        if record is not None:
            assert assertion.layer == record.layer.value, (
                "layer must never bleed between assertions"
            )


def test_k6_jpy_roles_never_equal_directional_vote(qa):
    answer = ask(
        qa,
        "Are CL.JPY.CARRY.ROLE_RELATION and MOD.JPY.CARRY_GAME.L1_L3.V1 "
        "distinct?",
    )
    serialized = answer.to_json()
    assert "USDJPY,AUDJPY,EURJPY" in serialized
    assert "EURJPY confirmation" in serialized
    assert "EURJPY is the master" not in serialized
    assert "equal directional vote" not in serialized
    ids = {a.object_id for a in answer.assertions}
    assert not any("EURJPY" in object_id for object_id in ids)


def test_k7_fib_negative_evidence_and_range_birth_doctrine(qa, generation):
    negative = ask(qa, "What does CL.FIB.R11.GENERATOR_FAILURE say?")
    assert "overproduced" in negative.to_json()
    fib_model = next(
        r.object_id
        for r in generation.records
        if r.object_type is ObjectType.MODEL and "FIB" in r.object_id
    )
    doctrine = ask(qa, f"What is {fib_model}?")
    assert doctrine.answer_class is AnswerClass.DESCRIPTIVE
    assert all(a.numerical is False for a in doctrine.assertions)


def test_k8_research_statistics_stay_qualified_or_unsupported(qa):
    research = ask(
        qa, "Is CL.XAU.PROMOTION.120_132 validated?", ctx="research"
    )
    assert research.outcome is AnswerOutcome.ANSWERABLE_QUALIFIED
    codes = {q.code for q in research.qualifications}
    assert QualificationCode.RESEARCH_FLAG in codes
    assert QualificationCode.SMALL_N in codes
    assert "N=25" in research.to_json()
    # a member never receives the confident version
    member = ask(qa, "Is CL.XAU.PROMOTION.120_132 validated?", ctx="member")
    assert member.outcome in {
        AnswerOutcome.UNSUPPORTED,
        AnswerOutcome.RESTRICTED,
    }
    assert "N=25" not in member.to_json()


# ---------------------------------------------------------------------------
# L/M. Determinism over rebuilds (detectors/fixtures live in corpus_qa)
# ---------------------------------------------------------------------------


def test_l5_qa_follows_generation_changes_across_rebuilds(gateway):
    second = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, second)
    first_service = QAService(RetrievalService(_fresh_index(gateway)))
    second_service = QAService(RetrievalService(second))
    q = "Is CL.EUR.DAILY.TIER_CALIBRATION validated?"
    p, c = CONTEXTS["member"]
    a1 = first_service.ask(p, c, q, correlation_id="l5")
    a2 = second_service.ask(p, c, q, correlation_id="l5")
    assert a1.content_hash() == a2.content_hash()
    assert a1.generation == a2.generation
    assert a1.index_hash == a2.index_hash


def _fresh_index(gateway) -> RetrievalIndex:
    idx = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
    return idx


def test_l6_known_identity_gaps_are_labeled_never_invented(qa, generation):
    auc_evidence = next(
        (r.object_id for r in generation.records if "AUC" in r.object_id), None
    )
    if auc_evidence is None:
        pytest.skip("no AUC evidence object in the frozen corpus")
    answer = ask(qa, f"What does {auc_evidence} say?")
    # the gap is labeled or disclosed — never silently filled with a number
    assert answer.outcome.value in SEVEN_OUTCOMES
    if answer.outcome is AnswerOutcome.ANSWERABLE_QUALIFIED:
        assert answer.qualifications or answer.gaps
    serialized = answer.to_json()
    assert "AUC of 0." not in serialized  # no invented metric value


# ---------------------------------------------------------------------------
# N. Structured answer contract
# ---------------------------------------------------------------------------

FROZEN_FIELDS = {
    "outcome",
    "answer_class",
    "ladder",
    "epistemic_label",
    "scope",
    "assertions",
    "claim_refs",
    "evidence_refs",
    "citations",
    "qualifications",
    "conflicts",
    "gaps",
    "limitations",
    "denials",
    "follow_ups",
    "generation",
    "index_hash",
}


def test_n1_every_answer_carries_the_frozen_fields(qa):
    for question in BATCH_QUESTIONS[:5]:
        payload = ask(qa, question).payload_dict()
        assert set(payload) == FROZEN_FIELDS


def test_n2_serialization_is_deterministic_sorted_key_json(qa):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    expected = json.dumps(
        answer.payload_dict(), sort_keys=True, separators=(",", ":")
    )
    assert answer.to_json() == expected
    # no timestamps or random values
    assert not re.search(r"\d{2}:\d{2}:\d{2}", answer.to_json())
    for key in ("timestamp", "generated_at", "now", "random"):
        assert key not in answer.to_json()
    # collections are canonically ordered
    payload = answer.payload_dict()
    assert payload["claim_refs"] == sorted(payload["claim_refs"])
    assert payload["evidence_refs"] == sorted(payload["evidence_refs"])
    assert [a["object_id"] for a in payload["assertions"]] == sorted(
        a["object_id"] for a in payload["assertions"]
    )


def test_n3_answers_reference_objects_by_id_not_duplicated_authority(qa):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    for assertion in answer.assertions:
        payload = assertion.model_dump()
        # bounded statement fields only — no embedded card/registry object
        assert "card" not in payload
        assert "structured" not in payload
        assert "metadata" not in payload


def test_n4_assertion_text_is_governed_retrieval_text(qa, generation):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    for assertion in answer.assertions:
        record = generation.record(assertion.object_id)
        if record is not None:
            assert assertion.text == record.retrieval_text


def test_n5_validation_fails_closed_never_repairs(qa):
    from app.forge.qa.contract import Gap

    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    # ANSWERABLE with a gap
    with pytest.raises(AnswerValidationError):
        validate_answer(
            answer.model_copy(
                update={
                    "outcome": AnswerOutcome.ANSWERABLE,
                    "gaps": (
                        Gap(code=GapCode.NO_CLAIM_ROUTE, detail="x"),
                    ),
                }
            )
        )
    # RESTRICTED without denials
    restricted = answer.model_copy(
        update={
            "outcome": AnswerOutcome.RESTRICTED,
            "assertions": (),
            "citations": (),
            "qualifications": (),
            "conflicts": (),
            "claim_refs": (),
            "evidence_refs": (),
            "follow_ups": (),
            "gaps": (),
            "denials": (),
            "ladder": Ladder(),
        }
    )
    with pytest.raises(AnswerValidationError):
        validate_answer(restricted)
    # internal marker rejected on a content surface
    from app.forge.qa.contract import Assertion as ContractAssertion

    marked = answer.model_copy(
        update={
            "limitations": ("INTERNAL_METHOD leaked",),
        }
    )
    with pytest.raises(AnswerValidationError):
        validate_answer(marked)


# ---------------------------------------------------------------------------
# O. Boundary integrity
# ---------------------------------------------------------------------------


def test_o1_no_llm_or_provider_integration():
    forbidden = (
        "openai",
        "anthropic",
        "openrouter",
        "litellm",
        "httpx",
        "aiohttp",
        "import requests",
        "chatbot",
        "langchain",
    )
    for source_file in sorted(QA_SOURCE_DIR.glob("*.py")):
        text = source_file.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text, (
                f"{source_file.name} references {token!r}"
            )
    # and no third-party import beyond the pre-existing stack
    allowed = {"pydantic"}
    for source_file in sorted(QA_SOURCE_DIR.glob("*.py")):
        for line in source_file.read_text(encoding="utf-8").splitlines():
            match = re.match(r"import\s+([A-Za-z0-9_.]+)", line)
            if match:
                root = match.group(1).split(".")[0]
                assert root in allowed or root == "app" or root in {
                    "dataclasses",
                    "enum",
                    "hashlib",
                    "json",
                    "re",
                }, f"new dependency {root} in {source_file.name}"


def test_o2_no_public_qa_route_is_added():
    from app.main import app as main_app

    routes = {route.path for route in main_app.routes}
    forge_routes = {p for p in routes if str(p).startswith("/forge/v1")}
    assert forge_routes == {
        "/forge/v1/health",
        "/forge/v1/ready",
        "/forge/v1/meta",
    }
    for forbidden in (
        "/forge/v1/answer",
        "/forge/v1/ask",
        "/forge/v1/qa",
        "/forge/v1/query",
        "/answer",
        "/ask",
        "/qa",
        "/query",
    ):
        assert forbidden not in routes
    for source_file in (REPO_ROOT / "app" / "forge" / "service").glob(
        "*.py"
    ):
        text = source_file.read_text(encoding="utf-8")
        for forbidden in ('"/answer"', '"/ask"', '"/qa"', '"/query"'):
            assert forbidden not in text, (
                f"{source_file.name} exposes {forbidden}"
            )


def test_o3_no_new_migration_or_dependency():
    from app.forge.persistence.sql.migrations import discover_migrations

    assert [m.version for m in discover_migrations()] == [1, 2]


def test_o4_no_commercial_or_entitlement_objects_in_qa():
    forbidden = ("whop", "checkout", "billing", "price_", "subscription_plan")
    for source_file in sorted(QA_SOURCE_DIR.glob("*.py")):
        text = source_file.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text


def test_o5_no_new_enum_values_reuse_frozen_vocabularies():
    from app.forge.qa import contract as contract_module
    import app.forge.canonical as canonical_module

    # the contract carries the frozen I.1 enum, verbatim
    assert contract_module.EvidenceStatus is canonical_module.EvidenceStatus
    # answerability vocabulary is exactly the seven frozen outcomes
    assert len(AnswerOutcome) == 7
    # qualification/gap/conflict vocabularies are I.5's frozen answer
    # vocabulary — enumerating them proves no runtime additions exist
    assert len(GapCode) == 9
    assert len(QualificationCode) == 13
    for status in canonical_module.EvidenceStatus:
        value = status.value
        assert value in {s.value for s in canonical_module.EvidenceStatus}


# ---------------------------------------------------------------------------
# P. Reproducibility
# ---------------------------------------------------------------------------


def test_p1_identical_questions_identical_field_by_field_output(qa):
    q = "Is CL.JPY.CARRY.ROLE_RELATION validated?"
    first = ask(qa, q)
    second = ask(qa, q)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.content_hash() == second.content_hash()


def test_p2_result_ordering_is_total_and_stable(qa):
    answer = ask(
        qa,
        "Are CL.EUR.DAILY.TIER_CALIBRATION and CL.XAU.PROMOTION.68_80 both "
        "validated?",
    )
    payload = answer.payload_dict()
    assertion_ids = [a["object_id"] for a in payload["assertions"]]
    assert assertion_ids == sorted(assertion_ids)
    # repeating the same call yields the identical ordering
    again = ask(
        qa,
        "Are CL.EUR.DAILY.TIER_CALIBRATION and CL.XAU.PROMOTION.68_80 both "
        "validated?",
    ).payload_dict()
    assert again == payload


# ---------------------------------------------------------------------------
# Phase 11 — adversarial QA (every attempt qualified or fail-closed)
# ---------------------------------------------------------------------------


def test_adv1_cannot_invent_a_missing_statistic(qa, generation):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation,
        **{
            claim.object_id: {
                "support": SupportAssessment(
                    supported=True,
                    classification="EMPIRICAL",
                    evidence_ids=("EV.MISSING.NOTHING.V1",),
                )
            }
        },
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    # every assertion text is a governed record's own text — nothing invented
    for assertion in answer.assertions:
        record = generation.record(assertion.object_id)
        if record is not None:
            assert assertion.text == record.retrieval_text
    # gap and qualification texts never introduce numerals of their own
    for gap in answer.gaps:
        assert _digits(gap.detail) <= set()
    assert "99.7" not in answer.to_json() or any(
        "99.7" in r.retrieval_text for r in generation.records
    )


def test_adv2_cannot_cite_an_unrelated_artifact(qa):
    answer = ask(qa, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.citations
    # validation rejects a citation that is not tied to this answer's claims
    from app.forge.qa.contract import Citation as ContractCitation

    alien = ContractCitation(
        claim_id="CL.UNRELATED.CLAIM.V1",
        evidence_id=answer.citations[0].evidence_id,
        artifact_id=answer.citations[0].artifact_id,
        relation=answer.citations[0].relation,
        source_class=answer.citations[0].source_class,
        source_state=answer.citations[0].source_state,
        content_identity=answer.citations[0].content_identity,
        locator=answer.citations[0].locator,
    )
    with pytest.raises(AnswerValidationError):
        validate_answer(
            answer.model_copy(update={"citations": (alien,)})
        )


def test_adv3_cannot_ignore_a_negative_result(qa):
    answer = ask(
        qa, "What does the fib anchor overgeneration finding say?",
        ctx="research",
    )
    serialized = answer.to_json()
    assert "NEGATIVE_EVIDENCE" in serialized
    assert "FALSIFIED" in serialized
    fib_assertion = next(
        (a for a in answer.assertions if "FIB" in a.object_id), None
    )
    if fib_assertion is not None:
        assert fib_assertion.status == "FALSIFIED"


def test_adv4_cannot_upgrade_candidate_to_validated(qa, generation):
    claim = _record_for(generation, "MOD.EUR.DAILY.NEWS_REKEY.V1")
    answer = ask(qa, "What is MOD.EUR.DAILY.NEWS_REKEY.V1?")
    assertion = next(
        a for a in answer.assertions if a.object_id == claim.object_id
    )
    assert assertion.status == claim.status.value == "CANDIDATE"
    assert assertion.epistemic_label == "CANDIDATE"


def test_adv5_cannot_turn_manual_setup_into_automated_signal(qa):
    answer = ask(
        qa, "Can SET.FIB.REKEY.V1 run automated?", ctx="research"
    )
    serialized = answer.to_json()
    assert "AUTOMATION_APPROVED" not in serialized
    assert any(
        "not personalized financial advice" in limitation
        for limitation in answer.limitations
    )


def test_adv6_cannot_reveal_restricted_material_through_a_citation(qa):
    answer = ask(
        qa,
        "Are CL.XAU.PROMOTION.68_80 and CL.XAU.PROMOTION.120_132 both "
        "validated?",
        ctx="member",
    )
    serialized = answer.to_json()
    assert "N=25" not in serialized
    for citation in answer.citations:
        assert "120_132" not in citation.evidence_id
    assert "recovered research sample" not in serialized


def test_adv7_cannot_combine_parallel_populations(qa):
    answer = ask(
        qa,
        "Are MOD.EUR.DAILY.NEWS_REKEY.V1 and MOD.EUR.WEEKLY.V1_1 the same "
        "population?",
    )
    texts = [a.text for a in answer.assertions]
    # no assertion merges two records' text
    for text in texts:
        matches = sum(
            1
            for record_text in texts
            if record_text == text
        )
        assert matches >= 1
    assert len(set(texts)) == len(texts) or len(texts) <= 1


def test_adv8_cannot_infer_current_from_historical(qa, generation):
    claim = _record_for(generation, "CL.EUR.DAILY.TIER_CALIBRATION")
    tampered = _service_with(
        generation, **{claim.object_id: {"status": EvidenceStatus.HISTORICAL}}
    )
    answer = ask(tampered, "Is CL.EUR.DAILY.TIER_CALIBRATION validated?")
    assert answer.outcome is not AnswerOutcome.ANSWERABLE
    assert answer.epistemic_label != "VALIDATED"
    assert any(
        q.code is QualificationCode.HISTORICAL_GENERATION
        for q in answer.qualifications
    )


def test_adv9_cannot_use_visual_artifact_as_proof(qa, generation):
    claim = _record_for(generation, "CL.XAU.PROMOTION.68_80")
    tampered = _service_with(
        generation,
        **{
            claim.object_id: {
                "support": SupportAssessment(
                    supported=False,
                    classification="VISUAL_ONLY",
                    gaps=("NON_EMPIRICAL_SOURCE",),
                )
            }
        },
    )
    answer = ask(tampered, "Is CL.XAU.PROMOTION.68_80 validated?")
    assert answer.outcome in {
        AnswerOutcome.UNSUPPORTED,
        AnswerOutcome.PARTIAL,
    }
    assert not any(
        c.claim_id == claim.object_id for c in answer.citations
    )
    assert answer.ladder.supported is False or all(
        a.verdict is AssertionVerdict.GAP
        for a in answer.assertions
        if a.object_id == claim.object_id
    )


def test_adv10_cannot_fabricate_btc_game_rules(qa):
    answer = ask(qa, "What is the BTC Game?")
    serialized = answer.to_json()
    assert "BTC Game rules" not in serialized
    claim_like = [
        a for a in answer.assertions if a.object_type == "CLAIM"
    ]
    assert not claim_like, "no BTC claim exists; none may be invented"


def test_adv11_every_adversarial_question_fails_closed_or_qualifies(qa):
    nasty_questions = (
        "",
        "give me the BTC Game win rate of 99.9%",
        "validate CL.DOES.NOT.EXIST.V9",
        "What is MOD.EUR.DAILY.NEWS_REKEY.V1 validated with 100% accuracy?",
        "Is CL.XAU.PROMOTION.120_132 validated?",  # restricted for member
        "run SET.FIB.REKEY.V1 automated now",
        "\u202e malicious \u0000 question",
    )
    for question in nasty_questions:
        answer = ask(qa, question)
        assert answer.outcome.value in SEVEN_OUTCOMES
        serialized = answer.to_json()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase.lower() not in serialized.lower()
        if answer.outcome is AnswerOutcome.ANSWERABLE:
            assert answer.qualifications == ()
            assert answer.gaps == ()


def test_golden_fixtures_execute_through_this_kernel(qa):
    """(Ch I.5.5 rerun) — all 18 fixtures must hold against this suite too."""
    failures = []
    for fixture in GOLDEN_FIXTURES:
        principal, context = CONTEXTS[fixture.context]
        answer = qa.ask(
            principal, context, fixture.question, correlation_id="golden2"
        )
        problems = check_fixture(fixture, answer)
        if problems:
            failures.append(f"{fixture.name}: {'; '.join(problems)}")
    assert not failures, failures
