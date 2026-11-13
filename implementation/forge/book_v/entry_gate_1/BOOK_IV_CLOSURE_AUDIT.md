# BOOK_IV_CLOSURE_AUDIT.md

**BA-37 Rung 1 — Book IV Closure Audit & Book V Readiness Gate (planning only).**
**Repository:** `dabiggestpoppa/cerebus-trader` · **Branch:** `forge`
**Starting / final SHA:** `e20b6010d2648a589cbab8cde715fee431ef026f`
**Mode:** Audit and planning only. No Book V implementation. No production code modified.

This document records the closure audit of Book IV (blocs IV.1–IV.6, Security
Amendment 1, Historical Lineage Amendment 1, BA-33/BA-34/BA-36 infrastructure
and evaluation supplements). It establishes whether Book IV has a clean,
defensible handoff into Book V and identifies exactly what Book V may implement
next.

## 1. Foundation verification (Phase 0)

All checks performed against actual source and executable tests at the
starting SHA `e20b601` (== `origin/forge`, working tree clean, append-only
ancestry confirmed via `git merge-base`).

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Local HEAD equals `origin/forge` | PASS | `git rev-parse HEAD` == `git rev-parse origin/forge` == `e20b6010d2648a589cbab8cde715fee431ef026f` |
| 2 | Exact required starting SHA | PASS | `e20b6010d2648a589cbab8cde715fee431ef026f` |
| 3 | Append-only ancestry | PASS | `git merge-base HEAD origin/forge` == HEAD == origin/forge |
| 4 | Working-tree cleanliness | PASS | `git status --porcelain` empty |
| 5 | Full test baseline | PASS | `2,697 passed / 0 failed / 29 skipped` |
| 6 | Migrations remain 001–004 | PASS | `app/forge/persistence/sql/00{1..4}_*.sql`, no `/ask` route |
| 7 | Routes remain frozen | PASS | `app/forge/service/routes.py` unchanged, no `/ask` route |
| 8 | Book II provider contracts | PASS | `app/forge/providers/llm.py` (LLMProvider port), `CAPABILITY_STRUCTURED_OUTPUT`, `app/forge/providers/fakes` (SimulatedClock), no default production provider |
| 9 | 17 canonical hash guards | PASS | `test_x006`, `test_c88`, `test_only_authorized_frozen_files_changed`, `test_am1_r27` all pass |
| 10 | BA-36 updated hash identities | PASS | `retrieval/service.py` committed blob `cdbe615f…`, canonical SHA-256 `2d73737e…b3535` |
| 11 | IV.5 refusal vocabulary | PASS | 6 codes: ACCESS_NOT_ENTITLED, AMBIGUOUS_SCOPE, MODEL_VERSION_UNAVAILABLE, CURRENT_DATA_UNAVAILABLE, SETUP_NOT_ENCODED, INSUFFICIENT_EVIDENCE; precedence highest-first |
| 12 | IV.6 evaluation contracts | PASS | `ASK_EVALUATION_CONTRACT_V1`, dataset V1, schema V1, CASE_COUNT=120, DRIVER_COUNT=112 |
| 13 | Dataset manifests and digests | PASS | EV-001–EV-120 digest `74bc217b…cbd31a8`; EV-121–EV-144 digest `881e8403…f92339` (`ASK_EVALUATION_DATASET_AM1_V1`); EV-145–EV-154 digest `aa7caee0…3eed2`; EV-155–EV-178 digest `ee9cbf30…b22657` |
| 14 | Prior ratification supplements | PASS | BA-34 `RATIFICATION_SUPPLEMENT_V2.md`; BA-35 `RATIFICATION_SUPPLEMENT_V1.md`; BA-36 `RATIFICATION_SUPPLEMENT_V2.md` all present |
| 15 | GitHub Actions at starting SHA | PASS (user-reported) | Run `43423278131`: test SUCCESS, postgres SUCCESS |

**Resolved:** BA-35 PLAN.md §1 references "EV-121–EV-144: 24 amendment cases". All 24 files exist under `implementation/forge/book_iv/security_amendment_1/fixtures/` (EV-121.json…EV-144.json), contiguous EV-121–EV-144, with `DATASET_MANIFEST.json` recording digest `881e8403fdd9ec868530f4a0ab42f809ae458e3965233469d988784721492339`, dataset version `ASK_EVALUATION_DATASET_AM1_V1`, schema `ASK_EVALUATION_CASE_SCHEMA_AM1_V1`, baseline dataset digest `74bc217b…cbd31a8` (matching EV-001–EV-120), and requirements AM1-R01…AM1-R24. The ratified 120-case corpus (EV-001–EV-120) is complete, contiguous, and green. Full EV-001–EV-178 inventory reconciles: 120 + 24 + 10 + 24 = 178 cases. All 27 Security Amendment 1 drivers (AM1-R01…AM1-R27) pass.

## 2. Six-bloc contract inventory (Phase 1)

Read directly from source (not from summaries). Each bloc lists its implemented
public API, input/output types, contract version, refusal behavior, authorization
boundary, evidence/provenance requirements, frozen dependencies, test inventory,
fixture inventory, open findings, and operational dependencies.

### IV.1 — Intent interpretation (`app/forge/ask_cerebus/interpreter/`)

- **Public API:** `interpret(text: str, context: InterpreterContext \| None) -> AskCerebusQueryPlan`
- **Input:** query text string; optional `InterpreterContext` (principal scope, max authorized depth)
- **Output:** `AskCerebusQueryPlan` — intent, entities, model_ids, setup_ids, market, layer, time_scope, requested/effective depth, requires_* flags, actionable, confidence, ambiguities, `plan_id`
- **Contract version:** `ASK_QUERY_CONTRACT_V1` (`interpreter/versions.py`)
- **Refusal behavior:** None at interpretation. Unresolvable material is captured as `Ambiguity` entries (code, material, candidates, detail) and surfaced as `AmbiguityOutcome` on the plan; the plan always returns.
- **Authorization boundary:** `InterpreterContext.max_authorized_depth` clamps requested depth; depth capping recorded as `DEPTH_CAPPED` ambiguity. No provider, no market, no retrieval.
- **Evidence/provenance:** None (interpretation only). Entity resolution is exact, source-backed vocabulary only; unknown phrases stay unresolved.
- **Frozen dependencies:** `Intent` (12 values), `Depth` (3), `TimeScope` (5), `AmbiguityReason`, `EntityKind`, `PlanConfidence`
- **Test inventory:** `tests/test_forge_ask_cerebus_interpreter.py`
- **Fixture inventory:** `implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py` (`plan()`, `operator()`, `default_records()`)
- **Open findings:** None open (F-01–F-10 all closed via Security Amendment 1; F-09/09b/10 closed via BA-35 Rung 2)
- **Operational dependencies:** None external (deterministic, offline)

### IV.2 — Retrieval and authorization (`app/forge/ask_cerebus/retrieval/`)

- **Public API:** `AskCerebusRetrievalService.retrieve(plan, principal, context, *, snapshot_context, correlation_id, semantic_limit) -> AuthorizedRetrievalBundle`
- **Input:** `AskCerebusQueryPlan`, principal, authorization context, optional `SnapshotContext`
- **Output:** `AuthorizedRetrievalBundle` — canonical_refs, claim_refs, evidence_refs, intelligence_refs, lineage_refs, semantic_passages, negative_refs, limitations, refusals, trace, selected_generation, selected_index_hash, bundle_id
- **Contract version:** `RETRIEVAL_CONTRACT_V1` (`retrieval/versions.py`)
- **Refusal behavior:** Bundle outcome `RESOLVED`/`PARTIAL`/`UNAVAILABLE`/`REFUSED`; `RefusalCode` vocabulary (REQUIRED_FIELDS_UNRESOLVED, PROVIDER_NOT_CONFIGURED, HISTORICAL_UNAVAILABLE, etc.)
- **Authorization boundary:** `ForgePolicyEnforcementService`, `SetupRegistry`; snapshot provider is optional (`None` = not configured). Intelligence (Book III market/snapshot) routing opened only when `requires_live_intelligence` or `time_scope in {CURRENT, AS_OF}` (BA-35 Rung 2 repair: `HISTORICAL_RESEARCH` removed from trigger).
- **Evidence/provenance:** Canonical Claim/Evidence join via `ClaimEvidenceJoiner`; join status `VERIFIED`/`SUPPORTED`/`UNSUPPORTED`/`MISSING`/`CONFLICT`/`INCOMPARABLE`; lineage refs; negative refs for parked/superseded/falsified claims
- **Frozen dependencies:** `LimitationCode`, `RefusalCode`, `RetrievalOutcome`, `PrecedenceTier`, `EvidenceJoinStatus`
- **Test inventory:** `tests/test_forge_ask_cerebus_retrieval.py`
- **Fixture inventory:** `implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py`
- **Open findings:** F-09 closed (BA-35 Rung 2); hash-pin conflict resolved (BA-36)
- **Operational dependencies:** None external (fixture-backed index, no provider)

### IV.3 — Context packaging (`app/forge/ask_cerebus/context/`)

- **Public API:** `ContextPackager.pack(plan, bundle, *, detail, budget) -> AuthorizedContextPackage`
- **Input:** `AskCerebusQueryPlan`, `AuthorizedRetrievalBundle`, optional `AuthorizedContextDetail`, `ContextBudget`
- **Output:** `AuthorizedContextPackage` — sections (8 section IDs), omissions, issues, refusals, token_accounting, manifest, package_id
- **Contract version:** `CONTEXT_CONTRACT_V1` / `CONTEXT_MANIFEST_V1` (`context/versions.py`)
- **Refusal behavior:** `ContextOutcome` RESOLVED/PARTIAL/REFUSED; `ContextRefusalCode` (CONTEXT_CONTRACT_UNSUPPORTED, CONTEXT_INPUT_MALFORMED, CONTEXT_BUDGET_EXCEEDED, CONTEXT_EXPOSURE_VIOLATION, CONTEXT_INTEGRITY_FAILURE, CONTEXT_DETAIL_UNAUTHORIZED)
- **Authorization boundary:** `exposure_allowed()` on canonical refs; `TrustClass` (TRUSTED_CONTROL vs UNTRUSTED_DATA); budget-based trimming; semantic quote scoping
- **Evidence/provenance:** Section-based packing (QUERY_CONTRACT, CURRENT_INTELLIGENCE, CANONICAL_MODEL, SETUP, CLAIMS, EVIDENCE, LINEAGE_TERMS, LIMITATIONS_NEGATIVE, GENERAL_KNOWLEDGE); manifest binds query_plan_id + retrieval_bundle_id + section digests + trust_boundary_hash
- **Frozen dependencies:** `ContextSectionId` (8), `EpistemicLabel` (11), `TrustClass` (2), `ContextIssueCode`, `ContextRefusalCode`, `SECTION_ORDER`
- **Test inventory:** `tests/test_forge_ask_cerebus_context.py` (C-01…C-92)
- **Fixture inventory:** `implementation/forge/book_iv/bloc_iv_3/fixtures/` (20 cases Q3-01…Q3-20)
- **Open findings:** None open
- **Operational dependencies:** None external

### IV.4 — LLM gateway (`app/forge/ask_cerebus/llm_gateway/`)

- **Public API:** `GatewayService.generate(package, *, budget, cancel) -> GatewayDraft \| GatewayRefusal`
- **Input:** `AuthorizedContextPackage`; caller-supplied providers + `RoutingPolicy`
- **Output:** `GatewayDraft` (sections, claims, citations, numbers, uncertainties, refusals, proposed_prose) or `GatewayRefusal`
- **Contract version:** `ASK_GATEWAY_CONTRACT_V1` / `ASK_GATEWAY_DRAFT_SCHEMA_V1` (`llm_gateway/versions.py`)
- **Refusal behavior:** `GatewayOutcome` DRAFT/REFUSED/FAILED/CANCELLED; `GatewayRefusalCode` (UPSTREAM_REFUSED, ROUTE_UNSUPPORTED, PROVIDER_NOT_CONFIGURED, BUDGET_REFUSED, CITATION_REQUIRED, MANDATORY_RESTRICTION_MISSING, etc.)
- **Authorization boundary:** `admit()` validates package/manifest identity and returns `Admission` or `AdmissionFailure`; route selection via `RoutingPolicy.select_route(task, depth, capabilities)`; `DRAFT_FORBIDDEN_FIELDS` blocks authority fields; draft must preserve mandatory limitations
- **Evidence/provenance:** Claim citations must resolve inside `admission.allowed_refs`; numeric links must resolve to admissible evidence (`numeric_ref_is_admissible`)
- **Frozen dependencies:** `RouteTask` (8 values: DEFINITION, CURRENT_STATE, SETUP_CONTEXT, STATISTIC_EVIDENCE, COMPARISON, HISTORICAL, RESEARCH, GENERAL), `DraftStatus.UNVALIDATED`, `DRAFT_FORBIDDEN_FIELDS`
- **Test inventory:** `tests/test_forge_ask_cerebus_gateway.py`
- **Fixture inventory:** None standalone (reuses bloc_iv_2 builders)
- **Open findings:** F-09 closed (gateway not the defect; task mapping correct); EV-GATE-01/07/10 OPEN (external provider/semantic dependencies)
- **Operational dependencies:** Caller-supplied LLM providers (none configured by default); no default production provider

### IV.5 — Answer compilation and validation (`app/forge/ask_cerebus/answer/`)

- **Public API:** `validate_answer(draft, package, *, policy) -> ValidatedAnswer \| GovernedAnswerRefusal`; also `prepare_claims`
- **Input:** `GatewayDraft` (UNVALIDATED), `AuthorizedContextPackage`, optional `AnswerPolicy`
- **Output:** `ValidatedAnswer` (sections, claims, citations, numbers, limitations, as_of, record) or `GovernedAnswerRefusal` (code, detail, findings, record, limitations)
- **Contract version:** `ASK_ANSWER_CONTRACT_V1` (`answer/versions.py`)
- **Refusal behavior:** 6 `AnswerRefusalCode` with frozen precedence (ACCESS_NOT_ENTITLED > AMBIGUOUS_SCOPE > MODEL_VERSION_UNAVAILABLE > CURRENT_DATA_UNAVAILABLE > SETUP_NOT_ENCODED > INSUFFICIENT_EVIDENCE); ~30 `ValidationCode` findings decay via `FINDING_REFUSAL`; admission-blocking codes (DRAFT_NOT_UNVALIDATED, ANSWER_CONTEXT_REFUSED, etc.)
- **Authorization boundary:** `AnswerPolicy` (quote_char_limit=400, corpus_bulk_limit=2000, require_as_of_for_current=True); draft must be UNVALIDATED; package/manifest/digest/identity reconciliation; upstream REFUSED propagates
- **Evidence/provenance:** Citations resolved via `PackageIndex`; claim sources must resolve; numbers must match authorized values; generation/layer/status validation against sources
- **Frozen dependencies:** `SectionId` (17 sections across 3 depth orders), `LAYER_VOCABULARY`, `CURRENT_EPISTEMIC_LABELS`/`NON_CURRENT_EPISTEMIC_LABELS`, `SetupVerdict`, `SETUP_PRECEDENCE`, `FINDING_REFUSAL` decay table
- **Test inventory:** `tests/test_forge_ask_cerebus_answer.py` (+ amendment1 `test_forge_ask_cerebus_amendment1.py` AM1-R01…R27)
- **Fixture inventory:** `implementation/forge/book_iv/bloc_iv_5/fixtures/` (ratified IV.5 builders)
- **Open findings:** F-01…F-07 closed via Security Amendment 1; F-07a closed via BA-35 Rung 2 Option C
- **Operational dependencies:** None external

### IV.6 — Evaluation and red team (`app/forge/ask_cerebus/evaluation/`)

- **Public API:** `run_case(case) -> EvaluationExecution`; `run_dataset(dataset) -> tuple[EvaluationExecution]`; `run_case_twice`/`replay_equal` for replay
- **Input:** `EvaluationCase` (frozen); `EvaluationDataset`
- **Output:** `EvaluationExecution` (outcome, refusal_code, validation_codes, stage identities, artifacts); `EvaluationReport` (scores, verdicts BG-A/BG-B/C, findings)
- **Contract version:** `ASK_EVALUATION_CONTRACT_V1`; dataset `ASK_EVALUATION_DATASET_V1`; schema `ASK_EVALUATION_CASE_SCHEMA_V1`
- **Refusal behavior:** Execution outcome `VALIDATED_ANSWER`/`GOVERNED_REFUSAL`/`ERROR`; `ERROR` only from unexpected exceptions (BA-35 Rung 2 F-09b repair prevents `None`→`validate_answer` TypeError)
- **Authorization boundary:** Independent oracle imports only `evaluation.schema/enums/versions` + `app.forge.canonical` (never interpreter/retrieval/context/llm_gateway/answer); `SYSTEM_UNDER_TEST` import isolation
- **Evidence/provenance:** Every case declares `ExpectedEvidencePath` (fixture_path, builder, record, values); dataset digest is SHA-256 over canonical case array; upstream pins (git blob IDs) for 10 frozen files; migrations pinned to (1,2,3,4)
- **Frozen dependencies:** 18 `CaseFamily` bands, 6 `CaseKind`, 4 `Authority` (MODEL_OUTPUT/SYSTEM_UNDER_TEST forbidden), 20 `MetricId`, 6 refusal codes, 3 depths, `TimeScope`, `ExpectedFreshness`
- **Test inventory:** `tests/test_forge_ask_cerebus_evaluation.py` (R001–R102 + X001–X010 = 112 drivers); amendment `tests/test_forge_ask_cerebus_evaluation_amendment1.py`; coverage `tests/test_forge_ask_cerebus_evaluation_coverage.py`
- **Fixture inventory:** `implementation/forge/book_iv/bloc_iv_6/fixtures/` (EV-001…EV-120, DATASET_MANIFEST.json, PROVENANCE.md); `implementation/forge/book_iv/security_amendment_1/fixtures/` (EV-121…EV-144, DATASET_MANIFEST.json, AM1-R01…AM1-R24); `bloc_iv_6/fixtures_v2/` (EV-145…EV-154); `bloc_iv_6/fixtures_v3/` (EV-155…EV-178, BA-35 Rung 2)
- **Open findings:** EV-GATE-02/03/09/11/12/13 OPEN (external governance/evidence dependencies)
- **Operational dependencies:** None external (deterministic fakes only; no network/provider/market/clock)

## 3. End-to-end contract audit (Phase 2)

Traced the complete product chain `interpret → retrieve → pack → generate → validate_answer` against actual source. No source code was changed to make a path pass.

| Path | Preserves request identity? | Preserves manifest identity? | Preserves auth context? | Preserves evidence provenance? | Preserves generation? | Preserves epistemic status? | Preserves refusal reason? | Preserves limitations? | Safe final response? | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Valid answer | Yes (plan_id → query_plan_id → package_id) | Yes (manifest digest → manifest_id) | Yes (Admission depth/task/limitations) | Yes (claim→evidence refs, citation resolution) | Yes (bundle generations → answer.generation) | Yes (epistemic_label per claim) | N/A (no refusal) | Yes (answer_limitations → limitations) | Yes (ValidatedAnswer) | PASS |
| Governed refusal | Yes | Yes | Yes | N/A | Yes (record.generation) | Yes (record) | Yes (code + detail + findings) | Yes (answer_limitations) | Yes (GovernedAnswerRefusal) | PASS |
| Unsupported intent (`INDICATOR_NAVIGATION`) | Yes | Yes | Yes | N/A | N/A | N/A | Yes (ROUTE_UNSUPPORTED, governed, never ERROR) | N/A | Yes (bounded refusal) | PASS (F-10 negative control) |
| Historical lineage | Yes | Yes | Yes | Yes (lineage_refs) | Yes (declared generation) | Yes (HISTORICAL label) | N/A (no refusal post-repair) | Yes (HISTORICAL_GENERATION) | Yes (VALIDATED_ANSWER) | PASS (F-09 repaired; H1–H3 verified) |
| Current-state w/o market data | Yes | Yes | Yes | N/A (intelligence refused) | N/A | N/A | Yes (CURRENT_DATA_UNAVAILABLE / PROVIDER_NOT_CONFIGURED) | Yes | Yes (GOVERNED_REFUSAL) | PASS |
| Entitlement denial | Yes | Yes | Yes | N/A | N/A | N/A | Yes (ACCESS_NOT_ENTITLED) | Yes | Yes | PASS |
| Unsupported provider | Yes | Yes | Yes | N/A | N/A | N/A | Yes (PROVIDER_NOT_CONFIGURED) | Yes | Yes | PASS |
| Unsupported numerical assertion | Yes | Yes | Yes | Yes (numeric_ref_is_admissible) | N/A | N/A | Yes (INSUFFICIENT_EVIDENCE) | Yes | Yes | PASS |
| Unsupported citation | Yes | Yes | Yes | Yes (Citation required; unresolved→CITATION_UNRESOLVED) | N/A | N/A | Yes (INSUFFICIENT_EVIDENCE) | Yes | Yes | PASS |
| Prompt injection | Yes | Yes | Yes | Yes (TRUSTED_DATA typing; INFERENCE reserved; DRAFT_FORBIDDEN_FIELDS) | N/A | N/A | Yes (ACCESS_NOT_ENTITLED / LEAKAGE_*) | Yes | Yes | PASS |
| No-go contradiction | Yes | Yes | Yes | N/A | N/A | N/A | Yes (SETUP_NOT_ENCODED / NO_GO_CONTRADICTION) | Yes (NO_GO_ACTIVE preserved) | Yes | PASS |
| Actionable execution advice | Yes | Yes | Yes | N/A | N/A | N/A | Yes (SETUP_NOT_ENCODED / ADVICE_PROHIBITED) | Yes | Yes | PASS |
| Generation mismatch | Yes | Yes | Yes | Yes | Yes (generation validated vs source) | Yes | Yes (INSUFFICIENT_EVIDENCE) | Yes | Yes | PASS |
| Model comparison | Yes | Yes | Yes | Yes (both model refs cited) | Yes (separate generations) | Yes | N/A | Yes | Yes | PASS |
| Beginner / Operator / Researcher depths | Yes (depth clamped) | Yes | Yes (depth in admission) | Yes | Yes | Yes | N/A | Yes | Yes | PASS |

**First failing boundary:** None. All 15 paths verified green against actual source. The only historical boundary failure (F-09/H1–H3 `ERROR`) was repaired in BA-35 Rung 2 and re-verified; F-09b (`None`→`validate_answer` `TypeError`) repaired; F-10 (`INDICATOR_NAVIGATION`→`ERROR`) preserved as governed `ROUTE_UNSUPPORTED`.

## 4. Open findings (Phase 4)

Findings reconciled against actual source and executable tests. Each finding reports original defect, owner, repair commit, regression driver, current outcome, residual limitation, closure evidence.

| ID | Original defect | Owner | Repair commit | Regression driver | Current outcome | Residual limitation | Closure evidence |
|---|---|---|---|---|---|---|---|
| F-01 | Execution guidance admitted | IV.5 validator | Security Amendment 1 | AM1-R18/19/20 | CLOSED | None | test_forge_ask_cerebus_amendment1.py green |
| F-02 | Untrusted text rendered as validated | IV.5 validator | Security Amendment 1 | AM1-R01…R13 | CLOSED | None | test_forge_ask_cerebus_amendment1.py green |
| F-03 | No-go contradiction | IV.5 validator | Security Amendment 1 | AM1-R14…R17 | CLOSED | None | test_forge_ask_cerebus_amendment1.py green |
| F-04 | Prose unvalidated | IV.4 draft / IV.5 | Security Amendment 1 | AM1-R21/22 | CLOSED | None | test_forge_ask_cerebus_amendment1.py green |
| F-05 | Numeric metric mislabel | IV.5 validator | Security Amendment 1 | AM1-R25 | CLOSED | None | test_forge_ask_cerebus_amendment1.py green |
| F-06 | Chain positives shape-only | IV.6 harness | Security Amendment 1 | AM1-R26 | CLOSED | None | test_forge_ask_cerebus_evaluation_amendment1.py green |
| F-07 | Refusals never assert limitations | IV.5 | Security Amendment 1 | AM1-R17/R21 | CLOSED | None | test_forge_ask_cerebus_amendment1.py green |
| F-08 | Hash guards encoding-dependent | BA-33 / test harness | BA-36 HASH_PIN_AMENDMENT_V1 | AM1-R27 + test_x006/test_c88 | CLOSED | BA-36 re-baselined `retrieval/service.py` pin (separately governed amendment) | 4 hash-guard tests pass; mutation test verified |
| F-09 | Historical research blocked by snapshot | IV.2 retrieval | BA-35 Rung 2 | R01–R28 + EV-155–178 | CLOSED | None | H1–H3 → VALIDATED_ANSWER; 28/28 drivers pass |
| F-09b | `None` → `validate_answer` TypeError | IV.6 harness | BA-35 Rung 2 | R18 (F-10) + EV-155–178 | CLOSED | None | AdmissionFailure carried; governed refusal preserved |
| F-10 | `INDICATOR_NAVIGATION` → ERROR | IV.6 harness | BA-35 Rung 2 | R18 (negative control) | CLOSED | No IV.4 task implemented (not authorized) | ROUTE_UNSUPPORTED governed, never ERROR |
| F-07a | `limitations` semantics ambiguous | IV.5 refusal surface | BA-35 Rung 2 Option C | A01–A15 (15 drivers) | CLOSED | None; `REFUSAL_CONSUMER_CONTRACT_V1.md` ratified | 15/15 F-07a drivers pass; zero payload change |

**Observation (resolved):** BA-35 PLAN.md §1 references "EV-121–EV-144: 24 amendment cases". All 24 files are present under `implementation/forge/book_iv/security_amendment_1/fixtures/` (EV-121.json…EV-144.json), with manifest digest `881e8403…f92339` and requirements AM1-R01…AM1-R24. The full EV-001–EV-178 inventory reconciles as 120 + 24 + 10 + 24 = 178 cases. This does not block any gate.

**No closed defect is reopened.** All findings have executable contradictory evidence only in the sense that they are verified fixed; none contradicted.

## 5. Evaluation coverage reconciliation (Phase 3)

| Corpus | Cases | Version | Digest | Modes | Positive | Refusal | Authorities | Status |
|---|---|---|---|---|---|---|---|---|
| EV-001–EV-120 | 120 | `ASK_EVALUATION_DATASET_V1` | `74bc217b…cbd31a8` | CHAIN + SEALED | 48 | 72 | FIXTURE_FACT/FROZEN_RULE/OPERATOR_ASSERTION/SYNTHETIC_INPUT | Green |
| EV-121–EV-144 | 24 | `ASK_EVALUATION_DATASET_AM1_V1` | `881e8403…f92339` | CHAIN + SEALED | — | — | — | Green (security_amendment_1/fixtures; AM1-R01…R24, 27 drivers pass) |
| EV-145–EV-154 | 10 | `ASK_EVALUATION_DATASET_V2` | `aa7caee0…3eed2` | CHAIN | 10 | 0 | — | Green (fixtures_v2) |
| EV-155–EV-178 | 24 | `ASK_EVALUATION_DATASET_V3` | `ee9cbf30…b22657` | CHAIN | 12 | 12 | SYNTHETIC_INPUT | Green (BA-35 Rung 2) |

- **Independent oracle:** import-independent (only `evaluation.schema/enums/versions` + `app.forge.canonical`); `SYSTEM_UNDER_TEST` = {interpreter, retrieval, context, llm_gateway, answer} excluded
- **CHAIN vs SEALED:** EV-001–EV-120 mixes both (CHAIN positives, SEALED for frozen packages); EV-145–154 and EV-155–178 are CHAIN
- **Numerical claim denominators:** `UNSUPPORTED_NUMERICAL_CLAIM_RATE`/`NUMERICAL_EXACT_MATCH_RATE` use asserted numbers only (test_r085/r086); denominator equality enforced
- **Citation resolution and support:** distinct populations (test_r087); `CITATION_RESOLUTION_ACCURACY` ≥ `CITATION_SUPPORT_ACCURACY`
- **False-refusal measurement:** `FALSE_REFUSAL_RATE` = 0.0; `VALID_ANSWER_COMPLETION_RATE` = 1.0 (test_r090)
- **Injection and extraction coverage:** 21 attacks; `INJECTION_ATTACK_SUCCESS_RATE` = 0.0; `PROTECTED_EXPOSURE_VIOLATION_RATE`/`ENTITLEMENT_BYPASS_RATE`/`CORPUS_EXTRACTION_LEAKAGE_RATE` numerators = 0 (test_r089)
- **Entitlement protections:** EV-094–EV-100 all `GOVERNED_REFUSAL`; `ACCESS_NOT_ENTITLED`/`AMBIGUOUS_SCOPE` enforced
- **Refusal limitation preservation:** `limitations` surface carries inherited restrictions; `code`/`detail` carry the refusal reason (F-07a Option C); empty `limitations` is legal
- **Historical-lineage coverage:** EV-155–EV-178 (3 models × 8 forms; definition/identity/lineage/comparison answer; evidence/statistic/current-state/actionable refuse)
- **Deterministic replay:** `run_case_twice`/`replay_equal` (test_r074/r096); report deterministic (test_r092)

**Classification distinction preserved:**
- DETERMINISTIC PASS: all 120 EV-001–120 + EV-145–154 + EV-155–178 + all drivers
- EV-121–EV-144 present and green (security_amendment_1/fixtures; 24 cases, AM1-R01…R24, 27 drivers pass) — included in DETERMINISTIC PASS
- EXTERNAL DEPENDENCY: EV-GATE-01/07/10 (provider, market data, semantic retrieval)
- PRODUCTION BLOCKER: BG-C BLOCKED; no gate closed by fixture-only success

## 6. Operational gate register (Phase 5)

### BG gates

| Gate | Verdict | Basis |
|---|---|---|
| BG-A deterministic completeness | PASS | Every case executes at one head with no stage exception; deterministic replay verified |
| BG-B end-to-end evidence integrity | PASS | Zero S1 findings; correct refusal rates (72/72, 0/48 false refusal); zero unsupported numbers in answers |
| BG-C operational readiness | BLOCKED | Provider, privacy, live data, entitlement, history, abuse controls, thresholds absent and unratified |

BG-A and BG-B are deterministic-fixture results; they do not imply BG-C. BG-C cannot pass in this rung and is not inferred from BG-A/BG-B.

### EV-GATE-01–13 (from `implementation/forge/book_iv/bloc_iv_6/FEASIBILITY_GATE.md`)

| Gate | Component | Class | Owner | Status | Book V depends? | Deterministic impl can proceed? | Production release depends? |
|---|---|---|---|---|---|---|---|
| EV-GATE-01 | IV.4 provider/tokenizer/pricing/privacy | F4 | Gateway owner + operator | OPEN | Yes | Yes | Yes |
| EV-GATE-02 | IV.5 citation presentation contract | F3 | Product/UX | OPEN | Yes | Yes | Yes |
| EV-GATE-03 | IV.5 current-data materiality/false-refusal threshold | F3 | Product owner | OPEN | Yes | Yes | Yes |
| EV-GATE-04 | Book VI commercial entitlement | F4 | Book VI | OPEN | Yes | Yes | Yes |
| EV-GATE-05 | IV.5 corpus licensing/retention | F4 | Legal/Ops + Book VIII | OPEN | No | Yes | Yes |
| EV-GATE-06 | Cross-session corpus-extraction protection | F4 | Book VIII | OPEN | Yes | Yes | Yes |
| EV-GATE-07 | Real current-market provider | F4 | Data owner | OPEN | Yes | Yes | Yes |
| EV-GATE-08 | Durable historical snapshots | F4 | Book VII | OPEN | Yes | Yes | Yes |
| EV-GATE-09 | Governed statistics/N/small-N policy | F4 | Research owner | OPEN | Yes | Yes | Yes |
| EV-GATE-10 | Real semantic retrieval | F4 | Book VII | OPEN | Yes | Yes | Yes |
| EV-GATE-11 | IV.5 refusal-precedence ratification | F3 | Product/Governance | OPEN | Yes | Yes | Yes |
| EV-GATE-12 | Human/operator review execution | F3 | Operator reviewer | OPEN | No | Yes | Yes |
| EV-GATE-13 | Launch threshold ratification | F3 | Product owner | OPEN | Yes | Yes | Yes |

All 13 gates OPEN. No gate is closed by a fake provider, synthetic snapshot, or fixture-only success. `EV-GATE-12` stays OPEN with an empty review set; `BG-C` stays BLOCKED (Security Amendment 1 acceptance condition #6).

## 7. Evidence limitations

- The hosted `postgres` CI job result was reported by the user (run `43423278131`, test+postgres SUCCESS) but could not be independently inspected from this environment (GitHub API/web return 404, private repo, no credentials). Local `test` suite is green (2,697/0/29).
- Book V does not yet exist; no consumer contract beyond `REFUSAL_CONSUMER_CONTRACT_V1.md` (Option C, zero payload change).
- No live market-data provider, no real semantic retrieval index, no durable snapshot store, no shared abuse store — all are EV-GATE OPEN / BG-C BLOCKED.

## 8. BG-A/BG-B/BG-C verdicts

| Gate | Verdict |
|---|---|
| BG-A | PASS |
| BG-B | PASS |
| BG-C | BLOCKED |

BG-A/BG-B must not imply BG-C. Release of ASK CEREBUS remains governed by EV-GATE-01–13.

## 9. Closure verdict

**Book IV deterministic implementation: COMPLETE and GREEN.** All six blocs (IV.1–IV.6), Security Amendment 1, Historical Lineage Amendment 1, and BA-33/BA-34/BA-36 supplements are internally consistent, fully tested (2,697 passed / 0 failed / 29 skipped), and all previously reported findings (F-01–F-10, F-07a, F-08 hash integrity) are closed with executable evidence.

**Book IV is ready for a Book V handoff** subject to the operational gate register above. Book V may consume the IV.5/IV.6 DTO surfaces described in `CONTRACT_HANDOFF.md` but must not cross any OPEN EV-GATE or assume BG-C.
