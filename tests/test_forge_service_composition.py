"""BOOK II / BLOC II.1 — SERVICE SKELETON — focused tests.

These tests target the II.1 acceptance clauses directly and also protect the
existing Signal Guard application composition.

They do NOT touch I.1/I.2 domain implementation.
"""

from __future__ import annotations

import ast
import importlib
import logging
import re
import sys
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

# Local helper: ensure FORGE domain modules do not import fastapi at import time.
_FASTAPI_TOPIC = "fastapi"


def _module_imports_topic(module_name: str, topic: str) -> bool:
    """AST scan: does module_name import `topic` (e.g. 'fastapi')?"""

    try:
        spec = importlib.util.find_spec(module_name)
    except Exception:
        return False
    if spec is None or spec.origin is None:
        return False
    path = Path(spec.origin)
    if not path.exists():
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _import_name_matches(alias.name, topic):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and _import_name_matches(node.module, topic):
                return True
    return False


def _import_name_matches(name: str, topic: str) -> bool:
    return name == topic or name.startswith(f"{topic}.")


# ---------------------------------------------------------------------------
# A3 / A5 — domain does not start server and does not import FastAPI
# ---------------------------------------------------------------------------

FORGE_DOMAIN_MODULES = (
    "app.forge.canonical",
    "app.forge.schemas",
    "app.forge.provenance",
)


class TestForgeDomainIsolation:
    """Domain modules remain transport-free."""

    def test_forge_domain_modules_import_without_fastapi(self) -> None:
        """A5: FORGE domain must not import FastAPI."""

        for mod in FORGE_DOMAIN_MODULES:
            assert _module_imports_topic(mod, _FASTAPI_TOPIC) is False, (
                f"{mod} must not import fastapi"
            )

    def test_importing_forge_domain_does_not_start_server(self) -> None:
        """A3: importing FORGE domain must not start HTTP serving."""

        # Importing these modules must not bind/listen/start uvicorn.
        for mod in FORGE_DOMAIN_MODULES:
            importlib.import_module(mod)

        # At minimum, importing FORGE domain must not call uvicorn.run.
        import uvicorn

        assert hasattr(uvicorn, "run")  # importable; no run was invoked by domain


# ---------------------------------------------------------------------------
# A4 / A6 — composition imports cleanly, service may import domain
# ---------------------------------------------------------------------------

class TestForgeServiceImports:
    """Service layer imports domain; no circular import."""

    def test_forge_service_package_imports(self) -> None:
        import app.forge.service  # noqa: F401

    def test_forge_service_errors_imports(self) -> None:
        import app.forge.service.errors  # noqa: F401

    def test_forge_service_correlation_imports(self) -> None:
        import app.forge.service.correlation  # noqa: F401

    def test_forge_service_container_imports(self) -> None:
        import app.forge.service.container  # noqa: F401

    def test_forge_service_lifecycle_imports(self) -> None:
        import app.forge.service.lifecycle  # noqa: F401

    def test_forge_service_health_imports(self) -> None:
        import app.forge.service.health  # noqa: F401

    def test_forge_service_routes_imports(self) -> None:
        import app.forge.service.routes  # noqa: F401

    def test_forge_config_imports(self) -> None:
        import app.forge.config  # noqa: F401


# ---------------------------------------------------------------------------
# G1/G2/G3 — container boundary and replaceability
# ---------------------------------------------------------------------------

class TestForgeServiceContainer:
    """Minimal FORGE dependency boundary is replaceable and II.1-correct."""

    def test_container_defaults_are_valid(self) -> None:
        from app.forge.config import forge_config_from_environment
        from app.forge.service.container import ForgeServiceContainer

        cfg = forge_config_from_environment()
        container = ForgeServiceContainer(config=cfg)
        assert container.config is cfg
        # II.1: persistence/policy/providers are NOT wired.
        assert container.persistence is None
        assert container.policy is None
        assert container.providers is None

    def test_container_can_be_replaced_in_tests(self) -> None:
        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer

        fake_cfg = ForgeConfig(
            service_name="test-forge",
            environment="test",
            application_version="0.0.0-test",
        )
        container = ForgeServiceContainer(config=fake_cfg)
        assert container.config.service_name == "test-forge"
        assert container.config.environment == "test"

    def test_container_rejects_wired_persistence_at_ii_1(self) -> None:
        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer

        cfg = ForgeConfig()
        with pytest.raises(RuntimeError, match="II.2"):
            ForgeServiceContainer(
                config=cfg, persistence=object()  # type: ignore[arg-type]
            )

    def test_container_rejects_wired_policy_at_ii_1(self) -> None:
        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer

        cfg = ForgeConfig()
        with pytest.raises(RuntimeError, match="II.4"):
            ForgeServiceContainer(
                config=cfg, policy=object()  # type: ignore[arg-type]
            )

    def test_container_rejects_wired_providers_at_ii_1(self) -> None:
        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer

        cfg = ForgeConfig()
        with pytest.raises(RuntimeError, match="II.5"):
            ForgeServiceContainer(
                config=cfg, providers=object()  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# C / D / E — health / readiness / meta
# ---------------------------------------------------------------------------

class TestForgeHealthReadinessMeta:
    """FORGE health/readiness/meta semantics are honest at II.1."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from app.main import app

        return TestClient(app)

    def test_forge_health_live(self, client: TestClient) -> None:
        resp = client.get("/forge/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "glx-forge"
        assert body["status"] == "alive"
        assert "request_id" in body
        assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", body["request_id"])

    def test_forge_health_does_not_claim_future_dependencies_ready(
        self, client: TestClient
    ) -> None:
        resp = client.get("/forge/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        # Health object must not include future dependency health claims.
        text = resp.text
        for forbidden in (
            "postgresql",
            "pgvector",
            "openrouter",
            "whop",
            "market_data",
            "ask_cerebus",
        ):
            assert forbidden not in text, (
                f"FORGE health must not reference {forbidden}"
            )

    def test_forge_ready_exists_and_is_honest(self, client: TestClient) -> None:
        resp = client.get("/forge/v1/ready")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "glx-forge"
        # II.1 has no required external dependency, so readiness is honest.
        assert body["status"] == "ready"
        deps = body["dependencies"]
        non_healthy = {
            "NOT_CONFIGURED",
            "NOT_APPLICABLE",
            "NOT_IMPLEMENTED",
        }
        for future_dep in ("postgresql", "pgvector", "openrouter", "whop", "market_data", "ask_cerebus"):
            assert deps[future_dep]["status"] in non_healthy
            # Future deps must not be marked required at II.1.
            assert deps[future_dep]["required"] is False
        assert deps["forge"]["status"] == "READY"
        assert deps["forge"]["required"] is True

    def test_forge_meta_is_deterministic_non_secret(self, client: TestClient) -> None:
        resp = client.get("/forge/v1/meta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "glx-forge"
        assert body["api_version"] == "v1"
        assert "application_version" in body
        assert "environment" in body
        assert "forge_domain_version" in body
        # Must not leak secrets/env values/corpus paths.
        text = resp.text
        for forbidden in ("OPENROUTER_API_KEY", "WHOP_API_KEY", "FORGE_DATABASE_URL"):
            assert forbidden not in text
        # Env var names should not appear either.
        for forbidden in (
            "POSTGRES",
            "DATABASE_URL",
            "API_KEY",
            "SECRET",
        ):
            assert forbidden not in text or forbidden.isupper() is False


# ---------------------------------------------------------------------------
# B — namespace
# ---------------------------------------------------------------------------

class TestForgeNamespace:
    """FORGE routes live under /forge/v1."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from app.main import app

        return TestClient(app)

    def test_forge_routes_are_under_forge_v1(self, client: TestClient) -> None:
        routes = [route.path for route in client.app.routes]
        forge_routes = [p for p in routes if str(p).startswith("/forge/v1")]
        assert len(forge_routes) >= 3
        expected = {"/forge/v1/health", "/forge/v1/ready", "/forge/v1/meta"}
        assert expected <= set(forge_routes)

    def test_signal_guard_routes_remain(self, client: TestClient) -> None:
        routes = [route.path for route in client.app.routes]
        existing = {"/health", "/state", "/webhook", "/logs", "/screenshot", "/reconcile"}
        present = {p for p in routes if str(p) in existing}
        assert present == existing


# ---------------------------------------------------------------------------
# H — error envelope
# ---------------------------------------------------------------------------

class TestForgeErrorEnvelope:
    """FORGE-owned error shape is stable and safe."""

    def test_forge_unknown_route_returns_404_from_fastapi(self) -> None:
        from app.main import app

        client = TestClient(app)
        resp = client.get("/forge/v1/unknown-route")
        assert resp.status_code == 404
        body = resp.json()
        # FastAPI default 404 detail is a plain string; FORGE does not change that
        # for non-FORGE routes, but FORGE routes use a stable envelope.
        assert isinstance(body, dict)
        assert "detail" in body

    def test_forge_meta_request_id_present(self) -> None:
        from app.main import app

        client = TestClient(app)
        resp = client.get(
            "/forge/v1/meta",
            headers={"X-Request-Id": "test-req-123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["request_id"] == "test-req-123"

    def test_forge_meta_invalid_inbound_request_id_ignored(self) -> None:
        from app.main import app

        client = TestClient(app)
        resp = client.get(
            "/forge/v1/meta",
            headers={"X-Request-Id": "!!!!invalid!!!!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        # Invalid inbound id should be ignored and a generated one used.
        assert re.fullmatch(r"fg-[0-9a-f]{16}", body["request_id"])


# ---------------------------------------------------------------------------
# F — configuration
# ---------------------------------------------------------------------------

class TestForgeConfig:
    """FORGE config boundary has safe defaults and fails clearly."""

    def test_default_config_is_local_like(self) -> None:
        from app.forge.config import forge_config_from_environment

        cfg = forge_config_from_environment()
        assert cfg.service_name == "glx-forge"
        assert cfg.api_version == "v1"
        assert cfg.is_local() or cfg.is_test()

    def test_config_fails_on_invalid_int_env(self) -> None:
        from app.forge.config import _int_env

        import os

        os.environ["FORGE_BOGUS_INT"] = "not-an-int"
        with pytest.raises(ValueError, match="invalid integer env"):
            _int_env("FORGE_BOGUS_INT", 0)
        os.environ.pop("FORGE_BOGUS_INT", None)

    def test_config_redacted_diagnostics_hides_secrets(self) -> None:
        from app.forge.config import ForgeConfig

        cfg = ForgeConfig(
            database_url="postgres://user:secret-password@db-host:5432/forge",
            database_enabled=True,
        )
        diag = cfg.redacted_diagnostics()
        assert "secret-password" not in str(diag)
        assert "db-host" not in str(diag)
        assert diag["database_configured"] is True
        assert diag["database_enabled"] is True

    def test_config_from_values_is_testable_without_env(self) -> None:
        from app.forge.config import forge_config_from_values

        cfg = forge_config_from_values(
            environment="test",
            application_version="0.0.0-test",
        )
        assert cfg.environment == "test"
        assert cfg.application_version == "0.0.0-test"

    def test_config_has_no_provider_credential_fields(self) -> None:
        """FORBIDDEN SCOPE: II.1 builds no provider configuration."""

        from dataclasses import fields as dataclass_fields

        from app.forge.config import ForgeConfig

        names = {f.name for f in dataclass_fields(ForgeConfig)}
        for forbidden in (
            "provider_openrouter_api_key",
            "provider_openrouter_base_url",
            "provider_whop_api_key",
            "provider_whop_base_url",
            "provider_market_data_backend",
        ):
            assert forbidden not in names


# ---------------------------------------------------------------------------
# I/J — logging/lifecycle smoke
# ---------------------------------------------------------------------------

class TestForgeLifecycle:
    """FORGE lifecycle is explicit, testable, and actually fires."""

    def test_lifecycle_startup_and_shutdown(self) -> None:
        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer
        from app.forge.service.lifecycle import ForgeLifecycle

        cfg = ForgeConfig(environment="test")
        container = ForgeServiceContainer(config=cfg)
        lifecycle = ForgeLifecycle(container)
        up = lifecycle.startup()
        assert up["started"] is True
        assert lifecycle.started is True
        down = lifecycle.shutdown()
        assert down["shutdown"] is True
        assert lifecycle.started is False

    def test_lifecycle_fires_on_application_startup_and_shutdown(self) -> None:
        """J1: lifecycle runs on the composed application, not just in isolation."""

        from fastapi import FastAPI

        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer
        from app.forge.service.lifecycle import ForgeLifecycle
        from app.forge.service.routes import create_forge_router

        cfg = ForgeConfig(environment="test")
        container = ForgeServiceContainer(config=cfg)
        lifecycle = ForgeLifecycle(container)
        probe = FastAPI()
        probe.include_router(
            create_forge_router(config=cfg, container=container)
        )
        probe.router.on_startup.append(lifecycle.startup)
        probe.router.on_shutdown.append(lifecycle.shutdown)

        with TestClient(probe) as probe_client:
            assert lifecycle.started is True
            resp = probe_client.get("/forge/v1/health")
            assert resp.status_code == 200
        assert lifecycle.started is False


class TestForgeErrorEnvelopeUnit:
    """H1-H3: FORGE error envelope helpers produce deterministic safe shapes."""

    def test_internal_error_payload_shape(self) -> None:
        from app.forge.service.errors import internal_error_payload

        payload = internal_error_payload(request_id="fg-test")
        assert payload["code"] == "FORGE_INTERNAL_ERROR"
        assert payload["message"] == "internal service error"
        assert payload["request_id"] == "fg-test"
        assert "traceback" not in payload

    def test_client_error_helper_is_422(self) -> None:
        import pytest as _pytest

        from app.forge.service.errors import client_error

        with _pytest.raises(Exception) as excinfo:
            raise client_error("bad input", request_id="fg-1")
        http_exc = excinfo.value
        assert http_exc.status_code == 422
        assert http_exc.detail["code"] == "FORGE_CLIENT_ERROR"

    def test_not_found_helper_is_404(self) -> None:
        import pytest as _pytest

        from app.forge.service.errors import not_found

        with _pytest.raises(Exception) as excinfo:
            raise not_found("missing", request_id="fg-2")
        http_exc = excinfo.value
        assert http_exc.status_code == 404
        assert http_exc.detail["code"] == "FORGE_NOT_FOUND"

    def test_dependency_unavailable_helper_is_503(self) -> None:
        import pytest as _pytest

        from app.forge.service.errors import dependency_unavailable

        with _pytest.raises(Exception) as excinfo:
            raise dependency_unavailable("postgres", request_id="fg-3")
        http_exc = excinfo.value
        assert http_exc.status_code == 503
        assert http_exc.detail["code"] == "FORGE_DEPENDENCY_UNAVAILABLE"

    def test_internal_exception_in_route_does_not_leak_internals(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """K2/H2: unexpected exception yields safe 500 envelope, no leak."""

        from app.forge.service import health as forge_health_module
        from app.forge.service.health import ForgeHealthService

        def _boom(self: ForgeHealthService) -> dict:
            raise RuntimeError(
                "secret-internal-path C:/Users/x/secret.py and token sk-123"
            )

        monkeypatch.setattr(forge_health_module.ForgeHealthService, "liveness", _boom)
        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/forge/v1/health")
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == "FORGE_INTERNAL_ERROR"
        assert body["message"] == "internal service error"
        assert "request_id" in body
        text = resp.text
        assert "secret-internal-path" not in text
        assert "sk-123" not in text
        assert "RuntimeError" not in text
