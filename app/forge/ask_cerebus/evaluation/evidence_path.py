"""Independent evidence-path evaluation V2 (F-06).

The V1 matcher asked whether an answer's citations *resolved*. That is necessary
and not sufficient: an answer can be fluent, cite a resolvable object, and still
be about the wrong canonical object, cite a query-plan pseudo-item instead of the
evidence the question requires, or carry the right statistic from the wrong
generation.

This module evaluates the whole path a positive control must walk:

    query intent -> canonical model -> claim -> evidence -> authorized package
    -> final citation

Import law. Like ``oracle.py``, this module may import only the evaluation's own
``enums``/``versions``/``schema`` and frozen fixture data. It never imports the
interpreter, retrieval, context, gateway or answer layers: an expectation built
on the system under test cannot detect a defect the system and the expectation
share. Observations arrive as plain tuples read off stage artifacts by duck
typing, so no SUT type is imported either.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

EVIDENCE_PATH_EVALUATION_V2 = "ASK_EVALUATION_EVIDENCE_PATH_V2"

PLAN_PREFIX = "PLAN."
MODEL_PREFIX = "MOD."
MANIFEST_PREFIX = "MFD."

#: How a V1 CHAIN case's plan-only citation was reconciled (F-06, BA-34).
DEFINITIONAL_PLAN_SOURCE = "DEFINITIONAL_PLAN_SOURCE"
CANONICAL_PATH = "CANONICAL_PATH"
CORPUS_ABSENT = "CORPUS_ABSENT"
PLAN_ONLY_NO_MODEL = "PLAN_ONLY_NO_MODEL"

RECONCILIATIONS = (
    CANONICAL_PATH,
    DEFINITIONAL_PLAN_SOURCE,
    CORPUS_ABSENT,
    PLAN_ONLY_NO_MODEL,
)


@dataclass(frozen=True)
class PathExpectation:
    """What a case requires, declared before any execution.

    ``canonical_model`` and ``evidence_refs`` are catalog identities. An empty
    ``canonical_model`` means the question has no canonical object: the
    expectation is then only that no unrelated model is substituted.
    """

    case_id: str
    intent: str
    canonical_model: str
    evidence_refs: tuple[str, ...]
    generation: str
    plan_only_acceptable: bool
    authority: str
    reconciliation: str

    def __post_init__(self) -> None:
        if self.reconciliation not in RECONCILIATIONS:
            raise ValueError(f"{self.case_id}: unknown reconciliation {self.reconciliation}")
        if self.reconciliation is CANONICAL_PATH and not self.canonical_model:
            raise ValueError(f"{self.case_id}: a canonical path needs a canonical model")
        if self.plan_only_acceptable and self.reconciliation is CANONICAL_PATH:
            raise ValueError(f"{self.case_id}: a canonical path cannot accept plan-only")

    @property
    def applicable(self) -> bool:
        """True when the case carries a canonical path that can be scored."""

        return bool(self.canonical_model) and not self.plan_only_acceptable

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "intent": self.intent,
            "canonical_model": self.canonical_model,
            "evidence_refs": list(self.evidence_refs),
            "generation": self.generation,
            "plan_only_acceptable": self.plan_only_acceptable,
            "authority": self.authority,
            "reconciliation": self.reconciliation,
            "applicable": self.applicable,
        }


@dataclass(frozen=True)
class PathObservation:
    """One run projected onto the stages the path check needs."""

    case_id: str
    outcome: str
    trace_ids: tuple[str, ...]
    trace_claim_ids: tuple[str, ...]
    trace_evidence_ids: tuple[str, ...]
    package_ids: tuple[str, ...]
    manifest_ids: tuple[str, ...]
    manifest_id: str
    claim_sources: tuple[tuple[str, ...], ...]
    claim_generations: tuple[str, ...]
    citations: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "outcome": self.outcome,
            "trace_ids": list(self.trace_ids),
            "trace_claim_ids": list(self.trace_claim_ids),
            "trace_evidence_ids": list(self.trace_evidence_ids),
            "package_ids": list(self.package_ids),
            "manifest_id": self.manifest_id,
            "claim_sources": [list(item) for item in self.claim_sources],
            "claim_generations": list(self.claim_generations),
            "citations": list(self.citations),
        }


@dataclass(frozen=True)
class PathVerdict:
    case_id: str
    reconciliation: str
    applicable: bool
    passed: bool
    checks: tuple[tuple[str, bool], ...]
    failures: tuple[str, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "reconciliation": self.reconciliation,
            "applicable": self.applicable,
            "passed": self.passed,
            "checks": [[name, ok] for name, ok in self.checks],
            "failures": list(self.failures),
        }

    def failed_checks(self) -> tuple[str, ...]:
        return tuple(name for name, ok in self.checks if not ok)


# ---------------------------------------------------------------------------
# V1 CHAIN reconciliation
# ---------------------------------------------------------------------------
#: The five V1 CHAIN positives, reconciled individually from their frozen query
#: text and the Book I catalog. Two are definitional questions about vocabulary
#: that has no canonical model object, two ask for model state that the frozen
#: catalog does not contain (a Book I coverage limit, not a retrieval defect),
#: and one -- EV-006 -- carries a fully observable canonical model path.
V1_CHAIN_EXPECTATIONS: tuple[PathExpectation, ...] = (
    PathExpectation(
        case_id="EV-001",
        intent="MODEL_DESCRIPTION",
        canonical_model="",
        evidence_refs=(),
        generation="",
        plan_only_acceptable=True,
        authority="Book IV IV.1 plan pseudo-item; a definitional question about a term",
        reconciliation=DEFINITIONAL_PLAN_SOURCE,
    ),
    PathExpectation(
        case_id="EV-002",
        intent="GENERAL_MARKET_KNOWLEDGE",
        canonical_model="",
        evidence_refs=(),
        generation="",
        plan_only_acceptable=True,
        authority="Book IV IV.1 plan pseudo-item; CEREBUS vocabulary, not a model",
        reconciliation=DEFINITIONAL_PLAN_SOURCE,
    ),
    PathExpectation(
        case_id="EV-006",
        intent="MODEL_DESCRIPTION",
        canonical_model="MOD.BTC.TRACKER.V1",
        evidence_refs=(),
        generation="",
        plan_only_acceptable=False,
        authority="Book I canonical catalog MOD.BTC.TRACKER.V1",
        reconciliation=CANONICAL_PATH,
    ),
    PathExpectation(
        case_id="EV-007",
        intent="GENERAL_MARKET_KNOWLEDGE",
        canonical_model="",
        evidence_refs=(),
        generation="",
        plan_only_acceptable=True,
        authority="Book I catalog contains no EUR weekly model; Book I coverage limit",
        reconciliation=CORPUS_ABSENT,
    ),
    PathExpectation(
        case_id="EV-010",
        intent="DEFINITION",
        canonical_model="",
        evidence_refs=(),
        generation="",
        plan_only_acceptable=True,
        authority="Book I catalog contains no JPY carry model; Book I coverage limit",
        reconciliation=CORPUS_ABSENT,
    ),
)

#: The additive V2 corpus, declared in
#: ``implementation/forge/book_iv/bloc_iv_6/fixtures_v2/cases.py``.
V2_EXPECTATIONS: tuple[PathExpectation, ...] = (
    PathExpectation("EV-145", "MODEL_DESCRIPTION", "MOD.BTC.GAME.V1", (), "", False, "Book I catalog MOD.BTC.GAME.V1", CANONICAL_PATH),
    PathExpectation("EV-146", "MODEL_DESCRIPTION", "MOD.XAU.GAME.V1", ("EV.XAU.SUPPORTED.V1",), "", False, "Book I catalog MOD.XAU.GAME.V1 + EV.XAU.SUPPORTED.V1", CANONICAL_PATH),
    PathExpectation("EV-147", "COMPARISON", "MOD.BTC.GAME.V1", ("MOD.BTC.TRACKER.V1",), "", False, "Book I catalog MOD.BTC.GAME.V1 + MOD.BTC.TRACKER.V1", CANONICAL_PATH),
    PathExpectation("EV-148", "GENERAL_MARKET_KNOWLEDGE", "MOD.ST.MANUAL.V1", (), "", False, "Book I catalog MOD.ST.MANUAL.V1", CANONICAL_PATH),
    PathExpectation("EV-149", "GENERAL_MARKET_KNOWLEDGE", "MOD.ST.MANUAL.V1", (), "", False, "Book I catalog MOD.ST.MANUAL.V1", CANONICAL_PATH),
    PathExpectation("EV-150", "MODEL_DESCRIPTION", "MOD.BTC.TRACKER.V1", (), "", False, "Book I catalog MOD.BTC.TRACKER.V1", CANONICAL_PATH),
    PathExpectation("EV-151", "LEVEL_COORDINATE", "MOD.FIB.RANGE_BIRTH.V1", ("EV.FIB.NEGATIVE.V1",), "", False, "Book I catalog MOD.FIB.RANGE_BIRTH.V1 + EV.FIB.NEGATIVE.V1", CANONICAL_PATH),
    PathExpectation("EV-152", "MODEL_DESCRIPTION", "MOD.BTC.TRACKER.V1", (), "", False, "Book I catalog MOD.BTC.TRACKER.V1", CANONICAL_PATH),
    PathExpectation("EV-153", "COMPARISON", "MOD.XAU.GAME.V1", ("EV.XAU.SUPPORTED.V1",), "", False, "Book I catalog MOD.XAU.GAME.V1 + EV.XAU.SUPPORTED.V1", CANONICAL_PATH),
    PathExpectation("EV-154", "COMPARISON", "", (), "", True, "No canonical comparison model exists; a plan-level source is correct", PLAN_ONLY_NO_MODEL),
)


def expectations() -> tuple[PathExpectation, ...]:
    return V1_CHAIN_EXPECTATIONS + V2_EXPECTATIONS


def expectation_index() -> dict[str, PathExpectation]:
    return {expectation.case_id: expectation for expectation in expectations()}


def expectation_for(case_id: str) -> PathExpectation:
    try:
        return expectation_index()[case_id]
    except KeyError as exc:  # pragma: no cover - guarded by drivers
        raise KeyError(f"no declared evidence path for {case_id}") from exc


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------


def observe(execution: Any) -> PathObservation:
    """Project one ``EvaluationExecution`` onto the path stages.

    Only attribute access on the stage artifacts is used, so this module keeps
    its import independence while still seeing what the run actually produced.
    """

    artifacts: Mapping[str, Any] = getattr(execution, "artifacts", {}) or {}
    bundle = artifacts.get("bundle")
    package = artifacts.get("package")
    answer = artifacts.get("answer")
    payload = answer.payload() if hasattr(answer, "payload") else {}
    trace = getattr(bundle, "trace", None)
    manifest = getattr(package, "manifest", None)
    claims = tuple(payload.get("claims", ()) or ())
    sections = tuple(getattr(package, "sections", ()) or ())
    section_ids = tuple(
        sorted(
            {
                str(item.source_ref_id)
                for section in sections
                for item in (getattr(section, "items", ()) or ())
                if getattr(item, "source_ref_id", "")
            }
        )
    )
    return PathObservation(
        case_id=str(getattr(execution, "case_id", "")),
        outcome=str(payload.get("outcome") or getattr(execution, "outcome", "")),
        trace_ids=tuple(str(item) for item in (getattr(trace, "selected_ids", ()) or ())),
        trace_claim_ids=tuple(str(item) for item in (getattr(trace, "claim_ids", ()) or ())),
        trace_evidence_ids=tuple(
            str(item) for item in (getattr(trace, "evidence_ids", ()) or ())
        ),
        package_ids=section_ids,
        manifest_ids=tuple(
            str(item) for item in (getattr(manifest, "included_object_ids", ()) or ())
        ),
        manifest_id=str(getattr(manifest, "manifest_digest", "") or ""),
        claim_sources=tuple(
            tuple(str(ref) for ref in (claim.get("source_refs") or ())) for claim in claims
        ),
        claim_generations=tuple(str(claim.get("generation") or "") for claim in claims),
        citations=tuple(
            str(citation.get("source_ref_id") or "")
            for citation in (payload.get("citations", ()) or ())
        ),
    )


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _names_model(ref: str, model: str) -> bool:
    """True when ``ref`` is an object of the expected model, never the plan."""

    if not ref or ref.startswith(PLAN_PREFIX):
        return False
    stem = model[len(MODEL_PREFIX):] if model.startswith(MODEL_PREFIX) else model
    stem = stem.removesuffix(".V1")
    return ref == model or (bool(stem) and stem in ref)


def _all_checks(expectation: PathExpectation, observation: PathObservation) -> list[tuple[str, bool]]:
    package = set(observation.package_ids)
    trace = set(observation.trace_ids)
    citations = set(observation.citations)
    claim_sources = {ref for sources in observation.claim_sources for ref in sources}

    if not expectation.applicable:
        checks: list[tuple[str, bool]] = [
            ("plan_source_cited", any(ref.startswith(PLAN_PREFIX) for ref in citations)),
            (
                "no_unrelated_model_cited",
                all(
                    ref == expectation.canonical_model
                    for ref in citations
                    if ref.startswith(MODEL_PREFIX)
                ),
            ),
            ("answer_reached_validation", observation.outcome == "VALIDATED_ANSWER"),
        ]
        if expectation.reconciliation is CORPUS_ABSENT:
            # The case is blocked on corpus coverage: record it, do not score it.
            checks.append(("corpus_evidence_available", False))
        return checks

    model = expectation.canonical_model
    expected_evidence = set(expectation.evidence_refs)

    checks = [
        ("model_selected_in_trace", model in trace),
        ("model_packaged", model in package),
        ("model_in_manifest", model in set(observation.manifest_ids)),
        ("manifest_identity_recorded", observation.manifest_id.startswith(MANIFEST_PREFIX)),
        ("manifest_matches_package", set(observation.manifest_ids) == package),
        (
            "claim_joins_canonical_evidence",
            bool(claim_sources & expected_evidence)
            or any(_names_model(ref, model) for ref in claim_sources),
        ),
        (
            "claim_cites_only_packaged_items",
            all(ref in package for ref in claim_sources),
        ),
        (
            "citation_supports_expected_source",
            bool(citations & expected_evidence)
            or any(_names_model(ref, model) for ref in citations),
        ),
        (
            "citation_resolves_into_package",
            all(ref in package for ref in citations if ref),
        ),
        (
            "not_plan_only",
            any(not ref.startswith(PLAN_PREFIX) for ref in citations),
        ),
        ("evidence_refs_packaged", expected_evidence <= package),
        (
            "no_unauthorized_package_evidence",
            package <= (trace | {ref for ref in package if ref.startswith(PLAN_PREFIX)}),
        ),
        (
            "trace_records_selection",
            bool(observation.trace_ids) or bool(observation.trace_evidence_ids),
        ),
    ]
    if expectation.generation:
        checks.append(
            ("generation_matches", expectation.generation in observation.claim_generations)
        )
    return checks


def evaluate(
    expectation: PathExpectation,
    observation: PathObservation,
    *,
    scored: bool = True,
) -> PathVerdict:
    """Score one case's path.

    ``scored=False`` records the checks without treating a corpus gap as a
    system failure; callers use it for ``CORPUS_ABSENT`` cases.
    """

    if expectation.case_id != observation.case_id:
        raise ValueError(
            f"expectation for {expectation.case_id} evaluated against {observation.case_id}"
        )
    checks = tuple(_all_checks(expectation, observation))
    failures = tuple(name for name, ok in checks if not ok)
    blocking = failures
    if not scored:
        blocking = tuple(name for name in failures if name != "corpus_evidence_available")
    return PathVerdict(
        case_id=expectation.case_id,
        reconciliation=expectation.reconciliation,
        applicable=expectation.applicable,
        passed=not blocking,
        checks=checks,
        failures=blocking,
    )


def evaluate_all(
    observations: Iterable[PathObservation],
) -> tuple[PathVerdict, ...]:
    by_id = {observation.case_id: observation for observation in observations}
    out: list[PathVerdict] = []
    for expectation in expectations():
        observation = by_id.get(expectation.case_id)
        if observation is None:
            continue
        out.append(
            evaluate(
                expectation,
                observation,
                scored=expectation.reconciliation is not CORPUS_ABSENT,
            )
        )
    return tuple(out)


def independent_import_roots() -> tuple[str, ...]:
    """The only modules this evaluator may import (R7 applied to V2)."""

    return (
        "app.forge.ask_cerebus.evaluation.enums",
        "app.forge.ask_cerebus.evaluation.versions",
        "app.forge.ask_cerebus.evaluation.schema",
    )


def forbidden_import_roots() -> tuple[str, ...]:
    return (
        "app.forge.ask_cerebus.interpreter",
        "app.forge.ask_cerebus.retrieval",
        "app.forge.ask_cerebus.context",
        "app.forge.ask_cerebus.llm_gateway",
        "app.forge.ask_cerebus.answer",
    )


__all__ = [
    "CANONICAL_PATH",
    "CORPUS_ABSENT",
    "DEFINITIONAL_PLAN_SOURCE",
    "EVIDENCE_PATH_EVALUATION_V2",
    "PLAN_ONLY_NO_MODEL",
    "RECONCILIATIONS",
    "PathExpectation",
    "PathObservation",
    "PathVerdict",
    "V1_CHAIN_EXPECTATIONS",
    "V2_EXPECTATIONS",
    "evaluate",
    "evaluate_all",
    "expectation_for",
    "expectation_index",
    "expectations",
    "forbidden_import_roots",
    "independent_import_roots",
    "observe",
]
