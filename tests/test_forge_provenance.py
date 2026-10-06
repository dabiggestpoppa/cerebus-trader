import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalReference,
    CanonicalRegistry,
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
)
from app.forge.provenance import (
    DEFAULT_ARTIFACT_CLASSES,
    Artifact,
    ArtifactClassRegistry,
    ArtifactRegistry,
    ClaimChainStatus,
    MaterializationState,
    ProvenanceEdge,
    ProvenanceRelation,
    ProvenanceRegistry,
    SourceState,
    SupportClassification,
    compute_content_identity,
    derive_artifact_id,
    is_numerical_claim,
    validate_source_state_transition,
)

# Fixtures reuse the current canonical claim/evidence identities from
# corpus/canonical/CLAIM_REGISTRY_V1.md.
CLAIM_ID = "CL.EUR.HO.D3_DIRECTION"
EVIDENCE_ID = "EV.EUR.HO.D3_DIRECTION.V1"
MODEL_ID = "MOD.EUR.HIGHER_ORDER.V1"


def canon(cid, status=EvidenceStatus.CANDIDATE, refs=(), metadata=None, layer=Layer.L3):
    return CanonicalObject(
        canonical_id=CanonicalId.parse(cid),
        title="fixture object",
        version="1",
        status=status,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=layer,
        references=refs,
        metadata=metadata or {},
    )


def base_registry() -> CanonicalRegistry:
    return CanonicalRegistry(
        [
            canon(
                CLAIM_ID,
                status=EvidenceStatus.FORWARD_OOS,
                refs=(CanonicalReference(target_id=EVIDENCE_ID, relation="SUPPORTED_BY"),),
                metadata={"numerical": True, "result": "69.5% (41/59)"},
            ),
            canon(EVIDENCE_ID, status=EvidenceStatus.FORWARD_OOS),
        ]
    )


def artifact(
    aid="ART.PDF.EUR_HO_REVIEW.V1",
    cls="PDF",
    state=SourceState.VERIFIED,
    content=b"pdf-bytes",
    locator="corpus/papers/eur_ho_review.pdf",
):
    return Artifact(
        artifact_id=aid,
        source_class=cls,
        source_state=state,
        content_identity=None if content is None else compute_content_identity(content),
        locator=locator,
    )


# ---------------------------------------------------------------------------
# 1. Valid artifact identities / types (I.2.1)
# ---------------------------------------------------------------------------


def test_all_default_artifact_classes_register_with_typed_ids():
    registry = ArtifactRegistry()
    for cls in DEFAULT_ARTIFACT_CLASSES:
        art = Artifact(artifact_id=f"ART.{cls}.SAMPLE.V1", source_class=cls)
        registry.add(art)
        assert CanonicalId.parse(art.artifact_id).object_type is ObjectType.ARTIFACT
    assert len(registry) == len(DEFAULT_ARTIFACT_CLASSES)


def test_artifact_registry_is_extensible_and_frozen_defaults_protected():
    classes = ArtifactClassRegistry()
    defaults = set(classes.members())
    classes.register("WHITEPAPER")
    assert "WHITEPAPER" in classes
    with pytest.raises(ValueError, match="duplicate artifact class"):
        classes.register("WHITEPAPER")
    with pytest.raises(ValueError, match="duplicate artifact class"):
        classes.register("PDF")  # frozen default cannot be overwritten
    with pytest.raises(ValueError, match="invalid artifact class name"):
        classes.register("pdf")
    assert defaults <= set(classes.members())
    registry = ArtifactRegistry(classes=classes)
    assert not hasattr(registry, "remove")
    assert not hasattr(registry.classes, "remove")


def test_registered_class_usable_and_unregistered_class_rejected():
    registry = ArtifactRegistry()
    registry.register_class("WHITEPAPER")
    registry.add(Artifact(artifact_id="ART.WHITEPAPER.NOTES.V1", source_class="WHITEPAPER"))
    with pytest.raises(ValueError, match="unknown artifact class"):
        registry.add(Artifact(artifact_id="ART.PAMPHLET.X.V1", source_class="PAMPHLET"))
    with pytest.raises(ValidationError):
        Artifact(artifact_id="PDF.NO_PREFIX.V1", source_class="PDF")


# ---------------------------------------------------------------------------
# 2. Deterministic content identity (I.2.2)
# ---------------------------------------------------------------------------


def test_content_identity_and_derived_ids_are_deterministic():
    first = compute_content_identity(b"same bytes")
    second = compute_content_identity(b"same bytes")
    other = compute_content_identity(b"other bytes")
    assert first == second
    assert first != other
    assert first.startswith("sha256:") and len(first) == 71
    assert derive_artifact_id("PDF", first) == derive_artifact_id("PDF", second)
    assert derive_artifact_id("PDF", first) != derive_artifact_id("CSV", first)
    art = Artifact(
        artifact_id=derive_artifact_id("PDF", first),
        source_class="PDF",
        content_identity=first,
        locator="corpus/papers/x.pdf",
    )
    assert art.materialization_state is MaterializationState.MATERIALIZED


def test_materialization_state_derived_from_content_and_source_state():
    assert artifact(content=None).materialization_state is MaterializationState.NOT_MATERIALIZED
    partial = artifact(state=SourceState.PARTIAL, content=b"partial")
    assert partial.materialization_state is MaterializationState.PARTIAL


# ---------------------------------------------------------------------------
# 3. Duplicate artifact identity rejection (I.2.2)
# ---------------------------------------------------------------------------


def test_duplicate_artifact_identity_rejected():
    registry = ArtifactRegistry()
    registry.add(artifact())
    with pytest.raises(ValueError, match="duplicate artifact id"):
        registry.add(artifact())
    with pytest.raises(ValueError, match="duplicate artifact content identity"):
        registry.add(artifact(aid="ART.PDF.OTHER_COPY.V1"))
    # identical bytes at a different locator are a distinct materialization
    registry.add(artifact(aid="ART.PDF.ELSEWHERE.V1", locator="archive/eur_ho_review.pdf"))
    assert len(registry) == 2


# ---------------------------------------------------------------------------
# 4/5. Valid and invalid provenance edges (I.2.3)
# ---------------------------------------------------------------------------


def test_valid_provenance_edges_accepted_for_all_relations():
    prov = ProvenanceRegistry(base_registry())
    prov.add_artifact(artifact())
    for relation in ProvenanceRelation:
        prov.add_edge(
            ProvenanceEdge(
                artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
                object_id=EVIDENCE_ID,
                relation=relation,
            )
        )
    assert len(prov.edges()) == len(ProvenanceRelation)
    assert len(prov.edges_for_object(EVIDENCE_ID)) == len(ProvenanceRelation)
    assert len(prov.edges_from_artifact("ART.PDF.EUR_HO_REVIEW.V1")) == len(
        ProvenanceRelation
    )


def test_invalid_provenance_edges_rejected():
    prov = ProvenanceRegistry(base_registry())
    prov.add_artifact(artifact())
    with pytest.raises(ValidationError):
        ProvenanceEdge(
            artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
            object_id=EVIDENCE_ID,
            relation="PROVES",
        )
    with pytest.raises(ValidationError, match="ARTIFACT id"):
        ProvenanceEdge(
            artifact_id=MODEL_ID, object_id=EVIDENCE_ID, relation=ProvenanceRelation.SUPPORTS
        )
    with pytest.raises(ValueError, match="unknown provenance artifact"):
        prov.add_edge(
            ProvenanceEdge(
                artifact_id="ART.PDF.NOT_REGISTERED.V1",
                object_id=EVIDENCE_ID,
                relation=ProvenanceRelation.SUPPORTS,
            )
        )
    with pytest.raises(ValueError, match="unknown canonical object"):
        prov.add_edge(
            ProvenanceEdge(
                artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
                object_id="MOD.NOT.REGISTERED.V1",
                relation=ProvenanceRelation.SUPPORTS,
            )
        )
    edge = ProvenanceEdge(
        artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
        object_id=EVIDENCE_ID,
        relation=ProvenanceRelation.SUPPORTS,
    )
    prov.add_edge(edge)
    with pytest.raises(ValueError, match="duplicate provenance edge"):
        prov.add_edge(edge)


def test_claim_source_chain_requires_a_claim():
    prov = ProvenanceRegistry(base_registry())
    with pytest.raises(ValueError, match="not a claim"):
        prov.claim_source_chain(EVIDENCE_ID)


# ---------------------------------------------------------------------------
# 6. Source-state validation / lifecycle (I.2.5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "current,target",
    [
        (SourceState.LOCATED, SourceState.READ),
        (SourceState.READ, SourceState.VERIFIED),
        (SourceState.VERIFIED, SourceState.MATERIALIZED),
        (SourceState.MATERIALIZED, SourceState.VERIFIED),
        (SourceState.MISSING, SourceState.LOCATED),
        (SourceState.PARTIAL, SourceState.READ),
        (SourceState.LOCATED, SourceState.PARTIAL),
        (SourceState.CONVERSATION_DERIVED, SourceState.LOCATED),
        (SourceState.READ, SourceState.READ),
    ],
)
def test_legal_source_state_transitions(current, target):
    validate_source_state_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        (SourceState.MISSING, SourceState.VERIFIED),
        (SourceState.CONVERSATION_DERIVED, SourceState.VERIFIED),
        (SourceState.MATERIALIZED, SourceState.LOCATED),
        (SourceState.LOCATED, SourceState.CONVERSATION_DERIVED),
        (SourceState.MISSING, SourceState.READ),
    ],
)
def test_illegal_source_state_transitions(current, target):
    with pytest.raises(ValueError, match="illegal source state transition"):
        validate_source_state_transition(current, target)


def test_unknown_source_state_value_rejected():
    with pytest.raises(ValidationError):
        Artifact(
            artifact_id="ART.PDF.PRESUMED.V1", source_class="PDF", source_state="PRESUMED"
        )


def test_registry_applies_source_state_lifecycle():
    registry = ArtifactRegistry()
    registry.add(artifact(aid="ART.PDF.LIFECYCLE.V1", state=SourceState.LOCATED, content=None))
    updated = registry.set_source_state("ART.PDF.LIFECYCLE.V1", SourceState.READ)
    assert updated.source_state is SourceState.READ
    again = registry.set_source_state("ART.PDF.LIFECYCLE.V1", SourceState.READ)
    assert again.source_state is SourceState.READ
    with pytest.raises(ValueError, match="illegal source state transition"):
        registry.set_source_state("ART.PDF.LIFECYCLE.V1", SourceState.CONVERSATION_DERIVED)


# ---------------------------------------------------------------------------
# 7. Visual cannot be independent empirical proof (I.2.4)
# ---------------------------------------------------------------------------


def test_visual_support_never_counts_as_independent_empirical_proof():
    registry = base_registry()
    prov = ProvenanceRegistry(registry)
    prov.add_artifact(
        artifact(
            aid="ART.VISUAL.XAU_INFOGRAPHIC.V1",
            cls="VISUAL",
            state=SourceState.VERIFIED,
            content=b"<svg>69.5%</svg>",
            locator="corpus/results/xau_promo.png",
        )
    )
    prov.add_edge(
        ProvenanceEdge(
            artifact_id="ART.VISUAL.XAU_INFOGRAPHIC.V1",
            object_id=EVIDENCE_ID,
            relation=ProvenanceRelation.SUPPORTS,
        )
    )
    assert prov.support_classification(EVIDENCE_ID) is SupportClassification.VISUAL_ONLY
    assert prov.independent_empirical_support(EVIDENCE_ID) is False
    status, classification = prov.claim_source_chain(CLAIM_ID)
    assert status is ClaimChainStatus.NON_EMPIRICAL_SOURCE
    assert classification is SupportClassification.VISUAL_ONLY
    report = prov.audit()
    assert f"{CLAIM_ID}:VISUAL_ONLY" in report.numerical_claims_non_empirical_source
    assert EVIDENCE_ID in report.visual_only_support
    assert any(
        gap["kind"] == "LAUNCH_NUMERICAL_CLAIM_WITH_NON_EMPIRICAL_SOURCE"
        and gap["target"] == CLAIM_ID
        for gap in report.gaps
    )


# ---------------------------------------------------------------------------
# 8. Conversation-derived restrictions (I.2.5)
# ---------------------------------------------------------------------------


def test_conversation_derived_source_is_not_empirical_and_never_verifies_directly():
    prov = ProvenanceRegistry(base_registry())
    prov.add_artifact(
        artifact(
            aid="ART.CONVERSATION_DERIVED.RESEARCH_CHAT.V1",
            cls="CONVERSATION_DERIVED",
            state=SourceState.CONVERSATION_DERIVED,
            content=b"operator conversation memo",
            locator="corpus/conversation-derived/research_chat.md",
        )
    )
    prov.add_edge(
        ProvenanceEdge(
            artifact_id="ART.CONVERSATION_DERIVED.RESEARCH_CHAT.V1",
            object_id=EVIDENCE_ID,
            relation=ProvenanceRelation.SUPPORTS,
        )
    )
    assert (
        prov.support_classification(EVIDENCE_ID)
        is SupportClassification.CONVERSATION_DERIVED_ONLY
    )
    assert prov.independent_empirical_support(EVIDENCE_ID) is False
    status, _ = prov.claim_source_chain(CLAIM_ID)
    assert status is ClaimChainStatus.NON_EMPIRICAL_SOURCE
    report = prov.audit()
    assert "ART.CONVERSATION_DERIVED.RESEARCH_CHAT.V1" in report.conversation_derived_sources
    # report lists canonical objects whose support is conversation-derived only
    assert EVIDENCE_ID in report.conversation_derived_support
    assert any(
        gap["kind"] == "LAUNCH_NUMERICAL_CLAIM_WITH_NON_EMPIRICAL_SOURCE"
        and gap["target"] == CLAIM_ID
        for gap in report.gaps
    )
    with pytest.raises(ValueError, match="illegal source state transition"):
        validate_source_state_transition(
            SourceState.CONVERSATION_DERIVED, SourceState.VERIFIED
        )


# ---------------------------------------------------------------------------
# 9/10. Missing and partial source states (I.2.5)
# ---------------------------------------------------------------------------


def test_missing_source_state_is_explicit_and_never_fabricated():
    registry = base_registry()
    prov = ProvenanceRegistry(registry)
    prov.add_artifact(
        artifact(
            aid="ART.PDF.ORIGINAL_STUDY.V1",
            state=SourceState.MISSING,
            content=None,
            locator="corpus/manuals/original_study.pdf",
        )
    )
    assert prov.artifacts.get("ART.PDF.ORIGINAL_STUDY.V1").content_identity is None
    report = prov.audit()
    assert {"artifact_id": "ART.PDF.ORIGINAL_STUDY.V1", "source_state": "MISSING"} in (
        report.unresolved_sources
    )
    assert report.artifacts_by_source_state["MISSING"] == 1
    assert any(
        gap["kind"] == "MISSING_SOURCE" and gap["target"] == "ART.PDF.ORIGINAL_STUDY.V1"
        for gap in report.gaps
    )
    # a search miss is not proof of absence: later rediscovery is legal
    recovered = prov.artifacts.set_source_state(
        "ART.PDF.ORIGINAL_STUDY.V1", SourceState.LOCATED
    )
    assert recovered.source_state is SourceState.LOCATED


def test_missing_source_cannot_carry_content_identity():
    with pytest.raises(ValidationError, match="MISSING"):
        Artifact(
            artifact_id="ART.PDF.FABRICATED.V1",
            source_class="PDF",
            source_state=SourceState.MISSING,
            content_identity=compute_content_identity(b"not actually found"),
        )
    registry = ArtifactRegistry()
    registry.add(artifact(aid="ART.PDF.HAS_CONTENT.V1", state=SourceState.LOCATED))
    with pytest.raises(ValueError, match="MISSING"):
        registry.set_source_state("ART.PDF.HAS_CONTENT.V1", SourceState.MISSING)


def test_partial_source_state_reported_explicitly():
    prov = ProvenanceRegistry(base_registry())
    prov.add_artifact(
        artifact(
            aid="ART.XLSX.WORKBOOK_FRAGMENT.V1",
            cls="XLSX",
            state=SourceState.PARTIAL,
            content=b"partial workbook bytes",
            locator="corpus/workbooks/frag.xlsx",
        )
    )
    report = prov.audit()
    assert "ART.XLSX.WORKBOOK_FRAGMENT.V1" in report.partial_sources
    assert {"artifact_id": "ART.XLSX.WORKBOOK_FRAGMENT.V1", "source_state": "PARTIAL"} in (
        report.unresolved_sources
    )
    assert any(
        gap["kind"] == "PARTIAL_SOURCE"
        and gap["target"] == "ART.XLSX.WORKBOOK_FRAGMENT.V1"
        for gap in report.gaps
    )


# ---------------------------------------------------------------------------
# 11/12. Orphan and coverage reporting (I.2.6)
# ---------------------------------------------------------------------------


def test_orphan_canonical_object_and_coverage_report():
    registry = CanonicalRegistry(
        [
            canon(
                CLAIM_ID,
                status=EvidenceStatus.FORWARD_OOS,
                refs=(CanonicalReference(target_id=EVIDENCE_ID, relation="SUPPORTED_BY"),),
                metadata={"numerical": True, "result": "69.5%"},
            ),
            canon(EVIDENCE_ID, status=EvidenceStatus.FORWARD_OOS),
            canon("TERM.AU.DEFINITION.V1", layer=Layer.NONE),
        ]
    )
    prov = ProvenanceRegistry(registry)
    prov.add_artifact(artifact())
    prov.add_edge(
        ProvenanceEdge(
            artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
            object_id=EVIDENCE_ID,
            relation=ProvenanceRelation.SUPPORTS,
        )
    )
    report = prov.audit()
    # claim routes to evidence, which has a source: not an orphan
    assert report.orphan_objects == ("TERM.AU.DEFINITION.V1",)
    assert report.source_coverage == {
        "objects_total": 3,
        "objects_with_source": 2,
        "objects_without_source": 1,
        "objects_with_empirical_source": 2,
    }
    assert report.evidence_without_source == ()


def test_evidence_without_source_reported():
    prov = ProvenanceRegistry(base_registry())
    report = prov.audit()
    assert report.evidence_without_source == (EVIDENCE_ID,)
    assert any(
        gap["kind"] == "EVIDENCE_WITHOUT_SOURCE" and gap["target"] == EVIDENCE_ID
        for gap in report.gaps
    )


# ---------------------------------------------------------------------------
# 13. Launch numerical claim without provenance is a GAP (I.2.6)
# ---------------------------------------------------------------------------


def test_launch_numerical_claim_without_provenance_is_a_gap():
    prov = ProvenanceRegistry(base_registry())
    report = prov.audit()
    assert report.launch_numerical_claims_without_source_chain == (CLAIM_ID,)
    assert any(
        gap["kind"] == "LAUNCH_NUMERICAL_CLAIM_WITHOUT_SOURCE_CHAIN"
        and gap["target"] == CLAIM_ID
        for gap in report.gaps
    )
    status, _ = prov.claim_source_chain(CLAIM_ID)
    assert status is ClaimChainStatus.EVIDENCE_WITHOUT_SOURCE


def test_claim_without_evidence_reference_is_a_gap():
    registry = CanonicalRegistry(
        [canon("CL.EUR.ORPHAN.NUMERIC.V1", metadata={"numerical": True, "result": "80%"})]
    )
    prov = ProvenanceRegistry(registry)
    status, _ = prov.claim_source_chain("CL.EUR.ORPHAN.NUMERIC.V1")
    assert status is ClaimChainStatus.NO_EVIDENCE_REFERENCE
    report = prov.audit()
    assert "CL.EUR.ORPHAN.NUMERIC.V1" in (
        report.launch_numerical_claims_without_source_chain
    )


def test_non_numerical_claim_is_not_treated_as_launch_numerical_claim():
    registry = CanonicalRegistry([canon("CL.EUR.QUALITATIVE.V1")])
    qualitative_claim = registry.get("CL.EUR.QUALITATIVE.V1")
    assert is_numerical_claim(qualitative_claim) is False
    # non-claim objects are never treated as numerical claims
    assert is_numerical_claim(canon(EVIDENCE_ID)) is False
    report = ProvenanceRegistry(registry).audit()
    assert report.launch_numerical_claims_without_source_chain == ()
    assert report.gaps == ()


# ---------------------------------------------------------------------------
# 14. Historical unresolved sources stay explicit (I.2.5 / I.2.6)
# ---------------------------------------------------------------------------


def test_historical_unresolved_source_stays_explicit_rather_than_fabricated():
    registry = CanonicalRegistry(
        [
            canon(
                "MOD.LEGACY.BASE80.V1",
                status=EvidenceStatus.HISTORICAL,
                refs=(
                    CanonicalReference(
                        target_id="ART.LEGACY.WORKBOOK.V1",
                        relation="SOURCE",
                        allow_unresolved_historical=True,
                    ),
                ),
            )
        ]
    )
    prov = ProvenanceRegistry(registry)
    prov.add_artifact(
        artifact(
            aid="ART.PDF.PARTIAL_SCAN.V1",
            state=SourceState.MISSING,
            content=None,
            locator="corpus/manuals/legacy_workbook_scan.pdf",
        )
    )
    report = prov.audit()
    assert any(
        "MOD.LEGACY.BASE80.V1" in text
        and "ART.LEGACY.WORKBOOK.V1" in text
        for text in report.historical_unresolved_references
    )
    assert any(
        gap["kind"] == "UNRESOLVED_HISTORICAL_REFERENCE"
        and gap["target"] == "MOD.LEGACY.BASE80.V1"
        for gap in report.gaps
    )
    assert {"artifact_id": "ART.PDF.PARTIAL_SCAN.V1", "source_state": "MISSING"} in (
        report.unresolved_sources
    )
    # nothing was invented: the unresolved artifact still has no content identity
    assert prov.artifacts.get("ART.PDF.PARTIAL_SCAN.V1").content_identity is None
    assert report.artifact_count == 1


# ---------------------------------------------------------------------------
# 15. Provenance edge cannot promote canonical/evidence status
# ---------------------------------------------------------------------------


def test_provenance_edge_never_promotes_canonical_status():
    registry = base_registry()
    registry.add(canon(MODEL_ID, status=EvidenceStatus.CANDIDATE, layer=Layer.L3))
    before = registry.get(MODEL_ID).content_hash()
    prov = ProvenanceRegistry(registry)
    prov.add_artifact(artifact())
    prov.add_edge(
        ProvenanceEdge(
            artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
            object_id=MODEL_ID,
            relation=ProvenanceRelation.DEFINES,
        )
    )
    prov.audit()
    after = registry.get(MODEL_ID)
    assert after.status is EvidenceStatus.CANDIDATE
    assert after.content_hash() == before
    assert registry.get(EVIDENCE_ID).status is EvidenceStatus.FORWARD_OOS


# ---------------------------------------------------------------------------
# 16. Artifact registry does not create Evidence objects
# ---------------------------------------------------------------------------


def test_artifact_registry_does_not_create_evidence_objects():
    registry = base_registry()
    prov = ProvenanceRegistry(registry)
    before = registry.ids()
    for cls in ("PDF", "VISUAL", "CONVERSATION_DERIVED", "CSV"):
        prov.add_artifact(
            Artifact(
                artifact_id=f"ART.{cls}.NO_AUTO_EVIDENCE.V1",
                source_class=cls,
                content_identity=None,
                locator=f"corpus/{cls.lower()}/file",
            )
        )
    assert registry.ids() == before
    evidence_ids = [
        oid for oid in registry.ids() if CanonicalId.parse(oid).object_type is ObjectType.EVIDENCE
    ]
    assert evidence_ids == [EVIDENCE_ID]


# ---------------------------------------------------------------------------
# 17. Deterministic audit output
# ---------------------------------------------------------------------------


def _build(reverse: bool = False) -> ProvenanceRegistry:
    registry = base_registry()
    prov = ProvenanceRegistry(registry)
    items = [
        Artifact(
            artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
            source_class="PDF",
            source_state=SourceState.VERIFIED,
            content_identity=compute_content_identity(b"pdf-bytes"),
            locator="corpus/papers/eur_ho_review.pdf",
        ),
        Artifact(
            artifact_id="ART.VISUAL.HO_DIAGRAM.V1",
            source_class="VISUAL",
            source_state=SourceState.VERIFIED,
            content_identity=compute_content_identity(b"diagram"),
            locator="corpus/results/ho_diagram.png",
        ),
        Artifact(
            artifact_id="ART.CSV.SAMPLE_TABLE.V1",
            source_class="CSV",
            source_state=SourceState.PARTIAL,
            content_identity=compute_content_identity(b"a,b,c"),
            locator="corpus/results/sample.csv",
        ),
    ]
    edges = [
        ProvenanceEdge(
            artifact_id="ART.PDF.EUR_HO_REVIEW.V1",
            object_id=EVIDENCE_ID,
            relation=ProvenanceRelation.SUPPORTS,
        ),
        ProvenanceEdge(
            artifact_id="ART.VISUAL.HO_DIAGRAM.V1",
            object_id=CLAIM_ID,
            relation=ProvenanceRelation.VISUALIZES,
        ),
        ProvenanceEdge(
            artifact_id="ART.CSV.SAMPLE_TABLE.V1",
            object_id=EVIDENCE_ID,
            relation=ProvenanceRelation.DERIVED_FROM,
        ),
    ]
    for item in (items if not reverse else list(reversed(items))):
        prov.add_artifact(item)
    for edge in (edges if not reverse else list(reversed(edges))):
        prov.add_edge(edge)
    return prov


def test_audit_output_is_deterministic_regardless_of_insertion_order():
    first = _build(reverse=False).audit()
    second = _build(reverse=True).audit()
    assert first.to_json() == second.to_json()
    assert first.content_hash() == second.content_hash()
    # no timestamps or wall-clock values in the report payload
    payload = first.to_json()
    assert "generated_at" not in payload and "timestamp" not in payload


def test_audit_report_fields_are_sorted():
    report = _build().audit()
    assert list(report.orphan_objects) == sorted(report.orphan_objects)
    assert list(report.gaps) == sorted(report.gaps, key=lambda g: (g["kind"], g["target"], g["detail"]))
    assert [e["artifact_id"] for e in report.unresolved_sources] == sorted(
        e["artifact_id"] for e in report.unresolved_sources
    )


# ---------------------------------------------------------------------------
# H. Invariants: no persistence / retrieval / UI / provider imports
# ---------------------------------------------------------------------------


def test_provenance_module_has_no_persistence_retrieval_or_provider_imports():
    allowed = {"__future__", "hashlib", "json", "re", "enum", "typing", "pydantic", "app"}
    module = Path(__file__).resolve().parents[1] / "app" / "forge" / "provenance.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert roots <= allowed, f"forbidden imports: {sorted(roots - allowed)}"
