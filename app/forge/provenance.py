"""Source & Provenance Fabric for GLX FORGE Book I / Bloc I.2.

Artifact != Evidence. This module registers physical/logical sources (artifacts),
content identity for those sources, and typed provenance edges from artifacts to
canonical objects. It never creates, mutates or promotes canonical objects; it
performs no persistence (Book II), retrieval (Bloc I.4), market calculation, LLM,
commerce or UI behavior.
"""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalRegistry,
    EvidenceStatus,
    ObjectType,
)


class ArtifactClass(str, Enum):
    """Frozen default source/artifact classes (taxonomy §16 ARTIFACT + Bloc I.2.1)."""

    PDF = "PDF"
    MARKDOWN = "MARKDOWN"
    TXT = "TXT"
    PINE = "PINE"
    CSV = "CSV"
    XLSX = "XLSX"
    VISUAL = "VISUAL"
    NOTEBOOK = "NOTEBOOK"
    SCRIPT = "SCRIPT"
    CONVERSATION_DERIVED = "CONVERSATION_DERIVED"
    EXTERNAL_REFERENCE = "EXTERNAL_REFERENCE"


DEFAULT_ARTIFACT_CLASSES: tuple[str, ...] = tuple(c.value for c in ArtifactClass)

# Visuals and conversation-derived sources are provenance/teaching support only.
# They can never constitute independent empirical support (I.2.4, I.2.5).
NON_EMPIRICAL_ARTIFACT_CLASSES: frozenset[str] = frozenset(
    {
        ArtifactClass.VISUAL.value,
        ArtifactClass.CONVERSATION_DERIVED.value,
    }
)

# Source states at which a non-visual, non-conversation source has actually been
# examined/verified and can therefore carry empirical support (I.2.4/I.2.5).
_EMPIRICAL_SOURCE_STATES: frozenset[str] = frozenset(
    {"READ", "VERIFIED", "MATERIALIZED"}
)

_CLASS_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
_CONTENT_IDENTITY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ArtifactClassRegistry:
    """Extensible registry of registrable artifact classes.

    The frozen defaults cannot be removed or overwritten; additional classes may
    be registered by governance/operator decision without editing frozen code.
    """

    def __init__(self, classes: Iterable[str] = DEFAULT_ARTIFACT_CLASSES) -> None:
        self._classes: dict[str, None] = {}
        for name in classes:
            self._validate_name(name)
            self._classes[name] = None

    @staticmethod
    def _validate_name(name: str) -> None:
        if not _CLASS_NAME_RE.fullmatch(name):
            raise ValueError(f"invalid artifact class name: {name!r}")

    def register(self, name: str) -> None:
        self._validate_name(name)
        if name in self._classes:
            raise ValueError(f"duplicate artifact class: {name}")
        self._classes[name] = None

    def members(self) -> tuple[str, ...]:
        return tuple(sorted(self._classes))

    def __contains__(self, name: object) -> bool:
        return name in self._classes

    def __len__(self) -> int:
        return len(self._classes)


class SourceState(str, Enum):
    """Explicit provenance resolution states (I.2.5).

    MISSING and PARTIAL are honest unresolved states. A search miss is never
    proof that an artifact never existed.
    """

    LOCATED = "LOCATED"
    READ = "READ"
    VERIFIED = "VERIFIED"
    MATERIALIZED = "MATERIALIZED"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    CONVERSATION_DERIVED = "CONVERSATION_DERIVED"


_ALLOWED_SOURCE_TRANSITIONS: dict[SourceState, set[SourceState]] = {
    SourceState.LOCATED: {
        SourceState.READ,
        SourceState.VERIFIED,
        SourceState.MATERIALIZED,
        SourceState.PARTIAL,
        SourceState.MISSING,
    },
    SourceState.READ: {
        SourceState.VERIFIED,
        SourceState.MATERIALIZED,
        SourceState.PARTIAL,
        SourceState.MISSING,
    },
    SourceState.VERIFIED: {SourceState.MATERIALIZED},
    SourceState.MATERIALIZED: {SourceState.VERIFIED},
    SourceState.PARTIAL: {
        SourceState.LOCATED,
        SourceState.READ,
        SourceState.VERIFIED,
        SourceState.MATERIALIZED,
        SourceState.MISSING,
    },
    # A miss stays recoverable: later rediscovery moves MISSING -> LOCATED/PARTIAL.
    SourceState.MISSING: {SourceState.LOCATED, SourceState.PARTIAL},
    # Conversation-derived material never becomes VERIFIED directly; it can only
    # be superseded by locating/materializing a physical source, or go PARTIAL/MISSING.
    SourceState.CONVERSATION_DERIVED: {
        SourceState.LOCATED,
        SourceState.MATERIALIZED,
        SourceState.PARTIAL,
        SourceState.MISSING,
    },
}


def validate_source_state_transition(current: SourceState, target: SourceState) -> None:
    if current == target:
        return
    if target not in _ALLOWED_SOURCE_TRANSITIONS.get(current, set()):
        raise ValueError(
            f"illegal source state transition: {current.value} -> {target.value}"
        )


class MaterializationState(str, Enum):
    NOT_MATERIALIZED = "NOT_MATERIALIZED"
    PARTIAL = "PARTIAL"
    MATERIALIZED = "MATERIALIZED"


def compute_content_identity(content: bytes) -> str:
    """Deterministic content identity for deterministic underlying content."""
    return "sha256:" + hashlib.sha256(content).hexdigest()


def derive_artifact_id(source_class: str, identity: str) -> str:
    """Deterministic artifact ID from (source class, content identity)."""
    token = re.sub(r"[^A-Z0-9]", "", source_class.upper())
    if not token:
        raise ValueError(f"cannot derive artifact id from class {source_class!r}")
    digest = identity.rsplit(":", 1)[-1].upper()
    return f"ART.{token}.{digest[:24]}"


class Artifact(BaseModel):
    """A registered source/artifact. Artifacts point to objects; they are not
    evidence and never become evidence by being registered."""

    model_config = ConfigDict(frozen=True)

    artifact_id: str
    source_class: str
    title: str = ""
    source_generation: str = ""
    version: str | None = None
    locator: str = ""
    content_identity: str | None = None
    source_state: SourceState = SourceState.LOCATED
    created_at: str | None = None
    observed_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("artifact_id")
    @classmethod
    def validate_artifact_id(cls, value: str) -> str:
        cid = CanonicalId.parse(value)
        if cid.object_type is not ObjectType.ARTIFACT:
            raise ValueError("expected ARTIFACT id")
        return value

    @field_validator("source_class")
    @classmethod
    def validate_source_class(cls, value: str) -> str:
        if not _CLASS_NAME_RE.fullmatch(value):
            raise ValueError(f"invalid artifact class name: {value!r}")
        return value

    @field_validator("content_identity")
    @classmethod
    def validate_content_identity(cls, value: str | None) -> str | None:
        if value is not None and not _CONTENT_IDENTITY_RE.fullmatch(value):
            raise ValueError("content identity must be 'sha256:<64 hex>'")
        return value

    @model_validator(mode="after")
    def validate_missing_has_no_content(self) -> "Artifact":
        if self.source_state is SourceState.MISSING and self.content_identity is not None:
            raise ValueError("a MISSING source cannot carry content identity")
        return self

    @property
    def materialization_state(self) -> MaterializationState:
        if self.content_identity is None:
            return MaterializationState.NOT_MATERIALIZED
        if self.source_state is SourceState.PARTIAL:
            return MaterializationState.PARTIAL
        return MaterializationState.MATERIALIZED


class ArtifactRegistry:
    """In-memory artifact registry. Persistence belongs to Book II."""

    def __init__(self, classes: ArtifactClassRegistry | None = None) -> None:
        self.classes = classes if classes is not None else ArtifactClassRegistry()
        self._artifacts: dict[str, Artifact] = {}
        self._content_index: dict[tuple[str, str], str] = {}

    def register_class(self, name: str) -> None:
        self.classes.register(name)

    def add(self, artifact: Artifact) -> None:
        if artifact.source_class not in self.classes:
            raise ValueError(f"unknown artifact class: {artifact.source_class}")
        key = artifact.artifact_id
        if key in self._artifacts:
            raise ValueError(f"duplicate artifact id: {key}")
        if artifact.content_identity is not None:
            content_key = (artifact.content_identity, artifact.locator)
            if content_key in self._content_index:
                raise ValueError(
                    "duplicate artifact content identity: "
                    f"{artifact.content_identity} already registered at locator "
                    f"{artifact.locator!r} as {self._content_index[content_key]}"
                )
            self._content_index[content_key] = key
        self._artifacts[key] = artifact

    def get(self, artifact_id: str) -> Artifact:
        try:
            return self._artifacts[artifact_id]
        except KeyError as exc:
            raise KeyError(f"unknown artifact id: {artifact_id}") from exc

    def set_source_state(self, artifact_id: str, target: SourceState) -> Artifact:
        current = self.get(artifact_id)
        validate_source_state_transition(current.source_state, target)
        if target is SourceState.MISSING and current.content_identity is not None:
            raise ValueError("a MISSING source cannot carry content identity")
        updated = current.model_copy(update={"source_state": target})
        self._artifacts[artifact_id] = updated
        return updated

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._artifacts))

    def __contains__(self, artifact_id: object) -> bool:
        return artifact_id in self._artifacts

    def __len__(self) -> int:
        return len(self._artifacts)


class ProvenanceRelation(str, Enum):
    """Typed artifact -> object provenance relations (I.2.3).

    These describe PHYSICAL ARTIFACT provenance, never concept/model lineage
    (which stays with object -> object LINEAGE references in the I.1 kernel).
    """

    SUPPORTS = "SUPPORTS"
    DEFINES = "DEFINES"
    IMPLEMENTS = "IMPLEMENTS"
    VISUALIZES = "VISUALIZES"
    DERIVED_FROM = "DERIVED_FROM"
    SUPERSEDES = "SUPERSEDES"


class ProvenanceEdge(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: str
    object_id: str
    relation: ProvenanceRelation
    note: str = ""

    @model_validator(mode="after")
    def validate_endpoints(self) -> "ProvenanceEdge":
        source = CanonicalId.parse(self.artifact_id)
        if source.object_type is not ObjectType.ARTIFACT:
            raise ValueError("provenance edge source must be an ARTIFACT id")
        CanonicalId.parse(self.object_id)
        return self


class SupportClassification(str, Enum):
    NO_SOURCE = "NO_SOURCE"
    EMPIRICAL = "EMPIRICAL"
    VISUAL_ONLY = "VISUAL_ONLY"
    CONVERSATION_DERIVED_ONLY = "CONVERSATION_DERIVED_ONLY"
    MIXED_NON_EMPIRICAL = "MIXED_NON_EMPIRICAL"
    NOT_YET_READ = "NOT_YET_READ"


def classify_support(sources: Iterable[Artifact]) -> SupportClassification:
    """Classify the support an object's sources provide.

    Visual and conversation-derived sources are never independent empirical
    support, regardless of source state (VISUAL != statistical proof).
    """
    artifacts = list(sources)
    if not artifacts:
        return SupportClassification.NO_SOURCE
    empirical = [
        a
        for a in artifacts
        if a.source_class not in NON_EMPIRICAL_ARTIFACT_CLASSES
        and a.source_state.value in _EMPIRICAL_SOURCE_STATES
    ]
    if empirical:
        return SupportClassification.EMPIRICAL
    classes = {a.source_class for a in artifacts}
    if classes == {ArtifactClass.VISUAL.value}:
        return SupportClassification.VISUAL_ONLY
    if classes == {ArtifactClass.CONVERSATION_DERIVED.value}:
        return SupportClassification.CONVERSATION_DERIVED_ONLY
    if classes <= {ArtifactClass.VISUAL.value, ArtifactClass.CONVERSATION_DERIVED.value}:
        return SupportClassification.MIXED_NON_EMPIRICAL
    return SupportClassification.NOT_YET_READ


class ClaimChainStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NO_EVIDENCE_REFERENCE = "NO_EVIDENCE_REFERENCE"
    EVIDENCE_WITHOUT_SOURCE = "EVIDENCE_WITHOUT_SOURCE"
    NON_EMPIRICAL_SOURCE = "NON_EMPIRICAL_SOURCE"


def is_numerical_claim(obj: CanonicalObject) -> bool:
    """A CLAIM carrying a result/statistic value must route to source/artifact.

    Bloc I.3 stamps launch claims with `numerical: true` or a `result` value;
    I.2 only audits the chain.
    """
    if obj.canonical_id.object_type is not ObjectType.CLAIM:
        return False
    metadata = obj.metadata
    if metadata.get("numerical") is True:
        return True
    for key in ("result", "statistic"):
        value = metadata.get(key)
        if value is not None and value != "":
            return True
    return False


class ProvenanceRegistry:
    """Artifact + provenance-edge registry with deterministic audit reporting.

    In-memory only. Persistence belongs to Book II; retrieval belongs to I.4.
    """

    def __init__(
        self,
        canonical: CanonicalRegistry,
        artifacts: ArtifactRegistry | None = None,
    ) -> None:
        self.canonical = canonical
        self.artifacts = artifacts if artifacts is not None else ArtifactRegistry()
        self._edges: dict[tuple[str, str, str], ProvenanceEdge] = {}

    def add_artifact(self, artifact: Artifact) -> None:
        """Registering an artifact never touches the canonical registry."""
        self.artifacts.add(artifact)

    def add_edge(self, edge: ProvenanceEdge) -> None:
        if edge.artifact_id not in self.artifacts:
            raise ValueError(f"unknown provenance artifact: {edge.artifact_id}")
        try:
            self.canonical.get(edge.object_id)
        except KeyError as exc:
            raise ValueError(f"unknown canonical object: {edge.object_id}") from exc
        key = (edge.artifact_id, edge.object_id, edge.relation.value)
        if key in self._edges:
            raise ValueError(
                f"duplicate provenance edge: {key[0]} -[{key[2]}]-> {key[1]}"
            )
        self._edges[key] = edge

    def edges(self) -> tuple[ProvenanceEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def edges_for_object(self, object_id: str) -> tuple[ProvenanceEdge, ...]:
        return tuple(
            edge
            for key, edge in sorted(self._edges.items())
            if key[1] == object_id
        )

    def edges_from_artifact(self, artifact_id: str) -> tuple[ProvenanceEdge, ...]:
        return tuple(
            edge
            for key, edge in sorted(self._edges.items())
            if key[0] == artifact_id
        )

    def support_classification(self, object_id: str) -> SupportClassification:
        sources = [
            self.artifacts.get(edge.artifact_id)
            for edge in self.edges_for_object(object_id)
        ]
        return classify_support(sources)

    def independent_empirical_support(self, object_id: str) -> bool:
        return self.support_classification(object_id) is SupportClassification.EMPIRICAL

    def _reachable_sources(
        self, object_id: str, visited: set[str] | None = None
    ) -> list[Artifact]:
        """Sources reachable from an object through its provenance edges and its
        typed references (the CLAIM -> EVIDENCE -> SOURCE chain), cycle-guarded.
        """
        if visited is None:
            visited = set()
        if object_id in visited:
            return []
        visited.add(object_id)
        sources = [
            self.artifacts.get(edge.artifact_id)
            for edge in self.edges_for_object(object_id)
        ]
        try:
            obj = self.canonical.get(object_id)
        except KeyError:
            return sources
        for ref in obj.references:
            sources.extend(self._reachable_sources(ref.target_id, visited))
        return sources

    def _evidence_ids(self, claim: CanonicalObject) -> tuple[str, ...]:
        return tuple(
            ref.target_id
            for ref in claim.references
            if CanonicalId.parse(ref.target_id).object_type is ObjectType.EVIDENCE
        )

    def claim_source_chain(
        self, claim_id: str
    ) -> tuple[ClaimChainStatus, SupportClassification]:
        """Resolve CLAIM -> EVIDENCE -> SOURCE/ARTIFACT for one claim."""
        claim = self.canonical.get(claim_id)
        if claim.canonical_id.object_type is not ObjectType.CLAIM:
            raise ValueError(f"not a claim: {claim_id}")
        evidence_ids = self._evidence_ids(claim)
        if not evidence_ids:
            return ClaimChainStatus.NO_EVIDENCE_REFERENCE, SupportClassification.NO_SOURCE
        sources = [
            self.artifacts.get(edge.artifact_id)
            for evidence_id in evidence_ids
            for edge in self.edges_for_object(evidence_id)
        ]
        if not sources:
            return (
                ClaimChainStatus.EVIDENCE_WITHOUT_SOURCE,
                SupportClassification.NO_SOURCE,
            )
        classification = classify_support(sources)
        status = (
            ClaimChainStatus.RESOLVED
            if classification is SupportClassification.EMPIRICAL
            else ClaimChainStatus.NON_EMPIRICAL_SOURCE
        )
        return status, classification

    def audit(self) -> "ProvenanceAuditReport":
        object_ids = self.canonical.ids()
        objects = {oid: self.canonical.get(oid) for oid in object_ids}
        artifact_ids = self.artifacts.ids()
        edge_list = self.edges()

        incoming: dict[str, int] = {oid: 0 for oid in object_ids}
        for edge in edge_list:
            if edge.object_id in incoming:
                incoming[edge.object_id] += 1

        classifications = {
            oid: self.support_classification(oid) for oid in object_ids
        }
        reachable = {oid: self._reachable_sources(oid) for oid in object_ids}

        orphan_objects = tuple(
            sorted(o for o in object_ids if not reachable[o])
        )
        evidence_without_source = tuple(
            sorted(
                o
                for o in object_ids
                if objects[o].canonical_id.object_type is ObjectType.EVIDENCE
                and incoming[o] == 0
            )
        )

        numerical_without_chain: list[str] = []
        numerical_non_empirical: list[str] = []
        for oid in object_ids:
            if not is_numerical_claim(objects[oid]):
                continue
            status, classification = self.claim_source_chain(oid)
            if status in (
                ClaimChainStatus.NO_EVIDENCE_REFERENCE,
                ClaimChainStatus.EVIDENCE_WITHOUT_SOURCE,
            ):
                numerical_without_chain.append(oid)
            elif status is ClaimChainStatus.NON_EMPIRICAL_SOURCE:
                numerical_non_empirical.append(f"{oid}:{classification.value}")

        unresolved_sources: list[dict[str, str]] = []
        partial_sources: list[str] = []
        conversation_derived_sources: list[str] = []
        artifacts_by_source_state: dict[str, int] = {s.value: 0 for s in SourceState}
        for aid in artifact_ids:
            artifact = self.artifacts.get(aid)
            artifacts_by_source_state[artifact.source_state.value] += 1
            if artifact.source_state is SourceState.PARTIAL:
                partial_sources.append(aid)
            if artifact.source_state is SourceState.CONVERSATION_DERIVED:
                conversation_derived_sources.append(aid)
            if artifact.source_state in (
                SourceState.MISSING,
                SourceState.PARTIAL,
                SourceState.CONVERSATION_DERIVED,
            ):
                unresolved_sources.append(
                    {"artifact_id": aid, "source_state": artifact.source_state.value}
                )
        unresolved_sources.sort(key=lambda entry: entry["artifact_id"])

        historical_unresolved: list[tuple[str, str]] = []
        for oid in object_ids:
            obj = objects[oid]
            if obj.status is not EvidenceStatus.HISTORICAL:
                continue
            for ref in obj.references:
                if ref.allow_unresolved_historical and ref.target_id not in objects:
                    historical_unresolved.append(
                        (oid, f"{oid} -> {ref.target_id} ({ref.relation})")
                    )
        historical_unresolved.sort()
        historical_unresolved_references = tuple(text for _, text in historical_unresolved)

        visual_only_support = tuple(
            sorted(
                oid
                for oid in object_ids
                if classifications[oid]
                in (SupportClassification.VISUAL_ONLY, SupportClassification.MIXED_NON_EMPIRICAL)
            )
        )
        conversation_derived_support = tuple(
            sorted(
                oid
                for oid in object_ids
                if classifications[oid]
                in (
                    SupportClassification.CONVERSATION_DERIVED_ONLY,
                    SupportClassification.MIXED_NON_EMPIRICAL,
                )
            )
        )

        support_classification_counts: dict[str, int] = {
            classification.value: 0 for classification in SupportClassification
        }
        for classification in classifications.values():
            support_classification_counts[classification.value] += 1

        objects_with_source = sum(1 for oid in object_ids if reachable[oid])
        objects_with_empirical_source = sum(
            1
            for oid in object_ids
            if classify_support(reachable[oid]) is SupportClassification.EMPIRICAL
        )
        source_coverage = {
            "objects_total": len(object_ids),
            "objects_with_source": objects_with_source,
            "objects_without_source": len(object_ids) - objects_with_source,
            "objects_with_empirical_source": objects_with_empirical_source,
        }

        gaps: list[dict[str, str]] = []
        for oid in sorted(numerical_without_chain):
            gaps.append(
                {
                    "kind": "LAUNCH_NUMERICAL_CLAIM_WITHOUT_SOURCE_CHAIN",
                    "target": oid,
                    "detail": "claim -> evidence -> source chain incomplete",
                }
            )
        for entry in sorted(numerical_non_empirical):
            oid, classification = entry.split(":", 1)
            gaps.append(
                {
                    "kind": "LAUNCH_NUMERICAL_CLAIM_WITH_NON_EMPIRICAL_SOURCE",
                    "target": oid,
                    "detail": classification,
                }
            )
        for oid in evidence_without_source:
            gaps.append(
                {
                    "kind": "EVIDENCE_WITHOUT_SOURCE",
                    "target": oid,
                    "detail": "no provenance edge",
                }
            )
        for entry in unresolved_sources:
            gaps.append(
                {
                    "kind": f"{entry['source_state']}_SOURCE",
                    "target": entry["artifact_id"],
                    "detail": "explicit unresolved provenance state",
                }
            )
        for oid, text in historical_unresolved:
            gaps.append(
                {
                    "kind": "UNRESOLVED_HISTORICAL_REFERENCE",
                    "target": oid,
                    "detail": text,
                }
            )
        gaps.sort(key=lambda gap: (gap["kind"], gap["target"], gap["detail"]))

        return ProvenanceAuditReport(
            artifact_count=len(artifact_ids),
            canonical_object_count=len(object_ids),
            provenance_edge_count=len(edge_list),
            source_coverage=source_coverage,
            artifacts_by_source_state=dict(sorted(artifacts_by_source_state.items())),
            orphan_objects=orphan_objects,
            evidence_without_source=evidence_without_source,
            launch_numerical_claims_without_source_chain=tuple(
                sorted(numerical_without_chain)
            ),
            numerical_claims_non_empirical_source=tuple(
                sorted(numerical_non_empirical)
            ),
            unresolved_sources=tuple(unresolved_sources),
            partial_sources=tuple(sorted(partial_sources)),
            conversation_derived_sources=tuple(sorted(conversation_derived_sources)),
            historical_unresolved_references=historical_unresolved_references,
            visual_only_support=visual_only_support,
            conversation_derived_support=conversation_derived_support,
            support_classification_counts=dict(
                sorted(support_classification_counts.items())
            ),
            gaps=tuple(gaps),
        )


class ProvenanceAuditReport(BaseModel):
    """Deterministic provenance audit output. No timestamps; sorted collections."""

    model_config = ConfigDict(frozen=True)

    schema_version: str = "FORGE_PROVENANCE_AUDIT_V1"
    artifact_count: int
    canonical_object_count: int
    provenance_edge_count: int
    source_coverage: dict[str, int]
    artifacts_by_source_state: dict[str, int]
    orphan_objects: tuple[str, ...]
    evidence_without_source: tuple[str, ...]
    launch_numerical_claims_without_source_chain: tuple[str, ...]
    numerical_claims_non_empirical_source: tuple[str, ...]
    unresolved_sources: tuple[dict[str, str], ...]
    partial_sources: tuple[str, ...]
    conversation_derived_sources: tuple[str, ...]
    historical_unresolved_references: tuple[str, ...]
    visual_only_support: tuple[str, ...]
    conversation_derived_support: tuple[str, ...]
    support_classification_counts: dict[str, int]
    gaps: tuple[dict[str, str], ...]

    def to_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    def content_hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()
