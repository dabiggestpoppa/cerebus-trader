"""FORGE configuration boundary.

This is the FORGE-owned config surface. It does not replace the existing
application config in `app.config`; it complements it with typed FORGE settings
and a redacted diagnostic representation.

No provider configuration beyond what II.1 needs is introduced here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _bool_env(name: str, default: bool = False) -> bool:
    return _env(name, str(default)).strip().lower() in ("1", "true", "yes")


def _int_env(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"invalid integer env {name!r}") from exc


@dataclass(frozen=True)
class ForgeConfig:
    """Typed FORGE configuration with safe LOCAL/TEST defaults."""

    service_name: str = "glx-forge"
    api_version: str = "v1"
    application_version: str = _env("FORGE_APPLICATION_VERSION", "1.0.0")
    environment: str = _env("FORGE_ENVIRONMENT", "local")
    log_level: str = _env("FORGE_LOG_LEVEL", "info").upper()
    request_id_header: str = "X-Request-Id"
    # II.1 does not require persistence/providers/policy; all of those are
    # explicitly off/empty/default at this stage. Provider credential config
    # is deliberately ABSENT until II.5 defines the provider port contract.
    database_url: str = ""
    database_enabled: bool = False
    migration_compatibility_required: bool = False

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
    )


def forge_config_from_values(**values: Any) -> ForgeConfig:
    """Build a FORGE config for tests without relying on process env."""

    base = ForgeConfig()
    # Simple override path for tests.
    return base.__class__(**{**base.__dict__, **values})  # type: ignore[arg-type]
