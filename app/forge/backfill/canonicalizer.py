"""Canonicalizer: historical cards -> governed canonical objects (I.3).

Transforms parsed card files into validated I.1 machine contracts
(``ModelCard``/``EvidenceCard``/``SetupOperatorCard``) and ``CanonicalObject``
aggregates with explicit provenance. Deterministic; validated with the ratified
schemas; no promotion, no fabrication, no silent field loss.

Migration classifications (MigrationClass) are a migration dimension and are
never used as evidence statuses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.forge.backfill import mappings as M
from app.forge.backfill.parser import ParsedCard, parse_card, split_csv
from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalReference,
    ClaimIdentity,
    EvidenceStatus,
    EvidenceType,
    Layer,
    ObjectType,
    ProductExposure,
    SetupClass,
)
from app.forge.persistence.records import CanonicalObjectRecord
from app.forge.schemas import EvidenceCard, ModelCard, SetupOperatorCard

_NOT_SPECIFIED = M.NOT_SPECIFIED
_RESULT_RE = re.compile(r"[-+]?\d*\.?\d+")
_EV_ID_RE = re.compile(r"^(EV\.[A-Za-z0-9_.\-]+)")


# ---------------------------------------------------------------------------
# Result / report dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MigrationOutcome:
    path: str
    canonical_id: str | None
    classification: M.MigrationClass
    reason: str
    object_type: str | None = None


@dataclass
class BackfillReport:
    """Deterministic, content-free audit report (counts + ids only)."""

    sources_inventoried: int = 0
    ready: int = 0
    mapped: int = 0
    migrated: int = 0
    unchanged: int = 0
    quarantined: int = 0
    missing_source: int = 0
    unresolved_reference: int = 0
    unsupported_numerical_claim: int = 0
    models: int = 0
    evidence: int = 0
    setups: int = 0
    claims: int = 0
    artifacts: int = 0
    provenance_edges: int = 0
    negative_evidence: int = 0
    visual_only_sources: int = 0
    conversation_derived_sources: int = 0
    conflicts: int = 0
    outcomes: tuple[MigrationOutcome, ...] = ()
    quarantined_ids: tuple[str, ...] = ()
    _sorted: bool = False

    def to_json(self) -> str:
        import json

        payload = {
            "sources_inventoried": self.sources_inventoried,
            "ready": self.ready,
            "mapped": self.mapped,
            "migrated": self.migrated,
            "unchanged": self.unchanged,
            "quarantined": self.quarantined,
            "missing_source": self.missing_source,
            "unresolved_reference": self.unresolved_reference,
            "unsupported_numerical_claim": self.unsupported_numerical_claim,
            "models": self.models,
            "evidence": self.evidence,
            "setups": self.setups,
            "claims": self.claims,
            "artifacts": self.artifacts,
            "provenance_edges": self.provenance_edges,
            "negative_evidence": self.negative_evidence,
            "visual_only_sources": self.visual_only_sources,
            "conversation_derived_sources": self.conversation_derived_sources,
            "conflicts": self.conflicts,
            "outcomes": [
                {
                    "path": o.path,
                    "canonical_id": o.canonical_id,
                    "classification": o.classification.value,
                    "reason": o.reason,
                    "object_type": o.object_type,
                }
                for o in self.outcomes
            ],
            "quarantined_ids": list(self.quarantined_ids),
        }
        return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)

    def content_hash(self) -> str:
        import hashlib

        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Per-kind canonicalization helpers (continued)
# ---------------------------------------------------------------------------


def _ask(card: ParsedCard, key: str, fallback: str = _NOT_SPECIFIED) -> str:
    value = card.ask_line(key)
    return value if value else fallback


def _forbidden(card: ParsedCard) -> tuple[str, ...]:
    raw = card.ask_line("Forbidden")
    if not raw:
        return ()
    return tuple(part.strip(" ;.") for part in raw.split(";") if part.strip(" ;."))


def _evidence(card: ParsedCard) -> tuple[EvidenceCard | None, str, list[tuple[str, object]]]:
    """Canonicalize one evidence card. Returns (EvidenceCard|None, reason, flags)."""
    f = card.fields
    flags: list[tuple[str, object]] = []
    evidence_id = f.get("evidence_id", "").strip()
    try:
        canonical_id = M.resolve_canonical_id(evidence_id, ObjectType.EVIDENCE)
    except ValueError as exc:
        return None, f"id mapping failed: {exc}", flags

    claim_id = f.get("claim_id", "").strip()
    try:
        claim_canonical = M.resolve_canonical_id(claim_id, ObjectType.CLAIM)
    except ValueError as exc:
        return None, f"claim id mapping failed: {exc}", flags

    status_resolved = M.resolve_status(f.get("status", ""))
    if status_resolved is None:
        return None, f"unknown legacy status: {f.get('status', '')!r}", flags
    status, status_map = status_resolved
    flags.extend(status_map.metadata_flags)

    type_resolved = M.resolve_evidence_type(f.get("evidence_type", ""), canonical_id)
    if type_resolved is None:
        return None, f"unknown legacy evidence type: {f.get('evidence_type', '')!r}", flags
    evidence_type, type_map = type_resolved
    flags.extend(type_map.metadata_flags)

    exposure = M.EVIDENCE_EXPOSURE.get(canonical_id)
    if exposure is None:
        return None, "no explicit frozen exposure assignment for evidence card", flags

    sample_raw = f.get("sample_n", "").strip()
    sample_n = 0
    if sample_raw:
        numbers = _RESULT_RE.findall(sample_raw)
        if numbers:
            sample_n = int(float(numbers[-1]))
            if not sample_raw.replace(str(sample_n), "").strip().isdigit():
                flags.append(("sample_n_note", sample_raw))

    section = card.section_text
    machine = EvidenceCard(
        evidence_id=canonical_id,
        claim_id=claim_canonical,
        title=card.title or canonical_id,
        status=status,
        evidence_type=evidence_type,
        source_artifact=f.get("source_artifact", "").strip() or _NOT_SPECIFIED,
        source_generation=f.get("source_generation", "").strip() or _NOT_SPECIFIED,
        market=f.get("market", "").strip() or _NOT_SPECIFIED,
        data_period=f.get("data_period", "").strip() or _NOT_SPECIFIED,
        sample_n=sample_n,
        exact_claim=section("Exact claim") or section("Exact claims") or _NOT_SPECIFIED,
        event_definition=_NOT_SPECIFIED,
        conditioning_event=_NOT_SPECIFIED,
        clock_origin=_NOT_SPECIFIED,
        horizon=_NOT_SPECIFIED,
        tolerance=_NOT_SPECIFIED,
        eligibility_filter=_NOT_SPECIFIED,
        metric=_NOT_SPECIFIED,
        result=section("Result") or _NOT_SPECIFIED,
        calculation_type=_NOT_SPECIFIED,
        implementation_name=_NOT_SPECIFIED,
        version_or_hash=_NOT_SPECIFIED,
        execution_semantics=_NOT_SPECIFIED,
        data_granularity=_NOT_SPECIFIED,
        session_definition=_NOT_SPECIFIED,
        clock_mode=_NOT_SPECIFIED,
        reproduction_status=_NOT_SPECIFIED,
        contradictions=tuple(card.section("Contradictions / negative evidence")) or (),
        interpretation=section("Interpretation") or _NOT_SPECIFIED,
        does_not_support=tuple(card.section("Does not support")) or (),
        product_exposure=exposure,
    )
    return machine, "ok", flags


def _setup(card: ParsedCard) -> tuple[SetupOperatorCard | None, str]:
    """Canonicalize one setup/operator card."""
    f = card.fields
    legacy_id = f.get("setup_id", "").strip()
    try:
        canonical_id = M.resolve_canonical_id(legacy_id, ObjectType.SETUP)
    except ValueError as exc:
        return None, f"id mapping failed: {exc}"

    status_resolved = M.resolve_status(f.get("status", ""))
    if status_resolved is None:
        return None, f"unknown legacy status: {f.get('status', '')!r}"
    status, _ = status_resolved

    try:
        execution_class = SetupClass(f.get("execution_class", "").strip())
    except ValueError:
        return None, f"unknown execution_class: {f.get('execution_class', '')!r}"
    try:
        exposure = ProductExposure(f.get("product_exposure", "").strip())
    except ValueError:
        return None, f"unknown/missing product_exposure: {f.get('product_exposure', '')!r}"

    parent_models = tuple(
        M.resolve_canonical_id(pid.strip(), ObjectType.MODEL)
        for pid in split_csv(f.get("parent_model_ids", ""))
    )

    machine = SetupOperatorCard(
        setup_id=canonical_id,
        name=card.title or canonical_id,
        version=f.get("version", "").strip() or "V1",
        status=status,
        market_scope=split_csv(f.get("market_scope", "")),
        execution_class=execution_class,
        parent_model_ids=parent_models,
        product_exposure=exposure,
        purpose=card.section_text("Purpose") or _NOT_SPECIFIED,
        eligibility=tuple(card.section("Eligibility")) or (),
        entry=tuple(card.section("Entry"))
        or tuple(card.section("Entry lineage"))
        or (),
        invalidation=tuple(card.section("Invalidation"))
        or tuple(card.section("Invalidation / targets"))
        or (),
        targets=tuple(card.section("Targets")) or (),
        no_go=tuple(card.section("No-go"))
        or tuple(card.section("No-go / stand-down"))
        or (),
        l3_destination=_NOT_SPECIFIED,
        l2_path=_NOT_SPECIFIED,
        l1_execution=_NOT_SPECIFIED,
        claim_ids=(),
        evidence_ids=tuple(
            M.resolve_canonical_id(match.group(1).rstrip("."), ObjectType.EVIDENCE)
            for match in (
                _EV_ID_RE.match(line.strip()) for line in card.section("Evidence")
            )
            if match is not None
        ),
        failure_repair=card.section_text("Failure / repair") or _NOT_SPECIFIED,
        manual_rule_source=_NOT_SPECIFIED,
        indicator_source=None,
        automation_status="MANUAL_OPERATOR"
        if execution_class is SetupClass.MANUAL_OPERATOR
        else ("RESEARCH_ONLY" if execution_class is SetupClass.RESEARCH_ONLY else _NOT_SPECIFIED),
        parity_status=_NOT_SPECIFIED,
        beginner_summary=_ask(card, "Beginner"),
        operator_instructions=_ask(card, "Operator"),
        researcher_notes=_ask(card, "Researcher"),
        forbidden_overclaims=_forbidden(card),
    )
    return machine, "ok"


def _machine_to_object(
    machine: ModelCard | EvidenceCard | SetupOperatorCard,
    legacy_id: str,
    flags: list[tuple[str, object]],
) -> CanonicalObject:
    """Build the persisted CanonicalObject aggregate from a validated machine card."""
    card_payload = machine.model_dump(mode="json")
    metadata: dict = {"card": card_payload, "legacy_ids": [legacy_id]}
    for key, value in flags:
        metadata[key] = value

    own_id = (
        machine.model_id
        if isinstance(machine, ModelCard)
        else machine.evidence_id
        if isinstance(machine, EvidenceCard)
        else machine.setup_id
    )
    cid = CanonicalId.parse(own_id)
    references: list[CanonicalReference] = []
    if isinstance(machine, ModelCard):
        for eid in machine.evidence_card_ids:
            references.append(CanonicalReference(target_id=eid, relation="supported_by"))
    elif isinstance(machine, EvidenceCard):
        references.append(
            CanonicalReference(target_id=machine.claim_id, relation="evidence_for")
        )
    elif isinstance(machine, SetupOperatorCard):
        for mid in machine.parent_model_ids:
            references.append(CanonicalReference(target_id=mid, relation="parent"))
        for eid in machine.evidence_ids:
            references.append(CanonicalReference(target_id=eid, relation="supported_by"))

    layer = (
        machine.layer
        if isinstance(machine, ModelCard)
        else Layer.NONE
    )
    return CanonicalObject(
        canonical_id=cid,
        title=card_payload.get("title") or card_payload.get("name") or own_id,
        version=card_payload.get("version") or "V1",
        status=machine.status,
        exposure=machine.product_exposure,
        layer=layer,
        references=tuple(references),
        metadata=metadata,
    )


def _claim_identity(entry: dict[str, str]) -> ClaimIdentity:
    """Build the population identity for a registry claim. Dimensions the frozen
    registry does not state carry NOT_SPECIFIED markers (uncertainty preserved).
    Result/statistic values are NOT part of identity (ACCEPTANCE G3)."""
    market = {
        "CL.EUR.HO.D3_DIRECTION": "EURUSD",
        "CL.EUR.HO.UNFINISHED_M3": "EURUSD",
        "CL.EUR.HO.M1_RANGE_CORR": "EURUSD",
        "CL.EUR.DAILY.TIER_CALIBRATION": "EURUSD",
        "CL.EUR.DAILY.NEWS_INCREMENT": "EURUSD",
        "CL.EUR.WEEKLY.TIER_RANGE": "EURUSD",
        "CL.XAU.PROMOTION.68_80": "XAUUSD",
        "CL.XAU.PROMOTION.120_132": "XAUUSD",
        "CL.JPY.CARRY.ROLE_RELATION": "USDJPY,AUDJPY,EURJPY",
        "CL.FIB.R11.GENERATOR_FAILURE": "EURUSD,XAUUSD,BTCUSD",
    }[entry["claim_id"]]
    return ClaimIdentity(
        market=market,
        event_definition=entry["claim"],
        conditioning_event=_NOT_SPECIFIED,
        clock_origin=_NOT_SPECIFIED,
        horizon=_NOT_SPECIFIED,
        tolerance=_NOT_SPECIFIED,
        eligibility=_NOT_SPECIFIED,
        implementation_semantics=_NOT_SPECIFIED,
    )


def build_claim_objects() -> tuple[CanonicalObjectRecord, ...]:
    """Deterministically build the 10 registry CLAIM records.

    Status is taken from the registry table through the SAME explicit status
    mapping used for cards (no silent promotion of VALIDATED_RESEARCH etc.).
    """
    records: list[CanonicalObjectRecord] = []
    for entry in M.REGISTRY_CLAIMS:
        status_resolved = M.resolve_status(entry["status"])
        if status_resolved is None:
            raise ValueError(f"registry claim status unmapped: {entry['status']!r}")
        status, status_map = status_resolved
        flags = dict(status_map.metadata_flags)
        if entry["claim_id"] == "CL.FIB.R11.GENERATOR_FAILURE":
            flags["negative_claim"] = True
        cid = CanonicalId.parse(entry["claim_id"])
        references = (
            CanonicalReference(target_id=entry["evidence"], relation="supported_by"),
            CanonicalReference(target_id=entry["model"], relation="belongs_to"),
        )
        records.append(
            CanonicalObjectRecord(
                canonical_id=cid.value,
                object_type=ObjectType.CLAIM,
                title=entry["claim"],
                version="V1",
                status=status,
                exposure=ProductExposure.SUBSCRIBER_MODEL,
                layer=Layer.NONE,
                references=references,
                metadata={
                    "legacy_ids": [entry["claim_id"]],
                    "claim_text": entry["claim"],
                    "layer_tag": entry["layer"],
                    **flags,
                },
                claim_identity=_claim_identity(entry),
            )
        )
    return tuple(records)


# ---------------------------------------------------------------------------
# Migration plan assembly
# ---------------------------------------------------------------------------


@dataclass
class MigrationPlan:
    """Everything one APPLY/DRY_RUN needs, derived deterministically."""

    objects: list[CanonicalObjectRecord] = field(default_factory=list)
    artifacts: list[tuple] = field(default_factory=list)  # (ArtifactRecord,)
    edges: list[tuple[str, str, str, str]] = field(default_factory=list)
    report: BackfillReport = field(default_factory=BackfillReport)


def _artifact_record(path: str, content: str) -> tuple:
    """Deterministic artifact registration for one source file."""
    from app.forge.persistence.records import ArtifactRecord
    from app.forge.provenance import compute_content_identity, derive_artifact_id

    identity = compute_content_identity(content.encode("utf-8"))
    artifact_id = derive_artifact_id("MARKDOWN", identity)
    return ArtifactRecord(
        artifact_id=artifact_id,
        source_class="MARKDOWN",
        title=path.rsplit("/", 1)[-1],
        source_generation="",
        version=None,
        locator=path,
        content_identity=identity,
        source_state="READ",
    )


def _named_artifact(path: str, content: str, source_class: str) -> tuple | None:
    from app.forge.persistence.records import ArtifactRecord
    from app.forge.provenance import compute_content_identity, derive_artifact_id

    if source_class not in ("PINE", "MARKDOWN"):
        return None
    identity = compute_content_identity(content.encode("utf-8"))
    token = "PINE" if source_class == "PINE" else "MARKDOWN"
    return ArtifactRecord(
        artifact_id=derive_artifact_id(token, identity),
        source_class=source_class,
        title=path.rsplit("/", 1)[-1],
        locator=path,
        content_identity=identity,
        source_state="READ",
    )


def canonicalize_files(files: dict[str, str]) -> MigrationPlan:
    """Migrate the in-scope card corpus (path -> text) into a MigrationPlan.

    Deterministic over the provided mapping; never touches disk state beyond
    what the caller passes; never mutates the inputs.
    """
    plan = MigrationPlan()
    report = plan.report
    seen_object_ids: set[str] = set()

    # 1. Card files (models, evidence, setups) -> canonical objects.
    for path in sorted(files):
        if path == M.CLAIM_REGISTRY_PATH:
            # Governance contract: inventoried + artifact-registered below
            # (step 2.5), never parsed as a card and never quarantined.
            continue
        text = files[path]
        card = parse_card(path, text)
        report.sources_inventoried += 1
        artifact = _artifact_record(path, text)

        outcome_id: str | None = None
        outcome_type: str | None = None

        if card.kind == "MODEL CARD":
            machine, reason, model_flags = _model(card)
            outcome_type = ObjectType.MODEL.value
            if machine is None:
                report.quarantined += 1
                report.outcomes += (
                    MigrationOutcome(path, None, M.MigrationClass.QUARANTINED, reason, outcome_type),
                )
                continue
            legacy_id = card.fields.get("model_id", "").strip()
            obj = _machine_to_object(machine, legacy_id, model_flags)
            if obj.canonical_id.value in seen_object_ids:
                report.conflicts += 1
                report.outcomes += (
                    MigrationOutcome(
                        path, obj.canonical_id.value, M.MigrationClass.QUARANTINED,
                        "duplicate canonical id from a second source card",
                        outcome_type,
                    ),
                )
                continue
            seen_object_ids.add(obj.canonical_id.value)
            plan.objects.append(CanonicalObjectRecord.from_domain(obj))
            outcome_id = obj.canonical_id.value
            report.models += 1
        elif card.kind == "EVIDENCE CARD":
            machine, reason, flags = _evidence(card)
            outcome_type = ObjectType.EVIDENCE.value
            if machine is None:
                report.quarantined += 1
                report.outcomes += (
                    MigrationOutcome(path, None, M.MigrationClass.QUARANTINED, reason, outcome_type),
                )
                continue
            if machine.evidence_type is EvidenceType.NEGATIVE_EVIDENCE:
                report.negative_evidence += 1
            legacy_id = card.fields.get("evidence_id", "").strip()
            obj = _machine_to_object(machine, legacy_id, flags)
            plan.objects.append(CanonicalObjectRecord.from_domain(obj))
            outcome_id = obj.canonical_id.value
            report.evidence += 1
        elif card.kind == "SETUP CARD":
            machine, reason = _setup(card)
            outcome_type = ObjectType.SETUP.value
            if machine is None:
                report.quarantined += 1
                report.outcomes += (
                    MigrationOutcome(path, None, M.MigrationClass.QUARANTINED, reason, outcome_type),
                )
                continue
            legacy_id = card.fields.get("setup_id", "").strip()
            obj = _machine_to_object(machine, legacy_id, [])
            plan.objects.append(CanonicalObjectRecord.from_domain(obj))
            outcome_id = obj.canonical_id.value
            report.setups += 1
        else:
            report.quarantined += 1
            report.outcomes += (
                MigrationOutcome(
                    path, None, M.MigrationClass.QUARANTINED,
                    "file does not match a known canonical card template",
                ),
            )
            continue

        # Provenance: card markdown DEFINES the canonical object.
        plan.artifacts.append(artifact)
        plan.edges.append((artifact.artifact_id, outcome_id, "DEFINES", "card source"))
        report.outcomes += (
            MigrationOutcome(
                path, outcome_id,
                M.MigrationClass.MAPPING_REQUIRED if any(
                    m.legacy_id == legacy_id and m.canonical_id != legacy_id
                    for m in M.LEGACY_ID_MAPPINGS
                ) else M.MigrationClass.READY,
                "migrated with explicit registry mapping"
                if any(m.legacy_id == legacy_id for m in M.LEGACY_ID_MAPPINGS)
                else "canonical id passthrough (validated)",
                outcome_type,
            ),
        )

    # 2. Registry claims.
    claim_records = build_claim_objects()
    for record in claim_records:
        plan.objects.append(record)
        report.claims += 1

    # 2.5. Claim registry artifact (ACCEPTANCE A1: the claim registry is an
    # in-scope source artifact; ACCEPTANCE I1: every migrated object —
    # including CLAIMs — carries >=1 provenance edge from a registered
    # artifact with deterministic content identity). A missing registry is
    # classified MISSING_SOURCE, never fabricated (ACCEPTANCE I4).
    registry_text = files.get(M.CLAIM_REGISTRY_PATH)
    if registry_text is None:
        report.missing_source += 1
        report.outcomes += (
            MigrationOutcome(
                M.CLAIM_REGISTRY_PATH, None, M.MigrationClass.MISSING_SOURCE,
                "claim registry not present in provided corpus state",
                ObjectType.CLAIM.value,
            ),
        )
    else:
        report.sources_inventoried += 1
        registry_artifact = _artifact_record(M.CLAIM_REGISTRY_PATH, registry_text)
        plan.artifacts.append(registry_artifact)
        for record in claim_records:
            plan.edges.append(
                (
                    registry_artifact.artifact_id,
                    record.canonical_id,
                    "DEFINES",
                    "claim registry defines this claim",
                )
            )
        report.outcomes += (
            MigrationOutcome(
                M.CLAIM_REGISTRY_PATH, None, M.MigrationClass.GOVERNANCE_CONTRACT,
                "governance contract inventoried (defines registry claims); "
                "not canonicalized into a domain object",
                ObjectType.CLAIM.value,
            ),
        )

    # 3. Named implementation/support/visualization artifacts + edges.
    for named in M.NAMED_ARTIFACT_EDGES:
        text = files.get(named.path)
        if text is None:
            report.missing_source += 1
            report.outcomes += (
                MigrationOutcome(
                    named.path, named.target_object,
                    M.MigrationClass.MISSING_SOURCE,
                    "named source not present in provided corpus state",
                    ObjectType.ARTIFACT.value,
                ),
            )
            continue
        artifact = _named_artifact(named.path, text, named.source_class)
        if artifact is None:
            report.quarantined += 1
            continue
        plan.artifacts.append(artifact)
        plan.edges.append((artifact.artifact_id, named.target_object, named.relation, named.note))
        if named.relation == "VISUALIZES":
            report.visual_only_sources += 1

    # 4. Conversation-derived inventory (non-empirical; never canonicalized).
    for path in sorted(files):
        if "/conversation-derived/" in path:
            report.conversation_derived_sources += 1

    # 5. Final counts.
    report.migrated = report.models + report.evidence + report.setups + report.claims
    report.artifacts = len(plan.artifacts)
    report.provenance_edges = len(plan.edges)
    report.mapped = sum(
        1 for o in report.outcomes if o.classification is M.MigrationClass.MAPPING_REQUIRED
    )
    report.ready = sum(
        1 for o in report.outcomes if o.classification is M.MigrationClass.READY
    )
    report.quarantined_ids = tuple(
        o.path for o in report.outcomes
        if o.classification is M.MigrationClass.QUARANTINED
    )
    return plan


def _ask(card: ParsedCard, key: str, fallback: str = _NOT_SPECIFIED) -> str:
    value = card.ask_line(key)
    return value if value else fallback


def _forbidden(card: ParsedCard) -> tuple[str, ...]:
    raw = card.ask_line("Forbidden")
    if not raw:
        return ()
    return tuple(part.strip(" ;.") for part in raw.split(";") if part.strip(" ;."))


def _model(
    card: ParsedCard,
) -> tuple[ModelCard | None, str, list[tuple[str, object]]]:
    """Canonicalize one model card. Returns (ModelCard|None, reason, flags)."""
    f = card.fields
    flags: list[tuple[str, object]] = []
    legacy_id = f.get("model_id", "").strip()
    try:
        canonical_id = M.resolve_canonical_id(legacy_id, ObjectType.MODEL)
    except ValueError as exc:
        return None, f"id mapping failed: {exc}", flags

    status_resolved = M.resolve_status(f.get("status", ""))
    if status_resolved is None:
        return None, f"unknown legacy status: {f.get('status', '')!r}", flags
    status, status_map = status_resolved
    flags.extend(status_map.metadata_flags)

    layer_resolved = M.resolve_layer(f.get("layer", ""))
    if layer_resolved is None:
        return None, f"unknown layer expression: {f.get('layer', '')!r}", flags
    layer_value, layer_detail = layer_resolved

    try:
        exposure = ProductExposure(f.get("product_exposure", "").strip())
    except ValueError:
        return None, (
            f"unknown/missing product_exposure: {f.get('product_exposure', '')!r}"
        ), flags

    evidence_ids = M.MODEL_EVIDENCE_LINKS.get(canonical_id, ())
    model_type = f.get("model_type", "").strip()
    purpose = card.section_text("Purpose") or _NOT_SPECIFIED
    if purpose == _NOT_SPECIFIED and not card.section("Purpose"):
        return None, "model card has no Purpose section", flags

    machine = ModelCard(
        model_id=canonical_id,
        name=card.title or canonical_id,
        version=f.get("version", "").strip() or "V1",
        status=status,
        market_scope=split_csv(f.get("market_scope", "")),
        layer=Layer(layer_value),
        model_type=model_type or _NOT_SPECIFIED,
        product_exposure=exposure,
        purpose=purpose,
        inputs=tuple(card.section("Inputs")) or (),
        state_space=tuple(card.section("State space")) or (),
        outputs=tuple(card.section("Outputs")) or (),
        eligibility=tuple(card.section("Eligibility / no-go"))
        or tuple(card.section("Eligibility"))
        or (),
        no_go=(),
        calibration={
            "layer_detail": layer_detail,
            "legacy_fields": dict(f),
        },
        evidence_card_ids=evidence_ids,
        known_limitations=tuple(card.section("Known limitations")) or (),
        ancestor_ids=(),
        descendant_ids=(),
        supersedes=(),
        absorbs=(),
        implementation_artifacts=(),
        parity_status=None,
        operator_interpretation=card.section_text("Operator interpretation")
        or _NOT_SPECIFIED,
        beginner_summary=_ask(card, "Beginner"),
        operator_summary=_ask(card, "Operator"),
        researcher_summary=_ask(card, "Researcher"),
        forbidden_overclaims=_forbidden(card),
    )
    return machine, "ok", flags
