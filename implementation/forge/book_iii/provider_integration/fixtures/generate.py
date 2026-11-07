"""Generate the WP-3B fixture set deterministically.

Writes twelve case files plus `FIXTURE_MANIFEST.json` and `FROZEN_BASELINE.json`.
`--check` regenerates in memory and verifies every file byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from _builders import ADAPTER_VERSION, CASE_NAMES, build_cases

HERE = Path(__file__).resolve().parent
CASE_FILES = "case_files"


def _dump(payload: object) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_bundle() -> dict[str, str]:
    cases = build_cases()
    files: dict[str, str] = {}
    manifest_entries: dict[str, dict] = {}
    baseline: dict[str, dict] = {}
    for case_id in CASE_NAMES:
        case = cases[case_id]
        name = f"{case_id.lower().replace('-', '_')}.json"
        text = _dump(case)
        files[name] = text
        digest = _digest(text)
        manifest_entries[name] = {"sha256": digest, "case_id": case_id}
        baseline[case_id] = {
            "sha256": digest,
            "adapter_version": ADAPTER_VERSION,
            "expected": case["expected"],
        }
    manifest = {
        "fixture_set": "WP3B_MARKET_DATA_INGEST",
        "adapter_version": ADAPTER_VERSION,
        "hash_normalization": "LF",
        "synthetic": True,
        "files": manifest_entries,
    }
    frozen = {
        "baseline_version": "FIXTURE_BASELINE_V1",
        "adapter_version": ADAPTER_VERSION,
        "provenance": "SYNTHETIC_FIXTURE",
        "cases": baseline,
    }
    files["FIXTURE_MANIFEST.json"] = _dump(manifest)
    files["FROZEN_BASELINE.json"] = _dump(frozen)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    files = build_bundle()
    if args.check:
        missing = []
        mismatched = []
        for name, text in files.items():
            path = HERE / name
            if not path.exists():
                missing.append(name)
                continue
            if path.read_text(encoding="utf-8") != text:
                mismatched.append(name)
        extras = sorted(
            path.name
            for path in HERE.glob("*.json")
            if path.name not in files
        )
        if missing or mismatched or extras:
            print(f"missing={missing} mismatched={mismatched} extras={extras}")
            return 1
        print(f"fixtures reproduce byte-identically ({len(files)} files)")
        return 0
    for name, text in files.items():
        (HERE / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
