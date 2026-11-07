#!/usr/bin/env python3
"""Generate the twelve IV.1 golden query-plan fixtures.

The fixtures assert interpretation only. They contain no market observation,
no probability and no answer. Regenerating on the same contract version must
produce byte-identical files.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.forge.ask_cerebus.interpreter import (  # noqa: E402
    ASK_QUERY_CONTRACT_V1,
    Depth,
    InterpreterContext,
    interpret,
)

HERE = Path(__file__).resolve().parent
EXPECTED = HERE / "expected"
BASE_HEAD = "6ca573d226b14100b9244b3a8d7bb92f68b5907f"

FIXTURES: tuple[tuple[str, str, str], ...] = (
    ("Q-01", "What is rekey?", "definition of a historical alias"),
    ("Q-02", "What does the Gold Game mean?", "XAU model description"),
    ("Q-03", "What's EURUSD doing today?", "current EURUSD state"),
    ("Q-04", "What's the current Gold setup?", "current XAU setup context"),
    ("Q-05", "Is BTC Game the same as BTC Tracker?", "BTC identity collision"),
    ("Q-06", "What's the 132% target win rate?", "unsupported statistic"),
    ("Q-07", "Show the original P90 model.", "P90 historical generation"),
    ("Q-08", "What was the EUR weekly state last Wednesday?", "AS_OF EUR weekly"),
    ("Q-09", "Should I enter Gold now?", "actionable XAU question"),
    ("Q-10", "Explain JPY carry confirmation.", "JPY methodology"),
    ("Q-11", "Give me the historical ST automation results.", "ST historical evidence"),
    ("Q-12", "Show the Fib R15 production anchor.", "Fib production gate"),
)

CONTEXT = InterpreterContext(
    principal_scope="fixture",
    max_authorized_depth=Depth.RESEARCHER,
    policy_fingerprint="fixture-policy",
)


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build() -> dict[str, object]:
    EXPECTED.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for fixture_id, question, expectation in FIXTURES:
        plan = interpret(question, CONTEXT)
        path = EXPECTED / f"{fixture_id}.json"
        text = _canonical(plan.payload()) + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        entries.append(
            {
                "id": fixture_id,
                "question": question,
                "expectation": expectation,
                "expected": f"expected/{fixture_id}.json",
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "intent": plan.intent.value,
                "outcome": plan.outcome.value,
                "plan_id": plan.plan_id,
            }
        )
    manifest = {
        "contract_version": ASK_QUERY_CONTRACT_V1,
        "base_head": BASE_HEAD,
        "fixture_count": len(entries),
        "fixtures": entries,
    }
    manifest_text = _canonical(manifest) + "\n"
    (HERE / "FIXTURE_MANIFEST.json").write_text(
        manifest_text, encoding="utf-8", newline="\n"
    )
    (HERE / "PROVENANCE.md").write_text(
        "# IV.1 golden fixture provenance\n\n"
        f"- Base head: `{BASE_HEAD}`\n"
        f"- Query contract: `{ASK_QUERY_CONTRACT_V1}`\n"
        f"- Fixtures: {len(entries)} (Q-01–Q-12)\n"
        "- Generator: `generate.py` (deterministic, offline)\n"
        "- Expectations: query plans only — intent, identity, scope, depth, "
        "flags, confidence, ambiguity.\n"
        "- No market observation, performance figure, probability, answer or "
        "provider response is present.\n"
        "- Regeneration on the same contract version must be byte-identical.\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


if __name__ == "__main__":
    built = build()
    print(f"generated {built['fixture_count']} fixtures at {EXPECTED}")
