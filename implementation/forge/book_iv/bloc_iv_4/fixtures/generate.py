"""Generate the 24 deterministic IV.4 gateway fixtures."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from _builders import build_all  # noqa: E402


def main() -> None:
    files = build_all()
    manifest = {
        "base_head": "5ace8dfcd57f12996d168120ca74ee20e20e3f52",
        "contract": "ASK_GATEWAY_CONTRACT_V1",
        "fixture_count": len(files),
        "fixtures": {},
    }
    for name, text in files.items():
        normalized = text.replace("\r\n", "\n").encode("utf-8")
        (HERE / name).write_bytes(normalized)
        manifest["fixtures"][name] = {
            "bytes": len(normalized),
            "sha256": hashlib.sha256(normalized).hexdigest(),
        }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (HERE / "FIXTURE_MANIFEST.json").write_bytes(manifest_text.encode("utf-8"))
    print(f"generated {len(files)} fixtures")


if __name__ == "__main__":
    main()
