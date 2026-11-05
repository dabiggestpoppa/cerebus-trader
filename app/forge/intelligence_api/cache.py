"""Two-tier cache keyed by snapshot identity and policy fingerprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from app.forge.intelligence_api.contracts import Snapshot
from app.forge.intelligence_api.serialization import content_hash

INVALIDATION_EVENTS = (
    "FINAL_BAR",
    "MODEL_VERSION",
    "CALIBRATION",
    "CORRECTED_DATA",
    "EXPOSURE_CHANGE",
)


@dataclass(frozen=True)
class ResponseKey:
    snapshot_id: str
    exposure: str
    policy_fingerprint: str
    principal_scope: str


def policy_fingerprint(*, allowed: bool, reason_code: str, exposure: str) -> str:
    return content_hash(
        {"allowed": bool(allowed), "reason": str(reason_code), "exposure": str(exposure)}
    )


def principal_scope(*, authenticated: bool, user_id: str | None) -> str:
    if authenticated and user_id:
        return f"user:{user_id}"
    return "anonymous"


class SnapshotCache:
    """Tier 1 composition cache + tier 2 authorization-scoped response cache."""

    def __init__(self, *, capacity: int = 16) -> None:
        self._capacity = max(1, int(capacity))
        self._composition: dict[str, Snapshot] = {}
        self._responses: dict[ResponseKey, Snapshot] = {}
        self._invalidations: list[str] = []

    # -- tier 1 ---------------------------------------------------------
    def put_composition(self, snapshot: Snapshot) -> None:
        snapshot_id = snapshot.snapshot_id
        if not snapshot_id:
            raise ValueError("snapshot must carry an id")
        self._composition[snapshot_id] = snapshot
        self._evict(self._composition)

    def get_composition(self, snapshot_id: str) -> Snapshot | None:
        return self._composition.get(snapshot_id)

    # -- tier 2 ---------------------------------------------------------
    def put_response(self, key: ResponseKey, snapshot: Snapshot) -> None:
        self._responses[key] = snapshot
        if len(self._responses) > self._capacity:
            for stale in sorted(
                self._responses, key=lambda item: (item.snapshot_id, item.exposure, item.principal_scope)
            )[: len(self._responses) - self._capacity]:
                del self._responses[stale]

    def get_response(self, key: ResponseKey) -> Snapshot | None:
        return self._responses.get(key)

    # -- lifecycle ------------------------------------------------------
    def invalidate(self, event: str, *, snapshot_id: str | None = None) -> None:
        if event not in INVALIDATION_EVENTS:
            raise ValueError(f"unknown invalidation event: {event}")
        self._invalidations.append(event)
        if snapshot_id is None:
            self._composition.clear()
            self._responses.clear()
            return
        self._composition.pop(snapshot_id, None)
        for key in [k for k in self._responses if k.snapshot_id == snapshot_id]:
            del self._responses[key]

    def invalidations(self) -> tuple[str, ...]:
        return tuple(self._invalidations)

    def sizes(self) -> Mapping[str, int]:
        return {"composition": len(self._composition), "responses": len(self._responses)}

    def _evict(self, store: dict[str, Snapshot]) -> None:
        if len(store) <= self._capacity:
            return
        for stale in sorted(store)[: len(store) - self._capacity]:
            del store[stale]


__all__ = [
    "INVALIDATION_EVENTS",
    "ResponseKey",
    "SnapshotCache",
    "policy_fingerprint",
    "principal_scope",
]
