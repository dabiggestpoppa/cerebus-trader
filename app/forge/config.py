"""FORGE configuration boundary.

This is the FORGE-owned config surface. It does not replace the existing
application config in `app.config`; it complements it with typed FORGE settings
and a redacted diagnostic representation.

II.5 adds provider selection (names only), resilience budgets, and credential
PRESENCE for future concrete adapters — values are carried but unread, never
repr'd, and never included in diagnostics (Ch II.5.1 redaction law).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

# Provider selection tokens (Ch II.5.6): lowercase, bounded, log-safe.
_PROVIDER_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _bool_env(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes")


def _int_env(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"invalid integer env {name!r}") from exc


def _float_env(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"invalid float env {name!r}") from exc


def _provider_env(name: str, default: str = "fake") -> str:
    value = _env(name, default).strip().lower()
    if not _PROVIDER_NAME_RE.match(value):
        raise ValueError(f"invalid provider name env {name!r}")
    return value


# Durable audit/event ledger write policies (Ch II.2.6 / GAP-05).
AUDIT_WRITE_POLICIES: tuple[str, ...] = ("best_effort", "require_durable")


@dataclass(frozen=True)
class AuditDurableConfig:
    """Durable audit/event ledger selection (frozen Ch II.2.6; GAP-05).

    Opt-in and fail-closed: disabled by default; enabling REQUIRES a
    database URL — durable audit is never silently downgraded to
    in-memory-only. `database_url` carries credentials and is excluded from
    repr and diagnostics (Ch II.5.1-style redaction: presence booleans
    only). Migrations are never applied by config/composition (frozen
    rule): migration 004 must be applied explicitly before enabling.
    """

    enabled: bool = False
    database_url: str = field(default="", repr=False)
    capacity: int = 10_000
    write_policy: str = "best_effort"

    def __post_init__(self) -> None:
        if self.enabled and not self.database_url:
            raise ValueError(
                "audit_durable enabled requires a database url "
                "(fail closed: durable audit is never in-memory-only)"
            )
        if self.capacity < 1:
            raise ValueError("audit_durable capacity must be >= 1")
        if self.write_policy not in AUDIT_WRITE_POLICIES:
            raise ValueError(
                f"audit_durable write_policy must be one of {AUDIT_WRITE_POLICIES}"
            )
        if self.write_policy == "require_durable" and not self.enabled:
            raise ValueError(
                "audit_durable write_policy 'require_durable' requires enabled"
            )


@dataclass(frozen=True)
class ForgeConfig:
    """Typed FORGE configuration with safe LOCAL/TEST defaults."""

    service_name: str = "glx-forge"
    api_version: str = "v1"
    application_version: str = _env("FORGE_APPLICATION_VERSION", "1.0.0")
    environment: str = _env("FORGE_ENVIRONMENT", "local")
    log_level: str = _env("FORGE_LOG_LEVEL", "info").upper()
    request_id_header: str = "X-Request-Id"
    database_url: str = ""
    database_enabled: bool = False
    migration_compatibility_required: bool = False
    # II.5: provider selection at the composition root (Ch II.5.6). "fake" is
    # the only registered builder until Book IV/VI add concrete adapters;
    # unknown names fail closed at providers_from_config().
    provider_llm: str = "fake"
    provider_commerce: str = "fake"
    provider_notification: str = "fake"
    provider_storage: str = "fake"
    provider_timeout_seconds: float = 10.0
    circuit_failure_threshold: int = 3
    circuit_recovery_seconds: float = 30.0
    # Credential presence for future concrete adapters (Book IV OpenRouter,
    # Book VI Whop). Carried but UNREAD at II.5, excluded from repr, never in
    # diagnostics (Ch II.5.1 redaction law). Only configured-booleans surface.
    openrouter_api_key: str = field(default="", repr=False)
    whop_api_key: str = field(default="", repr=False)
    # II.6: observability substrate selection. In-process only; no vendor,
    # no network. `observability_enabled=False` leaves the seam unwired
    # (readiness discloses NOT_CONFIGURED, core execution unaffected).
    observability_enabled: bool = True
    observability_event_capacity: int = 512
    observability_log_sinks: bool = True
    # GAP-05 / Ch II.2.6: durable audit/event ledger selection. Disabled by
    # default (byte-identical behavior); enabled only via explicit config.
    audit_durable: AuditDurableConfig = field(default_factory=AuditDurableConfig)

    def __post_init__(self) -> None:
        # Fail-closed validation (II.5): a malformed provider selection or
        # resilience budget must never reach the composition root silently.
        for port in ("llm", "commerce", "notification", "storage"):
            value = getattr(self, f"provider_{port}")
            if not _PROVIDER_NAME_RE.match(value or ""):
                raise ValueError(f"invalid provider name for {port!r}")
        if self.provider_timeout_seconds <= 0:
            raise ValueError("provider_timeout_seconds must be > 0")
        if self.circuit_failure_threshold < 1:
            raise ValueError("circuit_failure_threshold must be >= 1")
        if self.circuit_recovery_seconds < 0:
            raise ValueError("circuit_recovery_seconds must be >= 0")
        if self.observability_event_capacity < 1:
            raise ValueError("observability_event_capacity must be >= 1")
        if self.audit_durable.enabled and not self.observability_enabled:
            raise ValueError(
                "audit_durable enabled requires observability_enabled "
                "(fail closed: durable audit lives behind the observability seam)"
            )

    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"

    def is_test(self) -> bool:
        return self.environment.strip().lower() in ("test", "testing")

    def is_local(self) -> bool:
        return self.environment.strip().lower() in ("local", "development", "dev")

    def redacted_diagnostics(self) -> dict[str, Any]:
        """Safe diagnostic representation. Never secrets, never raw env dump."""

        def _redact(value: str) -> str:
            if not value:
                return ""
            if value.startswith("http"):
                return value.split("://", 1)[0] + "://[redacted]"
            if len(value) >= 8:
                return value[:4] + "****"
            return "****"

        return {
            "service_name": self.service_name,
            "api_version": self.api_version,
            "application_version": self.application_version,
            "environment": self.environment,
            "log_level": self.log_level,
            "database_enabled": self.database_enabled,
            "database_configured": bool(self.database_url),
            "migration_compatibility_required": self.migration_compatibility_required,
            # II.5: selection names and budgets are safe to disclose; credential
            # VALUES are never included — only configured-presence booleans.
            "provider_llm": self.provider_llm,
            "provider_commerce": self.provider_commerce,
            "provider_notification": self.provider_notification,
            "provider_storage": self.provider_storage,
            "provider_timeout_seconds": self.provider_timeout_seconds,
            "circuit_failure_threshold": self.circuit_failure_threshold,
            "circuit_recovery_seconds": self.circuit_recovery_seconds,
            "openrouter_api_key_configured": bool(self.openrouter_api_key),
            "whop_api_key_configured": bool(self.whop_api_key),
            # II.6: observability presence/booleans only, never event payloads.
            "observability_enabled": self.observability_enabled,
            "observability_event_capacity": self.observability_event_capacity,
            "observability_log_sinks": self.observability_log_sinks,
            # GAP-05: durable audit presence/booleans only, never the URL.
            "audit_durable_enabled": self.audit_durable.enabled,
            "audit_durable_configured": bool(self.audit_durable.database_url),
            "audit_durable_capacity": self.audit_durable.capacity,
            "audit_durable_write_policy": self.audit_durable.write_policy,
        }


_FORGE_ENV_FROM_APP_ENV: dict[str, str] = {
    "local": "local",
    "dev": "local",
    "development": "local",
    "test": "test",
    "testing": "test",
    "staging": "staging",
    "production": "production",
}


def forge_config_from_environment() -> ForgeConfig:
    """Build FORGE config from environment with safe defaults.

    II.1 requires no provider credentials and no database to start.
    """

    app_env = _env("ENVIRONMENT", "dev").strip().lower()
    forge_env = _FORGE_ENV_FROM_APP_ENV.get(app_env, "local")

    return ForgeConfig(
        environment=forge_env,
        application_version=_env("FORGE_APPLICATION_VERSION", "1.0.0"),
        log_level=_env("FORGE_LOG_LEVEL", "info").upper(),
        database_url=_env("FORGE_DATABASE_URL", ""),
        database_enabled=_bool_env("FORGE_DATABASE_ENABLED", False),
        migration_compatibility_required=_bool_env(
            "FORGE_MIGRATION_COMPATIBILITY_REQUIRED", False
        ),
        # II.5 provider selection (composition-root chooses adapters).
        provider_llm=_provider_env("FORGE_PROVIDER_LLM"),
        provider_commerce=_provider_env("FORGE_PROVIDER_COMMERCE"),
        provider_notification=_provider_env("FORGE_PROVIDER_NOTIFICATION"),
        provider_storage=_provider_env("FORGE_PROVIDER_STORAGE"),
        provider_timeout_seconds=_float_env(
            "FORGE_PROVIDER_TIMEOUT_SECONDS", 10.0
        ),
        circuit_failure_threshold=_int_env(
            "FORGE_CIRCUIT_FAILURE_THRESHOLD", 3
        ),
        circuit_recovery_seconds=_float_env(
            "FORGE_CIRCUIT_RECOVERY_SECONDS", 30.0
        ),
        # Credential presence only; values are never read by FORGE at II.5.
        openrouter_api_key=_env("FORGE_OPENROUTER_API_KEY", ""),
        whop_api_key=_env("FORGE_WHOP_API_KEY", ""),        # II.6 observability substrate (in-process, vendor-free).
        observability_enabled=_bool_env("FORGE_OBSERVABILITY_ENABLED", True),
        observability_event_capacity=_int_env(
            "FORGE_OBSERVABILITY_EVENT_CAPACITY", 512
        ),
        observability_log_sinks=_bool_env("FORGE_OBSERVABILITY_LOG_SINKS", True),
        # GAP-05 durable audit/event ledger (opt-in, fail-closed): the URL
        # falls back to FORGE_DATABASE_URL so one configured database serves
        # both seams; enabling without any URL raises in __post_init__.
        audit_durable=AuditDurableConfig(
            enabled=_bool_env("FORGE_AUDIT_DURABLE_ENABLED", False),
            database_url=(
                _env("FORGE_AUDIT_DURABLE_URL", "")
                or _env("FORGE_DATABASE_URL", "")
            ),
            capacity=_int_env("FORGE_AUDIT_DURABLE_CAPACITY", 10_000),
            write_policy=_env(
                "FORGE_AUDIT_DURABLE_WRITE_POLICY", "best_effort"
            )
            .strip()
            .lower(),
        ),
    )


def forge_config_from_values(**values: Any) -> ForgeConfig:
    """Build a FORGE config for tests without relying on process env."""

    base = ForgeConfig()
    # Simple override path for tests.
    return base.__class__(**{**base.__dict__, **values})  # type: ignore[arg-type]
