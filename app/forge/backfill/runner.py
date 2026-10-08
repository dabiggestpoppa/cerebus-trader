"""Corpus loader + backfill runner (Book I / Bloc I.3).

The runner is an explicit, controlled operation: DRY_RUN or APPLY, invoked
from code or CLI. It is NEVER run on import, on application startup, or on a
web request (tested). All writes go through the II.2 PersistenceGateway port
inside one transaction batch — no ad-hoc SQL, no direct DB writes.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.forge.backfill.canonicalizer import (
    BackfillReport,
    MigrationPlan,
    canonicalize_files,
)
from app.forge.backfill.mappings import NAMED_ARTIFACT_EDGES
from app.forge.persistence.port import PersistenceGateway

# Repository-rooted in-scope card corpus + named artifact paths.
CARD_GLOBS: tuple[str, ...] = (
    "corpus/canonical/models/*.md",
    "corpus/canonical/evidence/*.md",
    "corpus/canonical/setups/*.md",
)
CONVERSATION_DERIVED_GLOBS: tuple[str, ...] = (
    "corpus/conversation-derived/*.md",
)


def load_corpus_files(repo_root: Path) -> dict[str, str]:
    """Load the deterministic in-scope file map: card files, named artifact
    files, and conversation-derived files (inventory only). Purely read-only;
    no arbitrary path acceptance — only the frozen globs and the registry's
    named edges are ever read."""
    files: dict[str, str] = {}
    for pattern in CARD_GLOBS + CONVERSATION_DERIVED_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file():
                files[path.as_posix()] = path.read_text(encoding="utf-8")
    for named in NAMED_ARTIFACT_EDGES:
        candidate = repo_root / named.path
        if candidate.is_file() and named.path not in files:
            files[named.path] = candidate.read_text(encoding="utf-8")
    return files


class BackfillMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    APPLY = "APPLY"


@dataclass(frozen=True)
class BackfillResult:
    mode: BackfillMode
    report: BackfillReport
    content_hash: str


def run_backfill(
    gateway: PersistenceGateway,
    repo_root: Path,
    mode: BackfillMode = BackfillMode.DRY_RUN,
) -> BackfillResult:
    """Execute the canonical backfill in the requested mode.

    DRY_RUN: parse, map, validate, audit, report — zero persistent writes.
    APPLY: one logical transaction batch; conflict ⇒ explicit error + full
    rollback; identical re-run ⇒ NO-OP/ALREADY_CURRENT per object.
    """
    files = load_corpus_files(repo_root)
    plan: MigrationPlan = canonicalize_files(files)

    if mode is BackfillMode.DRY_RUN:
        return BackfillResult(mode, plan.report, plan.report.content_hash())

    _apply_plan(gateway, plan)

    # Deterministic reproducibility (ACCEPTANCE W): the APPLY content hash is
    # computed over the PLAN (source-derived truth), so identical source state
    # yields an identical hash on every run — run-mode deltas like the
    # "unchanged" counter stay out of the identity.
    plan_report = canonicalize_files(load_corpus_files(repo_root)).report
    return BackfillResult(mode, plan.report, plan_report.content_hash())


def _apply_plan(gateway: PersistenceGateway, plan: MigrationPlan) -> None:
    """Write the whole plan through the persistence port in one atomic batch.

    Two-phase: the runner stages the full batch and commits through the
    gateway's transaction so mutually-referencing aggregates (CLAIM <->
    EVIDENCE) resolve against the batch itself — matching SQL semantics where
    earlier inserts in the open transaction are visible. Conflict, duplicate,
    or dangling failure anywhere in the batch rolls back EVERYTHING.

    Idempotent per object: existing object with identical governed content is
    skipped (NO_CHANGE); existing object with DIFFERENT content raises
    ConflictError (no silent overwrite).
    """
    existing_ids = set(gateway.list_object_ids())

    # Resolve which records still need creating BEFORE opening the batch.
    to_create: list = []
    for record in sorted(plan.objects, key=lambda r: r.canonical_id):
        if record.canonical_id in existing_ids:
            current = gateway.get_object(record.canonical_id)
            if current is not None and _governed_payload(current) == _governed_payload(record):
                plan.report.unchanged += 1
                continue
            plan.report.conflicts += 1
            raise ConflictError(
                f"canonical id exists with different governed content: "
                f"{record.canonical_id}"
            )
        to_create.append(record)

    # Pre-stage artifacts and edges (edge targets must exist after commit).
    artifacts_to_create = [
        a for a in plan.artifacts if gateway.get_artifact(a.artifact_id) is None
    ]
    from app.forge.persistence.records import ProvenanceEdgeRecord

    edges_to_create: list[ProvenanceEdgeRecord] = []
    for artifact_id, object_id, relation, note in plan.edges:
        already = any(
            e.artifact_id == artifact_id and e.object_id == object_id and e.relation == relation
            for e in gateway.edges_for_object(object_id)
        )
        if not already:
            edges_to_create.append(
                ProvenanceEdgeRecord(
                    artifact_id=artifact_id, object_id=object_id,
                    relation=relation, note=note,
                )
            )

    # One transaction: everything commits or everything rolls back.
    with gateway.transaction():
        for artifact in artifacts_to_create:
            gateway.create_artifact(artifact)
        for record in to_create:
            gateway.create_object(record)
        for edge in edges_to_create:
            gateway.add_provenance_edge(edge)


            if record.canonical_id in existing_ids:
                current = gateway.get_object(record.canonical_id)
                if current is not None and _governed_payload(current) == _governed_payload(record):
                    plan.report.unchanged += 1
                    continue
                plan.report.conflicts += 1
                raise ConflictError(
                    f"canonical id exists with different governed content: "
                    f"{record.canonical_id}"
                )
            gateway.create_object(record)

        # 2. Artifacts.
        for artifact in plan.artifacts:
            if gateway.get_artifact(artifact.artifact_id) is None:
                gateway.create_artifact(artifact)

        # 3. Provenance edges (tolerate duplicate edges only when identical
        #    content already persisted; never overwrite differing content).
        for artifact_id, object_id, relation, note in plan.edges:
            already = any(
                e.artifact_id == artifact_id
                and e.object_id == object_id
                and e.relation == relation
                for e in gateway.edges_for_object(object_id)
            )
            if not already:
                from app.forge.persistence.records import ProvenanceEdgeRecord

                gateway.add_provenance_edge(
                    ProvenanceEdgeRecord(
                        artifact_id=artifact_id,
                        object_id=object_id,
                        relation=relation,
                        note=note,
                    )
                )


def _governed_payload(record) -> str:
    """Deterministic governed-content comparison (persistence-owned fields
    excluded)."""
    import json

    from app.forge.persistence.records import CanonicalObjectRecord

    assert isinstance(record, CanonicalObjectRecord)
    payload = {
        "canonical_id": record.canonical_id,
        "object_type": record.object_type.value,
        "title": record.title,
        "version": record.version,
        "status": record.status.value,
        "exposure": record.exposure.value,
        "layer": record.layer.value,
        "references": [
            {"target_id": r.target_id, "relation": r.relation,
             "allow_unresolved_historical": r.allow_unresolved_historical}
            for r in record.references
        ],
        "metadata": record.metadata,
        "claim_identity": (
            record.claim_identity.comparison_key()
            if record.claim_identity is not None
            else None
        ),
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


class ConflictError(Exception):
    """Explicit conflict: canonical id exists with different governed content."""


def main(argv: list[str] | None = None) -> int:
    """Explicit CLI entry point (never auto-run)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in ("dry-run", "apply"):
        print("usage: python -m app.forge.backfill.runner <dry-run|apply> <repo-root>")
        return 2
    mode = BackfillMode.DRY_RUN if argv[0] == "dry-run" else BackfillMode.APPLY
    from app.forge.persistence.memory import InMemoryPersistenceGateway

    gateway = InMemoryPersistenceGateway()
    result = run_backfill(gateway, Path(argv[1]), mode)
    print(result.report.to_json())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
