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
