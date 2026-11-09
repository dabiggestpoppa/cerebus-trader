"""Dataset load, validation, canonicalisation and digest accounting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.forge.ask_cerebus.evaluation import enums, versions
from app.forge.ask_cerebus.evaluation.schema import (
    EvaluationCase,
    EvaluationDataset,
    canonical_json,
    dataset_digest,
    dataset_from_cases,
)


#: R12 is a chapter rule, not a band rule: a golden corpus band is either a
#: positive battery or a trap battery, while every chapter area must show both
#: outcomes. Areas group the eighteen bands accordingly.
AREA_BY_FAMILY: dict[enums.CaseFamily, str] = {
    enums.CaseFamily.POSITIVE_CONTROL: "EXPLANATION",
    enums.CaseFamily.FALSE_REFUSAL_CONTROL: "EXPLANATION",
    enums.CaseFamily.BEGINNER: "EXPLANATION",
    enums.CaseFamily.OPERATOR: "EXPLANATION",
    enums.CaseFamily.RESEARCHER: "EXPLANATION",
    enums.CaseFamily.UNSUPPORTED_STAT: "VALIDITY",
    enums.CaseFamily.METRIC_LAUNDERING: "VALIDITY",
    enums.CaseFamily.LAYER_LAUNDERING: "VALIDITY",
    enums.CaseFamily.GENERATION_CONFLICT: "VALIDITY",
    enums.CaseFamily.SETUP_ELIGIBILITY: "VALIDITY",
    enums.CaseFamily.FRESHNESS: "VALIDITY",
    enums.CaseFamily.PROVIDER_FAILURE: "VALIDITY",
    enums.CaseFamily.REFUSAL_PRECEDENCE: "VALIDITY",
    enums.CaseFamily.INJECTION: "SECURITY",
    enums.CaseFamily.ENTITLEMENT: "SECURITY",
    enums.CaseFamily.EXTRACTION: "SECURITY",
    enums.CaseFamily.REPLAY: "OPERATIONS",
    enums.CaseFamily.HUMAN_REVIEW: "OPERATIONS",
}


def area_of(case: EvaluationCase) -> str:
    return AREA_BY_FAMILY[case.family]


class DatasetVersionError(ValueError):
    """An unknown dataset or case-schema version refuses the run (R15)."""


def band_of(case: EvaluationCase) -> enums.CaseFamily:
    match = versions.CASE_ID_PATTERN.match(case.case_id)
    if match is None:
        raise ValueError(f"bad case id: {case.case_id}")
    number = int(match.group(1))
    for family, (start, end) in enums.BAND_RANGES.items():
        if start <= number <= end:
            return family
    raise ValueError(f"case {case.case_id} falls outside every band")


def validate_case(case: EvaluationCase) -> tuple[str, ...]:
    """Return a tuple of problems; empty means the case is well formed."""

    problems: list[str] = []
    if not versions.CASE_ID_PATTERN.match(case.case_id):
        problems.append(f"{case.case_id}: id does not match EV-\\d{{3}}")
    if band_of(case) is not case.family:
        problems.append(f"{case.case_id}: family {case.family.value} does not own its band")
    if case.authority in enums.FORBIDDEN_AUTHORITIES:
        problems.append(f"{case.case_id}: forbidden authority {case.authority.value}")
    if case.depth not in versions.DEPTHS:
        problems.append(f"{case.case_id}: unknown depth {case.depth}")
    if case.expected_eligibility and case.expected_eligibility not in versions.ELIGIBILITY_VALUES:
        problems.append(f"{case.case_id}: unknown eligibility {case.expected_eligibility}")
    if case.expected_outcome is enums.ExpectedOutcomeKind.REFUSAL:
        if case.expected_refusal_code not in versions.REFUSAL_CODES:
            problems.append(f"{case.case_id}: refusal without a frozen code")
    elif case.expected_refusal_code is not None:
        problems.append(f"{case.case_id}: answer cannot carry a refusal code")
    if case.time_scope is enums.TimeScope.CURRENT and case.expected_freshness is enums.ExpectedFreshness.NOT_REQUIRED:
        if case.expected_outcome is enums.ExpectedOutcomeKind.ANSWER:
            problems.append(f"{case.case_id}: current answer must declare a freshness treatment")
    if not case.evidence_path.fixture_path:
        problems.append(f"{case.case_id}: no evidence path")
    for token in case.forbidden_numbers:
        if token in case.required_claims:
            problems.append(f"{case.case_id}: token {token} is both required and forbidden")
    return tuple(problems)


def validate_dataset(dataset: EvaluationDataset) -> tuple[str, ...]:
    problems: list[str] = []
    if dataset.dataset_version not in versions.SUPPORTED_DATASET_VERSIONS:
        problems.append(f"unknown dataset version {dataset.dataset_version}")
    if dataset.schema_version not in versions.SUPPORTED_CASE_SCHEMA_VERSIONS:
        problems.append(f"unknown case-schema version {dataset.schema_version}")
    if len(dataset.cases) != versions.CASE_COUNT:
        problems.append(f"dataset must carry {versions.CASE_COUNT} cases")
    for case in dataset.cases:
        problems.extend(validate_case(case))
    recomputed = dataset_digest(dataset.cases)
    if recomputed != dataset.digest:
        problems.append("dataset digest does not match its case array")
    for family in enums.CaseFamily:
        if not any(case.family is family for case in dataset.cases):
            problems.append(f"band {family.value} is empty")
    for area in sorted(set(AREA_BY_FAMILY.values())):
        owned = [case for case in dataset.cases if area_of(case) == area]
        if not any(case.is_positive for case in owned):
            problems.append(f"area {area} has no positive case")
        if not any(not case.is_positive for case in owned):
            problems.append(f"area {area} has no negative case")
    return tuple(problems)


def build_dataset(directory: Path | str) -> EvaluationDataset:
    """Load every ``EV-*.json`` in a directory into a validated dataset."""

    root = Path(directory)
    manifest_path = root / "DATASET_MANIFEST.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing dataset manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_version = manifest.get("dataset_version", "")
    schema_version = manifest.get("schema_version", "")
    if dataset_version not in versions.SUPPORTED_DATASET_VERSIONS:
        raise DatasetVersionError(f"unknown evaluation dataset version: {dataset_version}")
    if schema_version not in versions.SUPPORTED_CASE_SCHEMA_VERSIONS:
        raise DatasetVersionError(f"unknown evaluation case-schema version: {schema_version}")

    cases: list[EvaluationCase] = []
    paths = sorted(root.glob("EV-*.json"))
    if not paths:
        raise FileNotFoundError(f"no case files in {root}")
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases.append(EvaluationCase.from_payload(payload))

    dataset = dataset_from_cases(
        tuple(cases), dataset_version=dataset_version, schema_version=schema_version
    )
    expected_digest = manifest.get("digest", "")
    if expected_digest and expected_digest != dataset.digest:
        raise ValueError("dataset digest does not match the manifest")
    problems = validate_dataset(dataset)
    if problems:
        raise ValueError("invalid evaluation dataset: " + "; ".join(problems))
    return dataset


def write_dataset(dataset: EvaluationDataset, directory: Path | str) -> tuple[Path, ...]:
    """Write canonical case JSON and the manifest; never writes expectations."""

    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for case in sorted(dataset.cases, key=lambda item: item.case_id):
        path = root / f"{case.case_id}.json"
        path.write_text(
            json.dumps(case.payload(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    manifest = {
        "dataset_version": dataset.dataset_version,
        "schema_version": dataset.schema_version,
        "digest": dataset.digest,
        "case_count": len(dataset.cases),
        "band_counts": [[name, count] for name, count in dataset.band_counts],
        "authorities_used": list(dataset.authorities_used),
        "forbidden_authorities_absent": dataset.forbidden_authorities_absent,
        "balance_report": [[name, count] for name, count in dataset.balance_report],
    }
    manifest_path = root / "DATASET_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    written.append(manifest_path)
    return tuple(written)


def cases_by_family(dataset: EvaluationDataset) -> Mapping[enums.CaseFamily, tuple[EvaluationCase, ...]]:
    grouped: dict[enums.CaseFamily, list[EvaluationCase]] = {family: [] for family in enums.CaseFamily}
    for case in dataset.cases:
        grouped[case.family].append(case)
    return {family: tuple(items) for family, items in grouped.items()}


def ids_for_population(dataset: EvaluationDataset, metric: enums.MetricId) -> tuple[str, ...]:
    return tuple(case.case_id for case in dataset.cases if metric in case.score_population)


def subset_for(dataset: EvaluationDataset, case_ids: Iterable[str]) -> EvaluationDataset:
    return dataset.subset(case_ids)


def summary(dataset: EvaluationDataset) -> str:
    return canonical_json(
        {
            "dataset_version": dataset.dataset_version,
            "digest": dataset.digest,
            "bands": dict(dataset.band_counts),
            "balance": dict(dataset.balance_report),
        }
    )
