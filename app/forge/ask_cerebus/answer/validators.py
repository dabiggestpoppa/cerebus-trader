"""Deterministic truth validators for IV.5.

Every validator reads the same prepared claims and the frozen package index. A
finding vetoes the whole answer; there is no partial success and no warning that
merely accompanies a validated answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.forge.ask_cerebus.answer.admission import Admission
from app.forge.ask_cerebus.answer.citations import is_internal_ref
from app.forge.ask_cerebus.answer.enums import (
    LAYER_VOCABULARY,
    NON_CURRENT_EPISTEMIC_LABELS,
    SETUP_RANK,
    ValidationCode,
)
from app.forge.ask_cerebus.answer.resolution import ResolvedItem
from app.forge.ask_cerebus.context.enums import TrustClass
from app.forge.ask_cerebus.llm_gateway.draft import DraftClaim, NumericLink


@dataclass(frozen=True)
class Finding:
    code: ValidationCode
    detail: str
    claim_id: str = ""
    ref: str = ""

    def payload(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "detail": self.detail,
            "claim_id": self.claim_id,
            "ref": self.ref,
        }


@dataclass(frozen=True)
class PreparedClaim:
    claim_id: str
    draft: DraftClaim
    sources: tuple[ResolvedItem, ...]
    unresolved_refs: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return self.draft.text

    @property
    def normalized(self) -> str:
        return normalize(self.text)


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


_NUMBER_TOKEN = re.compile(r"(?<![A-Za-z0-9_.])(\d+(?:[.,]\d+)?%?)")

_CURRENT_TOKENS = (
    "current",
    "currently",
    "right now",
    "live",
    "today",
    "as of",
    "now at",
    "at present",
)

_ACTION_TOKENS = (
    "enter",
    "entry",
    "buy",
    "sell",
    "go long",
    "go short",
    "add to",
    "execute",
    "place an order",
    "take profit",
    "stop loss",
    "take a position",
)

_ADVICE_TOKENS = (
    "you should",
    "you must buy",
    "position size",
    "size your",
    "entry price",
    "price target",
    "stop loss at",
    "buy at",
    "sell at",
    "place a",
    "order at",
    "take a position",
)

_METRIC_FAMILY = {
    "completion_rate": "TARGET_COMPLETION",
    "target_completion": "TARGET_COMPLETION",
    "path_completion": "TARGET_COMPLETION",
    "correlation": "CORRELATION",
    "pearson": "CORRELATION",
    "basket_confirmation": "BASKET_CONFIRMATION",
    "basket": "BASKET_CONFIRMATION",
    "path_statistic": "PATH_STATISTIC",
    "win_rate": "WIN_RATE",
    "hit_rate": "WIN_RATE",
    "simulation": "SIMULATION",
    "frequency": "FREQUENCY",
}

_FAMILY_TOKENS = {
    "PROBABILITY": ("probability", "odds", "chance of", "likely to"),
    "WIN_RATE": ("win rate", "hit rate", "success rate", "wins"),
    "CORRELATION": ("correlation", "correlat", " pearson"),
    "TARGET_COMPLETION": ("completion rate", "completed", "target reached", "reached the target"),
    "BASKET_CONFIRMATION": ("basket confirmation", "basket confirmed", "basket"),
    "PATH_STATISTIC": ("path statistic", "path frequency"),
    "SIMULATION": ("simulated", "simulation", "backtest"),
    "EMPIRICAL": ("empirical", "observed in live", "live sample", "realised", "realized"),
}

_EMPIRICAL_CLASS_MARKERS = ("SIMULATION", "SIMULATED", "SYNTHETIC")

_INTERNAL_TEXT_TOKENS = (
    "app.forge",
    "app/forge",
    "insert into",
    "traceback",
    "sqlite",
    "http://",
    "https://",
    "object_id",
    "item_id",
    "row_id",
    "context_items",
    "evidence_rows",
    "manifest_digest",
    "pkg.",
    "mfd.",
)

_SYSTEM_TEXT_TOKENS = (
    "password",
    "api key",
    "secret",
    "credential",
    "system prompt",
    "you are an ai",
    "routing policy",
    "entitlement logic",
    "model config",
)

_ENUMERATION_TOKENS = (
    "other objects",
    "other snapshots",
    "hidden objects",
    "not included in the package",
    "remaining items",
    "number of items",
    "there are more",
    "beyond the package",
)

_UNTRUSTED_INSTRUCTION_TOKENS = (
    "ignore previous",
    "ignore all previous",
    "disregard the above",
    "you must now",
    "system:",
    "new instructions",
)


def number_tokens(text: str) -> tuple[str, ...]:
    return tuple(match.group(1) for match in _NUMBER_TOKEN.finditer(text or ""))


def asserts_current(text: str) -> bool:
    lowered = normalize(text)
    return any(token in lowered for token in _CURRENT_TOKENS)


def asserts_action(text: str) -> bool:
    lowered = normalize(text)
    return any(token in lowered for token in _ACTION_TOKENS)


def asserts_advice(text: str) -> bool:
    lowered = normalize(text)
    return any(token in lowered for token in _ADVICE_TOKENS)


def asserted_families(text: str) -> set[str]:
    lowered = normalize(text)
    return {
        family
        for family, tokens in _FAMILY_TOKENS.items()
        if any(token in lowered for token in tokens)
    }


def metric_family(metric: str) -> str:
    return _METRIC_FAMILY.get(normalize(metric).replace(" ", "_"), "")


# ---------------------------------------------------------------------------
# upstream unavailability propagation
# ---------------------------------------------------------------------------

_UPSTREAM_UNAVAILABLE = {
    "MODEL_VERSION_UNAVAILABLE": ValidationCode.MODEL_VERSION_UNAVAILABLE,
    "ACCESS_NOT_ENTITLED": ValidationCode.ACCESS_NOT_ENTITLED,
    "AMBIGUOUS_SCOPE": ValidationCode.AMBIGUOUS_SCOPE,
    "CURRENT_DATA_UNAVAILABLE": ValidationCode.MISSING_FRESHNESS,
}


def validate_upstream(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    """Propagate an unavailability the package already declares."""

    del claims
    findings: list[Finding] = []
    seen: set[str] = set()
    for entry in admission.index.items:
        markers = [entry.item.source_status, entry.fact_map.get("status", "")]
        markers.extend(
            entry.fact_map.get(key, "") for key in ("unavailable", "availability", "entitlement")
        )
        for marker in markers:
            value = (marker or "").upper()
            code = _UPSTREAM_UNAVAILABLE.get(value)
            if code is not None and value not in seen:
                seen.add(value)
                findings.append(
                    Finding(code, f"the authorized package declares {value}", ref=entry.ref)
                )
    return findings


# ---------------------------------------------------------------------------
# numerical
# ---------------------------------------------------------------------------


def _authorized_numbers(index_refs: tuple[ResolvedItem, ...], draft: tuple[NumericLink, ...]) -> set[str]:
    allowed: set[str] = set()
    for entry in index_refs:
        allowed.update(entry.numeric_values)
    for link in draft:
        allowed.add(link.value_text)
    expanded: set[str] = set()
    for value in allowed:
        expanded.add(value)
        expanded.update(number_tokens(value))
    return expanded


def validate_numerical(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    draft = admission.draft
    index = admission.index

    allowed_numbers = _authorized_numbers(
        tuple(entry for entry in index.items), draft.numbers
    )

    for link in draft.numbers:
        entry = index.resolve(link.source_ref_id)
        if entry is None:
            findings.append(
                Finding(
                    ValidationCode.NUMERIC_EVIDENCE_MISSING,
                    "numeric claim does not resolve to an authorized package item",
                    ref=link.source_ref_id,
                )
            )
            continue
        authorized = entry.numeric_values
        if not authorized:
            findings.append(
                Finding(
                    ValidationCode.NUMERIC_EVIDENCE_MISSING,
                    "authorized item carries no numeric value",
                    ref=link.source_ref_id,
                )
            )
            continue
        authorized_norm = {normalize(value) for value in authorized}
        if normalize(link.value_text) not in authorized_norm:
            findings.append(
                Finding(
                    ValidationCode.NUMERIC_MISMATCH,
                    "numeric claim does not equal an authorized value",
                    ref=link.source_ref_id,
                )
            )
        if link.unit and entry.numeric_units:
            units = {normalize(unit) for unit in entry.numeric_units}
            if normalize(link.unit) not in units:
                findings.append(
                    Finding(
                        ValidationCode.NUMERIC_UNIT_MISMATCH,
                        "numeric claim changes the authorized unit or scale",
                        ref=link.source_ref_id,
                    )
                )

    for prepared in claims:
        for token in number_tokens(prepared.text):
            if token not in allowed_numbers:
                findings.append(
                    Finding(
                        ValidationCode.NUMERIC_EVIDENCE_MISSING,
                        "claim states a number that no authorized value supports",
                        claim_id=prepared.claim_id,
                    )
                )
                break

    for prepared in claims:
        evidence_sources = [source for source in prepared.sources if source.evidence is not None]
        if not evidence_sources:
            continue
        families = asserted_families(prepared.text)
        for source in evidence_sources:
            card = source.evidence
            assert card is not None
            governing = metric_family(card.metric)
            if governing:
                drifted = {family for family in families if family in _FAMILY_TOKENS and family != governing and family != "EMPIRICAL"}
                if governing == "TARGET_COMPLETION" and "WIN_RATE" in drifted:
                    findings.append(
                        Finding(
                            ValidationCode.METRIC_SUBSTITUTION,
                            "target completion is presented as a win rate",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
                elif governing == "CORRELATION" and "PROBABILITY" in drifted:
                    findings.append(
                        Finding(
                            ValidationCode.METRIC_SUBSTITUTION,
                            "a correlation is presented as a probability",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
                elif governing == "BASKET_CONFIRMATION" and "WIN_RATE" in drifted:
                    findings.append(
                        Finding(
                            ValidationCode.METRIC_SUBSTITUTION,
                            "basket confirmation is presented as a win rate",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
                elif drifted:
                    findings.append(
                        Finding(
                            ValidationCode.METRIC_SUBSTITUTION,
                            "claim asserts a metric the authorized statistic does not measure",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
            evidence_class = f"{card.support_classification} {card.status} {source.item.source_status}".upper()
            if any(marker in evidence_class for marker in _EMPIRICAL_CLASS_MARKERS):
                if "EMPIRICAL" in families:
                    findings.append(
                        Finding(
                            ValidationCode.EVIDENCE_CLASS_LAUNDERING,
                            "a non-empirical evidence class is presented as empirical",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
            if card.missing:
                findings.append(
                    Finding(
                        ValidationCode.STATISTIC_INCOMPLETE,
                        "statistic claim omits required N, small-N, period or OOS state",
                        claim_id=prepared.claim_id,
                        ref=source.ref,
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# layer
# ---------------------------------------------------------------------------


def validate_layer(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for prepared in claims:
        if prepared.draft.layer:
            if prepared.draft.layer not in LAYER_VOCABULARY:
                findings.append(
                    Finding(
                        ValidationCode.LAYER_LAUNDERING,
                        "claim uses a layer outside the frozen vocabulary",
                        claim_id=prepared.claim_id,
                    )
                )
            layers = {source.layer for source in prepared.sources if source.layer}
            if layers and prepared.draft.layer not in layers:
                findings.append(
                    Finding(
                        ValidationCode.LAYER_LAUNDERING,
                        "claim attributes the content to a different layer than its source",
                        claim_id=prepared.claim_id,
                    )
                )
            if prepared.draft.layer == "L1" and "L3" in layers:
                findings.append(
                    Finding(
                        ValidationCode.LAYER_LAUNDERING,
                        "an L3 destination is presented as a direct L1 entry",
                        claim_id=prepared.claim_id,
                    )
                )
        lowered = prepared.normalized
        for source in prepared.sources:
            facts = source.fact_map
            metric_class = (facts.get("metric_class") or facts.get("metric") or "").upper()
            if "PATH" in metric_class and "win rate" in lowered:
                findings.append(
                    Finding(
                        ValidationCode.LAYER_LAUNDERING,
                        "an L2 path statistic is presented as a setup win rate",
                        claim_id=prepared.claim_id,
                        ref=source.ref,
                    )
                )
                break
        if ("override" in lowered or "overrides" in lowered) and (
            "no-go" in lowered or "no go" in lowered
        ):
            if not admission.index.has_cross_layer_rule():
                findings.append(
                    Finding(
                        ValidationCode.LAYER_AUTHORITY_VIOLATION,
                        "a lower layer cannot override a higher-layer no-go without an encoded rule",
                        claim_id=prepared.claim_id,
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# setup and action
# ---------------------------------------------------------------------------


def setup_verdicts(admission: Admission) -> tuple[str, ...]:
    out: list[str] = []
    for entry in admission.index.setup_items():
        facts = entry.fact_map
        verdict = (
            facts.get("setup_verdict")
            or facts.get("verdict")
            or facts.get("eligibility")
            or entry.item.source_status
        ).upper()
        if verdict:
            out.append(verdict)
    return tuple(out)


def worst_setup_verdict(verdicts: tuple[str, ...]) -> str:
    known = [verdict for verdict in verdicts if verdict in SETUP_RANK]
    if not known:
        return ""
    return min(known, key=lambda verdict: SETUP_RANK[verdict])


def validate_setup(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    verdicts = setup_verdicts(admission)
    worst = worst_setup_verdict(verdicts)
    setup_facts = [entry.fact_map for entry in admission.index.setup_items()]

    for prepared in claims:
        if asserts_advice(prepared.text):
            findings.append(
                Finding(
                    ValidationCode.ADVICE_PROHIBITED,
                    "personalized advice, sizing or execution instruction is not an answer",
                    claim_id=prepared.claim_id,
                )
            )
        if not asserts_action(prepared.text):
            continue
        if not verdicts:
            findings.append(
                Finding(
                    ValidationCode.SETUP_NOT_ENCODED,
                    "no validated setup is encoded for the requested action",
                    claim_id=prepared.claim_id,
                )
            )
            continue
        if worst != "ELIGIBLE":
            findings.append(
                Finding(
                    ValidationCode.SETUP_NOT_ENCODED,
                    f"the encoded setup is {worst or 'UNRESOLVED'}; no action is authorized",
                    claim_id=prepared.claim_id,
                )
            )
            continue
        lowered = prepared.normalized
        if "watch" in lowered:
            findings.append(
                Finding(
                    ValidationCode.SETUP_FIELD_MISMATCH,
                    "claim states a milder eligibility than the encoded verdict",
                    claim_id=prepared.claim_id,
                )
            )
        encoded_values: set[str] = set()
        for facts in setup_facts:
            for key in ("levels", "targets", "trigger", "invalidation", "anchor", "range"):
                if facts.get(key):
                    encoded_values.update(number_tokens(facts[key]))
        for token in number_tokens(prepared.text):
            if encoded_values and token not in encoded_values:
                findings.append(
                    Finding(
                        ValidationCode.SETUP_FIELD_MISMATCH,
                        "claim states a setup level the package does not encode",
                        claim_id=prepared.claim_id,
                    )
                )
                break
    return findings


# ---------------------------------------------------------------------------
# status and generation
# ---------------------------------------------------------------------------


def validate_status(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for prepared in claims:
        sources = [source for source in prepared.sources if source.ref_type != "LIMITATION"]
        if not sources:
            continue
        labels = {source.label.value for source in sources}
        if prepared.draft.epistemic_label not in labels:
            findings.append(
                Finding(
                    ValidationCode.STATUS_LAUNDERING,
                    "claim status does not match the authorized source status",
                    claim_id=prepared.claim_id,
                )
            )
        non_current = labels & NON_CURRENT_EPISTEMIC_LABELS
        lowered = prepared.normalized
        if non_current and (
            asserts_current(prepared.text)
            or "validated" in lowered
            or "production" in lowered
            or "confirmed" in lowered
        ):
            findings.append(
                Finding(
                    ValidationCode.STATUS_LAUNDERING,
                    "non-current evidence is presented as current validated fact",
                    claim_id=prepared.claim_id,
                )
            )
        for source in sources:
            if prepared.draft.generation and source.item.generation:
                if prepared.draft.generation != source.item.generation:
                    findings.append(
                        Finding(
                            ValidationCode.GENERATION_LAUNDERING,
                            "claim generation does not match the authorized generation",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
                    break
    return findings


# ---------------------------------------------------------------------------
# freshness
# ---------------------------------------------------------------------------


def _stale_markers(entry: ResolvedItem) -> bool:
    facts = entry.fact_map
    tokens = " ".join(
        [
            facts.get("quality", ""),
            facts.get("staleness", ""),
            facts.get("freshness", ""),
            entry.item.source_status,
        ]
    ).upper()
    return any(marker in tokens for marker in ("STALE", "OLD_SNAPSHOT", "EXPIRED"))


def validate_freshness(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    as_of = admission.index.as_of_values()
    for prepared in claims:
        current = asserts_current(prepared.text) or any(
            source.ref_type == "INTELLIGENCE" for source in prepared.sources
        )
        if not current:
            continue
        if admission.policy.require_as_of_for_current and not as_of:
            claim_as_of = any(
                source.fact_map.get("as_of") or source.fact_map.get("data_cutoff")
                for source in prepared.sources
            )
            if not claim_as_of:
                findings.append(
                    Finding(
                        ValidationCode.MISSING_FRESHNESS,
                        "current-state claim states no data cutoff or as-of basis",
                        claim_id=prepared.claim_id,
                    )
                )
                continue
        if any(
            _stale_markers(source)
            and ("live" in prepared.normalized or asserts_current(prepared.text))
            for source in prepared.sources
        ):
            findings.append(
                Finding(
                    ValidationCode.STALE_PRESENTED_AS_LIVE,
                    "a stale snapshot is presented as a live observation",
                    claim_id=prepared.claim_id,
                )
            )
    return findings


def propagated_limitations(admission: Admission) -> tuple[str, ...]:
    """Unresolved runtime states that must stay visible in the answer."""

    out: list[str] = []
    for entry in admission.index.items:
        facts = entry.fact_map
        clock = (facts.get("clock", "") or "").upper()
        if clock in ("UNRESOLVED", "CLOCK_UNRESOLVED"):
            if "CLOCK_UNRESOLVED" not in out:
                out.append("CLOCK_UNRESOLVED")
        for value in (
            entry.item.source_status,
            facts.get("quality", ""),
            facts.get("data_quality", ""),
        ):
            upper = (value or "").upper()
            if upper in ("CLOCK_UNRESOLVED", "PROVIDER_NOT_CONFIGURED", "DATA_QUALITY_BLOCKED"):
                if upper not in out:
                    out.append(upper)
    return tuple(out)


# ---------------------------------------------------------------------------
# leakage
# ---------------------------------------------------------------------------


def reproduces_beyond(source: str, target: str, limit: int) -> bool:
    """True when ``target`` contains a contiguous ``source`` run over ``limit``."""

    if not source or not target:
        return False
    window = limit + 1
    if len(source) < window:
        return False
    return any(source[start : start + window] in target for start in range(len(source) - window + 1))


def validate_leakage(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    limit = max(1, admission.policy.quote_char_limit)
    bulk = admission.policy.corpus_bulk_limit
    quoted: dict[str, int] = {}

    for prepared in claims:
        lowered = prepared.normalized
        raw = prepared.text

        if any(token in lowered for token in _INTERNAL_TEXT_TOKENS) or is_internal_ref(raw.strip()):
            findings.append(
                Finding(
                    ValidationCode.LEAKAGE_INTERNAL_MATERIAL,
                    "claim renders internal material instead of user-facing provenance",
                    claim_id=prepared.claim_id,
                )
            )
        if any(token in lowered for token in _ENUMERATION_TOKENS):
            findings.append(
                Finding(
                    ValidationCode.LEAKAGE_ENUMERATION,
                    "claim discloses objects outside the authorized package",
                    claim_id=prepared.claim_id,
                )
            )
        if any(token in lowered for token in _SYSTEM_TEXT_TOKENS) or any(
            token in lowered for token in _UNTRUSTED_INSTRUCTION_TOKENS
        ):
            findings.append(
                Finding(
                    ValidationCode.LEAKAGE_SYSTEM,
                    "claim discloses control material or promotes injected instructions",
                    claim_id=prepared.claim_id,
                )
            )
        for source in prepared.sources:
            if source.item.trust_class is TrustClass.UNTRUSTED_DATA and any(
                token in lowered for token in _UNTRUSTED_INSTRUCTION_TOKENS
            ):
                findings.append(
                    Finding(
                        ValidationCode.UNTRUSTED_INSTRUCTION,
                        "untrusted package text is rendered as an instruction",
                        claim_id=prepared.claim_id,
                        ref=source.ref,
                    )
                )
                break
            if source.item.text:
                if reproduces_beyond(source.item.text, raw, limit):
                    findings.append(
                        Finding(
                            ValidationCode.LEAKAGE_CORPUS,
                            "claim reproduces corpus text beyond the allowed quote scope",
                            claim_id=prepared.claim_id,
                            ref=source.ref,
                        )
                    )
                    break
                quoted[source.ref] = quoted.get(source.ref, 0) + len(raw)
        if any(length > bulk for length in quoted.values()):
            findings.append(
                Finding(
                    ValidationCode.LEAKAGE_CORPUS,
                    "answer reproduces bulk corpus material",
                    claim_id=prepared.claim_id,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# citations
# ---------------------------------------------------------------------------


def validate_citations(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for prepared in claims:
        if not prepared.draft.source_refs:
            findings.append(
                Finding(
                    ValidationCode.CITATION_REQUIRED,
                    "material claim carries no citation",
                    claim_id=prepared.claim_id,
                )
            )
        if prepared.unresolved_refs:
            findings.append(
                Finding(
                    ValidationCode.CITATION_UNRESOLVED,
                    "claim cites a reference that does not resolve inside the package",
                    claim_id=prepared.claim_id,
                )
            )
        if prepared.draft.source_refs and not prepared.sources:
            findings.append(
                Finding(
                    ValidationCode.CITATION_UNRESOLVED,
                    "claim citation does not support the claim",
                    claim_id=prepared.claim_id,
                )
            )
    for link in admission.draft.numbers:
        owning = [
            claim
            for claim in claims
            if link.value_text in claim.text or link.source_ref_id in claim.draft.source_refs
        ]
        if not owning:
            continue
        cited = any(
            link.source_ref_id in claim.draft.source_refs
            or link.source_ref_id in {source.ref for source in claim.sources}
            for claim in owning
        )
        if not cited:
            findings.append(
                Finding(
                    ValidationCode.CITATION_NUMERIC_MISMATCH,
                    "numeric claim cites a different source than its numeric link",
                    claim_id=owning[0].claim_id,
                    ref=link.source_ref_id,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------


def validate_assembly(admission: Admission, claims: tuple[PreparedClaim, ...]) -> list[Finding]:
    findings: list[Finding] = []
    if not claims:
        findings.append(
            Finding(ValidationCode.EMPTY_DRAFT, "the draft carries no material claim to validate")
        )
    return findings


VALIDATORS = (
    ("upstream", validate_upstream),
    ("numerical", validate_numerical),
    ("layer", validate_layer),
    ("setup", validate_setup),
    ("status", validate_status),
    ("freshness", validate_freshness),
    ("leakage", validate_leakage),
    ("citation", validate_citations),
    ("assembly", validate_assembly),
)


def run_validators(
    admission: Admission, claims: tuple[PreparedClaim, ...]
) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for _name, validator in VALIDATORS:
        findings.extend(validator(admission, claims))
    return tuple(findings)


__all__ = [
    "Finding",
    "PreparedClaim",
    "run_validators",
    "validate_upstream",
    "validate_numerical",
    "validate_layer",
    "validate_setup",
    "validate_status",
    "validate_freshness",
    "validate_leakage",
    "validate_citations",
    "validate_assembly",
    "VALIDATORS",
    "normalize",
    "number_tokens",
    "asserts_current",
    "asserts_action",
    "worst_setup_verdict",
    "setup_verdicts",
    "propagated_limitations",
]
