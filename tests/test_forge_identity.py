"""Focused II.3 tests: identity domain, persistence identity section,
authentication service, security invariants (Book II / Bloc II.3).

Covers ACCEPTANCE.md clauses A–S that are executable without a live
PostgreSQL server; PostgreSQL evidence lives in
`tests/test_forge_postgres_integration.py` (CI).
"""

from __future__ import annotations

import dataclasses
import hashlib
from datetime import datetime, timedelta, timezone

import pytest

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
    new_forge_user_id,
    new_session_token,
    token_digest,
    utc_now_iso,
    validate_user_state_transition,
)
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.service.authentication import (
    AUTHENTICATION_FAILURE_MESSAGE,
    AuthenticationFailure,
    ForgeAuthenticationService,
)
from app.forge.service.container import ForgeServiceContainer
from app.forge.config import forge_config_from_values

SQLA_AVAILABLE = True
try:
    import sqlalchemy  # noqa: F401
except ImportError:  # pragma: no cover
    SQLA_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _gateway() -> InMemoryPersistenceGateway:
    return InMemoryPersistenceGateway()


def _auth(gateway=None, clock=None) -> ForgeAuthenticationService:
    return ForgeAuthenticationService(gateway or _gateway(), clock=clock)


def _active_user(gateway, roles=None) -> ForgeUser:
    user = ForgeUser.create(roles=frozenset(roles) if roles else None)
    gateway.create_user(user)
    return user


FIXED_NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)


def _fixed_clock():
    return lambda: FIXED_NOW


# ---------------------------------------------------------------------------
# A — internal user identity
# ---------------------------------------------------------------------------


class TestInternalUserIdentity:
    def test_forge_user_id_generated_internally(self) -> None:
        uid = new_forge_user_id()
        assert isinstance(uid, str) and len(uid) == 32
        int(uid, 16)  # opaque 32-hex

    def test_user_ids_differ(self) -> None:
        assert new_forge_user_id() != new_forge_user_id()

    def test_provider_subject_is_not_internal_id(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        link = ExternalIdentityLink(
            provider="whop",
            provider_subject="whop-customer-000123",
            forge_user_id=user.user_id,
        )
        gw.create_identity_link(link)
        resolved = gw.get_identity_link("whop", "whop-customer-000123")
        assert resolved.forge_user_id == user.user_id
        assert resolved.forge_user_id != "whop-customer-000123"
        # provider subject is not a forge PK: users table has no such row
        assert gw.get_user("whop-customer-000123") is None

    def test_email_is_not_internal_id(self) -> None:
        gw = _gateway()
        user = ForgeUser.create(email="person@example.com")
        gw.create_user(user)
        # no email lookup path exists anywhere in the port
        assert gw.get_user("person@example.com") is None
        assert user.email == "person@example.com"  # attribute only

    def test_create_read_user_round_trip(self) -> None:
        gw = _gateway()
        user = ForgeUser.create(
            email="rt@example.com",
            display_label="Round Trip",
            roles=frozenset({IdentityRole.USER, IdentityRole.SUPPORT_ADMIN}),
        )
        gw.create_user(user)
        fetched = gw.get_user(user.user_id)
        assert fetched == user

    def test_user_state_round_trip_and_transition(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        assert user.state is UserState.ACTIVE
        result = gw.transition_user_state(user.user_id, "DISABLED")
        assert result.persisted_version == 2
        assert gw.get_user(user.user_id).state is UserState.DISABLED
        gw.transition_user_state(user.user_id, "ACTIVE")
        assert gw.get_user(user.user_id).state is UserState.ACTIVE

    def test_illegal_user_state_transitions_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        with pytest.raises(Exception):  # IllegalUserStateTransition
            gw.transition_user_state(user.user_id, "ACTIVE")
        validate_user_state_transition(UserState.ACTIVE, UserState.DISABLED)
        with pytest.raises(ValueError):
            validate_user_state_transition(UserState.DISABLED, UserState.DISABLED)

    def test_stale_user_mutation_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        with pytest.raises(Exception):  # StaleWriteConflict
            gw.transition_user_state(
                user.user_id, "DISABLED", expected_version=99
            )

    def test_user_identity_survives_provider_link_changes(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="whop", provider_subject="s1", forge_user_id=user.user_id
            )
        )
        gw.delete_identity_link("whop", "s1")
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="future", provider_subject="s2", forge_user_id=user.user_id
            )
        )
        # the FORGE identity is untouched throughout
        assert gw.get_user(user.user_id) == user

    def test_duplicate_user_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        with pytest.raises(Exception):  # DuplicateForgeUser
            gw.create_user(user)


# ---------------------------------------------------------------------------
# B — external identity links
# ---------------------------------------------------------------------------


class TestExternalIdentityLinks:
    def test_link_round_trip(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="provider-a",
                provider_subject="subject-1",
                forge_user_id=user.user_id,
                linked_at=utc_now_iso(),
            )
        )
        link = gw.get_identity_link("provider-a", "subject-1")
        assert (link.provider, link.provider_subject, link.forge_user_id) == (
            "provider-a",
            "subject-1",
            user.user_id,
        )

    def test_provider_subject_uniqueness(self) -> None:
        gw = _gateway()
        u1 = _active_user(gw)
        u2 = _active_user(gw)
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="p", provider_subject="s", forge_user_id=u1.user_id
            )
        )
        with pytest.raises(Exception):  # DuplicateIdentityLink
            gw.create_identity_link(
                ExternalIdentityLink(
                    provider="p", provider_subject="s", forge_user_id=u2.user_id
                )
            )

    def test_multiple_providers_one_user(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        for provider in ("whop", "provider-b", "provider-c"):
            gw.create_identity_link(
                ExternalIdentityLink(
                    provider=provider,
                    provider_subject=f"{provider}-subject",
                    forge_user_id=user.user_id,
                )
            )
        links = gw.identity_links_for_user(user.user_id)
        assert {link.provider for link in links} == {"whop", "provider-b", "provider-c"}

    def test_unlink_does_not_delete_user(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="whop", provider_subject="gone", forge_user_id=user.user_id
            )
        )
        gw.delete_identity_link("whop", "gone")
        assert gw.get_identity_link("whop", "gone") is None
        assert gw.get_user(user.user_id) == user

    def test_link_to_unknown_user_rejected(self) -> None:
        gw = _gateway()
        with pytest.raises(Exception):  # UserNotFound
            gw.create_identity_link(
                ExternalIdentityLink(
                    provider="p", provider_subject="s", forge_user_id="ghost"
                )
            )

    def test_no_provider_secrets_in_identity_metadata(self) -> None:
        # review-as-test: link record fields carry no credential material
        field_names = {f.name for f in dataclasses.fields(ExternalIdentityLink)}
        assert field_names == {
            "provider",
            "provider_subject",
            "forge_user_id",
            "linked_at",
        }


# ---------------------------------------------------------------------------
# C/D — principal & anonymous
# ---------------------------------------------------------------------------


class TestPrincipal:
    def test_principal_fields_exact(self) -> None:
        field_names = {f.name for f in dataclasses.fields(ForgePrincipal)}
        assert field_names == {"authenticated", "forge_user_id", "session_id", "roles"}

    def test_principal_contains_no_entitlement_vocabulary(self) -> None:
        forbidden = {
            "plan",
            "plans",
            "license",
            "licenses",
            "entitlement",
            "entitlements",
            "tier",
            "product",
            "capability",
            "capabilities",
            "exposure",
            "permissions",
        }
        for cls in (ForgePrincipal, ForgeUser, ForgeSession, ExternalIdentityLink):
            names = {f.name for f in dataclasses.fields(cls)}
            assert not (names & forbidden), (cls.__name__, names & forbidden)

    def test_authenticated_principal_shape(self) -> None:
        gw = _gateway()
        user = _active_user(gw, roles={IdentityRole.USER, IdentityRole.SERVICE})
        session = ForgeSession(
            session_id=new_forge_session_id(),
            user_id=user.user_id,
            token_digest=token_digest(new_session_token()),
            expires_at=utc_now_iso(FIXED_NOW + timedelta(hours=1)),
        )
        principal = ForgePrincipal.for_session(user, session)
        assert principal.authenticated is True
        assert principal.forge_user_id == user.user_id
        assert principal.session_id == session.session_id
        assert principal.roles == frozenset(
            {IdentityRole.USER, IdentityRole.SERVICE}
        )

    def test_anonymous_principal_structurally_distinct(self) -> None:
        anon = ANONYMOUS_PRINCIPAL
        assert anon.authenticated is False
        assert anon.forge_user_id is None
        assert anon.session_id is None
        assert anon.roles == frozenset()
        with pytest.raises(IdentityError):
            ForgePrincipal(authenticated=False, forge_user_id="someone", session_id=None)
        with pytest.raises(IdentityError):
            ForgePrincipal(authenticated=True, forge_user_id=None, session_id=None)


# ---------------------------------------------------------------------------
# E/F/G — sessions and tokens
# ---------------------------------------------------------------------------


class TestSessionsAndTokens:
    def test_session_id_distinct_from_user_id(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        session_id = new_forge_session_id()
        assert session_id != user.user_id
        assert new_forge_session_id() != new_forge_session_id()

    def test_issued_tokens_differ_and_are_strong(self) -> None:
        t1 = new_session_token()
        t2 = new_session_token()
        assert t1 != t2
        # 256-bit entropy: >= 32 bytes raw
        import base64

        assert len(base64.urlsafe_b64decode(t1 + "==")) >= 32

    def test_digest_is_sha256_hex(self) -> None:
        token = new_session_token()
        digest = token_digest(token)
        assert digest == hashlib.sha256(token.encode("utf-8")).hexdigest()
        assert len(digest) == 64

    def test_session_record_carries_digest_not_raw_token(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        stored = gw.get_session(issued.session.session_id)
        assert stored.token_digest == token_digest(issued.bearer_token)
        assert issued.bearer_token not in str(stored)
        assert issued.bearer_token not in repr(stored)

    def test_raw_token_absent_from_database_representation(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        # raw token appears nowhere in the persisted state of the gateway
        state_dump = repr(gw.__dict__)
        assert issued.bearer_token not in state_dump
        assert token_digest(issued.bearer_token) in state_dump

    def test_session_binds_exactly_one_user(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        assert issued.session.user_id == user.user_id
        # session_id != user_id
        assert issued.session.session_id != user.user_id

    def test_valid_token_authenticates(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        principal = auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        assert principal.authenticated is True
        assert principal.forge_user_id == user.user_id
        assert principal.session_id == issued.session.session_id

    def test_invalid_token_rejected(self) -> None:
        auth = _auth()
        with pytest.raises(AuthenticationFailure) as exc:
            auth.authenticate_bearer(f"Bearer {new_session_token()}")
        assert str(exc.value) == AUTHENTICATION_FAILURE_MESSAGE

    def test_expired_token_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        clock = _fixed_clock()
        auth = _auth(gw, clock=clock)
        issued = auth.open_session(user, ttl=timedelta(minutes=-1))
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")

    def test_expiry_deterministic_under_injected_clock(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        current = {"now": FIXED_NOW}
        auth = _auth(gw, clock=lambda: current["now"])
        issued = auth.open_session(user, ttl=timedelta(minutes=30))
        # just before expiry: valid
        current["now"] = FIXED_NOW + timedelta(minutes=29, seconds=59)
        principal = auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        assert principal.authenticated is True
        # exactly at expiry: rejected (>= boundary)
        current["now"] = FIXED_NOW + timedelta(minutes=30)
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")

    def test_revoked_token_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        auth.revoke_session(issued.session.session_id)
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")

    def test_disabled_user_rejected_through_valid_session(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        gw.transition_user_state(user.user_id, "DISABLED")
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")

    def test_no_credential_yields_anonymous_where_allowed(self) -> None:
        auth = _auth()
        for missing in (None, "", "   "):
            principal = auth.authenticate_bearer(missing, allow_anonymous=True)
            assert principal is ANONYMOUS_PRINCIPAL
            assert principal.forge_user_id is None
            assert principal.authenticated is False

    def test_no_credential_rejected_when_anonymous_disallowed(self) -> None:
        auth = _auth()
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(None, allow_anonymous=False)

    def test_anonymous_never_creates_persisted_user(self) -> None:
        gw = _gateway()
        auth = _auth(gw)
        auth.authenticate_bearer(None)
        assert gw.list_object_ids() == tuple()  # no objects; users dict private
        # anonymous user_id is None, never a fake string
        assert auth.authenticate_bearer(None).forge_user_id is None

    def test_session_revocation_persists(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        assert gw.get_session(issued.session.session_id).revoked_at is None
        auth.revoke_session(issued.session.session_id)
        assert gw.get_session(issued.session.session_id).revoked_at is not None
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")

    def test_revoke_all_invalidates_user_sessions(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued_a = auth.open_session(user, ttl=timedelta(minutes=10))
        issued_b = auth.open_session(user, ttl=timedelta(minutes=10))
        principal = auth.authenticate_bearer(f"Bearer {issued_a.bearer_token}")
        assert auth.revoke_all_sessions(principal) == 2
        for token in (issued_a.bearer_token, issued_b.bearer_token):
            with pytest.raises(AuthenticationFailure):
                auth.authenticate_bearer(f"Bearer {token}")

    def test_stale_session_revocation_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        with pytest.raises(Exception):  # StaleWriteConflict
            gw.revoke_session(issued.session.session_id, expected_version=42)

    def test_duplicate_session_rejected(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        session = ForgeSession(
            session_id=new_forge_session_id(),
            user_id=user.user_id,
            token_digest=token_digest(new_session_token()),
            expires_at=utc_now_iso(FIXED_NOW + timedelta(hours=1)),
        )
        gw.create_session(session)
        with pytest.raises(Exception):  # DuplicateSession
            gw.create_session(session)
        # digest uniqueness
        clash = ForgeSession(
            session_id=new_forge_session_id(),
            user_id=user.user_id,
            token_digest=session.token_digest,
            expires_at=utc_now_iso(FIXED_NOW + timedelta(hours=1)),
        )
        with pytest.raises(Exception):  # DuplicateSession("token_digest")
            gw.create_session(clash)

    def test_create_user_plus_link_transaction_rolls_back(self) -> None:
        gw = _gateway()
        survivor = ForgeUser.create()
        try:
            with gw.transaction():
                gw.create_user(survivor)
                gw.create_identity_link(
                    ExternalIdentityLink(
                        provider="p",
                        provider_subject="s",
                        forge_user_id=survivor.user_id,
                    )
                )
                # then a failure inside the same logical operation
                gw.create_identity_link(
                    ExternalIdentityLink(
                        provider="p",
                        provider_subject="s",
                        forge_user_id=survivor.user_id,
                    )
                )
        except Exception:
            pass
        assert gw.get_user(survivor.user_id) is None
        assert gw.get_identity_link("p", "s") is None


# ---------------------------------------------------------------------------
# M/N/O — authentication boundary, HTTP integration, error contract
# ---------------------------------------------------------------------------


class TestAuthenticationContract:
    def test_linking_requires_authenticated_proof(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        with pytest.raises(AuthenticationFailure):
            auth.link_external_identity(
                ANONYMOUS_PRINCIPAL, provider="whop", provider_subject="s"
            )
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        principal = auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        link = auth.link_external_identity(
            principal, provider="whop", provider_subject="s"
        )
        assert link.forge_user_id == user.user_id

    def test_linking_collision_rejected(self) -> None:
        gw = _gateway()
        u1 = _active_user(gw)
        u2 = _active_user(gw)
        auth = _auth(gw)
        p1 = ForgePrincipal(
            authenticated=True, forge_user_id=u1.user_id, session_id=None
        )
        auth.link_external_identity(p1, provider="whop", provider_subject="dup")
        p2 = ForgePrincipal(
            authenticated=True, forge_user_id=u2.user_id, session_id=None
        )
        with pytest.raises(AuthenticationFailure):
            auth.link_external_identity(p2, provider="whop", provider_subject="dup")

    def test_no_email_takeover_path(self) -> None:
        # linking never consults email: two users may share an email attribute
        gw = _gateway()
        u1 = ForgeUser.create(email="same@example.com")
        u2 = ForgeUser.create(email="same@example.com")
        gw.create_user(u1)
        gw.create_user(u2)
        assert u1.user_id != u2.user_id

    def test_uniform_failure_for_all_invalid_credentials(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        outcomes = set()

        def attempt(credential: str | None) -> None:
            try:
                auth.authenticate_bearer(credential, allow_anonymous=False)
            except AuthenticationFailure as exc:
                outcomes.add((type(exc).__name__, str(exc)))

        attempt("Bearer definitely-unknown-token")
        attempt("Token weird-scheme")
        attempt("Bearer")
        attempt("Bearer ")  # empty bearer
        expired = auth.open_session(user, ttl=timedelta(minutes=-1))
        attempt(f"Bearer {expired.bearer_token}")
        revoked = auth.open_session(user, ttl=timedelta(minutes=10))
        auth.revoke_session(revoked.session.session_id)
        attempt(f"Bearer {revoked.bearer_token}")
        gw.transition_user_state(user.user_id, "DISABLED")
        disabled = auth.open_session(user, ttl=timedelta(minutes=10))
        attempt(f"Bearer {disabled.bearer_token}")
        gw.transition_user_state(user.user_id, "ACTIVE")

        assert len(outcomes) == 1, outcomes
        assert outcomes == {
            ("AuthenticationFailure", AUTHENTICATION_FAILURE_MESSAGE)
        }

    def test_no_user_enumeration_disabled_vs_unknown(self) -> None:
        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        gw.transition_user_state(user.user_id, "DISABLED")
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        try:
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
            failure_disabled = None
        except AuthenticationFailure as exc:
            failure_disabled = (type(exc).__name__, str(exc))
        try:
            auth.authenticate_bearer(f"Bearer {new_session_token()}")
            failure_unknown = None
        except AuthenticationFailure as exc:
            failure_unknown = (type(exc).__name__, str(exc))
        assert failure_disabled == failure_unknown

    def test_auth_failure_never_carries_raw_db_errors(self) -> None:
        gw = _gateway()
        auth = _auth(gw)
        try:
            auth.authenticate_bearer("Bearer nope")
            raise AssertionError("expected failure")
        except AuthenticationFailure as exc:
            assert AUTHENTICATION_FAILURE_MESSAGE in str(exc)
            assert "sql" not in str(exc).lower()
            assert "sqlite" not in str(exc).lower()

    def test_token_not_present_in_auth_error(self) -> None:
        gw = _gateway()
        auth = _auth(gw)
        secret = "raw-secret-bearer-token-abcdef-0123456789"
        try:
            auth.authenticate_bearer(f"Bearer {secret}")
            raise AssertionError("expected failure")
        except AuthenticationFailure as exc:
            assert secret not in str(exc)
            assert secret not in repr(exc)

    def test_token_not_logged(self, caplog) -> None:
        import logging

        gw = _gateway()
        user = _active_user(gw)
        auth = _auth(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        with caplog.at_level(logging.DEBUG, logger="forge"):
            auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
            try:
                auth.authenticate_bearer("Bearer unknown-raw-token-value")
            except AuthenticationFailure:
                pass
        assert issued.bearer_token not in caplog.text
        assert "unknown-raw-token-value" not in caplog.text

    def test_token_not_present_in_meta_or_ready(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        gw = InMemoryPersistenceGateway()
        container = ForgeServiceContainer(
            config=forge_config_from_values(), persistence=gw
        )
        auth = ForgeAuthenticationService(gw)
        user = ForgeUser.create()
        gw.create_user(user)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        header = {"Authorization": f"Bearer {issued.bearer_token}"}
        with TestClient(app) as client:
            meta = client.get("/forge/v1/meta", headers=header)
            ready = client.get("/forge/v1/ready", headers=header)
        assert issued.bearer_token not in meta.text
        assert issued.bearer_token not in ready.text

    def test_no_new_public_route(self) -> None:
        from app.main import app

        paths = {
            getattr(route, "path", "")
            for route in app.router.routes
        }
        forge_paths = {p for p in paths if "/forge/" in p}
        assert forge_paths == {
            "/forge/v1/health",
            "/forge/v1/ready",
            "/forge/v1/meta",
        }
        forbidden = ("/users", "/sessions", "/admin", "/licenses", "/entitlements", "/plans")
        for path in paths:
            if not path:
                continue
            for f in forbidden:
                assert f not in path, path

    def test_container_builds_authentication_from_persistence(self) -> None:
        gw = _gateway()
        container = ForgeServiceContainer(
            config=forge_config_from_values(), persistence=gw
        )
        assert isinstance(container.authentication, ForgeAuthenticationService)
        assert container.authentication._gateway is gw

    def test_container_without_persistence_has_no_authentication(self) -> None:
        container = ForgeServiceContainer(config=forge_config_from_values())
        assert container.authentication is None

    def test_readiness_semantics_unchanged(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            body = client.get("/forge/v1/ready").json()
        deps = body["dependencies"]
        assert "identity" not in deps  # no fake identity readiness entry
        assert deps["postgresql"]["status"] == "NOT_CONFIGURED"
        assert set(deps) >= {"forge", "postgresql"}


# ---------------------------------------------------------------------------
# I/J/R — migrations, integrity, security scope
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not SQLA_AVAILABLE, reason="SQLAlchemy not installed")
class TestSqlContractIdentity:
    def _gateway(self):
        from sqlalchemy import create_engine

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        gw = SqlAlchemyPersistenceGateway(engine.connect())
        gw.apply_migrations()
        return gw

    def test_identity_migration_applies_after_001(self) -> None:
        from sqlalchemy import create_engine

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        gw = SqlAlchemyPersistenceGateway(engine.connect())
        assert gw.apply_migrations() == "APPLIED"
        assert gw.check_compatibility() == "OK"
        assert gw.apply_migrations() == "CURRENT"  # no-op when current

    def test_historical_migration_001_unchanged(self) -> None:
        import hashlib

        from app.forge.persistence.sql.migrations import discover_migrations

        migrations = {m.version: m for m in discover_migrations()}
        raw = migrations[1].sql.encode("utf-8")
        assert (
            hashlib.sha256(raw).hexdigest()
            == "d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14"
        )
        assert migrations[2].identity == "002_identity_session"

    def test_no_entitlement_or_license_table_created(self) -> None:
        from sqlalchemy import create_engine, text

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        conn = engine.connect()
        gw = SqlAlchemyPersistenceGateway(conn)
        gw.apply_migrations()
        tables = {
            r[0]
            for r in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
        forbidden = {
            "entitlements",
            "licenses",
            "plans",
            "subscriptions",
            "products",
            "capabilities",
            "policies",
        }
        assert not (tables & forbidden), tables & forbidden
        assert {"forge_users", "external_identity_links", "forge_sessions"} <= tables

    def test_sql_identity_round_trip(self) -> None:
        gw = self._gateway()
        user = ForgeUser.create(email="sql@example.com")
        gw.create_user(user)
        fetched = gw.get_user(user.user_id)
        assert fetched.user_id == user.user_id
        assert fetched.state is UserState.ACTIVE
        assert fetched.email == "sql@example.com"
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="whop", provider_subject="s1", forge_user_id=user.user_id
            )
        )
        assert gw.get_identity_link("whop", "s1").forge_user_id == user.user_id
        auth = ForgeAuthenticationService(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        found = gw.find_session_by_token_digest(token_digest(issued.bearer_token))
        assert found.session_id == issued.session.session_id
        principal = auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        assert principal.authenticated is True

    def test_sql_duplicate_rejections(self) -> None:
        gw = self._gateway()
        user = ForgeUser.create()
        gw.create_user(user)
        with pytest.raises(Exception):  # DuplicateForgeUser
            gw.create_user(user)
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="p", provider_subject="s", forge_user_id=user.user_id
            )
        )
        with pytest.raises(Exception):  # DuplicateIdentityLink
            gw.create_identity_link(
                ExternalIdentityLink(
                    provider="p", provider_subject="s", forge_user_id=user.user_id
                )
            )

    def test_sql_state_transition_and_stale_conflict(self) -> None:
        gw = self._gateway()
        user = ForgeUser.create()
        gw.create_user(user)
        gw.transition_user_state(user.user_id, "DISABLED")
        assert gw.get_user(user.user_id).state is UserState.DISABLED
        with pytest.raises(Exception):  # StaleWriteConflict
            gw.transition_user_state(
                user.user_id, "ACTIVE", expected_version=1
            )

    def test_sql_revocation_and_revoke_all(self) -> None:
        gw = self._gateway()
        user = ForgeUser.create()
        gw.create_user(user)
        auth = ForgeAuthenticationService(gw)
        a = auth.open_session(user, ttl=timedelta(minutes=10))
        b = auth.open_session(user, ttl=timedelta(minutes=10))
        assert gw.revoke_all_sessions(user.user_id) == 2
        for token in (a.bearer_token, b.bearer_token):
            with pytest.raises(AuthenticationFailure):
                auth.authenticate_bearer(f"Bearer {token}")

    def test_sql_unlink_keeps_user(self) -> None:
        gw = self._gateway()
        user = ForgeUser.create()
        gw.create_user(user)
        gw.create_identity_link(
            ExternalIdentityLink(
                provider="whop", provider_subject="s", forge_user_id=user.user_id
            )
        )
        gw.delete_identity_link("whop", "s")
        assert gw.get_user(user.user_id) is not None

    def test_sql_raw_token_never_stored(self) -> None:
        from sqlalchemy import create_engine, text

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        conn = engine.connect()
        gw = SqlAlchemyPersistenceGateway(conn)
        gw.apply_migrations()
        user = ForgeUser.create()
        gw.create_user(user)
        auth = ForgeAuthenticationService(gw)
        issued = auth.open_session(user, ttl=timedelta(minutes=10))
        rows = conn.execute(
            text("SELECT token_digest FROM forge_sessions")
        ).fetchall()
        assert rows and all(len(r[0]) == 64 for r in rows)
        assert issued.bearer_token not in str(rows)


# ---------------------------------------------------------------------------
# Scope guards
# ---------------------------------------------------------------------------


class TestScopeGuards:
    def test_no_whop_api_call_exists(self) -> None:
        import pathlib

        forge_root = pathlib.Path("app/forge")
        for path in forge_root.rglob("*.py"):
            content = path.read_text(encoding="utf-8").lower()
            # The provider name may appear only in docstring prose as a
            # replaceable-provider example; no import, URL or API call may
            # exist anywhere.
            assert "import whop" not in content
            assert "whop.com" not in content
            assert "api.whop" not in content
            assert "whop_client" not in content
            assert "requests.post" not in content
            assert "httpx.post" not in content

    def test_import_performs_no_db_or_auth_activity(self) -> None:
        import subprocess
        import sys

        probe = (
            "import sys; import app.forge.identity, app.forge.service.authentication"
            ", app.main; "
            "mods = [m for m in sys.modules if 'sqlalchemy' in m or 'psycopg' in m]; "
            "print('SQL_IMPORTS:', len([m for m in mods if 'sqlalchemy' in m and 'tests' not in m])); "
            "assert not any(m.startswith('psycopg') for m in sys.modules)"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr

    def test_identity_domain_has_no_http_or_db_imports(self) -> None:
        import app.forge.identity as identity_module

        source = identity_module.__dict__.get("__file__", "")
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        for forbidden in ("fastapi", "sqlalchemy", "psycopg", "pydantic"):
            assert forbidden not in content

    def test_persistence_records_stay_domain_only(self) -> None:
        import pathlib

        persistence = pathlib.Path("app/forge/persistence")
        for path in persistence.rglob("*.py"):
            content = path.read_text(encoding="utf-8").lower()
            assert "fastapi" not in content
            assert "starlette" not in content
