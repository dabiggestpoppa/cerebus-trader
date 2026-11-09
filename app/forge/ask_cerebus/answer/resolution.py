"""Read-only resolution of an authorized context package into answer material.

Nothing here mutates the package, calls a provider or fetches anything. The
index is derived purely from the frozen IV.3 structures: IV.3 flattens the
authorized evidence statistics into allowlisted item facts, so IV.5 reads them
back from there.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.ask_cerebus.context.enums import (
    ContextSectionId,
    ContextOutcome,
    EpistemicLabel,
    TrustClass,
)
from app.forge.ask_cerebus.context.schema import (
    AuthorizedContextPackage,
    ContextFact,
    ContextItem,
)
from app.forge.ask_cerebus.context.versions import CONTEXT_CONTRACT_V1


@dataclass(frozen=True)
class EvidenceCard:
    """The statistic fields IV.3 left on an evidence item."""

    evidence_id: str
    metric: str
    event_identity: str
    conditioning_population: str
    sample_size: str
    research_period: str
    small_n_flag: str
    support_classification: str
    status: str
    oos_status: str

    @property
    def missing(self) -> tuple[str, ...]:
        out: list[str] = []
        if not self.sample_size:
            out.append("N")
        if self.small_n_flag.upper() in ("", "UNRESOLVED"):
            out.append("SMALL_N")
        if not self.research_period:
            out.append("PERIOD")
        if not self.oos_status:
            out.append("OOS")
        return tuple(out)


@dataclass(frozen=True)
class ResolvedItem:
    item: ContextItem
    section_id: ContextSectionId
    facts: tuple[ContextFact, ...]
    evidence: EvidenceCard | None = None

    @property
    def ref(self) -> str:
        return self.item.source_ref_id or self.item.item_id

    @property
    def fact_map(self) -> dict[str, str]:
        return {fact.key: fact.value_text for fact in self.facts}

    @property
    def label(self) -> EpistemicLabel:
        return self.item.epistemic_label

    @property
    def layer(self) -> str:
        return self.item.layer

    @property
    def ref_type(self) -> str:
        return self.item.source_ref_type.upper()

    @property
    def numeric_values(self) -> tuple[str, ...]:
        """Authorized numeric texts that a claim may reproduce verbatim."""

        out: list[str] = []
        for fact in self.facts:
            if fact.key in _NUMERIC_FACT_KEYS and fact.value_text:
                out.append(fact.value_text)
        return tuple(out)

    @property
    def numeric_units(self) -> tuple[str, ...]:
        return tuple(fact.unit for fact in self.facts if fact.unit)


_NUMERIC_FACT_KEYS = frozenset(
    {
        "value",
        "result",
        "result_value",
        "sample_size",
        "n",
        "levels",
        "targets",
        "path_left",
        "anchor",
        "range",
        "state",
        "clock",
        "as_of",
        "data_cutoff",
        "cutoff",
    }
)


def item_refs(item: ContextItem) -> tuple[str, ...]:
    """Every reference the draft is allowed to use for this item."""

    refs = [item.item_id, item.source_ref_id, *item.evidence_refs]
    return tuple(ref for ref in refs if ref)


def _evidence_card(item: ContextItem) -> EvidenceCard | None:
    if item.source_ref_type.upper() != "EVIDENCE":
        return None
    facts = {fact.key: fact.value_text for fact in item.facts}
    return EvidenceCard(
        evidence_id=item.source_ref_id or item.item_id,
        metric=facts.get("metric", ""),
        event_identity=facts.get("event_identity", ""),
        conditioning_population=facts.get("conditioning_population", ""),
        sample_size=facts.get("sample_size", ""),
        research_period=facts.get("research_period", ""),
        small_n_flag=facts.get("small_n_flag", ""),
        support_classification=facts.get("support_classification", ""),
        status=facts.get("status", "") or item.source_status,
        oos_status=facts.get("oos_status", ""),
    )


@dataclass(frozen=True)
class PackageIndex:
    package: AuthorizedContextPackage
    items: tuple[ResolvedItem, ...]
    by_ref: dict[str, ResolvedItem]

    @classmethod
    def build(cls, package: AuthorizedContextPackage) -> "PackageIndex":
        resolved: list[ResolvedItem] = []
        by_ref: dict[str, ResolvedItem] = {}
        for section in package.sections:
            for item in section.items:
                entry = ResolvedItem(
                    item=item,
                    section_id=section.section_id,
                    facts=tuple(item.facts),
                    evidence=_evidence_card(item),
                )
                resolved.append(entry)
                for ref in item_refs(item):
                    by_ref.setdefault(ref, entry)
        return cls(package=package, items=tuple(resolved), by_ref=by_ref)

    # -- queries ----------------------------------------------------------

    def resolve(self, ref: str) -> ResolvedItem | None:
        return self.by_ref.get(ref)

    def section_items(self, section_id: ContextSectionId) -> tuple[ResolvedItem, ...]:
        return tuple(item for item in self.items if item.section_id is section_id)

    def type_items(self, source_ref_type: str) -> tuple[ResolvedItem, ...]:
        wanted = source_ref_type.upper()
        return tuple(item for item in self.items if item.ref_type == wanted)

    def limitations(self) -> tuple[str, ...]:
        """Every declared restriction, in stable order (never dropped)."""

        out: list[str] = []
        for entry in self.items:
            item = entry.item
            if item.source_ref_type.upper() == "LIMITATION" and item.source_status:
                if item.source_status not in out:
                    out.append(item.source_status)
        for issue in self.package.issues:
            code = issue.code.value
            if code.startswith(("UPSTREAM_", "MISSING_", "N_NOT_", "SMALL_N_", "DETAIL_")):
                if code not in out:
                    out.append(code)
        return tuple(out)

    def mandatory_texts(self) -> tuple[str, ...]:
        return tuple(
            entry.item.text for entry in self.items if entry.item.mandatory and entry.item.text
        )

    def setup_items(self) -> tuple[ResolvedItem, ...]:
        return self.type_items("SETUP")

    def evidence_items(self) -> tuple[ResolvedItem, ...]:
        return self.type_items("EVIDENCE")

    def untrusted_items(self) -> tuple[ResolvedItem, ...]:
        return tuple(
            entry for entry in self.items if entry.item.trust_class is TrustClass.UNTRUSTED_DATA
        )

    def has_cross_layer_rule(self) -> bool:
        for entry in self.items:
            if (
                entry.ref_type == "RULE"
                and entry.fact_map.get("rule_kind", "").upper() == "CROSS_LAYER_OVERRIDE"
            ):
                return True
        return False

    def as_of_values(self) -> tuple[str, ...]:
        out: list[str] = []
        for entry in self.items:
            for key in ("as_of", "data_cutoff", "cutoff"):
                value = entry.fact_map.get(key, "")
                if value and value not in out:
                    out.append(value)
        return tuple(out)


def is_answerable(package: object) -> bool:
    return (
        isinstance(package, AuthorizedContextPackage)
        and package.outcome is not ContextOutcome.REFUSED
    )


def package_contract_ok(package: AuthorizedContextPackage) -> bool:
    return package.context_contract_version == CONTEXT_CONTRACT_V1


__all__ = [
    "EvidenceCard",
    "ResolvedItem",
    "PackageIndex",
    "item_refs",
    "is_answerable",
    "package_contract_ok",
]
