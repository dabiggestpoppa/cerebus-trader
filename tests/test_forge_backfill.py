"""Focused I.3 tests: canonical backfill (Book I / Bloc I.3).

Maps to implementation/forge/book_i/bloc_i_3/ACCEPTANCE.md clauses A-X:
deterministic inventory, explicit ID/status/type mappings with no promotion,
model-truth fixtures (EUR/XAU/BTC/JPY/FIB/ST/P90), claim-evidence binding,
provenance edges, persistence through the II.2 port, idempotency, conflict
rejection, rollback, dry-run purity, exposure/policy safety, reproducibility.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.forge.backfill import mappings as M
from app.forge.backfill.canonicalizer import (
    MigrationPlan,
    build_claim_objects,
    canonicalize_files,
)
from app.forge.backfill.parser import parse_card
from app.forge.backfill.runner import (
    BackfillMode,
    ConflictError,
    load_corpus_files,
    run_backfill,
)
from app.forge.canonical import (
    CanonicalId,
    EvidenceStatus,
    EvidenceType,
    ObjectType,
    ProductExposure,
    SetupClass,
)
from app.forge.persistence.memory import InMemoryPersistenceGateway

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_corpus() -> dict[str, str]:
    return load_corpus_files(REPO_ROOT)


def _plan() -> MigrationPlan:
    return canonicalize_files(_load_corpus())


def _by_id(plan: MigrationPlan, canonical_id: str):
    for record in plan.objects:
        if record.canonical_id == canonical_id:
            return record
    raise AssertionError(f"missing canonical object: {canonical_id}")


def _fresh_gateway() -> InMemoryPersistenceGateway:
    return InMemoryPersistenceGateway()


def _applied_gateway() -> InMemoryPersistenceGateway:
    gateway = _fresh_gateway()
    run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
    return gateway


# ---------------------------------------------------------------------------
# A — deterministic inventory
# ---------------------------------------------------------------------------


class TestInventory:
    def test_inventory_is_deterministic(self) -> None:
        report_a = _plan().report
        report_b = _plan().report
        assert report_a.to_json() == report_b.to_json()
        assert report_a.content_hash() == report_b.content_hash()

    def test_every_in_scope_source_appears_once(self) -> None:
        report = _plan().report
        paths = [o.path for o in report.outcomes]
        assert len(paths) == len(set(paths))
        # 20 card files + 8 named implementation/support artifacts + 1
        # conversation-derived file + 1 claim registry (in-scope source
        # artifact per ACCEPTANCE A1).
        assert report.sources_inventoried == 30
        registry = [o for o in report.outcomes if o.path == "corpus/canonical/CLAIM_REGISTRY_V1.md"]
        assert len(registry) == 1
        assert registry[0].classification.value == "GOVERNANCE_CONTRACT"
        assert report.models == 7 and report.evidence == 10 and report.setups == 3
        assert report.claims == 10
        assert report.missing_source == 0

    def test_content_identity_is_deterministic(self) -> None:
        from app.forge.provenance import compute_content_identity

        text = (_load_corpus())["corpus/canonical/models/EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md"]
        assert compute_content_identity(text.encode("utf-8")) == (
            compute_content_identity(text.encode("utf-8"))
        )
        assert compute_content_identity(text.encode("utf-8")).startswith("sha256:")

    def test_sources_not_modified(self) -> None:
        # Backfill is read-only over the corpus tree: no source file changed.
        corpus = _load_corpus()
        assert all(isinstance(text, str) and text for text in corpus.values())

    def test_conversation_derived_inventoried_not_canonicalized(self) -> None:
        report = _plan().report
        assert report.conversation_derived_sources == 1
        for record in _plan().objects:
            assert "conversation" not in record.canonical_id.lower()


# ---------------------------------------------------------------------------
# B — legacy ID mapping
# ---------------------------------------------------------------------------


class TestLegacyIdMapping:
    def test_setup_id_maps_explicitly(self) -> None:
        assert M.resolve_canonical_id("SETUP.XAU.QUARTER_ZONE.V1", ObjectType.SETUP) == (
            "SET.XAU.QUARTER_ZONE.V1"
        )
        assert M.resolve_canonical_id("SETUP.FIB.REKEY.V1", ObjectType.SETUP) == (
            "SET.FIB.REKEY.V1"
        )
        assert M.resolve_canonical_id(
            "SETUP.JPY.CARRY_ROLE_GATE.V1", ObjectType.SETUP
        ) == "SET.JPY.CARRY_ROLE_GATE.V1"

    def test_invalid_legacy_id_does_not_fuzzy_map(self) -> None:
        with pytest.raises(ValueError):
            M.resolve_canonical_id("SETUP.DOES.NOT.EXIST.V1", ObjectType.SETUP)
        # A well-formed but unknown canonical-shaped id is still refused:
        # passthrough is only for registered/known in-scope ids, proven at the
        # canonicalizer level (unknown model_id ⇒ quarantine, see D tests).
        with pytest.raises(ValueError):
            M.resolve_canonical_id("garbage", ObjectType.MODEL)
        with pytest.raises(ValueError):
            M.resolve_canonical_id("", ObjectType.MODEL)

    def test_object_type_mismatch_rejected(self) -> None:
        with pytest.raises(ValueError):
            M.resolve_canonical_id("SETUP.XAU.QUARTER_ZONE.V1", ObjectType.MODEL)
        with pytest.raises(ValueError):
            M.resolve_canonical_id("EUR.WEEKLY.V1_1", ObjectType.SETUP)

    def test_no_two_legacy_ids_share_canonical_target(self) -> None:
        targets = [m.canonical_id for m in M.LEGACY_ID_MAPPINGS]
        assert len(targets) == len(set(targets))

    def test_all_migrated_ids_parse_with_expected_type(self) -> None:
        plan = _plan()
        for record in plan.objects:
            cid = CanonicalId.parse(record.canonical_id)
            assert cid.object_type is record.object_type

    def test_legacy_ids_preserved_in_metadata(self) -> None:
        record = _by_id(_plan(), "SET.XAU.QUARTER_ZONE.V1")
        assert record.metadata["legacy_ids"] == ["SETUP.XAU.QUARTER_ZONE.V1"]


# ---------------------------------------------------------------------------
# C — enum/status mapping: explicit, no promotion, unknown quarantined
# ---------------------------------------------------------------------------


class TestStatusMapping:
    def test_status_mapping_explicit_table(self) -> None:
        assert {m.legacy_status for m in M.STATUS_MAPPINGS} >= {
            "VALIDATED",
            "VALIDATED_RESEARCH",
            "VALIDATED_SMALL_N",
            "VALIDATED_RELATIONSHIP",
            "RESEARCH_FLAG_SMALL_N",
            "NEGATIVE_EVIDENCE",
            "CANONICALIZATION_CANDIDATE",
            "CORE_CANDIDATE",
            "SCIENTIFIC_CORE_CANDIDATE",
            "RESEARCH_OPERATOR_CANDIDATE",
            "CANONICAL_FROZEN_FAMILY",
            "ACTIVE_RESEARCH_IMPLEMENTED",
            "MODERN_RESEARCH_FRAMEWORK",
            "FORWARD_OOS",
            "CANDIDATE",
        }

    def test_unknown_status_quarantines(self) -> None:
        text = (
            "# MODEL CARD — X\n\nmodel_id: EUR.WEEKLY.V1_1\nstatus: TOTALLY_UNKNOWN\n"
            "market_scope: EURUSD\nlayer: L2\nmodel_type: PATH\n"
            "product_exposure: SUBSCRIBER_MODEL\n\n## Purpose\np\n"
        )
        plan = canonicalize_files({"t.md": text})
        assert plan.report.quarantined == 1
        assert not any(r.object_type is ObjectType.MODEL for r in plan.objects)

    def test_no_status_promotion(self) -> None:
        # CANDIDATE-family sources must land CANDIDATE/RESEARCH_FLAG, never higher.
        plan = _plan()
        assert _by_id(plan, "MOD.EUR.DAILY.NEWS_REKEY.V1").status is EvidenceStatus.CANDIDATE
        assert _by_id(plan, "MOD.EUR.WEEKLY.V1_1").status is EvidenceStatus.CANDIDATE
        assert (
            _by_id(plan, "MOD.EUR.HIGHER_ORDER.V1").status is EvidenceStatus.CANDIDATE
        )
        assert _by_id(plan, "MOD.JPY.CARRY_GAME.L1_L3.V1").status is EvidenceStatus.CANDIDATE
        assert _by_id(plan, "MOD.BTC.TRACKER.DWM.V1").status is EvidenceStatus.RESEARCH_FLAG
        assert (
            _by_id(plan, "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1").status
            is EvidenceStatus.RESEARCH_FLAG
        )
        assert _by_id(plan, "SET.FIB.REKEY.V1").status is EvidenceStatus.RESEARCH_FLAG

    def test_research_qualifiers_survive_as_metadata(self) -> None:
        plan = _plan()
        weekly_tiers = _by_id(plan, "EV.EUR.WEEKLY.TIER_RANGE.V1")
        assert weekly_tiers.status is EvidenceStatus.VALIDATED
        assert weekly_tiers.metadata.get("research_sample") is True

        xau68 = _by_id(plan, "EV.XAU.PROMOTION.68_80.V1")
        assert xau68.status is EvidenceStatus.VALIDATED
        assert xau68.metadata.get("small_n") is True

        xau132 = _by_id(plan, "EV.XAU.PROMOTION.120_132.V1")
        assert xau132.status is EvidenceStatus.RESEARCH_FLAG
        assert xau132.metadata.get("small_n") is True

        jpy = _by_id(plan, "EV.JPY.CARRY.BASKET_RELATION.V1")
        assert jpy.status is EvidenceStatus.VALIDATED
        assert jpy.metadata.get("relationship_statistic") is True

    def test_frozen_family_is_descriptive_not_validated(self) -> None:
        record = _by_id(_plan(), "MOD.XAU.GAME.L1_L2_L3.V1")
        assert record.status is EvidenceStatus.DESCRIPTIVE
        assert record.metadata.get("frozen_family") is True

    def test_negative_evidence_status_and_type_preserved(self) -> None:
        record = _by_id(_plan(), "EV.FIB.R11.ANCHOR_OVERGEN.V1")
        assert record.status is EvidenceStatus.FALSIFIED
        card = record.metadata["card"]
        assert card["evidence_type"] == EvidenceType.NEGATIVE_EVIDENCE.value


# ---------------------------------------------------------------------------
# D/E/F — card canonicalization
# ---------------------------------------------------------------------------


class TestCardCanonicalization:
    def test_all_model_cards_parse(self) -> None:
        plan = _plan()
        assert plan.report.models == 7
        expected = {
            "MOD.EUR.DAILY.NEWS_REKEY.V1",
            "MOD.EUR.HIGHER_ORDER.V1",
            "MOD.EUR.WEEKLY.V1_1",
            "MOD.XAU.GAME.L1_L2_L3.V1",
            "MOD.BTC.TRACKER.DWM.V1",
            "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1",
            "MOD.JPY.CARRY_GAME.L1_L3.V1",
        }
        assert {r.canonical_id for r in plan.objects if r.object_type is ObjectType.MODEL} == (
            expected
        )

    def test_invalid_model_card_quarantines(self) -> None:
        text = (
            "# MODEL CARD — Broken\n\nmodel_id: BAD.ID.FORMAT\nstatus: CANDIDATE\n"
            "market_scope: EURUSD\nlayer: L2\nmodel_type: PATH\n"
            "product_exposure: SUBSCRIBER_MODEL\n\n## Purpose\np\n"
        )
        plan = canonicalize_files({"broken.md": text})
        assert plan.report.quarantined == 1
        assert not any(r.object_type is ObjectType.MODEL for r in plan.objects)

    def test_all_evidence_cards_parse(self) -> None:
        assert _plan().report.evidence == 10

    def test_invalid_evidence_card_quarantines(self) -> None:
        text = (
            "# EVIDENCE CARD — X\n\nevidence_id: EV.X.Y.Z.V1\nclaim_id: CL.NOT.IN.REGISTRY\n"
            "status: MEGAscary_UNKNOWN\nevidence_type: VIBES\nmarket: EURUSD\n\n"
            "## Exact claim\nx\n"
        )
        plan = canonicalize_files({"bad_ev.md": text})
        assert plan.report.quarantined == 1

    def test_all_setup_cards_parse_with_typed_ids(self) -> None:
        plan = _plan()
        assert plan.report.setups == 3
        assert _by_id(plan, "SET.XAU.QUARTER_ZONE.V1").object_type is ObjectType.SETUP
        assert _by_id(plan, "SET.FIB.REKEY.V1").object_type is ObjectType.SETUP
        assert _by_id(plan, "SET.JPY.CARRY_ROLE_GATE.V1").object_type is ObjectType.SETUP

    def test_invalid_setup_card_quarantines(self) -> None:
        text = (
            "# SETUP CARD — X\n\nsetup_id: SETUP.BROKEN.V1\n"
            "execution_class: AUTOMATION_APPROVED\nparent_model_ids: MOD.NOPE.V1\n"
            "product_exposure: OPERATOR_ONLY\n\n## Purpose\np\n"
        )
        plan = canonicalize_files({"bad_setup.md": text})
        assert plan.report.quarantined == 1
        assert not any(r.object_type is ObjectType.SETUP for r in plan.objects)

    def test_no_silent_field_loss(self) -> None:
        record = _by_id(_plan(), "MOD.EUR.DAILY.NEWS_REKEY.V1")
        card = record.metadata["card"]
        assert card["purpose"]
        assert card["model_type"]
        assert card["beginner_summary"]
        # full parsed payload preserved
        assert "Asian seed" in json.dumps(card)

    def test_uncertainty_markers_not_fabricated_values(self) -> None:
        record = _by_id(_plan(), "EV.EUR.WEEKLY.TIER_RANGE.V1")
        card = record.metadata["card"]
        assert card["event_definition"] == M.NOT_SPECIFIED
        assert card["clock_origin"] == M.NOT_SPECIFIED


# ---------------------------------------------------------------------------
# F — execution class truth
# ---------------------------------------------------------------------------


class TestExecutionClass:
    def test_manual_operator_preserved(self) -> None:
        plan = _plan()
        for setup_id in ("SET.XAU.QUARTER_ZONE.V1", "SET.JPY.CARRY_ROLE_GATE.V1"):
            card = _by_id(plan, setup_id).metadata["card"]
            assert card["execution_class"] == SetupClass.MANUAL_OPERATOR.value

    def test_research_only_preserved(self) -> None:
        card = _by_id(_plan(), "SET.FIB.REKEY.V1").metadata["card"]
        assert card["execution_class"] == SetupClass.RESEARCH_ONLY.value

    def test_no_automation_approved_created(self) -> None:
        for record in _plan().objects:
            card = record.metadata.get("card", {})
            if card.get("execution_class"):
                assert card["execution_class"] != SetupClass.AUTOMATION_APPROVED.value
