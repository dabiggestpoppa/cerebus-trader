"""Loader for the additive V2 evaluation corpus (EV-145..EV-154)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.forge.ask_cerebus.evaluation.schema import EvaluationCase

ROOT = Path(__file__).resolve().parents[4]
V2_DIRECTORY = ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures_v2"
_MODULE = "iv6_v2_cases"


def module():
    if _MODULE in sys.modules:
        return sys.modules[_MODULE]
    spec = importlib.util.spec_from_file_location(_MODULE, V2_DIRECTORY / "cases.py")
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def cases() -> tuple[EvaluationCase, ...]:
    return module().cases()


def digest() -> str:
    return module().digest()


def manifest() -> dict[str, object]:
    return module().manifest()


def frozen_manifest() -> dict[str, object]:
    path = V2_DIRECTORY / "DATASET_MANIFEST.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify() -> tuple[str, ...]:
    """Compare the declared corpus against its frozen manifest on disk."""

    problems: list[str] = []
    path = V2_DIRECTORY / "DATASET_MANIFEST.json"
    if not path.exists():
        return (f"missing corpus manifest: {path}",)
    frozen = frozen_manifest()
    declared = manifest()
    if frozen.get("digest") != digest():
        problems.append("corpus digest does not match its case array")
    if frozen.get("digest") != declared.get("digest"):
        problems.append("declared manifest digest disagrees with the frozen manifest")
    if frozen.get("case_count") != len(cases()):
        problems.append("frozen case count disagrees with the case array")
    ids = [case.case_id for case in cases()]
    if len(set(ids)) != len(ids):
        problems.append("duplicate case id in the V2 corpus")
    if ids != [f"EV-{number}" for number in range(145, 145 + len(ids))]:
        problems.append("V2 case ids are not contiguous from EV-145")
    for case in cases():
        case_path = V2_DIRECTORY / f"{case.case_id}.json"
        if not case_path.exists():
            problems.append(f"{case.case_id}: case file is missing")
            continue
        on_disk = json.loads(case_path.read_text(encoding="utf-8"))
        if on_disk != case.payload():
            problems.append(f"{case.case_id}: case file disagrees with its declaration")
    return tuple(problems)


__all__ = [
    "ROOT",
    "V2_DIRECTORY",
    "cases",
    "digest",
    "frozen_manifest",
    "manifest",
    "module",
    "verify",
]
