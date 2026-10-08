"""BOOK II / BLOC II.2 — PERSISTENCE — focused acceptance tests.

Unit/contract truth runs through the persistence PORT (in-memory gateway is a
real port implementation; the SQL gateway executes its portable migration
contract on SQLite as a dialect/schema executor — PostgreSQL server semantics
are integration evidence, not asserted here).

The SQL tests are skipped automatically when SQLAlchemy is unavailable, so the
suite stays runnable in the repository's established CI environment.
"""

from __future__ import annotations

import importlib.util

import pytest

from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalReference,
    ClaimIdentity,
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
)
from app.forge.config import ForgeConfig
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.port import (
    DuplicateArtifact,
    DuplicateCanonicalObject,
    DuplicateProvenanceEdge,
    DanglingReference,
    IllegalStatusTransition,
    ObjectNotFound,
    PersistenceGateway,
    PersistenceUnavailable,
    SelfReferenceForbidden,
    StaleWriteConflict,
)
from app.forge.persistence.records import (
    ArtifactRecord,
    CanonicalObjectRecord,
    ProvenanceEdgeRecord,
)
from app.forge.provenance import Artifact, ArtifactClass, SourceState, classify_support

SQLA_AVAILABLE = importlib.util.find_spec("sqlalchemy") is not None


def _obj(
    cid: str = "MOD.TEST.OBJ.V1",
    object_type: ObjectType = ObjectType.MODEL,
    status: EvidenceStatus = EvidenceStatus.CANDIDATE,
    references: tuple[CanonicalReference, ...] = (),
    metadata: dict | None = None,
) -> CanonicalObject:
    return CanonicalObject(
        canonical_id=CanonicalId(value=cid, object_type=object_type),
        title="Test object",
        version="v1",
        status=status,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.L2,
        references=references,
        metadata=metadata or {"key": "value"},
    )


def _record(obj: CanonicalObject) -> CanonicalObjectRecord:
    return CanonicalObjectRecord.from_domain(obj)


def _artifact(
    aid: str = "ART.MARKDOWN.ABCDEF0123456789ABCDEFAB",
    source_class: str = ArtifactClass.MARKDOWN.value,
    source_state: SourceState = SourceState.VERIFIED,
    content_identity: str | None = "sha256:" + "a" * 64,
) -> ArtifactRecord:
    artifact = Artifact(
        artifact_id=aid,
        source_class=source_class,
        title="source",
        locator=" somewhere ",
        content_identity=content_identity,
        source_state=source_state,
    )
    return ArtifactRecord.from_domain(artifact)


# ---------------------------------------------------------------------------
# A — port / injection / isolation
# ---------------------------------------------------------------------------


class TestPortAndInjection:
    def test_in_memory_gateway_satisfies_port(self) -> None:
        assert isinstance(InMemoryPersistenceGateway(), PersistenceGateway)

    def test_container_accepts_persistence_wiring(self) -> None:
        from app.forge.service.container import ForgeServiceContainer

        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"),
            persistence=InMemoryPersistenceGateway(),
        )
        assert container.persistence is not None

    def test_container_rejects_non_port_persistence(self) -> None:
        from app.forge.service.container import ForgeServiceContainer

        with pytest.raises(TypeError, match="PersistenceGateway"):
            ForgeServiceContainer(
                config=ForgeConfig(environment="test"),
                persistence=object(),  # type: ignore[arg-type]
            )

    def test_container_still_rejects_policy_and_providers(self) -> None:
        from app.forge.policy import DefaultDenyPolicyEngine
        from app.forge.service.container import ForgeServiceContainer

        # II.4 supersedes the II.2-era RuntimeError guard: a valid PolicyEngine
        # is now accepted (the II.4 seam); arbitrary objects are still refused.
        ForgeServiceContainer(
            config=ForgeConfig(environment="test"), policy=DefaultDenyPolicyEngine()
        )
        with pytest.raises(TypeError, match="PolicyEngine"):
            ForgeServiceContainer(
                config=ForgeConfig(environment="test"), policy=object()
            )
        with pytest.raises(RuntimeError, match="II.5"):
            ForgeServiceContainer(
                config=ForgeConfig(environment="test"), providers=object()
            )

    def test_domain_modules_have_no_persistence_imports(self) -> None:
        import ast
        import importlib.resources

        for module in ("canonical", "schemas", "provenance"):
            pkg = importlib.resources.files("app.forge")
            tree = ast.parse((pkg / f"{module}.py").read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    assert not name.startswith(("sqlalchemy", "psycopg", "alembic")), (
                        f"domain module {module} imports {name}"
                    )

    def test_import_does_not_connect(self) -> None:
        # Importing the composition root with persistence disabled must not
        # construct any gateway or open any connection.
        import app.main  # noqa: F401
        import app.forge.persistence.memory  # noqa: F401
        import app.forge.persistence.sql.gateway  # noqa: F401

        from app.main import _build_forge_container

        container = _build_forge_container()
        assert container.persistence is None


# ---------------------------------------------------------------------------
# B / H — canonical round trips (all 8 object types)
# ---------------------------------------------------------------------------

ALL_TYPES = [
    (ObjectType.MODEL, "MOD.TEST.OBJ.V1"),
    (ObjectType.CLAIM, "CL.TEST.OBJ.V1"),
    (ObjectType.EVIDENCE, "EV.TEST.OBJ.V1"),
    (ObjectType.SETUP, "SET.TEST.OBJ.V1"),
    (ObjectType.DOCTRINE, "DOC.TEST.OBJ.V1"),
    (ObjectType.TERM, "TERM.TEST.OBJ.V1"),
    (ObjectType.LINEAGE, "LIN.TEST.OBJ.V1"),
    (ObjectType.ARTIFACT, "ART.TEST.OBJ.V1"),
]


class TestCanonicalRoundTrip:
    @pytest.mark.parametrize("object_type,cid", ALL_TYPES)
    def test_round_trip_preserves_type_identity(self, object_type, cid) -> None:
        gateway = InMemoryPersistenceGateway()
        obj = _obj(cid=cid, object_type=object_type)
        gateway.create_object(_record(obj))
        restored = gateway.get_object(cid)
        assert restored is not None
        domain = restored.to_domain()
        assert domain.canonical_id.object_type is object_type
        assert domain.canonical_id.value == cid
        assert domain.content_hash() == obj.content_hash()

    def test_status_exposure_layer_metadata_references_preserved(self) -> None:
        gateway = InMemoryPersistenceGateway()
        target = _obj(cid="MOD.TEST.TARGET.V1")
        gateway.create_object(_record(target))
        obj = _obj(
            cid="MOD.TEST.SRC.V1",
            status=EvidenceStatus.VALIDATED,
            references=(CanonicalReference(target_id="MOD.TEST.TARGET.V1", relation="SUPPORTS"),),
            metadata={"nested": {"a": 1}, "list": [1, 2, 3]},
        )
        gateway.create_object(_record(obj))
        restored = gateway.get_object("MOD.TEST.SRC.V1")
        assert restored is not None
        assert restored.status is EvidenceStatus.VALIDATED
        assert restored.exposure is ProductExposure.SUBSCRIBER_MODEL
        assert restored.layer is Layer.L2
        assert restored.metadata == {"nested": {"a": 1}, "list": [1, 2, 3]}
        assert restored.references[0].target_id == "MOD.TEST.TARGET.V1"
        domain = restored.to_domain()
        assert domain.deterministic_payload() == obj.deterministic_payload()

    def test_object_types_not_flattened(self) -> None:
        gateway = InMemoryPersistenceGateway()
        for object_type, cid in ALL_TYPES:
            gateway.create_object(_record(_obj(cid=cid, object_type=object_type)))
        ids = gateway.list_object_ids()
        assert len(ids) == 8
        for object_type, cid in ALL_TYPES:
            assert gateway.get_object(cid).object_type is object_type


# ---------------------------------------------------------------------------
# C — specialized contract storage
# ---------------------------------------------------------------------------


class TestSpecializedCards:
    def test_model_card_round_trip(self) -> None:
        from app.forge.schemas import ModelCard

        gateway = InMemoryPersistenceGateway()
        card = ModelCard(
            model_id="MOD.TEST.CARD.V1",
            name="Test model",
            version="v1",
            status=EvidenceStatus.CANDIDATE,
            market_scope=("EURUSD",),
            layer=Layer.L3,
            model_type="DISTRIBUTION",
            product_exposure=ProductExposure.SUBSCRIBER_MODEL,
            purpose="test",
            operator_interpretation="op",
            beginner_summary="b",
            operator_summary="o",
            researcher_summary="r",
        )
        obj = _obj(cid="MOD.TEST.CARD.V1", metadata={"card": card.model_dump(mode="json")})
        gateway.create_object(_record(obj))
        restored = gateway.get_object("MOD.TEST.CARD.V1").to_domain()
        rebuilt = ModelCard.model_validate(restored.metadata["card"])
        assert rebuilt == card

    def test_evidence_card_round_trip(self) -> None:
        from app.forge.schemas import EvidenceCard

        gateway = InMemoryPersistenceGateway()
        card = EvidenceCard(
            evidence_id="EV.TEST.CARD.V1",
            claim_id="CL.TEST.CARD.V1",
            title="Test evidence",
            status=EvidenceStatus.OBSERVED,
            evidence_type="RAW_BACKTEST",
            source_artifact="PDF",
            source_generation="g1",
            market="EURUSD",
            data_period="2020-2024",
            sample_n=100,
            exact_claim="claim",
            event_definition="e",
            conditioning_event="c",
            clock_origin="o",
            horizon="h",
            tolerance="t",
            eligibility_filter="f",
            metric="rate",
            result="0.5",
            calculation_type="count",
            implementation_name="impl",
            version_or_hash="v1",
            execution_semantics="s",
            data_granularity="M5",
            session_definition="LONDON",
            clock_mode="UTC",
            reproduction_status="NONE",
            interpretation="i",
            product_exposure=ProductExposure.RESEARCH_LAB,
        )
        obj = _obj(cid="EV.TEST.CARD.V1", object_type=ObjectType.EVIDENCE, metadata={"card": card.model_dump(mode="json")})
        gateway.create_object(_record(obj))
        restored = gateway.get_object("EV.TEST.CARD.V1").to_domain()
        rebuilt = EvidenceCard.model_validate(restored.metadata["card"])
        assert rebuilt == card

    def test_setup_operator_card_round_trip(self) -> None:
        from app.forge.schemas import SetupOperatorCard

        gateway = InMemoryPersistenceGateway()
        card = SetupOperatorCard(
            setup_id="SET.TEST.CARD.V1",
            name="Test setup",
            version="v1",
            status=EvidenceStatus.CANDIDATE,
            market_scope=("EURUSD",),
            execution_class="MANUAL_OPERATOR",
            parent_model_ids=("MOD.TEST.CARD.V1",),
            product_exposure=ProductExposure.OPERATOR_ONLY,
            purpose="p",
            eligibility=("e",),
            entry=("en",),
            invalidation=("in",),
            targets=("t",),
            no_go=("n",),
            l3_destination="l3",
            l2_path="l2",
            l1_execution="l1",
            failure_repair="f",
            manual_rule_source="m",
            automation_status="MANUAL",
            parity_status="NA",
            beginner_summary="b",
            operator_instructions="o",
            researcher_notes="r",
        )
        obj = _obj(cid="SET.TEST.CARD.V1", object_type=ObjectType.SETUP, metadata={"card": card.model_dump(mode="json")})
        gateway.create_object(_record(obj))
        restored = gateway.get_object("SET.TEST.CARD.V1").to_domain()
        rebuilt = SetupOperatorCard.model_validate(restored.metadata["card"])
        assert rebuilt == card

    def test_invalid_card_payload_rejected_at_boundary(self) -> None:
        from pydantic import ValidationError

        from app.forge.schemas import ModelCard

        with pytest.raises(ValidationError):
            ModelCard.model_validate({"model_id": "MOD.BAD", "name": "x"})


# ---------------------------------------------------------------------------
# D — claim identity
# ---------------------------------------------------------------------------


class TestClaimIdentity:
    def _claim(self, cid: str, result: str) -> CanonicalObjectRecord:
        identity = ClaimIdentity(
            market="EURUSD",
            event_definition="close outside band",
            conditioning_event="asian range break",
            clock_origin="06:00 UTC",
            horizon="D3",
            tolerance="0.1%",
            eligibility="T1 only",
            implementation_semantics="close-of-bar",
        )
        obj = _obj(
            cid=cid,
            object_type=ObjectType.CLAIM,
            metadata={"result": result},
        )
        record = _record(obj)
        # attach claim identity via dataclasses.replace-style construction
        return CanonicalObjectRecord(
            canonical_id=record.canonical_id,
            object_type=record.object_type,
            title=record.title,
            version=record.version,
            status=record.status,
            exposure=record.exposure,
            layer=record.layer,
            references=record.references,
            metadata=record.metadata,
            claim_identity=identity,
        )

    def test_claim_identity_round_trip(self) -> None:
        gateway = InMemoryPersistenceGateway()
        record = self._claim("CL.TEST.IDENTITY.V1", "0.62")
        gateway.create_object(record)
        restored = gateway.get_object("CL.TEST.IDENTITY.V1")
        assert restored.claim_identity == record.claim_identity

    def test_results_do_not_change_population_identity(self) -> None:
        gateway = InMemoryPersistenceGateway()
        record_a = self._claim("CL.TEST.POPA.V1", "0.62")
        record_b = self._claim("CL.TEST.POPB.V1", "0.99")
        gateway.create_object(record_a)
        gateway.create_object(record_b)
        # Population identity is the 8 dimensions; results differ only in metadata.
        assert record_a.claim_identity.comparison_key() == record_b.claim_identity.comparison_key()
        assert record_a.metadata["result"] != record_b.metadata["result"]


# ---------------------------------------------------------------------------
# E — artifacts & provenance
# ---------------------------------------------------------------------------


class TestArtifactAndProvenance:
    def test_artifact_round_trip(self) -> None:
        gateway = InMemoryPersistenceGateway()
        record = _artifact(source_state=SourceState.PARTIAL)
        gateway.create_artifact(record)
        restored = gateway.get_artifact(record.artifact_id)
        assert restored.source_state == "PARTIAL"
        assert restored.content_identity == record.content_identity
        domain = restored.to_domain()
        assert domain.materialization_state.value == "PARTIAL"

    def test_provenance_edge_round_trip_all_relations(self) -> None:
        gateway = InMemoryPersistenceGateway()
        obj = _obj(cid="MOD.TEST.EDGE.V1")
        gateway.create_object(_record(obj))
        relations = ["SUPPORTS", "DEFINES", "IMPLEMENTS", "VISUALIZES", "DERIVED_FROM", "SUPERSEDES"]
        for index, relation in enumerate(relations):
            aid = f"ART.MARKDOWN.ABCDEF0123456789ABCDEF{index}A"
            gateway.create_artifact(_artifact(aid=aid))
            gateway.add_provenance_edge(
                ProvenanceEdgeRecord(
                    artifact_id=aid,
                    object_id="MOD.TEST.EDGE.V1",
                    relation=relation,
                )
            )
        edges = gateway.edges_for_object("MOD.TEST.EDGE.V1")
        assert tuple(e.relation for e in edges) == tuple(relations)
        assert len(gateway.edges_from_artifact("ART.MARKDOWN.ABCDEF0123456789ABCDEF0A")) == 1

    def test_visual_support_remains_non_empirical_after_round_trip(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.VISUAL.V1")))
        gateway.create_artifact(
            _artifact(
                aid="ART.VISUAL.ABCDEF0123456789ABCDEFAB",
                source_class=ArtifactClass.VISUAL.value,
                source_state=SourceState.VERIFIED,
            )
        )
        gateway.add_provenance_edge(
            ProvenanceEdgeRecord(
                artifact_id="ART.VISUAL.ABCDEF0123456789ABCDEFAB",
                object_id="MOD.TEST.VISUAL.V1",
                relation="VISUALIZES",
            )
        )
        artifact = gateway.get_artifact("ART.VISUAL.ABCDEF0123456789ABCDEFAB").to_domain()
        assert classify_support([artifact]) is not None
        from app.forge.provenance import SupportClassification

        assert classify_support([artifact]) is SupportClassification.VISUAL_ONLY

    def test_conversation_derived_remains_non_empirical_after_round_trip(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_artifact(
            _artifact(
                aid="ART.CONVERSATIONDERIVED.ABCDEF0123456789ABCDE",
                source_class=ArtifactClass.CONVERSATION_DERIVED.value,
                source_state=SourceState.CONVERSATION_DERIVED,
                content_identity=None,
            )
        )
        artifact = gateway.get_artifact("ART.CONVERSATIONDERIVED.ABCDEF0123456789ABCDE").to_domain()
        from app.forge.provenance import SupportClassification

        assert classify_support([artifact]) is SupportClassification.CONVERSATION_DERIVED_ONLY


# ---------------------------------------------------------------------------
# F — integrity
# ---------------------------------------------------------------------------


class TestIntegrity:
    def test_duplicate_canonical_id_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.DUP.V1")))
        with pytest.raises(DuplicateCanonicalObject):
            gateway.create_object(_record(_obj(cid="MOD.TEST.DUP.V1")))

    def test_duplicate_artifact_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_artifact(_artifact())
        with pytest.raises(DuplicateArtifact):
            gateway.create_artifact(_artifact())

    def test_duplicate_provenance_edge_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.EDUP.V1")))
        gateway.create_artifact(_artifact())
        edge = ProvenanceEdgeRecord(
            artifact_id=_artifact().artifact_id, object_id="MOD.TEST.EDUP.V1", relation="SUPPORTS"
        )
        gateway.add_provenance_edge(edge)
        with pytest.raises(DuplicateProvenanceEdge):
            gateway.add_provenance_edge(edge)

    def test_self_reference_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        obj = _obj(
            cid="MOD.TEST.SELF.V1",
            references=(CanonicalReference(target_id="MOD.TEST.SELF.V1", relation="SUPPORTS"),),
        )
        with pytest.raises(SelfReferenceForbidden):
            gateway.create_object(_record(obj))

    def test_dangling_reference_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        obj = _obj(
            cid="MOD.TEST.DANGLE.V1",
            references=(CanonicalReference(target_id="MOD.TEST.MISSING.V1", relation="SUPPORTS"),),
        )
        with pytest.raises(DanglingReference):
            gateway.create_object(_record(obj))

    def test_unresolved_historical_reference_preserved(self) -> None:
        gateway = InMemoryPersistenceGateway()
        obj = _obj(
            cid="MOD.TEST.HIST.V1",
            status=EvidenceStatus.HISTORICAL,
            references=(
                CanonicalReference(
                    target_id="MOD.TEST.LOST.V1",
                    relation="ANCESTOR_OF",
                    allow_unresolved_historical=True,
                ),
            ),
        )
        gateway.create_object(_record(obj))
        restored = gateway.get_object("MOD.TEST.HIST.V1")
        assert restored.references[0].target_id == "MOD.TEST.LOST.V1"
        assert restored.references[0].allow_unresolved_historical is True


# ---------------------------------------------------------------------------
# G / I — writes, transactions, transitions
# ---------------------------------------------------------------------------


class TestWritesAndTransitions:
    def test_distinct_write_outcomes(self) -> None:
        gateway = InMemoryPersistenceGateway()
        created = gateway.create_object(_record(_obj(cid="MOD.TEST.WRITE.V1")))
        assert created.operation == "CREATE"
        transitioned = gateway.transition_status("MOD.TEST.WRITE.V1", "VALIDATED")
        assert transitioned.operation == "TRANSITION"
        with pytest.raises(DuplicateCanonicalObject):
            gateway.create_object(_record(_obj(cid="MOD.TEST.WRITE.V1")))
        with pytest.raises(ObjectNotFound):
            gateway.transition_status("MOD.TEST.MISSING.V1", "VALIDATED")

    def test_transaction_atomicity_rolls_back_failed_seed(self) -> None:
        gateway = InMemoryPersistenceGateway()
        good = _record(_obj(cid="MOD.TEST.TX.GOOD.V1"))
        bad = _record(
            _obj(
                cid="MOD.TEST.TX.BAD.V1",
                references=(CanonicalReference(target_id="MOD.TEST.MISSING.V1", relation="SUPPORTS"),),
            )
        )
        with pytest.raises(DanglingReference):
            with gateway.transaction():
                gateway.create_object(good)
                gateway.create_object(bad)
        # Nothing committed: the good object must not exist.
        assert gateway.get_object("MOD.TEST.TX.GOOD.V1") is None

    # -----------------------------------------------------------------------
    # I.3 repairs — mutual references in one batch + in-batch duplicate ids
    # -----------------------------------------------------------------------

    def test_mutual_references_commit_as_one_unit(self) -> None:
        """Repair A: CLAIM <-> EVIDENCE that reference each other inside one
        transaction commit together; unresolved ordinary references after
        commit remain forbidden."""
        gateway = InMemoryPersistenceGateway()
        claim = _record(
            _obj(
                cid="CL.TEST.MUTUAL.V1",
                object_type=ObjectType.CLAIM,
                references=(
                    CanonicalReference(
                        target_id="EV.TEST.MUTUAL.V1", relation="supported_by"
                    ),
                ),
            )
        )
        evidence = _record(
            _obj(
                cid="EV.TEST.MUTUAL.V1",
                object_type=ObjectType.EVIDENCE,
                references=(
                    CanonicalReference(
                        target_id="CL.TEST.MUTUAL.V1", relation="evidence_for"
                    ),
                ),
            )
        )
        with gateway.transaction():
            gateway.create_object(claim)
            gateway.create_object(evidence)

        restored_claim = gateway.get_object("CL.TEST.MUTUAL.V1")
        restored_evidence = gateway.get_object("EV.TEST.MUTUAL.V1")
        assert restored_claim is not None and restored_evidence is not None
        # After commit every ordinary reference resolves against the store:
        # batch-internal resolution never permits post-commit dangling truth.
        for record in (restored_claim, restored_evidence):
            for ref in record.references:
                assert ref.allow_unresolved_historical is False
                assert ref.target_id in gateway.list_object_ids()

        # A lone record whose ordinary reference target never arrives is
        # still rejected (batch-internal resolution is not a blanket pass).
        lone = _record(
            _obj(
                cid="CL.TEST.LONE.V1",
                object_type=ObjectType.CLAIM,
                references=(
                    CanonicalReference(
                        target_id="EV.TEST.ABSENT.V1", relation="supported_by"
                    ),
                ),
            )
        )
        with pytest.raises(DanglingReference):
            with gateway.transaction():
                gateway.create_object(lone)
        assert gateway.get_object("CL.TEST.LONE.V1") is None

    def test_duplicate_canonical_id_within_one_batch_rejected(self) -> None:
        """Repair B: two pending records with the same canonical id are
        rejected even when neither exists in the committed store — the second
        record must never silently overwrite the first."""
        gateway = InMemoryPersistenceGateway()
        first = _record(_obj(cid="MOD.TEST.BATCHDUP.V1", metadata={"who": "first"}))
        second = _record(_obj(cid="MOD.TEST.BATCHDUP.V1", metadata={"who": "second"}))
        with pytest.raises(DuplicateCanonicalObject):
            with gateway.transaction():
                gateway.create_object(first)
                gateway.create_object(second)
        # Atomic: neither duplicate committed and no partial batch truth.
        assert gateway.get_object("MOD.TEST.BATCHDUP.V1") is None

    def test_failed_batch_does_not_leak_artifacts_or_edges(self) -> None:
        """A failed logical batch must not leave ANY partial truth: objects,
        artifacts and provenance edges all roll back together (parity with
        the SQL gateway's single rolled-back DB transaction)."""
        gateway = InMemoryPersistenceGateway()
        artifact = _artifact(aid="ART.MARKDOWN.CCBBF0123456789ABCDEFAB")
        obj = _record(_obj(cid="MOD.TEST.LEAK.V1"))
        bad = _record(
            _obj(
                cid="MOD.TEST.LEAKBAD.V1",
                references=(
                    CanonicalReference(
                        target_id="MOD.TEST.GONE.V1", relation="SUPPORTS"
                    ),
                ),
            )
        )
        with pytest.raises(DanglingReference):
            with gateway.transaction():
                gateway.create_artifact(artifact)
                gateway.create_object(obj)
                gateway.add_provenance_edge(
                    ProvenanceEdgeRecord(
                        artifact_id=artifact.artifact_id,
                        object_id=obj.canonical_id,
                        relation="DEFINES",
                        note="leak probe",
                    )
                )
                gateway.create_object(bad)
        assert gateway.list_object_ids() == ()
        assert gateway.get_artifact(artifact.artifact_id) is None
        assert gateway.edges_for_object(obj.canonical_id) == ()

    def test_legal_transition_persists(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.LEGAL.V1", status=EvidenceStatus.OBSERVED)))
        result = gateway.transition_status("MOD.TEST.LEGAL.V1", "CANDIDATE")
        assert result.operation == "TRANSITION"
        assert gateway.get_object("MOD.TEST.LEGAL.V1").status is EvidenceStatus.CANDIDATE

    def test_illegal_transition_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.ILLEGAL.V1", status=EvidenceStatus.OBSERVED)))
        with pytest.raises(IllegalStatusTransition):
            gateway.transition_status("MOD.TEST.ILLEGAL.V1", "VALIDATED")

    def test_terminal_transition_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.TERMINAL.V1", status=EvidenceStatus.VALIDATED)))
        gateway.transition_status("MOD.TEST.TERMINAL.V1", "FALSIFIED")
        with pytest.raises(IllegalStatusTransition):
            gateway.transition_status("MOD.TEST.TERMINAL.V1", "CANDIDATE")


# ---------------------------------------------------------------------------
# N — concurrency
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_stale_object_write_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.STALE.V1", status=EvidenceStatus.OBSERVED)))
        version = gateway.object_version("MOD.TEST.STALE.V1")
        # Simulate a competing writer.
        gateway.transition_status("MOD.TEST.STALE.V1", "CANDIDATE")
        with pytest.raises(StaleWriteConflict):
            gateway.transition_status("MOD.TEST.STALE.V1", "VALIDATED", expected_version=version)

    def test_current_version_write_succeeds(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_record(_obj(cid="MOD.TEST.CURRENT.V1", status=EvidenceStatus.OBSERVED)))
        version = gateway.object_version("MOD.TEST.CURRENT.V1")
        result = gateway.transition_status(
            "MOD.TEST.CURRENT.V1", "CANDIDATE", expected_version=version
        )
        assert result.persisted_version == version + 1

    def test_stale_artifact_write_rejected(self) -> None:
        gateway = InMemoryPersistenceGateway()
        aid = _artifact().artifact_id
        gateway.create_artifact(_artifact())
        version = gateway.artifact_version(aid)
        # Competing writer advances the artifact state first.
        gateway.transition_artifact_state(aid, "MATERIALIZED")
        with pytest.raises(StaleWriteConflict):
            gateway.transition_artifact_state(aid, "MISSING", expected_version=version)


# ---------------------------------------------------------------------------
# K / L — startup & readiness
# ---------------------------------------------------------------------------


def _probe_app(persistence):
    from fastapi import FastAPI

    from app.forge.service.container import ForgeServiceContainer
    from app.forge.service.lifecycle import ForgeLifecycle
    from app.forge.service.routes import create_forge_router

    config = ForgeConfig(environment="test")
    container = ForgeServiceContainer(config=config, persistence=persistence)
    probe = FastAPI()
    probe.include_router(create_forge_router(config=config, container=container))
    lifecycle = ForgeLifecycle(container)
    probe.router.on_startup.append(lifecycle.startup)
    probe.router.on_shutdown.append(lifecycle.shutdown)
    return probe, container


class TestStartupAndReadiness:
    def test_persistence_disabled_boots_and_readiness_honest(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        ready = client.get("/forge/v1/ready").json()
        pg = ready["dependencies"]["postgresql"]
        assert pg["status"] == "NOT_CONFIGURED"
        assert pg["required"] is False
        assert ready["status"] == "ready"

    def test_persistence_enabled_healthy_ready_required(self) -> None:
        pytest.importorskip("sqlalchemy")
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
        probe, _container = _probe_app(SqlAlchemyPersistenceGateway(engine.connect()))
        with TestClient(probe) as client:
            ready = client.get("/forge/v1/ready").json()
            pg = ready["dependencies"]["postgresql"]
            assert pg["status"] == "READY"
            assert pg["required"] is True
            assert ready["status"] == "ready"

    def test_persistence_enabled_unavailable_not_ready(self) -> None:
        from fastapi.testclient import TestClient

        probe, _container = _probe_app(
            InMemoryPersistenceGateway(simulate_unavailable=True)
        )
        with TestClient(probe) as client:
            ready = client.get("/forge/v1/ready").json()
            pg = ready["dependencies"]["postgresql"]
            assert pg["status"] != "READY"
            assert pg["required"] is True
            assert ready["status"] == "not_ready"

    def test_readiness_leaks_no_credentials(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        text = client.get("/forge/v1/ready").text + client.get("/forge/v1/meta").text
        assert "FORGE_DATABASE_URL" not in text
        assert "postgres://" not in text
        assert "sqlite" not in text


# ---------------------------------------------------------------------------
# J — migrations (SQL contract on SQLite)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not SQLA_AVAILABLE, reason="SQLAlchemy not installed")
class TestMigrations:
    def _fresh(self):
        from sqlalchemy import create_engine

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        return SqlAlchemyPersistenceGateway(engine.connect())

    def test_apply_then_noop(self) -> None:
        gateway = self._fresh()
        assert gateway.apply_migrations() == "APPLIED"
        assert gateway.check_compatibility() == "OK"
        assert gateway.apply_migrations() == "CURRENT"

    def test_incompatible_empty_schema(self) -> None:
        gateway = self._fresh()
        # Without applying migrations the schema is behind/incompatible.
        assert gateway.check_compatibility() in {"BEHIND", "INCOMPATIBLE"}

    def test_migration_runner_not_invoked_by_import(self) -> None:
        # Importing anything FORGE must not run migrations: the composition
        # root with persistence disabled is the proof.
        import app.main  # noqa: F401

        from app.main import _build_forge_container

        assert _build_forge_container().persistence is None


# ---------------------------------------------------------------------------
# P — security
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not SQLA_AVAILABLE, reason="SQLAlchemy not installed")
class TestSqlClaimIdentityRoundtrip:
    """Regression: a CLAIM's ClaimIdentity must survive the SQL gateway
    (the old serializer silently stored {} and the read path crashed on
    reconstruction — proven by the I.3 corpus apply on PostgreSQL)."""

    def _fresh(self):
        from sqlalchemy import create_engine

        from app.forge.persistence.sql.gateway import SqlAlchemyPersistenceGateway

        engine = create_engine("sqlite://")
        gw = SqlAlchemyPersistenceGateway(engine.connect())
        gw.apply_migrations()
        return gw

    def test_claim_identity_survives_sql_roundtrip(self) -> None:
        from app.forge.canonical import ClaimIdentity

        identity = ClaimIdentity(
            market="EURUSD",
            event_definition="D3 state at quarter close",
            conditioning_event="session=London",
            clock_origin="exchange_rth_open",
            horizon="M3",
            tolerance="+-1 bar",
            eligibility="liquid sessions only",
            implementation_semantics="bar-close confirm",
        )
        record = CanonicalObjectRecord(
            canonical_id="CL.SQL.IDENTITY.V1",
            object_type=ObjectType.CLAIM,
            title="identity roundtrip",
            version="V1",
            status=EvidenceStatus.CANDIDATE,
            exposure=ProductExposure.SUBSCRIBER_MODEL,
            layer=Layer.NONE,
            references=(),
            metadata={"who": "sql-roundtrip"},
            claim_identity=identity,
        )
        gw = self._fresh()
        gw.create_object(record)
        restored = gw.get_object("CL.SQL.IDENTITY.V1")
        assert restored is not None
        assert restored.claim_identity is not None
        assert restored.claim_identity == identity
        assert restored.claim_identity.comparison_key() == identity.comparison_key()
        assert restored.metadata == {"who": "sql-roundtrip"}

    def test_missing_identity_is_absent_not_crash(self) -> None:
        # A claim row without persisted identity reads back as None instead
        # of raising (read path never crashes, never fabricates dimensions).
        gw = self._fresh()
        record = CanonicalObjectRecord(
            canonical_id="CL.SQL.NOIDENT.V1",
            object_type=ObjectType.CLAIM,
            title="no identity",
            version="V1",
            status=EvidenceStatus.CANDIDATE,
            exposure=ProductExposure.SUBSCRIBER_MODEL,
            layer=Layer.NONE,
            references=(),
            metadata={},
            claim_identity=None,
        )
        gw.create_object(record)
        restored = gw.get_object("CL.SQL.NOIDENT.V1")
        assert restored is not None
        assert restored.claim_identity is None


class TestSecurity:
    def test_no_public_data_routes(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        routes = {getattr(route, "path", "") for route in app.routes}
        forge_routes = {p for p in routes if str(p).startswith("/forge/")}
        assert forge_routes == {"/forge/v1/health", "/forge/v1/ready", "/forge/v1/meta"}
        # A few representative forbidden routes must not exist.
        for forbidden in ("/forge/v1/objects", "/forge/v1/artifacts", "/forge/v1/sql", "/forge/v1/corpus"):
            assert forbidden not in routes
            assert client.get(forbidden).status_code == 404

    def test_meta_does_not_leak_db_url(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        meta = client.get("/forge/v1/meta").text
        assert "sqlite" not in meta
        assert "postgres" not in meta

    def test_db_error_response_leaks_nothing(self) -> None:
        gateway = InMemoryPersistenceGateway(simulate_unavailable=True)
        with pytest.raises(PersistenceUnavailable) as excinfo:
            gateway.ping()
        # Redacted detail carries only the kind, never a URL/credential.
        assert "postgres" not in str(excinfo.value)
        assert "sqlite" not in str(excinfo.value)
        assert "://" not in str(excinfo.value)


# ---------------------------------------------------------------------------
# O — determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_content_hash_survives_round_trip_with_db_timestamps(self) -> None:
        # DB timestamps are persistence-owned; the record/domain conversion
        # never includes them, so hashes are stable.
        gateway = InMemoryPersistenceGateway()
        obj = _obj(cid="MOD.TEST.DET.V1")
        gateway.create_object(_record(obj))
        restored = gateway.get_object("MOD.TEST.DET.V1").to_domain()
        assert restored.content_hash() == obj.content_hash()
        assert "created_at" not in restored.deterministic_payload()
