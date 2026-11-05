"""Historical reconstruction from retained inputs under pinned versions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from app.forge.intelligence_api.composition import CompositionInputs, compose
from app.forge.intelligence_api.contracts import Snapshot
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.requests import HistoricalRequest
from app.forge.intelligence_api.versions import VIEW_HISTORICAL


@dataclass(frozen=True)
class RetainedRecord:
    snapshot_id: str
    inputs: CompositionInputs
    snapshot_hash: str
    model_version: str
    calculation_version: str
    data_cutoff: str


class HistoryStore:
    """Bounded in-memory retention. No durable store, no migration."""

    def __init__(self, *, capacity: int = 8) -> None:
        self._capacity = max(1, int(capacity))
        self._records: dict[str, RetainedRecord] = {}
        self._order: list[str] = []
        self._evicted: set[str] = set()

    def retain(self, snapshot: Snapshot, inputs: CompositionInputs) -> RetainedRecord:
        record = RetainedRecord(
            snapshot_id=snapshot.snapshot_id,
            inputs=inputs,
            snapshot_hash=snapshot.snapshot_hash,
            model_version=snapshot.key.model_version,
            calculation_version=snapshot.key.calculation_version,
            data_cutoff=snapshot.key.data_cutoff,
        )
        self._records[record.snapshot_id] = record
        if record.snapshot_id in self._order:
            self._order.remove(record.snapshot_id)
        self._order.append(record.snapshot_id)
        while len(self._order) > self._capacity:
            stale = self._order.pop(0)
            self._records.pop(stale, None)
            self._evicted.add(stale)
        return record

    def retained_ids(self) -> tuple[str, ...]:
        return tuple(self._order)

    def record(self, snapshot_id: str) -> RetainedRecord | None:
        return self._records.get(snapshot_id)

    def reconstruct(
        self,
        request: HistoricalRequest,
        *,
        current_rules_version: str | None = None,
        current_versions: Mapping[str, str] | None = None,
    ) -> Snapshot:
        from app.forge.intelligence_api.identity import snapshot_id as derive_id

        identity = derive_id(_key_for(request))
        record = self._records.get(identity)
        if record is None:
            if identity in self._evicted:
                raise RefusalError("HISTORICAL_NOT_RETAINED", detail="outside_retention")
            for candidate in self._records.values():
                key = candidate.inputs.key
                if (
                    key.instrument_id == request.instrument_id
                    and key.model_id == request.model_id
                    and key.layer is request.layer
                    and key.as_of == request.as_of
                    and key.data_cutoff == request.data_cutoff
                    and key.calculation_version == request.calculation_version
                ):
                    # Same pinned identity but a different model generation is
                    # version drift, not a missing history.
                    raise RefusalError("VERSION_DRIFT", detail="model_version_pinned")
            raise RefusalError("HISTORICAL_UNAVAILABLE", detail="no_retained_inputs")
        if request.model_version != record.model_version:
            raise RefusalError("VERSION_DRIFT", detail="model_version_pinned")
        if current_rules_version is not None and request.calculation_version != current_rules_version:
            # Replaying a retained generation with a different rule generation
            # is a mixed-generation request, not a historical snapshot.
            raise RefusalError("VERSION_DRIFT", detail="rules_mixed_generation")
        if request.calculation_version != record.calculation_version:
            raise RefusalError("HISTORICAL_UNAVAILABLE", detail="pinned_rules_unavailable")
        if current_versions is not None:
            pinned = dict(record.inputs.engine_versions)
            for name, version in current_versions.items():
                if name in pinned and pinned[name] != version:
                    raise RefusalError("HISTORICAL_UNAVAILABLE", detail="version_not_retained")

        snapshot = compose(replace(record.inputs, view=VIEW_HISTORICAL))
        if snapshot.snapshot_hash != record.snapshot_hash:
            raise RefusalError("HISTORICAL_UNAVAILABLE", detail="hash_mismatch")
        lineage = snapshot.lineage
        genesis = lineage.genesis_snapshot_id
        if genesis is not None and genesis not in self._records:
            snapshot = replace(snapshot, warnings=snapshot.warnings + ("LINEAGE_BREAK",))
        return replace(snapshot, view=VIEW_HISTORICAL)


def _key_for(request: HistoricalRequest):
    from app.forge.intelligence_api.contracts import SnapshotKey

    return SnapshotKey(
        instrument_id=request.instrument_id,
        model_id=request.model_id,
        model_version=request.model_version,
        layer=request.layer,
        as_of=request.as_of,
        data_cutoff=request.data_cutoff,
        calculation_version=request.calculation_version,
        clock_id=request.clock_id,
        session_id=request.session_id,
    )


__all__ = ["RetainedRecord", "HistoryStore"]
