# BOOK IV / BLOC IV.6 — DEPENDENCY HANDOFF
## ASK CEREBUS EVALUATION & RED TEAM
### BA-31 RUNG 1 — PLANNING PACKET

**Starting HEAD:** `578b55278ae64a6ced24e3e08782b396f07d35b4`
**Consumes:** IV.1, IV.2, IV.3, IV.4, IV.5, Book I, Book II, Book III
**Produces:** evaluation contract, dataset, oracle, harness, scores, red-team
matrix, Book IV gate record
**Provides to:** Book V, Book VI, Book VII, Book VIII

---

## 1. UPSTREAM CONSUMER CONTRACT

IV.6 consumes these interfaces. Any change to them invalidates the declared
impacted case subset (`PLAN.md` §12).

| Upstream | Interface consumed | Stability required |
|---|---|---|
| IV.1 | `interpret(text, context=None) -> AskCerebusQueryPlan` | intent, entities, model ids, depth, ambiguities, `plan_id` |
| IV.1 | `AskCerebusQueryPlan` fields | all 19 fields as built |
| IV.2 | `AskCerebusRetrievalService(index, ...)` and `.retrieve(...)` | bundle contents, refusals, limitations, trace |
| IV.2 | `AuthorizedRetrievalBundle` | `canonical_refs`, `claim_refs`, `evidence_refs`, `negative_refs`, `limitations`, `refusals`, `trace`, `bundle_id` |
| IV.2 | `RetrievalTrace` | `selected_ids`, `claim_ids`, `evidence_ids`, `generations`, `rejection_counts`, `digest` |
| IV.2 | `RetrievalOutcome`, `RefusalCode`, `LimitationCode`, `RejectionClass` | vocabulary |
| IV.3 | `ContextPackager.pack(plan, bundle, *, detail=None, budget=None)` | package outcome, omissions, issues, manifest |
| IV.3 | `AuthorizedContextPackage` | `outcome`, `sections`, `omissions`, `issues`, `refusals`, `token_accounting`, `manifest`, `package_id` |
| IV.3 | `ContextItem` | `source_ref_id`, `source_ref_type`, `source_status`, `epistemic_label`, `layer`, `exposure`, `generation`, `trust_class`, `facts`, `quote_scope` |
| IV.4 | `GatewayService(*, providers, policy, clock=None)` and `.generate(package, ...)` | draft or governed refusal |
| IV.4 | `GatewayDraft` (`UNVALIDATED` only) | `sections`, `claims`, `citations`, `numbers`, `uncertainties`, `refusals`, `usage`, `trace` |
| IV.4 | `GatewayFakeLLM`, `FakeScript`, `script_digest` | deterministic scripted provider |
| IV.5 | `validate_answer(draft, package, *, policy=None)` | terminal outcome + record |
| IV.5 | `ValidatedAnswer`, `GovernedAnswerRefusal`, `FinalResponseRecord` | fields as built |
| IV.5 | 6 refusal codes, 33 validation codes, `VALIDATOR_ORDER` | vocabulary |
| Book I | `canonical.py` enums (`Layer`, `EvidenceStatus`, `ProductExposure`, `ObjectType`), `ClaimIdentity` | vocabulary |
| Book II | `DefaultDenyPolicyEngine.decide`, `AuthorizationContext`, `ResourcePolicyMetadata`, `PolicyReason` | authorization authority |
| Book III | `SetupEligibility`, `SEVERITY_ORDER`, `worst_verdict`, intelligence views, freshness | state and eligibility |

### 1.1 What IV.6 must not do to upstream

- Not modify IV.1–IV.5 source, fixtures, acceptance packets or ratifications.
- Not add a route, endpoint or migration.
- Not wrap production services in evaluation-only behavior.
- Not "fix" an upstream defect discovered by evaluation; evaluation reports,
  the owning bloc repairs.
- Not treat a deterministic fake as evidence about a real provider.

---

## 2. INTERNAL DEPENDENCY GRAPH

```
versions ── enums ── schema
                 ├── dataset ── oracle
                 ├── harness ── matching
                 ├── scoring ── findings
                 ├── redteam
                 ├── review
                 └── report ── regression
```

Rules:

1. `oracle` may import only `schema`, `enums`, `versions` and fixture data.
2. `harness` is the only module allowed to import the five SUT stages.
3. `report` is the only module that writes a run artifact.
4. No module may import `app.forge.service.routes`.
5. Cyclic imports are a design defect, not a workaround target.

---

## 3. DOWNSTREAM HANDOFF — BOOK V (UI, DASHBOARD, INDICATORS)

### 3.1 Book V receives

| Artifact | Contents |
|---|---|
| `ValidatedAnswer` DTO | sections, claims, citations, numbers, limitations, `as_of`, `answer_id`, depth |
| `GovernedAnswerRefusal` DTO | refusal code, safe detail, findings, limitations, `answer_id` |
| Safe citations | rendered provenance refs only; no internal ids |
| Evidence/status labels | `CANONICAL`, `VALIDATED`, `FORWARD_OOS`, `CANDIDATE`, `RESEARCH_FLAG`, `HISTORICAL`, `NEGATIVE_EVIDENCE`, `PARKED`, `SUPERSEDED`, `INFERENCE`, `GENERAL_KNOWLEDGE`, `INSUFFICIENT_EVIDENCE` |
| Depth sections | beginner (4 sections), operator (state/eligibility/location/trigger/invalidation/target/no-go), researcher (13 metadata fields) |
| Current-state flags | `as_of`, cutoff, stale marker, `CURRENT_DATA_UNAVAILABLE` |
| Rendering requirements tested by IV.6 | EV-001–EV-046, EV-074–EV-084 |

### 3.2 Book V must not

- read a raw `GatewayDraft`;
- reinterpret Claim/Evidence records;
- recalculate any model value, level or statistic;
- clear, soften or hide a no-go;
- change eligibility, generation or epistemic status;
- reconstruct protected methods from citations;
- invent a missing market level, date or N;
- render a refusal as a hedged answer.

### 3.3 Rendering acceptance Book V inherits

| Requirement | Source |
|---|---|
| Refusal is rendered as a refusal, with its code and safe detail | EV-047–EV-055, EV-111–EV-114 |
| Status/layer/generation labels are visible, never collapsed | EV-048–EV-052, EV-067–EV-073 |
| Citations render as user-facing provenance | EV-024–EV-029 (IV.5), EV-101–EV-106 |
| Beginner non-implication section is always present | EV-021–EV-028 |
| No-go is visually non-dismissible | EV-030, EV-037, EV-066 |

---

## 4. DOWNSTREAM HANDOFF — BOOK VI (LICENSING & ACCOUNTS)

| Item | Detail |
|---|---|
| Consumed seam | `AuthorizationContext.capabilities` (exact-match atoms, no wildcard) |
| What Book VI must supply | entitlement resolution producing a capability set for an authenticated principal |
| What Book VI must never supply | price, plan name, provider id, or raw request authority inside the policy context |
| Evaluation cases waiting on Book VI | EV-094–EV-100 (entitlement matrix) |
| Gate | `EV-GATE-04` |
| Explicit non-claim | a passing Book II policy matrix is **not** commercial entitlement acceptance |

Book VI must re-run EV-094–EV-100 against real entitlement resolution and
publish the results beside the Book II matrix, not in place of it.

---

## 5. DOWNSTREAM HANDOFF — BOOK VII (PUBLISHING, RESEARCH, DATA)

| Item | Detail |
|---|---|
| Needed capability | durable historical snapshots, governed statistic registry with N/period/small-N, real semantic retrieval |
| Cases waiting | EV-040, EV-043, EV-046, EV-050, EV-080–EV-084, EV-101–EV-106 |
| Gates | `EV-GATE-07`, `EV-GATE-08`, `EV-GATE-09`, `EV-GATE-10` |
| Constraint | historical OOS must remain distinguishable from forward OOS after any index rebuild |

---

## 6. DOWNSTREAM HANDOFF — BOOK VIII (SECURITY, HARDENING, LAUNCH)

| Item | Detail |
|---|---|
| Needed capability | cross-session abuse detection, rate/aggregation controls, retention enforcement, launch hardening |
| Cases waiting | EV-103, EV-106, EV-100 (cross-principal), EV-085–EV-093 (production surface) |
| Gates | `EV-GATE-05`, `EV-GATE-06` |
| Constraint | the evaluator must be able to observe quote ceilings and overlap ratios after hardening; those are the same measurements, re-run |

Book VIII must not weaken the single-response protections to make cross-session
controls easier; the per-response ceiling remains the floor.

---

## 7. BLOCKED ITEMS AND THEIR OWNERS

| Item | Blocked on | Owner | What unblocks it |
|---|---|---|---|
| Real-provider answer evaluation | no provider authorized | Gateway owner + operator | `EV-GATE-01` |
| Live current-state evaluation | market data `NOT_CONFIGURED` | Data owner | `EV-GATE-07` |
| Commercial entitlement matrix | no Book VI resolver | Book VI | `EV-GATE-04` |
| Cross-session extraction measurement | no shared abuse store | Book VIII | `EV-GATE-06` |
| Citation-surface scoring | no public citation contract | Product/UX | `EV-GATE-02` |
| False-refusal threshold | no product decision | Product owner | `EV-GATE-03` |
| Materiality/cutoff scoring | declared policy only | Product owner | `EV-GATE-03` |
| Refusal-precedence scoring authority | documented, unratified | Governance | `EV-GATE-11` |
| Review agreement metric | no review performed | Operator reviewer | `EV-GATE-12` |
| Launch pass/fail | no ratified thresholds | Product owner | `EV-GATE-13` |
| Licensed statistics / small-N policy | no governed registry | Research owner | `EV-GATE-09` |
| Historical replay evaluation | no durable snapshots | Book VII | `EV-GATE-08` |

None of these is a defect in IV.6. Each is an external dependency with a named
owner and a stated closure artifact.

---

## 8. BOOK IV COMPLETION GATE (FULL FORM)

### 8.1 Three verdicts

| Gate | Question | Required evidence | Can pass now? |
|---|---|---|---|
| `BG-A` Deterministic subsystem completeness | do IV.1–IV.6 implementations, fixtures and regressions pass at one head? | CI jobs green; per-bloc test counts; dataset digest | after IV.6 Rung 2 |
| `BG-B` End-to-end evidence integrity | does the full chain preserve authorization, identity, truth, no-go and answer semantics across 120 cases? | zero S1 findings; false-refusal controls answered; injection fails closed | after IV.6 Rung 2 |
| `BG-C` Operational readiness | are provider policy, privacy, live data, entitlement, history, abuse controls and thresholds ratified? | `EV-GATE-01`, `04`, `05`, `06`, `07`, `08`, `09`, `10`, `13` closed | **no** |

`BG-B` may pass only while `BG-A` passes. `BG-C` is independent and cannot be
inferred from either.

### 8.2 Book IV evidence record (assembled at completion)

| Field | Source |
|---|---|
| Query-plan version | IV.1 |
| Retrieval contract version | IV.2 |
| Context contract version | IV.3 |
| Gateway/prompt versions | IV.4 |
| Answer contract + validator set versions | IV.5 |
| Evaluation dataset version + digest | IV.6 |
| End-to-end scores | IV.6 report |
| Red-team findings | IV.6 findings |
| Upstream gap inventory | this document §7 |
| Release blockers | S1 findings + open F3/F4 |
| Operator review | `HumanReviewRecord` set |
| Final ratification | operator sign-off |

### 8.3 Prohibited shortcuts

- `BG-A` green ⇒ "Book IV complete" — forbidden.
- `BG-B` green ⇒ "launch ready" — forbidden.
- `BG-C` attempted by fixtures — forbidden.
- Any verdict recorded without its evidence artifact — forbidden.

---

## 9. VERSION AND CHANGE CONTROL

| Change | Required action |
|---|---|
| Case added/removed/edited | new dataset digest; reviewed diff; `R16` |
| Expectation edited | explicit diff + rationale; never from a run (`R94`) |
| Metric definition edited | new `SCORING_V1.x`; old reports remain valid for their version |
| Upstream contract changed | impacted subset re-run (`PLAN.md` §12) + new manifest |
| New refusal code | IV.5 ratification first; then `EV-DEP-01` review |
| New canonical model id | Book I registry first; then corpus extension |

---

## 10. PLANNING-RUNG EXIT

This rung delivers four documents and nothing executable:

- `PLAN.md`
- `ACCEPTANCE.md`
- `FEASIBILITY_GATE.md`
- `DEPENDENCY_HANDOFF.md`

No IV.6 code, test source or fixture file is created. No IV.1–IV.5 file is
modified. No route, migration or provider configuration is touched.

**Handoff to IV.6 Rung 2:** implement `app/forge/ask_cerebus/evaluation/`,
`implementation/forge/book_iv/bloc_iv_6/fixtures/` (120 cases) and
`tests/test_forge_ask_cerebus_evaluation.py` (112 drivers), then produce
`EVIDENCE.md`, `RATIFICATION.md` and `CI_RECEIPT.md` under the same
append-only ladder used by IV.5.
