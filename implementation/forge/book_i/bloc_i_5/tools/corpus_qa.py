#!/usr/bin/env python3
"""Book I / Bloc I.5 — corpus QA detector harness (frozen chapters I.5.1–I.5.6).

Rebuilds the canonical store and retrieval index from the real governed
corpus through the persistence port (in-memory store only), then runs the
deterministic corpus QA detectors frozen in PLAN §11:

- I.5.1 link integrity   — parent/related/evidence/provenance references and
                           claim routes resolve; zero dangling references
- I.5.2 unsupported number — every digit-bearing claim is evidence-linked or
                           explicitly non-promoted (100% coverage)
- I.5.3 status leakage   — index status == canonical status; source
                           generation retained wherever the source states one
- I.5.4 exposure leakage — no default PUBLIC_TEACHING, no internal bodies
- index membership       — every canonical object is present in the index
- quarantine truth       — no canonical-card quarantine; quarantined source
                           never present in the index

Run from the repository root:

    PYTHONPATH=. python implementation/forge/book_i/bloc_i_5/tools/corpus_qa.py
    PYTHONPATH=. python implementation/forge/book_i/bloc_i_5/tools/corpus_qa.py \
        --write-report implementation/forge/book_i/bloc_i_5/COVERAGE_REPORT_V1.md

Exit status 0 only when every detector reports zero findings. Read-only with
respect to the corpus and to any database: it uses the in-memory gateway
only, and (unless ``--write-report`` is given) writes nothing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))

from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.runner import BackfillMode, load_corpus_files, run_backfill
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.qa.detectors import run_detectors, write_coverage_report
from app.forge.retrieval import (
    IndexBuildMode,
    QuarantineCatalog,
    RetrievalIndex,
    run_index_build,
)


def build() -> tuple[InMemoryPersistenceGateway, RetrievalIndex, object]:
    """Apply the corpus to an in-memory store and build the index."""

    gateway = InMemoryPersistenceGateway()
    run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
    index = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, index)
    plan = canonicalize_files(load_corpus_files(REPO_ROOT))
    catalog = QuarantineCatalog.from_report(plan.report)
    return gateway, index, catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-report",
        metavar="PATH",
        help="write the deterministic I.5 coverage report to PATH",
    )
    args = parser.parse_args(argv)

    gateway, index, catalog = build()
    report = run_detectors(gateway, index.require(), catalog)

    counts = report.counts
    print(f"objects={counts.objects} artifacts={counts.artifacts} "
          f"edges={counts.edges} quarantined={counts.quarantined} "
          f"claims={counts.claims} "
          f"claims_with_evidence={counts.claims_with_evidence} "
          f"digit_claims={counts.digit_claims} "
          f"digit_linked={counts.digit_claims_evidence_linked}")
    if report.findings:
        for finding in report.findings:
            print(f"FINDING [{finding.detector}] {finding.object_id}: "
                  f"{finding.detail}")
    else:
        print("findings=0")

    if args.write_report:
        target = Path(args.write_report)
        with target.open("w", encoding="utf-8", newline="\n") as f:
            write_coverage_report(report, f)
        print(f"coverage report written: {target}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
