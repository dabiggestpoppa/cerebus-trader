"""Deterministic snapshot identity and component hashing."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping

from app.forge.intelligence_api.contracts import Snapshot, SnapshotKey
from app.forge.intelligence_api.serialization import content_hash

SNAPSHOT_ID_PREFIX = "SNAP."
_SNAPSHOT_ID_LENGTH = 40


def snapshot_id(key: SnapshotKey) -> str:
    """Derive the logical snapshot id from the key alone."""

    return SNAPSHOT_ID_PREFIX + content_hash(key.payload())[:_SNAPSHOT_ID_LENGTH]


def component_hashes(components: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    """Fixed canonical order: component names sorted, never insertion order."""

    return tuple(sorted(((str(name), str(value)) for name, value in components.items())))


def fold_component_hashes(components: Mapping[str, str]) -> str:
    pairs = component_hashes(components)
    return content_hash({name: value for name, value in pairs})


def component_hash_list(pairs: Iterable[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(name), str(value)) for name, value in pairs))


def finalize(snapshot: Snapshot) -> Snapshot:
    """Attach derived identity and payload hash; the caller never supplies them."""

    identity = snapshot.snapshot_id or snapshot_id(snapshot.key)
    seeded = replace(snapshot, snapshot_id=identity, snapshot_hash="")
    return replace(seeded, snapshot_hash=seeded.compute_hash())


__all__ = [
    "SNAPSHOT_ID_PREFIX",
    "snapshot_id",
    "component_hashes",
    "fold_component_hashes",
    "component_hash_list",
    "finalize",
]
