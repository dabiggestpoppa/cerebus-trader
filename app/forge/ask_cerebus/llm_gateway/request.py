"""IV.3 package admission and provider-request construction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from app.forge.ask_cerebus.context.enums import (
    ContextOutcome,
    ContextSectionId,
    EpistemicLabel,
    SECTION_ORDER,
    TrustClass,
)
from app.forge.ask_cerebus.context.schema import (
    AuthorizedContextManifest,
    AuthorizedContextPackage,
    ContextItem,
)
from app.forge.ask_cerebus.context.trust import (
    contains_forbidden_words,
    exposure_allowed,
)
from app.forge.ask_cerebus.context.versions import (
    CONTEXT_CONTRACT_V1,
    CONTEXT_MANIFEST_V1,
)
from app.forge.ask_cerebus.interpreter.enums import Depth
from app.forge.ask_cerebus.llm_gateway.budget import context_units
from app.forge.ask_cerebus.llm_gateway.enums import GatewayRefusalCode, RouteTask
from app.forge.ask_cerebus.llm_gateway.policy import task_from_intent
from app.forge.ask_cerebus.llm_gateway.prompts import PromptContract, render_prompt
from app.forge.providers.llm import LLMRequest


@dataclass(frozen=True)
class Admission:
    package: AuthorizedContextPackage
    depth: Depth
    task: RouteTask
    query_facts: Mapping[str, str]
    limitations: tuple[str, ...]
    allowed_refs: frozenset[str]
    context_units: int
    prompt_units: int

    def payload(self) -> dict[str, Any]:
        return {
            "package_id": self.package.package_id,
            "manifest_id": self.package.manifest.manifest_digest,
            "query_plan_id": self.package.query_plan_id,
            "depth": self.depth.value,
            "task": self.task.value,
            "context_units": self.context_units,
            "prompt_units": self.prompt_units,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class AdmissionFailure:
    code: GatewayRefusalCode
    detail: str
    package_id: str = ""
    manifest_id: str = ""
    query_plan_id: str = ""


def _item_refs(item: ContextItem) -> set[str]:
    refs = {item.item_id, item.source_ref_id, *item.evidence_refs}
    return {ref for ref in refs if ref}


def _all_items(package: AuthorizedContextPackage) -> tuple[ContextItem, ...]:
    return tuple(item for section in package.sections for item in section.items)


def _fact_map(item: ContextItem) -> dict[str, str]:
    return {fact.key: fact.value_text for fact in item.facts}


def admit(package: object) -> Admission | AdmissionFailure:
    """Validate the exact IV.3 object and derive only its declared controls."""

    if not isinstance(package, AuthorizedContextPackage):
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_INCOMPLETE,
            "input is not an AuthorizedContextPackage",
        )
    package_id = getattr(package, "package_id", "")
    plan_id = getattr(package, "query_plan_id", "")
    if getattr(package, "context_contract_version", None) != CONTEXT_CONTRACT_V1:
        return AdmissionFailure(
            GatewayRefusalCode.CONTEXT_VERSION_REFUSED,
            "unsupported context contract version",
            package_id,
            "",
            plan_id,
        )
    manifest = getattr(package, "manifest", None)
    if not isinstance(manifest, AuthorizedContextManifest):
        return AdmissionFailure(
            GatewayRefusalCode.MANIFEST_REQUIRED,
            "authorized manifest is required",
            package_id,
            "",
            plan_id,
        )
    manifest_id = getattr(manifest, "manifest_digest", "")
    if (
        getattr(manifest, "manifest_version", None) != CONTEXT_MANIFEST_V1
        or getattr(manifest, "context_contract_version", None) != CONTEXT_CONTRACT_V1
    ):
        return AdmissionFailure(
            GatewayRefusalCode.MANIFEST_REQUIRED,
            "manifest contract/version is not admitted",
            package_id,
            manifest_id,
            plan_id,
        )
    try:
        if (
            manifest.query_plan_id != plan_id
            or manifest.retrieval_bundle_id != package.retrieval_bundle_id
            or package.compute_id() != package_id
            or manifest.compute_digest() != manifest_id
        ):
            raise ValueError("identity mismatch")
    except Exception:
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_IDENTITY_MISMATCH,
            "package and manifest identity does not reconcile",
            package_id,
            manifest_id,
            plan_id,
        )
    if getattr(package, "outcome", None) is ContextOutcome.REFUSED:
        return AdmissionFailure(
            GatewayRefusalCode.UPSTREAM_REFUSED,
            "upstream context package is refused",
            package_id,
            manifest_id,
            plan_id,
        )

    sections = tuple(getattr(package, "sections", ()) or ())
    if not sections:
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_INCOMPLETE,
            "context package contains no sections",
            package_id,
            manifest_id,
            plan_id,
        )
    section_ids = [getattr(s.section_id, "value", "") for s in sections]
    if (
        len(section_ids) != len(set(section_ids))
        or any(section_id not in {s.value for s in SECTION_ORDER} for section_id in section_ids)
        or tuple(section_ids) != tuple(manifest.included_section_ids)
    ):
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_INCOMPLETE,
            "context sections do not match the authorized manifest",
            package_id,
            manifest_id,
            plan_id,
        )
    items = _all_items(package)
    if not items or any(not isinstance(item, ContextItem) for item in items):
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_INCOMPLETE,
            "context items are missing or malformed",
            package_id,
            manifest_id,
            plan_id,
        )
    if any(not exposure_allowed(getattr(item, "exposure", "")) for item in items):
        return AdmissionFailure(
            GatewayRefusalCode.POLICY_DENIED,
            "package contains a forbidden exposure",
            package_id,
            manifest_id,
            plan_id,
        )
    if any(
        getattr(item, "text", None) and contains_forbidden_words(item.text)
        for item in items
    ):
        return AdmissionFailure(
            GatewayRefusalCode.POLICY_DENIED,
            "package text contains forbidden secret material",
            package_id,
            manifest_id,
            plan_id,
        )

    query_sections = [s for s in sections if s.section_id is ContextSectionId.QUERY_CONTRACT]
    if len(query_sections) != 1 or not query_sections[0].items:
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_INCOMPLETE,
            "query control section is required",
            package_id,
            manifest_id,
            plan_id,
        )
    query_items = query_sections[0].items
    if any(item.trust_class is not TrustClass.TRUSTED_CONTROL for item in query_items):
        return AdmissionFailure(
            GatewayRefusalCode.PACKAGE_INCOMPLETE,
            "query control is not trusted",
            package_id,
            manifest_id,
            plan_id,
        )
    query_facts = _fact_map(query_items[0])
    depth_value = (query_facts.get("depth") or "").upper()
    try:
        depth = Depth(depth_value)
    except ValueError:
        return AdmissionFailure(
            GatewayRefusalCode.DEPTH_UNSUPPORTED,
            "effective depth is missing or unsupported",
            package_id,
            manifest_id,
            plan_id,
        )
    task = task_from_intent(query_facts.get("intent", ""))
    if task is None:
        return AdmissionFailure(
            GatewayRefusalCode.ROUTE_UNSUPPORTED,
            "query intent has no declared route task",
            package_id,
            manifest_id,
            plan_id,
        )
    limitations = tuple(
        item.source_status
        for item in items
        if item.trust_class is TrustClass.TRUSTED_CONTROL
        and item.source_ref_type == "LIMITATION"
        and item.source_status
    )
    return Admission(
        package=package,
        depth=depth,
        task=task,
        query_facts=query_facts,
        limitations=limitations,
        allowed_refs=frozenset(ref for item in items for ref in _item_refs(item)),
        context_units=context_units(package),
        prompt_units=0,
    )


def item_for_ref(package: AuthorizedContextPackage, ref: str) -> ContextItem | None:
    for item in _all_items(package):
        if ref in _item_refs(item):
            return item
    return None


def numeric_ref_is_admissible(package: AuthorizedContextPackage, ref: str) -> bool:
    item = next(
        (
            candidate
            for candidate in _all_items(package)
            if candidate.source_ref_type == "EVIDENCE"
            and ref in _item_refs(candidate)
        ),
        None,
    )
    if item is None:
        return False
    facts = _fact_map(item)
    status = (facts.get("status") or item.source_status or "").upper()
    if status not in {"VALIDATED", "FORWARD_OOS"}:
        return False
    join_status = facts.get("join_status", "")
    if join_status and join_status.upper() not in {"VERIFIED", "SUPPORTED"}:
        return False
    return item.epistemic_label in {
        EpistemicLabel.VALIDATED,
        EpistemicLabel.FORWARD_OOS,
    }


def build_request(
    admission: Admission,
    contract: PromptContract,
    *,
    model: str,
    response_schema: Mapping[str, Any],
) -> LLMRequest:
    prompt = render_prompt(admission.package, contract)
    return LLMRequest(prompt=prompt, model=model, response_schema=response_schema)


def prompt_text(admission: Admission, contract: PromptContract) -> str:
    return render_prompt(admission.package, contract)


def attempt_identity(
    *,
    package_id: str,
    manifest_id: str,
    policy_version: str,
    route_id: str,
    prompt_id: str,
    prompt_version: str,
    provider: str,
    model: str,
    attempt: int,
) -> str:
    payload = {
        "package_id": package_id,
        "manifest_id": manifest_id,
        "policy_version": policy_version,
        "route_id": route_id,
        "prompt_id": prompt_id,
        "prompt_version": prompt_version,
        "provider": provider,
        "model": model,
        "attempt": attempt,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return "GWA." + digest[:32]


__all__ = [
    "Admission",
    "AdmissionFailure",
    "admit",
    "build_request",
    "prompt_text",
    "item_for_ref",
    "numeric_ref_is_admissible",
    "attempt_identity",
]
