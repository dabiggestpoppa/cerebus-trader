"""Rebuildable retrieval index for GLX FORGE Book I / Bloc I.4 (Ch I.4.6-I.4.7).

The index is an EXPLICIT, controlled operation — same law as the I.3 backfill
runner: DRY_RUN or APPLY, invoked from code or CLI, never on import, never on
ordinary application startup, never on a web request (tested).

Laws:

- Built from canonical persistence through the II.2 port only.
- Immutable generations: a build compiles fully, then publishes by a single
  reference swap. A partial or failed build can never become readable.
- Deterministic identity: ``source_fingerprint`` (governed canonical state,
  reference-order normalized) and ``index_hash`` (sorted record hashes).
- Idempotent: unchanged source ⇒ UNCHANGED outcome, same generation, same
  hash, zero duplicates.
- Freshness: ``is_stale()`` recomputes the fingerprint from the live port.
- The index never writes to the persistence port — it cannot become a
  competing source of canonical truth.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.forge.persistence.port import PersistenceGateway
from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
)
from app.forge.retrieval.compiler import (
    CompileContext,
    RetrievalCompileError,
    compile_record,
    normalized_content_hash,
)
from app.forge.retrieval.objects import RetrievalHeader, RetrievalObject


class IndexBuildMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    APPLY = "APPLY"


class IndexBuildOutcome(str, Enum):
    DRY_RUN = "DRY_RUN"
    PUBLISHED = "PUBLISHED"
    UNCHANGED = "UNCHANGED"


class IndexBuildError(Exception):
    """Build failed; nothing was published (previous generation stays live)."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


class IndexNotBuilt(Exception):
    """No published index generation exists — retrieval fails closed."""

    def __init__(self) -> None:
        super().__init__("no index generation has been published")


# ---------------------------------------------------------------------------
# Quarantine catalog (I.3 report truth, explicit build input)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuarantineEntry:
    source_path: str
    reason: str


@dataclass(frozen=True)
class QuarantineCatalog:
    """Sources that must never become retrievable truth.

    Quarantined sources are not canonicalized by I.3, so they are absent from
    persistence by construction; this catalog is the belt-and-braces guard
    (ACCEPTANCE L3) and the safe discovery metadata (L4).
    """

    entries: tuple[QuarantineEntry, ...] = ()

    @classmethod
    def empty(cls) -> "QuarantineCatalog":
        return cls(())

    @classmethod
    def from_report(cls, report: Any) -> "QuarantineCatalog":
        from app.forge.backfill.mappings import MigrationClass

        entries = tuple(
            sorted(
                (
                    QuarantineEntry(outcome.path, outcome.reason)
                    for outcome in report.outcomes
                    if outcome.classification is MigrationClass.QUARANTINED
                ),
                key=lambda entry: entry.source_path,
            )
        )
        return cls(entries)

    @property
    def paths(self) -> frozenset[str]:
        return frozenset(entry.source_path for entry in self.entries)

    def reason_for(self, source_path: str) -> str | None:
        for entry in self.entries:
            if entry.source_path == source_path:
                return entry.reason
        return None

    def __len__(self) -> int:
        return len(self.entries)


# ---------------------------------------------------------------------------
# Generation (immutable, atomically published)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IndexGeneration:
    """One complete, immutable index generation."""

    generation: int
    source_fingerprint: str
    index_hash: str
    records: tuple[RetrievalObject, ...]
    # Negative metadata about sources that were refused canonicalization;
    # served only through an explicit, policy-gated discovery query.
    quarantine: tuple[QuarantineEntry, ...] = ()

    def __post_init__(self) -> None:
        ids = [record.object_id for record in self.records]
        if len(ids) != len(set(ids)):
            raise IndexBuildError(
                "DUPLICATE_ENTRY", "an index generation cannot hold duplicate ids"
            )
        if tuple(ids) != tuple(sorted(ids)):
            object.__setattr__(self, "records", tuple(sorted(self.records, key=lambda r: r.object_id)))

    @property
    def headers(self) -> tuple[RetrievalHeader, ...]:
        return tuple(record.header() for record in self.records)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(record.object_id for record in self.records)

    def record(self, object_id: str) -> RetrievalObject | None:
        for record in self.records:
            if record.object_id == object_id:
                return record
        return None

    def header(self, object_id: str) -> RetrievalHeader | None:
        record = self.record(object_id)
        return record.header() if record is not None else None

    def counts_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.records:
            counts[record.object_type.value] = counts.get(record.object_type.value, 0) + 1
        return dict(sorted(counts.items()))

    def content_hash(self) -> str:
        payload = json.dumps(
            {
                "generation": self.generation,
                "source_fingerprint": self.source_fingerprint,
                "index_hash": self.index_hash,
                "records": [record.content_hash() for record in self.records],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# The index (holder + atomic publication + staleness)
# ---------------------------------------------------------------------------


class RetrievalIndex:
    """Holds the currently published generation.

    Reads always observe a whole generation: publication is a single
    reference assignment performed only after a successful full build.
    """

    def __init__(self) -> None:
        self._current: IndexGeneration | None = None

    @property
    def current(self) -> IndexGeneration | None:
        return self._current

    def require(self) -> IndexGeneration:
        if self._current is None:
            raise IndexNotBuilt()
        return self._current

    def publish(self, generation: IndexGeneration) -> None:
        """Atomic publication: one assignment, after full validation."""

        if not isinstance(generation, IndexGeneration):
            raise IndexBuildError("INVALID_GENERATION", "not an IndexGeneration")
        self._current = generation

    @property
    def generation_number(self) -> int:
        return self._current.generation if self._current is not None else 0

    def is_stale(self, gateway: PersistenceGateway) -> bool:
        """True when live canonical state no longer matches the index.

        An absent index is never fresh. Recomputation reads the persistence
        port only; it never mutates anything.
        """

        if self._current is None:
            return True
        return read_state(gateway).fingerprint != self._current.source_fingerprint


# ---------------------------------------------------------------------------
# Governed state read (port only) + source fingerprint
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GovernedState:
    records: dict[str, CanonicalObjectRecord]
    edges: dict[str, tuple[ProvenanceEdgeRecord, ...]]
    artifacts: dict[str, ArtifactRecord]
    fingerprint: str
    # Raw listing exactly as the port returned it (may expose a duplicate;
    # the build must detect that rather than silently de-duplicating).
    listing: tuple[str, ...] = ()

    def context(self) -> CompileContext:
        return CompileContext(
            records=self.records, edges=self.edges, artifacts=self.artifacts
        )


def _fingerprint(state: GovernedState) -> str:
    """sha256 over sorted, reference-order-normalized governed state.

    Covers canonical objects, their provenance edges and the reachable
    artifacts' governed fields (never persistence-owned timestamps).
    """

    lines: list[str] = []
    for object_id in sorted(state.records):
        lines.append(f"O:{object_id}:{normalized_content_hash(state.records[object_id])}")
        for edge in state.edges.get(object_id, ()):
            lines.append(f"E:{edge.artifact_id}:{edge.object_id}:{edge.relation}")
    for artifact_id in sorted(state.artifacts):
        artifact = state.artifacts[artifact_id]
        lines.append(
            "A:"
            + ":".join(
                (
                    artifact.artifact_id,
                    artifact.source_class,
                    artifact.source_state,
                    artifact.content_identity or "",
                    artifact.locator,
                )
            )
        )
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def read_state(gateway: PersistenceGateway) -> GovernedState:
    """Read every canonical object + its provenance through the port only."""

    records: dict[str, CanonicalObjectRecord] = {}
    edges: dict[str, tuple[ProvenanceEdgeRecord, ...]] = {}
    artifacts: dict[str, ArtifactRecord] = {}

    listing = tuple(gateway.list_object_ids())
    for object_id in sorted(set(listing)):
        record = gateway.get_object(object_id)
        if record is None:
            raise IndexBuildError(
                "OBJECT_VANISHED",
                f"object id listed by the gateway but unreadable: {object_id}",
            )
        records[object_id] = record
        object_edges = tuple(gateway.edges_for_object(object_id))
        edges[object_id] = object_edges
        for edge in object_edges:
            if edge.artifact_id in artifacts:
                continue
            artifact = gateway.get_artifact(edge.artifact_id)
            if artifact is None:
                raise IndexBuildError(
                    "SOURCE_ARTIFACT_MISSING",
                    f"provenance edge points at unregistered artifact "
                    f"{edge.artifact_id}",
                )
            artifacts[edge.artifact_id] = artifact

    partial = GovernedState(
        records=records, edges=edges, artifacts=artifacts, fingerprint=""
    )
    return GovernedState(
        records=records,
        edges=edges,
        artifacts=artifacts,
        fingerprint=_fingerprint(partial),
        listing=listing,
    )


# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IndexBuildReport:
    mode: IndexBuildMode
    outcome: IndexBuildOutcome
    generation: int
    source_fingerprint: str
    index_hash: str
    compiled: int
    published: bool
    counts_by_type: dict[str, int] = field(default_factory=dict)
    added: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    quarantined_excluded: tuple[str, ...] = ()
    records: tuple[RetrievalObject, ...] = ()

    def to_json(self) -> str:
        payload = {
            "mode": self.mode.value,
            "outcome": self.outcome.value,
            "generation": self.generation,
            "source_fingerprint": self.source_fingerprint,
            "index_hash": self.index_hash,
            "compiled": self.compiled,
            "published": self.published,
            "counts_by_type": self.counts_by_type,
            "added": list(self.added),
            "changed": list(self.changed),
            "removed": list(self.removed),
            "quarantined_excluded": list(self.quarantined_excluded),
        }
        return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)

    def content_hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


_COMPILE_ERRORS = (
    RetrievalCompileError,
    ValidationError,
    ValueError,
    TypeError,
    KeyError,
    AttributeError,
)


def build_index(
    gateway: PersistenceGateway,
    *,
    quarantine: QuarantineCatalog | None = None,
    index: RetrievalIndex | None = None,
    mode: IndexBuildMode = IndexBuildMode.APPLY,
) -> IndexBuildReport:
    """Compile the governed canonical state and (APPLY) publish it atomically.

    Everything below happens before publication: any error raises
    :class:`IndexBuildError` and leaves the previous generation current.
    """

    catalog = quarantine if quarantine is not None else QuarantineCatalog.empty()
    state = read_state(gateway)
    current = index.current if index is not None else None

    unchanged = (
        current is not None
        and state.fingerprint == current.source_fingerprint
        and _catalog_hash(catalog.entries) == _catalog_hash(current.quarantine)
    )
    target_generation = (
        current.generation
        if unchanged
        else (1 if current is None else current.generation + 1)
    )

    context = state.context()
    compiled: list[RetrievalObject] = []
    quarantined_excluded: list[str] = []
    seen: set[str] = set()

    for object_id in state.listing:
        if object_id in seen:
            raise IndexBuildError(
                "DUPLICATE_CANONICAL_OBJECT",
                f"duplicate canonical id during index build: {object_id}",
            )
        seen.add(object_id)

        record = state.records[object_id]
        # Quarantine guard (L3): a record whose DEFINES source is quarantined
        # must never become an ordinary retrieval record.
        defined_by_quarantined_source = any(
            edge.artifact_id in state.artifacts
            and state.artifacts[edge.artifact_id].locator in catalog.paths
            for edge in state.edges.get(object_id, ())
            if edge.relation == "DEFINES"
        )
        if defined_by_quarantined_source:
            quarantined_excluded.append(object_id)
            continue

        try:
            compiled.append(
                compile_record(record, context, generation=target_generation)
            )
        except _COMPILE_ERRORS as exc:  # fail closed, publish nothing
            raise IndexBuildError(
                getattr(exc, "kind", "COMPILE_FAILED"),
                f"failed to compile {object_id}: {exc}",
            ) from exc

    ids = [record.object_id for record in compiled]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise IndexBuildError(
            "DUPLICATE_ENTRY", f"duplicate index entries: {', '.join(dupes)}"
        )

    records = tuple(sorted(compiled, key=lambda record: record.object_id))
    index_hash = hashlib.sha256(
        "\n".join(f"{r.object_id}:{r.content_hash()}" for r in records).encode("utf-8")
    ).hexdigest()

    added, changed, removed = _diff(current, records)
    published = False
    outcome = IndexBuildOutcome.DRY_RUN
    if mode is IndexBuildMode.APPLY:
        if unchanged:
            outcome = IndexBuildOutcome.UNCHANGED
        else:
            outcome = IndexBuildOutcome.PUBLISHED
            published = True

    if published:
        if index is None:
            raise IndexBuildError(
                "NO_INDEX_TARGET",
                "APPLY mode requires a RetrievalIndex to publish into",
            )
        # Single reference assignment — atomic publication of a whole generation.
        index.publish(
            IndexGeneration(
                generation=target_generation,
                source_fingerprint=state.fingerprint,
                index_hash=index_hash,
                records=records,
                quarantine=catalog.entries,
            )
        )

    return IndexBuildReport(
        mode=mode,
        outcome=outcome,
        generation=target_generation,
        source_fingerprint=state.fingerprint,
        index_hash=index_hash,
        compiled=len(records),
        published=published,
        counts_by_type=dict(sorted(_counts(records).items())),
        added=tuple(added),
        changed=tuple(changed),
        removed=tuple(removed),
        quarantined_excluded=tuple(sorted(quarantined_excluded)),
        records=records,
    )


def _catalog_hash(entries: tuple[QuarantineEntry, ...]) -> str:
    """Identity of the quarantine catalog input (a build input, so a changed
    catalog forces a new generation even when canonical state is identical)."""

    lines = [f"{entry.source_path}|{entry.reason}" for entry in entries]
    return hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def _counts(records: tuple[RetrievalObject, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.object_type.value] = counts.get(record.object_type.value, 0) + 1
    return counts


def _diff(
    current: IndexGeneration | None, records: tuple[RetrievalObject, ...]
) -> tuple[list[str], list[str], list[str]]:
    new_hashes = {record.object_id: record.content_hash() for record in records}
    if current is None:
        return sorted(new_hashes), [], []
    old_hashes = {record.object_id: record.content_hash() for record in current.records}
    added = sorted(set(new_hashes) - set(old_hashes))
    removed = sorted(set(old_hashes) - set(new_hashes))
    changed = sorted(
        object_id
        for object_id in set(new_hashes) & set(old_hashes)
        if new_hashes[object_id] != old_hashes[object_id]
    )
    return added, changed, removed


# ---------------------------------------------------------------------------
# Runner (explicit operation, mirrors the I.3 backfill runner law)
# ---------------------------------------------------------------------------


def run_index_build(
    gateway: PersistenceGateway,
    repo_root: Path,
    mode: IndexBuildMode = IndexBuildMode.DRY_RUN,
    index: RetrievalIndex | None = None,
) -> IndexBuildReport:
    """Explicit index build with the I.3 report-derived quarantine catalog.

    The quarantine catalog is NEGATIVE metadata from the frozen I.3 report
    (which sources were refused canonicalization); retrieval records still
    come exclusively from canonical persistence.
    """

    from app.forge.backfill.canonicalizer import canonicalize_files
    from app.forge.backfill.runner import load_corpus_files

    plan = canonicalize_files(load_corpus_files(repo_root))
    catalog = QuarantineCatalog.from_report(plan.report)
    return build_index(gateway, quarantine=catalog, index=index, mode=mode)


def main(argv: list[str] | None = None) -> int:
    """Explicit CLI entry point (never auto-run).

    Builds an in-memory store via the I.3 backfill, then compiles the index —
    a local demonstration of the controlled operation, with zero writes to
    any external store.
    """

    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in ("dry-run", "apply"):
        print(
            "usage: python -m app.forge.retrieval.index <dry-run|apply> <repo-root>"
        )
        return 2
    mode = IndexBuildMode.DRY_RUN if argv[0] == "dry-run" else IndexBuildMode.APPLY
    from app.forge.backfill.runner import BackfillMode, run_backfill
    from app.forge.persistence.memory import InMemoryPersistenceGateway

    repo_root = Path(argv[1])
    gateway = InMemoryPersistenceGateway()
    run_backfill(gateway, repo_root, BackfillMode.APPLY)
    report = run_index_build(gateway, repo_root, mode, RetrievalIndex())
    print(report.to_json())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
