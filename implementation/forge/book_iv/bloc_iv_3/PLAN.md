# BOOK IV / BLOC IV.3 — CONTEXT PACKAGER
## PLAN — BA-28 RUNG 1 (PLANNING ONLY)

**Status:** Proposed; implementation not started.
**Authority:** Operator-directed BA-28 Rung 1.
**Base HEAD:** `23b2b9e19f1b1dee59c4aa9379a35a1dfed981b7`
**Branch:** `forge`
**Scope:** Book IV / Bloc IV.3 only. IV.1 and IV.2 are frozen and ratified.
**Contract:** `CONTEXT_CONTRACT_V1` (proposed)

---

## 0. FOUNDATION VERIFICATION

Verified against the working tree, not prior narrative.

| # | Check | Result |
|---|---|---|
| 1 | Local HEAD equals `origin/forge` | PASS — `23b2b9e19f1b1dee59c4aa9379a35a1dfed981b7` |
| 2 | Expected BA-28 head | PASS — exact match |
| 3 | IV.1 interpreter | PASS — 60/60; contract `ASK_QUERY_CONTRACT_V1` |
| 4 | IV.2 retrieval | PASS — 72/72; contract `RETRIEVAL_CONTRACT_V1` |
| 5 | IV.2 golden fixtures | PASS — 18/18 byte-reproducible |
| 6 | Book III synthetic integration | PASS — 96/96 |
| 7 | Full repository | PASS — 2,210 passed, 29 pre-existing skips |
| 8 | Current-head CI | PASS — run `42414373970`, `test` + `postgres` |
| 9 | Book I canonical/retrieval | Present and frozen; consumed read-only |
| 10 | Book II policy | Present and frozen; no second policy engine |
| 11 | Book III intelligence | Present; provider `NOT_CONFIGURED` |
| 12 | Routes | Frozen at `145757e0…d190af` |
| 13 | Migrations | `[1,2,3,4]`; no migration added |
| 14 | IV.3 package | ABSENT — this is planning only |
| 15 | `.bu_tmp/` | Preserved |

No IV.3 source, test or fixture exists at this head. This rung creates only the
four planning artifacts named in §13.

---

## 1. MISSION AND CORE LAW

IV.3 converts:

**`AskCerebusQueryPlan` + `AuthorizedRetrievalBundle` + optional already-authorized detail projections
→ `AuthorizedContextPackage` + `AuthorizedContextManifest`**

The future LLM receives only the package, never raw retrieval results, raw
canonical bodies, denied identifiers or unrestricted corpus text.

**The packager preserves truth, provenance, permissions, uncertainty and no-go
restrictions. It does not manufacture facts, validation, eligibility,
entitlement or current market state.**

This is a packaging and minimization boundary. It is not a retriever, policy
engine, canonical store, answer compiler or LLM gateway.

---

## 2. VERIFIED UPSTREAM API MAP

### 2.1 IV.1 plan

`AskCerebusQueryPlan` supplies:

`query_contract_version`, `plan_id`, `intent`, `entities`, `model_ids`,
`setup_ids`, `market`, `layer`, `time_scope`, `requested_depth`,
`effective_depth`, `requires_live_intelligence`, `requires_evidence`,
`requires_lineage`, `requires_setup_context`, `actionable`,
`requested_fields`, `confidence`, `ambiguities`.

IV.3 reads these fields; it never infers, widens or removes an ambiguity.

### 2.2 IV.2 bundle

`AuthorizedRetrievalBundle` supplies:

- `query_plan_id`, `retrieval_contract_version`, `bundle_id`;
- `canonical_refs`: id, type, version, status, layer, market scope, exposure,
  support classification, generation;
- `claim_refs`: claim id, model ids/versions, identity key, status, evidence
  ids, generation, optional result value, join status;
- `evidence_refs`: evidence id, claim ids, status, provenance ids, support
  classification, gaps, OOS status;
- `intelligence_refs`: request kind, snapshot id/hash, view, quality, no-go,
  model id/version, refusal;
- `lineage_refs`, `semantic_passages`, `negative_refs`;
- `limitations`, `refusals`, trace, selected generation/index hash.

The bundle does **not** contain free-form answers, eligibility verdicts,
entitlement grants, computed market values, or a plan body.

### 2.3 Actual dependency gaps discovered

| Gap | Actual condition | IV.3 handling |
|---|---|---|
| G1 snapshot values absent | `IntelligenceRef` carries snapshot identity/quality/no-go but not levels or prices | Accept an optional `AuthorizedContextDetail.intelligence` projection whose snapshot id must already exist in the bundle; otherwise emit `DETAIL_NOT_SUPPLIED` and no values |
| G2 statistical bodies absent | `EvidenceRef` carries status/provenance/OOS but not metric, population, period or sample size | Accept optional `AuthorizedContextDetail.statistics` keyed by an already-authorized evidence id; otherwise `N_NOT_PROVIDED` / `SMALL_N_UNRESOLVED` |
| G3 current provider absent | `market_data: NOT_CONFIGURED` | Preserve `PROVIDER_NOT_CONFIGURED`; never synthesize a current fact |
| G4 history not durable | no durable snapshot store | Preserve `HISTORICAL_UNAVAILABLE`; never substitute current |
| G5 entitlement projection absent | no Book VI capability projection | No package field grants or widens exposure |
| G6 Setup Card schema mismatch | `III.5-DEFECT-1` remains OPEN | Package setup refs verbatim; no card schema operation |
| G7 real semantic index absent | deterministic support only | Excerpts are untrusted, bounded support; never authority |

G1/G2 are explicit optional inputs, not new retrieval calls. IV.3 must never
load a snapshot or evidence body. Detail records whose id is not already in the
bundle are rejected as `CONTEXT_DETAIL_UNAUTHORIZED`.

### 2.4 Frozen hashes

EOL-normalized SHA-256 of the contracts read for this plan:

| File | SHA-256 |
|---|---|
| `app/forge/ask_cerebus/interpreter/plan.py` | `c43a34ba6ef085108743c2c87c1c1f13d85c134360a6e4e7f3067046f9fd344b` |
| `app/forge/ask_cerebus/retrieval/bundle.py` | `b38b356e01b349fe0110ce7ebd518fd1b3e9d1c82a7f8b979ac088019acc3455` |
| `app/forge/ask_cerebus/retrieval/refs.py` | `bbe1b937d6aa0bd7d0c26c8e0f7f5ba7dfa2ecee7f816dc9461b620d0961daa2` |
| `app/forge/ask_cerebus/retrieval/trace.py` | `6f8f08009da67975017de9c86263a52d0a72753afacf58f74aff7a91ec92e44d` |
| `app/forge/ask_cerebus/retrieval/service.py` | `d4ef64f9d3f994b08c331b48a2e720aa345f92af02d8b32a2d0feb9707d5fd83` |
| `app/forge/ask_cerebus/retrieval/enums.py` | `7c4604af7f8fc9eb3c9461d4ec938f85b99daa10b46c35422c4909f764e0279e` |
| `app/forge/ask_cerebus/retrieval/versions.py` | `b49f9c51439e6da1e8b46138660dbda6bc61c1103946f51ada93424237693132` |
| `app/forge/retrieval/service.py` | `0da911be828a0d5747b8cfe022ab20df3cd8187865ecb42232ddb4177339ade0` |
| `app/forge/retrieval/query.py` | `7bf0d614c2467b2d69700a6531fbc22bd6e713c2609ec498838cf62d9c2ce60d` |
| `app/forge/retrieval/objects.py` | `1114e4712175be974594094b05a8fdee6938c8b07ce533283cedac8e9b28403f` |
| `app/forge/policy.py` | `f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc` |
| `app/forge/service/policy_enforcement.py` | `9ccc3b72f77fca0cb3fd0685128fd96a2f0ce8ca975b532d96646d285476e381` |
| `app/forge/intelligence_api/requests.py` | `b2e484023dc55d1fafd90136a6654f07ba713ddfd8ca7d8da2b0ca4499237146` |
| `app/forge/intelligence_api/contracts.py` | `7d8f90adf8aeca993b94d473f61fe16ea13170a1cd977cb47fb186d64697d4f0` |
| `app/forge/intelligence_api/policy_gate.py` | `d805aa915383417eed0ef08581b2400f978a928f0d875460afb5559ad75c9ba9` |
| `app/forge/setup_engine/registry.py` | `1b900b6b93b9df6ca6d5c1173ac8c07b1b7e3d7b7404b40eed2443df10999807` |
| `app/forge/service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

---

## 3. CONTEXT CONTRACT

### 3.1 Closed enums

```
ContextContractVersion = CONTEXT_CONTRACT_V1
ContextOutcome         = RESOLVED | PARTIAL | REFUSED
ContextSectionId       = QUERY_CONTRACT | CURRENT_INTELLIGENCE | CANONICAL_MODEL |
                         SETUP | CLAIMS | EVIDENCE | LINEAGE_TERMS |
                         LIMITATIONS_NEGATIVE | GENERAL_KNOWLEDGE
EpistemicLabel         = CANONICAL | VALIDATED | FORWARD_OOS | CANDIDATE |
                         RESEARCH_FLAG | HISTORICAL | NEGATIVE_EVIDENCE |
                         PARKED | SUPERSEDED | INFERENCE | GENERAL_KNOWLEDGE |
                         INSUFFICIENT_EVIDENCE
TrustClass             = TRUSTED_CONTROL | UNTRUSTED_DATA
SmallNFlag             = TRUE | FALSE | UNRESOLVED
ContextIssueCode       = MISSING_EVIDENCE | CONTEXT_BUDGET_TRIMMED |
                         EPISTEMIC_LABEL_UNRESOLVED | DETAIL_NOT_SUPPLIED |
                         SMALL_N_UNRESOLVED | EXPOSURE_EXCLUDED |
                         UPSTREAM_LIMITATION | UPSTREAM_REFUSAL |
                         DUPLICATE_SUPPRESSED | INAPPLICABLE_SECTION
ContextRefusalCode     = CONTEXT_CONTRACT_UNSUPPORTED | CONTEXT_INPUT_MALFORMED |
                         CONTEXT_BUDGET_EXCEEDED | CONTEXT_EXPOSURE_VIOLATION |
                         CONTEXT_INTEGRITY_FAILURE | CONTEXT_DETAIL_UNAUTHORIZED
```

`INFERENCE` is reserved for a later authorized answer layer. IV.3 never emits
it.

### 3.2 `AuthorizedContextDetail`

Optional, already-authorized projections. IV.3 does not load them.

```
AuthorizedContextDetail
  intelligence: tuple[AuthorizedIntelligenceFact, ...]
  statistics:   tuple[AuthorizedEvidenceStatistic, ...]

AuthorizedIntelligenceFact
  snapshot_id, field_path, value_text, unit, layer, quality, synthetic: bool

AuthorizedEvidenceStatistic
  evidence_id, metric, event_identity, conditioning_population,
  sample_size: int | None, research_period, small_n_flag,
  small_n_threshold_ref, oos_status
```

Rules:

1. Every `snapshot_id` must already appear in `bundle.intelligence_refs`.
2. Every `evidence_id` must already appear in `bundle.evidence_refs`.
3. Unknown ids refuse the detail or the package; they never enter a section.
4. No detail record can change status, exposure, layer, generation or identity.
5. Synthetic detail remains labelled `SYNTHETIC_FIXTURE` and cannot satisfy
   empirical evidence.

### 3.3 Package

```
AuthorizedContextPackage
  context_contract_version: ContextContractVersion
  query_plan_id: str
  retrieval_bundle_id: str
  outcome: ContextOutcome
  sections: tuple[ContextSection, ...]          # frozen section order
  omissions: tuple[ContextOmission, ...]
  issues: tuple[ContextIssue, ...]              # bounded codes only
  refusals: tuple[ContextRefusal, ...]
  token_accounting: TokenAccounting
  manifest: AuthorizedContextManifest
  package_id: str                               # PKG.<32 hex>
```

No `answer`, `recommendation`, `eligibility`, `entitlement`, `position_size`,
`order_intent`, `probability`, `win_rate` or `confidence` field exists.

### 3.4 Manifest

```
AuthorizedContextManifest
  manifest_version: str                          # CONTEXT_MANIFEST_V1
  context_contract_version: str
  query_plan_id: str
  retrieval_bundle_id: str
  included_section_ids: tuple[str, ...]
  included_object_ids: tuple[str, ...]           # authorized refs only
  omitted_section_ids: tuple[str, ...]
  estimator_version: str
  estimated_units: int
  section_digests: tuple[tuple[str, str], ...]
  trust_boundary_hash: str
  manifest_digest: str                           # MFD.<64 hex>
```

`included_object_ids` is the union of source-reference ids actually packaged.
It never contains rejected, internal, secret or denied ids.

### 3.5 Section and item

```
ContextSection
  section_id: ContextSectionId
  items: tuple[ContextItem, ...]
  omissions: tuple[ContextOmission, ...]
  estimated_units: int
  mandatory_units: int

ContextItem
  item_id: str                    # CTX.<section>.<ordinal>, never canonical
  source_ref_id: str
  source_ref_type: str
  source_status: str              # verbatim upstream status
  epistemic_label: EpistemicLabel
  layer: str
  exposure: str
  generation: str
  trust_class: TrustClass
  facts: tuple[ContextFact, ...]
  text: str | None                # UNTRUSTED_DATA only
  quote_scope: str
  provenance_refs: tuple[str, ...]
  evidence_refs: tuple[str, ...]
  token_units: int
  priority: int
  mandatory: bool

ContextFact
  key: str
  value_text: str
  unit: str
```

The fact-key allowlist is frozen: `identity`, `version`, `status`, `layer`,
`market_scope`, `generation`, `support_classification`, `join_status`,
`identity_key`, `result_value`, `metric`, `event_identity`,
`conditioning_population`, `sample_size`, `research_period`, `oos_status`,
`quality`, `no_go`, `setup_id`, `setup_version`, `setup_class`,
`eligibility`, `surface`, `snapshot_id`, `snapshot_hash`, `view`, `refusal`,
`intent`, `time_scope`, `depth`, `actionable`, `ambiguity`,
`general_knowledge_allowed`.

No free-form `body`, `content`, `code`, `secret`, `instructions` or `prompt`
field exists.

---

## 4. SECTION HIERARCHY

| Order | Section | Source | Inclusion | Omission |
|---:|---|---|---|---|
| 0 | `QUERY_CONTRACT` | IV.1 plan | Always; require `plan.plan_id == bundle.query_plan_id` | Only malformed/unsupported input refusal |
| 1 | `CURRENT_INTELLIGENCE` | IV.2 `intelligence_refs` + authorized detail | Current/AS_OF when plan requires; quality/no-go/refusal always; values only with detail | `PROVIDER_NOT_CONFIGURED`, `HISTORICAL_UNAVAILABLE`, detail absent |
| 2 | `CLAIMS` | IV.2 `claim_refs` | Claim identity always; result only when evidence join and label permit | Unsupported number; duplicate |
| 2 | `EVIDENCE` | IV.2 `evidence_refs` + authorized detail | Every included claim's evidence refs; status/provenance | Missing evidence, duplicate |
| 3 | `CANONICAL_MODEL` | IV.2 `canonical_refs` | Model/doctrine/term refs for resolved plan | No applicable model |
| 4 | `SETUP` | IV.2 canonical/setup refs | Setup identity, class, eligibility, surface verbatim | No setup context |
| 5 | `LIMITATIONS_NEGATIVE` | IV.2 limitations, refusals, negative refs | Always when non-empty; no-go mandatory | Never silently omitted |
| 6 | `LINEAGE_TERMS` | IV.2 lineage refs + terms | Generation-sensitive lineage and terms | No lineage/term refs |
| 7 | `GENERAL_KNOWLEDGE` | Allowance marker only | Only when plan permits general knowledge | Never carries CEREBUS facts or numbers |

`LIMITATIONS_NEGATIVE` is mandatory when it contains no-go, invalidation,
refusal or insufficiency. It is not a lower-priority narrative section.

---

## 5. CANONICAL COMPRESSION

1. Prefer typed canonical references and allowlisted facts over passage text.
2. A semantic passage is included only if:
   - its object id is already authorized;
   - it adds bounded nuance/provenance;
   - quote scope permits it;
   - the section has remaining budget.
3. A raw source excerpt is omitted when the canonical item already carries the
   fact. It is never used to supply a missing canonical value.
4. Excerpt maximum: 1,000 UTF-8 characters, normalized to LF and stripped of
   trailing whitespace.
5. Excerpts are `UNTRUSTED_DATA`; their `quote_scope` and exposure remain
   attached.
6. Duplicate identities are collapsed by `source_ref_id`, not by matching text
   or similarity.
7. Deduplication may merge provenance/evidence references for the same
   identity; it may not merge statuses, generations, layers or numeric values.
8. Deterministic item order:

```
(section order, priority, source_ref_type, source_ref_id,
 generation, ordinal, text_sha256)
```

Semantic support is ordered after canonical items in the same section.

---

## 6. TOKEN BUDGET AND ESTIMATOR

### 6.1 Estimator

`CTX_UTF8_QUARTER_V1`:

```
item_units = ceil(utf8_bytes(canonical_json(control_facts)) / 4)
           + ceil(utf8_bytes(text or "") / 4)
           + 8
section_units = 16 + sum(item_units)
```

This is a reproducible packing estimate, not a provider tokenizer count. A
future `TokenizerPort` may replace it only by a new contract version.

### 6.2 Budget

```
DEFAULT_MAX_UNITS = 4096
DEFAULT_SAFETY_RESERVE_UNITS = 512
available_units = max_units - safety_reserve_units
MAX_EXCERPT_CHARS = 1000
MAX_ITEMS_PER_SECTION = 64
```

No provider-specific token accuracy is claimed.

### 6.3 Priority and trimming

| Priority | Content | Trim behavior |
|---:|---|---|
| mandatory | query contract; no-go/invalidation; refusal; evidence insufficiency; missing-evidence control | Never trimmed |
| 1 | current state/quality/restrictions | Trim optional facts last |
| 2 | direct claim/evidence | Trim after current |
| 3 | model doctrine | Trim after claims/evidence |
| 4 | setup context | Trim after model |
| 5 | negative evidence not already mandatory | Trim after setup |
| 6 | lineage/terms | Trim after negative |
| 7 | supplementary semantic context | Trim first |

Trimming is by whole item in reverse priority with stable `source_ref_id` order.
A section header and its mandatory items remain. Every removed optional item
appears in the omission ledger.

If mandatory units exceed `available_units`, return `REFUSED` with
`CONTEXT_BUDGET_EXCEEDED`; emit no partial context and no untrusted text.

If optional items are trimmed, return `PARTIAL` with
`CONTEXT_BUDGET_TRIMMED`; all mandatory restrictions remain.

---

## 7. EPISTEMIC AND LAYER INTEGRITY

### 7.1 Status mapping

| Upstream status | Epistemic label |
|---|---|
| direct canonical object identity | `CANONICAL` |
| `VALIDATED` | `VALIDATED` |
| `FORWARD_OOS` | `FORWARD_OOS` |
| `CANDIDATE` | `CANDIDATE` |
| `RESEARCH_FLAG` | `RESEARCH_FLAG` |
| `HISTORICAL` | `HISTORICAL` |
| `PARKED` | `PARKED` |
| `SUPERSEDED` | `SUPERSEDED` |
| `FALSIFIED`, `NO_GO`, `INTERNAL_CONTRADICTION`, `IMPLEMENTATION_NOT_PARITY_SAFE` | `NEGATIVE_EVIDENCE` |
| `OBSERVED`, `DESCRIPTIVE`, `REPRODUCTION_REQUIRED`, unmapped | `INSUFFICIENT_EVIDENCE` with `EPISTEMIC_LABEL_UNRESOLVED` |
| missing numeric evidence | `INSUFFICIENT_EVIDENCE` |
| general-knowledge allowance marker | `GENERAL_KNOWLEDGE` |

`source_status` is preserved verbatim in every item. `CANONICAL` identifies
source authority, not numerical validation. A number is packable only with an
evidence join that permits it.

No packaging operation promotes a label. `INFERENCE` is forbidden in IV.3.

### 7.2 Layer rules

- Every item carries the exact source `layer`.
- An L3 statistic cannot populate an L1 setup-performance field.
- An L2 path fact cannot become entry authority.
- `HISTORICAL` cannot be relabelled current.
- JPY `MANUAL_OPERATOR` cannot become execution permission.
- Fib `RESEARCH_ONLY` cannot become production eligibility.
- Cross-layer facts remain separate; no confluence score is computed.

### 7.3 Small-N and missing evidence

- N is included only from `AuthorizedEvidenceStatistic` or an authoritative
  upstream fact.
- No default N, no inferred N and no N from a request.
- A small-N flag is `TRUE`/`FALSE` only with a governed threshold reference;
  otherwise `UNRESOLVED`.
- The actual N is still shown when the threshold is unresolved.
- Missing evidence emits `MISSING_EVIDENCE`; the numerical `result_value` is
  omitted.
- Conflicting evidence keeps both refs and both statuses; no winner.
- Historical generations remain separate; no newest-version fallback.

---

## 8. ANTI-INJECTION BOUNDARY

1. Every retrieved passage is `UNTRUSTED_DATA`.
2. Control facts and untrusted text are separate fields and separate canonical
   digest domains.
3. Source text may not create, remove or modify a control item.
4. Source text cannot grant entitlement, alter exposure, change epistemic
   label/layer/status, insert a canonical id or statistic, promote a setup or
   clear a no-go.
5. Instruction-like text is preserved only as quoted data with a SHA-256; it is
   never executed or promoted into the control block.
6. `GENERAL_KNOWLEDGE` is an allowance marker, not a place to inject CEREBUS
   facts or external numeric authority.
7. A detected attempt is retained as data plus a bounded issue; it cannot cause
   a privileged state transition.

The package is not a prompt. IV.4 owns instruction assembly and must treat the
whole package as data except for the typed control fields defined here.

---

## 9. EXPOSURE MINIMIZATION

Field-level allowlist only. The packager must:

- exclude `INTERNAL_METHOD` and `INTERNAL_CODE` unconditionally;
- never widen `exposure` or add an exposure not present upstream;
- never include denied ids, hidden-object existence or protected names;
- never include secrets, source code, internal method prose or unrestricted
  corpus bodies;
- cap excerpts at 1,000 characters and semantic items at 64 per section;
- include only authorized object ids in the manifest;
- represent omissions by bounded section/reason codes, never by denied ids.

An internal or unauthorized detail record fails closed with
`CONTEXT_EXPOSURE_VIOLATION` or `CONTEXT_DETAIL_UNAUTHORIZED`.
No “the answer would not quote it” exception exists.

---

## 10. DETERMINISTIC MANIFEST AND SERIALIZATION

- Canonical JSON: sorted keys, separators `,`/`:`, UTF-8, `ensure_ascii=False`.
- No wall clock, random value, process id, path or environment value in a hash.
- `section_digests`: SHA-256 of each canonical section payload.
- `trust_boundary_hash`: SHA-256 of the canonical control block.
- `manifest_digest`: `MFD.` + SHA-256 of canonical manifest payload excluding
  `manifest_digest`.
- `package_id`: `PKG.` + SHA-256 of canonical package payload excluding
  `package_id`.
- Identical plan, bundle, detail, budget and contract must produce identical
  package and manifest ids.
- Different index generation, bundle id, detail value, budget, contract or
  selector version must change the applicable identity.

---

## 11. FAILURE AND REFUSAL BEHAVIOR

| Condition | Outcome | Required behavior |
|---|---|---|
| Unsupported plan/bundle contract | `REFUSED` | `CONTEXT_CONTRACT_UNSUPPORTED`; no sections |
| Malformed bundle or ID mismatch | `REFUSED` | `CONTEXT_INPUT_MALFORMED`; no context |
| Mandatory units exceed budget | `REFUSED` | `CONTEXT_BUDGET_EXCEEDED`; no untrusted text |
| Internal/unauthorized detail | `REFUSED` | `CONTEXT_EXPOSURE_VIOLATION` / `CONTEXT_DETAIL_UNAUTHORIZED` |
| Broken deterministic invariant | `REFUSED` | `CONTEXT_INTEGRITY_FAILURE` |
| Bundle partial | `PARTIAL` | Preserve every limitation/refusal |
| Missing evidence | `PARTIAL` | `MISSING_EVIDENCE`, known model context retained, no number |
| Optional trim | `PARTIAL` | Omission ledger + `CONTEXT_BUDGET_TRIMMED` |
| Bundle refused | `REFUSED` | Safe upstream refusal propagation; no claims/numbers |

Refusals are values, not exceptions crossing the boundary.

---

## 12. PROPOSED ARCHITECTURE (NOT IMPLEMENTED)

```
app/forge/ask_cerebus/context/
    versions.py       CONTEXT_CONTRACT_V1, CONTEXT_MANIFEST_V1
    enums.py          sections, outcomes, labels, trust, issues, refusals
    schema.py         package, manifest, section, item, detail, accounting
    selector.py       applicable sections and source mapping
    compression.py    canonical-first selection, dedupe, excerpts
    budgeting.py      estimator, mandatory floor, trim, omission ledger
    labels.py         status -> epistemic label, layer/small-N guards
    trust.py          control/data separation, exposure allowlist
    manifest.py       canonical JSON, section digests, package/manifest ids
    service.py        plan + bundle + optional detail -> package
    __init__.py       public surface
```

No loader, provider, vector store, LLM, database, route or migration is part of
this package.

---

## 13. DELIVERABLES

Exactly:

1. `implementation/forge/book_iv/bloc_iv_3/PLAN.md`
2. `implementation/forge/book_iv/bloc_iv_3/ACCEPTANCE.md`
3. `implementation/forge/book_iv/bloc_iv_3/FEASIBILITY_GATE.md`
4. `implementation/forge/book_iv/bloc_iv_3/DEPENDENCY_HANDOFF.md`

No source, test, fixture, migration or route file is part of this rung.

---

## 14. DOWNSTREAM HANDOFF SUMMARY

- **IV.4** receives only `AuthorizedContextPackage`; never the raw bundle.
- **IV.5** may explain only facts carrying an admissible epistemic label and
  must preserve all issues/refusals.
- **IV.6** evaluates package reproducibility, exposure safety, injection
  resistance and the twenty Q3 fixtures.
- **Book V** displays package facts without recomputing values.
- **Book VI** owns commercial entitlement; IV.3 does not project it.
- **Book VII** owns real semantic indexes, tokenizer accuracy and governed
  statistical bodies.
- **Book III** owns provider/history; IV.3 cannot fill their absences.

---

## 15. IMPLEMENTATION-READINESS VERDICT

**READY FOR IV.3 RUNG 2 IMPLEMENTATION** of the deterministic context contract,
subject to:

- 92 requirements and 92 named tests;
- 20 golden fixtures;
- F3/F4 limitations preserved rather than faked;
- no modification of IV.1, IV.2, Book I/II/III, routes, migrations or provider
  seam;
- no LLM, network, vector or real tokenizer dependency.

**Not ready to claim:** live current context, production tokenizer accuracy,
complete statistical bodies, commercial entitlement, durable history, or a
production GO.
