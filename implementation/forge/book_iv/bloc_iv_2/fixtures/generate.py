"""Deterministic generator for the eighteen IV.2 golden retrieval bundles.

Importing this module builds nothing. ``build_all()`` returns the exact bytes
that must be committed under ``expected/``; ``main()`` writes them.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))

_BUILDERS_NAME = "iv2_fixture_builders"
_spec = importlib.util.spec_from_file_location(_BUILDERS_NAME, HERE / "_builders.py")
assert _spec is not None and _spec.loader is not None
B = importlib.util.module_from_spec(_spec)
sys.modules[_BUILDERS_NAME] = B
_spec.loader.exec_module(B)

from app.forge.ask_cerebus.interpreter.enums import Depth, Intent, TimeScope  # noqa: E402
from app.forge.ask_cerebus.retrieval import (  # noqa: E402
    AskCerebusRetrievalService,
    SemanticCandidate,
)
from app.forge.policy import CAPABILITY_CORPUS_READ_MEMBER, AuthorizationContext  # noqa: E402

BASE_HEAD = "38b322b562317fdd42ad8ea61a9866b2931966a7"
BASE_INDEX = B.build_index()
NO_GO_INDEX = B.build_index(nogo=True)


class _Leaky:
    def __init__(self, candidate):
        self.candidate = candidate

    def search(self, query, authorized_ids, limit):
        return (self.candidate,)[:limit]


def _scenarios():
    current = B.snapshot_context()
    historical = B.snapshot_context()
    return (
        ("Q2-01", B.plan(model_ids=("XAU.GAME",)), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-02", B.plan(model_ids=("XAU.GAME",), intent=Intent.MODEL_DESCRIPTION), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-03", B.plan(model_ids=("XAU.GAME",), intent=Intent.STATISTIC_EVIDENCE, evidence=True), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-04", B.plan(model_ids=("XAU.NOEV",), intent=Intent.STATISTIC_EVIDENCE, evidence=True), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-05", B.plan(model_ids=("BTC.GAME", "BTC.TRACKER")), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-06", B.plan(model_ids=("P90",), intent=Intent.HISTORICAL_LINEAGE), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-07", B.plan(model_ids=("XAU.GAME",), scope=TimeScope.CURRENT), B.operator(), B.operator_context(), current, None, BASE_INDEX),
        ("Q2-08", B.plan(setup_ids=("SETUP.XAU.QUARTER_ZONE.V1",), intent=Intent.SETUP_CONTEXT), B.operator(), B.operator_context(), None, None, NO_GO_INDEX),
        ("Q2-09", B.plan(setup_ids=("SETUP.XAU.QUARTER_ZONE.V1",), intent=Intent.SETUP_CONTEXT), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-10", B.plan(setup_ids=("SETUP.FIB.REKEY.V1",), intent=Intent.SETUP_CONTEXT, depth=Depth.RESEARCHER), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-11", B.plan(setup_ids=("SETUP.JPY.CARRY_ROLE_GATE.V1",), intent=Intent.SETUP_CONTEXT), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-12", B.plan(model_ids=("MOD.XAU.CONFLICT.V1",), intent=Intent.COMPARISON), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-13", B.plan(model_ids=("MOD.XAU.INCOMPARABLE.V1",), intent=Intent.COMPARISON), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-14", B.plan(model_ids=("FIB",)), B.operator(), B.operator_context(), None, None, BASE_INDEX),
        ("Q2-15", B.plan(model_ids=("MOD.XAU.SECRET.V1",)), B.operator(), B.public_context(), None, None, BASE_INDEX),
        ("Q2-16", B.plan(model_ids=("XAU.GAME",)), B.operator(), B.operator_context(), None, _Leaky(SemanticCandidate("MOD.XAU.SECRET.V1", "hidden neighbour")), BASE_INDEX),
        ("Q2-17", B.plan(model_ids=("XAU.GAME",), scope=TimeScope.AS_OF), B.operator(), B.operator_context(), historical, None, BASE_INDEX),
        ("Q2-18", B.plan(model_ids=("XAU.GAME",)), B.operator(), B.operator_context(), None, _Leaky(SemanticCandidate("MOD.XAU.GAME.V1", "contradictory semantic text")), BASE_INDEX),
    )


def build_all() -> dict[str, str]:
    out: dict[str, str] = {}
    for name, plan, principal, context, snapshot, semantic, index in _scenarios():
        service = AskCerebusRetrievalService(index, semantic=semantic)
        bundle = service.retrieve(
            plan, principal, context, snapshot_context=snapshot
        )
        out[f"{name}.json"] = bundle.to_json() + "\n"
    return out


def build_manifest(files: dict[str, str]) -> str:
    payload = {
        "contract": "RETRIEVAL_CONTRACT_V1",
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
    files = build_all()
    for name, text in files.items():
        (expected / name).write_text(text, encoding="utf-8", newline="\n")
    (HERE / "FIXTURE_MANIFEST.json").write_text(
        build_manifest(files), encoding="utf-8", newline="\n"
    )
    print(json.dumps({"generated": len(files), "dir": str(expected)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["BASE_HEAD", "build_all", "build_manifest", "main", "_scenarios"]
