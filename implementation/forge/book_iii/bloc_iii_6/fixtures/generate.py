"""Regenerate the twelve III.6 golden fixtures, manifest and baseline.

Usage::

    python implementation/forge/book_iii/bloc_iii_6/fixtures/generate.py
    python implementation/forge/book_iii/bloc_iii_6/fixtures/generate.py --check
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from app.forge.intelligence_api.serialization import canonical_json  # noqa: E402

BASELINE_PACKAGES = {
    "market_data": "app/forge/market_data",
    "measurements": "app/forge/measurements",
    "model_runtime": "app/forge/model_runtime",
    "state_engine": "app/forge/state_engine",
    "setup_engine": "app/forge/setup_engine",
}


def _entry(name: str) -> dict:
    sys.path.insert(0, str(HERE))
    try:
        import _builders  # type: ignore
    finally:
        sys.path.pop(0)
    return _builders.build_case(name)


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _package_hash(directory: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in directory.glob("*.py"))
    for path in files:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\n")
        digest.update(path.read_bytes())
    return len(files), digest.hexdigest()


def build() -> tuple[dict[str, bytes], dict[str, bytes]]:
    from _builders import CASE_NAMES  # type: ignore

    files: dict[str, bytes] = {}
    hashes: dict[str, str] = {}
    for name in CASE_NAMES:
        text = canonical_json(_entry(name)) + "\n"
        data = text.encode("utf-8")
        files[f"{name}.json"] = data
        hashes[f"{name}.json"] = _hash_bytes(data)

    manifest = {"schema_version": "III6_FIXTURE_MANIFEST.V1", "fixtures": hashes}
    files["FIXTURE_MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )

    packages = {}
    for name, relative in BASELINE_PACKAGES.items():
        count, digest = _package_hash(REPO / relative)
        packages[name] = {"modules": count, "aggregate_sha256": digest}
    baseline = {"schema_version": "III6_FROZEN_BASELINE.V1", "packages": packages}
    files["FROZEN_BASELINE.json"] = (
        json.dumps(baseline, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return files, {}


def main(argv: list[str]) -> int:
    files, _ = build()
    check = "--check" in argv
    changes: list[str] = []
    for name, data in files.items():
        path = HERE / name
        if check:
            if not path.exists() or path.read_bytes() != data:
                changes.append(name)
        else:
            path.write_bytes(data)
    if check:
        if changes:
            print("fixtures differ: " + ", ".join(sorted(changes)))
            return 1
        print(f"fixtures reproduce byte-identically ({len(files)} files)")
        return 0
    print(f"wrote {len(files)} fixture files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
