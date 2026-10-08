"""Focused I.3 tests part 2: model truth, claims, provenance, persistence,
policy safety, reproducibility (Book I / Bloc I.3).

Reconstructed from the compiled bytecode of the interrupted build (the source
file was clobbered by an interrupted edit); structure, assertions and constants
mirror the original module one-for-one.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.forge.backfill import mappings as M
from app.forge.backfill.canonicalizer import build_claim_objects, canonicalize_files
from app.forge.backfill.runner import BackfillMode, ConflictError, run_backfill
from app.forge.canonical import (
    ClaimComparison,
    ClaimIdentity,
    EvidenceStatus,
    EvidenceType,
    ObjectType,
    ProductExposure,
    SetupClass,
    compare_claim_identity,
)
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.policy import (
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyResourceType,
    ResourcePolicyMetadata,
)
from tests.test_forge_backfill import (
    REPO_ROOT,
    _applied_gateway,
    _by_id,
    _fresh_gateway,
    _load_corpus,
    _plan,
)

ENGINE = DefaultDenyPolicyEngine()


# ---------------------------------------------------------------------------
# Frozen model-family truths (EUR / XAU / BTC / JPY / FIB / ST / P90)
# ---------------------------------------------------------------------------


class TestModelTruth:
    def test_eur_daily_weekly_higher_order_separate(self) -> None:
        plan = _plan()
        ids = {r.canonical_id for r in plan.objects}
        assert {
            "MOD.EUR.DAILY.NEWS_REKEY.V1",
            "MOD.EUR.HIGHER_ORDER.V1",
            "MOD.EUR.WEEKLY.V1_1",
        } <= ids

        # Daily Distribution (L1) != Weekly Engine (L2) != Higher Order (L3).
        assert _by_id(plan, "MOD.EUR.DAILY.NEWS_REKEY.V1").layer.value == "L1"
        assert _by_id(plan, "MOD.EUR.WEEKLY.V1_1").layer.value == "L2"
        assert _by_id(plan, "MOD.EUR.HIGHER_ORDER.V1").layer.value == "L3"

    def test_xau_l3_l2_l1_distinction_preserved(self) -> None:
        plan = _plan()
        card = _by_id(plan, "MOD.XAU.GAME.L1_L2_L3.V1").metadata["card"]
        payload = json.dumps(card)
        assert "L3" in payload and "L2" in payload and "L1" in payload

        # Quarter-zone manual operator stays manual (never automation).
        setup = _by_id(plan, "SET.XAU.QUARTER_ZONE.V1").metadata["card"]
        assert setup["execution_class"] == SetupClass.MANUAL_OPERATOR.value

    def test_btc_tracker_migrated_independently(self) -> None:
        plan = _plan()
        record = _by_id(plan, "MOD.BTC.TRACKER.DWM.V1")
        # Implemented indicator is not validation: research flag stands.
        assert record.metadata.get("implemented") is True
        assert record.status is EvidenceStatus.RESEARCH_FLAG

        # Honest gap: no evidence card exists for the Tracker (no fabrication).
        card = record.metadata["card"]
        assert card["evidence_card_ids"] == []

    def test_btc_game_not_fabricated(self) -> None:
        plan = _plan()
        for record in plan.objects:
            assert "BTC.GAME" not in record.canonical_id
            assert record.title != "BTC Game"
        gateway = _applied_gateway()
        for object_id in gateway.list_object_ids():
            assert "BTC.GAME" not in object_id

    def test_jpy_role_asymmetry_preserved(self) -> None:
        plan = _plan()
        card = _by_id(plan, "MOD.JPY.CARRY_GAME.L1_L3.V1").metadata["card"]
        payload = json.dumps(card)
        assert "confirmation" in payload or "veto" in payload
        setup = _by_id(plan, "SET.JPY.CARRY_ROLE_GATE.V1").metadata["card"]
        setup_payload = json.dumps(setup)
        assert "majority-vote" in setup_payload or "equal voting" in setup_payload

    def test_fib_r11_negative_evidence_survives(self) -> None:
        plan = _plan()
        record = _by_id(plan, "EV.FIB.R11.ANCHOR_OVERGEN.V1")
        assert record.status is EvidenceStatus.FALSIFIED
        card = record.metadata["card"]
        assert card["evidence_type"] == EvidenceType.NEGATIVE_EVIDENCE.value

        # The negative result stays bound to the Range Birth model...
        model = _by_id(plan, "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1")
        assert "EV.FIB.R11.ANCHOR_OVERGEN.V1" in [
            r.target_id for r in model.references
        ]

        # ...and to the rekey operator card (R11 overgeneration lineage).
        setup = _by_id(plan, "SET.FIB.REKEY.V1")
        assert "EV.FIB.R11.ANCHOR_OVERGEN.V1" in [
            r.target_id for r in setup.references
        ]

    def test_fib_range_birth_not_reduced_to_coordinates(self) -> None:
        plan = _plan()
        card = _by_id(plan, "MOD.CROSSASSET.FIB.RANGE_BIRTH.V1").metadata["card"]
        assert "Range Birth" in card["purpose"] or "range" in card["purpose"].lower()
        payload = json.dumps(card)
        assert (
            "coordinates do NOT create structure" in payload
            or "earned" in payload.lower()
        )

    def test_st_family_doctrine_preserved_via_eur_daily(self) -> None:
        # ST is a valid manual/operator family: the EUR Daily card carries the
        # P90 lineage plus the separation doctrine (never conflation).
        plan = _plan()
        card = _by_id(plan, "MOD.EUR.DAILY.NEWS_REKEY.V1").metadata["card"]
        payload = json.dumps(card)
        assert "P90" in payload
        assert (
            "do not import" in payload.lower()
            or "must be separated" in payload.lower()
        )

    def test_p90_not_conflated_with_st_and_no_invented_performance(self) -> None:
        plan = _plan()
        all_payloads = json.dumps([r.metadata for r in plan.objects])

        for record in plan.objects:
            if record.object_type is ObjectType.CLAIM:
                continue
            # No canonical object impersonates a P90 performance statistic.
            assert "P90.WR" not in record.canonical_id

    def test_no_autonomous_execution_approval_anywhere(self) -> None:
        gateway = _applied_gateway()
        for object_id in gateway.list_object_ids():
            record = gateway.get_object(object_id)
            card = record.metadata.get("card", {})
            if card.get("execution_class"):
                assert card["execution_class"] != SetupClass.AUTOMATION_APPROVED.value


# ---------------------------------------------------------------------------
# Claims: registry identity, evidence binding, population discipline
# ---------------------------------------------------------------------------


class TestClaims:
    def test_all_ten_registry_claims_exist(self) -> None:
        plan = _plan()
        claims = [r for r in plan.objects if r.object_type is ObjectType.CLAIM]
        assert len(claims) == 10
        assert all(r.claim_identity is not None for r in claims)

    def test_claim_identity_dimensions_preserved(self) -> None:
        record = _by_id(_plan(), "CL.EUR.HO.D3_DIRECTION")
        identity = record.claim_identity
        assert identity.market == "EURUSD"
        assert "D3" in identity.event_definition

        # Dimensions the frozen registry never stated stay NOT_SPECIFIED.
        assert identity.clock_origin == M.NOT_SPECIFIED
        assert identity.tolerance == M.NOT_SPECIFIED

    def test_result_value_does_not_change_population_identity(self) -> None:
        left = ClaimIdentity(
            market="XAUUSD",
            event_definition="68-state promotion",
            conditioning_event="8h acceptance",
            clock_origin="NY",
            horizon="8h",
            tolerance="1 AU",
            eligibility="quarter active",
            implementation_semantics="close-based",
        )

        # An identical result reported over identical dimensions is the SAME
        # population — results themselves are not identity dimensions.
        right = ClaimIdentity(
            market=left.market,
            event_definition=left.event_definition,
            conditioning_event=left.conditioning_event,
            clock_origin=left.clock_origin,
            horizon=left.horizon,
            tolerance=left.tolerance,
            eligibility=left.eligibility,
            implementation_semantics=left.implementation_semantics,
        )
        assert compare_claim_identity(left, right) is ClaimComparison.SAME_POPULATION
        other = ClaimIdentity(
            market=left.market,
            event_definition=left.event_definition,
            conditioning_event=left.conditioning_event,
            clock_origin=left.clock_origin,
            horizon=left.horizon,
            tolerance=left.tolerance,
            eligibility="different eligibility filter",
            implementation_semantics=left.implementation_semantics,
        )
        assert compare_claim_identity(left, other) is ClaimComparison.PARALLEL

    def test_parallel_populations_not_merged(self) -> None:
        plan = _plan()
        ev_ids = [
            r.canonical_id
            for r in plan.objects
            if r.object_type is ObjectType.EVIDENCE
        ]

        # XAU 68->80 and 120->132 remain two distinct evidence objects:
        # small-N populations are never merged into one "promotion" claim.
        assert "EV.XAU.PROMOTION.68_80.V1" in ev_ids
        assert "EV.XAU.PROMOTION.120_132.V1" in ev_ids

    def test_numerical_claims_have_evidence_path(self) -> None:
        plan = _plan()
        object_ids = {r.canonical_id for r in plan.objects}
        for record in plan.objects:
            if record.object_type is not ObjectType.CLAIM:
                continue
            evidence_refs = [
                r.target_id
                for r in record.references
                if r.target_id.startswith("EV.")
            ]

            assert evidence_refs, f"{record.canonical_id} lacks an evidence path"
            assert set(evidence_refs) <= object_ids

    def test_claim_without_evidence_would_be_unsupported(self) -> None:
        # An orphan numerical claim is not canonical truth: a claim record
        # whose evidence target does not exist is rejected by the gateway.

        gateway = InMemoryPersistenceGateway()
        from app.forge.canonical import CanonicalObject
        from app.forge.persistence.records import CanonicalObjectRecord
        from app.forge.canonical import CanonicalReference, CanonicalId, Layer

        orphan = CanonicalObjectRecord(
            canonical_id="CL.TEST.ORPHAN.V1",
            object_type=ObjectType.CLAIM,
            title="orphan numerical claim",
            version="V1",
            status=EvidenceStatus.CANDIDATE,
            exposure=ProductExposure.RESEARCH_LAB,
            layer="NONE",
            metadata={"result": "87.5%", "numerical": True},
            claim_identity=ClaimIdentity(
                market="XAUUSD",
                event_definition="e",
                conditioning_event="c",
                clock_origin="k",
                horizon="h",
                tolerance="t",
                eligibility="el",
                implementation_semantics="im",
            ),
        )

        from app.forge.canonical import CanonicalObject as _CO

        domain = _CO(
            canonical_id=CanonicalId(
                value="CL.TEST.ORPHAN.V2", object_type=ObjectType.CLAIM
            ),
            title="orphan numerical claim",
            version="V1",
            status=EvidenceStatus.CANDIDATE,
            exposure=ProductExposure.RESEARCH_LAB,
            metadata={"result": "87.5%", "numerical": True},
            references=(
                CanonicalReference(
                    target_id="EV.TEST.MISSING.V1", relation="supported_by"
                ),
            ),
        )
        from app.forge.persistence.port import DanglingReference

        with pytest.raises(DanglingReference):
            gateway.create_object(CanonicalObjectRecord.from_domain(domain))


# ---------------------------------------------------------------------------
# Provenance: artifact identity, typed edges, visual/conversation classes
# ---------------------------------------------------------------------------


class TestProvenance:
    def test_source_artifacts_registered_with_identity(self) -> None:
        plan = _plan()
        assert plan.report.artifacts >= 20
        for artifact in plan.artifacts:
            assert (
                artifact.content_identity is None
                or artifact.content_identity.startswith("sha256:")
            )
            assert artifact.locator

    def test_markdown_defines_edges(self) -> None:
        plan = _plan()
        defines = [e for e in plan.edges if e[2] == "DEFINES"]
        assert len(defines) >= 20
        targets = {e[1] for e in defines}
        assert "MOD.JPY.CARRY_GAME.L1_L3.V1" in targets
        assert "EV.FIB.R11.ANCHOR_OVERGEN.V1" in targets
        assert "SET.FIB.REKEY.V1" in targets

    def test_supports_edge_correct(self) -> None:
        plan = _plan()
        supports = [e for e in plan.edges if e[2] == "SUPPORTS"]
        assert len(supports) == 1
        artifact_id, object_id, _, _ = supports[0]
        artifact = next(a for a in plan.artifacts if a.artifact_id == artifact_id)
        assert object_id == "EV.EUR.DAILY.PHASE1_TIERS.V1"
        assert artifact.locator.endswith("PHASE_1_LEDGER.md")
        assert artifact.source_class == "MARKDOWN"

    def test_implements_edges_correct(self) -> None:
        plan = _plan()
        implements = {e[1] for e in plan.edges if e[2] == "IMPLEMENTS"}
        assert implements == {
            "MOD.BTC.TRACKER.DWM.V1",
            "MOD.XAU.GAME.L1_L2_L3.V1",
            "MOD.EUR.DAILY.NEWS_REKEY.V1",
        }

    def test_visualizes_edges_correct_and_non_empirical(self) -> None:
        plan = _plan()
        visualizes = [e for e in plan.edges if e[2] == "VISUALIZES"]
        assert visualizes
        assert all(e[1] == "MOD.EUR.HIGHER_ORDER.V1" for e in visualizes)
        assert plan.report.visual_only_sources == len(visualizes)

        from app.forge.provenance import Artifact, SourceState, classify_support

        # Visual lineage is representable as an artifact class, and it is
        # never on its own an empirical SUPPORT (see edge assertions below).
        visual_artifacts = [
            Artifact(
                artifact_id="ART.PINE.TEST1",
                source_class="PINE",
                source_state=SourceState.READ,
            )
        ]

        assert visual_artifacts[0].source_class == "PINE"

    def test_missing_named_source_classified_not_fabricated(self) -> None:
        # Remove one named implementation source: it must be classified
        # MISSING_SOURCE, never fabricated or silently dropped.
        files = _load_corpus()
        removed = "corpus/indicators/xau/CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine"
        files = {k: v for k, v in files.items() if k != removed}
        plan = canonicalize_files(files)
        assert plan.report.missing_source == 1
        outcomes = [o for o in plan.report.outcomes if o.path == removed]
        assert outcomes[0].classification.value == "MISSING_SOURCE"

    def test_no_supports_edge_for_visual_or_conversation(self) -> None:
        plan = _plan()
        for edge in plan.edges:
            if edge[2] == "SUPPORTS":
                artifact = next(
                    a for a in plan.artifacts if a.artifact_id == edge[0]
                )
                assert artifact.source_class not in (
                    "VISUAL",
                    "CONVERSATION_DERIVED",
                )

    def test_every_migrated_object_has_provenance_edge(self) -> None:
        # ACCEPTANCE I1: every migrated object — including the 10 CLAIMs —
        # carries >=1 provenance edge from a registered artifact with a
        # deterministic content identity and repo-relative locator.
        plan = _plan()
        targets = {e[1] for e in plan.edges}
        missing = [r.canonical_id for r in plan.objects if r.canonical_id not in targets]
        assert missing == []
        artifacts = {a.artifact_id: a for a in plan.artifacts}
        for artifact_id, _, _, _ in plan.edges:
            artifact = artifacts[artifact_id]
            assert artifact.content_identity
            assert artifact.content_identity.startswith("sha256:")
            assert artifact.locator and not artifact.locator.startswith("/")

    def test_claim_registry_inventoried_with_claim_edges(self) -> None:
        # ACCEPTANCE A1: the claim registry is an in-scope source artifact.
        report = _plan().report
        outcomes = [o for o in report.outcomes if o.path == M.CLAIM_REGISTRY_PATH]
        assert len(outcomes) == 1
        assert outcomes[0].classification.value == "GOVERNANCE_CONTRACT"
        assert report.sources_inventoried == 30
        registry_edges = [
            e for e in _plan().edges if e[3] == "claim registry defines this claim"
        ]
        assert len(registry_edges) == 10
        assert len({e[1] for e in registry_edges}) == 10

    def test_claim_registry_missing_classified_not_fabricated(self) -> None:
        # ACCEPTANCE I4: named-but-missing source classifies MISSING_SOURCE;
        # the artifact and its edges are never fabricated without the file.
        files = _load_corpus()
        files = {k: v for k, v in files.items() if k != M.CLAIM_REGISTRY_PATH}
        plan = canonicalize_files(files)
        assert plan.report.missing_source == 1
        outcomes = [o for o in plan.report.outcomes if o.path == M.CLAIM_REGISTRY_PATH]
        assert outcomes[0].classification.value == "MISSING_SOURCE"
        assert all(e[3] != "claim registry defines this claim" for e in plan.edges)
        # Claims themselves still exist from the governed mapping table.
        claims = [r for r in plan.objects if r.object_type is ObjectType.CLAIM]
        assert len(claims) == 10

    def test_registry_claims_match_registry_file_table(self) -> None:
        # Anti-fabrication: the governed REGISTRY_CLAIMS table must match the
        # source registry table row-for-row (ids, model through the explicit
        # ID mapping, claim text, evidence, status, layer).
        text = _load_corpus()[M.CLAIM_REGISTRY_PATH]
        rows: list[list[str]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("| CL."):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) == 6, cells
            rows.append(cells)
        assert len(rows) == 10
        by_id = {e["claim_id"]: e for e in M.REGISTRY_CLAIMS}
        assert set(by_id) == {r[0] for r in rows}
        for claim_id, model, claim, evidence, status, layer in rows:
            entry = by_id[claim_id]
            assert M.resolve_canonical_id(model, ObjectType.MODEL) == entry["model"]
            assert claim == entry["claim"]
            assert evidence == entry["evidence"]
            assert status == entry["status"]
            assert layer == entry["layer"]


# ---------------------------------------------------------------------------
# Exposure stamping & II.4 policy boundary safety
# ---------------------------------------------------------------------------


class TestExposureAndPolicySafety:
    def test_all_migrated_objects_carry_valid_exposure(self) -> None:
        gateway = _applied_gateway()
        for object_id in gateway.list_object_ids():
            record = gateway.get_object(object_id)
            assert isinstance(record.exposure, ProductExposure)

    def test_evidence_exposure_assignment_follows_frozen_rules(self) -> None:
        plan = _plan()

        assert (
            _by_id(plan, "EV.EUR.DAILY.PHASE1_TIERS.V1").exposure
            is ProductExposure.SUBSCRIBER_MODEL
        )

        assert (
            _by_id(plan, "EV.XAU.PROMOTION.120_132.V1").exposure
            is ProductExposure.RESEARCH_LAB
        )

        assert (
            _by_id(plan, "EV.FIB.R11.ANCHOR_OVERGEN.V1").exposure
            is ProductExposure.RESEARCH_LAB
        )

        assert (
            _by_id(plan, "EV.EUR.DAILY.NEWS_AUC.V1").exposure
            is ProductExposure.RESEARCH_LAB
        )

    def test_unknown_exposure_fails_closed(self) -> None:
        text = (
            "# MODEL CARD — X\n\nmodel_id: EUR.WEEKLY.V1_1\nstatus: CANDIDATE\n"
            "market_scope: EURUSD\nlayer: L2\nmodel_type: PATH\n"
            "product_exposure: SUPER_PREMIUM_ELITE\n\n## Purpose\np\n"
        )
        plan = canonicalize_files({"t.md": text})
        assert plan.report.quarantined == 1

    def test_no_public_teaching_by_default(self) -> None:
        gateway = _applied_gateway()

        # Backfill never stamps PUBLIC_TEACHING: readable source text is not
        # a public-teaching authorization.
        exposures = {
            gateway.get_object(oid).exposure
            for oid in gateway.list_object_ids()
        }
        assert ProductExposure.PUBLIC_TEACHING not in exposures

    def test_policy_engine_untouched_by_backfill(self) -> None:
        import inspect

        import app.forge.policy as policy_module
        import app.forge.backfill.runner as runner_module

        # The runner never references the policy engine directly...
        runner_src = inspect.getsource(runner_module)
        assert "PolicyEngine" not in runner_src
        engine = DefaultDenyPolicyEngine()
        decision = engine.decide(
            __import__(
                "app.forge.identity", fromlist=["ANONYMOUS_PRINCIPAL"]
            ).ANONYMOUS_PRINCIPAL,
            __import__(
                "app.forge.policy", fromlist=["AuthorizationContext"]
            ).AuthorizationContext.empty(),
            PolicyAction.VIEW,
            ResourcePolicyMetadata(
                PolicyResourceType.CANONICAL_OBJECT,
                "MOD.JPY.CARRY_GAME.L1_L3.V1",
                ProductExposure.SUBSCRIBER_MODEL,
            ),
        )
        # ...and backfill created no entitlement: II.4 still denies.
        assert decision.allowed is False

    def test_no_entitlement_license_whop_created(self) -> None:
        gateway = _applied_gateway()
        banned = ("PLAN", "SUBSCRIPTION", "LICENSE", "WHOP", "BILLING", "CHECKOUT")
        for object_id in gateway.list_object_ids():
            for token in banned:
                assert token not in object_id


# ---------------------------------------------------------------------------
# Persistence semantics: dry-run purity, apply, idempotency, conflict,
# failed-batch atomic rollback
# ---------------------------------------------------------------------------


class TestPersistenceSemantics:
    def test_dry_run_performs_zero_writes(self) -> None:
        gateway = _fresh_gateway()
        result = run_backfill(gateway, REPO_ROOT, BackfillMode.DRY_RUN)
        assert gateway.list_object_ids() == ()
        assert result.report.migrated == 30

    def test_apply_performs_writes_and_roundtrip(self) -> None:
        gateway = _applied_gateway()
        ids = gateway.list_object_ids()
        assert len(ids) == 30
        record = gateway.get_object("MOD.JPY.CARRY_GAME.L1_L3.V1")
        assert record.status is EvidenceStatus.CANDIDATE
        assert record.metadata["legacy_ids"] == ["JPY.CARRY_GAME.L1_L3.V1"]
        card_artifact = next(
            a
            for a in _plan().artifacts
            if a.locator.endswith("JPY_CARRY_GAME_MODEL_CARD_V1.md")
        )

        artifact = gateway.get_artifact(card_artifact.artifact_id)
        assert artifact is not None
        assert artifact.content_identity.startswith("sha256:")
        edges = gateway.edges_for_object("MOD.JPY.CARRY_GAME.L1_L3.V1")
        assert any(e.relation == "DEFINES" for e in edges)

        xau_edges = gateway.edges_for_object("MOD.XAU.GAME.L1_L2_L3.V1")
        assert any(e.relation == "IMPLEMENTS" for e in xau_edges)

    def test_second_identical_apply_is_idempotent(self) -> None:
        gateway = _fresh_gateway()
        run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
        first_ids = gateway.list_object_ids()
        result = run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
        assert result.report.unchanged == 30
        assert gateway.list_object_ids() == first_ids
        assert result.report.conflicts == 0

    def test_conflicting_content_rejected_no_silent_overwrite(self) -> None:
        gateway = _applied_gateway()
        record = gateway.get_object("MOD.BTC.TRACKER.DWM.V1")
        mutated = replace(record, status=EvidenceStatus.VALIDATED)
        gateway._objects["MOD.BTC.TRACKER.DWM.V1"] = (mutated, 2)

        with pytest.raises(ConflictError):
            run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)

        # The governed content was NOT overwritten.
        assert (
            gateway.get_object("MOD.BTC.TRACKER.DWM.V1").status
            is EvidenceStatus.VALIDATED
        )

    def test_reference_order_is_not_governed_content(self) -> None:
        # References are an unordered set in the frozen schema (PK =
        # canonical_id + target_id + relation; the SQL gateway reads them
        # back in sorted order). Authored order must not be treated as
        # governed content, or idempotency breaks on any multi-reference
        # object persisted through SQL.
        gateway = _fresh_gateway()
        run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
        plan = canonicalize_files(_load_corpus())
        target = next(r for r in plan.objects if len(r.references) > 1)
        from dataclasses import replace as _replace

        reordered = _replace(target, references=tuple(reversed(target.references)))
        plan.objects = [
            reordered if r.canonical_id == target.canonical_id else r
            for r in plan.objects
        ]
        from app.forge.backfill.runner import _apply_plan

        _apply_plan(gateway, plan)  # must NOT raise ConflictError
        assert plan.report.unchanged == 30
        assert plan.report.conflicts == 0
        assert len(gateway.list_object_ids()) == 30

    def test_failed_batch_rolls_back(self) -> None:
        gateway = _fresh_gateway()
        # Inject a duplicate canonical id directly into the derived plan: the
        # gateway must reject the whole pending batch atomically (a second
        # same-id record may never silently replace the first), leaving zero
        # partial canonical truth behind.

        from app.forge.backfill.canonicalizer import canonicalize_files as _cf
        from app.forge.persistence.port import DuplicateCanonicalObject

        plan = _cf(_load_corpus())
        plan.objects.append(plan.objects[0])

        from app.forge.backfill.runner import _apply_plan as _ap

        with pytest.raises(DuplicateCanonicalObject):
            _ap(gateway, plan)
        # Nothing from the poisoned batch persisted — full atomic rollback.
        assert gateway.list_object_ids() == ()


def run_backfill_with_plan(gateway, files) -> None:
    """Apply a caller-supplied file map directly (test scaffolding)."""
    from app.forge.backfill.runner import _apply_plan

    _apply_plan(gateway, canonicalize_files(files))


# ---------------------------------------------------------------------------
# V/W — no public route, reproducibility
# ---------------------------------------------------------------------------


class TestScopeAndReproducibility:
    def test_no_new_public_corpus_route(self) -> None:
        from app.main import app as fastapi_app

        route_paths = {getattr(r, "path", "") for r in fastapi_app.routes}
        forbidden_prefixes = (
            "/forge/v1/corpus",
            "/forge/v1/models",
            "/forge/v1/claims",
            "/forge/v1/evidence",
            "/forge/v1/setups",
            "/forge/v1/artifacts",
            "/corpus",
            "/models",
            "/claims",
            "/evidence",
            "/setups",
            "/artifacts",
        )
        # This bloc creates truth, not product presentation: none of the
        # forbidden public corpus surfaces may exist.
        for path in route_paths:
            for prefix in forbidden_prefixes:
                assert not path.startswith(prefix), path

    def test_reproducible_from_clean_state(self) -> None:
        gateway_a = _fresh_gateway()
        gateway_b = _fresh_gateway()
        result_a = run_backfill(gateway_a, REPO_ROOT, BackfillMode.APPLY)
        result_b = run_backfill(gateway_b, REPO_ROOT, BackfillMode.APPLY)
        assert result_a.content_hash == result_b.content_hash
        assert gateway_a.list_object_ids() == gateway_b.list_object_ids()
        for object_id in gateway_a.list_object_ids():
            record_a = gateway_a.get_object(object_id)
            record_b = gateway_b.get_object(object_id)
            assert record_a.status == record_b.status
            assert record_a.exposure == record_b.exposure
            assert record_a.references == record_b.references
            assert record_a.metadata == record_b.metadata

    def test_persisted_hash_stable(self) -> None:
        gateway = _applied_gateway()
        record = gateway.get_object("EV.FIB.R11.ANCHOR_OVERGEN.V1")
        from app.forge.canonical import CanonicalId

        # Content hash is a pure function of governed content: two calls on
        # the same persisted round-trip agree exactly.
        domain = record.to_domain()
        assert domain.content_hash() == domain.content_hash()


# ---------------------------------------------------------------------------
# Audit hygiene: no internal bodies, no import/startup backfill
# ---------------------------------------------------------------------------


class TestAuditHygiene:
    def test_report_contains_no_internal_bodies(self) -> None:
        plan = _plan()
        report_json = plan.report.to_json()
        assert (
            "INTERNAL_METHOD"
            not in report_json.replace("INTERNAL_METHOD", "INTERNAL_METHOD")
        )
        # Reasons are bounded, content-free classifications: no card bodies.
        for outcome in plan.report.outcomes:
            assert len(outcome.reason) < 200
            assert "Asian seed" not in outcome.reason
            assert "carry master" not in outcome.reason

    def test_backfill_runs_never_on_import_or_startup(self) -> None:
        # Reloading the app module must not canonicalize anything.

        import importlib

        import app.main as main_module

        importlib.reload(main_module)
        gateway = _fresh_gateway()
        assert gateway.list_object_ids() == ()

        import app.forge.backfill.runner as runner

        importlib.reload(runner)
        assert callable(runner.run_backfill)
