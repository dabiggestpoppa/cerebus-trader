"""Specialized canonical card contracts for FORGE Book I / Bloc I.1.

These are machine-readable counterparts to the frozen Markdown card schemas.
They validate identity and cross-object references without implementing
persistence or corpus backfill.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.forge.canonical import (
    CanonicalId,
    EvidenceStatus,
    EvidenceType,
    Layer,
    ProductExposure,
    SetupClass,
)


def _typed_id(value: str, expected: str) -> str:
    cid = CanonicalId.parse(value)
    if cid.object_type.value != expected:
        raise ValueError(f"expected {expected} id, got {cid.object_type.value}")
    return value


class ModelCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_id: str
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: EvidenceStatus
    market_scope: tuple[str, ...]
    layer: Layer
    model_type: str = Field(min_length=1)
    product_exposure: ProductExposure
    purpose: str = Field(min_length=1)
    inputs: tuple[str, ...] = ()
    state_space: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    eligibility: tuple[str, ...] = ()
    no_go: tuple[str, ...] = ()
    calibration: dict[str, Any] = Field(default_factory=dict)
    evidence_card_ids: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    ancestor_ids: tuple[str, ...] = ()
    descendant_ids: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    absorbs: tuple[str, ...] = ()
    implementation_artifacts: tuple[str, ...] = ()
    parity_status: str | None = None
    operator_interpretation: str = Field(min_length=1)
    beginner_summary: str = Field(min_length=1)
    operator_summary: str = Field(min_length=1)
    researcher_summary: str = Field(min_length=1)
    forbidden_overclaims: tuple[str, ...] = ()

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, value: str) -> str:
        return _typed_id(value, "MODEL")

    @field_validator("evidence_card_ids")
    @classmethod
    def validate_evidence_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            _typed_id(value, "EVIDENCE")
        return values


class EvidenceCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: str
    claim_id: str
    title: str = Field(min_length=1)
    status: EvidenceStatus
    evidence_type: EvidenceType
    source_artifact: str
    source_generation: str
    market: str
    data_period: str
    sample_n: int = Field(ge=0)
    exact_claim: str = Field(min_length=1)
    event_definition: str
    conditioning_event: str
    clock_origin: str
    horizon: str
    tolerance: str
    eligibility_filter: str
    numerator: float | int | None = None
    denominator: float | int | None = None
    metric: str
    result: str
    calculation_type: str
    implementation_name: str
    version_or_hash: str
    execution_semantics: str
    data_granularity: str
    session_definition: str
    clock_mode: str
    in_sample: bool = False
    out_of_sample: bool = False
    forward_oos: bool = False
    reproduction_status: str
    contradictions: tuple[str, ...] = ()
    interpretation: str
    does_not_support: tuple[str, ...] = ()
    product_exposure: ProductExposure

    @field_validator("evidence_id")
    @classmethod
    def validate_evidence_id(cls, value: str) -> str:
        return _typed_id(value, "EVIDENCE")

    @field_validator("claim_id")
    @classmethod
    def validate_claim_id(cls, value: str) -> str:
        return _typed_id(value, "CLAIM")


class SetupOperatorCard(BaseModel):
    model_config = ConfigDict(frozen=True)

    setup_id: str
    name: str
    version: str
    status: EvidenceStatus
    market_scope: tuple[str, ...]
    execution_class: SetupClass
    parent_model_ids: tuple[str, ...]
    product_exposure: ProductExposure
    purpose: str
    eligibility: tuple[str, ...]
    entry: tuple[str, ...]
    invalidation: tuple[str, ...]
    targets: tuple[str, ...]
    no_go: tuple[str, ...]
    l3_destination: str
    l2_path: str
    l1_execution: str
    claim_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    failure_repair: str
    manual_rule_source: str
    indicator_source: str | None = None
    automation_status: str
    parity_status: str
    beginner_summary: str
    operator_instructions: str
    researcher_notes: str
    forbidden_overclaims: tuple[str, ...] = ()

    @field_validator("setup_id")
    @classmethod
    def validate_setup_id(cls, value: str) -> str:
        return _typed_id(value, "SETUP")

    @field_validator("parent_model_ids")
    @classmethod
    def validate_models(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            _typed_id(value, "MODEL")
        return values

    @field_validator("claim_ids")
    @classmethod
    def validate_claims(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            _typed_id(value, "CLAIM")
        return values

    @field_validator("evidence_ids")
    @classmethod
    def validate_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            _typed_id(value, "EVIDENCE")
        return values
