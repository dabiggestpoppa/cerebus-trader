"""Structured, header-first canonical resolution.

Identity is exact and source-backed. A model token may select a canonical
namespace (``MOD.XAU.GAME.*``), but it never fuzzy-matches a different object.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.forge.ask_cerebus.interpreter.enums import EntityKind
from app.forge.canonical import EvidenceStatus, ObjectType, ProductExposure
from app.forge.retrieval.aliases import HISTORICAL_ALIASES
from app.forge.retrieval.objects import RetrievalObject
from app.forge.retrieval.query import RetrievalQuery
from app.forge.retrieval.service import RetrievalService
from app.forge.setup_engine.contracts import SetupEligibility, SetupSurface
from app.forge.setup_engine.registry import SetupRegistry, project_status

from .enums import LimitationCode, RefusalCode, RejectionClass
from .query_builder import ResolverTargets
from .refs import CanonicalRef, Limitation, Refusal


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def _enum_text(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _canonical_setup_id(value: str) -> str:
    if value.startswith("SETUP."):
        return "SET." + value[len("SETUP."):]
    return value


def _header_matches(header, token: str) -> bool:
    if token.startswith("MOD."):
        return header.object_id == token
    prefix = f"MOD.{token}"
    return header.object_id == prefix or header.object_id.startswith(prefix + ".")


@dataclass
class StructuredResolution:
    canonical_refs: tuple[CanonicalRef, ...] = ()
    records: tuple[RetrievalObject, ...] = ()
    claim_ids: tuple[str, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    refusals: tuple[Refusal, ...] = ()
    rejections: tuple[RejectionClass, ...] = ()
    unresolved: tuple[str, ...] = ()
    denied_ids: tuple[str, ...] = ()

    def add_ref(self, ref: CanonicalRef) -> None:
        if all(existing.object_id != ref.object_id for existing in self.canonical_refs):
            self.canonical_refs = self.canonical_refs + (ref,)

    def add_record(self, record: RetrievalObject) -> None:
        if all(existing.object_id != record.object_id for existing in self.records):
            self.records = self.records + (record,)

    def add_claim(self, claim_id: str) -> None:
        if claim_id not in self.claim_ids:
            self.claim_ids = self.claim_ids + (claim_id,)


class StructuredResolver:
    def __init__(
        self,
        service: RetrievalService,
        registry: SetupRegistry | None = None,
    ) -> None:
        if not isinstance(service, RetrievalService):
            raise TypeError("service must be a RetrievalService")
        self._service = service
        self._registry = registry or SetupRegistry()
        self._generation = service.index.require()

    @property
    def service(self) -> RetrievalService:
        return self._service

    def candidate_headers(self, plan) -> tuple:
        """Read-only safe-header selection. No protected body is loaded here."""

        tokens = build_tokens(plan.model_ids)
        return tuple(
            header
            for header in self._generation.headers
            if header.object_type is ObjectType.MODEL
            and any(_header_matches(header, token) for token in tokens)
        )

    def resolve(
        self,
        plan,
        targets: ResolverTargets,
        principal,
        context,
        *,
        correlation_id: str = "",
    ) -> StructuredResolution:
        out = StructuredResolution()

        # Safe header selection precedes any body load.
        model_ids = self._model_ids(targets.model_tokens)
        for token in targets.model_tokens:
            if not any(
                self._generation.header(object_id) is not None
                for object_id in model_ids
            ):
                out.unresolved = out.unresolved + (token,)
                out.limitations = out.limitations + (
                    Limitation(LimitationCode.UNRESOLVED_IDENTITY, token),
                )
                out.rejections = out.rejections + (RejectionClass.NOT_FOUND,)

        for object_id in model_ids:
            record = self._load(object_id, principal, context, out, correlation_id)
            if record is None:
                continue
            out.add_ref(self._ref(record))
            out.add_record(record)
            for link in record.related_ids:
                if link.target_id.startswith("CL."):
                    out.add_claim(link.target_id)

        for setup_id in targets.setup_ids:
            self._resolve_setup(setup_id, plan, principal, context, out, correlation_id)

        for term_id in targets.term_ids:
            self._resolve_term(term_id, principal, context, out, correlation_id)

        return out

    def _model_ids(self, tokens: tuple[str, ...]) -> tuple[str, ...]:
        found: list[str] = []
        for token in tokens:
            for header in self._generation.headers:
                if header.object_type is ObjectType.MODEL and _header_matches(header, token):
                    if header.object_id not in found:
                        found.append(header.object_id)
        return tuple(sorted(found))

    def _resolve_setup(
        self, setup_id: str, plan, principal, context, out, correlation_id: str
    ) -> None:
        surface = (
            SetupSurface.RESEARCH
            if getattr(plan.effective_depth, "value", "") == "RESEARCHER"
            else SetupSurface.OPERATOR
        )
        try:
            card = self._registry.card(setup_id)
        except Exception:
            out.unresolved = out.unresolved + (setup_id,)
            out.limitations = out.limitations + (
                Limitation(LimitationCode.UNRESOLVED_IDENTITY, setup_id),
            )
            out.rejections = out.rejections + (RejectionClass.NOT_FOUND,)
            return

        resolution = self._registry.resolve(setup_id, card.version, surface)
        if not resolution.resolved:
            code = getattr(resolution.code, "value", "SETUP_BLOCKED")
            out.refusals = out.refusals + (
                Refusal(
                    RefusalCode.RESEARCH_ONLY_NOT_PRODUCTION
                    if "RESEARCH_ONLY" in code
                    else RefusalCode.AUTOMATION_NOT_APPROVED
                    if "AUTOMATION" in code
                    else RefusalCode.SETUP_BLOCKED,
                    code,
                ),
            )
            out.limitations = out.limitations + (
                Limitation(
                    LimitationCode.RESEARCH_ONLY_NOT_PRODUCTION
                    if "RESEARCH_ONLY" in code
                    else LimitationCode.AUTOMATION_NOT_APPROVED
                    if "AUTOMATION" in code
                    else LimitationCode.SETUP_BLOCKED,
                    setup_id,
                ),
            )
            if resolution.verdict is SetupEligibility.BLOCKED:
                out.rejections = out.rejections + (RejectionClass.STATUS_INELIGIBLE,)
            return

        canonical_id = _canonical_setup_id(setup_id)
        record = self._load(canonical_id, principal, context, out, correlation_id)
        if record is not None:
            out.add_ref(self._ref(record))
            out.add_record(record)
            if record.status in (
                EvidenceStatus.NO_GO,
                EvidenceStatus.PARKED,
                EvidenceStatus.FALSIFIED,
                EvidenceStatus.SUPERSEDED,
            ):
                out.limitations = out.limitations + (
                    Limitation(LimitationCode.NO_GO_ACTIVE, canonical_id),
                )
                out.refusals = out.refusals + (
                    Refusal(RefusalCode.SETUP_BLOCKED, "SETUP_STATUS_REFUSED"),
                )
            for link in record.related_ids:
                if link.target_id.startswith("CL."):
                    out.add_claim(link.target_id)
            return

        # The Setup Card is a governed fallback identity only when the index
        # does not carry a compiled record for it (legacy SETUP/SET mismatch).
        out.add_ref(
            CanonicalRef(
                object_id=canonical_id,
                object_type=ObjectType.SETUP.value,
                version=card.version,
                status=project_status(card.status).value,
                layer="NONE",
                market_scope=card.market_scope,
                exposure=card.exposure.value,
                support_classification="NO_SOURCE",
                generation=card.status.value,
            )
        )

    def _resolve_term(
        self, term_id, principal, context, out, correlation_id: str
    ) -> None:
        header = self._generation.header(term_id)
        if header is None:
            # Exact governed alias fallback: TERM.<slug> only.
            for entry in HISTORICAL_ALIASES:
                if "TERM." + _slug(entry.historical) == term_id:
                    header = self._generation.header(term_id)
                    break
        if header is None:
            out.unresolved = out.unresolved + (term_id,)
            out.rejections = out.rejections + (RejectionClass.NOT_FOUND,)
            return
        record = self._load(term_id, principal, context, out, correlation_id)
        if record is not None:
            out.add_ref(self._ref(record))
            out.add_record(record)

    def _load(self, object_id, principal, context, out, correlation_id) -> RetrievalObject | None:
        response = self._service.retrieve(
            principal,
            context,
            RetrievalQuery(canonical_id=object_id),
            correlation_id=correlation_id,
        )
        if response.denied:
            out.denied_ids = out.denied_ids + (object_id,)
            out.rejections = out.rejections + (RejectionClass.POLICY_DENIED,)
            out.limitations = out.limitations + (
                Limitation(LimitationCode.POLICY_DENIED),
            )
            return None
        if not response.results:
            out.rejections = out.rejections + (RejectionClass.NOT_FOUND,)
            return None
        record = self._service.load_record(
            principal, context, object_id, correlation_id=correlation_id
        )
        return record

    @staticmethod
    def _ref(record: RetrievalObject) -> CanonicalRef:
        return CanonicalRef(
            object_id=record.object_id,
            object_type=record.object_type.value,
            version=record.canonical_version,
            status=record.status.value,
            layer=record.layer.value,
            market_scope=record.market_scope,
            exposure=(
                record.exposure_class.value
                if record.exposure_class is not None
                else "UNKNOWN"
            ),
            support_classification=record.support.classification,
            generation=record.conflict.generation,
        )


def build_tokens(model_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(model_ids))


__all__ = ["StructuredResolver", "StructuredResolution", "build_tokens"]
