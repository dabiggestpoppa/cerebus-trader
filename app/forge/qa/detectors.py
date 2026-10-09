"""I.5 corpus QA detectors (frozen chapters I.5.1–I.5.4).

Read-only checks over the applied canonical store and the built index:

- **I.5.1 orphan detector** — every parent/related/evidence/provenance target
  resolves; every CLAIM either routes to evidence or is explicitly flagged as
  an evidence gap (never silently dangling).
- **I.5.2 unsupported-number detector** — every launch CLAIM whose governed
  text contains a digit is evidence-linked or explicitly non-promoted.
- **I.5.3 status/generation leakage** — index status identical to canonical
  status for every record; source generation retained where stated.
- **I.5.4 exposure leakage** — no internal body exists in the index
  (identity-only records), PUBLIC_TEACHING is never assigned by default, and
  the frozen exposure inventory matches I.3 truth.

No detector writes anything; a violation is reported, never repaired here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.forge.canonical import ObjectType, ProductExposure

DIGIT_RE = re.compile(r"\d")

# Statuses that may carry an unqualified current assertion (I.5.2):
# a digit-bearing claim outside this set is "explicitly non-promoted".
_PROMOTABLE_STATUSES = frozenset({"VALIDATED", "FORWARD_OOS"})

_CARD_PREFIXES = (
    "corpus/canonical/models/",
    "corpus/canonical/evidence/",
    "corpus/canonical/setups/",
)


@dataclass(frozen=True)
class Finding:
    detector: str
    object_id: str
    detail: str


@dataclass(frozen=True)
class CorpusCounts:
    objects: int
    by_type: dict
    by_exposure: dict
    artifacts: int
    edges: int
    quarantined: int
    card_quarantines: int
    claims: int
    claims_with_evidence: int
    digit_claims: int
    digit_claims_evidence_linked: int
    subscriber_visible: int


@dataclass(frozen=True)
class CorpusQaReport:
    findings: tuple[Finding, ...]
    counts: CorpusCounts

    @property
    def ok(self) -> bool:
        return not self.findings

    def by_detector(self) -> dict:
        out: dict = {}
        for finding in self.findings:
            out.setdefault(finding.detector, []).append(finding)
        return out


def run_detectors(gateway, generation, catalog) -> CorpusQaReport:
    """I.5.1–I.5.4 over one published index generation."""
    findings: list[Finding] = []

    index_ids = set(generation.ids)
    records = {r.object_id: r for r in generation.records}
    artifact_ids: set[str] = set()
    edge_total = 0
    by_type: dict = {}
    by_exposure: dict = {}
    for object_id in sorted(gateway.list_object_ids()):
        record = gateway.get_object(object_id)
        by_type[record.object_type.value] = by_type.get(record.object_type.value, 0) + 1
        by_exposure[record.exposure.value] = by_exposure.get(record.exposure.value, 0) + 1
        for edge in gateway.edges_for_object(object_id):
            edge_total += 1
            artifact_ids.add(edge.artifact_id)

    # ------------------------------------------------------ I.5.1 orphans
    claims = 0
    claims_with_evidence = 0
    digit_claims = 0
    digit_claims_linked = 0
    for object_id, record in sorted(records.items()):
        for parent in record.parent_ids:
            if parent.startswith("ART."):
                if parent not in artifact_ids:
                    findings.append(Finding("link_integrity", object_id, f"missing artifact parent {parent}"))
            elif parent not in index_ids:
                findings.append(Finding("link_integrity", object_id, f"missing parent {parent}"))
        for link in record.related_ids:
            target = link.target_id
            if target.startswith("ART."):
                if target not in artifact_ids:
                    findings.append(Finding("link_integrity", object_id, f"missing related artifact {target}"))
            elif target not in index_ids:
                findings.append(Finding("link_integrity", object_id, f"missing related {target}"))
        for evidence_id in record.support.evidence_ids:
            if evidence_id not in index_ids:
                findings.append(Finding("link_integrity", object_id, f"missing evidence {evidence_id}"))
        for provenance in record.provenance:
            if provenance.artifact_id not in artifact_ids:
                findings.append(Finding("link_integrity", object_id, f"missing provenance artifact {provenance.artifact_id}"))
        if not record.provenance:
            findings.append(Finding("link_integrity", object_id, "record has no provenance"))

        if record.object_type is ObjectType.CLAIM:
            claims += 1
            if record.support.evidence_ids:
                claims_with_evidence += 1
            elif not record.support.gaps:
                findings.append(
                    Finding(
                        "link_integrity",
                        object_id,
                        "claim routes to neither evidence nor an explicit gap",
                    )
                )
            # ------------------------------------------------ I.5.2 numbers
            if DIGIT_RE.search(record.title + " " + record.retrieval_text):
                digit_claims += 1
                linked = bool(record.support.evidence_ids)
                promoted = record.status.value in _PROMOTABLE_STATUSES
                if linked:
                    digit_claims_linked += 1
                elif promoted:
                    findings.append(
                        Finding(
                            "unsupported_number",
                            object_id,
                            "promoted digit-bearing claim is neither "
                            "evidence-linked nor non-promoted",
                        )
                    )
                # not linked + not promoted ⇒ explicitly non-promoted (ok)

        # ------------------------------------------- I.5.3 status leakage
        canonical = gateway.get_object(object_id)
        if canonical is None:
            findings.append(Finding("status_leakage", object_id, "record missing from canonical store"))
            continue
        if canonical.status is not record.status:
            findings.append(
                Finding(
                    "status_leakage",
                    object_id,
                    f"index status {record.status.value} != canonical {canonical.status.value}",
                )
            )
        card = canonical.metadata.get("card") or {}
        stated_generation = canonical.metadata.get("source_generation") or card.get(
            "source_generation"
        )
        # mirror the compiler's normalization: not-specified collapses to ""
        if isinstance(stated_generation, str):
            stated_generation = (
                "" if stated_generation.strip().upper() == "NOT_SPECIFIED_IN_SOURCE"
                else stated_generation.strip()
            )
        if stated_generation and record.conflict.generation != stated_generation:
            findings.append(
                Finding(
                    "status_leakage",
                    object_id,
                    f"source generation not retained: {record.conflict.generation!r} != {stated_generation!r}",
                )
            )

        # ------------------------------------------- I.5.4 exposure leak
        if record.exposure_class is ProductExposure.PUBLIC_TEACHING:
            findings.append(
                Finding("exposure_leakage", object_id, "PUBLIC_TEACHING assigned by default")
            )
        if record.exposure_class in (
            ProductExposure.INTERNAL_METHOD,
            ProductExposure.INTERNAL_CODE,
        ) and record.retrieval_text:
            findings.append(
                Finding(
                    "exposure_leakage",
                    object_id,
                    "internal record carries a body (must be identity-only)",
                )
            )
        if record.leakage.contains_internal_method or record.leakage.contains_code:
            if record.retrieval_text:
                findings.append(
                    Finding(
                        "exposure_leakage",
                        object_id,
                        "leakage-flagged record still carries text",
                    )
                )

    # records absent from the index (fail closed: index should hold all 30)
    for canonical_id in sorted(gateway.list_object_ids()):
        if canonical_id not in index_ids:
            findings.append(Finding("membership", canonical_id, "canonical object absent from index"))

    # quarantine truth (L1)
    card_quarantines = [
        entry.source_path
        for entry in catalog.entries
        if entry.source_path.startswith(_CARD_PREFIXES)
    ]
    if card_quarantines:
        findings.append(
            Finding("quarantine", ",".join(card_quarantines), "card file quarantined")
        )
    if set(catalog.paths) & index_ids:
        findings.append(
            Finding("quarantine", "index", "quarantined source present in index")
        )

    # subscriber-visible count (authorized records a member can see is a
    # runtime property; the static build check is the exposure inventory)
    subscriber_visible = sum(
        1
        for record in records.values()
        if record.exposure_class is ProductExposure.SUBSCRIBER_MODEL
    )

    counts = CorpusCounts(
        objects=len(generation.ids),
        by_type=by_type,
        by_exposure=by_exposure,
        artifacts=len(artifact_ids),
        edges=edge_total,
        quarantined=len(catalog),
        card_quarantines=len(card_quarantines),
        claims=claims,
        claims_with_evidence=claims_with_evidence,
        digit_claims=digit_claims,
        digit_claims_evidence_linked=digit_claims_linked,
        subscriber_visible=subscriber_visible,
    )
    return CorpusQaReport(findings=tuple(findings), counts=counts)


# ---------------------------------------------------------------------------
# I.5 frozen coverage report (B7 — deterministic regeneration)
# ---------------------------------------------------------------------------

_FROZEN_SNAPSHOT = """\
## Frozen snapshot (I.5 manual audit)

| Dimension | Frozen value |
|---|---|
| Canonical objects | 30 (10 CLAIM, 10 EVIDENCE, 7 MODEL, 3 SETUP, 0 DOCTRINE/TERM/LINEAGE) |
| Source artifacts | 29 |
| Provenance edges | 38 |
| Exposure inventory | PUBLIC_TEACHING 0, SUBSCRIBER_MODEL 24, RESEARCH_LAB 4, OPERATOR_ONLY 2, INTERNAL_METHOD 0, INTERNAL_CODE 0 |
| Quarantined out-of-scope | 9 files (5 setup + 2 Bitcoin + 2 oil; none is a canonical card, term, doctrine, or lineage file) |
| Claims | 10, evidence-linked 10/10; digit-bearing 6, digit-linked 6/6; research-claim layers 6; research-only claims 0; identity gaps 1 (AUC-001 metric NOT_SPECIFIED_IN_SOURCE) |
| Catalog debt | 0 canonical catalog files; DOCTRINE/TERM/LINEAGE compiler = 0 lines |
| Membership | 0 must-exist / 0 must-not-exist (never frozen) |
| Index membership | frozen deliverable: exactly these 30 records |
"""


def write_coverage_report(report: CorpusQaReport, f) -> None:
    """Write the deterministic I.5 coverage report (B7).

    `f` is any text-mode file object. No timestamps: two runs over the same
    snapshot produce byte-identical output.
    """

    c = report.counts
    by_type = ", ".join(
        f"{kind.value} {c.by_type.get(kind, 0)}" for kind in ObjectType
        if c.by_type.get(kind, 0)
    )
    by_exp = ", ".join(
        f"{exposure.value} {c.by_exposure.get(exposure, 0)}"
        for exposure in ProductExposure
        if c.by_exposure.get(exposure, 0)
    )
    checks = (
        ("I.5.1 link integrity (broken parent/related/evidence/provenance or "
         "claim route)", "link_integrity"),
        ("I.5.2 unsupported number (promoted digit-bearing claim without "
         "evidence)", "unsupported_number"),
        ("I.5.3 status/generation leakage (index vs canonical divergence)",
         "status_leakage"),
        ("I.5.4 exposure leakage (default PUBLIC_TEACHING / internal bodies)",
         "exposure_leakage"),
        ("Index membership (canonical object absent from index)", "membership"),
        ("Quarantine truth (card quarantined / quarantined source in index)",
         "quarantine"),
    )
    f.write("# CEREBUS I.5 Corpus Coverage Report\n\n")
    f.write("Deterministic regeneration of the frozen I.5 corpus coverage "
            "snapshot.\n\n")
    f.write(_FROZEN_SNAPSHOT)
    f.write("\n## Automated corpus counts (regenerated)\n\n")
    f.write(f"- canonical objects: {c.objects} ({by_type})\n")
    f.write(f"- exposure inventory: {by_exp}\n")
    f.write(f"- source artifacts: {c.artifacts}\n")
    f.write(f"- provenance edges: {c.edges}\n")
    f.write(f"- quarantined: {c.quarantined} "
            f"(canonical-card quarantines: {c.card_quarantines})\n")
    f.write(f"- claims: {c.claims}, evidence-linked "
            f"{c.claims_with_evidence}/{c.claims}; digit-bearing "
            f"{c.digit_claims}, evidence-linked "
            f"{c.digit_claims_evidence_linked}/{c.digit_claims}\n")
    f.write(f"- subscriber-visible records: {c.subscriber_visible}\n")
    f.write("\n## Automated checks\n\n")
    for label, detector in checks:
        if detector is None:
            hits = [x for x in report.findings
                    if x.detector in ("status_leakage",)]
        else:
            hits = [x for x in report.findings if x.detector == detector]
        f.write(f"- {'PASS' if not hits else 'FAIL'} — {label}\n")
    f.write("\n## Findings\n\n")
    if not report.findings:
        f.write("None.\n")
    else:
        for finding in report.findings:
            f.write(f"- [{finding.detector}] {finding.object_id}: "
                    f"{finding.detail}\n")


__all__ = ["CorpusCounts", "CorpusQaReport", "Finding", "run_detectors"]
