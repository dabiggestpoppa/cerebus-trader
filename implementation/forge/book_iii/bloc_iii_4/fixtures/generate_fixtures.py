"""Deterministic golden-fixture generator for Bloc III.4.

Run from anywhere:

    python implementation/forge/book_iii/bloc_iii_4/fixtures/generate_fixtures.py

It writes the twelve `BLOC_III_4.*.V1` fixtures plus the LF-normalized
`FIXTURE_MANIFEST.json`.  Every fixture is provenance-labelled:
`SYNTHETIC_FIXTURE` values are structural validation material only, and
`CANONICAL_SOURCE_SLICE` values are canonical constants quoted verbatim
from the ratified III.2/III.3 registries and frozen model cards.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import _builders as B  # noqa: E402

from app.forge.market_data import DataOutcome  # noqa: E402
from app.forge.model_runtime import ProductionAuthorization, compute_hash  # noqa: E402
from app.forge.state_engine import (  # noqa: E402
    EUR_DAILY_LADDER,
    TRANSITION_AUTHORITY,
    STATE_ENGINE_CODES,
    STATE_ENGINE_VERSION,
    DeliveryObservation,
    DeliverySide,
    DeclaredTarget,
    FailureState,
    TransitionKind,
    advance_failure,
    build_path,
    failure_grammar_for,
    start_failure_chain,
)

SYNTHETIC = "SYNTHETIC_FIXTURE — structural validation material only; not empirical evidence"
CANONICAL = "CANONICAL_SOURCE_SLICE — canonical constants quoted from frozen cards/registries"


def write(name: str, payload: dict) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    (HERE / name).write_text(text, encoding="utf-8", newline="\n")


def state_snapshots() -> dict:
    snapshots = B.build_family_snapshots()
    return {
        "fixture_id": "BLOC_III_4.STATE_SNAPSHOTS.V1",
        "data_classification": SYNTHETIC,
        "engine_version": STATE_ENGINE_VERSION,
        "snapshots": [
            {
                "family": family,
                "model_id": snapshot.model_id,
                "model_version": snapshot.model_version,
                "layer": snapshot.layer.value,
                "active_state": snapshot.active_state,
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_hash": snapshot.snapshot_hash,
                "source_output_hash": snapshot.source_output_hash,
                "production_authorization": snapshot.production_authorization.value,
                "quality_state": snapshot.quality_state.value,
                "claim_refs": list(snapshot.claim_refs),
                "evidence_refs": list(snapshot.evidence_refs),
            }
            for family, snapshot in snapshots.items()
        ],
    }


def transition_vocabulary() -> dict:
    return {
        "fixture_id": "BLOC_III_4.TRANSITION_VOCABULARY.V1",
        "data_classification": CANONICAL,
        "kinds": [kind.value for kind in TransitionKind],
        "families": {
            family: {
                "model_id": entry.model_id,
                "model_version": entry.model_version,
                "allowed": sorted(kind.value for kind in entry.allowed),
                "restricted": sorted(kind.value for kind in entry.restricted),
                "unresolved": sorted(kind.value for kind in entry.unresolved),
            }
            for (model_id, model_version), entry in TRANSITION_AUTHORITY.items()
            for family in [entry.family]
        },
    }


def first_delivery() -> dict:
    cases = []
    for case in B.build_contract_cases()["first_delivery"]:
        if "expected_error" in case:
            cases.append(case)
            continue
        targets = tuple(
            DeclaredTarget(target_id=tid, side=DeliverySide(side), declared_order_index=idx)
            for tid, side, idx in case["targets"]
        )
        observations = tuple(
            DeliveryObservation(
                target_id=tid,
                realized_event_time=__import__("datetime").datetime.fromisoformat(when),
                realizing_bar_ref=bar,
            )
            for tid, when, bar in case["hits"]
        )
        path = build_path(clock_id="CLOCK.UTC", targets=targets, observations=observations)
        payload = path.to_payload()
        cases.append(
            {
                **case,
                "expected_order": list(path.delivery_order),
                "terminal": path.terminal_reach.value,
                "first_delivery": path.first_delivery.target_id if path.first_delivery else None,
                "path_hash": compute_hash(payload),
            }
        )
    return {
        "fixture_id": "BLOC_III_4.FIRST_DELIVERY.V1",
        "data_classification": SYNTHETIC,
        "cases": cases,
    }


def failure_repair() -> dict:
    grammar = failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
    chain = start_failure_chain(
        "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=B.TS
    )
    chain = advance_failure(
        chain,
        TransitionKind.ACCEPT,
        grammar=grammar,
        event_time=B.T1,
        acceptance_ref="ACCEPTANCE.1",
    )
    chain = advance_failure(
        chain, TransitionKind.FAIL, grammar=grammar, event_time=B.T2
    )
    chain = advance_failure(
        chain, TransitionKind.REPAIR, grammar=grammar, event_time=B.T3
    )
    return {
        "fixture_id": "BLOC_III_4.FAILURE_REPAIR.V1",
        "data_classification": CANONICAL,
        "grammars": ["EUR.DAILY.NEWS_REKEY.V1@PHASE1", "XAU.GAME.L1_L2_L3.V1@V1"],
        "states": [state.value for state in FailureState],
        "cases": B.build_contract_cases()["failure_repair"],
        "golden_chain": {
            "rule_id": grammar.rule.rule_id,
            "steps": list(chain.steps),
            "state": chain.state.value,
            "acceptance_ref": chain.acceptance_ref,
        },
    }


def rekey() -> dict:
    return {
        "fixture_id": "BLOC_III_4.REKEY.V1",
        "data_classification": CANONICAL,
        "eur_daily_ladder": list(EUR_DAILY_LADDER),
        "cases": B.build_contract_cases()["rekey"],
    }


def layer_handoff() -> dict:
    return {
        "fixture_id": "BLOC_III_4.LAYER_HANDOFF.V1",
        "data_classification": SYNTHETIC,
        "cases": B.build_contract_cases()["layer_handoff"],
    }


def range_left() -> dict:
    return {
        "fixture_id": "BLOC_III_4.RANGE_LEFT.V1",
        "data_classification": SYNTHETIC,
        "cases": B.build_contract_cases()["range_left"],
    }


def stand_down() -> dict:
    from app.forge.model_runtime import NoGoReason

    reasons = [NoGoReason(name) for name in B.build_contract_cases()["stand_down"]]
    return {
        "fixture_id": "BLOC_III_4.STAND_DOWN.V1",
        "data_classification": CANONICAL,
        "mapping": [B.stand_down_case(reason) for reason in reasons],
    }


def transition_history() -> dict:
    genesis, snapshots, ledger = B.build_eur_daily_ledger()
    return {
        "fixture_id": "BLOC_III_4.TRANSITION_HISTORY.V1",
        "data_classification": SYNTHETIC,
        "genesis_snapshot_id": ledger.genesis_snapshot_id,
        "genesis_snapshot_hash": ledger.genesis_snapshot_hash,
        "events": [
            {
                "sequence": event.sequence,
                "event_id": event.event_id,
                "kind": event.kind.value,
                "prior_state": event.prior_state,
                "resulting_state": event.resulting_state,
                "resulting_state_id": event.resulting_state_id,
                "source_snapshot_ref": event.source_snapshot_ref,
                "rule_id": event.rule_id,
                "event_hash": event.event_hash,
                "prev_event_hash": event.prev_event_hash,
            }
            for event in ledger.events
        ],
        "history_hash": ledger.history_hash,
        "current_state": ledger.current_state,
        "negative_events": [event.event_id for event in ledger.negative_events()],
    }


def path_invariants() -> dict:
    cases = first_delivery()["cases"]
    ab = next(case for case in cases if case["case_id"] == "ORDER_AB")
    ba = next(case for case in cases if case["case_id"] == "ORDER_BA")
    return {
        "fixture_id": "BLOC_III_4.PATH_INVARIANTS.V1",
        "data_classification": SYNTHETIC,
        "same_terminal_result": ab["terminal"],
        "order_ab_hash": ab["path_hash"],
        "order_ba_hash": ba["path_hash"],
        "hashes_differ": ab["path_hash"] != ba["path_hash"],
    }


def family_authority() -> dict:
    entries = []
    all_kinds = [kind.value for kind in TransitionKind]
    for (model_id, model_version), entry in TRANSITION_AUTHORITY.items():
        allowed = {kind.value for kind in entry.allowed}
        unresolved = {kind.value for kind in entry.unresolved}
        entries.append(
            {
                "family": entry.family,
                "model_id": model_id,
                "model_version": model_version,
                "layer": entry.layer.value,
                "canonical_sources": sorted(entry.canonical_source_refs),
                "states": sorted(entry.states),
                "allowed": sorted(allowed),
                "restricted": sorted(kind.value for kind in entry.restricted),
                "unresolved": sorted(unresolved),
                "never": sorted(set(all_kinds) - allowed),
                "canonical_only_targets": sorted(entry.canonical_only_targets),
                "forbidden_pairs": [list(pair) for pair in sorted(entry.forbidden_pairs)],
            }
        )
    return {
        "fixture_id": "BLOC_III_4.FAMILY_AUTHORITY.V1",
        "data_classification": CANONICAL,
        "engine_codes": list(STATE_ENGINE_CODES),
        "entries": entries,
    }


def replay_hashes() -> dict:
    snapshots = B.build_family_snapshots()
    _genesis, _snapshots, ledger = B.build_eur_daily_ledger()
    return {
        "fixture_id": "BLOC_III_4.REPLAY_HASHES.V1",
        "data_classification": SYNTHETIC,
        "snapshot_hashes": {
            family: snapshot.snapshot_hash for family, snapshot in snapshots.items()
        },
        "history_hash": ledger.history_hash,
        "event_hashes": list(ledger.event_hashes),
        "engine_version": STATE_ENGINE_VERSION,
    }


BUILDERS = {
    "state_snapshots.json": state_snapshots,
    "transition_vocabulary_cases.json": transition_vocabulary,
    "first_delivery_cases.json": first_delivery,
    "failure_repair_cases.json": failure_repair,
    "rekey_cases.json": rekey,
    "layer_handoff_cases.json": layer_handoff,
    "range_left_cases.json": range_left,
    "stand_down_cases.json": stand_down,
    "transition_history_cases.json": transition_history,
    "path_invariants_cases.json": path_invariants,
    "model_family_transition_authority.json": family_authority,
    "replay_hashes.json": replay_hashes,
}


def main() -> None:
    for name, builder in BUILDERS.items():
        write(name, builder())
    files = {}
    for name in sorted(BUILDERS):
        raw = (HERE / name).read_bytes().replace(b"\r\n", b"\n")
        files[name] = hashlib.sha256(raw).hexdigest()
    write(
        "FIXTURE_MANIFEST.json",
        {
            "algorithm": "sha256",
            "description": (
                "Deterministic committed golden fixtures for Bloc III.4. Hashes "
                "cover every JSON fixture in this directory except this manifest. "
                "Hashes are recorded over LF-normalized content, so the manifest "
                "verifies identically on Windows (CRLF worktrees) and Linux CI "
                "(LF checkouts)."
            ),
            "engine_version": STATE_ENGINE_VERSION,
            "files": files,
            "generator": "generate_fixtures.py",
            "provenance": {
                "canonical_constants": CANONICAL,
                "contract_cases": SYNTHETIC,
                "history_hashes": SYNTHETIC,
                "snapshot_hashes": SYNTHETIC,
            },
        },
    )
    print(f"wrote {len(BUILDERS) + 1} fixture files to {HERE}")


if __name__ == "__main__":
    main()
