"""Object/blob storage provider port (Book II / Bloc II.5, Ch II.5.5).

If runtime needs non-database protected artifacts:

- put/get metadata
- signed/authorized access strategy
- delete/version behavior

Library/GitHub recovery sources are NOT automatically production blob storage:
no such adapter exists at II.5 and none may be registered without a Bloc that
owns that decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.forge.providers.doctrine import ProviderHealth

# Frozen method set of the storage port.
STORAGE_METHODS: frozenset[str] = frozenset(
    {"put", "get", "delete", "access_strategy", "health"}
)

ACCESS_STRATEGY_KINDS: tuple[str, ...] = ("signed_url", "authorized_stream")


@dataclass(frozen=True)
class StoredObject:
    key: str
    version: int
    size_bytes: int
    content_type: str
    checksum: str


@dataclass(frozen=True)
class StoredObjectData:
    object: StoredObject
    data: bytes


@dataclass(frozen=True)
class AccessStrategy:
    kind: str
    target: str
    expires_at: float | None = None


@runtime_checkable
class StorageProvider(Protocol):
    """The frozen II.5 object/blob storage port."""

    def put(self, key: str, data: bytes, *, content_type: str) -> StoredObject:
        """Store bytes under key; mints the next version (append-only)."""
        ...

    def get(self, key: str, *, version: int | None = None) -> StoredObjectData:
        """Read current or pinned version. Missing/deleted key => classified
        error (invalid_request), never a silent empty success."""
        ...

    def delete(self, key: str) -> None:
        """Delete key (tombstone); versions are retained while retained."""
        ...

    def access_strategy(
        self, key: str, *, ttl_seconds: float
    ) -> AccessStrategy:
        """Signed or authorized access descriptor for a stored object."""
        ...

    def health(self) -> ProviderHealth:
        """Pure health answer; never a network call by itself."""
        ...
