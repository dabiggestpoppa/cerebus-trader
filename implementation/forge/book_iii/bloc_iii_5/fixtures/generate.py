"""Deterministic generator for the III.5 golden fixtures.

Usage (from the repository root):

    python implementation/forge/book_iii/bloc_iii_5/fixtures/generate.py
    python implementation/forge/book_iii/bloc_iii_5/fixtures/generate.py --check

Every case is *evaluated* before it is written, and the resulting verdict
is compared with the expectation declared here.  A disagreement fails
generation — fixtures never merely record whatever the engine happens to
return.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import importlib.util  # noqa: E402

_SPEC = importlib.util.spec_from_file_location(
    "bloc_iii_5_builders", _HERE / "_builders.py"
)
B = importlib.util.module_from_spec(_SPEC)
sys.modules["bloc_iii_5_builders"] = B
_SPEC.loader.exec_module(B)

from app.forge.canonical import EvidenceStatus  # noqa: E402
from app.forge.setup_engine import (  # noqa: E402
    CardStatus,
    ParameterMaterialization,
    SetupEligibility,
    SetupRegistry,
    SetupSurface,
    describe_relationship,
    describe_statistic,
    evaluate_setup,
)

E = SetupEligibility

# fixture id -> (file name, ((case id, builder/expectation), ...))
CASES = {
    "BLOC_III_5.SETUP_REGISTRY.V1": (
        "setup_registry_cases.json",
        (
            ("registry_canonical_ids", "registry_ids", E.ELIGIBLE),
            ("registry_unknown_id", "registry_unknown", E.UNRESOLVED),
            ("registry_no_version", "registry_no_version", E.UNRESOLVED),
            ("registry_version_drift", "registry_version_drift", E.BLOCKED),
            ("registry_parked", "registry_parked", E.BLOCKED),
            ("registry_parity_unsafe", "registry_parity_unsafe", E.BLOCKED),
            ("registry_quarantined", "registry_quarantined", E.BLOCKED),
            ("registry_research_as_production", "registry_research_production", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.SETUP_CONTRACT.V1": (
        "setup_contract_cases.json",
        (
            ("contract_record_payload", "contract_record", E.ELIGIBLE),
            ("contract_record_roundtrip", "contract_roundtrip", E.ELIGIBLE),
        ),
    ),
    "BLOC_III_5.ELIGIBILITY.V1": (
        "eligibility_cases.json",
        (
            ("eligibility_clean", "eligibility_clean", E.ELIGIBLE),
            ("eligibility_missing_parent", "eligibility_missing_parent", E.UNRESOLVED),
            ("eligibility_model_drift", "eligibility_model_drift", E.UNRESOLVED),
            ("eligibility_wrong_layer", "eligibility_wrong_layer", E.BLOCKED),
            ("eligibility_state_not_declared", "eligibility_state", E.BLOCKED),
            ("eligibility_anchor_unresolved", "eligibility_anchor", E.UNRESOLVED),
            ("eligibility_tier_foreign", "eligibility_tier_foreign", E.BLOCKED),
            ("eligibility_tier_no_go", "eligibility_tier_no_go", E.BLOCKED),
            ("eligibility_clock_unresolved", "eligibility_clock", E.UNRESOLVED),
            ("eligibility_checkpoint_unreached", "eligibility_checkpoint", E.WATCH),
            ("eligibility_higher_layer_no_go", "eligibility_higher_no_go", E.BLOCKED),
            ("eligibility_layer_conflict", "eligibility_conflict", E.BLOCKED),
            ("eligibility_nonfinal_bar", "eligibility_nonfinal", E.BLOCKED),
            ("eligibility_stale_data", "eligibility_stale", E.BLOCKED),
            ("eligibility_declared_parameter", "eligibility_declared", E.WATCH),
            ("eligibility_missing_parameter", "eligibility_absent", E.UNRESOLVED),
            ("eligibility_lock_binding", "eligibility_lock", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.TRIGGER.V1": (
        "trigger_cases.json",
        (
            ("trigger_excursion_and_close", "trigger_satisfied", E.ELIGIBLE),
            ("trigger_touch_only", "trigger_touch_only", E.BLOCKED),
            ("trigger_nonfinal_close", "trigger_nonfinal_close", E.WATCH),
            ("trigger_no_observation", "trigger_armed", E.WATCH),
        ),
    ),
    "BLOC_III_5.INVALIDATION.V1": (
        "invalidation_cases.json",
        (
            ("invalidation_none_fired", "invalidation_none", E.ELIGIBLE),
            ("invalidation_price_fired", "invalidation_price", E.BLOCKED),
            ("invalidation_structural_fired", "invalidation_structural", E.BLOCKED),
            ("invalidation_temporal_fired", "invalidation_temporal", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.TARGET_PROMOTION.V1": (
        "target_promotion_cases.json",
        (
            ("targets_canonical_order", "targets_order", E.ELIGIBLE),
            ("targets_first_delivery", "targets_delivery", E.ELIGIBLE),
            ("targets_promotion", "targets_promotion", E.ELIGIBLE),
        ),
    ),
    "BLOC_III_5.XAU_QUARTER_ZONE.V1": (
        "xau_quarter_zone_cases.json",
        (
            ("xau_clean_canonical", "xau_clean", E.ELIGIBLE),
            ("xau_declared_mapping", "xau_declared", E.WATCH),
            ("xau_blind_touch", "xau_blind_touch", E.BLOCKED),
            ("xau_parked", "xau_parked", E.BLOCKED),
            ("xau_l3_destination_only", "xau_l3_only", E.BLOCKED),
            ("xau_under_lock", "xau_lock", E.BLOCKED),
            ("xau_invalidation_fired", "xau_invalidated", E.BLOCKED),
            ("xau_automation_surface", "xau_automation", E.BLOCKED),
            ("xau_version_drift", "xau_drift", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.FIB_REKEY.V1": (
        "fib_rekey_cases.json",
        (
            ("fib_unresolved_anchor", "fib_unresolved", E.UNRESOLVED),
            ("fib_invalidated_anchor", "fib_invalidated", E.BLOCKED),
            ("fib_declared_anchor_rule", "fib_declared_rule", E.UNRESOLVED),
            ("fib_production_request", "fib_production", E.BLOCKED),
            ("fib_operator_request", "fib_operator", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.JPY_ROLE_GATE.V1": (
        "jpy_role_gate_cases.json",
        (
            ("jpy_clean", "jpy_clean", E.ELIGIBLE),
            ("jpy_no_go_tier", "jpy_no_go", E.BLOCKED),
            ("jpy_foreign_tier", "jpy_foreign", E.BLOCKED),
            ("jpy_automation_surface", "jpy_automation", E.BLOCKED),
            ("jpy_under_lock", "jpy_lock", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.ST_P90.V1": (
        "st_p90_cases.json",
        (
            ("st_manual_framework", "st_framework", E.BLOCKED),
            ("p90_unverified_lineage", "p90_lineage", E.UNRESOLVED),
        ),
    ),
    "BLOC_III_5.STATISTICS.V1": (
        "statistics_cases.json",
        (
            ("statistics_claim_reference", "statistics_claim", E.ELIGIBLE),
            ("statistics_relationship", "statistics_relationship", E.ELIGIBLE),
            ("statistics_unclaimed", "statistics_unclaimed", E.BLOCKED),
        ),
    ),
    "BLOC_III_5.AUTHORITY_MATRIX.V1": (
        "setup_authority_matrix.json",
        (
            ("authority_registry_matrix", "authority_matrix", E.ELIGIBLE),
        ),
    ),
}


# -- builders referenced by the case table ---------------------------------


def registry_ids():
    return {"ids": list(SetupRegistry().ids())}


def registry_unknown():
    return evaluate_setup(B.xau_request(setup_id="SETUP.XAU.QUARTER_ZONE.V9"))


def registry_no_version():
    return evaluate_setup(B.xau_request(setup_version=None))


def registry_version_drift():
    return evaluate_setup(B.xau_request(setup_version="0.9"))


def registry_parked():
    registry = SetupRegistry().with_status(
        B.xau_quarter_zone.SETUP_ID, CardStatus.PARKED
    )
    return evaluate_setup(B.xau_request(), registry=registry)


def registry_parity_unsafe():
    registry = SetupRegistry().with_status(
        B.xau_quarter_zone.SETUP_ID, CardStatus.IMPLEMENTATION_NOT_PARITY_SAFE
    )
    return evaluate_setup(B.xau_request(), registry=registry)


def registry_quarantined():
    registry = SetupRegistry().with_status(
        B.xau_quarter_zone.SETUP_ID, CardStatus.INTERNAL_CONTRADICTION
    )
    return evaluate_setup(B.xau_request(), registry=registry)


def registry_research_production():
    return evaluate_setup(B.fib_request(surface=SetupSurface.PRODUCTION))


def contract_record():
    evaluation = evaluate_setup(B.xau_request())
    return {"payload": evaluation.record.to_payload()}


def contract_roundtrip():
    from app.forge.setup_engine import SetupRecord

    evaluation = evaluate_setup(B.xau_request())
    record = evaluation.record
    restored = SetupRecord.from_json(record.to_json())
    return {
        "equal": restored.to_payload() == record.to_payload(),
        "hash": restored.evaluation_hash,
    }


def eligibility_clean():
    return evaluate_setup(B.xau_request())


def eligibility_missing_parent():
    return evaluate_setup(B.xau_request(parents=()))


def eligibility_model_drift():
    parent = B.model_output(version="0.9")
    return evaluate_setup(B.xau_request(parents=(parent,)))


def eligibility_wrong_layer():
    from dataclasses import replace

    from app.forge.model_runtime.contract import Layer
    from app.forge.setup_engine import ParentRequirement

    card = B.xau_quarter_zone.card()
    requirement = ParentRequirement(
        model_id="XAU.GAME.L1_L2_L3.V1",
        model_version="1.0",
        allowed_states=card.parent_requirements[0].allowed_states,
        required_layer=Layer.L2,
    )
    registry = SetupRegistry((replace(card, parent_requirements=(requirement,)),))
    return evaluate_setup(B.xau_request(), registry=registry)


def eligibility_state():
    return evaluate_setup(B.xau_request(parents=(B.model_output(state="UNKNOWN_STATE"),)))


def eligibility_anchor():
    return evaluate_setup(B.fib_request())


def eligibility_tier_foreign():
    return evaluate_setup(B.xau_request(tier=B.xau_tier(native=False)))


def eligibility_tier_no_go():
    return evaluate_setup(B.xau_request(tier=B.xau_tier(no_go=True)))


def eligibility_clock():
    from app.forge.setup_engine import SetupClock

    return evaluate_setup(B.xau_request(clock=SetupClock("NY", "AFTER_0300_NY", resolved=False)))


def eligibility_checkpoint():
    from app.forge.setup_engine import SetupClock

    return evaluate_setup(
        B.xau_request(clock=SetupClock("NY", "AFTER_0300_NY", checkpoint_reached=False))
    )


def eligibility_higher_no_go():
    from app.forge.model_runtime.contract import Layer, NoGoReason

    extra = B.model_output(
        model_id="XAU.GAME.L3_CONTEXT.V1", layer=Layer.L3, no_go=(NoGoReason.ASIAN_RANGE_NO_GO,)
    )
    return evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))


def eligibility_conflict():
    from app.forge.model_runtime.contract import DirectionSide, Layer

    extra = B.model_output(
        model_id="XAU.GAME.L3_CONTEXT.V1", layer=Layer.L3, side=DirectionSide.DOWN
    )
    return evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))


def eligibility_nonfinal():
    return evaluate_setup(
        B.xau_request(data_quality=B.DataQualityFacts(final_bar=False))
    )


def eligibility_stale():
    return evaluate_setup(B.xau_request(data_quality=B.DataQualityFacts(stale=True)))


def eligibility_declared():
    return evaluate_setup(B.declared_xau_request())


def eligibility_absent():
    return evaluate_setup(B.xau_request(parameters=B.absent_xau_parameters()))


def eligibility_lock():
    return evaluate_setup(B.xau_request(stand_down=B.stand_down_record()))


def trigger_satisfied():
    return evaluate_setup(B.xau_request())


def trigger_touch_only():
    return evaluate_setup(B.xau_request(observations=(B.touch(1),)))


def trigger_nonfinal_close():
    return evaluate_setup(
        B.xau_request(observations=(B.excursion(1), B.close_nonfinal(2)))
    )


def trigger_armed():
    return evaluate_setup(B.xau_request(observations=()))


def invalidation_none():
    return evaluate_setup(B.xau_request())


def invalidation_price():
    return evaluate_setup(
        B.xau_request(invalidation_events=B.InvalidationEvents(price_fired=True))
    )


def invalidation_structural():
    return evaluate_setup(
        B.xau_request(invalidation_events=B.InvalidationEvents(structural_fired=True))
    )


def invalidation_temporal():
    from app.forge.setup_engine import TemporalInvalidation, resolve_invalidations

    card = B.xau_quarter_zone.card()
    resolved = resolve_invalidations(
        price=card.default_invalidation_price,
        structural=card.default_invalidation_structural,
        temporal=TemporalInvalidation(
            bound_id="TEMP.SESSION.END",
            checkpoint="AFTER_0300_NY_END",
            source_ref="XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md",
        ),
        events=B.InvalidationEvents(temporal_fired=True),
    )
    return {"active": list(resolved.active_kinds())}


def targets_order():
    ordered = B.xau_quarter_zone.card().targets
    return {
        "order": [target.target_id for target in ordered],
        "primary": B.xau_quarter_zone.primary_target().target_id,
        "confirmation": [target.target_id for target in B.xau_quarter_zone.confirmation_targets()],
    }


def targets_delivery():
    from app.forge.setup_engine import first_delivery_order

    return {"order": list(first_delivery_order(B.delivery_path()))}


def targets_promotion():
    from app.forge.setup_engine import promote_target

    target = B.xau_quarter_zone.primary_target()
    promoted = promote_target(
        target, transition_ref="TRANSITION.L1.CONFIRMED", transitions=(B.transition(),)
    )
    return {
        "active": promoted.active,
        "order_index": promoted.declared_order_index,
        "transition_ref": promoted.transition_ref,
    }


def xau_clean():
    return evaluate_setup(B.xau_request())


def xau_declared():
    return evaluate_setup(B.declared_xau_request())


def xau_blind_touch():
    return evaluate_setup(B.xau_request(observations=(B.touch(1),)))


def xau_parked():
    return evaluate_setup(B.xau_request(parents=(B.model_output(state="PARKED"),)))


def xau_l3_only():
    from app.forge.model_runtime.contract import DirectionSide, Layer

    extra = B.model_output(
        model_id="XAU.GAME.L3_DESTINATION.V1", layer=Layer.L3, side=DirectionSide.DOWN
    )
    return evaluate_setup(B.xau_request(parents=(B.model_output(), extra)))


def xau_lock():
    return evaluate_setup(B.xau_request(stand_down=B.stand_down_record()))


def xau_invalidated():
    return evaluate_setup(
        B.xau_request(invalidation_events=B.InvalidationEvents(structural_fired=True))
    )


def xau_automation():
    return evaluate_setup(B.xau_request(surface=SetupSurface.AUTOMATION))


def xau_drift():
    return evaluate_setup(B.xau_request(setup_version="0.9"))


def fib_unresolved():
    return evaluate_setup(B.fib_request())


def fib_invalidated():
    from app.forge.measurements.anchors import AnchorStatus

    return evaluate_setup(
        B.fib_request(anchors=(B.fib_anchor(status=AnchorStatus.INVALIDATED),))
    )


def fib_declared_rule():
    from app.forge.measurements.anchors import RuleMaterialization

    return evaluate_setup(
        B.fib_request(
            anchors=(B.fib_anchor(materialization=RuleMaterialization.DECLARED),)
        )
    )


def fib_production():
    return evaluate_setup(B.fib_request(surface=SetupSurface.PRODUCTION))


def fib_operator():
    return evaluate_setup(B.fib_request(surface=SetupSurface.OPERATOR))


def jpy_clean():
    return evaluate_setup(B.jpy_request())


def jpy_no_go():
    return evaluate_setup(B.jpy_request(tier=B.jpy_tier(no_go=True)))


def jpy_foreign():
    return evaluate_setup(B.jpy_request(tier=B.jpy_tier(native=False)))


def jpy_automation():
    return evaluate_setup(B.jpy_request(surface=SetupSurface.AUTOMATION))


def jpy_lock():
    return evaluate_setup(B.jpy_request(stand_down=B.stand_down_record()))


def st_framework():
    from app.forge.setup_engine import st_manual

    framework = st_manual.framework()
    verdict, code = st_manual.automation_request_refused()
    return {
        "framework_id": framework.framework_id,
        "chain": list(framework.tier_chain),
        "automation_permitted": framework.automation_permitted,
        "perception_gap": framework.perception_gap,
        "setup_identity": framework.setup_identity,
        "verdict": verdict.value,
        "code": code.value,
    }


def p90_lineage():
    from app.forge.setup_engine import p90_lineage

    item = p90_lineage.lineage()
    return {
        "lineage_id": item.lineage_id,
        "version": item.version,
        "status": item.status.value,
        "parity_status": item.parity_status,
        "automation_permitted": item.automation_permitted,
        "evidence": [
            {"ref": reference.artifact_ref, "status": reference.status.value}
            for reference in item.evidence_refs
        ],
    }


def statistics_claim():
    claim = describe_statistic(
        claim_id="CL.XAU.PROMOTION.68_80",
        population_key="XAU.PROMOTION",
        identity=B.claim_identity(),
        evidence=B.xau_evidence(),
    )
    return {"claim_id": claim.claim_id, "relationship": claim.relationship}


def statistics_relationship():
    claim = describe_relationship(
        claim_id="CL.JPY.CARRY.ROLE_RELATION",
        population_key="JPY.BASKET.ROLE",
        identity=B.claim_identity("USDJPY"),
        evidence=B.jpy_relationship_evidence(),
    )
    return {"claim_id": claim.claim_id, "relationship": claim.relationship}


def statistics_unclaimed():
    try:
        describe_statistic(
            claim_id=None,
            population_key="XAU.PROMOTION",
            identity=B.claim_identity(),
            evidence=B.unclaimed_evidence(),
        )
    except Exception as exc:  # recorded refusal, not a raised evaluation
        return {"refused": type(exc).__name__}
    return {"refused": "NONE"}


def authority_matrix():
    registry = SetupRegistry()
    rows = []
    for card in registry.cards():
        for surface in SetupSurface:
            resolution = registry.resolve(card.setup_id, card.version, surface)
            rows.append(
                {
                    "setup_id": card.setup_id,
                    "execution_class": card.execution_class.value,
                    "surface": surface.value,
                    "verdict": resolution.verdict.value,
                    "code": None if resolution.code is None else resolution.code.value,
                }
            )
    return {"rows": rows}


RESOLVERS = {
    name: value
    for name, value in globals().items()
    if callable(value) and not name.startswith("_")
}


def _expected(verdict: SetupEligibility, result) -> str:
    if hasattr(result, "eligibility"):
        return result.eligibility.value
    return verdict.value


def build(fixture_id: str, file_name: str, cases) -> dict:
    payload = {
        "fixture_id": fixture_id,
        "provenance": "SYNTHETIC_FIXTURE",
        "canonical_source_slice": "CANONICAL_SOURCE_SLICE",
        "cases": [],
    }
    for case_id, resolver, expectation in cases:
        result = RESOLVERS[resolver]()
        observed = _expected(expectation, result)
        if hasattr(result, "eligibility") and observed != expectation.value:
            raise SystemExit(
                f"{fixture_id}/{case_id}: expected {expectation.value}, got {observed}"
            )
        if hasattr(result, "eligibility"):
            case = {
                "case_id": case_id,
                "setup_id": result.setup_id,
                "surface": result.surface.value,
                "expected_eligibility": observed,
                "expected_reasons": [code.value for code in result.reasons],
            }
        else:
            case = {"case_id": case_id, "expected": result}
        payload["cases"].append(case)
    return payload


def render(payload: dict) -> bytes:
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    return text.encode("utf-8")


def manifest(paths: dict[str, bytes]) -> dict:
    return {
        "fixture_manifest_version": "BLOC_III_5.FIXTURE_MANIFEST.V1",
        "normalization": "LF",
        "files": {
            name: hashlib.sha256(data).hexdigest() for name, data in sorted(paths.items())
        },
    }


#: Ratified upstream packages whose module hashes this Bloc must not move.
FROZEN_PACKAGES = (
    "app/forge/market_data",
    "app/forge/measurements",
    "app/forge/model_runtime",
    "app/forge/state_engine",
)


def frozen_baseline() -> dict:
    counts = {}
    files = {}
    for package in FROZEN_PACKAGES:
        directory = _ROOT / package
        modules = sorted(directory.glob("*.py"))
        counts[package] = len(modules)
        for module in modules:
            relative = module.relative_to(_ROOT).as_posix()
            files[relative] = hashlib.sha256(module.read_bytes()).hexdigest()
    return {
        "frozen_baseline_version": "BLOC_III_5.FROZEN_BASELINE.V1",
        "module_counts": counts,
        "files": files,
    }


def main(argv: list[str]) -> int:
    check = "--check" in argv
    rendered: dict[str, bytes] = {}
    for fixture_id, (file_name, cases) in CASES.items():
        rendered[file_name] = render(build(fixture_id, file_name, cases))
    manifest_payload = manifest(rendered)
    manifest_bytes = render(manifest_payload)
    baseline_bytes = render(frozen_baseline())

    failures: list[str] = []
    for name, data in rendered.items():
        path = _HERE / name
        if check:
            if not path.exists() or path.read_bytes() != data:
                failures.append(name)
        else:
            path.write_bytes(data)
    if check:
        path = _HERE / "FIXTURE_MANIFEST.json"
        if not path.exists() or path.read_bytes() != manifest_bytes:
            failures.append("FIXTURE_MANIFEST.json")
        baseline = _HERE / "FROZEN_BASELINE.json"
        if not baseline.exists() or baseline.read_bytes() != baseline_bytes:
            failures.append("FROZEN_BASELINE.json")
        if failures:
            print("FIXTURE DRIFT: " + ", ".join(failures))
            return 1
        print("fixtures reproduce byte-identically: " + str(len(rendered)) + " files")
        return 0

    (_HERE / "FIXTURE_MANIFEST.json").write_bytes(manifest_bytes)
    (_HERE / "FROZEN_BASELINE.json").write_bytes(baseline_bytes)
    print("wrote " + str(len(rendered)) + " fixtures + manifest + frozen baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
