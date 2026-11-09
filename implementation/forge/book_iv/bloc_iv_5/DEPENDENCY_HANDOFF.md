# BOOK IV / BLOC IV.5 — DEPENDENCY HANDOFF
## BA-30 RUNG 1

**Contract:** `ASK_ANSWER_CONTRACT_V1` (proposed)
**Base HEAD:** `b6018bb1c3923093981ffb4646a7798abf45b922`
**Upstream:** IV.1 query -> IV.2 retrieval -> IV.3 context -> IV.4 gateway draft
**Downstream:** IV.6 evaluation -> Book V presentation
**Status:** planning only; no implementation or credential exists.

---

## 1. FROZEN CHAIN

```
IV.1 ASK_QUERY_CONTRACT_V1
  -> IV.2 RETRIEVAL_CONTRACT_V1
  -> IV.3 CONTEXT_CONTRACT_V1 (AuthorizedContextPackage + Manifest)
  -> IV.4 ASK_GATEWAY_CONTRACT_V1 (GatewayDraft status=UNVALIDATED)
  -> IV.5 ASK_ANSWER_CONTRACT_V1 (ValidatedAnswer | GovernedAnswerRefusal)
  -> IV.6 evaluation
  -> Book V presentation
```

IV.5 may not bypass, re-run, widen or reinterpret any earlier stage. It does
not receive an IV.2 bundle, raw corpus, database handle, URL or canonical body,
and it cannot obtain one.

---

## 2. INPUT CONTRACT TO IV.5

### 2.1 Required input

- one `GatewayDraft` where `status is DraftStatus.UNVALIDATED`;
- the same `AuthorizedContextPackage` the draft names;
- the same `AuthorizedContextManifest`;
- an `AnswerPolicy` version (materiality, wording, citation surface);
- an optional deterministic clock.

### 2.2 Admission checks

| Check | Failure code |
|---|---|
| draft status is `UNVALIDATED` | `DRAFT_NOT_UNVALIDATED` |
| `package_id` / `manifest_id` / `query_plan_id` agree across draft and inputs | `ANSWER_IDENTITY_MISMATCH` |
| `context_contract_version == CONTEXT_CONTRACT_V1` | `ANSWER_CONTEXT_REFUSED` |
| package `outcome is not REFUSED` | `ANSWER_CONTEXT_REFUSED` |
| manifest present and `manifest_digest == compute_digest()` | `ANSWER_MANIFEST_INVALID` |

Admission never invokes a provider or retriever and never mutates the package.

### 2.3 What must never be accepted directly

- a second draft, a regenerated draft or a "repaired" model response;
- a different package or manifest, including one with the same query plan;
- raw retrieval objects, canonical bodies or an arbitrary URL;
- client-supplied status, layer, eligibility or entitlement hints;
- API keys, cookies, auth headers or provider secrets;
- prose-only model output that bypassed `parse_draft`.

---

## 3. OUTPUT CONTRACT

### 3.1 `ValidatedAnswer`

| Field | Meaning |
|---|---|
| `answer_contract_version` | `ASK_ANSWER_CONTRACT_V1` |
| `answer_schema_version` | `ANSWER_SECTION_SCHEMA_V1` |
| `validator_set_version` | `VALIDATOR_SET_V1` |
| `answer_id` | deterministic `ANS.` identity |
| `depth` | `BEGINNER` / `OPERATOR` / `RESEARCHER` |
| `sections` | ordered depth-specific semantic blocks |
| `claims` | resolved text + epistemic label + layer + generation + citations |
| `citations` | ordered, deduplicated, user-facing provenance refs |
| `numbers` | authorized value text + citation + source ref |
| `limitations` | no-go, insufficiency, conflict, unresolved markers |
| `freshness` | `as_of` / data cutoff / stale marker where material |
| `validation` | ordered validator codes; all passed |
| `record` | `FinalResponseRecord` |

Every field is derived from the package. `ValidatedAnswer` is not canonical
truth; it is a bounded, citation-backed explanation of canonical truth.

### 3.2 `GovernedAnswerRefusal`

| Field | Meaning |
|---|---|
| `answer_refusal_code` | one of the six frozen codes |
| `detail` | safe statement of the failing check / unavailable subject |
| `failing_codes` | ordered validator codes that caused the refusal |
| `identity` | package/manifest/query/draft identity |
| `record` | `FinalResponseRecord` |

### 3.3 `FinalResponseRecord`

Fields: `record_version`, `answer_id`, contract/validator versions, `outcome`,
`answer_refusal_code`, package/manifest/query identity, route/prompt/provider/model
identity, `depth`, `cited_refs`, `claim_statuses`, `validation_codes`, `as_of`,
`latency_ms`, `cost_usd`, `cost_basis`, `prose_retained=false`.

The record is safe metadata. It excludes prompts, package bodies, provider
payloads, credentials and account identifiers.

---

## 4. VALIDATION AND REFUSAL CODES

### 4.1 Six answer refusal codes (exhaustive)

| Code | Meaning |
|---|---|
| `INSUFFICIENT_EVIDENCE` | The package does not support the requested claim |
| `CURRENT_DATA_UNAVAILABLE` | Current state cannot be established or is stale |
| `MODEL_VERSION_UNAVAILABLE` | The requested model/version is not encoded |
| `SETUP_NOT_ENCODED` | No validated setup exists for an action request |
| `ACCESS_NOT_ENTITLED` | The package encodes a denial for this scope |
| `AMBIGUOUS_SCOPE` | The request cannot be resolved to one scope |

Precedence: `ACCESS_NOT_ENTITLED > AMBIGUOUS_SCOPE > MODEL_VERSION_UNAVAILABLE >
CURRENT_DATA_UNAVAILABLE > SETUP_NOT_ENCODED > INSUFFICIENT_EVIDENCE`.

### 4.2 Validation codes (recorded, cause a refusal)

| Group | Codes |
|---|---|
| Numerical | `NUMERIC_EVIDENCE_MISSING`, `NUMERIC_MISMATCH`, `NUMERIC_UNIT_MISMATCH`, `METRIC_SUBSTITUTION`, `EVIDENCE_CLASS_LAUNDERING`, `STATISTIC_INCOMPLETE` |
| Citation | `CITATION_REQUIRED`, `CITATION_UNRESOLVED`, `CITATION_NUMERIC_MISMATCH` |
| Layer | `LAYER_LAUNDERING`, `LAYER_AUTHORITY_VIOLATION` |
| Setup/action | `SETUP_FIELD_MISMATCH` |
| Status | `STATUS_LAUNDERING`, `GENERATION_LAUNDERING` |
| Freshness | `STALE_PRESENTED_AS_LIVE`, `CLOCK_UNRESOLVED` |
| Leakage | `LEAKAGE_INTERNAL_MATERIAL`, `LEAKAGE_CORPUS`, `LEAKAGE_ENUMERATION`, `LEAKAGE_SYSTEM` |

A validation code is recorded and the answer refuses; it is never a warning that
accompanies a validated answer.

---

## 5. IV.6 HANDOFF — EVALUATION

### 5.1 IV.6 receives

- the frozen 86-test contract (`A-01`–`A-86`);
- the 46 Q5 golden scenarios;
- deterministic IV.3/IV.4 fixtures and a deterministic clock;
- expected validation and refusal codes per scenario;
- the refusal-precedence order;
- the `FinalResponseRecord` schema.

### 5.2 IV.6 must measure

- factual grounding of every claim;
- numeric equality and absence of laundering;
- citation validity, coverage and provenance safety;
- layer/status/generation correctness;
- actionability gating and no-advice compliance;
- freshness labeling;
- leakage and injection resistance;
- refusal precision: no false success and no unnecessary refusal where the
  package supports an answer;
- record completeness and determinism;
- Book V rendering equivalence against the same contracts.

### 5.3 Evaluation laws

- Q5-01–Q5-06 are valid-output controls.
- Q5-07–Q5-39 are adversarial truth/security controls.
- Q5-40–Q5-44 are refusal-vocabulary controls.
- Q5-45–Q5-46 are record/determinism controls.
- A deterministic pass proves contract wiring only.
- No production-quality claim without IV.6 ratification on the launch golden
  suite.

---

## 6. BOOK V HANDOFF — PRESENTATION

Book V receives and renders; it does not validate.

| Item | Contract |
|---|---|
| Answer payload | `ValidatedAnswer` with typed sections and citations |
| Refusal payload | `GovernedAnswerRefusal` with one frozen code and safe detail |
| Depth modes | `BEGINNER`, `OPERATOR`, `RESEARCHER` |
| Citations | user-facing provenance refs only; no internal IDs |
| Freshness | `as_of`/cutoff/stale marker where material |
| Unavailable states | explicit; never replaced by fallback prose |
| Record | safe metadata; prose not retained by default |

Book V must not add claims, compute statistics, reinterpret labels, invent
citations, hide no-go/limitations or turn a refusal into an answer. Any
frontend restructuring must preserve the four beginner semantics and the
operator/researcher field sets.

---

## 7. UPSTREAM DEPENDENCY HANDOFF

### 7.1 IV.4 -> IV.5

| Item | Contract |
|---|---|
| Draft | `GatewayDraft(status=UNVALIDATED)` |
| Identity | `package_id`, `manifest_id`, `query_plan_id` |
| Claims | text + `source_refs` + label/layer/generation |
| Numbers | `value_text` + `source_ref_id` + unit |
| Citations | package-local refs only |
| Usage | tokens/cost marker/latency |
| Refusals | `GatewayRefusal` is terminal; IV.5 does not repair it |

IV.5 must re-resolve everything. IV.4's structural admission is necessary, not
sufficient.

### 7.2 IV.3 -> IV.5

| Item | Contract |
|---|---|
| Package | immutable, ordered sections, `CONTEXT_CONTRACT_V1` |
| Manifest | digests, trust boundary hash, finalized `manifest_digest` |
| Evidence | `ContextItem.facts`, `evidence_refs`, `provenance_refs`, `quote_scope` |
| Statistics | `AuthorizedEvidenceStatistic` with N/small-N/OOS |
| Limitations | `mandatory` items and issue codes |

IV.5 re-verifies the manifest digest; it does not rebuild the package.

### 7.3 Setup/measurement -> IV.5

| Item | Contract |
|---|---|
| Eligibility | `ELIGIBLE` / `WATCH` / `BLOCKED` / `UNRESOLVED`, precedence fixed |
| Anchor | `UNRESOLVED`/`ELIGIBLE`/`ACTIVE`/`INVALIDATED`/`REKEYED` |
| Path remaining | `UNRESOLVED` state, never `0` |
| Quality | `DATA_QUALITY_BLOCKED` propagated |
| Model version | `MODEL_VERSION_UNAVAILABLE` mapped to the answer refusal |

IV.5 renders these; it does not recompute them.

---

## 8. DEPENDENCY OWNERSHIP MATRIX

| Dependency | Owner | IV.5 may | IV.5 may not |
|---|---|---|---|
| IV.4 draft | IV.4 | consume read-only, re-resolve | regenerate, repair truth, re-call model |
| IV.3 package/manifest | IV.3 | verify identity/digest, read | re-retrieve, mutate, widen |
| Epistemic labels | IV.3 | preserve | relabel, promote, drop |
| Setup eligibility | setup engine | reproduce verdict and reasons | recompute from prose, soften |
| Measurements | measurement owner | render values/unresolved states | substitute defaults or zero |
| Refusal vocabulary | IV.5 + PROD | use the six codes | invent a seventh code |
| Refusal precedence | PROD + IV.5 | implement the documented order | choose per case |
| Citation surface | PROD + IV.5 | render typed provenance | invent presentation or internal IDs |
| Entitlement | Book VI / IV.3 | propagate an encoded denial | infer, grant or bypass |
| Retention | SEC + OPS | store safe metadata | persist protected prose |
| Corpus reproduction | DATA + SEC | enforce `quote_scope` | expand beyond policy |
| Evaluation | IV.6 | expose tests/fixtures/record | declare production quality |

---

## 9. F3/F4 DEPENDENCIES

| Gate | Owner | Blocks | Closure |
|---|---|---|---|
| Citation presentation contract (R26) | PROD + AC | user-facing provenance rendering | approved field allowlist + rendering corpus |
| Cross-layer override authority (R39) | SETUP + OPS | any L1-over-higher-layer claim | encoded rule + version + case matrix |
| Current-state materiality/cutoff (R53) | PROD + MEAS | "current" answers | accepted policy ID |
| Missing-freshness materiality (R55) | PROD + MEAS | unavailable-vs-answer decision | accepted policy |
| Refusal precedence ratification (R63) | PROD + AC | stable refusal wording | ratified order + wording |
| Corpus reproduction policy (R58) | DATA + SEC | bulk excerpting | approved data-governance limits |
| Prose retention policy (R71) | SEC + OPS | storing answer prose | Book VIII retention decision |

No F3/F4 gate may be "closed" by prose, a fixture or a model assumption.

---

## 10. IMPLEMENTATION SEQUENCE FOR RUNG 2

1. Freeze enums/versions and `ASK_ANSWER_CONTRACT_V1`.
2. Package index/resolution over `allowed_refs` and item/evidence structures.
3. Typed `ResolvedClaim`, `ResolvedNumber`, `CitationRef`, depth field records.
4. Admission: status, identity, contract, manifest digest.
5. Numerical validator and normalization law.
6. Layer, setup/action, status, freshness validators.
7. Citation resolution/rendering and leakage veto.
8. Beginner, Operator and Researcher compilers over one validation core.
9. Six-code refusal and precedence.
10. `FinalResponseRecord` and deterministic `answer_id`.
11. 86 tests and 46 Q5 fixtures.
12. IV.6 harness and Book V contract handoff; CI and frozen-hash checks.

No step may modify Books I–III, IV.1–IV.4, routes or migrations.

---

## 11. VERIFICATION HANDOFF

Required before Rung 2 is declared complete:

- all 86 names collected and passing;
- all 46 Q5 scenarios deterministic and byte-reproducible;
- no network, provider, model or retrieval call;
- no credential present;
- upstream contract hashes, routes and migrations unchanged;
- IV.1/IV.2/IV.3/IV.4 suites unchanged and green;
- full repository regression green;
- both CI jobs green at the final head;
- F3/F4 status reported honestly;
- IV.6 and Book V acceptance criteria acknowledged.

---

## 12. STOP / ESCALATION RULES

Stop and escalate if:

- an upstream contract must change;
- a real provider call, credential or corpus expansion is required;
- a validator would need to fetch or regenerate evidence;
- a number cannot be tied to an authorized value;
- a layer/status/generation rule is not encoded in the package;
- an action needs an eligibility verdict the package does not carry;
- a refusal would have to be replaced by a fabricated answer;
- a citation surface would require exposing internal identifiers;
- test success would depend on a real model being available.

---

## 13. HANDOFF VERDICT

**IV.6:** ready to receive 86 tests, 46 Q5 scenarios and the
`FinalResponseRecord` schema; real-provider evaluation remains outside IV.5.

**Book V:** ready to render `ValidatedAnswer` and `GovernedAnswerRefusal`
without a second validator.

**Upstream:** no change requested from IV.1–IV.4 or the setup/measurement
contracts.

**Overall:** **RUNG 2 MAY PROCEED; PRODUCTION REMAINS BLOCKED.**
