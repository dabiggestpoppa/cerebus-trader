import ast
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalReference,
    CanonicalRegistry,
    ClaimComparison,
    ClaimIdentity,
    EvidenceStatus,
    EvidenceType,
    Layer,
    ObjectType,
    ProductExposure,
    compare_claim_identity,
    validate_status_transition,
)


def obj(
    cid="MOD.EUR.DAILY.V1",
    status=EvidenceStatus.CANDIDATE,
    refs=(),
    metadata=None,
):
    return CanonicalObject(
        canonical_id=CanonicalId.parse(cid),
        title="Test object",
        version="1",
        status=status,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.L1,
        references=refs,
        metadata=metadata or {},
    )


def test_id_parses_type():
    cid = CanonicalId.parse("EV.EUR.HO.D3_DIRECTION.V1")
    assert cid.object_type == ObjectType.EVIDENCE


def test_id_prefix_type_mismatch_fails():
    with pytest.raises(ValidationError):
        CanonicalId(value="MOD.EUR.DAILY.V1", object_type=ObjectType.CLAIM)


def test_invalid_id_fails():
    with pytest.raises(ValueError):
        CanonicalId.parse("EUR DAILY")


def test_identity_is_immutable():
    cid = CanonicalId.parse("CL.EUR.TEST.V1")
    with pytest.raises(ValidationError):
        cid.value = "CL.EUR.OTHER.V1"


def test_unsupported_enum_fails():
    with pytest.raises(ValidationError):
        CanonicalObject(
            canonical_id=CanonicalId.parse("MOD.EUR.TEST.V1"),
            title="x",
            version="1",
            status="MAGIC",
            exposure=ProductExposure.SUBSCRIBER_MODEL,
        )


def test_deterministic_hash_ignores_metadata_dictionary_order():
    a = obj(metadata={"b": 2, "a": 1})
    b = obj(metadata={"a": 1, "b": 2})
    assert a.deterministic_payload() == b.deterministic_payload()
    assert a.content_hash() == b.content_hash()


def test_duplicate_id_rejected():
    registry = CanonicalRegistry([obj()])
    with pytest.raises(ValueError, match="duplicate"):
        registry.add(obj())


def test_self_reference_rejected():
    ref = CanonicalReference(target_id="MOD.EUR.DAILY.V1", relation="PARENT")
    with pytest.raises(ValueError, match="self reference"):
        CanonicalRegistry([obj(refs=(ref,))])


def test_dangling_reference_rejected():
    ref = CanonicalReference(target_id="EV.EUR.MISSING.V1", relation="SUPPORTED_BY")
    registry = CanonicalRegistry([obj(refs=(ref,))])
    with pytest.raises(ValueError, match="dangling"):
        registry.validate_references()


def test_historical_partial_reference_may_be_explicitly_unresolved():
    ref = CanonicalReference(
        target_id="ART.LEGACY.MISSING.V1",
        relation="SOURCE",
        allow_unresolved_historical=True,
    )
    registry = CanonicalRegistry(
        [obj(cid="MOD.LEGACY.V1", status=EvidenceStatus.HISTORICAL, refs=(ref,))]
    )
    registry.validate_references()


def test_nonhistorical_cannot_use_partial_escape_hatch():
    ref = CanonicalReference(
        target_id="ART.MISSING.V1",
        relation="SOURCE",
        allow_unresolved_historical=True,
    )
    registry = CanonicalRegistry([obj(refs=(ref,))])
    with pytest.raises(ValueError, match="dangling"):
        registry.validate_references()


def test_reference_resolves_when_target_present():
    evidence = obj(cid="EV.EUR.TEST.V1", status=EvidenceStatus.VALIDATED)
    ref = CanonicalReference(target_id="EV.EUR.TEST.V1", relation="SUPPORTED_BY")
    model = obj(refs=(ref,))
    registry = CanonicalRegistry([evidence, model])
    registry.validate_references()
    assert registry.ids() == ("EV.EUR.TEST.V1", "MOD.EUR.DAILY.V1")


@pytest.mark.parametrize(
    "current,target",
    [
        (EvidenceStatus.OBSERVED, EvidenceStatus.CANDIDATE),
        (EvidenceStatus.CANDIDATE, EvidenceStatus.VALIDATED),
        (EvidenceStatus.VALIDATED, EvidenceStatus.FORWARD_OOS),
        (EvidenceStatus.VALIDATED, EvidenceStatus.SUPERSEDED),
        (EvidenceStatus.INTERNAL_CONTRADICTION, EvidenceStatus.REPRODUCTION_REQUIRED),
    ],
)
def test_legal_lifecycle_transitions(current, target):
    validate_status_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        (EvidenceStatus.SUPERSEDED, EvidenceStatus.VALIDATED),
        (EvidenceStatus.FALSIFIED, EvidenceStatus.CANDIDATE),
        (EvidenceStatus.OBSERVED, EvidenceStatus.FORWARD_OOS),
        (EvidenceStatus.HISTORICAL, EvidenceStatus.VALIDATED),
    ],
)
def test_illegal_lifecycle_transitions(current, target):
    with pytest.raises(ValueError, match="illegal canonical status transition"):
        validate_status_transition(current, target)


def test_registry_transition_preserves_identity():
    registry = CanonicalRegistry([obj()])
    before = registry.get("MOD.EUR.DAILY.V1").canonical_id
    after = registry.transition("MOD.EUR.DAILY.V1", EvidenceStatus.VALIDATED)
    assert after.canonical_id == before
    assert after.status == EvidenceStatus.VALIDATED


def claim(**overrides):
    base = dict(
        market="EURUSD",
        event_definition="D3 close direction",
        conditioning_event="complete quarter",
        clock_origin="quarter open",
        horizon="quarter close",
        tolerance="exact direction",
        eligibility="complete quarter",
        implementation_semantics="HO_V1",
    )
    base.update(overrides)
    return ClaimIdentity(**base)


def test_equal_claim_identity_same_population():
    assert compare_claim_identity(claim(), claim()) == ClaimComparison.SAME_POPULATION


@pytest.mark.parametrize(
    "field,value",
    [
        ("market", "XAUUSD"),
        ("event_definition", "M1 direction"),
        ("conditioning_event", "D3 and M1 agree"),
        ("clock_origin", "M1 open"),
        ("horizon", "M3 close"),
        ("tolerance", "+/- 1 day"),
        ("eligibility", "OOS only"),
        ("implementation_semantics", "HO_V2"),
    ],
)
def test_material_claim_identity_mismatch_is_parallel(field, value):
    assert compare_claim_identity(claim(), claim(**{field: value})) == ClaimComparison.PARALLEL


# ---------------------------------------------------------------------------
# Acceptance-clause coverage: executable assertions for clauses that were
# previously satisfied only by inspection (see ACCEPTANCE.md sections B, E, F).
# ---------------------------------------------------------------------------

_CANONICAL_MD = Path(__file__).resolve().parents[1] / "corpus" / "canonical"


def _md_tokens(heading: str, filename: str) -> set[str]:
    """Collect uppercase enum-like tokens under a markdown heading."""
    lines = (_CANONICAL_MD / filename).read_text(encoding="utf-8").splitlines()
    tokens: set[str] = set()
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            collecting = True
            continue
        if not collecting:
            continue
        if stripped.startswith("##"):
            break
        token = stripped.rstrip(".")
        if token and re.fullmatch(r"[A-Z][A-Z0-9_]*", token):
            tokens.add(token)
    return tokens


def test_object_type_covers_frozen_i1_registry_classes():
    """ACCEPTANCE B: object type includes the frozen registry classes for I.1."""
    assert {t.value for t in ObjectType} == {
        "MODEL",
        "CLAIM",
        "EVIDENCE",
        "SETUP",
        "DOCTRINE",
        "TERM",
        "LINEAGE",
        "ARTIFACT",
    }


def test_evidence_status_enum_matches_frozen_taxonomy():
    frozen = _md_tokens("## Evidence statuses", "CEREBUS_CANONICAL_TAXONOMY_V1.md")
    assert frozen, "taxonomy section must not be empty"
    assert {s.value for s in EvidenceStatus} == frozen


def test_evidence_type_enum_matches_frozen_taxonomy():
    frozen = _md_tokens("### 12 EVIDENCE", "CEREBUS_CANONICAL_TAXONOMY_V1.md")
    assert frozen, "taxonomy section must not be empty"
    assert {t.value for t in EvidenceType} == frozen


def test_exposure_enum_matches_frozen_exposure_rules():
    frozen = _md_tokens("## Exposure classes", "PRODUCT_EXPOSURE_RULES_V1.md")
    assert frozen, "exposure rules section must not be empty"
    assert {e.value for e in ProductExposure} == frozen


def test_claim_population_identity_excludes_result_values():
    """ACCEPTANCE E: claim values/results are not part of population identity."""
    assert set(ClaimIdentity.model_fields) == {
        "market",
        "event_definition",
        "conditioning_event",
        "clock_origin",
        "horizon",
        "tolerance",
        "eligibility",
        "implementation_semantics",
    }
    assert compare_claim_identity(
        claim(result="69.5%"), claim(result="41.0%")
    ) == ClaimComparison.SAME_POPULATION


def test_kernel_imports_have_no_persistence_retrieval_or_provider_leakage():
    """ACCEPTANCE F / kernel contract: no persistence, retrieval, UI or provider
    behavior inside the I.1 kernel modules."""
    allowed = {"__future__", "hashlib", "json", "re", "enum", "typing", "pydantic", "app"}
    pkg_dir = Path(__file__).resolve().parents[1] / "app" / "forge"
    for module in ("canonical.py", "schemas.py"):
        tree = ast.parse((pkg_dir / module).read_text(encoding="utf-8"))
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        assert roots <= allowed, f"{module} imports forbidden modules: {sorted(roots - allowed)}"
