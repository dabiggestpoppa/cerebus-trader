"""Focused I.4 tests: retrieval index (Book I / Bloc I.4).

Maps 1:1 to implementation/forge/book_i/bloc_i_4/ACCEPTANCE.md clauses A-W:
index authority, frozen record contract, structured lookup, claim population
separation, deterministic ranking, alias/generation routing, exposure
compilation, policy-before-content deny-before-load, the six-class exposure
matrix, FOUND vs SUPPORTED provenance navigation, negative evidence,
quarantine, build/rebuild/staleness/failure laws, reference-order
normalization, governance coverage, model-truth regressions, boundary
integrity, reproducibility and security.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.runner import (
    BackfillMode,
    load_corpus_files,
    run_backfill,
)
from app.forge.canonical import (
    CanonicalReference,
    EvidenceStatus,
    EvidenceType,
    Layer,
    ObjectType,
    ProductExposure,
    SetupClass,
    compare_claim_identity,
)
from app.forge.identity import ForgePrincipal
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.records import CanonicalObjectRecord
from app.forge.policy import (
    CAPABILITY_ADMIN_RESEARCH,
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_CORPUS_READ_PUBLIC,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_FORGE_INTERNAL,
    CAPABILITY_MODEL_READ_OPERATOR,
    AuthorizationContext,
)
from app.forge.retrieval import (
    CompileContext,
    IndexBuildError,
    IndexBuildMode,
    IndexBuildOutcome,
    IndexGeneration,
    IndexNotBuilt,
    QuarantineCatalog,
    QuarantineEntry,
    RetrievalCompileError,
    RetrievalIndex,
    RetrievalQuery,
    RetrievalService,
    build_index,
    compile_record,
    expand_query_text,
    filter_headers,
    normalize_query,
    normalized_content_hash,
    rank,
    run_index_build,
    sanitize_text,
)
from app.forge.retrieval.aliases import HISTORICAL_ALIASES, aliases_present

REPO_ROOT = Path(__file__).resolve().parents[1]
CARD_PREFIXES = (
    "corpus/canonical/models/",
    "corpus/canonical/evidence/",
    "corpus/canonical/setups/",
)

# Frozen II.4 boundary: app/forge/policy.py must not change under I.4 (R2).
POLICY_MODULE_SHA256 = "f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc"

ANON = ForgePrincipal.anonymous()
AUTH = ForgePrincipal(authenticated=True, forge_user_id="user-r", session_id=None)
NO_CAP = AuthorizationContext.empty()
PUBLIC = AuthorizationContext.of(CAPABILITY_CORPUS_READ_PUBLIC)
MEMBER = AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER)
OPERATOR = AuthorizationContext.of(CAPABILITY_MODEL_READ_OPERATOR)
RESEARCH = AuthorizationContext.of(CAPABILITY_EVIDENCE_READ_RESEARCH)
ADMIN = AuthorizationContext.of(CAPABILITY_ADMIN_RESEARCH)
INTERNAL = AuthorizationContext.of(CAPABILITY_FORGE_INTERNAL)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _applied() -> InMemoryPersistenceGateway:
    gateway = InMemoryPersistenceGateway()
    run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
    return gateway


def _built() -> tuple[InMemoryPersistenceGateway, RetrievalIndex]:
    gateway = _applied()
    index = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, index)
    return gateway, index


@pytest.fixture(scope="module")
def gateway() -> InMemoryPersistenceGateway:
    return _applied()


@pytest.fixture(scope="module")
def index(gateway) -> RetrievalIndex:
    idx = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
    return idx


@pytest.fixture(scope="module")
def generation(index) -> IndexGeneration:
    return index.require()


@pytest.fixture(scope="module")
def service(index) -> RetrievalService:
    return RetrievalService(index)


def _record(
    canonical_id: str,
    object_type: ObjectType,
    *,
    exposure=ProductExposure.SUBSCRIBER_MODEL,
    title: str = "Synthetic object",
    status: EvidenceStatus = EvidenceStatus.CANDIDATE,
    layer: Layer = Layer.NONE,
    metadata: dict | None = None,
    references=(),
    claim_identity=None,
) -> CanonicalObjectRecord:
    return CanonicalObjectRecord(
        canonical_id=canonical_id,
        object_type=object_type,
        title=title,
        version="V1",
        status=status,
        exposure=exposure,
        layer=layer,
        references=tuple(references),
        metadata=metadata or {},
        claim_identity=claim_identity,
    )


def _synthetic_gateway(records, artifacts=(), edges=()) -> InMemoryPersistenceGateway:
    gateway = InMemoryPersistenceGateway()
    with gateway.transaction():
        for artifact in artifacts:
            gateway.create_artifact(artifact)
        for record in records:
            gateway.create_object(record)
        for edge in edges:
            gateway.add_provenance_edge(edge)
    return gateway


def _indexed(records, artifacts=(), edges=()) -> RetrievalIndex:
    gateway = _synthetic_gateway(records, artifacts, edges)
    idx = RetrievalIndex()
    build_index(gateway, index=idx, mode=IndexBuildMode.APPLY)
    return idx


def _marker_index(text: str) -> RetrievalIndex:
    return _indexed(
        [
            _record(
                "EV.SYNTH.SECRET.V1",
                ObjectType.EVIDENCE,
                exposure=ProductExposure.RESEARCH_LAB,
                title="Secret research evidence",
                metadata={"card": {"exact_claim": text}},
            )
        ]
    )


def _spy_service(index) -> tuple[RetrievalService, list[str]]:
    loads: list[str] = []

    def loader(generation, object_id):
        loads.append(object_id)
        return generation.record(object_id)

    return RetrievalService(index, record_loader=loader), loads


class _ReorderedReferences:
    """Port wrapper returning every record with reversed reference order."""

    def __init__(self, inner) -> None:
        self._inner = inner

    def get_object(self, canonical_id):
        record = self._inner.get_object(canonical_id)
        if record is None:
            return None
        return replace(record, references=tuple(reversed(record.references)))

    def __getattr__(self, name):
        return getattr(self._inner, name)


class _PoisonedExposure:
    """Port wrapper returning one record with an unrecognized exposure."""

    def __init__(self, inner, poison_id: str) -> None:
        self._inner = inner
        self._poison_id = poison_id

    def get_object(self, canonical_id):
        record = self._inner.get_object(canonical_id)
        if record is not None and canonical_id == self._poison_id:
            return replace(record, exposure="NOT_A_REAL_EXPOSURE")
        return record

    def __getattr__(self, name):
        return getattr(self._inner, name)


class _DuplicatedListing:
    """Port wrapper listing one canonical id twice (conflict injection)."""

    def __init__(self, inner) -> None:
        self._inner = inner

    def list_object_ids(self):
        ids = tuple(self._inner.list_object_ids())
        return ids + (ids[0],)

    def __getattr__(self, name):
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# A — index authority
# ---------------------------------------------------------------------------


class TestIndexAuthority:
    def test_records_come_from_persistence_not_markdown(self) -> None:
        # This object exists ONLY in persistence — no source file names it, so
        # a Markdown-driven index could never produce this record.
        gateway = _synthetic_gateway(
            [_record("MOD.NOWHERE.PROBE.V1", ObjectType.MODEL, title="Probe")]
        )
        idx = RetrievalIndex()
        build_index(gateway, index=idx, mode=IndexBuildMode.APPLY)
        record = idx.require().record("MOD.NOWHERE.PROBE.V1")
        assert record is not None
        assert record.title == "Probe"

    def test_index_never_writes_to_the_port(self) -> None:
        gateway = _applied()
        ids_before = gateway.list_object_ids()
        versions_before = {
            object_id: gateway.object_version(object_id) for object_id in ids_before
        }
        idx = RetrievalIndex()
        build_index(gateway, index=idx, mode=IndexBuildMode.APPLY)
        assert gateway.list_object_ids() == ids_before
        assert {
            object_id: gateway.object_version(object_id)
            for object_id in gateway.list_object_ids()
        } == versions_before
        from app.forge.retrieval import index as index_module

        for name in dir(index_module):
            assert not name.startswith(("create_", "add_", "delete_", "update_")), name

    def test_artifacts_are_never_retrieval_records(self, generation) -> None:
        assert all(not record.object_id.startswith("ART.") for record in generation.records)
        assert all(record.object_type is not ObjectType.ARTIFACT for record in generation.records)

    def test_header_is_safe_projection_without_body(self, generation) -> None:
        record = generation.records[0]
        header = record.header()
        assert set(header.model_dump()) == {
            "object_id",
            "object_type",
            "canonical_version",
            "status",
            "exposure",
            "layer",
            "market_scope",
            "model_family",
            "source_artifact_ids",
        }
        assert header.exposure is record.exposure_class

    def test_records_carry_their_index_generation(self, generation) -> None:
        assert all(record.generation == generation.generation for record in generation.records)


# ---------------------------------------------------------------------------
# B — frozen retrieval object contract
# ---------------------------------------------------------------------------


class TestFrozenRecordContract:
    FROZEN_FIELDS = (
        "object_id",
        "object_type",
        "canonical_version",
        "title",
        "market_scope",
        "layer",
        "status",
        "exposure_class",
        "parent_ids",
        "source_artifact_ids",
        "retrieval_text",
        "structured",
        "routing",
        "leakage",
        "conflict",
    )

    def test_every_record_implements_the_frozen_fields(self, generation) -> None:
        for record in generation.records:
            for field_name in self.FROZEN_FIELDS:
                assert hasattr(record, field_name), (record.object_id, field_name)

    def test_provenance_rule_every_record_routes_to_a_source(self, generation) -> None:
        for record in generation.records:
            assert record.source_artifact_ids, record.object_id

    def test_deterministic_payload_and_hash(self, generation) -> None:
        for record in generation.records:
            payload = record.deterministic_payload()
            assert payload == record.deterministic_payload()
            assert record.content_hash() == hashlib.sha256(payload.encode()).hexdigest()

    def test_identity_independent_of_relationship_order(self, generation) -> None:
        record = generation.record("CL.XAU.PROMOTION.68_80")
        shuffled = record.model_copy(
            update={"related_ids": tuple(reversed(record.related_ids))}
        )
        assert shuffled.content_hash() == record.content_hash()

    def test_unstated_facets_stay_empty_and_stated_ones_survive(self, gateway, index) -> None:
        card = gateway.get_object("EV.EUR.DAILY.PHASE1_TIERS.V1").metadata["card"]
        assert card["event_definition"] == "NOT_SPECIFIED_IN_SOURCE"
        tiers = index.require().record("EV.EUR.DAILY.PHASE1_TIERS.V1")
        assert tiers.structured.events == ()
        assert tiers.structured.clocks == ()
        assert tiers.structured.metrics == ()
        assert tiers.structured.levels == ()
        assert tiers.structured.states == ()
        assert tiers.structured.sample_n == 995

    def test_sample_n_present_only_where_source_states_it(self, generation) -> None:
        with_n = {
            record.object_id: record.structured.sample_n
            for record in generation.records
            if record.structured.sample_n is not None
        }
        assert with_n == {
            "EV.EUR.DAILY.PHASE1_TIERS.V1": 995,
            "EV.EUR.HO.D3_DIRECTION.V1": 14,
            "EV.JPY.CARRY.BASKET_RELATION.V1": 182,
            "EV.XAU.PROMOTION.68_80.V1": 48,
            "EV.XAU.PROMOTION.120_132.V1": 25,
        }

    def test_period_and_implementation_ids_from_real_fields(self, generation) -> None:
        assert (
            generation.record("EV.EUR.DAILY.PHASE1_TIERS.V1").structured.period
            == "M5 source Nov2022-Sep2026 lineage"
        )
        implementations = {
            record.object_id: record.structured.implementation_ids
            for record in generation.records
            if record.structured.implementation_ids
        }
        assert set(implementations) == {
            "MOD.BTC.TRACKER.DWM.V1",
            "MOD.EUR.DAILY.NEWS_REKEY.V1",
            "MOD.XAU.GAME.L1_L2_L3.V1",
        }
        for artifact_ids in implementations.values():
            assert all(artifact_id.startswith("ART.PINE.") for artifact_id in artifact_ids)

    def test_claim_identity_carried_verbatim(self, gateway, generation) -> None:
        checked = 0
        for object_id in gateway.list_object_ids():
            canonical = gateway.get_object(object_id)
            if canonical.claim_identity is None:
                continue
            checked += 1
            built = generation.record(object_id)
            assert built.structured.claim_identity == canonical.claim_identity
            assert len(built.structured.claim_identity.comparison_key()) == 8
        assert checked == 10

    def test_facets_from_stated_card_fields(self) -> None:
        # A synthetic card that states every structured dimension.
        record = _record(
            "EV.SYNTH.FACETS.V1",
            ObjectType.EVIDENCE,
            metadata={
                "card": {
                    "exact_claim": "facet probe",
                    "metric": "AUC",
                    "clock_origin": "session open",
                    "event_definition": "news window",
                    "state_space": ("tier-up",),
                    "data_period": "2024",
                    "sample_n": 7,
                }
            },
        )
        compiled = compile_record(record, CompileContext({}, {}, {}))
        assert compiled.structured.metrics == ("AUC",)
        assert compiled.structured.clocks == ("session open",)
        assert compiled.structured.events == ("news window",)
        assert compiled.structured.states == ("tier-up",)
        assert compiled.structured.period == "2024"
        assert compiled.structured.sample_n == 7

    def test_retrieval_text_is_generated_from_governed_fields(self, generation) -> None:
        for record in generation.records:
            assert record.retrieval_text
            assert "```" not in record.retrieval_text
            assert len(record.retrieval_text) < 2000


# ---------------------------------------------------------------------------
# C — structured retrieval
# ---------------------------------------------------------------------------


class TestStructuredLookup:
    def test_exact_id_lookup_returns_exactly_one(self, service) -> None:
        response = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(canonical_id="MOD.XAU.GAME.L1_L2_L3.V1")
        )
        assert [result.object_id for result in response.results] == [
            "MOD.XAU.GAME.L1_L2_L3.V1"
        ]

    def test_unknown_id_is_never_fuzzily_matched(self, service) -> None:
        assert service.exact(AUTH, MEMBER, "MOD.XAU.GAME.L1_L2_L3") is None
        assert service.exact(AUTH, MEMBER, "MOD.XAU.GAME.V1") is None

    def test_type_filter_partitions_the_index(self, service) -> None:
        for object_type, count in (
            ("MODEL", 7),
            ("EVIDENCE", 10),
            ("SETUP", 3),
            ("CLAIM", 10),
        ):
            response = service.retrieve(
                AUTH, RESEARCH, RetrievalQuery(object_type=object_type)
            )
            assert len(response.results) == count, object_type
            assert {result.object_type for result in response.results} == {object_type}

    def test_market_filter_is_exact_and_disjoint(self, service) -> None:
        eur = service.retrieve(AUTH, MEMBER, RetrievalQuery(market="EURUSD"))
        xau = service.retrieve(AUTH, MEMBER, RetrievalQuery(market="XAUUSD"))
        eur_ids = {result.object_id for result in eur.results}
        xau_ids = {result.object_id for result in xau.results}
        assert eur_ids and xau_ids
        # only genuinely cross-asset objects may appear on both sides
        assert (eur_ids & xau_ids) <= {
            "CL.FIB.R11.GENERATOR_FAILURE",
            "EV.FIB.R11.ANCHOR_OVERGEN.V1",
        }
        assert all("EURUSD" in result.market_scope for result in eur.results)
        assert all("XAUUSD" in result.market_scope for result in xau.results)
        # a single-market object never bleeds across
        assert "MOD.EUR.WEEKLY.V1_1" in eur_ids
        assert "MOD.EUR.WEEKLY.V1_1" not in xau_ids

    def test_model_family_filter_separates_families(self, service) -> None:
        models = {
            family: {
                result.object_id
                for result in service.retrieve(
                    AUTH,
                    MEMBER,
                    RetrievalQuery(object_type="MODEL", model_family=family),
                ).results
            }
            for family in ("EUR", "XAU", "BTC", "JPY")
        }
        assert models["EUR"] == {
            "MOD.EUR.DAILY.NEWS_REKEY.V1",
            "MOD.EUR.HIGHER_ORDER.V1",
            "MOD.EUR.WEEKLY.V1_1",
        }
        assert models["XAU"] == {"MOD.XAU.GAME.L1_L2_L3.V1"}
        assert models["BTC"] == {"MOD.BTC.TRACKER.DWM.V1"}
        assert models["JPY"] == {"MOD.JPY.CARRY_GAME.L1_L3.V1"}
        assert not (models["EUR"] & models["XAU"])
        assert not (models["EUR"] & models["BTC"])

    def test_status_and_exposure_filters(self, service) -> None:
        falsified = service.retrieve(AUTH, RESEARCH, RetrievalQuery(status="FALSIFIED"))
        assert {result.object_id for result in falsified.results} == {
            "CL.FIB.R11.GENERATOR_FAILURE",
            "EV.FIB.R11.ANCHOR_OVERGEN.V1",
        }
        research = service.retrieve(
            AUTH, RESEARCH, RetrievalQuery(exposure="RESEARCH_LAB")
        )
        assert {result.object_id for result in research.results} == {
            "EV.EUR.DAILY.NEWS_AUC.V1",
            "EV.FIB.R11.ANCHOR_OVERGEN.V1",
            "EV.XAU.PROMOTION.120_132.V1",
            "SET.FIB.REKEY.V1",
        }

    def test_layer_filter_returns_disjoint_sets(self, service) -> None:
        assert [
            r.object_id
            for r in service.retrieve(AUTH, MEMBER, RetrievalQuery(layer="L1")).results
        ] == ["MOD.EUR.DAILY.NEWS_REKEY.V1"]
        assert [
            r.object_id
            for r in service.retrieve(AUTH, MEMBER, RetrievalQuery(layer="L2")).results
        ] == ["MOD.EUR.WEEKLY.V1_1"]
        assert [
            r.object_id
            for r in service.retrieve(AUTH, MEMBER, RetrievalQuery(layer="L3")).results
        ] == ["MOD.EUR.HIGHER_ORDER.V1"]

    def test_source_artifact_and_provenance_relation_filters(self, service) -> None:
        implements = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(provenance_relation="IMPLEMENTS")
        )
        assert {r.object_id for r in implements.results} == {
            "MOD.BTC.TRACKER.DWM.V1",
            "MOD.EUR.DAILY.NEWS_REKEY.V1",
            "MOD.XAU.GAME.L1_L2_L3.V1",
        }
        record = service.index.require().record("MOD.XAU.GAME.L1_L2_L3.V1")
        by_artifact = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(source_artifact=record.source_artifact_ids[0])
        )
        assert "MOD.XAU.GAME.L1_L2_L3.V1" in {
            r.object_id for r in by_artifact.results
        }

    def test_unknown_filter_value_matches_nothing(self, service) -> None:
        response = service.retrieve(
            AUTH, RESEARCH, RetrievalQuery(status="TOTALLY_MADE_UP")
        )
        assert response.results == ()
        assert response.candidates == 0

    def test_header_filters_run_before_any_body_load(self, index) -> None:
        normalized = normalize_query(RetrievalQuery(object_type="SETUP"))
        headers = filter_headers(index.require().headers, normalized)
        assert len(headers) == 3
        assert all(header.object_type is ObjectType.SETUP for header in headers)


# ---------------------------------------------------------------------------
# D — claim population separation
# ---------------------------------------------------------------------------


class TestClaimPopulationSeparation:
    def test_identity_filter_returns_only_same_population(self, index, service) -> None:
        identity = index.require().record(
            "CL.XAU.PROMOTION.68_80"
        ).structured.claim_identity
        response = service.retrieve(AUTH, MEMBER, RetrievalQuery(claim_identity=identity))
        assert [result.object_id for result in response.results] == [
            "CL.XAU.PROMOTION.68_80"
        ]

    def test_near_identical_prose_different_population_stays_distinct(
        self, index, service
    ) -> None:
        generation = index.require()
        left = generation.record("CL.XAU.PROMOTION.68_80")
        right = generation.record("CL.XAU.PROMOTION.120_132")
        assert left.structured.claim_identity != right.structured.claim_identity
        # near-identical prose: same sentence shape, different population
        assert "state promotes path" in left.retrieval_text
        assert "state promotes path" in right.retrieval_text
        assert left.retrieval_text != right.retrieval_text
        for record in (left, right):
            response = service.retrieve(
                AUTH,
                MEMBER,
                RetrievalQuery(claim_identity=record.structured.claim_identity),
            )
            assert [result.object_id for result in response.results] == [
                record.object_id
            ]

    def test_parallel_populations_are_not_contradictions(self, index) -> None:
        generation = index.require()
        a = generation.record("CL.EUR.HO.D3_DIRECTION").structured.claim_identity
        b = generation.record("CL.XAU.PROMOTION.68_80").structured.claim_identity
        assert compare_claim_identity(a, b).value == "PARALLEL"

    def test_result_values_never_enter_identity(self, gateway) -> None:
        for object_id in gateway.list_object_ids():
            identity = gateway.get_object(object_id).claim_identity
            if identity is None:
                continue
            key = " ".join(identity.comparison_key()).lower()
            assert "87.5" not in key and "42/48" not in key


# ---------------------------------------------------------------------------
# E — text retrieval and deterministic ranking
# ---------------------------------------------------------------------------


class TestRanking:
    def test_exact_identity_outranks_lexical_similarity(self, index, service) -> None:
        response = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(text="EV.EUR.DAILY.PHASE1_TIERS.V1")
        )
        assert response.results[0].object_id == "EV.EUR.DAILY.PHASE1_TIERS.V1"
        assert response.results[0].exact_identity is True

    def test_ranking_is_total_and_stable_under_input_order(self, index) -> None:
        normalized = normalize_query(RetrievalQuery(text="tier calibration eurusd"))
        records = list(index.require().records)
        expected = [item.record.object_id for item in rank(normalized, records)]
        assert [item.record.object_id for item in rank(normalized, list(reversed(records)))] == expected
        assert [
            item.record.object_id
            for item in rank(normalized, sorted(records, key=lambda r: r.title))
        ] == expected

    def test_same_query_twice_returns_identical_results(self, service) -> None:
        query = RetrievalQuery(text="rekey range tier")
        assert (
            service.retrieve(AUTH, MEMBER, query).to_dict()
            == service.retrieve(AUTH, MEMBER, query).to_dict()
        )

    def test_zero_signal_query_returns_nothing(self, service) -> None:
        response = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(text="zzzz qqqq unknown-token-xyz")
        )
        assert response.results == ()

    def test_ranking_never_changes_status_or_exposure(self, index, service) -> None:
        generation = index.require()
        response = service.retrieve(AUTH, RESEARCH, RetrievalQuery(text="tier"))
        assert response.results
        for result in response.results:
            canonical = generation.record(result.object_id)
            assert result.status == canonical.status.value
            assert result.exposure == canonical.exposure_class.value
            assert result.support_classification == canonical.support.classification

    def test_no_embedding_vector_or_provider_surface_exists(self) -> None:
        banned = (
            "openrouter",
            "whop",
            "embedding",
            "pgvector",
            "vector_store",
            "numpy",
            "torch",
        )
        package = REPO_ROOT / "app" / "forge" / "retrieval"
        for path in sorted(package.glob("*.py")):
            source = path.read_text(encoding="utf-8").lower()
            for token in banned:
                assert token not in source, (path.name, token)

    def test_lexical_match_never_implies_support(self, index, service) -> None:
        # BTC tracker lexically matches "tracker" but has no evidence chain.
        response = service.retrieve(AUTH, MEMBER, RetrievalQuery(text="tracker"))
        result = next(
            r for r in response.results if r.object_id == "MOD.BTC.TRACKER.DWM.V1"
        )
        assert result.supported is False
        assert "NO_EVIDENCE_REFERENCE" in result.support_gaps


# ---------------------------------------------------------------------------
# F — alias / generation routing
# ---------------------------------------------------------------------------


def _crosswalk_rows() -> list[tuple[str, str, str, str]]:
    text = (REPO_ROOT / "corpus" / "canonical" / "ONTOLOGY_CROSSWALK_V1.md").read_text(
        encoding="utf-8"
    )
    rows: list[tuple[str, ...]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "Historical language":
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(tuple(cells))
    return rows  # type: ignore[return-value]


class TestAliasRouting:
    def test_alias_table_is_verbatim_the_frozen_crosswalk(self) -> None:
        table = [
            (entry.historical, entry.intermediate, entry.canonical_kind, entry.modern)
            for entry in HISTORICAL_ALIASES
        ]
        assert table == _crosswalk_rows()

    def test_historical_query_expands_to_modern_tokens(self) -> None:
        expansions = expand_query_text("What is a Constraint Deficit?")
        assert "remaining" in expansions
        assert "distribution" in expansions

    def test_record_aliases_carry_its_own_historical_vocabulary(self, index) -> None:
        daily = index.require().record("MOD.EUR.DAILY.NEWS_REKEY.V1")
        assert "Rekey" in daily.structured.aliases
        assert "Tier" in daily.structured.aliases
        assert aliases_present("rekey ladder") == ("Rekey",)

    def test_historical_query_reaches_modern_records(self, service) -> None:
        response = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(text="Constraint Deficit")
        )
        assert response.results
        assert response.results[0].lexical_hits + response.results[0].structured_hits > 0

    def test_generation_is_retained_from_the_source(self, index) -> None:
        assert (
            index.require().record("EV.EUR.HO.D3_DIRECTION.V1").conflict.generation
            == "EUR Higher Order Scientific Review V1"
        )
        assert (
            index.require().record("EV.FIB.R11.ANCHOR_OVERGEN.V1").conflict.generation
            == "Fib Sequence R11"
        )

    def test_alias_routing_never_rewrites_status(self, index, service) -> None:
        generation = index.require()
        response = service.retrieve(
            AUTH, RESEARCH, RetrievalQuery(text="Range Birth Rekey")
        )
        assert response.results
        for result in response.results:
            assert result.status == generation.record(result.object_id).status.value


# ---------------------------------------------------------------------------
# G — exposure compiler
# ---------------------------------------------------------------------------


class TestExposureCompiler:
    def test_every_real_record_carries_a_valid_exposure(self, generation) -> None:
        for record in generation.records:
            assert isinstance(record.exposure_class, ProductExposure)

    def test_public_teaching_is_never_assigned_by_default(self, generation) -> None:
        assert not any(
            record.exposure_class is ProductExposure.PUBLIC_TEACHING
            for record in generation.records
        )

    def test_internal_method_record_is_identity_only(self) -> None:
        record = _record(
            "MOD.SYNTH.INTERNAL.V1",
            ObjectType.MODEL,
            exposure=ProductExposure.INTERNAL_METHOD,
            title="Internal method object",
            metadata={
                "card": {
                    "purpose": "secret internal transformation workflow",
                    "known_limitations": ["hidden calibration detail"],
                }
            },
        )
        compiled = compile_record(record, CompileContext({}, {}, {}))
        assert compiled.retrieval_text == ""
        assert compiled.structured.states == ()
        assert compiled.structured.aliases == ()
        assert compiled.leakage.max_quote_scope == "NONE"
        assert compiled.header().exposure is ProductExposure.INTERNAL_METHOD

    def test_internal_code_record_is_identity_only(self) -> None:
        record = _record(
            "MOD.SYNTH.CODE.V1",
            ObjectType.MODEL,
            exposure=ProductExposure.INTERNAL_CODE,
            metadata={"card": {"purpose": "def secret(): return 1"}},
        )
        compiled = compile_record(record, CompileContext({}, {}, {}))
        assert compiled.retrieval_text == ""
        assert compiled.leakage.max_quote_scope == "NONE"

    def test_unknown_exposure_fails_the_build(self) -> None:
        record = replace(
            _record("MOD.SYNTH.UNKNOWN.V1", ObjectType.MODEL),
            exposure="NOT_A_REAL_EXPOSURE",
        )
        with pytest.raises(RetrievalCompileError) as excinfo:
            compile_record(record, CompileContext({}, {}, {}))
        assert excinfo.value.kind == "UNKNOWN_EXPOSURE"

    def test_artifact_type_is_refused(self) -> None:
        record = _record("ART.SYNTH.NOPE.V1", ObjectType.ARTIFACT)
        with pytest.raises(RetrievalCompileError) as excinfo:
            compile_record(record, CompileContext({}, {}, {}))
        assert excinfo.value.kind == "NON_RETRIEVAL_OBJECT_TYPE"

    def test_code_segments_are_stripped_from_generated_text(self) -> None:
        clean, hit_internal, hit_code = sanitize_text(
            "A safe statement. indicator(period) plots a line."
        )
        assert hit_code is True
        assert "indicator(" not in clean
        assert "A safe statement." in clean

    def test_internal_segments_are_stripped_from_generated_text(self) -> None:
        clean, hit_internal, hit_code = sanitize_text(
            "Fine sentence. anti-leakage logic guards the feature engineering."
        )
        assert hit_internal is True
        assert hit_code is False
        assert "anti-leakage" not in clean
        assert "Fine sentence." in clean

    def test_max_quote_scope_is_synthesis_for_real_records(self, generation) -> None:
        assert {
            record.leakage.max_quote_scope for record in generation.records
        } == {"SYNTHESIS"}


# ---------------------------------------------------------------------------
# H — policy before content
# ---------------------------------------------------------------------------


class TestPolicyBeforeContent:
    def test_deny_before_load_zero_loads_on_deny(self, index) -> None:
        svc, loads = _spy_service(index)
        response = svc.retrieve(AUTH, NO_CAP, RetrievalQuery(text="eur weekly tier"))
        assert response.results == ()
        assert len(response.denied) > 0
        assert loads == []

    def test_allow_loads_each_allowed_record_exactly_once(self, index) -> None:
        svc, loads = _spy_service(index)
        response = svc.retrieve(AUTH, MEMBER, RetrievalQuery(object_type="MODEL"))
        allowed = [result.object_id for result in response.results]
        assert len(allowed) == 7
        assert sorted(loads) == sorted(allowed)
        assert len(loads) == len(set(loads))

    def test_denial_entries_are_content_free(self, service) -> None:
        response = service.retrieve(ANON, NO_CAP, RetrievalQuery(object_type="MODEL"))
        assert response.results == ()
        assert response.denied
        for denied in response.denied:
            assert set(denied.__dict__) == {"object_id", "exposure", "reason_code"}
        assert "retrieval_text" not in str(response.to_dict()["denied"])

    def test_unauthorized_text_never_reaches_the_response(self) -> None:
        marker = "SECRET_INTERNAL_MARKER_XYZZY"
        svc = RetrievalService(_marker_index(marker))
        denied = svc.retrieve(AUTH, MEMBER, RetrievalQuery())
        assert denied.results == ()
        assert marker not in str(denied.to_dict())
        allowed = svc.retrieve(AUTH, RESEARCH, RetrievalQuery())
        assert [r.object_id for r in allowed.results] == ["EV.SYNTH.SECRET.V1"]
        assert marker in str(allowed.to_dict())

    def test_unknown_exposure_fails_closed_at_release(self, index) -> None:
        generation = index.require()
        target = generation.records[0]
        broken_generation = IndexGeneration(
            generation=generation.generation,
            source_fingerprint=generation.source_fingerprint,
            index_hash=generation.index_hash,
            records=tuple(
                record.model_copy(update={"exposure_class": None})
                if record.object_id == target.object_id
                else record
                for record in generation.records
            ),
        )
        broken_index = RetrievalIndex()
        broken_index.publish(broken_generation)
        svc, loads = _spy_service(broken_index)
        response = svc.retrieve(AUTH, INTERNAL, RetrievalQuery())
        assert loads == []
        reasons = {denied.reason_code for denied in response.denied}
        assert "UNKNOWN_EXPOSURE" in reasons

    def test_sequence_uses_the_ratified_enforcement_service(self, service) -> None:
        assert hasattr(service.enforcement, "guard")
        assert hasattr(service.enforcement, "audit_records")
        service.retrieve(AUTH, MEMBER, RetrievalQuery(text="tier"))
        record = service.enforcement.audit_records()[-1]
        assert set(record.__dict__) >= {
            "correlation_id",
            "principal_id",
            "action",
            "resource_type",
            "resource_id",
            "exposure",
            "allowed",
            "reason_code",
            "authenticated",
            "at",
        }


# ---------------------------------------------------------------------------
# I — exposure matrix
# ---------------------------------------------------------------------------


def _exposure_index() -> RetrievalIndex:
    records = [
        _record(
            f"MOD.EXP.{label}.V1",
            ObjectType.MODEL,
            exposure=exposure,
            title=f"{label} object",
        )
        for label, exposure in (
            ("PUBLIC", ProductExposure.PUBLIC_TEACHING),
            ("SUBSCRIBER", ProductExposure.SUBSCRIBER_MODEL),
            ("OPERATOR", ProductExposure.OPERATOR_ONLY),
            ("RESEARCH", ProductExposure.RESEARCH_LAB),
            ("INTERNALM", ProductExposure.INTERNAL_METHOD),
            ("INTERNALC", ProductExposure.INTERNAL_CODE),
        )
    ]
    return _indexed(records)


class TestExposureMatrix:
    @pytest.mark.parametrize(
        "principal,context,allowed",
        [
            (ANON, NO_CAP, {"PUBLIC"}),
            (ANON, MEMBER, {"PUBLIC"}),
            (AUTH, NO_CAP, {"PUBLIC"}),
            (AUTH, PUBLIC, {"PUBLIC"}),
            (AUTH, MEMBER, {"PUBLIC", "SUBSCRIBER"}),
            (AUTH, OPERATOR, {"PUBLIC", "SUBSCRIBER", "OPERATOR", "RESEARCH"}),
            (AUTH, RESEARCH, {"PUBLIC", "SUBSCRIBER", "OPERATOR", "RESEARCH"}),
            (AUTH, ADMIN, {"PUBLIC"}),
            # forge.internal admits ONLY the internal classes (fail closed for
            # ordinary exposure: no ordinary capability atom is held).
            (AUTH, INTERNAL, {"PUBLIC", "INTERNALM", "INTERNALC"}),
        ],
    )
    def test_matrix(self, principal, context, allowed) -> None:
        svc = RetrievalService(_exposure_index())
        response = svc.retrieve(principal, context, RetrievalQuery())
        seen = {result.object_id.rsplit(".", 2)[-2] for result in response.results}
        assert seen == allowed

    def test_real_corpus_operator_only_requires_operator_capability(self, service) -> None:
        denied = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(canonical_id="SET.XAU.QUARTER_ZONE.V1")
        )
        assert denied.results == ()
        assert denied.denied[0].reason_code == "ENTITLEMENT_MISSING"
        allowed = service.retrieve(
            AUTH, OPERATOR, RetrievalQuery(canonical_id="SET.XAU.QUARTER_ZONE.V1")
        )
        assert [r.object_id for r in allowed.results] == ["SET.XAU.QUARTER_ZONE.V1"]

    def test_research_authorization_never_changes_research_status(self, service) -> None:
        response = service.retrieve(
            AUTH, RESEARCH, RetrievalQuery(canonical_id="EV.XAU.PROMOTION.120_132.V1")
        )
        result = response.results[0]
        assert result.status == "RESEARCH_FLAG"
        assert result.exposure == "RESEARCH_LAB"

    def test_anonymous_never_sees_non_public_corpus(self, service) -> None:
        response = service.retrieve(ANON, NO_CAP, RetrievalQuery())
        assert response.results == ()
        assert len(response.denied) == 30


# ---------------------------------------------------------------------------
# J — evidence and provenance navigation
# ---------------------------------------------------------------------------


class TestProvenanceNavigation:
    def test_claim_to_evidence_to_source_artifact(self, service) -> None:
        chain = service.navigate(AUTH, RESEARCH, "CL.EUR.DAILY.TIER_CALIBRATION")
        assert chain.found is True and chain.allowed is True
        assert chain.supported is True
        assert "EV.EUR.DAILY.PHASE1_TIERS.V1" in chain.evidence_ids
        assert any(hop.kind == "EVIDENCE" for hop in chain.hops)
        assert any(hop.kind == "ARTIFACT" for hop in chain.hops)
        locators = [artifact.locator for artifact in chain.artifacts]
        assert "corpus/research/eur/daily_range_tracker/PHASE_1_LEDGER.md" in locators
        for artifact in chain.artifacts:
            assert artifact.content_identity.startswith("sha256:")
            assert artifact.source_state in {"READ", "VERIFIED", "MATERIALIZED", "LOCATED"}

    def test_found_is_distinct_from_supported(self, service) -> None:
        chain = service.navigate(AUTH, MEMBER, "MOD.BTC.TRACKER.DWM.V1")
        assert chain.found is True
        assert chain.allowed is True
        assert chain.supported is False
        assert chain.support_classification == "NO_SOURCE"
        assert "NO_EVIDENCE_REFERENCE" in chain.support_gaps

    def test_missing_object_is_reported_not_invented(self, service) -> None:
        chain = service.navigate(AUTH, MEMBER, "CL.DOES.NOT.EXIST")
        assert chain.found is False
        assert chain.supported is False
        assert [link.reason for link in chain.missing] == ["NOT_IN_INDEX"]

    def test_evidence_without_source_is_reported_as_missing(self) -> None:
        claim = _record(
            "CL.SYNTH.NOSOURCE.V1",
            ObjectType.CLAIM,
            references=(
                CanonicalReference(
                    target_id="EV.SYNTH.NOSOURCE.V1", relation="supported_by"
                ),
            ),
        )
        evidence = _record(
            "EV.SYNTH.NOSOURCE.V1",
            ObjectType.EVIDENCE,
            references=(
                CanonicalReference(
                    target_id="CL.SYNTH.NOSOURCE.V1", relation="evidence_for"
                ),
            ),
        )
        idx = _indexed([claim, evidence])
        chain = RetrievalService(idx).navigate(AUTH, MEMBER, "CL.SYNTH.NOSOURCE.V1")
        assert chain.found is True
        assert chain.allowed is True
        assert chain.supported is False
        assert "EVIDENCE_WITHOUT_SOURCE" in chain.support_gaps
        assert chain.artifacts == ()

    def test_denied_hop_stops_the_chain_without_loading_it(self, index) -> None:
        svc, loads = _spy_service(index)
        chain = svc.navigate(AUTH, MEMBER, "CL.XAU.PROMOTION.120_132")
        assert chain.allowed is True
        assert "EV.XAU.PROMOTION.120_132.V1" not in loads
        assert chain.denied[0].object_id == "EV.XAU.PROMOTION.120_132.V1"
        assert any(link.reason == "POLICY_DENIED" for link in chain.missing)
        assert chain.artifacts == ()

    def test_denied_root_loads_nothing(self, index) -> None:
        svc, loads = _spy_service(index)
        chain = svc.navigate(AUTH, NO_CAP, "CL.EUR.HO.D3_DIRECTION")
        assert chain.found is True
        assert chain.allowed is False
        assert loads == []
        assert chain.artifacts == ()

    def test_every_launch_claim_resolves_a_chain(self, service) -> None:
        generation = service.index.require()
        claims = [
            record.object_id
            for record in generation.records
            if record.object_type is ObjectType.CLAIM
        ]
        assert len(claims) == 10
        for claim_id in claims:
            chain = service.navigate(AUTH, RESEARCH, claim_id)
            assert chain.allowed is True, claim_id
            assert chain.evidence_ids, claim_id
            assert chain.artifacts, claim_id


# ---------------------------------------------------------------------------
# K — negative evidence
# ---------------------------------------------------------------------------


class TestNegativeEvidence:
    def test_fib_r11_survives_as_falsified_negative_evidence(self, gateway, service) -> None:
        canonical = gateway.get_object("EV.FIB.R11.ANCHOR_OVERGEN.V1")
        assert canonical.status is EvidenceStatus.FALSIFIED
        assert (
            canonical.metadata["card"]["evidence_type"]
            == EvidenceType.NEGATIVE_EVIDENCE.value
        )
        result = service.exact(AUTH, RESEARCH, "EV.FIB.R11.ANCHOR_OVERGEN.V1")
        assert result is not None
        assert result.status == "FALSIFIED"
        assert result.supported is True

    def test_negative_evidence_is_research_gated(self, service) -> None:
        member = service.retrieve(
            AUTH, MEMBER, RetrievalQuery(canonical_id="EV.FIB.R11.ANCHOR_OVERGEN.V1")
        )
        assert member.results == ()
        assert member.denied[0].exposure == "RESEARCH_LAB"

    def test_negative_evidence_is_never_reworded_as_support(self, index) -> None:
        record = index.require().record("CL.FIB.R11.GENERATOR_FAILURE")
        assert record.status is EvidenceStatus.FALSIFIED
        assert "overproduced" in record.retrieval_text


# ---------------------------------------------------------------------------
# L — quarantine
# ---------------------------------------------------------------------------


class TestQuarantine:
    @pytest.fixture(scope="class")
    def report(self):
        return canonicalize_files(load_corpus_files(REPO_ROOT)).report

    @pytest.fixture(scope="class")
    def catalog(self, report) -> QuarantineCatalog:
        return QuarantineCatalog.from_report(report)

    def test_counts_match_persisted_state(self, gateway, report, catalog) -> None:
        assert len(gateway.list_object_ids()) == 30
        artifact_ids = {
            edge.artifact_id
            for object_id in gateway.list_object_ids()
            for edge in gateway.edges_for_object(object_id)
        }
        assert len(artifact_ids) == 29
        edge_count = sum(
            len(gateway.edges_for_object(object_id))
            for object_id in gateway.list_object_ids()
        )
        assert edge_count == 38
        assert report.quarantined == 9
        assert len(catalog) == 9

    def test_zero_card_file_quarantines(self, catalog) -> None:
        assert [
            entry.source_path
            for entry in catalog.entries
            if entry.source_path.startswith(CARD_PREFIXES)
        ] == []

    def test_quarantined_sources_never_become_records(self, generation, catalog) -> None:
        assert not (set(generation.ids) & catalog.paths)
        assert generation.quarantine == catalog.entries

    def test_ordinary_search_never_returns_quarantine(self, service, catalog) -> None:
        response = service.retrieve(AUTH, RESEARCH, RetrievalQuery())
        assert response.quarantined == ()
        assert not ({r.object_id for r in response.results} & catalog.paths)

    def test_quarantined_source_excludes_a_defined_record(self, gateway) -> None:
        catalog = QuarantineCatalog(
            (
                QuarantineEntry(
                    "corpus/canonical/models/JPY_CARRY_GAME_MODEL_CARD_V1.md",
                    "test quarantine of a card source",
                ),
            )
        )
        idx = RetrievalIndex()
        report = build_index(
            gateway, quarantine=catalog, index=idx, mode=IndexBuildMode.APPLY
        )
        assert report.quarantined_excluded == ("MOD.JPY.CARRY_GAME.L1_L3.V1",)
        assert idx.require().record("MOD.JPY.CARRY_GAME.L1_L3.V1") is None
        assert len(idx.require().records) == 29

    def test_quarantine_discovery_requires_research_authorization(self, service) -> None:
        allowed = service.retrieve(
            AUTH, RESEARCH, RetrievalQuery(include_quarantine=True)
        )
        assert len(allowed.quarantined) == 9
        for notice in allowed.quarantined:
            assert set(notice.__dict__) == {"source_path", "reason", "quarantined"}
            assert notice.quarantined is True

        # the operator capability is cumulative through RESEARCH_LAB, so it
        # admits research-gap discovery too (frozen II.4 matrix).
        operator_view = service.retrieve(
            AUTH, OPERATOR, RetrievalQuery(include_quarantine=True)
        )
        assert len(operator_view.quarantined) == 9

        for principal, context in (
            (AUTH, MEMBER),
            (AUTH, NO_CAP),
            (ANON, NO_CAP),
            (AUTH, ADMIN),
            (AUTH, INTERNAL),
        ):
            denied = service.retrieve(
                principal, context, RetrievalQuery(include_quarantine=True)
            )
            assert denied.quarantined == (), (principal, context)


# ---------------------------------------------------------------------------
# M / N — build, rebuild, freshness, conflict, failure
# ---------------------------------------------------------------------------


class TestBuildLaws:
    def test_dry_run_publishes_nothing(self, gateway) -> None:
        idx = RetrievalIndex()
        report = run_index_build(gateway, REPO_ROOT, IndexBuildMode.DRY_RUN, idx)
        assert report.outcome is IndexBuildOutcome.DRY_RUN
        assert report.published is False
        assert report.compiled == 30
        assert idx.current is None

    def test_unbuilt_index_fails_closed(self) -> None:
        with pytest.raises(IndexNotBuilt):
            RetrievalIndex().require()

    def test_rebuild_is_idempotent(self, gateway) -> None:
        idx = RetrievalIndex()
        first = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        second = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        assert first.outcome is IndexBuildOutcome.PUBLISHED
        assert second.outcome is IndexBuildOutcome.UNCHANGED
        assert first.index_hash == second.index_hash
        assert second.generation == first.generation == 1
        generation = idx.require()
        assert len(generation.ids) == len(set(generation.ids)) == 30

    def test_staleness_detected_and_cleared_by_rebuild(self) -> None:
        gateway = _applied()
        idx = RetrievalIndex()
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        assert idx.is_stale(gateway) is False
        gateway.transition_status("MOD.EUR.WEEKLY.V1_1", "PARKED")
        assert idx.is_stale(gateway) is True
        report = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        assert report.outcome is IndexBuildOutcome.PUBLISHED
        assert report.changed == ("MOD.EUR.WEEKLY.V1_1",)
        assert report.generation == 2
        assert idx.is_stale(gateway) is False
        assert (
            idx.require().record("MOD.EUR.WEEKLY.V1_1").status is EvidenceStatus.PARKED
        )

    def test_fresh_index_is_stale_until_built(self, gateway) -> None:
        assert RetrievalIndex().is_stale(gateway) is True

    def test_added_object_starts_a_new_generation(self) -> None:
        gateway = _applied()
        idx = RetrievalIndex()
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        with gateway.transaction():
            gateway.create_object(_record("MOD.SYNTH.ADDED.V1", ObjectType.MODEL))
        report = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        assert report.added == ("MOD.SYNTH.ADDED.V1",)
        assert report.removed == ()
        assert report.generation == 2
        assert idx.require().record("MOD.SYNTH.ADDED.V1") is not None

    def test_generation_metadata_never_changes_record_identity(self) -> None:
        """Index-generation bookkeeping is not content: a record recompiled
        into a later generation keeps its exact ``content_hash()``."""
        gateway = _applied()
        idx = RetrievalIndex()
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        first = idx.require()
        survivor = "CL.XAU.PROMOTION.68_80"
        first_record = first.record(survivor)
        first_hash = first_record.content_hash()
        assert first_record.generation == 1
        # top-level generation bookkeeping is excluded from identity (the
        # source generation inside conflict metadata is content, F3)
        assert "generation" not in json.loads(first_record.deterministic_payload())

        with gateway.transaction():
            gateway.create_object(_record("MOD.SYNTH.ADDED.V1", ObjectType.MODEL))
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        second = idx.require()
        assert second.generation == 2
        rebuilt = second.record(survivor)
        assert rebuilt.generation == 2
        assert rebuilt.content_hash() == first_hash

    def test_duplicate_listing_conflicts_and_publishes_nothing(self) -> None:
        gateway = _applied()
        idx = RetrievalIndex()
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        before = idx.require().content_hash()
        with pytest.raises(IndexBuildError) as excinfo:
            build_index(_DuplicatedListing(gateway), index=idx, mode=IndexBuildMode.APPLY)
        assert excinfo.value.kind == "DUPLICATE_CANONICAL_OBJECT"
        assert idx.require().content_hash() == before

    def test_partial_failure_leaves_previous_generation_current(self) -> None:
        gateway = _applied()
        idx = RetrievalIndex()
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        before = idx.require()
        with pytest.raises(IndexBuildError):
            build_index(
                _PoisonedExposure(gateway, "MOD.EUR.WEEKLY.V1_1"),
                index=idx,
                mode=IndexBuildMode.APPLY,
            )
        after = idx.require()
        assert after.content_hash() == before.content_hash()
        assert after.generation == before.generation == 1

    def test_publication_is_atomic_from_a_readers_view(self, gateway) -> None:
        idx = RetrievalIndex()
        run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
        seen = idx.current
        assert isinstance(seen, IndexGeneration)
        assert tuple(sorted(seen.ids)) == seen.ids
        assert len(seen.records) == 30

    def test_index_never_executes_on_import_or_startup(self) -> None:
        from app.forge.retrieval import index as index_module

        assert not any(
            isinstance(value, RetrievalIndex) for value in vars(index_module).values()
        )
        from app.main import _build_forge_container

        container = _build_forge_container()
        assert not hasattr(container, "retrieval_index")


# ---------------------------------------------------------------------------
# O — reference-order normalization (I.3 limitation A)
# ---------------------------------------------------------------------------


class TestReferenceOrderNormalization:
    def _two_records(self):
        first = CanonicalReference(target_id="EV.SYNTH.A.V1", relation="supported_by")
        second = CanonicalReference(target_id="EV.SYNTH.B.V1", relation="supported_by")
        return (
            _record("MOD.SYNTH.ORDER.V1", ObjectType.MODEL, references=(first, second)),
            _record("MOD.SYNTH.ORDER.V1", ObjectType.MODEL, references=(second, first)),
        )

    def test_frozen_i1_hash_semantics_are_untouched(self) -> None:
        a, b = self._two_records()
        # frozen I.1 IS reference-order-sensitive (unchanged semantics) …
        domain_a = a.to_domain()
        domain_b = b.to_domain()
        assert domain_a.content_hash() != domain_b.content_hash()
        # … while index identity normalizes the reference SET.
        assert normalized_content_hash(a) == normalized_content_hash(b)

    def test_index_hash_is_identical_across_reference_order(self) -> None:
        gateway = _applied()
        first = RetrievalIndex()
        report_a = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, first)
        reordered = RetrievalIndex()
        report_b = build_index(
            _ReorderedReferences(gateway), index=reordered, mode=IndexBuildMode.APPLY
        )
        assert report_a.index_hash == report_b.index_hash
        assert report_a.source_fingerprint == report_b.source_fingerprint

    def test_governed_payload_sorts_relationships(self, index) -> None:
        record = index.require().record("MOD.EUR.HIGHER_ORDER.V1")
        related = record.related_ids
        assert list(related) == sorted(
            related, key=lambda item: (item.relation, item.target_id)
        )
        assert record.content_hash() == record.model_copy(
            update={"related_ids": tuple(reversed(related))}
        ).content_hash()


# ---------------------------------------------------------------------------
# P — governance artifact coverage (I.3 limitation B)
# ---------------------------------------------------------------------------


class TestGovernanceCoverage:
    GOVERNANCE_CONTRACTS = (
        "ANSWER_CONTRACT_V1",
        "RETRIEVAL_OBJECT_SCHEMA_V1",
        "PRODUCT_EXPOSURE_RULES_V1",
        "ONTOLOGY_CROSSWALK_V1",
        "CEREBUS_CANONICAL_TAXONOMY_V1",
        "MODEL_CARD_SCHEMA_V1",
        "EVIDENCE_CARD_SCHEMA_V1",
        "SETUP_OPERATOR_CARD_SCHEMA_V1",
    )

    @staticmethod
    def _registered_locators(gateway) -> set[str]:
        locators = set()
        for object_id in gateway.list_object_ids():
            for edge in gateway.edges_for_object(object_id):
                artifact = gateway.get_artifact(edge.artifact_id)
                if artifact is not None:
                    locators.add(artifact.locator)
        return locators

    def test_claim_registry_is_registered_but_never_a_record(
        self, gateway, generation
    ) -> None:
        locators = self._registered_locators(gateway)
        assert "corpus/canonical/CLAIM_REGISTRY_V1.md" in locators
        assert not any(record.object_id.startswith("ART.") for record in generation.records)
        assert not any(
            "CLAIM_REGISTRY" in record.object_id for record in generation.records
        )

    def test_governance_contracts_are_never_indexed(self, gateway, generation) -> None:
        locators = self._registered_locators(gateway)
        for contract in self.GOVERNANCE_CONTRACTS:
            assert not any(contract in locator for locator in locators)
        for record in generation.records:
            for contract in self.GOVERNANCE_CONTRACTS:
                assert contract not in record.object_id
                assert contract not in record.retrieval_text

    def test_claim_registry_still_defines_every_claim(self, gateway) -> None:
        claims = [
            object_id
            for object_id in gateway.list_object_ids()
            if object_id.startswith("CL.")
        ]
        assert len(claims) == 10
        for claim_id in claims:
            assert "DEFINES" in {
                edge.relation for edge in gateway.edges_for_object(claim_id)
            }


# ---------------------------------------------------------------------------
# Q — model-truth regressions
# ---------------------------------------------------------------------------


class TestModelTruth:
    def test_eur_families_stay_separate(self, service) -> None:
        daily = service.exact(AUTH, MEMBER, "MOD.EUR.DAILY.NEWS_REKEY.V1")
        weekly = service.exact(AUTH, MEMBER, "MOD.EUR.WEEKLY.V1_1")
        higher = service.exact(AUTH, MEMBER, "MOD.EUR.HIGHER_ORDER.V1")
        assert {daily.status, weekly.status, higher.status} == {"CANDIDATE"}
        assert len({daily.title, weekly.title, higher.title}) == 3
        assert {daily.model_family, weekly.model_family, higher.model_family} == {"EUR"}
        assert daily.retrieval_text != weekly.retrieval_text != higher.retrieval_text

    def test_xau_layers_remain_distinct(self, service) -> None:
        xau = service.retrieve(AUTH, MEMBER, RetrievalQuery(model_family="XAU"))
        by_layer = {result.object_id: result.layer for result in xau.results}
        assert by_layer["MOD.XAU.GAME.L1_L2_L3.V1"] == "CROSS_LAYER"
        assert by_layer["CL.XAU.PROMOTION.68_80"] == "NONE"
        seen: dict[str, set[str]] = {}
        for layer in ("L1", "L2", "L3"):
            seen[layer] = {
                result.object_id
                for result in service.retrieve(
                    AUTH, MEMBER, RetrievalQuery(layer=layer)
                ).results
            }
        assert all(seen.values())
        assert not (seen["L1"] & seen["L2"])
        assert not (seen["L2"] & seen["L3"])

    def test_btc_game_is_not_fabricated(self, generation) -> None:
        ids = generation.ids
        assert not any("BTC.GAME" in object_id for object_id in ids)
        assert "MOD.BTC.TRACKER.DWM.V1" in ids

    def test_btc_tracker_keeps_its_honest_gap(self, service) -> None:
        result = service.exact(AUTH, MEMBER, "MOD.BTC.TRACKER.DWM.V1")
        assert result is not None
        assert result.supported is False
        assert "NO_EVIDENCE_REFERENCE" in result.support_gaps
        record = service.index.require().record("MOD.BTC.TRACKER.DWM.V1")
        assert record.routing.requires_evidence_card is False

    def test_jpy_role_asymmetry_is_preserved(self, service) -> None:
        claim = service.exact(AUTH, MEMBER, "CL.JPY.CARRY.ROLE_RELATION")
        assert claim is not None
        assert claim.market_scope == ("USDJPY", "AUDJPY", "EURJPY")
        assert "confirmation" in claim.retrieval_text
        lowered = claim.retrieval_text.lower()
        assert "equal vote" not in lowered
        assert "equal-vote" not in lowered

    def test_execution_classes_survive_without_automation_creep(
        self, gateway, generation
    ) -> None:
        expected = {
            "SET.XAU.QUARTER_ZONE.V1": SetupClass.MANUAL_OPERATOR.value,
            "SET.JPY.CARRY_ROLE_GATE.V1": SetupClass.MANUAL_OPERATOR.value,
            "SET.FIB.REKEY.V1": SetupClass.RESEARCH_ONLY.value,
        }
        for setup_id, execution_class in expected.items():
            card = gateway.get_object(setup_id).metadata["card"]
            assert card["execution_class"] == execution_class
            terms = generation.record(setup_id).structured.terms
            assert execution_class.lower() in terms
        for object_id in gateway.list_object_ids():
            card = gateway.get_object(object_id).metadata.get("card", {})
            if card.get("execution_class"):
                assert card["execution_class"] != SetupClass.AUTOMATION_APPROVED.value
        for record in generation.records:
            lowered = record.retrieval_text.lower()
            assert "automation approved" not in lowered
            assert "autonomous execution" not in lowered

    def test_p90_stays_lineage_never_a_statistic(self, generation) -> None:
        daily = generation.record("MOD.EUR.DAILY.NEWS_REKEY.V1")
        assert "do not import historical P90 win rates" in daily.retrieval_text
        assert daily.structured.metrics == ()
        assert daily.structured.sample_n is None
        for record in generation.records:
            for match in re.finditer(r"P90[^.]{0,40}", record.retrieval_text):
                assert "%" not in match.group(0), record.object_id

    def test_fib_range_birth_is_not_reduced_to_coordinates(self, generation) -> None:
        record = generation.record("MOD.CROSSASSET.FIB.RANGE_BIRTH.V1")
        assert "Range Birth" in record.structured.aliases
        assert record.support.supported is True
        assert record.support.evidence_ids == ("EV.FIB.R11.ANCHOR_OVERGEN.V1",)


# ---------------------------------------------------------------------------
# R — internal material
# ---------------------------------------------------------------------------


class TestInternalMaterial:
    MARKERS = (
        "internal_method",
        "internal_code",
        "anti-leakage",
        "hidden calibration",
        "unreleased transformation",
        "feature engineering",
        "```",
        "indicator(",
        "strategy(",
    )

    def test_no_internal_body_anywhere_in_the_index(self, generation) -> None:
        for record in generation.records:
            haystack = " ".join(
                (
                    record.retrieval_text,
                    " ".join(record.structured.terms),
                    " ".join(record.structured.aliases),
                    " ".join(record.structured.states),
                    " ".join(record.structured.events),
                )
            ).lower()
            for marker in self.MARKERS:
                assert marker not in haystack, (record.object_id, marker)
            assert record.leakage.contains_code is False
            assert record.leakage.contains_internal_method is False

    def test_policy_module_is_untouched(self) -> None:
        digest = hashlib.sha256(
            (REPO_ROOT / "app" / "forge" / "policy.py").read_bytes()
        ).hexdigest()
        assert digest == POLICY_MODULE_SHA256

    def test_retrieval_never_assigns_public_exposure_itself(self) -> None:
        package = REPO_ROOT / "app" / "forge" / "retrieval"
        for path in sorted(package.glob("*.py")):
            assert "PUBLIC_TEACHING" not in path.read_text(encoding="utf-8"), path.name

    def test_internal_records_are_released_only_to_forge_internal(self) -> None:
        idx = _indexed(
            [
                _record(
                    "MOD.SYNTH.INTERNAL2.V1",
                    ObjectType.MODEL,
                    exposure=ProductExposure.INTERNAL_METHOD,
                    metadata={"card": {"purpose": "internal purpose text"}},
                )
            ]
        )
        svc = RetrievalService(idx)
        for principal, context in (
            (AUTH, NO_CAP),
            (AUTH, MEMBER),
            (AUTH, OPERATOR),
            (AUTH, RESEARCH),
            (AUTH, ADMIN),
            (ANON, NO_CAP),
        ):
            response = svc.retrieve(principal, context, RetrievalQuery())
            assert response.results == (), (principal, context)
            assert response.denied[0].reason_code in {
                "EXPOSURE_FORBIDDEN",
                "NOT_AUTHENTICATED",
            }
        allowed = svc.retrieve(AUTH, INTERNAL, RetrievalQuery())
        assert [r.object_id for r in allowed.results] == ["MOD.SYNTH.INTERNAL2.V1"]
        # even to forge.internal the body stays empty: I.4 never indexes it
        assert allowed.results[0].retrieval_text == ""


# ---------------------------------------------------------------------------
# S — boundary integrity
# ---------------------------------------------------------------------------


class TestBoundaryIntegrity:
    FORGE_ROUTES = {"/forge/v1/health", "/forge/v1/ready", "/forge/v1/meta"}

    def test_no_route_is_added(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        routes = {getattr(route, "path", "") for route in app.routes}
        assert {path for path in routes if path.startswith("/forge/")} == self.FORGE_ROUTES
        for forbidden in (
            "/forge/v1/retrieval",
            "/forge/v1/search",
            "/forge/v1/objects",
            "/forge/v1/corpus",
            "/forge/v1/query",
            "/forge/v1/index",
        ):
            assert forbidden not in routes
            assert client.get(forbidden).status_code == 404

    def test_no_commercial_or_provider_object_is_created(self) -> None:
        """II.5 supersedes the II.1-era assertion: the composition root now
        wires the provider registry. The bound objects are deterministic
        in-process fakes — still no commercial vendor object, no credential
        material, and no network client.
        """
        from app.main import _build_forge_container

        container = _build_forge_container()
        assert container.providers is not None
        assert container.providers.bound_names() == {
            "llm": "fake",
            "commerce": "fake",
            "notification": "fake",
            "storage": "fake",
        }
        for impl in container.providers.implementations():
            assert type(impl).__module__ == "app.forge.providers.fakes"

    def test_no_new_migration(self) -> None:
        from app.forge.persistence.sql.migrations import discover_migrations

        # Exact authorized set incl. operator-authorized 003 (closure repair)
        # and 004 (Build Agent #14 GAP-05 durable audit/event ledger packet).
        assert [migration.version for migration in discover_migrations()] == [1, 2, 3, 4]

    def test_retrieval_package_has_no_credential_material(self) -> None:
        package = REPO_ROOT / "app" / "forge" / "retrieval"
        for path in sorted(package.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for banned in (
                "postgres://",
                "postgresql://",
                "api_key",
                "password",
                "secret_",
            ):
                assert banned not in source, (path.name, banned)


# ---------------------------------------------------------------------------
# T — reproducibility
# ---------------------------------------------------------------------------


class TestReproducibility:
    def test_two_builds_are_byte_identical(self) -> None:
        generation_a = _built()[1].require()
        generation_b = _built()[1].require()
        assert generation_a.source_fingerprint == generation_b.source_fingerprint
        assert generation_a.index_hash == generation_b.index_hash
        assert generation_a.content_hash() == generation_b.content_hash()
        for record_a, record_b in zip(generation_a.records, generation_b.records):
            assert record_a.object_id == record_b.object_id
            assert record_a.content_hash() == record_b.content_hash()

    def test_report_is_deterministic(self, gateway) -> None:
        first = run_index_build(gateway, REPO_ROOT, IndexBuildMode.DRY_RUN)
        second = run_index_build(gateway, REPO_ROOT, IndexBuildMode.DRY_RUN)
        assert first.to_json() == second.to_json()
        assert first.content_hash() == second.content_hash()
        assert "timestamp" not in first.to_json()


# ---------------------------------------------------------------------------
# V — security
# ---------------------------------------------------------------------------


class TestSecurity:
    def test_denial_never_produces_a_body(self) -> None:
        marker = "PROTECTED_BODY_SHOULD_NOT_APPEAR"
        svc = RetrievalService(_marker_index(marker))
        response = svc.retrieve(AUTH, MEMBER, RetrievalQuery())
        assert response.results == ()
        assert marker not in str(response.to_dict())

    def test_audit_trail_carries_no_query_body_or_result_text(self, index) -> None:
        svc, _loads = _spy_service(index)
        svc.retrieve(AUTH, MEMBER, RetrievalQuery(text="uniquequerytoken"))
        for record in svc.enforcement.audit_records():
            assert "uniquequerytoken" not in record.resource_id
            assert not hasattr(record, "retrieval_text")

    def test_no_credential_material_in_tests_or_sources(self) -> None:
        package = REPO_ROOT / "app" / "forge" / "retrieval"
        for path in sorted(package.glob("*.py")):
            source = path.read_text(encoding="utf-8")
            for banned in ("postgres://", "postgresql://", "api_key=", "API_KEY="):
                assert banned not in source, (path.name, banned)

    def test_citations_are_traceable_without_bodies(self, service) -> None:
        chain = service.navigate(AUTH, MEMBER, "CL.XAU.PROMOTION.68_80")
        assert chain.allowed is True
        assert chain.artifacts
        for artifact in chain.artifacts:
            assert artifact.locator.startswith("corpus/")
            assert artifact.content_identity.startswith("sha256:")
