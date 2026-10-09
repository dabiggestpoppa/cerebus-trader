"""I.5 golden fixtures (Ch I.5.5 + PLAN §12): question → expected route.

Explicit fixtures for the seven launch models and the eight CEREBUS truth
traps. Every fixture is executed through the real kernel by
``tests/test_forge_corpus_qa.py`` — an accurately qualified answer must
pass; a misleadingly confident one must fail (``forbidden_texts`` /
``forbidden_id_fragments`` / expected outcome).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoldenFixture:
    name: str
    question: str
    context: str                 # member | research | operator | anon
    expected_class: str          # AnswerClass value
    expected_outcomes: tuple[str, ...]
    route: tuple[str, ...] = ()  # ids required among assertions ∪ claim_refs
    qualification_codes: tuple[str, ...] = ()
    gap_codes: tuple[str, ...] = ()
    expected_label: str | None = None
    expected_limitations: tuple[str, ...] = ()
    require_texts: tuple[str, ...] = ()
    forbidden_texts: tuple[str, ...] = ()
    forbidden_id_fragments: tuple[str, ...] = ()


def _ids(answer) -> set[str]:
    return {a.object_id for a in answer.assertions} | set(answer.claim_refs)


def check_fixture(fixture: GoldenFixture, answer) -> list[str]:
    """Return a list of violations (empty ⇒ fixture passes)."""
    problems: list[str] = []
    if answer.answer_class.value != fixture.expected_class:
        problems.append(
            f"class {answer.answer_class.value} != {fixture.expected_class}"
        )
    if answer.outcome.value not in fixture.expected_outcomes:
        problems.append(
            f"outcome {answer.outcome.value} not in {fixture.expected_outcomes}"
        )
    present = _ids(answer)
    for required in fixture.route:
        if required not in present:
            problems.append(f"route id missing: {required}")
    codes = {q.code.value for q in answer.qualifications}
    for required in fixture.qualification_codes:
        if required not in codes:
            problems.append(f"qualification missing: {required}")
    gaps = {g.code.value for g in answer.gaps}
    for required in fixture.gap_codes:
        if required not in gaps:
            problems.append(f"gap missing: {required}")
    if fixture.expected_label is not None:
        if answer.epistemic_label != fixture.expected_label:
            problems.append(
                f"label {answer.epistemic_label} != {fixture.expected_label}"
            )
    limitations = set(answer.limitations)
    for required in fixture.expected_limitations:
        if required not in limitations:
            problems.append(f"limitation missing: {required}")
    serialized = answer.to_json()
    for required in fixture.require_texts:
        if required not in serialized:
            problems.append(f"required text missing: {required!r}")
    for forbidden in fixture.forbidden_texts:
        if forbidden in serialized:
            problems.append(f"forbidden text present: {forbidden!r}")
    for fragment in fixture.forbidden_id_fragments:
        if any(fragment in object_id for object_id in present):
            problems.append(f"forbidden id fragment: {fragment!r}")
    return problems


# ---------------------------------------------------------------------------
# The seven launch models (Ch I.5.5)
# ---------------------------------------------------------------------------

LAUNCH_MODEL_FIXTURES: tuple[GoldenFixture, ...] = (
    GoldenFixture(
        name="eur_daily_model_doctrine",
        question="What is MOD.EUR.DAILY.NEWS_REKEY.V1?",
        context="member",
        expected_class="DESCRIPTIVE",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("MOD.EUR.DAILY.NEWS_REKEY.V1",),
        qualification_codes=("CANDIDATE_STATUS",),
        expected_label="CANDIDATE",
    ),
    GoldenFixture(
        name="eur_daily_tier_claim_validated",
        question="Is CL.EUR.DAILY.TIER_CALIBRATION validated?",
        context="member",
        expected_class="EMPIRICAL",
        expected_outcomes=("ANSWERABLE",),
        route=("CL.EUR.DAILY.TIER_CALIBRATION",),
        expected_label="VALIDATED",
        require_texts=("Phase1 Asian-range tiers",),
    ),
    GoldenFixture(
        name="eur_weekly_research_sample",
        question="Is CL.EUR.WEEKLY.TIER_RANGE research qualified?",
        context="member",
        expected_class="DESCRIPTIVE",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.EUR.WEEKLY.TIER_RANGE",),
        qualification_codes=("RESEARCH_SAMPLE",),
        expected_label="VALIDATED",
        require_texts=("recovered research sample",),
    ),
    GoldenFixture(
        name="eur_higher_order_forward_oos",
        question="Is CL.EUR.HO.D3_DIRECTION validated?",
        context="member",
        expected_class="EMPIRICAL",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.EUR.HO.D3_DIRECTION",),
        qualification_codes=("FORWARD_OOS",),
        expected_label="FORWARD_OOS",
        require_texts=("forward out-of-sample",),
    ),
    GoldenFixture(
        name="xau_game_small_n_validated",
        question="Is CL.XAU.PROMOTION.68_80 validated?",
        context="member",
        expected_class="EMPIRICAL",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.XAU.PROMOTION.68_80",),
        qualification_codes=("SMALL_N",),
        expected_label="VALIDATED",
        require_texts=("N=48",),
    ),
    GoldenFixture(
        name="jpy_basket_role_relationship",
        question="Is CL.JPY.CARRY.ROLE_RELATION validated?",
        context="member",
        expected_class="EMPIRICAL",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.JPY.CARRY.ROLE_RELATION",),
        qualification_codes=("RELATIONSHIP_STATISTIC",),
        expected_label="VALIDATED",
        require_texts=("never a trade win rate",),
        forbidden_texts=("win rate of", "probability of"),
    ),
    GoldenFixture(
        name="btc_tracker_honest_gap",
        question="Does the BTC tracker establish BTC Game rules?",
        context="member",
        expected_class="DESCRIPTIVE",
        expected_outcomes=("PARTIAL",),
        route=("MOD.BTC.TRACKER.DWM.V1",),
        gap_codes=("NO_EVIDENCE_REFERENCE",),
        forbidden_id_fragments=("CL.BTC", "GAME"),
    ),
    GoldenFixture(
        name="fib_r11_negative_evidence",
        question="What does CL.FIB.R11.GENERATOR_FAILURE say?",
        context="member",
        expected_class="DESCRIPTIVE",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.FIB.R11.GENERATOR_FAILURE",),
        qualification_codes=("NEGATIVE_EVIDENCE",),
        expected_label="NEGATIVE_EVIDENCE",
        require_texts=("overproduced",),
    ),
)

# ---------------------------------------------------------------------------
# The eight truth traps (PLAN §12)
# ---------------------------------------------------------------------------

TRUTH_TRAP_FIXTURES: tuple[GoldenFixture, ...] = (
    # 1. Symmetry trap: manual/operator validity ≠ automation parity.
    GoldenFixture(
        name="symmetry_research_setup_not_automation",
        question="Can SET.FIB.REKEY.V1 run automated?",
        context="research",
        expected_class="ACTIONABLE",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("SET.FIB.REKEY.V1",),
        qualification_codes=("RESEARCH_FLAG",),
        expected_limitations=(
            "actionable answers are research/operator context, not personalized "
            "financial advice",
        ),
        forbidden_texts=("AUTOMATION_APPROVED",),
    ),
    GoldenFixture(
        name="symmetry_member_restricted_research_setup",
        question="Can SET.FIB.REKEY.V1 run automated?",
        context="member",
        expected_class="ACTIONABLE",
        expected_outcomes=("RESTRICTED",),
        forbidden_texts=("AUTOMATION_APPROVED",),
    ),
    # 2. P90: lineage vocabulary, version/evidence bound, never a statistic.
    GoldenFixture(
        name="p90_stays_lineage",
        question="What is P90 in MOD.EUR.DAILY.NEWS_REKEY.V1?",
        context="member",
        expected_class="ACTIONABLE",
        expected_outcomes=("PARTIAL", "ANSWERABLE_QUALIFIED"),
        route=("MOD.EUR.DAILY.NEWS_REKEY.V1",),
        require_texts=(
            "lineage",
            "do not import historical P90 win rates",
        ),
        forbidden_texts=("P90 win rate ", "P90 performance"),
    ),
    # 3. BTC: tracker ≠ game (also in launch fixtures).
    GoldenFixture(
        name="btc_game_not_invented",
        question="What is the BTC Game?",
        context="member",
        expected_class="DESCRIPTIVE",
        expected_outcomes=("PARTIAL", "UNSUPPORTED"),
        route=("MOD.BTC.TRACKER.DWM.V1",),
        gap_codes=("NO_EVIDENCE_REFERENCE",),
        forbidden_id_fragments=("CL.BTC", "GAME"),
        forbidden_texts=("BTC Game rules",),
    ),
    # 4. EURUSD: families never collapse.
    GoldenFixture(
        name="eur_families_stay_separate",
        question=(
            "Are MOD.EUR.DAILY.NEWS_REKEY.V1 and MOD.EUR.WEEKLY.V1_1 the "
            "same population?"
        ),
        context="member",
        expected_class="COMPARATIVE",
        expected_outcomes=("ANSWERABLE_QUALIFIED", "ANSWERABLE"),
        route=("MOD.EUR.DAILY.NEWS_REKEY.V1", "MOD.EUR.WEEKLY.V1_1"),
        expected_limitations=(
            "parallel populations are presented separately and never merged",
        ),
        forbidden_texts=("same population as",),
    ),
    # 5. XAU: layers stay distinct.
    GoldenFixture(
        name="xau_layers_stay_distinct",
        question="Are L3 destination and L1 execution different layers for XAU?",
        context="member",
        expected_class="COMPARATIVE",
        expected_outcomes=("ANSWERABLE_QUALIFIED", "ANSWERABLE"),
        route=("MOD.XAU.GAME.L1_L2_L3.V1",),
        require_texts=("explicit layer ownership",),
    ),
    # 6. JPY: role asymmetry preserved.
    GoldenFixture(
        name="jpy_role_asymmetry_preserved",
        question=(
            "Are CL.JPY.CARRY.ROLE_RELATION and MOD.JPY.CARRY_GAME.L1_L3.V1 "
            "distinct?"
        ),
        context="member",
        expected_class="COMPARATIVE",
        expected_outcomes=("ANSWERABLE_QUALIFIED", "ANSWERABLE"),
        route=(
            "CL.JPY.CARRY.ROLE_RELATION",
            "MOD.JPY.CARRY_GAME.L1_L3.V1",
        ),
        require_texts=("USDJPY,AUDJPY,EURJPY", "EURJPY confirmation"),
        forbidden_texts=("EURJPY is the master", "equal directional vote"),
    ),
    # 7. Fib: negative evidence survives as falsified (also launch fixture).
    GoldenFixture(
        name="fib_negative_never_positive_rule",
        question="What does the fib anchor overgeneration finding say?",
        context="research",
        expected_class="EMPIRICAL",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.FIB.R11.GENERATOR_FAILURE",),
        qualification_codes=("NEGATIVE_EVIDENCE",),
        expected_label="NEGATIVE_EVIDENCE",
        require_texts=("overproduced",),
        forbidden_texts=("is now validated", "current trading rule"),
    ),
    # 8. Research statistics: small-N qualifiers survive.
    GoldenFixture(
        name="xau_120_research_small_n",
        question="Is CL.XAU.PROMOTION.120_132 validated?",
        context="research",
        expected_class="EMPIRICAL",
        expected_outcomes=("ANSWERABLE_QUALIFIED",),
        route=("CL.XAU.PROMOTION.120_132",),
        qualification_codes=("RESEARCH_FLAG", "SMALL_N"),
        expected_label="RESEARCH_FLAG",
        require_texts=("N=25",),
    ),
    GoldenFixture(
        name="xau_120_member_chain_restricted",
        question="Is CL.XAU.PROMOTION.120_132 validated?",
        context="member",
        expected_class="EMPIRICAL",
        expected_outcomes=("UNSUPPORTED",),
        route=("CL.XAU.PROMOTION.120_132",),
        gap_codes=("DENIED",),
        expected_label="INSUFFICIENT_EVIDENCE",
    ),
)

GOLDEN_FIXTURES: tuple[GoldenFixture, ...] = (
    LAUNCH_MODEL_FIXTURES + TRUTH_TRAP_FIXTURES
)

__all__ = [
    "GoldenFixture",
    "GOLDEN_FIXTURES",
    "LAUNCH_MODEL_FIXTURES",
    "TRUTH_TRAP_FIXTURES",
    "check_fixture",
]
