"""First-party SQL migration runner for FORGE persistence.

Ordered, immutable, forward-only `.sql` migrations under
`app/forge/persistence/sql/`. Applied versions are recorded in
`forge_schema_migrations`. Execution is always explicit — never a side
effect of import. Never destructive; no drop/recreate.
"""

from __future__ import annotations

import importlib.resources
import re
from dataclasses import dataclass
from typing import Any, List

from sqlalchemy import text

from app.forge.persistence.port import MigrationOutcome

_MIGRATION_FILE_RE = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")


@dataclass(frozen=True)
class Migration:
    version: int
    identity: str
    sql: str


def split_sql_statements(sql_text: str) -> List[str]:
    """Split a migration file into individual SQL statements.

    Migration SQL is first-party and reviewable; it never contains
    semicolons inside string literals orComments, so a conservative
    line-aware split after stripping comment lines is correct here.
    """

    cleaned_lines: List[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        cleaned_lines.append(line)
    joined = "\n".join(cleaned_lines)
    statements = [s.strip() for s in joined.split(";")]
    return [s for s in statements if s]


def discover_migrations() -> tuple[Migration, ...]:
    """Deterministically load all migration files (numeric order)."""

    package = importlib.resources.files("app.forge.persistence.sql")
    found: list[Migration] = []
    for entry in sorted(package.iterdir()):
        name = entry.name
        match = _MIGRATION_FILE_RE.match(name)
        if not match:
            continue
        text = entry.read_text(encoding="utf-8")
        identity_line = ""
        for line in text.splitlines():
            if line.startswith("-- FORGE persistence — migration "):
                identity_line = line.split("— migration ", 1)[1].strip()
                break
        found.append(
            Migration(version=int(match.group(1)), identity=identity_line or name, sql=text)
        )
    found.sort(key=lambda m: m.version)
    versions = [m.version for m in found]
    if versions != sorted(set(versions)):
        raise RuntimeError("migration version collision")
    return tuple(found)


class SqlMigrationRunner:
    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._migrations = discover_migrations()

    def _fetch(self, sql: str, params: tuple = ()) -> List[Any]:
        result = self._connection.execute(text(sql), params)
        return list(result.fetchall())

    def _applied_versions(self) -> List[int]:
        self._ensure_table()
        rows = self._fetch("SELECT version FROM forge_schema_migrations")
        return sorted(int(r[0]) for r in rows)

    def _ensure_table(self) -> None:
        self._connection.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS forge_schema_migrations (
                version     INTEGER PRIMARY KEY,
                identity    VARCHAR(120) NOT NULL,
                applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
            )
        )

    def applied_versions(self) -> List[int]:
        return self._applied_versions()

    def check_compatibility(self) -> str:
        """OK / BEHIND / INCOMPATIBLE / AHEAD schema identity."""

        applied = self._applied_versions()
        code_versions = [m.version for m in self._migrations]
        if not code_versions:
            return MigrationOutcome.INCOMPATIBLE
        latest_code = code_versions[-1]
        if not applied:
            return "BEHIND"
        if applied[-1] == latest_code and set(applied) == set(code_versions):
            return "OK"
        if applied[-1] > latest_code:
            return "AHEAD"
        return "BEHIND"

    def apply_migrations(self) -> str:
        self._ensure_table()
        applied = set(self._applied_versions())
        outcome = MigrationOutcome.CURRENT
        for migration in self._migrations:
            if migration.version in applied:
                continue
            for statement in split_sql_statements(migration.sql):
                self._connection.execute(text(statement))
            self._connection.execute(
                text(
                    "INSERT INTO forge_schema_migrations (version, identity) VALUES (:v, :i)"
                ),
                {"v": migration.version, "i": migration.identity},
            )
            outcome = MigrationOutcome.APPLIED
        return outcome
