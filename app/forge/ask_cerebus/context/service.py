"""Authorized context packaging for Book IV / Bloc IV.3.

This service consumes an already-authorized retrieval bundle. It performs no
retrieval, policy evaluation, model call or market observation.
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any, Iterable

from app.forge.ask_cerebus.context.budgeting import (
    ContextBudget,
    estimate_item,
    select_within_budget,
)
from app.forge.ask_cerebus.context.compression import excerpt, facts, item
from app.forge.ask_cerebus.context.enums import (
    ContextIssueCode,
    ContextOutcome,
    ContextRefusalCode,
    ContextSectionId,
    EpistemicLabel,
    SECTION_ORDER,
    SmallNFlag,
    TrustClass,
)
from app.forge.ask_cerebus.context.labels import (
    map_status,
    number_is_admissible,
    small_n_state,
)
from app.forge.ask_cerebus.context.manifest import build_manifest
from app.forge.ask_cerebus.context.schema import (
    AuthorizedContextDetail,
    AuthorizedContextPackage,
    AuthorizedEvidenceStatistic,
    AuthorizedIntelligenceFact,
    ContextIssue,
    ContextOmission,
    ContextRefusal,
    ContextSection,
    TokenAccounting,
)
from app.forge.ask_cerebus.context.selector import (
    permits_general_knowledge,
    section_for_object_type,
)
from app.forge.ask_cerebus.context.trust import (
    contains_forbidden_words,
    exposure_allowed,
    intelligence_path_allowed,
    normalise_excerpt,
)
from app.forge.ask_cerebus.context.versions import (
    CONTEXT_CONTRACT_V1,
    ESTIMATOR_VERSION,
)
from app.forge.ask_cerebus.interpreter.versions import ASK_QUERY_CONTRACT_V1
from app.forge.ask_cerebus.retrieval.versions import RETRIEVAL_CONTRACT_V1

_LIMITATION_LABELS = {
    "NO_GO_ACTIVE": EpistemicLabel.NEGATIVE_EVIDENCE,
    "SETUP_BLOCKED": EpistemicLabel.NEGATIVE_EVIDENCE,
    "SETUP_NOT_ELIGIBLE": EpistemicLabel.NEGATIVE_EVIDENCE,
    "RESEARCH_ONLY_NOT_PRODUCTION": EpistemicLabel.RESEARCH_FLAG,
    "AUTOMATION_NOT_APPROVED": EpistemicLabel.RESEARCH_FLAG,
    "POLICY_DENIED": EpistemicLabel.INSUFFICIENT_EVIDENCE,
    "EVIDENCE_INSUFFICIENT": EpistemicLabel.INSUFFICIENT_EVIDENCE,
    "EVIDENCE_CONFLICT": EpistemicLabel.INSUFFICIENT_EVIDENCE,
    "INCOMPARABLE_EVIDENCE": EpistemicLabel.INSUFFICIENT_EVIDENCE,
    "PROVIDER_NOT_CONFIGURED": EpistemicLabel.INSUFFICIENT_EVIDENCE,
    "HISTORICAL_UNAVAILABLE": EpistemicLabel.INSUFFICIENT_EVIDENCE,
}

_SETUP_CLASSES = {
    "MANUAL_OPERATOR",
    "OPERATOR_CONFIRMATION",
    "AUTOMATION_APPROVED",
    "RESEARCH_ONLY",
    "PRODUCTION",
}
_SETUP_SURFACES = {"OPERATOR", "PRODUCTION", "RESEARCH", "AUTOMATION"}


def _value(value: Any) -> str:
    if value is None:
        return ""
    return getattr(value, "value", str(value))


def _seq(value: Any) -> tuple[Any, ...]:
    return value if isinstance(value, tuple) else ()


def _valid_contracts(plan: Any, bundle: Any) -> bool:
    try:
        return (
            getattr(plan, "query_contract_version", None) == ASK_QUERY_CONTRACT_V1
            and getattr(bundle, "retrieval_contract_version", None)
            == RETRIEVAL_CONTRACT_V1
            and bool(getattr(plan, "plan_id", ""))
            and getattr(plan, "plan_id", "") == getattr(bundle, "query_plan_id", None)
        )
    except Exception:
        return False


def _authorized_ids(bundle: Any) -> set[str]:
    ids: set[str] = set()
    for name in ("canonical_refs", "claim_refs", "evidence_refs", "intelligence_refs"):
        for ref in _seq(getattr(bundle, name, ())):
            value = getattr(ref, "object_id", None) or getattr(ref, "claim_id", None)
            value = value or getattr(ref, "evidence_id", None)
            value = value or getattr(ref, "snapshot_id", None)
            if value:
                ids.add(value)
    return ids


class ContextPackager:
    """Build a minimized, deterministic context package."""

    def pack(
        self,
        plan: Any,
        bundle: Any,
        *,
        detail: AuthorizedContextDetail | None = None,
        budget: ContextBudget | None = None,
    ) -> AuthorizedContextPackage:
        budget = budget or ContextBudget()
        detail = detail or AuthorizedContextDetail()
        try:
            if not _valid_contracts(plan, bundle):
                if getattr(plan, "query_contract_version", None) != ASK_QUERY_CONTRACT_V1:
                    code = ContextRefusalCode.CONTEXT_CONTRACT_UNSUPPORTED
                elif getattr(bundle, "retrieval_contract_version", None) != RETRIEVAL_CONTRACT_V1:
                    code = ContextRefusalCode.CONTEXT_CONTRACT_UNSUPPORTED
                else:
                    code = ContextRefusalCode.CONTEXT_INPUT_MALFORMED
                return _refusal(
                    plan_id=_value(getattr(plan, "plan_id", "")),
                    bundle_id=_value(getattr(bundle, "bundle_id", "")),
                    code=code,
                    detail="input contracts or identities do not reconcile",
                    budget=budget,
                )

            if any(
                not exposure_allowed(_value(getattr(ref, "exposure", "")))
                for ref in _seq(getattr(bundle, "canonical_refs", ()))
            ):
                return _refusal(
                    plan_id=plan.plan_id,
                    bundle_id=getattr(bundle, "bundle_id", ""),
                    code=ContextRefusalCode.CONTEXT_EXPOSURE_VIOLATION,
                    detail="authorized bundle contains a forbidden exposure",
                    budget=budget,
                )

            detail_ok = _detail_is_authorized(
                detail,
                _seq(getattr(bundle, "intelligence_refs", ())),
                _seq(getattr(bundle, "evidence_refs", ())),
            )
            if not detail_ok:
                return _refusal(
                    plan_id=plan.plan_id,
                    bundle_id=getattr(bundle, "bundle_id", ""),
                    code=ContextRefusalCode.CONTEXT_DETAIL_UNAUTHORIZED,
                    detail="detail id is not present in the authorized bundle",
                    budget=budget,
                )

            grouped: dict[ContextSectionId, list[Any]] = {
                section: [] for section in SECTION_ORDER
            }
            issues: list[ContextIssue] = []

            self._query(grouped, plan)
            self._current(grouped, plan, bundle, detail, issues)
            self._canonical(grouped, bundle, issues)
            self._setup(grouped, bundle, issues)
            self._claims(grouped, bundle, issues)
            self._evidence(grouped, bundle, detail, issues)
            self._lineage(grouped, bundle)
            self._limitations(grouped, bundle, issues)
            self._general(grouped, plan)
            self._semantic(grouped, bundle, issues, budget)

            kept, trimmed, mandatory_total = select_within_budget(grouped, budget)
            if mandatory_total > budget.available_units:
                return _refusal(
                    plan_id=plan.plan_id,
                    bundle_id=getattr(bundle, "bundle_id", ""),
                    code=ContextRefusalCode.CONTEXT_BUDGET_EXCEEDED,
                    detail="mandatory safety context exceeds the available budget",
                    budget=budget,
                )

            sections, omissions = _finalize_sections(kept, trimmed)
            issues.extend(
                ContextIssue(
                    ContextIssueCode.CONTEXT_BUDGET_TRIMMED,
                    section,
                    item.source_ref_id,
                )
                for section, item in trimmed
            )
            used = sum(section.estimated_units for section in sections)
            refusals = tuple(getattr(bundle, "refusals", ()))
            outcome = (
                ContextOutcome.REFUSED
                if refusals
                else (
                    ContextOutcome.PARTIAL
                    if issues or trimmed or getattr(bundle, "limitations", ())
                    else ContextOutcome.RESOLVED
                )
            )
            accounting = TokenAccounting(
                estimator_version=ESTIMATOR_VERSION,
                max_units=budget.max_units,
                reserve_units=budget.reserve_units,
                mandatory_units=sum(
                    item.token_units
                    for section in sections
                    for item in section.items
                    if item.mandatory
                ),
                optional_units=used
                - sum(
                    item.token_units
                    for section in sections
                    for item in section.items
                    if item.mandatory
                ),
                used_units=used,
                trimmed_units=sum(estimate_item(item) for _, item in trimmed),
            )
            manifest = build_manifest(
                plan_id=plan.plan_id,
                bundle_id=getattr(bundle, "bundle_id", ""),
                sections=sections,
                omissions=omissions,
            )
            package = AuthorizedContextPackage(
                context_contract_version=CONTEXT_CONTRACT_V1,
                query_plan_id=plan.plan_id,
                retrieval_bundle_id=getattr(bundle, "bundle_id", ""),
                outcome=outcome,
                sections=sections,
                omissions=omissions,
                issues=tuple(_dedupe_issues(issues)),
                token_accounting=accounting,
                manifest=manifest,
            )
            return package.finalized()
        except Exception:
            if os.environ.get("IV3_DEBUG"):
                raise
            return _refusal(
                plan_id=_value(getattr(plan, "plan_id", "")),
                bundle_id=_value(getattr(bundle, "bundle_id", "")),
                code=ContextRefusalCode.CONTEXT_INTEGRITY_FAILURE,
                detail="packaging failed closed",
                budget=budget,
            )

    # -- section builders ------------------------------------------------

    def _query(self, grouped: dict, plan: Any) -> None:
        ambiguities = tuple(
            _value(getattr(entry, "reason", entry))
            for entry in _seq(getattr(plan, "ambiguities", ()))
        )
        grouped[ContextSectionId.QUERY_CONTRACT].append(
            item(
                section=ContextSectionId.QUERY_CONTRACT.value,
                source_ref_id=plan.plan_id,
                source_ref_type="QUERY_PLAN",
                source_status="PLAN",
                label=EpistemicLabel.CANONICAL,
                layer=_value(getattr(plan, "layer", "")),
                exposure="NONE",
                trust_class=TrustClass.TRUSTED_CONTROL,
                facts=facts(
                    ("identity", plan.plan_id, ""),
                    ("intent", _value(getattr(plan, "intent", "")), ""),
                    ("time_scope", _value(getattr(plan, "time_scope", "")), ""),
                    ("depth", _value(getattr(plan, "effective_depth", "")), ""),
                    ("actionable", getattr(plan, "actionable", ""), ""),
                    ("ambiguity", ",".join(ambiguities), ""),
                ),
                priority=0,
                mandatory=True,
            )
        )

    def _current(
        self,
        grouped: dict,
        plan: Any,
        bundle: Any,
        detail: AuthorizedContextDetail,
        issues: list[ContextIssue],
    ) -> None:
        by_snapshot: dict[str, list[AuthorizedIntelligenceFact]] = {}
        for fact in detail.intelligence:
            by_snapshot.setdefault(fact.snapshot_id, []).append(fact)

        for ref in _seq(getattr(bundle, "intelligence_refs", ())):
            snapshot_id = getattr(ref, "snapshot_id", "")
            no_go = tuple(getattr(ref, "no_go", ()))
            refusal = getattr(ref, "refusal", "")
            quality = getattr(ref, "quality", "")
            status = refusal or quality or "UNAVAILABLE"
            label = (
                EpistemicLabel.CANONICAL
                if quality and not refusal
                else EpistemicLabel.INSUFFICIENT_EVIDENCE
            )
            fact_list = [
                ("snapshot_id", snapshot_id, ""),
                ("snapshot_hash", getattr(ref, "snapshot_hash", ""), ""),
                ("view", getattr(ref, "view", ""), ""),
                ("quality", quality, ""),
                ("no_go", ",".join(no_go), ""),
                ("refusal", refusal, ""),
            ]
            if snapshot_id in by_snapshot:
                for fact in by_snapshot[snapshot_id]:
                    if intelligence_path_allowed(fact.field_path):
                        fact_list.append(
                            (fact.field_path, fact.value_text, fact.unit)
                        )
                    else:
                        issues.append(
                            ContextIssue(
                                ContextIssueCode.EXPOSURE_EXCLUDED,
                                ContextSectionId.CURRENT_INTELLIGENCE,
                                "intelligence detail field path excluded",
                            )
                        )
            else:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.DETAIL_NOT_SUPPLIED,
                        ContextSectionId.CURRENT_INTELLIGENCE,
                        snapshot_id,
                    )
                )

            grouped[ContextSectionId.CURRENT_INTELLIGENCE].append(
                item(
                    section=ContextSectionId.CURRENT_INTELLIGENCE.value,
                    source_ref_id=snapshot_id or "SNAPSHOT.UNAVAILABLE",
                    source_ref_type="INTELLIGENCE",
                    source_status=status,
                    label=label,
                    layer=_value(getattr(ref, "model_version", "")),
                    exposure="NONE",
                    generation=_value(getattr(ref, "snapshot_hash", "")),
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(*fact_list),
                    priority=1,
                    mandatory=bool(no_go or refusal),
                )
            )
            if refusal:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.UPSTREAM_REFUSAL,
                        ContextSectionId.CURRENT_INTELLIGENCE,
                        refusal,
                    )
                )

    def _canonical(self, grouped: dict, bundle: Any, issues: list) -> None:
        seen: set[str] = set()
        for ref in _seq(getattr(bundle, "canonical_refs", ())):
            object_id = getattr(ref, "object_id", "")
            object_type = getattr(ref, "object_type", "")
            section = section_for_object_type(object_type)
            if section is None or section is ContextSectionId.SETUP:
                continue
            if object_id in seen:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.DUPLICATE_SUPPRESSED,
                        section,
                        object_id,
                    )
                )
                continue
            seen.add(object_id)
            status = getattr(ref, "status", "")
            grouped[section].append(
                item(
                    section=section.value,
                    source_ref_id=object_id,
                    source_ref_type=object_type or "CANONICAL",
                    source_status=status,
                    label=map_status(status, direct=status in {"CANONICAL", "ACTIVE", "CURRENT"}),
                    layer=getattr(ref, "layer", ""),
                    exposure=getattr(ref, "exposure", ""),
                    generation=getattr(ref, "generation", ""),
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(
                        ("identity", object_id, ""),
                        ("version", getattr(ref, "version", ""), ""),
                        ("status", status, ""),
                        ("layer", getattr(ref, "layer", ""), ""),
                        ("market_scope", ",".join(getattr(ref, "market_scope", ())), ""),
                        ("generation", getattr(ref, "generation", ""), ""),
                        ("support_classification", getattr(ref, "support_classification", ""), ""),
                    ),
                    priority=3,
                )
            )

    def _setup(self, grouped: dict, bundle: Any, issues: list) -> None:
        for ref in _seq(getattr(bundle, "canonical_refs", ())):
            if section_for_object_type(getattr(ref, "object_type", "")) is not ContextSectionId.SETUP:
                continue
            support = getattr(ref, "support_classification", "")
            setup_class = support if support in _SETUP_CLASSES else ""
            surface = support if support in _SETUP_SURFACES else ""
            if not setup_class and not surface:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.DETAIL_NOT_SUPPLIED,
                        ContextSectionId.SETUP,
                        getattr(ref, "object_id", ""),
                    )
                )
            grouped[ContextSectionId.SETUP].append(
                item(
                    section=ContextSectionId.SETUP.value,
                    source_ref_id=getattr(ref, "object_id", ""),
                    source_ref_type="SETUP",
                    source_status=getattr(ref, "status", ""),
                    label=map_status(getattr(ref, "status", ""), direct=False),
                    layer=getattr(ref, "layer", ""),
                    exposure=getattr(ref, "exposure", ""),
                    generation=getattr(ref, "generation", ""),
                    facts=facts(
                        ("setup_id", getattr(ref, "object_id", ""), ""),
                        ("setup_version", getattr(ref, "version", ""), ""),
                        ("setup_class", setup_class, ""),
                        ("surface", surface, ""),
                        ("eligibility", getattr(ref, "status", ""), ""),
                        ("status", getattr(ref, "status", ""), ""),
                        ("layer", getattr(ref, "layer", ""), ""),
                    ),
                    priority=4,
                )
            )

    def _claims(self, grouped: dict, bundle: Any, issues: list) -> None:
        evidence_ids = {
            getattr(ref, "evidence_id", "")
            for ref in _seq(getattr(bundle, "evidence_refs", ()))
        }
        model_layers: dict[str, str] = {}
        for ref in _seq(getattr(bundle, "canonical_refs", ())):
            if section_for_object_type(getattr(ref, "object_type", "")) is not ContextSectionId.CANONICAL_MODEL:
                continue
            object_id = getattr(ref, "object_id", "")
            layer = getattr(ref, "layer", "")
            model_layers[object_id] = layer
            if object_id.startswith("MOD."):
                model_layers[object_id[4:].rsplit(".", 1)[0]] = layer
        missing = False
        for ref in _seq(getattr(bundle, "claim_refs", ())):
            claim_id = getattr(ref, "claim_id", "")
            refs = tuple(getattr(ref, "evidence_ids", ()))
            join = _value(getattr(ref, "join_status", ""))
            status = getattr(ref, "status", "")
            label = map_status(status)
            has_evidence = bool(refs) and all(eid in evidence_ids for eid in refs)
            result = getattr(ref, "result_value", None)
            if not has_evidence or join in {"MISSING", "UNSUPPORTED"}:
                missing = True
                issues.append(
                    ContextIssue(
                        ContextIssueCode.MISSING_EVIDENCE,
                        ContextSectionId.CLAIMS,
                        claim_id,
                    )
                )
                result = None
            if not number_is_admissible(label, join):
                result = None
            identity_key = getattr(ref, "identity_key", None)
            fact_list = [
                ("identity", claim_id, ""),
                ("version", ",".join(getattr(ref, "model_versions", ())), ""),
                ("status", status, ""),
                ("generation", getattr(ref, "generation", ""), ""),
                ("join_status", join, ""),
                ("identity_key", "|".join(identity_key) if identity_key else "", ""),
                ("result_value", result, ""),
            ]
            grouped[ContextSectionId.CLAIMS].append(
                item(
                    section=ContextSectionId.CLAIMS.value,
                    source_ref_id=claim_id,
                    source_ref_type="CLAIM",
                    source_status=status,
                    label=label,
                    layer=next(
                        (
                            model_layers[model_id]
                            for model_id in getattr(ref, "model_ids", ())
                            if model_id in model_layers
                        ),
                        "",
                    ),
                    generation=getattr(ref, "generation", ""),
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(*fact_list),
                    evidence_refs=refs,
                    priority=2,
                )
            )
        if missing:
            grouped[ContextSectionId.LIMITATIONS_NEGATIVE].append(
                item(
                    section=ContextSectionId.LIMITATIONS_NEGATIVE.value,
                    source_ref_id="",
                    source_ref_type="MISSING_EVIDENCE",
                    source_status="MISSING_EVIDENCE",
                    label=EpistemicLabel.INSUFFICIENT_EVIDENCE,
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(("status", "MISSING_EVIDENCE", "")),
                    priority=0,
                    mandatory=True,
                )
            )

    def _evidence(
        self,
        grouped: dict,
        bundle: Any,
        detail: AuthorizedContextDetail,
        issues: list,
    ) -> None:
        stats_by_id: dict[str, list[AuthorizedEvidenceStatistic]] = {}
        for stat in detail.statistics:
            stats_by_id.setdefault(stat.evidence_id, []).append(stat)

        for ref in _seq(getattr(bundle, "evidence_refs", ())):
            evidence_id = getattr(ref, "evidence_id", "")
            status = getattr(ref, "status", "")
            stats = stats_by_id.get(evidence_id, [])
            fact_list = [
                ("identity", evidence_id, ""),
                ("status", status, ""),
                ("support_classification", getattr(ref, "support_classification", ""), ""),
                ("oos_status", getattr(ref, "oos_status", ""), ""),
            ]
            for stat in stats:
                fact_list.extend(
                    [
                        ("metric", stat.metric, ""),
                        ("event_identity", stat.event_identity, ""),
                        ("conditioning_population", stat.conditioning_population, ""),
                        ("sample_size", stat.sample_size, ""),
                        ("research_period", stat.research_period, ""),
                        ("oos_status", stat.oos_status, ""),
                    ]
                )
                if stat.sample_size is None:
                    issues.append(
                        ContextIssue(
                            ContextIssueCode.N_NOT_PROVIDED,
                            ContextSectionId.EVIDENCE,
                            evidence_id,
                        )
                    )
                    issues.append(
                        ContextIssue(
                            ContextIssueCode.DETAIL_NOT_SUPPLIED,
                            ContextSectionId.EVIDENCE,
                            evidence_id,
                        )
                    )
                if small_n_state(
                    stat.sample_size, stat.small_n_flag, stat.small_n_threshold_ref
                ) is SmallNFlag.UNRESOLVED:
                    issues.append(
                        ContextIssue(
                            ContextIssueCode.SMALL_N_UNRESOLVED,
                            ContextSectionId.EVIDENCE,
                            evidence_id,
                        )
                    )
            if not stats:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.DETAIL_NOT_SUPPLIED,
                        ContextSectionId.EVIDENCE,
                        evidence_id,
                    )
                )
            grouped[ContextSectionId.EVIDENCE].append(
                item(
                    section=ContextSectionId.EVIDENCE.value,
                    source_ref_id=evidence_id,
                    source_ref_type="EVIDENCE",
                    source_status=status,
                    label=map_status(status),
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(*fact_list),
                    provenance_refs=tuple(getattr(ref, "provenance_ids", ())),
                    priority=2,
                )
            )

    def _lineage(self, grouped: dict, bundle: Any) -> None:
        for ref in _seq(getattr(bundle, "lineage_refs", ())):
            grouped[ContextSectionId.LINEAGE_TERMS].append(
                item(
                    section=ContextSectionId.LINEAGE_TERMS.value,
                    source_ref_id=getattr(ref, "object_id", ""),
                    source_ref_type="LINEAGE",
                    source_status="LINEAGE",
                    label=EpistemicLabel.CANONICAL,
                    generation=getattr(ref, "generation", ""),
                    facts=facts(
                        ("identity", getattr(ref, "object_id", ""), ""),
                        ("generation", getattr(ref, "generation", ""), ""),
                        ("status", getattr(ref, "relation", ""), ""),
                    ),
                    priority=6,
                )
            )
        for ref in _seq(getattr(bundle, "canonical_refs", ())):
            if section_for_object_type(getattr(ref, "object_type", "")) is not ContextSectionId.LINEAGE_TERMS:
                continue
            grouped[ContextSectionId.LINEAGE_TERMS].append(
                item(
                    section=ContextSectionId.LINEAGE_TERMS.value,
                    source_ref_id=getattr(ref, "object_id", ""),
                    source_ref_type="TERM",
                    source_status=getattr(ref, "status", ""),
                    label=map_status(getattr(ref, "status", "")),
                    layer=getattr(ref, "layer", ""),
                    exposure=getattr(ref, "exposure", ""),
                    generation=getattr(ref, "generation", ""),
                    facts=facts(
                        ("identity", getattr(ref, "object_id", ""), ""),
                        ("version", getattr(ref, "version", ""), ""),
                        ("status", getattr(ref, "status", ""), ""),
                        ("support_classification", getattr(ref, "support_classification", ""), ""),
                    ),
                    priority=6,
                )
            )

    def _limitations(self, grouped: dict, bundle: Any, issues: list) -> None:
        for limitation in _seq(getattr(bundle, "limitations", ())):
            code = _value(getattr(limitation, "code", ""))
            grouped[ContextSectionId.LIMITATIONS_NEGATIVE].append(
                item(
                    section=ContextSectionId.LIMITATIONS_NEGATIVE.value,
                    source_ref_id="",
                    source_ref_type="LIMITATION",
                    source_status=code,
                    label=_LIMITATION_LABELS.get(
                        code, EpistemicLabel.INSUFFICIENT_EVIDENCE
                    ),
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(("status", code, "")),
                    priority=0,
                    mandatory=True,
                )
            )
            issues.append(
                ContextIssue(
                    ContextIssueCode.UPSTREAM_LIMITATION,
                    ContextSectionId.LIMITATIONS_NEGATIVE,
                    code,
                )
            )

        for ref in _seq(getattr(bundle, "negative_refs", ())):
            status = getattr(ref, "status", "")
            grouped[ContextSectionId.LIMITATIONS_NEGATIVE].append(
                item(
                    section=ContextSectionId.LIMITATIONS_NEGATIVE.value,
                    source_ref_id=getattr(ref, "object_id", ""),
                    source_ref_type="NEGATIVE",
                    source_status=status,
                    label=map_status(status),
                    generation=getattr(ref, "generation", ""),
                    facts=facts(
                        ("identity", getattr(ref, "object_id", ""), ""),
                        ("status", status, ""),
                        ("support_classification", getattr(ref, "reason", ""), ""),
                    ),
                    priority=5,
                    mandatory=status in {"NO_GO", "FALSIFIED", "INTERNAL_CONTRADICTION"},
                )
            )

        for refusal in _seq(getattr(bundle, "refusals", ())):
            code = _value(getattr(refusal, "code", ""))
            grouped[ContextSectionId.LIMITATIONS_NEGATIVE].append(
                item(
                    section=ContextSectionId.LIMITATIONS_NEGATIVE.value,
                    source_ref_id="",
                    source_ref_type="REFUSAL",
                    source_status=code,
                    label=EpistemicLabel.INSUFFICIENT_EVIDENCE,
                    trust_class=TrustClass.TRUSTED_CONTROL,
                    facts=facts(("refusal", code, "")),
                    priority=0,
                    mandatory=True,
                )
            )
            issues.append(
                ContextIssue(
                    ContextIssueCode.UPSTREAM_REFUSAL,
                    ContextSectionId.LIMITATIONS_NEGATIVE,
                    code,
                )
            )

    def _general(self, grouped: dict, plan: Any) -> None:
        if not permits_general_knowledge(_value(getattr(plan, "intent", ""))):
            return
        grouped[ContextSectionId.GENERAL_KNOWLEDGE].append(
            item(
                section=ContextSectionId.GENERAL_KNOWLEDGE.value,
                source_ref_id="",
                source_ref_type="GENERAL_ALLOWANCE",
                source_status="ALLOWED",
                label=EpistemicLabel.GENERAL_KNOWLEDGE,
                trust_class=TrustClass.TRUSTED_CONTROL,
                facts=facts(("general_knowledge_allowed", "true", "")),
                priority=7,
            )
        )

    def _semantic(
        self,
        grouped: dict,
        bundle: Any,
        issues: list,
        budget: ContextBudget,
    ) -> None:
        authorized = _authorized_ids(bundle)
        exposures = {
            getattr(ref, "object_id", ""): getattr(ref, "exposure", "")
            for ref in _seq(getattr(bundle, "canonical_refs", ()))
        }
        for passage in _seq(getattr(bundle, "semantic_passages", ())):
            object_id = getattr(passage, "object_id", "")
            if object_id not in authorized:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.EXPOSURE_EXCLUDED,
                        None,
                        "semantic object is outside the authorized bundle",
                    )
                )
                continue
            quote_scope = getattr(passage, "quote_scope", "NONE")
            text = excerpt(
                getattr(passage, "text", ""), max_chars=budget.max_excerpt_chars
            )
            if text is None or quote_scope in {"", "NONE"}:
                issues.append(
                    ContextIssue(
                        ContextIssueCode.EXPOSURE_EXCLUDED,
                        None,
                        "semantic excerpt or quote scope is unavailable",
                    )
                )
                continue
            if contains_forbidden_words(text):
                issues.append(
                    ContextIssue(
                        ContextIssueCode.EXPOSURE_EXCLUDED,
                        None,
                        "semantic excerpt contains secret-like material",
                    )
                )
                continue
            if object_id.startswith("MOD") or object_id.startswith("DOC"):
                section = ContextSectionId.CANONICAL_MODEL
            elif object_id.startswith("CL"):
                section = ContextSectionId.CLAIMS
            elif object_id.startswith("EV"):
                section = ContextSectionId.EVIDENCE
            elif object_id.startswith("TERM") or object_id.startswith("LIN"):
                section = ContextSectionId.LINEAGE_TERMS
            else:
                section = ContextSectionId.CANONICAL_MODEL
            grouped[section].append(
                item(
                    section=section.value,
                    source_ref_id=object_id,
                    source_ref_type="SEMANTIC_SUPPORT",
                    source_status=getattr(passage, "status", "SUPPORT_ONLY"),
                    label=EpistemicLabel.INSUFFICIENT_EVIDENCE,
                    exposure=exposures.get(object_id, "AUTHORIZED"),
                    trust_class=TrustClass.UNTRUSTED_DATA,
                    facts=facts(
                        ("status", getattr(passage, "status", ""), ""),
                        ("support_classification", getattr(passage, "support_classification", ""), ""),
                    ),
                    text=text,
                    quote_scope=quote_scope,
                    priority=7,
                )
            )


def _detail_is_authorized(
    detail: AuthorizedContextDetail,
    intelligence_refs: Iterable[Any],
    evidence_refs: Iterable[Any],
) -> bool:
    snapshots = {
        getattr(ref, "snapshot_id", "") for ref in intelligence_refs if getattr(ref, "snapshot_id", "")
    }
    evidence = {getattr(ref, "evidence_id", "") for ref in evidence_refs}
    for fact in detail.intelligence:
        if fact.snapshot_id not in snapshots:
            return False
    for stat in detail.statistics:
        if stat.evidence_id not in evidence:
            return False
    return True


def _dedupe_issues(issues: list[ContextIssue]) -> list[ContextIssue]:
    seen: set[tuple[str, str, str]] = set()
    out: list[ContextIssue] = []
    for issue in issues:
        key = (issue.code.value, issue.section_id.value if issue.section_id else "", issue.detail)
        if key in seen:
            continue
        seen.add(key)
        out.append(issue)
    return out


def _finalize_sections(
    grouped: dict[ContextSectionId, list[Any]],
    trimmed: list[tuple[ContextSectionId, Any]],
) -> tuple[tuple[ContextSection, ...], tuple[ContextOmission, ...]]:
    sections: list[ContextSection] = []
    omissions: list[ContextOmission] = []
    trimmed_sections = {section for section, _ in trimmed}
    for section in SECTION_ORDER:
        items = sorted(
            grouped.get(section, []),
            key=lambda entry: (
                entry.priority,
                entry.source_ref_type,
                entry.source_ref_id,
                entry.generation,
                entry.text or "",
            ),
        )
        if not items:
            if section not in trimmed_sections:
                omissions.append(
                    ContextOmission(section, ContextIssueCode.INAPPLICABLE_SECTION)
                )
            continue
        finalized = tuple(
            replace(
                entry,
                item_id=f"CTX.{section.value}.{ordinal:03d}",
                token_units=estimate_item(entry),
            )
            for ordinal, entry in enumerate(items)
        )
        section_omissions = tuple(
            ContextOmission(
                section,
                ContextIssueCode.CONTEXT_BUDGET_TRIMMED,
                entry.source_ref_id,
                estimate_item(entry),
            )
            for trimmed_section, entry in trimmed
            if trimmed_section is section
        )
        omissions.extend(section_omissions)
        sections.append(
            ContextSection(
                section_id=section,
                items=finalized,
                omissions=section_omissions,
                estimated_units=16 + sum(entry.token_units for entry in finalized),
                mandatory_units=sum(
                    entry.token_units for entry in finalized if entry.mandatory
                ),
            )
        )
    return tuple(sections), tuple(omissions)


def _refusal(
    *,
    plan_id: str,
    bundle_id: str,
    code: ContextRefusalCode,
    detail: str,
    budget: ContextBudget,
) -> AuthorizedContextPackage:
    manifest = build_manifest(
        plan_id=plan_id,
        bundle_id=bundle_id,
        sections=(),
        omissions=(),
    )
    accounting = TokenAccounting(
        estimator_version=ESTIMATOR_VERSION,
        max_units=budget.max_units,
        reserve_units=budget.reserve_units,
        mandatory_units=0,
        optional_units=0,
        used_units=0,
        trimmed_units=0,
    )
    return AuthorizedContextPackage(
        context_contract_version=CONTEXT_CONTRACT_V1,
        query_plan_id=plan_id,
        retrieval_bundle_id=bundle_id,
        outcome=ContextOutcome.REFUSED,
        refusals=(ContextRefusal(code, detail),),
        issues=(),
        token_accounting=accounting,
        manifest=manifest,
    ).finalized()


__all__ = ["ContextPackager"]
