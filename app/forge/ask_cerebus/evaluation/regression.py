"""Cross-bloc regression: declared impact map, upstream pins, replay equality.

The impact map is a statement about blast radius, not a way to shrink CI: it is
checked for completeness (every case appears, every upstream change is owned)
and never used to skip a run (R95, x006, x010).
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from app.forge.ask_cerebus.evaluation import versions
from app.forge.ask_cerebus.evaluation.schema import EvaluationCase, EvaluationDataset

#: PLAN.md §12, verbatim as ranges.
IMPACT_MAP: Mapping[str, tuple[tuple[int, int], ...]] = {
    "IV.1_interpreter": ((1, 46),),
    "IV.2_retrieval": ((29, 37), (94, 106)),
    "IV.3_context": ((5, 12), (74, 84)),
    "IV.4_gateway": ((107, 110), (85, 93)),
    "IV.5_validator": ((47, 84), (111, 114)),
    "Book_I_canonical": ((1, 20), (67, 73)),
    "Book_II_policy": ((94, 100),),
    "Book_III_intelligence": ((5, 7), (29, 34), (80, 84)),
    "IV.6_evaluation": ((115, 120),),
}


@dataclass(frozen=True)
class PinCheck:
    path: str
    expected: str
    observed: str | None
    ok: bool

    def as_record(self) -> dict[str, object]:
        return {
            "path": self.path,
            "expected": self.expected,
            "observed": self.observed,
            "ok": self.ok,
        }


def _number(case_id: str) -> int:
    return int(case_id.split("-")[1])


def impacted_case_ids(change: str) -> tuple[str, ...]:
    if change not in IMPACT_MAP:
        raise KeyError(f"no declared impact for {change!r}")
    out: list[str] = []
    for low, high in IMPACT_MAP[change]:
        out.extend(f"EV-{number:03d}" for number in range(low, high + 1))
    return tuple(dict.fromkeys(out))


def cases_for_change(dataset: EvaluationDataset, change: str) -> tuple[EvaluationCase, ...]:
    wanted = set(impacted_case_ids(change))
    return tuple(case for case in dataset.cases if case.case_id in wanted)


def uncovered_changes(cases: Iterable[EvaluationCase]) -> tuple[str, ...]:
    """Every case must be declared against at least one upstream change."""

    covered = {case_id for change in IMPACT_MAP for case_id in impacted_case_ids(change)}
    return tuple(case.case_id for case in cases if case.case_id not in covered)


def stale_declarations(cases: Iterable[EvaluationCase]) -> tuple[str, ...]:
    """Declared case ids that the dataset no longer contains."""

    present = {case.case_id for case in cases}
    declared = {
        case_id
        for change in IMPACT_MAP
        for case_id in impacted_case_ids(change)
    }
    return tuple(sorted(declared - present))


def check_impact_map(cases: Sequence[EvaluationCase]) -> tuple[str, ...]:
    problems = list(uncovered_changes(cases))
    problems.extend(f"missing:{case_id}" for case_id in stale_declarations(cases))
    return tuple(problems)


def blob_id(path: Path | str, root: Path | str) -> str | None:
    """Reproduce the pinned git blob id without asking git about history."""

    target = Path(root) / Path(path)
    if not target.is_file():
        return None
    data = target.read_bytes()
    # ``git hash-object`` applies the text filter, so a checkout with CRLF line
    # endings still yields the same blob id as the LF original.
    normalised = data.replace(b"\r\n", b"\n")
    header = f"blob {len(normalised)}\0".encode("ascii")
    return hashlib.sha1(header + normalised).hexdigest()


def verify_upstream_pins(root: Path | str) -> tuple[PinCheck, ...]:
    return tuple(
        PinCheck(
            path=path,
            expected=expected,
            observed=blob_id(path, root),
            ok=blob_id(path, root) == expected,
        )
        for path, expected in sorted(versions.UPSTREAM_PINS.items())
    )


def changed_pins(checks: Iterable[PinCheck]) -> tuple[str, ...]:
    return tuple(check.path for check in checks if not check.ok)


ROUTE_PREFIX = "/forge/v1"
ROUTE_PATHS = ("/health", "/ready", "/meta")


def check_routes(root: Path | str) -> tuple[str, ...]:
    """The FORGE router surface is unchanged and gained no ask route (x009)."""

    route_file = Path(root) / "app/forge/service/routes.py"
    if not route_file.is_file():
        return ("app/forge/service/routes.py: missing",)
    text = route_file.read_text(encoding="utf-8")
    problems: list[str] = []
    if ROUTE_PREFIX not in text:
        problems.append(f"{ROUTE_PREFIX}: prefix absent")
    for path in ROUTE_PATHS:
        if f'"{path}"' not in text:
            problems.append(f"{path}: absent")
    if "/ask" in text:
        problems.append("/ask: IV.6 must not add an ask route")
    return tuple(problems)


def check_migrations(root: Path | str) -> tuple[str, ...]:
    """Migration set is exactly the frozen four (x010)."""

    directory = Path(root) / "app/forge/persistence/sql"
    if not directory.is_dir():
        return ("app/forge/persistence/sql: directory absent",)
    seen = sorted(
        int(item.name.split("_", 1)[0])
        for item in directory.iterdir()
        if item.suffix == ".sql" and item.name[:1].isdigit()
    )
    if tuple(seen) != versions.MIGRATION_VERSIONS:
        return (f"migrations: {tuple(seen)} != {versions.MIGRATION_VERSIONS}",)
    return ()


def changed_upstream_files(root: Path | str) -> tuple[str, ...]:
    """Files this bloc must never touch, checked by pin rather than by diff."""

    return changed_pins(verify_upstream_pins(root))


def replay_signature(executions: Iterable[object]) -> str:
    payload = "\n".join(
        sorted(f"{getattr(execution, 'case_id', '?')}:{getattr(execution, 'digest', '?')}" for execution in executions)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_status_dirty(root: Path | str, *, paths: Sequence[str] = ()) -> tuple[str, ...]:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain", *paths],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ("git: unavailable",)
    return tuple(line for line in completed.stdout.splitlines() if line.strip())
