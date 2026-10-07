"""FORGE authentication service (Book II / Bloc II.3).

The runtime authentication boundary: converts a request credential into a
`ForgePrincipal`, or fails deterministically.

Governing laws enforced here:

- AUTHENTICATION != AUTHORIZATION: this service performs NO authorization,
  plan, license, entitlement, capability, exposure, or product check. It
  answers only "who is calling, and is the credential currently valid?".
  Roles are carried as identity primitives; nothing consults them.
- SESSION != LICENSE: session validity is authentication truth only.
- IDENTITY != ENTITLEMENT: the principal carries identity only.

Token flow (frozen Ch II.3.3/II.3.4):

    request credential
      -> SHA-256 digest (raw token never leaves this boundary un-hashed)
      -> session lookup by digest (unique index path)
      -> session state validation (revocation, then expiry under the
         injected clock)
      -> user lookup
      -> user state validation (ACTIVE)
      -> authenticated principal (identity + session + roles)

No credential + anonymous allowed => explicit anonymous principal.
Any invalid credential => ONE uniform `AuthenticationFailure` with a single
constant message. No user enumeration, no disabled-vs-invalid distinction,
no raw database/provider errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from app.forge.identity import (
    ANONYMOUS_PRINCIPAL,
    ExternalIdentityLink,
    ForgePrincipal,
    ForgeSession,
    ForgeUser,
    IdentityError,
    IdentityRole,
    IssuedSession,
    UserState,
    new_forge_session_id,
    new_session_token,
    token_digest,
    utc_now_iso,
)
from app.forge.persistence.port import PersistenceGateway

# Uniform external failure contract (ACCEPTANCE O1/O2): every authentication
# failure — unknown token, malformed credential, expired, revoked, disabled
# user — is externally indistinguishable.
AUTHENTICATION_FAILURE_MESSAGE = "authentication failed"

# Authentication-relevant security claim carried alongside the principal.
# Deliberately narrow: no entitlement authority of any kind is attached.
_BEARER_SCHEME = "Bearer "

Clock = Callable[[], datetime]


def _system_clock() -> datetime:
    return datetime.now(timezone.utc)


class AuthenticationFailure(Exception):
    """Uniform, deterministic authentication failure.

    The message is a constant; it never reveals whether a user exists, a
    provider identity exists, a token digest matched partially, or an account
    is disabled versus the token being invalid. `kind` is retained for
    internal test/observability use ONLY — it is never rendered to callers,
    logged with credential material, or embedded in HTTP payloads.
    """

    def __init__(self, kind: str) -> None:
        super().__init__(AUTHENTICATION_FAILURE_MESSAGE)
        self.kind = kind


@dataclass(frozen=True)
class IssuedCredential:
    """Issuance-boundary result for a newly opened session.

    `bearer_token` exists ONLY here — the single issuance moment. It is never
    persisted (only its SHA-256 digest is), never logged, and never returned
    by any HTTP surface.
    """

    bearer_token: str
    session: ForgeSession


class ForgeAuthenticationService:
    """Credential -> principal boundary over the persistence port.

    The service takes the gateway explicitly (no module state) and an
    injectable clock so expiry is deterministic and testable.
    """

    def __init__(
        self,
        gateway: PersistenceGateway,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._gateway = gateway
        self._clock: Clock = clock or _system_clock

    # -- issuance -------------------------------------------------------------

    def open_session(
        self,
        user: ForgeUser,
        *,
        ttl: timedelta,
        now: datetime | None = None,
    ) -> IssuedCredential:
        """Open a new session for an ACTIVE user and issue one bearer token.

        Raw token is returned exactly once (issuance boundary); persistence
        receives only the SHA-256 digest.
        """

        current = now or self._clock()
        if user.state is not UserState.ACTIVE:
            raise AuthenticationFailure("user_not_active")
        token = new_session_token()
        expires = (current + ttl).astimezone(timezone.utc)
        session = ForgeSession(
            session_id=new_forge_session_id(),
            user_id=user.user_id,
            token_digest=token_digest(token),
            created_at=utc_now_iso(current),
            expires_at=expires.isoformat(),
        )
        self._gateway.create_session(session)
        return IssuedCredential(bearer_token=token, session=session)

    # -- linking (frozen Ch II.3.5: authenticated proof required) -------------

    def link_external_identity(
        self,
        principal: ForgePrincipal,
        *,
        provider: str,
        provider_subject: str,
        linked_at: str | None = None,
    ) -> ExternalIdentityLink:
        """Attach a provider identity to the authenticated FORGE user.

        Requires an authenticated principal (verified proof of account
        control) — anonymous linking is rejected. A subject already bound to
        a DIFFERENT user is a collision and is rejected: there is no
        email-string-only takeover path (email is never consulted).
        """

        if not principal.authenticated or principal.forge_user_id is None:
            raise AuthenticationFailure("not_authenticated")
        existing = self._gateway.get_identity_link(provider, provider_subject)
        if existing is not None and existing.forge_user_id != principal.forge_user_id:
            raise AuthenticationFailure("identity_collision")
        link = ExternalIdentityLink(
            provider=provider,
            provider_subject=provider_subject,
            forge_user_id=principal.forge_user_id,
            linked_at=linked_at or utc_now_iso(self._clock()),
        )
        self._gateway.create_identity_link(link)
        return link

    # -- authentication -------------------------------------------------------

    def authenticate_bearer(
        self,
        credential: str | None,
        *,
        allow_anonymous: bool = True,
    ) -> ForgePrincipal:
        """Convert a bearer credential (or its absence) into a principal.

        `credential` is the raw Authorization header value. Absence of a
        credential yields the anonymous principal when the caller allows
        anonymous access; the decision to allow anonymous is the route's
        (II.4 will own enforcement of authenticated-only surfaces).
        """

        if not credential or not credential.strip():
            if allow_anonymous:
                return ANONYMOUS_PRINCIPAL
            raise AuthenticationFailure("missing_credential")

        value = credential.strip()
        if not value.lower().startswith(_BEARER_SCHEME.strip().lower() + " "):
            raise AuthenticationFailure("malformed_credential")
        raw_token = value[len(_BEARER_SCHEME):].strip()
        if not raw_token:
            raise AuthenticationFailure("malformed_credential")

        digest = token_digest(raw_token)
        session = self._gateway.find_session_by_token_digest(digest)
        if session is None:
            raise AuthenticationFailure("unknown_credential")
        if session.revoked_at is not None:
            raise AuthenticationFailure("revoked_session")
        if session.is_expired(self._clock()):
            raise AuthenticationFailure("expired_session")

        user = self._gateway.get_user(session.user_id)
        if user is None:
            # Session dangling without its user: the FK prevents this in SQL;
            # treat defensively as invalid credential (no enumeration).
            raise AuthenticationFailure("unknown_credential")
        if user.state is not UserState.ACTIVE:
            raise AuthenticationFailure("user_not_active")

        return ForgePrincipal.for_session(user, session)

    # -- revocation -----------------------------------------------------------

    def revoke_session(self, session_id: str) -> None:
        """Revoke one session (admin/support path; II.4 will gate callers)."""

        self._gateway.revoke_session(session_id)

    def revoke_all_sessions(self, principal: ForgePrincipal) -> int:
        """Revoke every session of the authenticated principal's user."""

        if not principal.authenticated or principal.forge_user_id is None:
            raise AuthenticationFailure("not_authenticated")
        return self._gateway.revoke_all_sessions(principal.forge_user_id)


__all__ = [
    "AUTHENTICATION_FAILURE_MESSAGE",
    "AuthenticationFailure",
    "ForgeAuthenticationService",
    "IssuedCredential",
]
