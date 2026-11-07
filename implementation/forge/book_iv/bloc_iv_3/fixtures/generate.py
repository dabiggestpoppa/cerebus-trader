"""Generate the twenty IV.3 golden context packages and their manifest."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))

_NAME = "iv3_fixture_builders"
_spec = importlib.util.spec_from_file_location(_NAME, HERE / "_builders.py")
assert _spec is not None and _spec.loader is not None
B = importlib.util.module_from_spec(_spec)
sys.modules[_NAME] = B
_spec.loader.exec_module(B)

BASE_HEAD = "0d64fa8cf6d1c568dae6d7110281d38b5587705a"


def build_manifest(files: dict[str, str]) -> str:
    payload = {
        "contract": "CONTEXT_CONTRACT_V1",
        "base_head": BASE_HEAD,
        "fixture_count": len(files),
        "fixtures": {
            name: {
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "bytes": len(text.encode("utf-8")),
            }
            for name, text in sorted(files.items())
        },
    }
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def main() -> int:
    expected = HERE / "expected"
    expected.mkdir(parents=True, exist_ok=True)
    files = B.build_all()
    for name, text in files.items():
        (expected / name).write_text(text, encoding="utf-8", newline="\n")
    (HERE / "FIXTURE_MANIFEST.json").write_text(
        build_manifest(files), encoding="utf-8", newline="\n"
    )
    print(json.dumps({"generated": len(files), "dir": str(expected)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["BASE_HEAD", "build_manifest", "main"]
