"""Report assembly and launch-gate verdicts.

The report is a pure function of the dataset, the executions and the declared
metric rules: no run state leaks into a stored expectation, and the run digest
covers exactly what was executed (R93, R94, R100).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from app.forge.ask_cerebus.evaluation import enums, redteam, review, scoring, versions
from app.forge.ask_cerebus.evaluation.findings import (
    blocking_findings,
    derive_findings,
    severity_counts,
)
from app.forge.ask_cerebus.evaluation.matching import CaseMatch, match_all
from app.forge.ask_cerebus.evaluation.schema import (
    EvaluationDataset,
    EvaluationExecution,
    EvaluationFinding,
    EvaluationManifest,
    EvaluationReport,
    EvaluationScore,
    digest_of,
)

GATE_BG_A = "BG-A"
GATE_BG_B = "BG-B"
GATE_BG_C = "BG-C"

PASS = "PASS"
FAIL = "FAIL"
BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AssembledRun:
    manifest: EvaluationManifest
    report: EvaluationReport
    matches: tuple[CaseMatch, ...]
    findings: tuple[EvaluationFinding, ...]
    attacks: tuple[redteam.AttackResult, ...]
    gate_notes: tuple[tuple[str, str, str], ...]

    def score_index(self) -> dict[str, EvaluationScore]:
        return scoring.score_index(self.report.scores)


def manifest_for(dataset: EvaluationDataset) -> EvaluationManifest:
    return EvaluationManifest(
        contract_version=versions.ASK_EVALUATION_CONTRACT_V1,
        dataset_version=dataset.dataset_version,
        schema_version=versions.CASE_SCHEMA_V1,
        oracle_version=versions.ORACLE_V1,
        scoring_version=versions.SCORING_V1,
        report_version=versions.REPORT_V1,
        dataset_digest=dataset.digest,
        case_count=len(dataset.cases),
        upstream_pins=tuple(sorted(versions.UPSTREAM_PINS.items())),
        migration_versions=versions.MIGRATION_VERSIONS,
    )


def verdicts_for(
    executions: Sequence[EvaluationExecution],
    matches: Sequence[CaseMatch],
    findings: Sequence[EvaluationFinding],
) -> tuple[tuple[str, str], ...]:
    errors = [execution for execution in executions if execution.outcome == "ERROR"]
    bg_a = FAIL if errors else PASS
    bg_b = FAIL if blocking_findings(findings) else PASS
    return (
        (GATE_BG_A, bg_a),
        (GATE_BG_B, bg_b),
        (GATE_BG_C, BLOCKED),
    )


def gate_notes_for(
    executions: Sequence[EvaluationExecution],
    matches: Sequence[CaseMatch],
    findings: Sequence[EvaluationFinding],
    attacks: Sequence[redteam.AttackResult],
) -> tuple[tuple[str, str, str], ...]:
    failed = [match.case_id for match in matches if not match.passed]
    errors = [execution.case_id for execution in executions if execution.outcome == "ERROR"]
    blocking = blocking_findings(findings)
    counts = severity_counts(findings)
    return (
        (
            GATE_BG_A,
            "dataset, oracle and harness execute every case without a stage exception",
            f"{len(executions)} executions, {len(errors)} stage errors, "
            f"{len(matches)} matches, {len(failed)} failing",
        ),
        (
            GATE_BG_B,
            "no S1 finding remains open across the frozen corpus",
            f"{len(blocking)} S1 findings; S1={counts['S1']} S2={counts['S2']} S3={counts['S3']}; "
            f"{len(redteam.exposures(attacks))} exposed attacks",
        ),
        (
            GATE_BG_C,
            "no production threshold is declared and no readiness claim is made",
            "human review agreement is BLOCKED until real review records exist",
        ),
    )


def assemble(
    dataset: EvaluationDataset,
    executions: Sequence[EvaluationExecution],
    *,
    review_records: Sequence[object] = (),
) -> AssembledRun:
    matches = tuple(match_all(dataset.cases, executions))
    attacks = redteam.classify_all(dataset.cases, executions)
    boundary_by_case = {attack.case_id: attack.boundary for attack in attacks}
    findings: list[EvaluationFinding] = []
    for case in dataset.cases:
        match = next((item for item in matches if item.case_id == case.case_id), None)
        execution = next((item for item in executions if item.case_id == case.case_id), None)
        if match is None or execution is None:
            continue
        findings.extend(
            derive_findings(
                case,
                match,
                execution,
                boundary=boundary_by_case.get(case.case_id),
            )
        )
    findings.extend(review.review_findings(review_records))  # type: ignore[arg-type]

    records = scoring.records(dataset.cases, executions, matches)
    scores = scoring.score_dataset(dataset, records, review_records=review_records)  # type: ignore[arg-type]
    scoring.assert_declared_denominators(scores)

    verdicts = verdicts_for(executions, matches, findings)
    run_digest = digest_of(
        {
            "dataset_digest": dataset.digest,
            "executions": [execution.payload() for execution in executions],
            "verdicts": [list(pair) for pair in verdicts],
        }
    )
    report = EvaluationReport(
        report_version=versions.REPORT_V1,
        contract_version=versions.ASK_EVALUATION_CONTRACT_V1,
        dataset_version=dataset.dataset_version,
        dataset_digest=dataset.digest,
        upstream_pins=tuple(sorted(versions.UPSTREAM_PINS.items())),
        executions=tuple(executions),
        findings=tuple(findings),
        scores=tuple(scores),
        verdicts=verdicts,
        blocked_metrics=scoring.blocked_metrics(scores),
        run_digest=run_digest,
    )
    return AssembledRun(
        manifest=manifest_for(dataset),
        report=report,
        matches=matches,
        findings=tuple(findings),
        attacks=attacks,
        gate_notes=gate_notes_for(executions, matches, findings, attacks),
    )


def metric_value(run: AssembledRun, metric: enums.MetricId) -> float | None:
    return run.score_index()[metric.value].value


def verdict_map(run: AssembledRun) -> Mapping[str, str]:
    return dict(run.report.verdicts)


def is_ratifiable(run: AssembledRun) -> bool:
    """BG-A and BG-B must pass; BG-C stays BLOCKED by construction (R100)."""

    verdicts = verdict_map(run)
    return verdicts[GATE_BG_A] == PASS and verdicts[GATE_BG_B] == PASS


def summarise(run: AssembledRun) -> Mapping[str, object]:
    return {
        "dataset_digest": run.report.dataset_digest,
        "run_digest": run.report.run_digest,
        "cases": len(run.report.executions),
        "verdicts": dict(run.report.verdicts),
        "blocked_metrics": list(run.report.blocked_metrics),
        "scores": {
            score.metric_id.value: {
                "value": score.value,
                "numerator": score.numerator,
                "denominator": score.denominator,
                "status": score.status.value,
            }
            for score in run.report.scores
        },
        "severity": severity_counts(run.findings),
        "redteam": redteam.summary(run.attacks),
        "review": review.agreement([]),
    }


def render_markdown(run: AssembledRun) -> str:
    """A compact report body reused by the evidence bundle."""

    lines = [
        "# ASK CEREBUS evaluation run",
        "",
        f"- contract: `{run.report.contract_version}`",
        f"- dataset: `{run.report.dataset_version}` (`{run.report.dataset_digest[:16]}`)",
        f"- run digest: `{run.report.run_digest[:16]}`",
        f"- cases: {len(run.report.executions)}",
        "",
        "## Gates",
        "",
        "| gate | verdict |",
        "| --- | --- |",
    ]
    lines.extend(f"| {gate} | {verdict} |" for gate, verdict in run.report.verdicts)
    lines += ["", "## Metrics", "", "| metric | value | numerator | denominator | status |", "| --- | --- | --- | --- | --- |"]
    for score in run.report.scores:
        value = "n/a" if score.value is None else f"{score.value:.3f}"
        lines.append(
            f"| {score.metric_id.value} | {value} | {score.numerator} | {score.denominator} | {score.status.value} |"
        )
    lines += [
        "",
        "## Red team",
        "",
        f"- attempts: {len(run.attacks)}",
        f"- boundaries: {dict(redteam.boundary_counts(run.attacks))}",
        f"- exposed: {[attack.case_id for attack in redteam.exposures(run.attacks)] or 'none'}",
        "",
        "## Findings",
        "",
        f"- S1: {severity_counts(run.findings)['S1']}",
        f"- S2: {severity_counts(run.findings)['S2']}",
        f"- S3: {severity_counts(run.findings)['S3']}",
        "",
    ]
    return "\n".join(lines)


def write_report(run: AssembledRun) -> tuple[str, str]:
    return (
        __import__("json").dumps(run.manifest.payload(), indent=2, sort_keys=True),
        __import__("json").dumps(run.report.payload(), indent=2, sort_keys=True),
    )
