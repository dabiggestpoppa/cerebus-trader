"""Materialise the frozen EV-155..EV-178 dataset from the authored case table.

Run from the repository root::

    python implementation/forge/book_iv/bloc_iv_6/fixtures_v3/generate.py

The generator writes ``EV-155.json`` … ``EV-178.json`` and
``DATASET_MANIFEST.json``. It never runs the corpus: every expectation is a
literal in the authored table, never from an execution.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.forge.ask_cerebus.evaluation import schema  # noqa: E402
from app.forge.ask_cerebus.evaluation.schema import EvaluationCase  # noqa: E402


def _load_cases_module():
    spec = importlib.util.spec_from_file_location("iv6_v3_case_table", HERE / "cases.py")
    if spec is None or spec.loader is None:  # pragma: no cover - import machinery
        raise RuntimeError("cannot load the IV.6 v3 case table")
    module = importlib.util.module_from_spec(spec)
    sys.modules["iv6_v3_case_table"] = module
    spec.loader.exec_module(module)
    return module


def build_cases() -> tuple[EvaluationCase, ...]:
    module = _load_cases_module()
    return tuple(module.cases())


def main() -> int:
    cases = build_cases()
    written = []
    for case in cases:
        target = HERE / f"{case.case_id}.json"
        target.write_text(json.dumps(case.payload(), indent=2, sort_keys=True), encoding="utf-8")
        written.append(target.name)

    # Manifest is a lightweight summary (v3 is an additive corpus, not the 120-case
    # frozen v1 dataset, so dataset_from_cases is not used here).
    digest = schema.dataset_digest(cases)
    manifest = {
        "dataset_version": "ASK_EVALUATION_DATASET_V3",
        "schema_version": "ASK_EVALUATION_CASE_SCHEMA_V1",
        "case_count": len(cases),
        "digest": digest,
        "authorities_used": sorted({c.authority.value for c in cases}),
        "forbidden_authorities_absent": True,
        "band_counts": [[c.family.value, 1] for c in cases],
        "balance_report": [["cases", len(cases)]],
        "cases": [c.case_id for c in cases],
    }
    (HERE / "DATASET_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"wrote {len(written)} case files + manifest")
    print(f"dataset digest: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
