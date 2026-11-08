# BOOK IV / BLOC IV.4 — EVIDENCE
## LLM GATEWAY & MODEL ROUTING — BA-29 RUNG 2

**Starting HEAD:** `5ace8dfcd57f12996d168120ca74ee20e20e3f52`
**Implementation HEAD:** `7b7c837`
**Acceptance HEAD:** `b75dc7e`
**Contract:** `ASK_GATEWAY_CONTRACT_V1`
**Verdict:** **PASS — deterministic fake-provider contract satisfied**

Final documentation and CI heads are recorded in `CI_RECEIPT.md`. This evidence
does not claim production provider readiness.

---

## 1. PHASE 0 VERIFICATION

| Check | Result |
|---|---|
| Starting local HEAD | PASS — `5ace8dfcd57f12996d168120ca74ee20e20e3f52` |
| Starting HEAD equals `origin/forge` | PASS — verified before modification |
| Four IV.4 planning documents | PASS — `PLAN.md`, `ACCEPTANCE.md`, `FEASIBILITY_GATE.md`, `DEPENDENCY_HANDOFF.md` |
| IV.1 interpreter | PASS — 60 collected/passed |
| IV.2 retrieval | PASS — 72 collected/passed |
| IV.3 context packager | PASS — 93 collected/passed |
| Book III integration | PASS — 96 collected/passed |
| III.1 provider compatibility | PASS — 49 collected/passed |
| WP-3B provider integration | PASS — 66 collected/passed |
| Frozen routes | PASS — SHA-256 `145757e0…d190af` |
| SQL migrations | PASS — `[1,2,3,4]` |
| Market-data provider | `NOT_CONFIGURED`; no market-data source changed |
| `.bu_tmp/` | Preserved; used only for local logs and the shallow-clone probe |
| Real LLM/network call | None |

Book I/II/III, IV.1, IV.2 and IV.3 source files were not modified. The change
surface is the new gateway package, the Q4 fixture directory, and the new test
file.

---

## 2. IMPLEMENTED MODULES

`app/forge/ask_cerebus/llm_gateway/`

| Module | Responsibility |
|---|---|
| `versions.py` | Contract, routing, prompt, schema and status constants |
| `enums.py` | Closed outcome, draft, task, attempt, cost and refusal vocabularies |
| `policy.py` | Declared task/depth/capability route selection and policy identity |
| `prompts.py` | BEGINNER/OPERATOR/RESEARCHER prompt contracts and trusted/untrusted envelope |
| `request.py` | IV.3 package/manifest admission, prompt assembly, request and attempt identity |
| `draft.py` | Structured draft/refusal models, schema and structural draft admission |
| `budget.py` | `CTX_UTF8_QUARTER_V1` units and gateway budgets |
| `trace.py` | Exposure-safe attempt, usage and gateway traces |
| `fake.py` | Deterministic Book II-port fake with ordered scripts |
| `retry.py` | Frozen provider-error normalization and retryability |
| `fallback.py` | Ordered alternate-candidate helpers |
| `service.py` | Bounded orchestration, retries, cancellation, fallback and accounting |
| `__init__.py` | Public IV.4 surface |

No new LLM interface, retrieval pipeline, context builder, route, migration or
provider adapter was added. OpenRouter remains absent from the domain package.

---

## 3. REQUIREMENT COVERAGE

| Group | Requirements | Covered |
|---|---|---:|
| T1 provider port | R1–R6 | 6/6 |
| T2 model routing | R7–R12 | 6/6 |
| T3 depth prompts | R13–R18 | 6/6 |
| T4 structured draft | R19–R24 | 6/6 |
| T5 retry/cancel | R25–R30 | 6/6 |
| T6 safe fallback | R31–R36 | 6/6 |
| T7 cost/latency | R37–R42 | 6/6 |
| T8 privacy | R43–R48 | 6/6 |
| T9 deterministic fake | R49–R54 | 6/6 |
| T10 replacement | R55–R60 | 6/6 |
| **Total** | **R1–R60** | **60/60** |

Feasibility remains **F1=18, F2=35, F3=3, F4=4**. F3/F4 were not converted into
positive production capabilities.

---

## 4. ACCEPTANCE TESTS

`tests/test_forge_ask_cerebus_gateway.py`

- Exact binding drivers: **72** (`A-01`–`A-72`).
- Unique names: **72**.
- Missing, renamed, duplicate, skipped, xfailed or placeholder tests: **0**.
- Drivers A-01–A-60 map one-to-one to R1–R60.
- A-61–A-72 are the frozen cross-cutting drivers.
- Result: **72 passed in 1.82s**.
- No network socket is opened; A-72 actively denies socket creation.
- A-70 proves invalid package type and manifest/package identity mismatch refuse
  before any provider call, with zero invocations.

---

## 5. GOLDEN FIXTURES

`implementation/forge/book_iv/bloc_iv_4/fixtures/`

- `_builders.py` — 24 scenarios built from real IV.3 `ContextPackager` output.
- `generate.py` — deterministic LF writer and SHA-256 manifest generator.
- `Q4-01.json`–`Q4-24.json` — immutable fixture payloads.
- `FIXTURE_MANIFEST.json` — 24 entries, 164,284 bytes total.
- `README.md` and `PROVENANCE.md` — reproduction and boundary.

A-55 rebuilds all 24 files in memory and verifies byte-identical output against
the manifest. Result: **24/24**, zero mismatches.

The fixture map now follows the binding `ACCEPTANCE.md` table:

- Valid: Q4-01–Q4-05.
- Numeric/citation refusal: Q4-06, Q4-08, Q4-09, Q4-10.
- IV.5 rejection preserved in an unvalidated draft: Q4-07, Q4-11–Q4-16.
- Security: Q4-17, Q4-18.
- Transport/fallback/budget: Q4-19–Q4-23.
- Conforming replacement: Q4-24.

Q4-06 and Q4-08 refuse before a numeric link can be admitted; Q4-07 remains
unvalidated because the number is structurally linked but semantically altered.
Q4-22 blocks an unsafe foreign-reference fallback. Q4-24 produces the same
domain draft through a second conforming fake.

---

## 6. BOOK II PORT COMPATIBILITY

- Uses the frozen `LLMRequest(prompt, model, response_schema)` port.
- Uses `LLMProvider.generate`, `LLMResponse`, `LLMUsage`, `ProviderHealth` and
  `CAPABILITY_STRUCTURED_OUTPUT`.
- Uses the frozen provider error taxonomy and `SimulatedClock`.
- A-01/A-02/A-04/A-06 verify port use, request shape, response metadata and no
  vendor client import.
- A-58 verifies capability mismatch refuses without invoking the provider.
- A-59/A-69 verify replacement through the same port without domain changes.

No provider SDK, vendor DTO, credential, live endpoint or OpenRouter adapter is
present.

---

## 7. IV.3 CONTEXT AND MANIFEST ADMISSION

`admit()` requires:

1. `CONTEXT_CONTRACT_V1`.
2. An `AuthorizedContextManifest` with `CONTEXT_MANIFEST_V1`.
3. Recomputable package identity and manifest digest reconciliation.
4. A non-`REFUSED` upstream outcome.
5. Declared sections matching the manifest.
6. Trusted query control, supported depth and a known route task.
7. Allowed exposure and absence of forbidden secret material.

A-70 proves a wrong type returns `PACKAGE_INCOMPLETE` and a tampered package ID
returns `PACKAGE_IDENTITY_MISMATCH`, both with **zero provider calls**. A-67
preserves package, manifest and query-plan identity. No corpus or IV.2 bundle is
readable from the gateway package.

---

## 8. ROUTING AND PROMPTS

- Routes are selected only from an explicit `RoutingPolicy`.
- Selection uses task, effective depth, structured capability and declared
  candidates.
- `production_authorized` is false in every fixture policy.
- No default provider, implicit upgrade or model-name truth exists.
- A-07–A-12 verify deterministic selection, bounded unsupported-route refusal,
  versioning, trace recording and declared-only alternates.
- A-13–A-18 verify three versioned prompt IDs, effective-depth selection, no
  hidden evidence, trusted/untrusted separation and bounded assembly.
- A-47 verifies retrieved instruction-like text remains after the untrusted-data
  boundary and never becomes trusted control.

The prompt includes package and manifest identity for audit but not raw package
bodies, credentials or internal methods.

---

## 9. DRAFT AND REFUSAL ADMISSION

A successful result is always `GatewayDraft(status=UNVALIDATED)`. No code path
emits a validated status, an answer authority field, an entitlement grant or an
execution instruction.

Structural admission enforces:

- Required fields and closed top-level/claim/number shapes.
- Package-local claim and citation references.
- A citation list covering every claim reference.
- Mandatory upstream limitation preservation.
- Forbidden authority fields.
- Evidence-typed, validated numeric links.

A-19–A-24 verify schema fields, number links, citation bounds, forbidden
authority, mandatory no-go/history preservation and malformed-output refusal.
No malformed output falls back to prose.

---

## 10. NUMERICAL AND CITATION BOUNDARIES

- Citations must resolve inside the admitted package.
- A claim with no citation returns `CITATION_REQUIRED`.
- A foreign claim/citation/number returns `CITATION_OUTSIDE_PACKAGE`.
- A material number resolves only to an `EVIDENCE` item whose status is
  `VALIDATED` or `FORWARD_OOS`; setup, model, query and unsupported claim items
  are not numeric evidence.
- A structurally admitted but semantically altered number remains
  `UNVALIDATED` for IV.5 (`Q4-07`).
- IV.4 does not perform fact checking, metric equivalence, layer validation or
  generation comparison. Those remain IV.5 authority.

Q4-06, Q4-08, Q4-09, Q4-10 verify refusal. Q4-05 verifies a valid 58% evidence
link. Q4-07, Q4-11–Q4-16 preserve IV.5 rejection cases.

---

## 11. TIMEOUT, RETRY AND CANCELLATION

- Per-attempt timeout and route total deadline are enforced.
- Retries occur only for retryable, idempotent transport failures.
- Maximum attempts and the shared deadline bound the loop.
- Retries reuse the identical package, manifest, prompt, schema and route.
- Cancellation is checked before each provider call and returns `CANCELLED` with
  no draft.
- A-25/A-26/A-27/A-28/A-42 and A-61/A-62/A-63 verify deadline, safe retry,
  attempt/cost caps, stable retry identity and cancellation.

---

## 12. SAFE FALLBACK

- A fallback exists only when a later candidate is explicitly declared.
- It reuses the same package, manifest, prompt, schema and model identity.
- It cannot add context, widen exposure, change depth/time scope or remove a
  limitation.
- Non-retryable failures and malformed drafts fail closed rather than falling
  back.
- A-31–A-35 verify declared alternate use, identity reuse, no broadening,
  prompt/schema preservation and ordered traces.
- A-36 and Q4-21 verify malformed output is not masked by fallback.
- Q4-19 is the successful declared fallback; Q4-20 fails both providers;
  Q4-22 refuses an unsafe foreign-reference fallback.

---

## 13. COST AND USAGE ACCOUNTING

- Tracks prompt, completion and total tokens, cost, latency, attempts, context
  units and prompt units.
- Aggregates retries and fallback without double counting.
- Preserves provider-reported cost basis; no authoritative-price claim exists.
- Enforces pre-call context/cost estimates and post-call generation/cost/latency
  limits.
- Refuses before provider invocation when the declared request cannot fit.
- A-37–A-42 and Q4-23 verify budgets and accounting.

`CTX_UTF8_QUARTER_V1` remains an estimator, not a provider tokenizer. Pricing
and account/cost allocation remain F3/F4.

---

## 14. PRIVACY AND EXPOSURE

- Provider requests contain only the prompt envelope and minimized package
  content.
- No internal code/method, denied ID, hidden object, credential, auth header,
  raw retrieval bundle, canonical dump or unrelated account data is serialized.
- Consumer traces contain route/attempt/usage identity, not raw prompts or
  package bodies.
- A-43–A-48 and A-68 verify minimization, secret exclusion, redaction and the
  trusted/untrusted boundary.

Provider retention/training approval remains **F4 open**. No real provider
request was made.

---

## 15. DETERMINISTIC FAKE

`GatewayFakeLLM` implements the Book II port and supports ordered scripts for:

- Valid structured drafts.
- Hallucinated/altered/unsupported numbers.
- Missing and foreign citations.
- Status, generation, research, layer, metric and evidence-class laundering.
- Prompt-injection obedience attempts.
- Malformed output, timeout, rate limit, unavailable and hard failure.
- Cancellation, budget refusal, safe fallback, unsafe fallback and replacement.

Fake usage, cost and latency are fixed. A-49–A-54 verify valid determinism,
adversarial scripts, injection, transport failures, fixed accounting and swap
semantics. A-55 runs all 24 Q4 scenarios. A-56/A-57 verify no vendor client or
OpenRouter domain dependency.

---

## 16. DETERMINISM AND TRACE IDENTITY

- Canonical JSON and sorted structures produce stable fixture bytes.
- Attempt IDs bind package, manifest, policy, route, prompt, provider, model and
  attempt number.
- A-10, A-49, A-53, A-54, A-55 and A-62 verify deterministic policy, output,
  usage and retry identity.
- A-69 verifies a conforming replacement changes provider identity, not the
  domain contract.
- No wall-clock, random, process, path or cache identity enters the draft.

---

## 17. F3/F4 GOVERNANCE — REMAIN OPEN

### F3

| ID | Requirement | Status |
|---|---|---|
| R7 | Authorized model-route catalog and budget policy | OPEN — local test policy only |
| R31 | Declared production alternate/fallback policy | OPEN — fixtures only |
| R42 | Account/feature cost allocation | OPEN — local aggregation only |

### F4

| ID | Requirement | Status |
|---|---|---|
| R18 | Provider-accurate tokenizer | OPEN — declarative estimator only |
| R41 | Authoritative provider pricing | OPEN — reported/unknown cost only |
| R48 | Provider retention/training terms | OPEN — no real request permitted |
| R55 | Real provider/model candidate matrix | OPEN — fake provider only |

A green fake run does not close any F3/F4 gate and does not approve production
OpenRouter use.

---

## 18. FROZEN INTEGRITY

Rechecked:

| Surface | Result |
|---|---|
| IV.3 `context/schema.py` | SHA-256 `499dbdfb…cfc2c0`; unchanged |
| Service routes | SHA-256 `145757e0…d190af`; unchanged |
| SQL migrations | `[1,2,3,4]`; unchanged |
| Book II port | Imported, not modified |
| Book I/III and IV.1–IV.3 | No source changes |
| Provider readiness | No configuration change |
| OpenRouter adapter | Absent |
| Credentials | Absent |

A-70/A-71 enforce the context hash, route hash and migration baseline.

---

## 19. FULL REGRESSION

Final local tree:

| Suite | Result |
|---|---|
| IV.4 gateway | **72 passed** |
| IV.3 context | **93 passed** |
| IV.2 retrieval | **72 passed** |
| IV.1 interpreter | **60 passed** |
| Book III integration | **96 passed** |
| III.1 provider compatibility | **49 passed** |
| WP-3B provider integration | **66 passed** |
| Book II providers | **74 passed** |
| Book I policy | **86 passed** |
| Book I retrieval | **124 passed** |
| **Full repository** | **2,375 passed, 29 skipped, 4 warnings in 42.88s** |

The 29 skips are the existing PostgreSQL/pgvector environment gates
(`FORGE_TEST_DATABASE_URL` absent). The full suite total is 2,404 collected;
2,375 + 29. The starting baseline total was 2,332 collected.

---

## 20. BASELINE PASS/SKIP DISCREPANCY

The prior IV.3 record reported local **2,303 passed, 29 skipped**. The BA-29
planning CI `test` job reported **2,302 passed, 30 skipped**. Both total 2,332,
so the difference is one pass-to-skip classification, not coverage loss.

A depth-1 clone reproduced the extra skip at:

`tests/test_forge_market_data.py:1767`
`test_planning_pins_unchanged`
Reason: `planning-pin commit objects unavailable (shallow clone)`

The shallow clone also has 13 unrelated history-dependent failures, so it is not
used as a clean pass-count baseline. Its only relevant classification signal is
the additional planning-pin skip. No frozen test was changed to restore a count.

Final local regression is exactly the prior 2,303 plus the 72 new IV.4 drivers:
**2,375 passed, 29 skipped**.

---

## 21. DEFECTS AND REPAIRS

| Finding | Repair |
|---|---|
| Initial Q4 IDs followed an earlier descriptive list, not the binding acceptance table | Rebuilt all 24 fixtures to the exact Q4 map: Q4-06/08 numeric, Q4-09/10 citation, Q4-11–16 laundering, Q4-19 fallback, Q4-20 both-fail, Q4-21 malformed, Q4-22 unsafe fallback, Q4-23 budget, Q4-24 conforming replacement |
| Numeric lookup matched a claim through its `evidence_refs` alias | Resolve material numbers only against evidence-typed items with validated/forward-OOS status |
| Prompt envelope omitted package identity | Added package/manifest identity to the trusted prompt envelope |
| Q4-24 replacement test compared provider-specific traces | Compare domain fields and status; provider identity is allowed to change |
| A-15 treated the prompt’s prohibition text as a forbidden assertion | Assert the explicit “never claim CANONICAL_VERIFIED” instruction instead |
| Q4-21 outcome was classified as `FAILED` in the draft table | Kept the frozen refusal vocabulary consistent: `REFUSED` with `PROVIDER_UNAVAILABLE` |

All repairs are covered by the 72 passing drivers. No assertion was weakened,
skipped or removed. No upstream contract was changed to force compatibility.

---

## 22. NON-CLAIMS

A passing IV.4 contract does **not** establish:

- production OpenRouter integration;
- a real provider/model candidate matrix;
- exact provider tokenization or context limits;
- authoritative pricing or account cost allocation;
- provider retention/training approval;
- semantic validation of model output;
- IV.5 fact, number, status, layer, metric or citation validation;
- entitlement or execution authority;
- Book IV completion.

## 23. CI EVIDENCE

| Job | Result | Duration | pytest summary |
|---|---|---|---|
| `test` | **SUCCESS** | 30s | **2,374 passed, 30 skipped** |
| `postgres` | **SUCCESS** | 1m9s | **2,403 passed, 1 skipped** |

Run: `42530782457` — https://github.com/dabiggestpoppa/cerebus-trader/actions/runs/42530782457
Head: `413b9f34716793844edf709b9571ba46b5e87560`

CI `test` has one additional skip versus local because its checkout is shallow:
`test_planning_pins_unchanged` cannot see the pinned planning commits. This is
the same single classification difference identified in section 20. The
PostgreSQL job executes the live database gates skipped locally.

**Evidence verdict:** deterministic `ASK_GATEWAY_CONTRACT_V1` satisfied for the
fake-provider boundary. F3/F4 remain open. IV.5 is the sole validation authority.
