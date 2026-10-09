"""Focused I.5 tests: corpus QA detectors + golden fixtures (Book I / Bloc I.5).

Maps to implementation/forge/book_i/bloc_i_5/ACCEPTANCE.md clauses L (corpus
QA detectors I.5.1–I.5.4), M (coverage report + freeze manifest) and to Ch
I.5.5 golden fixtures (PLAN §11–§12): every fixture for the seven launch
models and the eight truth traps is executed through the real kernel — an
accurately qualified answer must pass, a misleadingly confident one must fail.
"""
from __future__ import annotations

import dataclasses
import io
import re
import sys
from pathlib import Path

import pytest

from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.runner import BackfillMode, load_corpus_files, run_backfill
from app.forge.canonical import EvidenceStatus, Layer, ObjectType, ProductExposure
from app.forge.identity import ForgePrincipal
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.records import CanonicalObjectRecord
from app.forge.policy import (
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_MODEL_READ_OPERATOR,
    AuthorizationContext,
)
from app.forge.qa import QAService
from app.forge.qa.detectors import run_detectors, write_coverage_report
from app.forge.qa.golden import GOLDEN_FIXTURES, check_fixture
from app.forge.retrieval import (
    IndexBuildMode,
    QuarantineCatalog,
    QuarantineEntry,
    RetrievalIndex,
    RetrievalService,
    SupportAssessment,
    run_index_build,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

MANIFEST_PATH = (
    REPO_ROOT / "implementation" / "forge" / "book_i" / "bloc_i_5"
    / "BOOK_I_FREEZE_MANIFEST_V1.md"
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
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
    return idx


@pytest.fixture(scope="module")
def generation(index):
    return index.require()


@pytest.fixture(scope="module")
def catalog() -> QuarantineCatalog:
    plan = canonicalize_files(load_corpus_files(REPO_ROOT))
    return QuarantineCatalog.from_report(plan.report)


@pytest.fixture(scope="module")
def report(gateway, generation, catalog):
    return run_detectors(gateway, generation, catalog)


@pytest.fixture(scope="module")
def qa(index) -> QAService:
    return QAService(RetrievalService(index))


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
    "anon": (ANON, AuthorizationContext.empty()),
}


def _tampered(generation, canonical_id: str, **updates):
    """One index generation whose record `canonical_id` carries `updates`."""

    records = tuple(
        record.model_copy(update=updates)
        if record.object_id == canonical_id
        else record
        for record in generation.records
    )
    return dataclasses.replace(generation, records=records)


# ---------------------------------------------------------------------------
# L1–L4 — corpus QA detectors over the real corpus
# ---------------------------------------------------------------------------


def test_real_corpus_has_zero_findings(report):
    assert report.ok, [f for f in report.findings]


def test_counts_match_frozen_snapshot(report):
    c = report.counts
    assert c.objects == 30
    assert c.by_type == {
        "MODEL": 7, "CLAIM": 10, "EVIDENCE": 10, "SETUP": 3,
    }
    assert c.by_exposure == {
        "SUBSCRIBER_MODEL": 24, "OPERATOR_ONLY": 2, "RESEARCH_LAB": 4,
    }
    assert c.artifacts == 29
    assert c.edges == 38
    assert c.quarantined == 9
    assert c.card_quarantines == 0
    assert c.claims == 10
    assert c.claims_with_evidence == 10
    assert c.digit_claims == 6
    assert c.digit_claims_evidence_linked == 6
    assert c.subscriber_visible == 24


def test_detector_detects_missing_parent(report, gateway, generation, catalog):
    tampered = _tampered(generation, "MOD.EUR.DAILY.NEWS_REKEY.V1",
                         parent_ids=("X.MISSING.V1",))
    r = run_detectors(gateway, tampered, catalog)
    assert not r.ok
    assert any(
        f.detector == "link_integrity" and "missing parent" in f.detail
        for f in r.findings
    )


def test_detector_detects_claim_route_gap(report, gateway, generation, catalog):
    # a CLAIM that routes to neither evidence nor an explicit gap is a
    # dangling route even when its status is untouched …
    claim = next(
        rec for rec in generation.records if rec.object_type is ObjectType.CLAIM
    )
    assert claim.object_id  # a real registry claim
    tampered = _tampered(
        generation, claim.object_id, support=SupportAssessment()
    )
    r = run_detectors(gateway, tampered, catalog)
    assert any(
        f.detector == "link_integrity"
        and "neither evidence nor an explicit gap" in f.detail
        for f in r.findings
    ), [f for f in r.findings if f.detector == "link_integrity"]


def test_unsupported_number_detects_promoted_unlinked(
    report, gateway, generation, catalog
):
    # a promoted digit-bearing claim with no evidence link must be flagged …
    claim = next(
        rec for rec in generation.records
        if rec.object_type is ObjectType.CLAIM
        and rec.status in (EvidenceStatus.VALIDATED, EvidenceStatus.FORWARD_OOS)
        and re.search(r"\d", rec.title + rec.retrieval_text)
    )
    tampered = _tampered(generation, claim.object_id,
                         support=SupportAssessment())
    r = run_detectors(gateway, tampered, catalog)
    assert any(f.detector == "unsupported_number" for f in r.findings)

    # … while the identical gap on a non-promoted claim is explicit and legal
    tampered2 = _tampered(
        generation,
        claim.object_id,
        support=SupportAssessment(),
        status=EvidenceStatus.CANDIDATE,
    )
    r2 = run_detectors(gateway, tampered2, catalog)
    assert not any(f.detector == "unsupported_number" for f in r2.findings)


def test_status_leakage_detects_index_canonical_divergence(
    report, gateway, generation, catalog
):
    claim = next(
        rec for rec in generation.records
        if rec.object_type is ObjectType.CLAIM
        and rec.status is EvidenceStatus.VALIDATED
    )
    tampered = _tampered(generation, claim.object_id,
                         status=EvidenceStatus.CANDIDATE)
    r = run_detectors(gateway, tampered, catalog)
    assert any(
        f.detector == "status_leakage" and f.object_id == claim.object_id
        for f in r.findings
    )


def test_exposure_leakage_flags_public_default_and_internal_body(
    report, gateway, generation, catalog
):
    model_id = "MOD.EUR.DAILY.NEWS_REKEY.V1"
    public_tampered = _tampered(
        generation, model_id, exposure_class=ProductExposure.PUBLIC_TEACHING
    )
    r = run_detectors(gateway, public_tampered, catalog)
    assert any(f.detector == "exposure_leakage" for f in r.findings)

    internal_tampered = _tampered(
        generation, model_id, exposure_class=ProductExposure.INTERNAL_METHOD
    )
    r2 = run_detectors(gateway, internal_tampered, catalog)
    assert any(
        f.detector == "exposure_leakage" and "identity-only" in f.detail
        for f in r2.findings
    )


def test_membership_detects_canonical_object_absent_from_index(
    report, generation, catalog
):
    # isolated store: the shared module gateway stays pristine
    gw = InMemoryPersistenceGateway()
    run_backfill(gw, REPO_ROOT, BackfillMode.APPLY)
    extra = CanonicalObjectRecord(
        canonical_id="TERM.SYNTHETIC.MEMBERSHIP_PROBE.V1",
        object_type=ObjectType.TERM,
        title="Membership probe",
        version="V1",
        status=EvidenceStatus.CANDIDATE,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.NONE,
        references=(),
        metadata={},
        claim_identity=None,
    )
    with gw.transaction():
        gw.create_object(extra)
    r = run_detectors(gw, generation, catalog)
    assert any(
        f.detector == "membership"
        and f.object_id == "TERM.SYNTHETIC.MEMBERSHIP_PROBE.V1"
        for f in r.findings
    )


def test_quarantine_truth_detects_card_and_indexed_source(
    report, gateway, generation, catalog
):
    card_entry = QuarantineCatalog(
        (QuarantineEntry("corpus/canonical/models/LEAKED.md", "probe"),)
    )
    r = run_detectors(gateway, generation, card_entry)
    assert any(
        f.detector == "quarantine" and "card file quarantined" in f.detail
        for f in r.findings
    )

    indexed_entry = QuarantineCatalog(
        (QuarantineEntry("MOD.EUR.DAILY.NEWS_REKEY.V1", "probe"),)
    )
    r2 = run_detectors(gateway, generation, indexed_entry)
    assert any(
        f.detector == "quarantine" and "quarantined source present" in f.detail
        for f in r2.findings
    )


# ---------------------------------------------------------------------------
# M3 — coverage report (I.5.6)
# ---------------------------------------------------------------------------


def test_coverage_report_is_deterministic_and_all_pass(report):
    first = io.StringIO()
    second = io.StringIO()
    write_coverage_report(report, first)
    write_coverage_report(report, second)
    assert first.getvalue() == second.getvalue()

    text = first.getvalue()
    assert text.startswith("# CEREBUS I.5 Corpus Coverage Report")
    assert "## Frozen snapshot (I.5 manual audit)" in text
    assert "| Canonical objects | 30" in text
    assert "PASS" in text and "FAIL" not in text
    assert "## Findings\n\nNone.\n" in text
    # every listed check line passes
    checks = [
        line for line in text.splitlines() if line.startswith("- PASS")
        or line.startswith("- FAIL")
    ]
    assert len(checks) == 6
    assert all(line.startswith("- PASS") for line in checks)


def test_coverage_report_lists_findings_when_present(
    gateway, generation, catalog
):
    tampered = _tampered(generation, "MOD.EUR.DAILY.NEWS_REKEY.V1",
                         parent_ids=("X.MISSING.V1",))
    r = run_detectors(gateway, tampered, catalog)
    buf = io.StringIO()
    write_coverage_report(r, buf)
    text = buf.getvalue()
    assert "- FAIL" in text
    assert "X.MISSING.V1" in text


# ---------------------------------------------------------------------------
# M4 — Book freeze manifest (I.5.7)
# ---------------------------------------------------------------------------


def test_freeze_manifest_exists_and_matches_live_state(generation, report):
    assert MANIFEST_PATH.exists(), (
        "BOOK_I_FREEZE_MANIFEST_V1.md must be committed (I.5.7)"
    )
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    expected_pairs = {
        "generation": str(generation.generation),
        "source_fingerprint": generation.source_fingerprint,
        "index_hash": generation.index_hash,
        "objects": str(report.counts.objects),
        "artifacts": str(report.counts.artifacts),
        "edges": str(report.counts.edges),
        "quarantined": str(report.counts.quarantined),
        "claims": str(report.counts.claims),
    }
    for key, value in expected_pairs.items():
        match = re.search(rf"^- {re.escape(key)}: (.+)$", text, re.MULTILINE)
        assert match, f"manifest missing '- {key}:' line"
        assert match.group(1).strip() == value, (
            f"manifest {key} {match.group(1).strip()!r} != live {value!r}"
        )


# ---------------------------------------------------------------------------
# I.5.5 — golden fixtures executed through the real kernel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture", GOLDEN_FIXTURES, ids=[f.name for f in GOLDEN_FIXTURES]
)
def test_golden_fixture(qa, fixture):
    principal, context = CONTEXTS[fixture.context]
    answer = qa.ask(
        principal, context, fixture.question, correlation_id="golden"
    )
    problems = check_fixture(fixture, answer)
    assert not problems, (
        f"fixture {fixture.name}: " + "; ".join(problems)
    )


def test_every_fixture_has_a_unique_name():
    names = [f.name for f in GOLDEN_FIXTURES]
    assert len(names) == len(set(names))
    assert len(GOLDEN_FIXTURES) == 18


# ---------------------------------------------------------------------------
# CLI harness (implementation/forge/book_i/bloc_i_5/tools/corpus_qa.py)
# ---------------------------------------------------------------------------


def test_corpus_qa_cli_runs_clean_and_writes_report(tmp_path):
    from implementation.forge.book_i.bloc_i_5.tools import corpus_qa

    out = tmp_path / "COVERAGE.md"
    rc = corpus_qa.main(["--write-report", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "PASS" in text and "FAIL" not in text
