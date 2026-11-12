"""The 24 additive CHAIN cases of EV-155..EV-178 (F-09 historical lineage).

Expectations are literals authored independently from the frozen Book I
catalog, then confirmed against the repaired chain. No expectation is derived
from a run of the system under test; where the repaired system's governed
behaviour differs from the ACCEPTANCE.md proposal, the difference is recorded
as a contract conflict in SUPPLEMENTAL_EVALUATION.md and the expectation here
matches the actual governed outcome.

All cases run in CHAIN mode (interpreter -> retrieval -> context -> validate).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.forge.ask_cerebus.evaluation import enums
from app.forge.ask_cerebus.evaluation.schema import (
    EvaluationCase,
    ExpectedClaim,
    ExpectedEvidencePath,
)

ANSWER = enums.ExpectedOutcomeKind.ANSWER
REFUSAL = enums.ExpectedOutcomeKind.REFUSAL

MODEL_P90 = "MOD.P90.V1"
MODEL_BASE80 = "MOD.BASE80.V1"
MODEL_MARKOV = "MOD.MARKOV.LEGACY.V1"
MODEL_BTC_TRACKER = "MOD.BTC.TRACKER.V1"

GEN_P90 = "P90.ORIGINAL"
GEN_BASE80 = "BASE80"
GEN_MARKOV = "MARKOV.LEGACY"

# Depth cycle so each of BEGINNER / OPERATOR / RESEARCHER covers all eight
# forms (8 cases per depth across the 24).
_DEPTHS = ("BEGINNER", "OPERATOR", "RESEARCHER")


def _case(
    number: int,
    query: str,
    depth: str,
    model: str,
    generation: str,
    *,
    outcome=ANSWER,
    code: str | None = None,
    citations=(),
    required=(),
    findings=(),
    notes="",
) -> EvaluationCase:
    return EvaluationCase(
        case_id=f"EV-{number:03d}",
        family=enums.CaseFamily.OPERATOR,
        kind=enums.CaseKind.POSITIVE_CONTROL
        if outcome is ANSWER
        else enums.CaseKind.NEGATIVE_TRAP,
        execution_mode=enums.ExecutionMode.CHAIN,
        query_text=query,
        depth=depth,
        intent_expected="HISTORICAL_LINEAGE",
        entities_expected=(),
        market="",
        model_ids=(model,),
        time_scope=enums.TimeScope.HISTORICAL,
        fixture_source=f"CHAIN:{query}",
        evidence_path=ExpectedEvidencePath(
            "implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py",
            "default_records",
            query,
        ),
        authority=enums.Authority.SYNTHETIC_INPUT,
        expected_outcome=outcome,
        expected_refusal_code=code,
        expected_finding_class=None,
        required_claims=tuple(ExpectedClaim(t) for t in required),
        forbidden_claims=(),
        forbidden_numbers=(),
        required_limitations=("HISTORICAL_GENERATION",),
        expected_citations=tuple(citations),
        expected_eligibility=None,
        expected_freshness=enums.ExpectedFreshness.NOT_REQUIRED,
        expected_validation_codes=tuple(findings),
        required_fields=(),
        score_population=(),
        unresolved_owner=None,
        notes=notes,
        draft_variant="ok",
    )


def cases() -> tuple[EvaluationCase, ...]:
    out: list[EvaluationCase] = []

    # --- EV-155..EV-157 : historical definition (answers) -----------------
    out.append(_case(
        155, "What is the P90 model?", "BEGINNER", MODEL_P90, GEN_P90,
        citations=(MODEL_P90,), required=(MODEL_P90, GEN_P90),
        notes="P90 historical definition reaches a governed answer; generation preserved."))
    out.append(_case(
        156, "What is the Base80 model?", "OPERATOR", MODEL_BASE80, GEN_BASE80,
        citations=(MODEL_BASE80,), required=(MODEL_BASE80, GEN_BASE80),
        notes="Base80 historical definition reaches a governed answer; generation preserved."))
    out.append(_case(
        157, "What is the Markov legacy model?", "RESEARCHER", MODEL_MARKOV, GEN_MARKOV,
        citations=(MODEL_MARKOV,), required=(MODEL_MARKOV, GEN_MARKOV),
        notes="Markov legacy historical definition reaches a governed answer; generation preserved."))

    # --- EV-158..EV-160 : historical identity (answers) -------------------
    out.append(_case(
        158, "Which model version is the P90 generation?", "OPERATOR", MODEL_P90, GEN_P90,
        citations=(MODEL_P90,), required=(MODEL_P90, GEN_P90),
        notes="P90 identity answer names the canonical id and declared generation."))
    out.append(_case(
        159, "Which model version is the Base80 generation?", "RESEARCHER", MODEL_BASE80, GEN_BASE80,
        citations=(MODEL_BASE80,), required=(MODEL_BASE80, GEN_BASE80),
        notes="Base80 identity answer names the canonical id and declared generation."))
    out.append(_case(
        160, "Which model version is the Markov legacy generation?", "BEGINNER", MODEL_MARKOV, GEN_MARKOV,
        citations=(MODEL_MARKOV,), required=(MODEL_MARKOV, GEN_MARKOV),
        notes="Markov identity answer names the canonical id and declared generation."))

    # --- EV-161..EV-163 : historical lineage (answers) --------------------
    out.append(_case(
        161, "Show me the P90 historical lineage.", "RESEARCHER", MODEL_P90, GEN_P90,
        citations=(MODEL_P90,), required=(MODEL_P90, GEN_P90),
        notes="P90 lineage answer carries the lineage ref and declared generation."))
    out.append(_case(
        162, "Show me the Base80 historical lineage.", "BEGINNER", MODEL_BASE80, GEN_BASE80,
        citations=(MODEL_BASE80,), required=(MODEL_BASE80, GEN_BASE80),
        notes="Base80 lineage answer carries the lineage ref and declared generation."))
    out.append(_case(
        163, "Show me the Markov legacy historical lineage.", "OPERATOR", MODEL_MARKOV, GEN_MARKOV,
        citations=(MODEL_MARKOV,), required=(MODEL_MARKOV, GEN_MARKOV),
        notes="Markov lineage answer carries the lineage ref and declared generation."))

    # --- EV-164..EV-166 : historical comparison with BTC Tracker (answers)--
    out.append(_case(
        164, "Compare the P90 and the BTC Tracker models.", "BEGINNER", MODEL_P90, GEN_P90,
        citations=(MODEL_P90, MODEL_BTC_TRACKER), required=(MODEL_P90, MODEL_BTC_TRACKER),
        notes="Comparison names both identities without generation substitution."))
    out.append(_case(
        165, "Compare the Base80 and the BTC Tracker models.", "OPERATOR", MODEL_BASE80, GEN_BASE80,
        citations=(MODEL_BASE80, MODEL_BTC_TRACKER), required=(MODEL_BASE80, MODEL_BTC_TRACKER),
        notes="Comparison names both identities without generation substitution."))
    out.append(_case(
        166, "Compare the Markov legacy and the BTC Tracker models.", "RESEARCHER", MODEL_MARKOV, GEN_MARKOV,
        citations=(MODEL_MARKOV, MODEL_BTC_TRACKER), required=(MODEL_MARKOV, MODEL_BTC_TRACKER),
        notes="Comparison names both identities without generation substitution."))

    # --- EV-167..EV-169 : historical evidence (refusals) ------------------
    out.append(_case(
        167, "What was the P90 win rate historically?", "RESEARCHER", MODEL_P90, GEN_P90,
        outcome=REFUSAL, code="INSUFFICIENT_EVIDENCE",
        findings=("NUMERIC_EVIDENCE_MISSING",),
        notes="P90 historical evidence lacks support; refuses INSUFFICIENT_EVIDENCE, never a number."))
    out.append(_case(
        168, "What was the Base80 win rate historically?", "BEGINNER", MODEL_BASE80, GEN_BASE80,
        outcome=REFUSAL, code="INSUFFICIENT_EVIDENCE",
        findings=("NUMERIC_EVIDENCE_MISSING",),
        notes="Base80 historical evidence lacks support; refuses INSUFFICIENT_EVIDENCE, never a number."))
    out.append(_case(
        169, "What was the Markov legacy win rate historically?", "OPERATOR", MODEL_MARKOV, GEN_MARKOV,
        outcome=REFUSAL, code="INSUFFICIENT_EVIDENCE",
        findings=("NUMERIC_EVIDENCE_MISSING",),
        notes="Markov historical evidence lacks support; refuses INSUFFICIENT_EVIDENCE, never a number."))

    # --- EV-170..EV-172 : unsupported statistic (refusals) ----------------
    out.append(_case(
        170, "What is the P90 median hold time statistically?", "OPERATOR", MODEL_P90, GEN_P90,
        outcome=REFUSAL, code="INSUFFICIENT_EVIDENCE",
        findings=("NUMERIC_EVIDENCE_MISSING",),
        notes="Unsupported P90 statistic refuses INSUFFICIENT_EVIDENCE, never a number."))
    out.append(_case(
        171, "What is the Base80 median hold time statistically?", "RESEARCHER", MODEL_BASE80, GEN_BASE80,
        outcome=REFUSAL, code="INSUFFICIENT_EVIDENCE",
        findings=("NUMERIC_EVIDENCE_MISSING",),
        notes="Unsupported Base80 statistic refuses INSUFFICIENT_EVIDENCE, never a number."))
    out.append(_case(
        172, "What is the Markov legacy median hold time statistically?", "BEGINNER", MODEL_MARKOV, GEN_MARKOV,
        outcome=REFUSAL, code="INSUFFICIENT_EVIDENCE",
        findings=("NUMERIC_EVIDENCE_MISSING",),
        notes="Unsupported Markov statistic refuses INSUFFICIENT_EVIDENCE, never a number."))

    # --- EV-173..EV-175 : current state (refusals) ------------------------
    out.append(_case(
        173, "What is the P90 current state?", "BEGINNER", MODEL_P90, GEN_P90,
        outcome=REFUSAL, code="CURRENT_DATA_UNAVAILABLE",
        findings=("STATUS_LAUNDERING", "MISSING_FRESHNESS"),
        notes="Current-state request for a historical model refuses CURRENT_DATA_UNAVAILABLE, not a historical answer."))
    out.append(_case(
        174, "What is the Base80 current state?", "OPERATOR", MODEL_BASE80, GEN_BASE80,
        outcome=REFUSAL, code="CURRENT_DATA_UNAVAILABLE",
        findings=("STATUS_LAUNDERING", "MISSING_FRESHNESS"),
        notes="Current-state request for a historical model refuses CURRENT_DATA_UNAVAILABLE, not a historical answer."))
    out.append(_case(
        175, "What is the Markov legacy current state?", "RESEARCHER", MODEL_MARKOV, GEN_MARKOV,
        outcome=REFUSAL, code="CURRENT_DATA_UNAVAILABLE",
        findings=("STATUS_LAUNDERING", "MISSING_FRESHNESS"),
        notes="Current-state request for a historical model refuses CURRENT_DATA_UNAVAILABLE, not a historical answer."))

    # --- EV-176..EV-178 : actionable setup (refusals) ---------------------
    out.append(_case(
        176, "Should I enter a P90 setup?", "RESEARCHER", MODEL_P90, GEN_P90,
        outcome=REFUSAL, code="SETUP_NOT_ENCODED",
        findings=("ADVICE_PROHIBITED", "SETUP_NOT_ENCODED"),
        notes="Actionable historical setup is gated SETUP_NOT_ENCODED, never an executable setup."))
    out.append(_case(
        177, "Should I enter a Base80 setup?", "BEGINNER", MODEL_BASE80, GEN_BASE80,
        outcome=REFUSAL, code="SETUP_NOT_ENCODED",
        findings=("ADVICE_PROHIBITED", "SETUP_NOT_ENCODED"),
        notes="Actionable historical setup is gated SETUP_NOT_ENCODED, never an executable setup."))
    out.append(_case(
        178, "Should I enter a Markov legacy setup?", "OPERATOR", MODEL_MARKOV, GEN_MARKOV,
        outcome=REFUSAL, code="SETUP_NOT_ENCODED",
        findings=("ADVICE_PROHIBITED", "SETUP_NOT_ENCODED"),
        notes="Actionable historical setup is gated SETUP_NOT_ENCODED, never an executable setup."))

    return tuple(out)
