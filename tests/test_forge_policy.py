"""Focused II.4 tests: policy kernel, exposure matrix, enforcement boundary,
adversarial extraction and internal-exposure suites (Book II / Bloc II.4).

Covers ACCEPTANCE.md clauses A–Z executable without external infrastructure.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import fields

import pytest

from app.forge.canonical import ProductExposure
from app.forge.identity import (
    ANONYMOUS_PRINCIPAL,
    ForgePrincipal,
    IdentityRole,
)
from app.forge.policy import (
    CAPABILITY_ADMIN_COMMERCE,
    CAPABILITY_ADMIN_RESEARCH,
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_CORPUS_READ_PUBLIC,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_FORGE_INTERNAL,
    CAPABILITY_MODEL_READ_OPERATOR,
    REGISTERED_CAPABILITIES,
    AuthorizationContext,
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyDecision,
    PolicyReason,
    PolicyResourceType,
    ResourcePolicyMetadata,
    is_well_formed,
)
from app.forge.service.policy_enforcement import (
    ForgePolicyEnforcementService,
    GuardedAccess,
    PolicyAuditRecord,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ANON = ANONYMOUS_PRINCIPAL
AUTH = ForgePrincipal(authenticated=True, forge_user_id="user-1", session_id=None)
NO_CAP = AuthorizationContext.empty()
PUBLIC = AuthorizationContext.of(CAPABILITY_CORPUS_READ_PUBLIC)
MEMBER = AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER)
OPERATOR = AuthorizationContext.of(CAPABILITY_MODEL_READ_OPERATOR)
RESEARCH = AuthorizationContext.of(CAPABILITY_EVIDENCE_READ_RESEARCH)
ADMIN = AuthorizationContext.of(CAPABILITY_ADMIN_RESEARCH, CAPABILITY_ADMIN_COMMERCE)
INTERNAL = AuthorizationContext.of(CAPABILITY_FORGE_INTERNAL)
ALL_ORDINARY = AuthorizationContext.of(
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_MODEL_READ_OPERATOR,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
)

ENGINE = DefaultDenyPolicyEngine()


def _res(exposure) -> ResourcePolicyMetadata:
    return ResourcePolicyMetadata(
        PolicyResourceType.CANONICAL_OBJECT, "MOD.TEST.X", exposure
    )


def decide(principal, context, action, exposure) -> PolicyDecision:
    return ENGINE.decide(principal, context, action, _res(exposure))


def allowed(principal, context, action, exposure) -> bool:
    return decide(principal, context, action, exposure).allowed


# ---------------------------------------------------------------------------
# A/B/C — decision structure, actions, resources
# ---------------------------------------------------------------------------


class TestPolicyDecisionStructure:
    def test_deterministic_allow(self) -> None:
        d = decide(AUTH, MEMBER, PolicyAction.VIEW, ProductExposure.SUBSCRIBER_MODEL)
        assert d.allowed is True
        assert d.reason_code == PolicyReason.GRANTED

    def test_deterministic_deny(self) -> None:
        d = decide(ANON, NO_CAP, PolicyAction.VIEW, ProductExposure.SUBSCRIBER_MODEL)
        assert d.allowed is False
        assert d.reason_code == PolicyReason.NOT_AUTHENTICATED

    def test_structured_reason_code_and_value_equality(self) -> None:
        a1 = decide(AUTH, MEMBER, PolicyAction.VIEW, ProductExposure.SUBSCRIBER_MODEL)
        a2 = decide(AUTH, MEMBER, PolicyAction.VIEW, ProductExposure.SUBSCRIBER_MODEL)
        assert a1 == a2  # same trusted inputs => same decision
        assert isinstance(a1.reason_code, PolicyReason)
        assert isinstance(a1.detail, str)

    def test_decision_contains_no_protected_content(self) -> None:
        secret = "CLASSIFIED-BODY-STRING-0123456789"
        d = decide(AUTH, MEMBER, PolicyAction.VIEW, ProductExposure.SUBSCRIBER_MODEL)
        assert secret not in str(d)
        d2 = decide(ANON, NO_CAP, PolicyAction.VIEW, ProductExposure.INTERNAL_CODE)
        assert secret not in str(d2)


class TestActionsAndResources:
    def test_governed_actions_only(self) -> None:
        assert {a.value for a in PolicyAction} == {
            "VIEW",
            "QUERY",
            "OPERATE",
            "ADMINISTER",
        }

    def test_unknown_action_denied(self) -> None:
        d = decide(ANON, NO_CAP, "EXECUTE_ARBITRARY", ProductExposure.PUBLIC_TEACHING)
        assert d.allowed is False
        assert d.reason_code == PolicyReason.UNKNOWN_ACTION

    def test_resource_metadata_is_body_free(self) -> None:
        names = {f.name for f in fields(ResourcePolicyMetadata)}
        assert names == {"resource_type", "resource_id", "exposure"}

    def test_resource_type_bounded(self) -> None:
        with pytest.raises(ValueError):
            ResourcePolicyMetadata("NOT_A_TYPE", "x", ProductExposure.PUBLIC_TEACHING)
        with pytest.raises(ValueError):
            ResourcePolicyMetadata(PolicyResourceType.CANONICAL_OBJECT, "", None)

    def test_unknown_resource_type_denies(self) -> None:
        # a well-formed engine refuses a malformed metadata object outright
        d = ENGINE.decide(
            AUTH, MEMBER, PolicyAction.VIEW, ("bogus", "x", "PUBLIC_TEACHING")
        )
        assert d.allowed is False


# ---------------------------------------------------------------------------
# E — authorization context seam
# ---------------------------------------------------------------------------


class TestAuthorizationContext:
    def test_context_shape_is_capability_facts_only(self) -> None:
        names = {f.name for f in fields(AuthorizationContext)}
        assert names == {"capabilities"}

    def test_no_commercial_fields_anywhere(self) -> None:
        forbidden = {
            "plan",
            "subscription",
            "price",
            "billing",
            "license",
            "whop",
            "tier",
        }
        for cls in (AuthorizationContext, ResourcePolicyMetadata, PolicyDecision):
            names = {f.name for f in fields(cls)}
            assert not (names & forbidden)

    def test_capability_atoms_exact_match(self) -> None:
        ctx = AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER)
        assert ctx.has(CAPABILITY_CORPUS_READ_MEMBER)
        assert not ctx.has("corpus.read")
        assert not ctx.has("corpus.read.member.extra")
        assert not ctx.has("*")
        assert not ctx.has("")

    def test_wildcards_and_substrings_grant_nothing(self) -> None:
        fake = AuthorizationContext.of(
            "corpus.read", "corpus.read.member.*", "*", "forge.intern", "forge.internal/x"
        )
        assert not allowed(AUTH, fake, "VIEW", ProductExposure.SUBSCRIBER_MODEL)
        assert not allowed(AUTH, fake, "VIEW", ProductExposure.INTERNAL_METHOD)

    def test_malformed_context_denies(self) -> None:
        d = ENGINE.decide(AUTH, "garbage", PolicyAction.VIEW, _res(ProductExposure.PUBLIC_TEACHING))
        assert d.reason_code == PolicyReason.MALFORMED_CONTEXT
        d2 = ENGINE.decide(AUTH, None, PolicyAction.VIEW, _res(ProductExposure.PUBLIC_TEACHING))
        assert d2.reason_code == PolicyReason.MALFORMED_CONTEXT
        assert not is_well_formed(object())
        with pytest.raises(ValueError):
            AuthorizationContext(capabilities="corpus.read.member")  # type: ignore[arg-type]

    def test_missing_context_denies_protected_resource(self) -> None:
        assert not allowed(AUTH, NO_CAP, "VIEW", ProductExposure.SUBSCRIBER_MODEL)
        assert not allowed(AUTH, None, "VIEW", ProductExposure.SUBSCRIBER_MODEL)


# ---------------------------------------------------------------------------
# F–L — the exposure matrix (table-driven)
# ---------------------------------------------------------------------------


class TestExposureMatrix:
    @pytest.mark.parametrize(
        ("principal", "context", "exposure", "action", "expected"),
        [
            # PUBLIC_TEACHING
            (ANON, NO_CAP, ProductExposure.PUBLIC_TEACHING, "VIEW", True),
            (ANON, NO_CAP, ProductExposure.PUBLIC_TEACHING, "QUERY", True),
            (ANON, NO_CAP, ProductExposure.PUBLIC_TEACHING, "OPERATE", False),
            (ANON, NO_CAP, ProductExposure.PUBLIC_TEACHING, "ADMINISTER", False),
            (AUTH, NO_CAP, ProductExposure.PUBLIC_TEACHING, "VIEW", True),
            (AUTH, MEMBER, ProductExposure.PUBLIC_TEACHING, "VIEW", True),
            # SUBSCRIBER_MODEL
            (ANON, NO_CAP, ProductExposure.SUBSCRIBER_MODEL, "VIEW", False),
            (AUTH, NO_CAP, ProductExposure.SUBSCRIBER_MODEL, "VIEW", False),
            (AUTH, PUBLIC, ProductExposure.SUBSCRIBER_MODEL, "VIEW", False),
            (AUTH, MEMBER, ProductExposure.SUBSCRIBER_MODEL, "VIEW", True),
            (AUTH, OPERATOR, ProductExposure.SUBSCRIBER_MODEL, "VIEW", True),
            (AUTH, RESEARCH, ProductExposure.SUBSCRIBER_MODEL, "VIEW", True),
            # OPERATOR_ONLY
            (ANON, NO_CAP, ProductExposure.OPERATOR_ONLY, "VIEW", False),
            (AUTH, NO_CAP, ProductExposure.OPERATOR_ONLY, "VIEW", False),
            (AUTH, MEMBER, ProductExposure.OPERATOR_ONLY, "VIEW", False),
            (AUTH, OPERATOR, ProductExposure.OPERATOR_ONLY, "VIEW", True),
            (AUTH, RESEARCH, ProductExposure.OPERATOR_ONLY, "VIEW", True),
            # RESEARCH_LAB
            (ANON, NO_CAP, ProductExposure.RESEARCH_LAB, "VIEW", False),
            (AUTH, NO_CAP, ProductExposure.RESEARCH_LAB, "VIEW", False),
            (AUTH, MEMBER, ProductExposure.RESEARCH_LAB, "VIEW", False),
            (AUTH, OPERATOR, ProductExposure.RESEARCH_LAB, "VIEW", True),
            (AUTH, RESEARCH, ProductExposure.RESEARCH_LAB, "VIEW", True),
            # INTERNAL_METHOD
            (ANON, NO_CAP, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, NO_CAP, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, MEMBER, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, OPERATOR, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, RESEARCH, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, ALL_ORDINARY, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, ADMIN, ProductExposure.INTERNAL_METHOD, "VIEW", False),
            (AUTH, INTERNAL, ProductExposure.INTERNAL_METHOD, "VIEW", True),
            # INTERNAL_CODE
            (ANON, NO_CAP, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, NO_CAP, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, MEMBER, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, OPERATOR, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, RESEARCH, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, ALL_ORDINARY, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, ADMIN, ProductExposure.INTERNAL_CODE, "VIEW", False),
            (AUTH, INTERNAL, ProductExposure.INTERNAL_CODE, "VIEW", True),
        ],
    )
    def test_matrix(
        self, principal, context, exposure, action, expected
    ) -> None:
        d = decide(principal, context, action, exposure)
        assert d.allowed is expected, (principal, context, exposure, action, d)

    def test_internal_reason_code(self) -> None:
        d = decide(AUTH, MEMBER, "VIEW", ProductExposure.INTERNAL_METHOD)
        assert d.reason_code == PolicyReason.EXPOSURE_FORBIDDEN

    def test_subscriber_reason_code_missing_capability(self) -> None:
        d = decide(AUTH, NO_CAP, "VIEW", ProductExposure.SUBSCRIBER_MODEL)
        assert d.reason_code == PolicyReason.ENTITLEMENT_MISSING

    def test_unknown_exposure_denies_and_never_coerces(self) -> None:
        d = ENGINE.decide(
            AUTH, MEMBER, "VIEW",
            ResourcePolicyMetadata(PolicyResourceType.CANONICAL_OBJECT, "x", None),
        )
        assert d.allowed is False
        assert d.reason_code == PolicyReason.UNKNOWN_EXPOSURE
        d2 = ENGINE.decide(
            AUTH, MEMBER, "VIEW",
            ResourcePolicyMetadata(PolicyResourceType.CANONICAL_OBJECT, "x", "PREMIUM"),
        )
        assert d2.allowed is False

    def test_anonymous_only_public_teaching(self) -> None:
        for exposure in ProductExposure:
            if exposure is ProductExposure.PUBLIC_TEACHING:
                continue
            assert not allowed(ANON, NO_CAP, "VIEW", exposure), exposure


# ---------------------------------------------------------------------------
# I — research law: authorization never mutates status
# ---------------------------------------------------------------------------


class TestResearchLaw:
    def test_research_access_does_not_mutate_evidence_status(self) -> None:
        from app.forge.canonical import EvidenceStatus

        # deciding on a research object cannot change any status vocabulary:
        # the kernel holds no status mutation API at all
        d = decide(AUTH, RESEARCH, "VIEW", ProductExposure.RESEARCH_LAB)
        assert d.allowed
        assert EvidenceStatus.CANDIDATE.value == "CANDIDATE"
        assert EvidenceStatus.VALIDATED.value == "VALIDATED"
        # the decision carries no promoted status field
        names = {f.name for f in fields(PolicyDecision)}
        assert names == {"allowed", "reason_code", "detail"}

    def test_authorization_pure_over_domain_objects(self) -> None:
        # repeated decisions do not change anything engine- or object-side
        r = _res(ProductExposure.RESEARCH_LAB)
        d1 = ENGINE.decide(AUTH, RESEARCH, "VIEW", r)
        d2 = ENGINE.decide(AUTH, RESEARCH, "VIEW", r)
        assert d1 == d2 and d1.allowed


# ---------------------------------------------------------------------------
# O — provider/request data cannot grant access
# ---------------------------------------------------------------------------


class TestProviderDataHasNoAuthority:
    def test_provider_subject_whop_id_email_grant_nothing(self) -> None:
        fake = AuthorizationContext.of(
            "whop-customer-000123",  # provider subject as capability atom
            "user@example.com",  # email as capability atom
            "cs_9x8y7z",
            "USER",  # identity role as capability atom
        )
        for exposure in (
            ProductExposure.SUBSCRIBER_MODEL,
            ProductExposure.OPERATOR_ONLY,
            ProductExposure.INTERNAL_METHOD,
            ProductExposure.INTERNAL_CODE,
        ):
            assert not allowed(AUTH, fake, "VIEW", exposure), exposure

    def test_role_is_not_a_capability(self) -> None:
        roles = AuthorizationContext.of(*(role.value for role in IdentityRole))
        assert not allowed(AUTH, roles, "VIEW", ProductExposure.SUBSCRIBER_MODEL)
        assert not allowed(AUTH, roles, "VIEW", ProductExposure.INTERNAL_METHOD)

    def test_admin_capabilities_do_not_open_internal_classes(self) -> None:
        assert not allowed(AUTH, ADMIN, "VIEW", ProductExposure.INTERNAL_METHOD)
        assert not allowed(AUTH, ADMIN, "VIEW", ProductExposure.INTERNAL_CODE)
        assert not allowed(AUTH, ADMIN, "ADMINISTER", ProductExposure.SUBSCRIBER_MODEL)


# ---------------------------------------------------------------------------
# P/Q — pre-retrieval enforcement
# ---------------------------------------------------------------------------


class SpyLoader:
    def __init__(self, body: str = "PROTECTED-BODY-CONTENT") -> None:
        self.calls: list[tuple] = []
        self.body = body

    def __call__(self, resource_id: str, *args):
        self.calls.append((resource_id, args))
        return {"body": self.body, "id": resource_id}


class TestPreRetrievalEnforcement:
    def test_deny_never_invokes_loader(self) -> None:
        svc = ForgePolicyEnforcementService()
        loader = SpyLoader()
        out = svc.guard(
            AUTH, NO_CAP, "VIEW", _res(ProductExposure.SUBSCRIBER_MODEL), loader, "MOD.X"
        )
        assert out.allowed is False
        assert out.payload is None
        assert loader.calls == []

    def test_allow_invokes_loader_exactly_once(self) -> None:
        svc = ForgePolicyEnforcementService()
        loader = SpyLoader()
        out = svc.guard(
            AUTH, MEMBER, "VIEW", _res(ProductExposure.SUBSCRIBER_MODEL), loader, "MOD.X"
        )
        assert out.allowed is True
        assert len(loader.calls) == 1
        assert out.payload["id"] == "MOD.X"

    def test_denied_loader_result_cannot_leak_body(self) -> None:
        svc = ForgePolicyEnforcementService()
        loader = SpyLoader(body="INTERNAL-CODE-SECRET")
        out = svc.guard(
            AUTH, NO_CAP, "VIEW", _res(ProductExposure.INTERNAL_CODE), loader, "SRC.X"
        )
        assert out.allowed is False
        assert out.payload is None
        assert "INTERNAL-CODE-SECRET" not in str(out)
        assert loader.calls == []

    def test_adversarial_extraction_varying_requests(self) -> None:
        """The critical extraction test: a principal lacking authorization
        varies id/type/exposure/action/wording — the loader must NEVER run."""

        svc = ForgePolicyEnforcementService()
        loader = SpyLoader()
        attempts = 0
        public_loads_expected = 0
        for resource_id in ("MOD.A", "MOD.B", "CLM.C", "SRC.D", "../etc/passwd", "MOD.A?ver=2"):
            for rtype in PolicyResourceType:
                for exposure in list(ProductExposure) + [None]:
                    for action in ("VIEW", "QUERY", "READ", "list", "view ", "VIEW;"):
                        res = ResourcePolicyMetadata(rtype, resource_id, exposure)
                        out = svc.guard(AUTH, NO_CAP, action, res, loader, resource_id)
                        attempts += 1
                        if out.allowed:
                            # only the explicitly-public class may ever load
                            assert exposure is ProductExposure.PUBLIC_TEACHING, (
                                rtype, resource_id, exposure, action
                            )
                            assert action in ("VIEW", "QUERY")
                            public_loads_expected += 1
                        else:
                            assert out.payload is None
        # no protected load happened despite the variation barrage: loads
        # correspond exactly to the legitimate public-teaching allows
        assert len(loader.calls) == public_loads_expected
        assert attempts >= 100
        assert len(loader.calls) < attempts  # most attempts never loaded

    def test_pre_llm_boundary_seam_is_reusable(self) -> None:
        """The guard composes around any loader — the future Ask CEREBUS
        boundary is 'policy before the loader that feeds LLM context'."""

        svc = ForgePolicyEnforcementService()

        def fake_retrieval_loader(query: str) -> list[str]:
            return [f"chunk-for:{query}"]  # would enter an LLM context

        denied = svc.guard(
            ANON, NO_CAP, "QUERY",
            ResourcePolicyMetadata(PolicyResourceType.CANONICAL_OBJECT, "q", ProductExposure.SUBSCRIBER_MODEL),
            fake_retrieval_loader, "operator triggers",
        )
        assert denied.allowed is False and denied.payload is None
        permitted = svc.guard(
            AUTH, MEMBER, "QUERY",
            ResourcePolicyMetadata(PolicyResourceType.CANONICAL_OBJECT, "q", ProductExposure.SUBSCRIBER_MODEL),
            fake_retrieval_loader, "beginner concepts",
        )
        assert permitted.allowed is True
        assert permitted.payload == ["chunk-for:beginner concepts"]


# ---------------------------------------------------------------------------
# II.3 integration — auth failures never reach the loader
# ---------------------------------------------------------------------------


class TestAuthenticationIntegration:
    def test_invalid_token_cannot_reach_policy_as_authenticated(self) -> None:
        from app.forge.persistence.memory import InMemoryPersistenceGateway
        from app.forge.service.authentication import (
            AuthenticationFailure,
            ForgeAuthenticationService,
        )

        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw)
        with pytest.raises(AuthenticationFailure):
            principal = auth.authenticate_bearer("Bearer bogus", allow_anonymous=False)
            svc = ForgePolicyEnforcementService()
            svc.guard(
                principal, MEMBER, "VIEW",
                _res(ProductExposure.SUBSCRIBER_MODEL), SpyLoader(), "MOD.X"
            )

    def _blocked_before_loader(self, credential: str | None) -> None:
        from datetime import timedelta

        from app.forge.persistence.memory import InMemoryPersistenceGateway
        from app.forge.service.authentication import (
            AuthenticationFailure,
            ForgeAuthenticationService,
        )

        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw)
        user = ForgeUser_create()
        gw.create_user(user)
        loader = SpyLoader()
        svc = ForgePolicyEnforcementService()
        if credential is None:
            principal = auth.authenticate_bearer(None, allow_anonymous=True)
        else:
            with pytest.raises(AuthenticationFailure):
                principal = auth.authenticate_bearer(credential, allow_anonymous=False)
            return  # auth failure: policy/loader never reached
        out = svc.guard(
            principal, MEMBER, "VIEW", _res(ProductExposure.SUBSCRIBER_MODEL),
            loader, "MOD.X",
        )
        assert loader.calls == []  # anonymous/public-only: protected never loads

    def test_expired_revoked_disabled_never_reach_loader(self) -> None:
        from datetime import timedelta

        from app.forge.persistence.memory import InMemoryPersistenceGateway
        from app.forge.service.authentication import (
            AuthenticationFailure,
            ForgeAuthenticationService,
        )

        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw)
        user = ForgeUser_create()
        gw.create_user(user)
        loader = SpyLoader()
        svc = ForgePolicyEnforcementService()

        # expired
        expired = auth.open_session(user, ttl=timedelta(minutes=-1))
        with pytest.raises(AuthenticationFailure):
            principal = auth.authenticate_bearer(f"Bearer {expired.bearer_token}")
        assert loader.calls == []

        # revoked
        revoked = auth.open_session(user, ttl=timedelta(minutes=5))
        auth.revoke_session(revoked.session.session_id)
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {revoked.bearer_token}")
        assert loader.calls == []

        # disabled user with an otherwise-valid session
        disabled = auth.open_session(user, ttl=timedelta(minutes=5))
        gw.transition_user_state(user.user_id, "DISABLED")
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer(f"Bearer {disabled.bearer_token}")
        assert loader.calls == []

    def test_anonymous_principal_structurally_preserved(self) -> None:
        # policy receives the II.3 singleton unchanged
        svc = ForgePolicyEnforcementService()
        out = svc.guard(
            ANON, NO_CAP, "VIEW", _res(ProductExposure.PUBLIC_TEACHING), SpyLoader(), "T.X"
        )
        assert out.allowed is True  # public teaching is anonymous-readable
        audit = svc.audit_records()[-1]
        assert audit.principal_id == "anonymous"
        assert audit.authenticated is False


def ForgeUser_create():
    from app.forge.identity import ForgeUser

    return ForgeUser.create()


# ---------------------------------------------------------------------------
# R/S — error contract and audit
# ---------------------------------------------------------------------------


class TestErrorAndAuditContract:
    def test_denial_is_structured_not_thrown(self) -> None:
        d = decide(AUTH, NO_CAP, "VIEW", ProductExposure.INTERNAL_METHOD)
        assert isinstance(d, PolicyDecision) and d.allowed is False

    def test_auth_failure_vs_authorization_denial_distinguishable_internally(self) -> None:
        from app.forge.persistence.memory import InMemoryPersistenceGateway
        from app.forge.service.authentication import (
            AuthenticationFailure,
            ForgeAuthenticationService,
        )

        auth = ForgeAuthenticationService(InMemoryPersistenceGateway())
        with pytest.raises(AuthenticationFailure):
            auth.authenticate_bearer("Bearer nope", allow_anonymous=False)
        # authorization denial: a decision, no exception
        d = decide(AUTH, NO_CAP, "VIEW", ProductExposure.SUBSCRIBER_MODEL)
        assert d.reason_code == PolicyReason.ENTITLEMENT_MISSING

    def test_audit_record_shape_and_hygiene(self) -> None:
        svc = ForgePolicyEnforcementService(now=lambda: "2026-10-07T00:00:00+00:00")
        svc.guard(AUTH, MEMBER, "VIEW", _res(ProductExposure.SUBSCRIBER_MODEL), SpyLoader(), "MOD.X")
        svc.guard(AUTH, NO_CAP, "VIEW", _res(ProductExposure.INTERNAL_CODE), SpyLoader(), "SRC.X")
        records = svc.audit_records()
        assert len(records) == 2
        names = {f.name for f in fields(PolicyAuditRecord)}
        assert names == {
            "correlation_id",
            "principal_id",
            "authenticated",
            "action",
            "resource_type",
            "resource_id",
            "exposure",
            "allowed",
            "reason_code",
            "at",
        }
        blob = str(records)
        assert "PROTECTED-BODY-CONTENT" not in blob
        assert "INTERNAL-CODE-SECRET" not in blob
        assert "Bearer " not in blob
        rec = records[0]
        assert rec.principal_id == "user-1"
        assert rec.allowed is True
        assert rec.reason_code == "GRANTED"
        assert records[1].allowed is False
        assert records[1].reason_code == "EXPOSURE_FORBIDDEN"

    def test_correlation_id_preserved_on_denial(self) -> None:
        svc = ForgePolicyEnforcementService()
        out = svc.guard(
            AUTH, NO_CAP, "VIEW", _res(ProductExposure.INTERNAL_METHOD), SpyLoader(), "SRC.Y",
            correlation_id="req-123",
        )
        assert out.allowed is False
        assert svc.audit_records()[-1].correlation_id == "req-123"

    def test_audit_is_bounded(self) -> None:
        svc = ForgePolicyEnforcementService(audit_capacity=5)
        for i in range(20):
            svc.authorize(ANON, NO_CAP, "VIEW", _res(ProductExposure.INTERNAL_METHOD))
        assert len(svc.audit_records()) == 5


# ---------------------------------------------------------------------------
# T — determinism & purity
# ---------------------------------------------------------------------------


class TestPurity:
    def test_no_network_sql_fastapi_in_kernel(self) -> None:
        import pathlib

        source = pathlib.Path("app/forge/policy.py").read_text(encoding="utf-8")
        for forbidden in ("fastapi", "sqlalchemy", "psycopg", "socket", "urllib", "requests", "httpx"):
            assert forbidden not in source

    def test_no_mutable_global_state(self) -> None:
        e1 = DefaultDenyPolicyEngine()
        e2 = DefaultDenyPolicyEngine()
        r = _res(ProductExposure.SUBSCRIBER_MODEL)
        d1 = e1.decide(AUTH, MEMBER, "VIEW", r)
        d2 = e2.decide(ANON, NO_CAP, "VIEW", r)
        assert d1.allowed is True and d2.allowed is False
        # instances do not influence each other
        d3 = e1.decide(ANON, NO_CAP, "VIEW", r)
        assert d3.allowed is False
        assert d1 == e1.decide(AUTH, MEMBER, "VIEW", r)

    def test_no_network_call_in_decision(self) -> None:
        # a socket-using guard proves decide() performs no I/O
        import socket

        original = socket.socket
        try:
            socket.socket = lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("policy engine attempted network I/O")
            )
            d = decide(AUTH, MEMBER, "VIEW", ProductExposure.SUBSCRIBER_MODEL)
            assert d.allowed
        finally:
            socket.socket = original


# ---------------------------------------------------------------------------
# U/V/X — persistence, HTTP scope, commercial leak
# ---------------------------------------------------------------------------


class TestScopeGuards:
    def test_no_new_migration(self) -> None:
        from app.forge.persistence.sql.migrations import discover_migrations

        # Exact authorized set: 001/002 (historical) + 003_vector_projection
        # (Book II closure repair, operator-authorized — see
        # implementation/forge/book_ii/closure_repair/PLAN.md). Still a pin:
        # any further migration fails here without its own authorization.
        assert [m.version for m in discover_migrations()] == [1, 2, 3]

    def test_001_and_002_unchanged(self) -> None:
        import hashlib
        import pathlib

        raw001 = pathlib.Path(
            "app/forge/persistence/sql/001_initial_schema.sql"
        ).read_bytes()
        assert hashlib.sha256(raw001).hexdigest() == (
            "d91c2ea2ec45de5f89f64b56acab80316339f68a53fd28a88c3c7ea0b7662f14"
        )
        from app.forge.persistence.sql.migrations import discover_migrations

        identities = {m.version: m.identity for m in discover_migrations()}
        assert identities == {
            1: "001_initial_schema",
            2: "002_identity_session",
            3: "003_vector_projection",
        }

    def test_no_policy_or_audit_tables(self) -> None:
        from sqlalchemy import create_engine, text

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        conn = create_engine("sqlite://").connect()
        gw = SqlAlchemyPersistenceGateway(conn)
        gw.apply_migrations()
        tables = {
            r[0]
            for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        assert not (tables & {"policies", "policy_decisions", "policy_audit", "audit_log"})

    def test_no_new_public_route(self) -> None:
        from app.main import app

        forge_paths = {
            getattr(route, "path", "") for route in app.router.routes
        } - {""}
        assert {p for p in forge_paths if "/forge/" in p} == {
            "/forge/v1/health",
            "/forge/v1/ready",
            "/forge/v1/meta",
        }
        for path in forge_paths:
            for marker in ("/users", "/sessions", "/admin", "/licenses", "/corpus", "/objects", "/entitlements"):
                assert marker not in path, path

    def test_health_ready_meta_unchanged(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            assert client.get("/forge/v1/health").status_code == 200
            ready = client.get("/forge/v1/ready").json()
            assert ready["status"] == "ready"
            assert "identity" not in ready["dependencies"]
            meta = client.get("/forge/v1/meta").json()
            assert meta["service"] == "glx-forge"

    def test_no_commercial_domain_objects(self) -> None:
        import app.forge.policy as policy_module

        exported = set(getattr(policy_module, "__all__", []))
        for name in ("Plan", "Subscription", "License", "WhopCustomer", "BillingStatus", "Price"):
            assert name not in exported
        source = policy_module.__dict__["__file__"]
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        for atom in ('"FREE"', '"PRO"', '"PREMIUM"', '"free"', '"premium"'):
            assert atom not in content

    def test_no_whop_integration(self) -> None:
        import pathlib

        for path in list(pathlib.Path("app/forge").rglob("*.py")):
            content = path.read_text(encoding="utf-8").lower()
            assert "import whop" not in content
            assert "whop.com" not in content
            assert "api.whop" not in content

    def test_container_accepts_policy_engine(self) -> None:
        from app.forge.service.container import ForgeServiceContainer
        from app.forge.config import forge_config_from_values

        container = ForgeServiceContainer(
            config=forge_config_from_values(), policy=DefaultDenyPolicyEngine()
        )
        assert container.policy is not None
        assert container.redacted_diagnostics()["policy_wired"] is True
        with pytest.raises(TypeError):
            ForgeServiceContainer(
                config=forge_config_from_values(), policy="bogus"  # type: ignore[arg-type]
            )
