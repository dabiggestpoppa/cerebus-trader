"""IV.5 public entry point: draft and package in, one terminal outcome out."""

from __future__ import annotations

from app.forge.ask_cerebus.answer.admission import (
    Admission,
    AdmissionFailure,
    AnswerPolicy,
    admit,
)
from app.forge.ask_cerebus.answer.citations import claim_sources, collect
from app.forge.ask_cerebus.answer.compilers import answer_limitations, compile_answer
from app.forge.ask_cerebus.answer.enums import AnswerDepth, AnswerOutcome
from app.forge.ask_cerebus.answer.record import answer_id, as_of_value, build_record
from app.forge.ask_cerebus.answer.resolution import PackageIndex
from app.forge.ask_cerebus.answer.schema import (
    AnswerNumber,
    GovernedAnswerRefusal,
    ValidatedAnswer,
)
from app.forge.ask_cerebus.answer.uncertainty import (
    failure_codes,
    refusal_detail,
    refusal_for,
)
from app.forge.ask_cerebus.answer.validators import (
    Finding,
    PreparedClaim,
    normalize,
    run_validators,
)
from app.forge.ask_cerebus.context.schema import AuthorizedContextPackage
from app.forge.ask_cerebus.llm_gateway.draft import GatewayDraft


def prepare_claims(admission: Admission) -> tuple[PreparedClaim, ...]:
    prepared: list[PreparedClaim] = []
    for position, claim in enumerate(admission.draft.claims, start=1):
        unresolved = tuple(
            ref for ref in claim.source_refs if admission.index.resolve(ref) is None
        )
        prepared.append(
            PreparedClaim(
                claim_id=f"AC-{position:02d}",
                draft=claim,
                sources=claim_sources(admission.index, claim.source_refs),
                unresolved_refs=unresolved,
            )
        )
    return tuple(prepared)


def _answer_numbers(admission: Admission) -> tuple[AnswerNumber, ...]:
    out: list[AnswerNumber] = []
    for link in admission.draft.numbers:
        out.append(
            AnswerNumber(
                value_text=link.value_text,
                unit=link.unit,
                source_ref_id=link.source_ref_id,
                normalized=normalize(link.value_text),
            )
        )
    return tuple(out)


def _validated_answer(
    admission: Admission, prepared: tuple[PreparedClaim, ...]
) -> ValidatedAnswer:
    citations, _unresolved = collect(admission.index, admission.draft.citations)
    sections, claims = compile_answer(admission, prepared, citations)
    cited_refs = tuple(citation.source_ref_id for citation in citations)
    identifier = answer_id(
        admission=admission,
        outcome=AnswerOutcome.VALIDATED_ANSWER,
        cited_refs=cited_refs,
        validation_codes=(),
    )
    record = build_record(
        admission=admission,
        outcome=AnswerOutcome.VALIDATED_ANSWER,
        identifier=identifier,
        citations=citations,
        claims=claims,
    )
    return ValidatedAnswer(
        answer_id=identifier,
        depth=admission.depth,
        sections=sections,
        claims=claims,
        citations=citations,
        numbers=_answer_numbers(admission),
        limitations=answer_limitations(admission),
        as_of=as_of_value(admission),
        record=record,
    )


def _governed_refusal(
    admission: Admission,
    findings: tuple[Finding, ...],
) -> GovernedAnswerRefusal:
    code = refusal_for(findings)
    codes = failure_codes(findings)
    identifier = answer_id(
        admission=admission,
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        cited_refs=(),
        validation_codes=codes,
    )
    record = build_record(
        admission=admission,
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        identifier=identifier,
        citations=(),
        validation_codes=codes,
        refusal_code=code,
    )
    return GovernedAnswerRefusal(
        answer_id=identifier,
        code=code,
        detail=refusal_detail(code, findings),
        depth=admission.depth,
        findings=codes,
        record=record,
        limitations=answer_limitations(admission),
    )


def _admission_refusal(
    draft: object,
    package: object,
    failure: AdmissionFailure,
    policy: AnswerPolicy,
) -> GovernedAnswerRefusal | ValidatedAnswer:
    """Refuse before any validation, still producing a safe record."""

    if not isinstance(draft, GatewayDraft):
        raise TypeError("the answer layer only accepts a GatewayDraft")

    index = PackageIndex.build(package) if isinstance(package, AuthorizedContextPackage) else PackageIndex(
        package=AuthorizedContextPackage(
            context_contract_version="",
            query_plan_id="",
            retrieval_bundle_id="",
            outcome=None,  # type: ignore[arg-type]
        ),
        items=(),
        by_ref={},
    )
    try:
        depth = AnswerDepth(str(draft.depth).upper())
    except ValueError:
        depth = AnswerDepth.OPERATOR

    admission = Admission(draft=draft, index=index, depth=depth, policy=policy)
    finding = Finding(failure.code, failure.detail)
    code = refusal_for((finding,))
    codes = failure_codes((finding,))
    identifier = answer_id(
        admission=admission,
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        cited_refs=(),
        validation_codes=codes,
    )
    record = build_record(
        admission=admission,
        outcome=AnswerOutcome.GOVERNED_REFUSAL,
        identifier=identifier,
        citations=(),
        validation_codes=codes,
        refusal_code=code,
    )
    return GovernedAnswerRefusal(
        answer_id=identifier,
        code=code,
        detail=refusal_detail(code, (finding,)),
        depth=depth,
        findings=codes,
        record=record,
        limitations=answer_limitations(admission),
    )


def validate_answer(
    draft: object,
    package: object,
    *,
    policy: AnswerPolicy | None = None,
) -> ValidatedAnswer | GovernedAnswerRefusal:
    """Validate a gateway draft against its own authorized package."""

    effective = policy or AnswerPolicy()
    admitted = admit(draft, package, policy=effective)
    if isinstance(admitted, AdmissionFailure):
        return _admission_refusal(draft, package, admitted, effective)
    prepared = prepare_claims(admitted)
    findings = run_validators(admitted, prepared)
    if findings:
        return _governed_refusal(admitted, findings)
    return _validated_answer(admitted, prepared)


__all__ = ["validate_answer", "prepare_claims"]
