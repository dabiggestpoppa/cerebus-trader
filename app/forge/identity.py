"""FORGE identity & session domain (Book II / Bloc II.3).

Pure domain module: no database library imports, no HTTP imports, no
persistence imports. Persistence mirrors these contracts in
`app.forge.persistence.records` (II.2 dependency direction: service and
persistence depend on domain; domain depends on nothing here).

Governing laws (frozen):

- IDENTITY != ENTITLEMENT — nothing in this module describes what a user may
  access. No plan, license, entitlement, capability, product tier or exposure
  concept exists here. Those belong to Book II / Bloc II.4 and Book VI.
- AUTHENTICATION != AUTHORIZATION — this module defines *who* is calling;
  never *what* they may do. Roles are identity primitives (frozen Ch II.3.6),
  carried as data, never consulted here for any access decision.
- SESSION != LICENSE — a session is a revocable, expiring authentication
  context. It snapshots no entitlement.
- PROVIDER ID != FORGE ID — the FORGE-generated `user_id` is authoritative.
  Provider identifiers are attributes on typed external identity links.

Token design (frozen Ch II.3.4 + PLAN):

- Opaque bearer tokens: `secrets.token_urlsafe(32)` — 256 bits of CSPRNG
  entropy. No JWT; nothing in the frozen architecture requires signed
  self-contained tokens.
- Only the SHA-256 hex digest of a token is persisted. The raw token exists
  only at the issuance boundary (`IssuedSession.raw_token`) and at the
  request-credential extraction moment; it is never stored, logged, or
  returned by any endpoint.
- No server-side pepper: a 256-bit CSPRNG token cannot be brute-forced
  through its SHA-256 digest, so a pepper would add secret-management burden
  without a threat-model gain. Documented design decision.
- Digest equality on the security-sensitive verification path uses
  `hmac.compare_digest`.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class IdentityError(Exception):
    """Base class for deterministic identity-domain failures."""


class UserState(str, Enum):
    """FORGE user lifecycle state (frozen Ch II.3.2 — deliberately minimal)."""

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class IdentityRole(str, Enum):
    """Platform roles — identity primitives, NOT entitlements (Ch II.3.6).

    Roles are carried on users/principals as data. Enforcement belongs to
    Book II / Bloc II.4. There is no generic ADMIN bypass here.
    """

    USER = "USER"
    RESEARCH_ADMIN = "RESEARCH_ADMIN"
    SUPPORT_ADMIN = "SUPPORT_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    SERVICE = "SERVICE"


# Governed user-state transitions. Both directions exist (disable/reactivate);
# same-state and unknown transitions are illegal. No terminal states are
# invented — the frozen plan requires exactly this minimal lifecycle.
_USER_STATE_TRANSITIONS: dict[UserState, frozenset[UserState]] = {
    UserState.ACTIVE: frozenset({UserState.DISABLED}),
    UserState.DISABLED: frozenset({UserState.ACTIVE}),
}


def validate_user_state_transition(current: UserState, target: UserState) -> None:
    """Raise ValueError for an illegal user-state transition."""

    if target not in _USER_STATE_TRANSITIONS.get(current, frozenset()):
        raise ValueError(
            f"illegal user state transition: {current.value} -> {target.value}"
        )


# ---------------------------------------------------------------------------
# FORGE-generated identifiers
# ---------------------------------------------------------------------------


def new_forge_user_id() -> str:
    """FORGE-owned internal user identifier (opaque 32-hex, uuid4).

    Never derived from a provider ID, an email, or any caller-supplied value:
    the internal identifier is authoritative (frozen Ch II.3.1).
    """

    return uuid.uuid4().hex


def new_forge_session_id() -> str:
    """FORGE-owned session identifier. Session ID != user ID."""

    return uuid.uuid4().hex


def utc_now_iso(now: datetime | None = None) -> str:
    """UTC ISO-8601 timestamp string used across identity records."""

    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Session token material
# ---------------------------------------------------------------------------


def new_session_token() -> str:
    """Opaque bearer token: 256 bits of CSPRNG entropy, URL-safe.

    The caller receives this raw token exactly once (issuance boundary).
    """

    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    """SHA-256 hex digest of a raw token — the ONLY persisted representation."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def digests_equal(left: str, right: str) -> bool:
    """Timing-safe digest comparison for the security-sensitive path."""

    return hmac.compare_digest(left, right)


# ---------------------------------------------------------------------------
# Domain records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForgeUser:
    """A FORGE-owned internal user.

    `user_id` is the authoritative identity. `email` is an optional UNTRUSTED
    attribute: never a key, never unique, never a lookup path, never an
    identity. Roles are identity primitives, not entitlements.
    """

    user_id: str
    state: UserState = UserState.ACTIVE
    roles: frozenset[IdentityRole] = field(default_factory=frozenset)
    email: str | None = None
    display_label: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not self.user_id or not isinstance(self.user_id, str):
            raise IdentityError("user_id must be a non-empty string")

    @classmethod
    def create(
        cls,
        *,
        roles: frozenset[IdentityRole] | None = None,
        email: str | None = None,
        display_label: str | None = None,
        now: str | None = None,
        user_id: str | None = None,
    ) -> "ForgeUser":
        """Factory that generates the internal identifier FORGE-side."""

        return cls(
            user_id=user_id or new_forge_user_id(),
            state=UserState.ACTIVE,
            roles=frozenset(roles) if roles else frozenset({IdentityRole.USER}),
            email=email,
            display_label=display_label,
            created_at=now or utc_now_iso(),
            updated_at=now or utc_now_iso(),
        )


@dataclass(frozen=True)
class ExternalIdentityLink:
    """Typed link from an external provider identity to a FORGE user.

    `(provider, provider_subject)` is unique. The FORGE user survives any
    link/unlink. Provider data is an attribute, never authorization and never
    a FORGE key. No provider secrets are stored here.
    """

    provider: str
    provider_subject: str
    forge_user_id: str
    linked_at: str | None = None

    def __post_init__(self) -> None:
        if not self.provider or not isinstance(self.provider, str):
            raise IdentityError("provider must be a non-empty string")
        if not self.provider_subject or not isinstance(self.provider_subject, str):
            raise IdentityError("provider_subject must be a non-empty string")
        if not self.forge_user_id or not isinstance(self.forge_user_id, str):
            raise IdentityError("forge_user_id must be a non-empty string")


@dataclass(frozen=True)
class ForgeSession:
    """A FORGE session: opaque ID, one user, digest, expiry, revocation.

    `token_digest` is the SHA-256 hex of the bearer token — the raw token is
    never carried on this record. A session confers no entitlement (frozen
    Ch II.3.4: no entitlement snapshot is stored or trusted).
    """

    session_id: str
    user_id: str
    token_digest: str
    created_at: str | None = None
    expires_at: str = ""
    revoked_at: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not isinstance(self.session_id, str):
            raise IdentityError("session_id must be a non-empty string")
        if not self.user_id or not isinstance(self.user_id, str):
            raise IdentityError("user_id must be a non-empty string")
        if not self.token_digest or not isinstance(self.token_digest, str):
            raise IdentityError("token_digest must be a non-empty string")
        if len(self.token_digest) != 64:
            raise IdentityError("token_digest must be a 64-char SHA-256 hex digest")
        if not self.expires_at:
            raise IdentityError("expires_at is required")

    def is_expired(self, now: datetime) -> bool:
        """Deterministic expiry against an injected clock (UTC-aware)."""

        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        try:
            expires = datetime.fromisoformat(self.expires_at)
        except ValueError as exc:
            raise IdentityError("expires_at is not a valid ISO-8601 timestamp") from exc
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc) >= expires

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


@dataclass(frozen=True)
class IssuedSession:
    """The issuance boundary result.

    `raw_token` exists ONLY here, returned once to the caller that opened the
    session. Nothing downstream (persistence, logging, HTTP responses) may
    carry it. The persisted/queried representation is `session.token_digest`.
    """

    raw_token: str
    session: ForgeSession


# ---------------------------------------------------------------------------
# Runtime principal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForgePrincipal:
    """Runtime authenticated identity context (frozen Ch II.3.3 port shape).

    Carries ONLY trustworthy runtime identity context: who (forge_user_id),
    how-bound (session identity), authentication state, and identity roles.
    It never carries plan, license, entitlement, product tier, exposure
    permission, or capability — those are downstream (II.4 / Book VI).

    The principal is never persisted and never HTTP-aware. Anonymous is a
    structurally distinct value with `forge_user_id=None` — never a fake
    user ID.
    """

    authenticated: bool
    forge_user_id: str | None
    session_id: str | None
    roles: frozenset[IdentityRole] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.authenticated:
            if not self.forge_user_id:
                raise IdentityError(
                    "an authenticated principal must carry a forge_user_id"
                )
        else:
            if self.forge_user_id is not None or self.session_id is not None:
                raise IdentityError(
                    "an anonymous principal must not carry user or session identity"
                )

    @classmethod
    def anonymous(cls) -> "ForgePrincipal":
        """The explicit anonymous principal (structurally distinct)."""

        return cls(
            authenticated=False, forge_user_id=None, session_id=None, roles=frozenset()
        )

    @classmethod
    def for_session(
        cls, user: ForgeUser, session: ForgeSession
    ) -> "ForgePrincipal":
        """Build the verified principal for a validated session."""

        return cls(
            authenticated=True,
            forge_user_id=user.user_id,
            session_id=session.session_id,
            roles=frozenset(user.roles),
        )


ANONYMOUS_PRINCIPAL: ForgePrincipal = ForgePrincipal.anonymous()


__all__ = [
    "IdentityError",
    "UserState",
    "IdentityRole",
    "validate_user_state_transition",
    "new_forge_user_id",
    "new_forge_session_id",
    "utc_now_iso",
    "new_session_token",
    "token_digest",
    "digests_equal",
    "ForgeUser",
    "ExternalIdentityLink",
    "ForgeSession",
    "IssuedSession",
    "ForgePrincipal",
    "ANONYMOUS_PRINCIPAL",
]
