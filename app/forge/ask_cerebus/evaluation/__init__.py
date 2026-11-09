"""Book IV / Bloc IV.6 — ASK CEREBUS evaluation and red team.

The package is an evaluator, not a participant: the oracle never imports the
system it measures, and a run never writes an expectation. Public entry points
are the dataset, oracle, harness, scoring, report and regression modules.
"""

from __future__ import annotations

from app.forge.ask_cerebus.evaluation import (
    dataset,
    enums,
    findings,
    harness,
    matching,
    oracle,
    redteam,
    regression,
    report,
    review,
    schema,
    scoring,
    versions,
)

__all__ = [
    "dataset",
    "enums",
    "findings",
    "harness",
    "matching",
    "oracle",
    "redteam",
    "regression",
    "report",
    "review",
    "schema",
    "scoring",
    "versions",
]
