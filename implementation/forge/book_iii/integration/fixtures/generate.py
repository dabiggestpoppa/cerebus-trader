"""Generate the ten deterministic Book III integration fixtures.

Structural proof only: these fixtures are synthetic contract inputs, never
market evidence. Regeneration must be byte-identical (LF-normalized).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve()
_ROOT = _HERE.parents[5]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_SPEC = importlib.util.spec_from_file_location("integration_fixture_builders", _HERE.with_name("_builders.py"))
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise SystemExit("cannot load integration builders")
_builders = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_builders)


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build() -> tuple[dict[str, str], dict[str, str]]:
    files: dict[str, str] = {}
    hashes: dict[str, str] = {}
    for name in _builders.CASE_NAMES:
        text = json.dumps(_builders.case(name), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        files[f"{name}.json"] = text
        hashes[f"{name}.json"] = hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    manifest = {
        "schema": "BOOK_III_INTEGRATION_FIXTURE_MANIFEST_V1",
        "fixtures": hashes,
        "note": "synthetic structural proof only; never empirical market evidence",
    }
    files["FIXTURE_MANIFEST.json"] = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    baseline = {
        "schema": "BOOK_III_INTEGRATION_FROZEN_BASELINE_V1",
        "starting_head": "9f423a490d6b1d74be4f2bd03827593152103e4c",
        "modules": {
            "market_data": 11,
            "measurements": 12,
            "model_runtime": 13,
            "state_engine": 13,
            "setup_engine": 16,
            "intelligence_api": 14,
        },
        "fixture_count": len(_builders.CASE_NAMES),
    }
    files["FROZEN_BASELINE.json"] = json.dumps(baseline, sort_keys=True, indent=2) + "\n"
    return files, hashes


def main(argv: list[str]) -> int:
    files, _hashes = build()
    if "--check" in argv:
        mismatched = []
        for name, text in files.items():
            target = _HERE.with_name(name)
            if not target.exists() or target.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
                mismatched.append(name)
        if mismatched:
            print("fixture mismatch: " + ", ".join(sorted(mismatched)))
            return 1
        print(f"fixtures reproduce byte-identically ({len(files)} files)")
        return 0
    for name, text in files.items():
        _HERE.with_name(name).write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} fixture files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
