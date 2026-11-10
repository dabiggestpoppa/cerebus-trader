"""Additive evaluation corpus V2: evidence-path coverage (EV-145..EV-154).

Every case is a CHAIN positive, so the evidence it must cite is produced by the
real interpreter -> retrieval -> context -> gateway -> validate path rather than
scripted into a package.

Expectations are declared here, before any run, from the frozen canonical
catalog in ``implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py``
(the ``MOD.*`` object ids and the ``EV.*`` evidence ids that catalog defines).
No expectation is copied from a retrieval result, a draft, an answer or a
previous evaluation report.

This module is data. It imports only the evaluation schema and enums.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.forge.ask_cerebus.evaluation import enums
from app.forge.ask_cerebus.evaluation.schema import (
    EvaluationCase,
    ExpectedEvidencePath,
    digest_of,
)

CORPUS_VERSION = "ASK_EVALUATION_DATASET_V2"
CASE_SCHEMA_VERSION = "ASK_EVALUATION_CASE_SCHEMA_V1"
CATALOG = "implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py"
DIRECTORY = Path(__file__).resolve().parent

REQUIRED_FIELDS = (
    "WHAT_IT_MEANS",
    "WHAT_CEREBUS_SEES",
    "WHAT_IT_DOES_NOT_MEAN",
    "NEXT_RELEVANT_STATE",
)

#: ``(number, query, canonical model, evidence refs, depth, market, reconciliation)``
#:
#: ``canonical_model`` and ``evidence_refs`` are Book I catalog identities. A case
#: with no canonical model is an explicitly plan-sourced question: its expectation
#: is that no unrelated model is substituted, not that a model is cited.
_DECLARED: tuple[tuple[int, str, str, tuple[str, ...], str, str, str], ...] = (
    (145, "Show me the BTC Game state.", "MOD.BTC.GAME.V1", (), "BEGINNER", "BTCUSD", "CANONICAL_PATH"),
    (146, "Show me the Gold Game state.", "MOD.XAU.GAME.V1", ("EV.XAU.SUPPORTED.V1",), "OPERATOR", "XAUUSD", "CANONICAL_PATH"),
    (147, "Compare the BTC Game and the BTC Tracker.", "MOD.BTC.GAME.V1", ("MOD.BTC.TRACKER.V1",), "RESEARCHER", "BTCUSD", "CANONICAL_PATH"),
    (148, "Show me the ST manual state.", "MOD.ST.MANUAL.V1", (), "BEGINNER", "XAUUSD", "CANONICAL_PATH"),
    (149, "Explain the ST manual.", "MOD.ST.MANUAL.V1", (), "OPERATOR", "XAUUSD", "CANONICAL_PATH"),
    (150, "What does the BTC Tracker show?", "MOD.BTC.TRACKER.V1", (), "RESEARCHER", "BTCUSD", "CANONICAL_PATH"),
    (151, "Show me the Fib range birth state.", "MOD.FIB.RANGE_BIRTH.V1", ("EV.FIB.NEGATIVE.V1",), "OPERATOR", "XAUUSD", "CANONICAL_PATH"),
    (152, "Show me the BTC Tracker state.", "MOD.BTC.TRACKER.V1", (), "BEGINNER", "BTCUSD", "CANONICAL_PATH"),
    (153, "Compare the Gold Game and Gold Game V2.", "MOD.XAU.GAME.V1", ("EV.XAU.SUPPORTED.V1",), "OPERATOR", "XAUUSD", "CANONICAL_PATH"),
    (154, "Show me the Gold comparison state.", "", (), "BEGINNER", "XAUUSD", "PLAN_ONLY_NO_MODEL"),
)


def _case(
    number: int,
    query: str,
    model: str,
    evidence: tuple[str, ...],
    depth: str,
    market: str,
    reconciliation: str,
) -> EvaluationCase:
    case_id = f"EV-{number}"
    return EvaluationCase(
        case_id=case_id,
        family=enums.CaseFamily.POSITIVE_CONTROL,
        kind=enums.CaseKind.POSITIVE_CONTROL,
        execution_mode=enums.ExecutionMode.CHAIN,
        query_text=query,
        depth=depth,
        intent_expected="MODEL_DESCRIPTION",
        entities_expected=(),
        market=market,
        model_ids=(model.replace("MOD.", "").removesuffix(".V1"),) if model else (),
        time_scope=enums.TimeScope.ANY,
        fixture_source=f"CHAIN:{query}",
        evidence_path=ExpectedEvidencePath(
            fixture_path=CATALOG,
            builder="build_chain_index",
            record=model or query,
            values=(("model", model), ("reconciliation", reconciliation)),
        ),
        authority=enums.Authority.FIXTURE_FACT,
        expected_outcome=enums.ExpectedOutcomeKind.ANSWER,
        expected_refusal_code=None,
        expected_finding_class=None,
        required_claims=(),
        forbidden_claims=(),
        forbidden_numbers=(),
        required_limitations=(),
        expected_citations=(model,) if model else (),
        expected_eligibility=None,
        expected_freshness=enums.ExpectedFreshness.NOT_REQUIRED,
        expected_validation_codes=(),
        required_fields=REQUIRED_FIELDS,
        score_population=(
            enums.MetricId.VALID_ANSWER_COMPLETION_RATE,
            enums.MetricId.FALSE_REFUSAL_RATE,
        ),
        unresolved_owner=None,
        notes=(
            "Additive F-06 evidence-path control: the question must be answered "
            "from the declared canonical object, not from the query plan."
            if model
            else "Additive F-06 control: no canonical model exists for this question, "
            "so a plan-level source is correct and no model may be substituted."
        ),
    )


def cases() -> tuple[EvaluationCase, ...]:
    return tuple(_case(*row) for row in _DECLARED)


def digest() -> str:
    return digest_of([case.payload() for case in cases()])


def manifest() -> dict[str, object]:
    return {
        "dataset_version": CORPUS_VERSION,
        "schema_version": CASE_SCHEMA_VERSION,
        "digest": digest(),
        "case_count": len(cases()),
        "case_ids": [case.case_id for case in cases()],
        "execution_modes": ["CHAIN"],
        "declared_canonical_models": {
            case.case_id: case.expected_citations[0] if case.expected_citations else ""
            for case in cases()
        },
    }


def write_fixtures(directory: Path | str = DIRECTORY) -> tuple[Path, ...]:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for case in cases():
        path = root / f"{case.case_id}.json"
        path.write_text(
            json.dumps(case.payload(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        written.append(path)
    manifest_path = root / "DATASET_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    written.append(manifest_path)
    return tuple(written)


__all__ = [
    "CATALOG",
    "CORPUS_VERSION",
    "CASE_SCHEMA_VERSION",
    "DIRECTORY",
    "REQUIRED_FIELDS",
    "cases",
    "digest",
    "manifest",
    "write_fixtures",
]
