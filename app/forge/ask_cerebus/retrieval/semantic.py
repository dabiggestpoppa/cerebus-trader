"""Replaceable semantic retrieval port and deterministic fake.

Semantic search receives only ids that policy already allowed. It cannot load
bodies, resolve canonical identity or alter a status.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SemanticCandidate:
    object_id: str
    text: str
    score: float = 0.0
    quote_scope: str = "SYNTHESIS"


class SemanticIndexPort(Protocol):
    def search(
        self, query: str, authorized_ids: frozenset[str], limit: int
    ) -> tuple[SemanticCandidate, ...]: ...


class DeterministicFakeSemanticIndex:
    """Fixture-backed semantic surface with no provider or network access."""

    def __init__(self, candidates: tuple[SemanticCandidate, ...] = ()) -> None:
        self._candidates = tuple(candidates)

    def search(
        self, query: str, authorized_ids: frozenset[str], limit: int
    ) -> tuple[SemanticCandidate, ...]:
        selected = [
            candidate
            for candidate in self._candidates
            if candidate.object_id in authorized_ids
        ]
        selected.sort(key=lambda candidate: (-candidate.score, candidate.object_id))
        return tuple(selected[:limit])


class EmptySemanticIndex:
    def search(
        self, query: str, authorized_ids: frozenset[str], limit: int
    ) -> tuple[SemanticCandidate, ...]:
        return ()


__all__ = [
    "SemanticCandidate",
    "SemanticIndexPort",
    "DeterministicFakeSemanticIndex",
    "EmptySemanticIndex",
]
