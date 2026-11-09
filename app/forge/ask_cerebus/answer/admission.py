"""IV.5 input admission: exactly one unvalidated draft with its own package."""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.ask_cerebus.answer.enums import AnswerDepth, ValidationCode
from app.forge.ask_cerebus.answer.resolution import PackageIndex
from app.forge.ask_cerebus.answer.versions import ANSWER_POLICY_V1
from app.forge.ask_cerebus.context.enums import ContextOutcome
from app.forge.ask_cerebus.context.schema import (
    AuthorizedContextManifest,
    AuthorizedContextPackage,
)
from app.forge.ask_cerebus.context.versions import (
    CONTEXT_CONTRACT_V1,
    CONTEXT_MANIFEST_V1,
    SUPPORTED_CONTEXT_CONTRACT_VERSIONS,
)
from app.forge.ask_cerebus.llm_gateway.draft import GatewayDraft
from app.forge.ask_cerebus.llm_gateway.enums import DraftStatus


@dataclass(frozen=True)
class AnswerPolicy:
    """Declared, versioned answer policy.

    The defaults are deliberately conservative: no silent defaults for missing
    freshness, a bounded quote allowance and a bulk-reproduction ceiling. The
    production materiality and licensing decisions remain F3/F4.
    """

    version: str = ANSWER_POLICY_V1
    quote_char_limit: int = 400
    corpus_bulk_limit: int = 2000
    require_as_of_for_current: bool = True

    def payload(self) -> dict[str, object]:
        return {
            "version": self.version,
            "quote_char_limit": self.quote_char_limit,
            "corpus_bulk_limit": self.corpus_bulk_limit,
            "require_as_of_for_current": self.require_as_of_for_current,
        }


@dataclass(frozen=True)
class Admission:
    draft: GatewayDraft
    index: PackageIndex
    depth: AnswerDepth
    policy: AnswerPolicy


@dataclass(frozen=True)
class AdmissionFailure:
    code: ValidationCode
    detail: str


def _fail(code: ValidationCode, detail: str) -> AdmissionFailure:
    return AdmissionFailure(code=code, detail=detail)


def admit(
    draft: object,
    package: object,
    *,
    policy: AnswerPolicy | None = None,
) -> Admission | AdmissionFailure:
    if not isinstance(draft, GatewayDraft):
        return _fail(ValidationCode.DRAFT_NOT_UNVALIDATED, "input is not a GatewayDraft")
    if draft.status is not DraftStatus.UNVALIDATED:
        return _fail(
            ValidationCode.DRAFT_NOT_UNVALIDATED,
            "only an UNVALIDATED gateway draft may enter the answer layer",
        )

    if not isinstance(package, AuthorizedContextPackage):
        return _fail(
            ValidationCode.ANSWER_CONTEXT_REFUSED,
            "originating authorized context package is required",
        )
    if package.context_contract_version not in SUPPORTED_CONTEXT_CONTRACT_VERSIONS:
        return _fail(
            ValidationCode.ANSWER_CONTEXT_REFUSED,
            "unsupported context contract version",
        )
    if package.context_contract_version != CONTEXT_CONTRACT_V1:
        return _fail(ValidationCode.ANSWER_CONTEXT_REFUSED, "context contract not admitted")
    if package.outcome is ContextOutcome.REFUSED:
        return _fail(ValidationCode.ANSWER_CONTEXT_REFUSED, "upstream context was refused")

    manifest = package.manifest
    if not isinstance(manifest, AuthorizedContextManifest):
        return _fail(ValidationCode.ANSWER_MANIFEST_INVALID, "authorized manifest is required")
    if (
        manifest.manifest_version != CONTEXT_MANIFEST_V1
        or manifest.context_contract_version != CONTEXT_CONTRACT_V1
    ):
        return _fail(ValidationCode.ANSWER_MANIFEST_INVALID, "manifest version is not admitted")

    try:
        digest_ok = manifest.compute_digest() == manifest.manifest_digest
        package_ok = package.compute_id() == package.package_id
    except Exception:
        return _fail(
            ValidationCode.ANSWER_MANIFEST_INVALID, "manifest digest could not be verified"
        )
    if not digest_ok:
        return _fail(
            ValidationCode.ANSWER_MANIFEST_INVALID, "manifest digest does not reconcile"
        )
    if not package_ok:
        return _fail(ValidationCode.ANSWER_IDENTITY_MISMATCH, "package identity does not reconcile")

    if (
        draft.package_id != package.package_id
        or draft.manifest_id != manifest.manifest_digest
        or draft.query_plan_id != package.query_plan_id
        or draft.query_plan_id != manifest.query_plan_id
    ):
        return _fail(
            ValidationCode.ANSWER_IDENTITY_MISMATCH,
            "draft does not belong to the supplied package, manifest and query plan",
        )

    try:
        depth = AnswerDepth(str(draft.depth).upper())
    except ValueError:
        return _fail(ValidationCode.ANSWER_DEPTH_UNSUPPORTED, "answer depth is not supported")

    if not package.sections:
        return _fail(ValidationCode.ANSWER_CONTEXT_REFUSED, "package carries no sections")

    return Admission(
        draft=draft,
        index=PackageIndex.build(package),
        depth=depth,
        policy=policy or AnswerPolicy(),
    )


__all__ = ["AnswerPolicy", "Admission", "AdmissionFailure", "admit"]
