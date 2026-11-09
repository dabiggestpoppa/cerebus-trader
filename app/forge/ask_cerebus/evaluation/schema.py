"""Immutable evaluation DTOs for Book IV / Bloc IV.6.

The schema depends only on the evaluation's own enums and versions, so the
independent oracle can import it without pulling in the system under test.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Mapping

from app.forge.ask_cerebus.evaluation import enums, versions

_MISSING = object()


def canonical_json(value: Any) -> str:
    """Canonical JSON used by every digest in this bloc (R4)."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_of(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


@dataclass(frozen=True)
class ExpectedEvidencePath:
    """Names the exact fixture record that authorises an expectation (R5)."""

    fixture_path: str
    builder: str
    record: str
    values: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require(bool(self.fixture_path), "evidence path requires a fixture path")
        _require(bool(self.builder), "evidence path requires a builder name")
        _require(bool(self.record), "evidence path requires a record identity")

    def payload(self) -> dict[str, Any]:
        return {
            "fixture_path": self.fixture_path,
            "builder": self.builder,
            "record": self.record,
            "values": [[key, value] for key, value in self.values],
        }


@dataclass(frozen=True)
class ExpectedClaim:
    """A claim that must (or must not) survive into the final answer."""

    token: str
    source_ref: str = ""

    def __post_init__(self) -> None:
        _require(bool(self.token.strip()), "expected claim token must be non-empty")

    def payload(self) -> dict[str, str]:
        return {"token": self.token, "source_ref": self.source_ref}


@dataclass(frozen=True)
class EvaluationCase:
    """The frozen case record (PLAN.md §6.1).

    ``draft_variant`` and ``payload_marker`` are harness bindings: they say
    *how* to build the fixture draft and which literal an injected attack
    carries. They are not expectations and never influence scoring.
    """

    case_id: str
    family: enums.CaseFamily
    kind: enums.CaseKind
    execution_mode: enums.ExecutionMode
    query_text: str
    depth: str
    intent_expected: str
    entities_expected: tuple[str, ...]
    market: str
    model_ids: tuple[str, ...]
    time_scope: enums.TimeScope
    fixture_source: str
    evidence_path: ExpectedEvidencePath
    authority: enums.Authority
    expected_outcome: enums.ExpectedOutcomeKind
    expected_refusal_code: str | None
    expected_finding_class: enums.FindingCode | None
    required_claims: tuple[ExpectedClaim, ...]
    forbidden_claims: tuple[ExpectedClaim, ...]
    forbidden_numbers: tuple[str, ...]
    required_limitations: tuple[str, ...]
    expected_citations: tuple[str, ...]
    expected_eligibility: str | None
    expected_freshness: enums.ExpectedFreshness
    expected_validation_codes: tuple[str, ...]
    required_fields: tuple[str, ...]
    score_population: tuple[enums.MetricId, ...]
    unresolved_owner: enums.AttributionOwner | None
    notes: str
    draft_variant: str = "as_is"
    payload_marker: str = ""

    def __post_init__(self) -> None:
        _require(bool(versions.CASE_ID_PATTERN.match(self.case_id)), f"bad case id: {self.case_id}")
        _require(bool(self.query_text.strip()), f"{self.case_id} has no query text")
        _require(self.depth in versions.DEPTHS, f"{self.case_id} has an unknown depth")
        _require(self.authority in enums.VALID_AUTHORITIES, f"{self.case_id} has a forbidden authority")
        if self.expected_outcome is enums.ExpectedOutcomeKind.REFUSAL:
            _require(
                self.expected_refusal_code in versions.REFUSAL_CODES,
                f"{self.case_id} refusal must name one of the six frozen codes",
            )
        else:
            _require(
                self.expected_refusal_code is None,
                f"{self.case_id} is an answer and cannot name a refusal code",
            )
        _require(
            all(isinstance(metric, enums.MetricId) for metric in self.score_population),
            f"{self.case_id} score population must be metric ids",
        )
        _require(
            self.expected_freshness is enums.ExpectedFreshness.NOT_REQUIRED
            or self.time_scope is enums.TimeScope.CURRENT
            or self.expected_freshness is enums.ExpectedFreshness.REFUSAL,
            f"{self.case_id} declares freshness for a non-current case",
        )

    @property
    def number(self) -> int:
        match = versions.CASE_ID_PATTERN.match(self.case_id)
        assert match is not None
        return int(match.group(1))

    @property
    def is_positive(self) -> bool:
        return self.expected_outcome is enums.ExpectedOutcomeKind.ANSWER

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "family": self.family.value,
            "kind": self.kind.value,
            "execution_mode": self.execution_mode.value,
            "query_text": self.query_text,
            "depth": self.depth,
            "intent_expected": self.intent_expected,
            "entities_expected": list(self.entities_expected),
            "market": self.market,
            "model_ids": list(self.model_ids),
            "time_scope": self.time_scope.value,
            "fixture_source": self.fixture_source,
            "evidence_path": self.evidence_path.payload(),
            "authority": self.authority.value,
            "expected_outcome": self.expected_outcome.value,
            "expected_refusal_code": self.expected_refusal_code,
            "expected_finding_class": (
                self.expected_finding_class.value if self.expected_finding_class else None
            ),
            "required_claims": [claim.payload() for claim in self.required_claims],
            "forbidden_claims": [claim.payload() for claim in self.forbidden_claims],
            "forbidden_numbers": list(self.forbidden_numbers),
            "required_limitations": list(self.required_limitations),
            "expected_citations": list(self.expected_citations),
            "expected_eligibility": self.expected_eligibility,
            "expected_freshness": self.expected_freshness.value,
            "expected_validation_codes": list(self.expected_validation_codes),
            "required_fields": list(self.required_fields),
            "score_population": [metric.value for metric in self.score_population],
            "unresolved_owner": self.unresolved_owner.value if self.unresolved_owner else None,
            "notes": self.notes,
            "draft_variant": self.draft_variant,
            "payload_marker": self.payload_marker,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "EvaluationCase":
        _require(
            isinstance(payload, Mapping),
            "a case payload must be a mapping",
        )
        missing = [name for name in _CASE_FIELDS if name not in payload]
        _require(not missing, f"case payload missing mandatory fields: {missing}")
        evidence = payload["evidence_path"]
        _require(isinstance(evidence, Mapping), "evidence_path must be a mapping")
        return cls(
            case_id=payload["case_id"],
            family=enums.CaseFamily(payload["family"]),
            kind=enums.CaseKind(payload["kind"]),
            execution_mode=enums.ExecutionMode(payload["execution_mode"]),
            query_text=payload["query_text"],
            depth=payload["depth"],
            intent_expected=payload["intent_expected"],
            entities_expected=tuple(payload["entities_expected"]),
            market=payload["market"],
            model_ids=tuple(payload["model_ids"]),
            time_scope=enums.TimeScope(payload["time_scope"]),
            fixture_source=payload["fixture_source"],
            evidence_path=ExpectedEvidencePath(
                fixture_path=evidence["fixture_path"],
                builder=evidence["builder"],
                record=evidence["record"],
                values=tuple(tuple(pair) for pair in evidence.get("values", ())),
            ),
            authority=enums.Authority(payload["authority"]),
            expected_outcome=enums.ExpectedOutcomeKind(payload["expected_outcome"]),
            expected_refusal_code=payload["expected_refusal_code"],
            expected_finding_class=(
                enums.FindingCode(payload["expected_finding_class"])
                if payload["expected_finding_class"]
                else None
            ),
            required_claims=tuple(
                ExpectedClaim(claim["token"], claim["source_ref"])
                for claim in payload["required_claims"]
            ),
            forbidden_claims=tuple(
                ExpectedClaim(claim["token"], claim["source_ref"])
                for claim in payload["forbidden_claims"]
            ),
            forbidden_numbers=tuple(payload["forbidden_numbers"]),
            required_limitations=tuple(payload["required_limitations"]),
            expected_citations=tuple(payload["expected_citations"]),
            expected_eligibility=payload["expected_eligibility"],
            expected_freshness=enums.ExpectedFreshness(payload["expected_freshness"]),
            expected_validation_codes=tuple(payload["expected_validation_codes"]),
            required_fields=tuple(payload["required_fields"]),
            score_population=tuple(enums.MetricId(metric) for metric in payload["score_population"]),
            unresolved_owner=(
                enums.AttributionOwner(payload["unresolved_owner"])
                if payload["unresolved_owner"]
                else None
            ),
            notes=payload["notes"],
            draft_variant=payload.get("draft_variant", "as_is"),
            payload_marker=payload.get("payload_marker", ""),
        )


_CASE_FIELDS = (
    "case_id",
    "family",
    "kind",
    "execution_mode",
    "query_text",
    "depth",
    "intent_expected",
    "entities_expected",
    "market",
    "model_ids",
    "time_scope",
    "fixture_source",
    "evidence_path",
    "authority",
    "expected_outcome",
    "expected_refusal_code",
    "expected_finding_class",
    "required_claims",
    "forbidden_claims",
    "forbidden_numbers",
    "required_limitations",
    "expected_citations",
    "expected_eligibility",
    "expected_freshness",
    "expected_validation_codes",
    "required_fields",
    "score_population",
    "unresolved_owner",
    "notes",
)


@dataclass(frozen=True)
class EvaluationDataset:
    """Ordered case array plus derived integrity metadata (R3, R4)."""

    dataset_version: str
    schema_version: str
    cases: tuple[EvaluationCase, ...]
    digest: str
    band_counts: tuple[tuple[str, int], ...]
    authorities_used: tuple[str, ...]
    forbidden_authorities_absent: bool
    balance_report: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        _require(bool(self.cases), "evaluation dataset is empty")
        _require(bool(self.digest), "evaluation dataset requires a digest")

    def payload(self) -> dict[str, Any]:
        return {
            "dataset_version": self.dataset_version,
            "schema_version": self.schema_version,
            "digest": self.digest,
            "band_counts": [[name, count] for name, count in self.band_counts],
            "authorities_used": list(self.authorities_used),
            "forbidden_authorities_absent": self.forbidden_authorities_absent,
            "balance_report": [[name, count] for name, count in self.balance_report],
            "cases": [case.payload() for case in self.cases],
        }

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(case.case_id for case in self.cases)

    def case(self, case_id: str) -> EvaluationCase:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise KeyError(case_id)

    def subset(self, case_ids: Iterable[str]) -> "EvaluationDataset":
        wanted = set(case_ids)
        return dataset_from_cases(
            tuple(case for case in self.cases if case.case_id in wanted),
            dataset_version=self.dataset_version,
            schema_version=self.schema_version,
        )

    @classmethod
    def build(
        cls,
        cases: Iterable[EvaluationCase],
        *,
        dataset_version: str = versions.EVALUATION_DATASET_V1,
        schema_version: str = versions.CASE_SCHEMA_V1,
    ) -> "EvaluationDataset":
        return dataset_from_cases(
            tuple(cases), dataset_version=dataset_version, schema_version=schema_version
        )


@dataclass(frozen=True)
class EvaluationExecution:
    """One case, one execution, with every stage identity (R13)."""

    case_id: str
    mode: str
    plan_digest: str
    bundle_digest: str
    trace_digest: str
    package_id: str
    manifest_id: str
    draft_digest: str
    answer_id: str
    outcome: str
    validation_codes: tuple[str, ...]
    refusal_code: str | None
    latency_ms: float
    artifacts: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        _require(bool(self.case_id), "execution requires a case id")
        _require(self.mode in (enums.ExecutionMode.CHAIN.value, enums.ExecutionMode.SEALED.value),
                 "execution mode must be CHAIN or SEALED")
        _require(
            self.outcome in ("VALIDATED_ANSWER", "GOVERNED_REFUSAL", "ERROR"),
            f"unknown execution outcome: {self.outcome}",
        )

    def payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "mode": self.mode,
            "plan_digest": self.plan_digest,
            "bundle_digest": self.bundle_digest,
            "trace_digest": self.trace_digest,
            "package_id": self.package_id,
            "manifest_id": self.manifest_id,
            "draft_digest": self.draft_digest,
            "answer_id": self.answer_id,
            "outcome": self.outcome,
            "validation_codes": list(self.validation_codes),
            "refusal_code": self.refusal_code,
            "latency_ms": self.latency_ms,
        }

    def answer_payload(self) -> Mapping[str, Any]:
        answer = self.artifacts.get("answer")
        return answer.payload() if hasattr(answer, "payload") else {}

    def answer_text(self) -> str:
        return canonical_json(self.answer_payload())


@dataclass(frozen=True)
class EvaluationFinding:
    finding_id: str
    case_id: str
    severity: enums.FindingSeverity
    code: str
    owner: enums.AttributionOwner
    detail: str
    evidence_refs: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "case_id": self.case_id,
            "severity": self.severity.value,
            "code": self.code,
            "owner": self.owner.value,
            "detail": self.detail,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class EvaluationScore:
    metric_id: enums.MetricId
    numerator: int
    denominator: int
    eligible_case_ids: tuple[str, ...]
    value: float | None
    status: enums.ScoreStatus
    notes: str = ""

    def __post_init__(self) -> None:
        _require(self.numerator >= 0, "numerator cannot be negative")
        _require(self.denominator >= 0, "denominator cannot be negative")
        _require(self.numerator <= self.denominator, "numerator cannot exceed its denominator")
        _require(
            (self.status is enums.ScoreStatus.MEASURED) == (self.denominator > 0),
            "a measured score requires a positive denominator and vice versa",
        )
        if self.status is enums.ScoreStatus.MEASURED:
            _require(self.value is not None, "measured score requires a value")
        else:
            _require(self.value is None, "non-measured score cannot carry a value")

    def payload(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id.value,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "eligible_case_ids": list(self.eligible_case_ids),
            "value": self.value,
            "status": self.status.value,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class EvaluationManifest:
    contract_version: str
    dataset_version: str
    schema_version: str
    oracle_version: str
    scoring_version: str
    report_version: str
    dataset_digest: str
    case_count: int
    upstream_pins: tuple[tuple[str, str], ...]
    migration_versions: tuple[int, ...]

    def payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "dataset_version": self.dataset_version,
            "schema_version": self.schema_version,
            "oracle_version": self.oracle_version,
            "scoring_version": self.scoring_version,
            "report_version": self.report_version,
            "dataset_digest": self.dataset_digest,
            "case_count": self.case_count,
            "upstream_pins": [[path, blob] for path, blob in self.upstream_pins],
            "migration_versions": list(self.migration_versions),
        }


@dataclass(frozen=True)
class EvaluationReport:
    report_version: str
    contract_version: str
    dataset_version: str
    dataset_digest: str
    upstream_pins: tuple[tuple[str, str], ...]
    executions: tuple[EvaluationExecution, ...]
    findings: tuple[EvaluationFinding, ...]
    scores: tuple[EvaluationScore, ...]
    verdicts: tuple[tuple[str, str], ...]
    blocked_metrics: tuple[str, ...]
    run_digest: str

    def payload(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "contract_version": self.contract_version,
            "dataset_version": self.dataset_version,
            "dataset_digest": self.dataset_digest,
            "upstream_pins": [[path, blob] for path, blob in self.upstream_pins],
            "executions": [execution.payload() for execution in self.executions],
            "findings": [finding.payload() for finding in self.findings],
            "scores": [score.payload() for score in self.scores],
            "verdicts": [[gate, verdict] for gate, verdict in self.verdicts],
            "blocked_metrics": list(self.blocked_metrics),
            "run_digest": self.run_digest,
        }

    def score(self, metric_id: enums.MetricId) -> EvaluationScore:
        for score in self.scores:
            if score.metric_id is metric_id:
                return score
        raise KeyError(metric_id)

    def verdict(self, gate: str) -> str:
        for name, verdict in self.verdicts:
            if name == gate:
                return verdict
        raise KeyError(gate)


@dataclass(frozen=True)
class HumanReviewRecord:
    """Every field of PLAN.md §6.7 (R99)."""

    review_id: str
    case_id: str
    reviewer_role: str
    expected_answerability: str
    actual_answer_excerpt: str
    evidence_path: str
    numerical_correctness: str
    citation_support: str
    status_layer_setup_correctness: str
    unsafe_omissions: tuple[str, ...]
    verdict: enums.ReviewVerdict
    notes: str
    disagreement_disposition: enums.DisagreementDisposition
    proposed_corpus_correction: str
    review_version: str
    reviewed_at: str

    def __post_init__(self) -> None:
        for name in (
            "review_id",
            "case_id",
            "reviewer_role",
            "expected_answerability",
            "evidence_path",
            "numerical_correctness",
            "citation_support",
            "status_layer_setup_correctness",
            "review_version",
            "reviewed_at",
        ):
            _require(bool(str(getattr(self, name)).strip()), f"review record missing {name}")
        _require(
            bool(self.actual_answer_excerpt.strip()),
            "review record must quote what was actually answered",
        )
        if self.verdict is enums.ReviewVerdict.DISAGREE_SYSTEM:
            _require(
                self.disagreement_disposition is enums.DisagreementDisposition.OPEN_FINDING,
                "DISAGREE_SYSTEM must open a finding",
            )
        if self.verdict is enums.ReviewVerdict.DISAGREE_EXPECTATION:
            _require(
                self.disagreement_disposition
                is enums.DisagreementDisposition.DATASET_CHANGE_PROPOSAL,
                "DISAGREE_EXPECTATION must route to a dataset-change proposal",
            )
            _require(
                bool(self.proposed_corpus_correction.strip()),
                "a dataset-change proposal must describe the correction",
            )
        if self.verdict is enums.ReviewVerdict.AGREE:
            _require(
                self.disagreement_disposition is enums.DisagreementDisposition.NONE,
                "AGREE cannot carry a disagreement disposition",
            )

    def payload(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "case_id": self.case_id,
            "reviewer_role": self.reviewer_role,
            "expected_answerability": self.expected_answerability,
            "actual_answer_excerpt": self.actual_answer_excerpt,
            "evidence_path": self.evidence_path,
            "numerical_correctness": self.numerical_correctness,
            "citation_support": self.citation_support,
            "status_layer_setup_correctness": self.status_layer_setup_correctness,
            "unsafe_omissions": list(self.unsafe_omissions),
            "verdict": self.verdict.value,
            "notes": self.notes,
            "disagreement_disposition": self.disagreement_disposition.value,
            "proposed_corpus_correction": self.proposed_corpus_correction,
            "review_version": self.review_version,
            "reviewed_at": self.reviewed_at,
        }

    def routed_finding(self, owner: enums.AttributionOwner) -> EvaluationFinding | None:
        """DISAGREE_SYSTEM opens a finding; other verdicts do not (R100)."""

        if self.verdict is not enums.ReviewVerdict.DISAGREE_SYSTEM:
            return None
        return EvaluationFinding(
            finding_id=f"F-REV-{self.review_id}",
            case_id=self.case_id,
            severity=enums.FindingSeverity.S2,
            code=enums.FindingCode.FALSE_REFUSAL.value,
            owner=owner,
            detail=f"human review disagreed with the system: {self.notes}",
            evidence_refs=(self.evidence_path,),
        )

    def dataset_proposal(self) -> str:
        """DISAGREE_EXPECTATION yields a proposal, never an edit (R100, R94)."""

        if self.verdict is not enums.ReviewVerdict.DISAGREE_EXPECTATION:
            return ""
        return canonical_json(
            {
                "case_id": self.case_id,
                "proposal": self.proposed_corpus_correction,
                "review_id": self.review_id,
                "requires_review": True,
            }
        )


def dataset_from_cases(
    cases: tuple[EvaluationCase, ...],
    *,
    dataset_version: str = versions.EVALUATION_DATASET_V1,
    schema_version: str = versions.CASE_SCHEMA_V1,
) -> EvaluationDataset:
    """Validate, then derive counts and the canonical digest."""

    if dataset_version not in versions.SUPPORTED_DATASET_VERSIONS:
        raise ValueError(f"unknown evaluation dataset version: {dataset_version}")
    if schema_version not in versions.SUPPORTED_CASE_SCHEMA_VERSIONS:
        raise ValueError(f"unknown evaluation case-schema version: {schema_version}")
    if len(cases) != versions.CASE_COUNT:
        raise ValueError(f"dataset must carry {versions.CASE_COUNT} cases, found {len(cases)}")

    seen: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            raise ValueError(f"duplicate case id: {case.case_id}")
        seen.add(case.case_id)
    numbers = sorted(case.number for case in cases)
    if numbers != list(range(1, versions.CASE_COUNT + 1)):
        raise ValueError("case ids must be contiguous EV-001..EV-120")

    band_counts: dict[str, int] = {family.value: 0 for family in enums.CaseFamily}
    for case in cases:
        band_counts[case.family.value] += 1
    balance: dict[str, int] = {kind.value: 0 for kind in enums.CaseKind}
    for case in cases:
        balance[case.kind.value] += 1
    balance["POSITIVE"] = sum(1 for case in cases if case.is_positive)
    balance["REFUSAL"] = sum(1 for case in cases if not case.is_positive)

    authorities = sorted({case.authority.value for case in cases})
    forbidden_absent = not any(
        case.authority in enums.FORBIDDEN_AUTHORITIES for case in cases
    )
    return EvaluationDataset(
        dataset_version=dataset_version,
        schema_version=schema_version,
        cases=cases,
        digest=dataset_digest(cases),
        band_counts=tuple(sorted(band_counts.items())),
        authorities_used=tuple(authorities),
        forbidden_authorities_absent=forbidden_absent,
        balance_report=tuple(sorted(balance.items())),
    )


def dataset_digest(cases: Iterable[EvaluationCase]) -> str:
    """SHA-256 over the canonical case array (R4, R93)."""

    return digest_of([case.payload() for case in cases])
