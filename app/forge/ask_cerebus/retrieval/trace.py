"""Deterministic, exposure-safe retrieval traces."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Iterable

from app.forge.ask_cerebus.retrieval.enums import (
    RejectionClass,
    RetrievalOutcome,
    TraceClass,
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class RetrievalTrace:
    plan_id: str
    contract_version: str
    outcome: RetrievalOutcome
    index_generation: int = 0
    index_hash: str = ""
    selected_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    snapshot_ids: tuple[str, ...] = ()
    generations: tuple[str, ...] = ()
    rejection_counts: tuple[tuple[str, int], ...] = ()
    digest: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "contract_version": self.contract_version,
            "outcome": self.outcome.value,
            "index_generation": self.index_generation,
            "index_hash": self.index_hash,
            "selected_ids": list(self.selected_ids),
            "claim_ids": list(self.claim_ids),
            "evidence_ids": list(self.evidence_ids),
            "snapshot_ids": list(self.snapshot_ids),
            "generations": list(self.generations),
            "rejection_counts": {
                key: count for key, count in self.rejection_counts
            },
        }

    def compute_digest(self) -> str:
        return hashlib.sha256(_canonical(self.payload()).encode("utf-8")).hexdigest()

    def finalized(self) -> "RetrievalTrace":
        return replace(self, digest=self.compute_digest())

    def consumer_payload(self) -> dict[str, Any]:
        """Exposure-safe projection: no rejected ids, no internal content."""

        return {
            "trace_class": TraceClass.CONSUMER.value,
            "plan_id": self.plan_id,
            "contract_version": self.contract_version,
            "outcome": self.outcome.value,
            "selected_ids": list(self.selected_ids),
            "claim_ids": list(self.claim_ids),
            "evidence_ids": list(self.evidence_ids),
            "snapshot_ids": list(self.snapshot_ids),
            "index_generation": self.index_generation,
            "digest": self.digest,
        }

    def refusal_payload(self, code: str) -> dict[str, str]:
        return {
            "trace_class": TraceClass.REFUSAL.value,
            "plan_id": self.plan_id,
            "contract_version": self.contract_version,
            "code": code,
        }


def rejection_counts(
    values: Iterable[RejectionClass],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value.value] = counts.get(value.value, 0) + 1
    return tuple(sorted(counts.items()))


__all__ = ["RetrievalTrace", "rejection_counts"]
