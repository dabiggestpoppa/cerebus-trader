# BOOK IV / BLOC IV.5 — ANSWER COMPILER, VALIDATOR & CITATIONS
## PLAN — BA-30 RUNG 1 (PLANNING ONLY)

**Status:** Planning complete; implementation not started.
**Authority:** Operator-directed BA-30 Rung 1.
**Base HEAD:** `b6018bb1c3923093981ffb4646a7798abf45b922`
**Branch:** `forge`
**Scope:** Book IV / Bloc IV.5 only. IV.1, IV.2, IV.3 and IV.4 are frozen.
**Contract:** `ASK_ANSWER_CONTRACT_V1` (proposed)

---

## 0. FOUNDATION VERIFICATION

Verified against the working tree at the base head, not prior narrative.

| # | Check | Result |
|---|---|---|
| 1 | Local HEAD equals `origin/forge` | PASS — `b6018bb1c3923093981ffb4646a7798abf45b922` |
| 2 | Append-only ancestry | PASS — BA-27/28/29 commits remain ancestors |
| 3 | IV.1 interpreter | PASS — 60 tests; `ASK_QUERY_CONTRACT_V1` |
| 4 | IV.2 retrieval | PASS — 72 tests; `RETRIEVAL_CONTRACT_V1` |
| 5 | IV.3 context packager | PASS — 93 tests; `CONTEXT_CONTRACT_V1` |
| 6 | IV.4 LLM gateway | PASS — 72 tests; `ASK_GATEWAY_CONTRACT_V1` |
| 7 | Book III integration | PASS — 96 tests |
| 8 | Five-suite run at this head | PASS — 393 passed (`interpreter`, `retrieval`, `context`, `gateway`, Book III integration) |
| 9 | IV.4 worktree clean | PASS — only untracked `.bu_tmp/` |
| 10 | `GatewayDraft` present | PRESENT — `app/forge/ask_cerebus/llm_gateway/draft.py` |
| 11 | `GatewayDraft.status` | `DraftStatus.UNVALIDATED` only |
| 12 | Context package/manifest present | PRESENT — `app/forge/ask_cerebus/context/schema.py` |
| 13 | Setup eligibility contract | PRESENT — `SetupEligibility` with `BLOCKED > UNRESOLVED > WATCH > ELIGIBLE` |
| 14 | Migrations | `[1,2,3,4]`; no migration added |
| 15 | Routes | Frozen at `145757e0…d190af`; no route added |
| 16 | Market data | `NOT_CONFIGURED` |
| 17 | Network/model call in IV.5 | None; none planned |
| 18 | `.bu_tmp/` and unrelated files | PRESERVED |

No IV.5 source, test or fixture exists at this head. This rung creates only the
four planning artifacts in §14.

---

## 1. MISSION AND CORE LAW

IV.5 consumes:

**`GatewayDraft(status=UNVALIDATED)` + the originating
`AuthorizedContextPackage` + `AuthorizedContextManifest`**

and emits exactly one of:

**`ValidatedAnswer` | `GovernedAnswerRefusal`**

plus a **`FinalResponseRecord`** for either outcome.

When the draft carries no answerable content and the package says the material
is unavailable, IV.5 emits a governed refusal. When the draft is structurally
admissible but one or more truth checks fail, IV.5 emits a governed refusal. It
never downgrades a failure into a "best effort" prose answer.

**The draft is untrusted. The package is the evidence. IV.5 is the last
authority before the user.**

Core law:

1. A draft cannot become an answer by being fluent, confident or long.
2. A number is accepted only if it equals an authorized value.
3. A label is preserved, never upgraded.
4. A layer cannot lend authority to another layer.
5. An action requires an encoded, eligible setup.
6. A current claim requires a freshness basis.
7. A citation must resolve to user-facing provenance.
8. No internal machinery is rendered.
9. Unavailable is said plainly, never replaced by invention.
10. Every answer and refusal produces a safe record.

IV.5 does not retrieve, re-plan, re-generate, call a model, promote evidence,
price, execute, grant entitlement or create canonical truth.

---

## 2. VERIFIED UPSTREAM API MAP

### 2.1 IV.4 output contract — `GatewayDraft`

`app/forge/ask_cerebus/llm_gateway/draft.py` supplies:

- `GatewayDraft` with `package_id`, `manifest_id`, `query_plan_id`,
  `route_policy_version`, `route_id`, `prompt_id`, `prompt_version`, `depth`,
  `provider`, `model`, `sections`, `claims`, `citations`, `numbers`,
  `uncertainties`, `refusals`, `proposed_prose`, `usage`, `attempts`, `trace`;
- `status: DraftStatus = DraftStatus.UNVALIDATED` — the only member of the enum;
- `DraftClaim(text, source_refs, epistemic_label, layer, generation)`;
- `NumericLink(value_text, source_ref_id, unit)`;
- `DraftSection(heading, bullets)`;
- `GatewayRefusal` (a transport/structural gateway refusal, not an answer);
- `DraftFailure` and `parse_draft(...)`.

`parse_draft` already enforces: required top-level fields, no unknown fields,
no forbidden authority fields, non-empty `source_refs`, claim refs inside
`admission.allowed_refs`, citations inside the package, numeric links that
resolve to admissible evidence, frozen epistemic vocabulary, `INFERENCE`
rejected, and mandatory upstream limitations preserved verbatim. **Those are
structural checks. None of them decides whether a claim is true.**

### 2.2 IV.3 evidence contract

`app/forge/ask_cerebus/context/schema.py` supplies:

- `AuthorizedContextPackage` with `context_contract_version`, `query_plan_id`,
  `retrieval_bundle_id`, `outcome`, immutable ordered `sections`, bounded
  `omissions`/`issues`/`refusals`, `token_accounting`, `manifest`, `package_id`;
- `ContextItem` with `item_id`, `source_ref_id`, `source_ref_type`,
  `source_status`, `epistemic_label`, `layer`, `exposure`, `generation`,
  `trust_class`, allowlisted `facts`, optional bounded `text`, `quote_scope`,
  `provenance_refs`, `evidence_refs`, `token_units`, `priority`, `mandatory`;
- `ContextFact(key, value_text, unit)`;
- `AuthorizedEvidenceStatistic` with `evidence_id`, `metric`, `event_identity`,
  `conditioning_population`, `sample_size`, `research_period`, `small_n_flag`,
  `small_n_threshold_ref`, `oos_status`;
- `AuthorizedIntelligenceFact` with `snapshot_id`, `field_path`, `value_text`,
  `unit`, `layer`, `quality`, `synthetic`;
- `AuthorizedContextManifest` with section digests, `trust_boundary_hash`,
  `manifest_digest`, `included_object_ids`, `omitted_section_ids`.

`app/forge/ask_cerebus/context/enums.py` supplies the closed vocabularies:
`ContextOutcome`, `ContextSectionId`, `EpistemicLabel`, `TrustClass`,
`SmallNFlag`, `ContextIssueCode`, `ContextRefusalCode`.

### 2.3 Truth-adjacent contracts IV.5 must honour, not re-implement

| Contract | Location | IV.5 use |
|---|---|---|
| `SetupEligibility` (`ELIGIBLE`, `WATCH`, `BLOCKED`, `UNRESOLVED`) and `worst_verdict` precedence `BLOCKED > UNRESOLVED > WATCH > ELIGIBLE` | `app/forge/setup_engine/contracts.py` | Reproduce the package verdict, never recompute from prose |
| `AnchorStatus` (`UNRESOLVED`, `ELIGIBLE`, `ACTIVE`, `INVALIDATED`, `REKEYED`) | `app/forge/measurements/anchors.py` | Render anchor state, including unresolved |
| `RemainingState.UNRESOLVED` and `HigherOrderState.UNRESOLVED` | `measurements/path_metrics.py`, `measurements/higher_order.py` | Render "unresolved", never `0` |
| `DataOutcome.DATA_QUALITY_BLOCKED` | `app/forge/market_data/quality.py` | Propagate as an insufficiency/no-go condition |
| `MODEL_VERSION_UNAVAILABLE` | `app/forge/measurements/errors.py` | Map to the answer refusal of the same name |
| Freshness codes `PROVIDER_NOT_CONFIGURED`, `DATA_QUALITY_BLOCKED`, `CLOCK_UNRESOLVED` | `app/forge/intelligence_api/freshness.py` | Freshness validator inputs |
| `DRAFT_FORBIDDEN_FIELDS` | `llm_gateway/enums.py` | Second-line defence even though IV.4 already rejects them |

IV.5 reads these; it does not fork, edit or extend them.

### 2.4 Frozen hashes at the base head

| File | SHA-256 |
|---|---|
| `app/forge/ask_cerebus/llm_gateway/draft.py` | `9aac55a78f78e917c24c3b78ab308af0422643e2bca718502f3672806040ba7c` |
| `app/forge/ask_cerebus/llm_gateway/enums.py` | `52fb6475631f7b6f3083f9e8e720b1a5f661cca0c7943701f173bf4d9e8b2892` |
| `app/forge/ask_cerebus/llm_gateway/versions.py` | `01dac8b2541788fc478e3c696ccbd13b1c7cba80d839733b2c7c3cd0f71cf61b` |
| `app/forge/ask_cerebus/llm_gateway/service.py` | `9bfc0111ed5a50b394037073634fa918065223cb019b315dff9617c229d2d86e` |
| `app/forge/ask_cerebus/llm_gateway/request.py` | `f60bb6589b611763befbab0e6f28ea84af0e445af9a2cae6606e51e2cdf60b6a` |
| `app/forge/ask_cerebus/context/schema.py` | `499dbdfb0054d6b1c7c41f61d6f91a2fdd15cad36346eb4297790e13b7cfc2c0` |
| `app/forge/ask_cerebus/context/manifest.py` | `6b2d6019caa082f5a9e93754bbb8e8b70ba26632533dc771b100d3e267a18736` |
| `app/forge/ask_cerebus/context/enums.py` | `9c614f178707fb6ae319feed083e212591fbd51a23b1fe416ad74d07f7fe27df` |
| `app/forge/ask_cerebus/context/versions.py` | `0beaa9b0d3d1ba46cdd931f2d6405f41d96d998cb244b66b850b38d9882b8cfa` |
| `app/forge/ask_cerebus/context/service.py` | `c05b045c653ce23c749f12dea3e61d3cc42bdcebd5bbc399676a17a8cabe29cf` |
| `app/forge/setup_engine/contracts.py` | to re-freeze in Rung 2 |
| `app/forge/service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

Hashes are re-measured in Rung 2 before any test run and must be unchanged.

---

## 3. GAPS DISCOVERED

| Gap | Condition | IV.5 handling |
|---|---|---|
| G1 No answer compiler exists | `ask_cerebus/answer/` absent | Plan the module set; create nothing in Rung 1 |
| G2 Citation UX undefined | No product surface for provenance rendering | Render a typed provenance reference; presentation is an F3 gate |
| G3 Numeric normalization unspecified | No canonical numeric-normalization utility | Define an explicit normalization law in Rung 2; exact provider tokenizer is not involved |
| G4 Retention policy absent | No approved fine-grained retention | Persist safe metadata only; full prose persistence is F4 |
| G5 Cross-layer override rule absent | No encoded L1-over-higher-layer rule authority | Refuse cross-layer authority claims; F3 owner decision |
| G6 Entitlement engine absent | Book VI not implemented | Only propagate a denial already encoded in the package; F4 |
| G7 Corpus quote scope | `quote_scope` exists but licensing policy does not | Enforce the per-item scope; bulk reproduction policy is F4 |
| G8 Malicious package text | Package is untrusted data by contract | Leakage/injection validator treats it as data; no tool access |

These gaps are **not** closed by planning documents, fixtures or a green
deterministic suite.

---

## 4. ARCHITECTURE

Provisional package, subject to Rung 2 repository-convention check:

```
app/forge/ask_cerebus/answer/
    versions.py        ASK_ANSWER_CONTRACT_V1, ANSWER_RECORD_V1,
                       ANSWER_SECTION_SCHEMA_V1, VALIDATOR_SET_V1
    enums.py           AnswerOutcome, AnswerDepth, AnswerRefusalCode,
                       ValidationCode, CitationKind, ValidationVerdict
    claims.py          ResolvedClaim, ResolvedNumber, CitationRef,
                       OperatorFields, BeginnerFields, ResearcherFields
    resolution.py      package index: ref -> item/fact/statistic/provenance
    citations.py       resolution, ordering, dedupe, renderer
    validators/
        numerical.py
        layers.py
        setup.py
        status.py
        freshness.py
        leakage.py
        ordering.py    fixed validator order + veto semantics
    compilers/
        beginner.py
        operator.py
        researcher.py
    uncertainty.py     six-code refusal precedence and safe wording
    record.py          FinalResponseRecord, deterministic answer_id
    service.py         draft+package -> ValidatedAnswer | GovernedAnswerRefusal
```

No module above is created in Rung 1.

### 4.1 Inputs

- one `GatewayDraft` with `status is DraftStatus.UNVALIDATED`;
- the same `AuthorizedContextPackage` and `AuthorizedContextManifest` the draft
  names, with `context_contract_version == CONTEXT_CONTRACT_V1`;
- optional deterministic clock and a declared `AnswerPolicy` version.

### 4.2 Admission (before any compilation)

| Check | Refusal |
|---|---|
| draft status is not `UNVALIDATED` | `DRAFT_NOT_UNVALIDATED` |
| `draft.package_id` / `manifest_id` / `query_plan_id` disagree with inputs | `ANSWER_IDENTITY_MISMATCH` |
| package contract not `CONTEXT_CONTRACT_V1` | `ANSWER_CONTEXT_REFUSED` |
| manifest missing, or `manifest_digest != manifest.compute_digest()` | `ANSWER_MANIFEST_INVALID` |
| package `outcome is REFUSED` | `ANSWER_CONTEXT_REFUSED` |
| package `manifest` is `None` | `ANSWER_MANIFEST_INVALID` |

Admission never calls a provider, never re-retrieves and never mutates the
package.

### 4.3 Outputs

`ValidatedAnswer`:

- `answer_contract_version`, `answer_schema_version`, `validator_set_version`;
- `answer_id`;
- depth-specific sections (`BEGINNER` / `OPERATOR` / `RESEARCHER`);
- resolved claim list with epistemic label, layer, generation and citations;
- rendered citations in deterministic order;
- uncertainty/no-go/limitation block;
- `as_of`/freshness block where material;
- validation result: all validators passed with their codes;
- `FinalResponseRecord`.

`GovernedAnswerRefusal`:

- one of the six frozen answer refusal codes;
- deterministic precedence-selected code when several apply;
- safe detail naming the failing check, never protected content;
- the same `FinalResponseRecord` shape.

---

## 5. COMPILER SEMANTICS

### 5.1 Beginner compiler (Ch IV.5.1)

Four required semantics, in order:

1. **WHAT IT MEANS** — plain-language meaning of the cited model/term.
2. **WHAT CEREBUS SEES** — the current canonical/structured state, or an
   explicit statement that no current state is encoded.
3. **WHAT IT DOES NOT MEAN** — at minimum every upstream limitation, no-go,
   unresolved marker and non-prediction caveat.
4. **NEXT RELEVANT STATE/LEVEL** — the next state or level the package encodes,
   or an explicit "not encoded".

Headings may be compressed when UX prefers, but the four semantics must remain
identifiable in output and stable in the record. Beginner prose may reference
operator fields only as cited context, never as a claim of executable setup.

### 5.2 Operator compiler (Ch IV.5.2)

Fields, when applicable and encoded:

`MODEL/LAYER`, `CURRENT STATE`, `ELIGIBILITY`, `ACTIVE RANGE/ANCHOR`, `CLOCK`,
`PATH/RANGE LEFT`, `LEVELS`, `TRIGGER`, `INVALIDATION`, `TARGETS`, `NO-GO`,
`EVIDENCE STATUS`.

Laws:

- every field is populated from a cited package fact or an explicit
  `UNRESOLVED`/`NOT_ENCODED` marker;
- `ELIGIBILITY` reproduces the package verdict and its precedence; it is not
  recomputed from the prose;
- `PATH/RANGE LEFT` never renders `0` for an unresolved measurement;
- `NO-GO` is rendered in meaning and cannot be dropped for brevity, cost or
  style;
- `EVIDENCE STATUS` names the governing epistemic label for each field group.

### 5.3 Researcher compiler (Ch IV.5.3)

Exposes: model/version, claim ID, event identity, conditioning population, N,
period, metric/result, OOS/reproduction status, implementation identity,
contradictions, source generation.

Laws:

- `N` is required for a statistic claim; `N_NOT_PROVIDED` and
  `SMALL_N_UNRESOLVED` are rendered, not hidden;
- `metric` is rendered verbatim in meaning; substitution is a numerical
  failure, not a wording choice;
- contradictions and negative evidence present in the package must appear;
- implementation identity is rendered from the package, not from the model's
  self-description.

---

## 6. CITATION AND PROVENANCE LAW

A citation is a resolvable path from an answer claim to an authorized
canonical object, evidence record or source reference. It is not decorative and
not a footnote added after the fact.

1. Every material CEREBUS claim carries at least one citation.
2. Every citation resolves inside the package's `allowed_refs`; an unresolvable
   citation refuses the whole answer (`CITATION_UNRESOLVED`).
3. Every numeric claim's citation resolves to the same source as its
   `NumericLink.source_ref_id` (`CITATION_NUMERIC_MISMATCH`).
4. Citations are ordered by a deterministic key (section order, then source
   order, then resolved ref) and de-duplicated without losing distinct
   evidence paths.
5. Rendered provenance uses only user-facing reference material derived from
   `source_ref_id`, `source_ref_type`, `provenance_refs`, `evidence_refs` and
   `source_status`. It never renders a database row, table name, SQL fragment,
   internal enum, endpoint or hidden object ID.
6. A missing evidence path is a refusal. A fabricated citation is a refusal and
   a defect, never a repaired answer.

---

## 7. VALIDATOR LAW

### 7.1 Fixed order

```
1 numerical
2 layer
3 setup/action
4 status (epistemic + generation)
5 freshness
6 leakage
7 citation resolution/rendering
8 assembly
```

Rationale: numbers and class conversions are the highest-risk laundering;
layer and setup decide whether action language is even legal; status decides
whether the sentence may read as current fact; freshness decides whether
"current" has a basis; leakage is the last veto before anything is shown;
citations are resolved against the same package index the earlier validators
used.

Ordering is fixed and non-configurable. Every validator receives the same
immutable `ValidationContext` and returns a `ValidationVerdict`
(`PASS`, `FAIL(code)`, `VETO(code)`).

### 7.2 Numerical validator (Ch IV.5.5)

Reject or refuse:

- an invented number → `NUMERIC_EVIDENCE_MISSING`;
- an altered or value-changing rounded number → `NUMERIC_MISMATCH`;
- a unit/scale change absent from the package → `NUMERIC_UNIT_MISMATCH`;
- correlation → probability → `METRIC_SUBSTITUTION`;
- target completion → win rate → `METRIC_SUBSTITUTION`;
- basket confirmation → win rate → `METRIC_SUBSTITUTION`;
- simulation → empirical result → `EVIDENCE_CLASS_LAUNDERING`;
- a statistic claim without required N/status → `STATISTIC_INCOMPLETE`;
- a numeric claim absent from the draft `numbers` set → `NUMERIC_EVIDENCE_MISSING`.

Equality is normalized exactly: same digits and same scale, or an explicitly
declared equivalently-rendered form present in the package (`1,234` vs `1234`).
There is no "close enough" and no implicit rounding tolerance.

### 7.3 Layer validator (Ch IV.5.6)

Reject:

- an L3 destination used as a direct L1 entry → `LAYER_LAUNDERING`;
- an L2 path statistic presented as setup win rate → `LAYER_LAUNDERING`;
- an L1 trigger overriding a higher-layer no-go without an encoded rule →
  `LAYER_AUTHORITY_VIOLATION`;
- a claim whose layer differs from its source item's layer;
- a layer label outside the frozen vocabulary;
- cross-layer inference presented as canonical.

Mixed-layer answers are allowed only when each claim carries its own layer.

### 7.4 Setup/action validator (Ch IV.5.7)

- Actionable language requires an `ELIGIBLE` encoded setup in the package.
- `WATCH` permits observation language only.
- `UNRESOLVED` and `BLOCKED` forbid action and surface their reason.
- Multiple verdicts reduce by `BLOCKED > UNRESOLVED > WATCH > ELIGIBLE`.
- When no setup is encoded, the fixed sentence is required:
  **"CEREBUS has model context, but no validated setup is currently encoded for
  this action."**
- No personalized financial advice, position sizing, order intent, entry price,
  price target, stop instruction or execution instruction.

### 7.5 Status validator (Ch IV.5.8)

- `HISTORICAL`, `CANDIDATE`, `RESEARCH_FLAG`, `PARKED`, `SUPERSEDED` and
  `NEGATIVE_EVIDENCE` cannot be phrased as current validated fact.
- The emitted label must equal the source label; an empty label cannot satisfy a
  labeled claim.
- Generation/timestamp of historical evidence is preserved.
- Status cannot be upgraded by prose confidence, model tier, citation count or
  length.

### 7.6 Freshness validator (Ch IV.5.9)

- Material current-state claims expose `as_of` / data cutoff.
- A stale or old-snapshot state must be labeled.
- An old snapshot cannot be presented as live.
- Missing freshness metadata → `CURRENT_DATA_UNAVAILABLE`, never an assumed date.
- `CLOCK_UNRESOLVED`, `PROVIDER_NOT_CONFIGURED` and `DATA_QUALITY_BLOCKED`
  propagate explicitly.

### 7.7 Leakage validator (Ch IV.5.10)

Detect and veto:

- internal code, enum names, table/column names, endpoints, stack traces;
- internal-method fields;
- bulk contiguous corpus reproduction beyond an item's `quote_scope`;
- hidden object enumeration, or counts of non-included objects;
- system/prompt/model-config/credential/entitlement-logic disclosure;
- injected instructions inside package text being rendered as trusted
  instruction.

### 7.8 Uncertainty and refusal (Ch IV.5.11)

Exactly six answer-level refusal codes:

| Code | Meaning |
|---|---|
| `INSUFFICIENT_EVIDENCE` | The package does not support the requested claim |
| `CURRENT_DATA_UNAVAILABLE` | Current state cannot be established or is stale |
| `MODEL_VERSION_UNAVAILABLE` | The requested model/version is not encoded |
| `SETUP_NOT_ENCODED` | No validated setup exists for an action request |
| `ACCESS_NOT_ENTITLED` | The package already encodes a denial for this scope |
| `AMBIGUOUS_SCOPE` | The request cannot be resolved to one scope |

Deterministic precedence when several apply:

```
ACCESS_NOT_ENTITLED
> AMBIGUOUS_SCOPE
> MODEL_VERSION_UNAVAILABLE
> CURRENT_DATA_UNAVAILABLE
> SETUP_NOT_ENCODED
> INSUFFICIENT_EVIDENCE
```

No fabrication, guess, invented range or hedge-as-answer is permitted to avoid
saying unavailable.

---

## 8. FINAL RESPONSE RECORD (Ch IV.5.12)

`FinalResponseRecord` fields:

| Field | Meaning |
|---|---|
| `record_version` | `ANSWER_RECORD_V1` |
| `answer_id` | deterministic identity (below) |
| `answer_contract_version` | `ASK_ANSWER_CONTRACT_V1` |
| `validator_set_version` | `VALIDATOR_SET_V1` |
| `outcome` | `VALIDATED` / `REFUSED` |
| `answer_refusal_code` | null or one of the six codes |
| `package_id`, `manifest_id`, `query_plan_id` | exact upstream identity |
| `route_policy_version`, `route_id`, `prompt_id`, `prompt_version` | draft identity |
| `provider`, `model` | recorded; not truth |
| `depth` | `BEGINNER` / `OPERATOR` / `RESEARCHER` |
| `cited_refs` | resolved canonical/evidence/provenance refs |
| `claim_statuses` | per-claim epistemic label, layer, generation |
| `validation_codes` | ordered validator results |
| `as_of` | freshness basis where material |
| `latency_ms`, `cost_usd`, `cost_basis` | from the draft usage |
| `prose_retained` | `false` by default |

`answer_id` is deterministic:

```
sha256(record_version + answer_contract_version + validator_set_version
       + package_id + manifest_id + query_plan_id
       + route_policy_version + prompt_id + prompt_version + depth
       + outcome + sorted(cited_refs) + sorted(validation_codes))
```

prefixed `ANS.` and truncated consistently.

Retention law: the record stores safe metadata, not full protected prose. Full
prose persistence requires an approved retention policy and is **F4**.

---

## 9. SECURITY, PRIVACY AND LEAKAGE BOUNDARY

- IV.5 sends nothing anywhere. No network, no provider, no retrieval.
- The package remains `TRUSTED_CONTROL` vs `UNTRUSTED_DATA`; package text is
  data and never instruction.
- The rendered answer excludes internal code, method fields, SQL, endpoints,
  hidden IDs, model configuration, credentials, headers and entitlement logic.
- Refusal details name the failing check, not the protected content.
- Logs and records exclude prompts, package bodies, provider payloads and
  secrets.
- Quote scope is enforced per item; bulk corpus reproduction is vetoed.
- No personalized financial advice, no sizing, no execution.

---

## 10. DETERMINISTIC FIXTURE AND FAKE STRATEGY

IV.5 tests consume:

- deterministic `GatewayDraft` fixtures produced by IV.4 fakes;
- deterministic `AuthorizedContextPackage`/manifest fixtures from IV.3;
- a deterministic clock;
- byte-identical golden expectations.

No real model, provider, network or credential is involved. The fake draft
families cover: valid drafts, invented/altered numbers, missing/foreign
citations, metric and evidence-class substitution, layer laundering, status and
generation laundering, stale current state, leakage, injection, actionable
requests without setups, blocked/watch/unresolved setups and identity
mismatches.

---

## 11. TEST AND FIXTURE STRATEGY

- 76 requirements, `R1`–`R76`.
- 86 proposed tests, `A-01`–`A-86`.
- 76 base drivers (one per requirement).
- 10 cross-cutting drivers.
- 46 golden scenarios, `Q5-01`–`Q5-46`.

The test file target is `tests/test_forge_ask_cerebus_answer.py`.

---

## 12. FEASIBILITY SUMMARY

| Class | Meaning | Count |
|---|---|---:|
| **F1** | Directly supported by frozen IV.3/IV.4/setup-engine contracts | 34 |
| **F2** | Implementable through deterministic IV.5 logic | 35 |
| **F3** | Requires a later product/operations/ownership decision | 5 |
| **F4** | Missing external infrastructure, policy or entitlement engine | 2 |
| **Total** | | **76** |

F3/F4 gates are not closed by deterministic fixtures. See
`FEASIBILITY_GATE.md`.

---

## 13. HANDOFF SUMMARY

**IV.6** receives: the 86-test contract, the 46 Q5 scenarios, deterministic
draft/package fixtures, expected validation codes, refusal precedence and the
`FinalResponseRecord` shape. IV.6 measures grounding, citation validity,
laundering resistance, actionability gating, leakage resistance and refusal
precision.

**Book V** receives: `ValidatedAnswer` and `GovernedAnswerRefusal` payloads,
citation/evidence references, the three depth modes, explicit
unavailable/no-evidence states and the freshness block. Book V renders those
contracts; it does not create a second validator or reinterpret CEREBUS
statistics.

---

## 14. DELIVERABLES

- `implementation/forge/book_iv/bloc_iv_5/PLAN.md`
- `implementation/forge/book_iv/bloc_iv_5/ACCEPTANCE.md`
- `implementation/forge/book_iv/bloc_iv_5/FEASIBILITY_GATE.md`
- `implementation/forge/book_iv/bloc_iv_5/DEPENDENCY_HANDOFF.md`

No implementation source, route, migration, credential or external call is
part of this rung.

---

## 15. STOP CONDITIONS

Do not proceed to IV.5 implementation if:

- an upstream contract hash changes;
- a provider, model or network call is introduced into IV.5;
- a real credential is required;
- the package or manifest is bypassed;
- a validator can be disabled or reordered to produce a validated answer;
- a number can pass without equality to authorized evidence;
- a status/layer/generation can be upgraded by prose;
- an action can be emitted without an eligible encoded setup;
- a refusal can be turned into a fabricated answer;
- a green deterministic suite is represented as production readiness.

---

## 16. READINESS VERDICT

**READY FOR IV.5 RUNG 2 IMPLEMENTATION** under the 76 requirements, 86 exact
tests and 46 Q5 scenarios, with F3/F4 dependencies explicitly open.

**NOT READY FOR PRODUCTION ANSWERING.** No IV.5 code exists at this head; the
citation presentation surface, freshness materiality policy, cross-layer rule
authority, refusal-precedence ratification, entitlement engine and retention
policy remain open or unimplemented.
