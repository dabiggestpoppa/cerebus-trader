"""Deterministic context manifest construction for IV.3."""

from __future__ import annotations

import hashlib

from app.forge.ask_cerebus.context.enums import (
    ContextSectionId,
    SECTION_ORDER,
    TrustClass,
)
from app.forge.ask_cerebus.context.schema import (
    AuthorizedContextManifest,
    ContextIssue,
    ContextOmission,
    ContextSection,
    canonical_json,
)
from app.forge.ask_cerebus.context.versions import (
    CONTEXT_CONTRACT_V1,
    CONTEXT_MANIFEST_V1,
    ESTIMATOR_VERSION,
)


def _sha(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def trust_boundary_hash(sections: tuple[ContextSection, ...]) -> str:
    controls = []
    for section in sections:
        for item in section.items:
            if item.trust_class is TrustClass.TRUSTED_CONTROL:
                controls.append(item.control_payload())
    return _sha(controls)


def build_manifest(
    *,
    plan_id: str,
    bundle_id: str,
    sections: tuple[ContextSection, ...],
    omissions: tuple[ContextOmission, ...],
) -> AuthorizedContextManifest:
    included_sections = tuple(section.section_id.value for section in sections)
    included_ids = tuple(
        sorted(
            {
                item.source_ref_id
                for section in sections
                for item in section.items
                if item.source_ref_id
            }
        )
    )
    omitted = tuple(
        section.value
        for section in SECTION_ORDER
        if section.value not in included_sections
    )
    digests = tuple(
        (section.section_id.value, _sha(section.payload()))
        for section in sections
    )
    manifest = AuthorizedContextManifest(
        manifest_version=CONTEXT_MANIFEST_V1,
        context_contract_version=CONTEXT_CONTRACT_V1,
        query_plan_id=plan_id,
        retrieval_bundle_id=bundle_id,
        included_section_ids=included_sections,
        included_object_ids=included_ids,
        omitted_section_ids=omitted,
        estimator_version=ESTIMATOR_VERSION,
        estimated_units=sum(section.estimated_units for section in sections),
        section_digests=digests,
        trust_boundary_hash=trust_boundary_hash(sections),
    )
    return manifest.finalized()


__all__ = ["build_manifest", "trust_boundary_hash"]
