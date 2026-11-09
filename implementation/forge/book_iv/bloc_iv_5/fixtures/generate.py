"""Deterministically write the forty-six Q5 fixture records.

Run from the repository root:

    python implementation/forge/book_iv/bloc_iv_5/fixtures/generate.py

The generator is the only writer. Tests re-run the scenarios and compare the
recorded payload digest, so a byte-level drift fails immediately.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
for path in (str(ROOT), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import scenarios  # noqa: E402

from app.forge.ask_cerebus.answer import validate_answer  # noqa: E402


def digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def record_for(scenario) -> dict:
    outcome = validate_answer(scenario.draft, scenario.package)
    payload = outcome.payload()
    return {
        "id": scenario.id,
        "kind": scenario.kind,
        "expected_code": scenario.code,
        "required_findings": list(scenario.required_findings),
        "outcome": payload["outcome"],
        "answer_id": payload["answer_id"],
        "depth": payload["depth"],
        "payload_sha256": digest(payload),
        "package_id": scenario.package.package_id,
        "manifest_id": scenario.package.manifest.manifest_digest,
        "query_plan_id": scenario.package.query_plan_id,
        "findings": list(getattr(outcome, "findings", ())),
        "sections": [section["section_id"] for section in payload.get("sections", [])],
        "limitations": list(payload.get("limitations", [])),
    }


def main() -> int:
    manifest: dict[str, str] = {}
    for scenario in scenarios.cases():
        record = record_for(scenario)
        text = json.dumps(record, indent=2, sort_keys=True) + "\n"
        path = HERE / f"{scenario.id}.json"
        path.write_text(text, encoding="utf-8", newline="\n")
        manifest[scenario.id] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    manifest_text = json.dumps(
        {"count": len(manifest), "records": manifest},
        indent=2,
        sort_keys=True,
    )
    (HERE / "FIXTURE_MANIFEST.json").write_text(
        manifest_text + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {len(manifest)} fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
