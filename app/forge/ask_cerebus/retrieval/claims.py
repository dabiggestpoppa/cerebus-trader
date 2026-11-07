"""Claim -> Evidence -> Provenance join over Book I navigation."""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.retrieval.query import RetrievalQuery
from app.forge.retrieval.service import RetrievalService

from .enums import EvidenceJoinStatus, LimitationCode, RejectionClass
from .refs import ClaimRef, EvidenceRef, Limitation


@dataclass
class ClaimJoin:
    claim_refs: tuple[ClaimRef, ...] = ()
    evidence_refs: tuple[EvidenceRef, ...] = ()
    limitations: tuple[Limitation, ...] = ()
    rejections: tuple[RejectionClass, ...] = ()
    missing_evidence: tuple[str, ...] = ()


class ClaimEvidenceJoiner:
    def __init__(self, service: RetrievalService) -> None:
        self._service = service

    def join(
        self,
        claim_ids: tuple[str, ...],
        principal,
        context,
        *,
        correlation_id: str = "",
    ) -> ClaimJoin:
        out = ClaimJoin()
        for claim_id in dict.fromkeys(claim_ids):
            response = self._service.retrieve(
                principal,
                context,
                RetrievalQuery(canonical_id=claim_id),
                correlation_id=correlation_id,
            )
            if response.denied:
                out.limitations = out.limitations + (
                    Limitation(LimitationCode.POLICY_DENIED),
                )
                out.rejections = out.rejections + (RejectionClass.POLICY_DENIED,)
                continue
            if not response.results:
                out.rejections = out.rejections + (RejectionClass.NOT_FOUND,)
                continue
            record = self._service.load_record(
                principal, context, claim_id, correlation_id=correlation_id
            )
            if record is None:
                out.limitations = out.limitations + (
                    Limitation(LimitationCode.POLICY_DENIED),
                )
                continue
            chain = self._service.navigate(
                principal, context, claim_id, correlation_id=correlation_id
            )
            evidence_ids = tuple(dict.fromkeys(chain.evidence_ids))
            identity = record.structured.claim_identity
            result_value = record.retrieval_text or None
            if chain.denied:
                out.limitations = out.limitations + (
                    Limitation(LimitationCode.POLICY_DENIED),
                )
            if not evidence_ids:
                out.limitations = out.limitations + (
                    Limitation(LimitationCode.EVIDENCE_INSUFFICIENT, claim_id),
                )
                out.missing_evidence = out.missing_evidence + (claim_id,)
            join_status = (
                EvidenceJoinStatus.VERIFIED
                if chain.supported
                else EvidenceJoinStatus.UNSUPPORTED
            )
            out.claim_refs = out.claim_refs + (
                ClaimRef(
                    claim_id=claim_id,
                    model_ids=(),
                    model_versions=(record.canonical_version,),
                    identity_key=(
                        identity.comparison_key() if identity is not None else None
                    ),
                    status=record.status.value,
                    evidence_ids=evidence_ids,
                    generation=record.conflict.generation,
                    result_value=result_value,
                    join_status=join_status,
                ),
            )
            for evidence_id in evidence_ids:
                evidence = self._service.load_record(
                    principal, context, evidence_id, correlation_id=correlation_id
                )
                if evidence is None:
                    continue
                out.evidence_refs = out.evidence_refs + (
                    EvidenceRef(
                        evidence_id=evidence_id,
                        claim_ids=(claim_id,),
                        status=evidence.status.value,
                        provenance_ids=tuple(
                            link.artifact_id for link in evidence.provenance
                        ),
                        support_classification=evidence.support.classification,
                        gaps=evidence.support.gaps,
                        oos_status="UNAVAILABLE",
                    ),
                )
        return out


__all__ = ["ClaimJoin", "ClaimEvidenceJoiner"]
