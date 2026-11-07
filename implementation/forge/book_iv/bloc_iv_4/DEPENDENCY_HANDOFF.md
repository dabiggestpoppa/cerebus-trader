# BOOK IV / BLOC IV.4 — DEPENDENCY HANDOFF
## BA-29 RUNG 1

**Contract:** `ASK_GATEWAY_CONTRACT_V1` (proposed)
**Base HEAD:** `a15e0bf89a4192832ae94bf92f3f78f5069ca312`
**Upstream:** IV.1 query contract -> IV.2 retrieval -> IV.3 authorized context
**Downstream:** IV.5 Answer Compiler -> IV.6 Evaluation
**Provider layer:** Book II `LLMProvider`
**Status:** planning only; no implementation or credential exists.

---

## 1. FROZEN CHAIN

```
IV.1 ASK_QUERY_CONTRACT_V1
  -> IV.2 RETRIEVAL_CONTRACT_V1
  -> IV.3 AuthorizedContextPackage + AuthorizedContextManifest
  -> IV.4 ASK_GATEWAY_CONTRACT_V1
  -> IV.5 answer validation/compilation
  -> IV.6 evaluation
```

IV.4 may not bypass, re-run, widen or reinterpret any earlier stage.

The gateway receives the package **after** authorization and minimization. It
does not receive an IV.2 retrieval bundle, raw corpus, database handle, URL or
canonical body.

---

## 2. INPUT CONTRACT TO IV.4

### 2.1 Required input

- `AuthorizedContextPackage`
- matching `AuthorizedContextManifest`
- gateway policy/version
- optional budget and deterministic provider/clock

### 2.2 Admission checks

| Check | Failure |
|---|---|
| `context_contract_version == CONTEXT_CONTRACT_V1` | bounded `CONTEXT_VERSION_REFUSED` |
| manifest present and valid | `MANIFEST_REQUIRED` |
| package/manifest identity agrees | `PACKAGE_IDENTITY_MISMATCH` |
| package outcome not `REFUSED` | `UPSTREAM_REFUSED` |
| required sections present | `PACKAGE_INCOMPLETE` |
| effective depth in frozen enum | `DEPTH_UNSUPPORTED` |
| prompt/route/schema version supported | `ROUTE_UNSUPPORTED` |

Refusal happens before any provider call.

### 2.3 What must never be accepted directly

- raw retrieval objects or canonical store records;
- arbitrary document text outside the package;
- client-supplied status/layer/entitlement hints;
- API keys, cookies, auth headers or provider secrets;
- an arbitrary URL to “look up” more context;
- a different package on retry or fallback.

---

## 3. OUTPUT CONTRACT TO IV.5

### 3.1 `GatewayDraft`

Proposed fields:

| Field | Meaning |
|---|---|
| `gateway_contract_version` | `ASK_GATEWAY_CONTRACT_V1` |
| `route_policy_version` | `ASK_MODEL_ROUTING_V1` |
| `prompt_id`, `prompt_version` | depth/extractor/validator prompt used |
| `package_id`, `manifest_id`, `query_plan_id` | exact upstream identity |
| `draft_status` | always `UNVALIDATED` at IV.4 |
| `provider`, `model` | selected route; configuration, not truth |
| `attempts` | ordered transport attempts |
| `sections` | ordered structured answer sections |
| `claims` | claim/fact records with evidence links |
| `numbers` | numeric value + authorized evidence/value text |
| `citations` | package item/object/evidence refs only |
| `uncertainties` | explicit unknown/partial/conflict states |
| `refusals` | bounded no-evidence/no-current/no-setup/access outcomes |
| `proposed_prose` | optional rendering of the structured draft |
| `usage` | input/output/total units, cost marker, latency |
| `trace` | consumer-safe attempt/route accounting |

No field is authoritative. `UNVALIDATED` is mandatory.

### 3.2 `GatewayRefusal`

Fields:

- bounded refusal code;
- safe detail (no context/payload/credential);
- package/manifest/query identity where available;
- route/prompt version when known;
- attempt/cost summary;
- deterministic identity.

Refusal codes are stable and testable; no raw provider exception escapes.

### 3.3 `GatewayTrace`

May contain:

- package/manifest identity;
- route/prompt/provider/model versions;
- attempt order and retry count;
- token/cost/latency by attempt;
- outcome and refusal code.

Must not contain:

- full prompt or package body;
- provider request/response body;
- credentials, Authorization headers or signed URLs;
- hidden canonical IDs, SQL, stack traces or internal code.

---

## 4. IV.5 HANDOFF — ANSWER COMPILER

### 4.1 IV.5 owns

- semantic truth of every claim;
- numerical equality/rounding/unit checks;
- status, layer, generation, freshness and historical validation;
- setup/action eligibility and no-go enforcement;
- citation rendering and final user-facing answer;
- entitlement/access decisions supplied by Book VI when present;
- final refusal wording and answer-level consistency.

### 4.2 IV.4 provides

- structured, schema-valid, unvalidated draft;
- package-local evidence/citation links;
- numeric links and authorized value text;
- preserved labels/no-go/uncertainty markers;
- exact package/manifest identity for revalidation;
- route/usage trace.

### 4.3 Required IV.5 behavior

1. Reject any draft without `UNVALIDATED`.
2. Re-resolve every citation against the same package/manifest.
3. Reject unsupported/altered numbers, not merely uncited ones.
4. Reject status/layer/metric/time laundering.
5. Reject claims absent from authoritative evidence.
6. Preserve IV.3 no-go/limitations in the final answer.
7. Never treat provider prose, model confidence or route tier as evidence.
8. Treat gateway refusals as terminal unless IV.5 has a strictly narrower,
   authorized alternative; it may not re-call a model to “fix” a refusal by
   widening context.
9. Never expose the internal draft schema or hidden evidence IDs as authority.
10. Return a validated answer or a bounded refusal; never “probably correct”.

### 4.4 Handoff invariants

- Same `package_id` and `manifest_id`; no re-retrieval.
- Prompt/route/provider identity retained for audit.
- Gateway cannot mark validated.
- IV.5 cannot silently substitute a different draft or model.
- A failed IV.5 validation is not a reason to fallback within IV.4.

---

## 5. IV.6 HANDOFF — EVALUATION

### 5.1 IV.6 receives

- the frozen 72-test contract;
- the 24 Q4 golden scenarios;
- deterministic fake provider scripts;
- expected structural outcomes and IV.5 validation outcomes;
- provider-neutral replacement harness;
- route/prompt/schema versions;
- refusal-code catalog.

### 5.2 IV.6 must measure

- fact/number grounding;
- citation validity and coverage;
- status/layer/time correctness;
- no-go/limitation preservation;
- injection resistance;
- safe fallback and fail-closed behavior;
- malformed-output handling;
- budget/latency/cost behavior;
- provider replacement equivalence;
- refusal precision (no false success, no unnecessary refusal where evidence
  supports an answer).

### 5.3 Evaluation laws

- Q4-01–Q4-05 are valid-output controls.
- Q4-06–Q4-18 are adversarial truth/security controls.
- Q4-19–Q4-23 are transport/fallback/budget controls.
- Q4-24 is replacement, not a quality score.
- A fake passing all cases proves contract wiring only.
- No production-quality claim without real approved provider runs.

---

## 6. BOOK II PROVIDER HANDOFF

| Item | Contract |
|---|---|
| Port | `LLMProvider.generate`, `capabilities`, `health` |
| Request | `LLMRequest(prompt, model, response_schema)` |
| Timeout | Caller-supplied per attempt; total deadline gateway-owned |
| Retry | Adapter never retries; gateway owns bounded retries |
| Errors | Eight frozen classes; cancellation outside taxonomy |
| Fallback | `FallbackPolicy.for_port("llm")`, mode `alternate`, declared only |
| Circuit | Book II `CircuitBreaker`, injected clock |
| Usage | `LLMUsage`; per attempt; no provider billing claim |
| Redaction | Safe text only; no payloads/credentials/stack traces |
| Health | `healthy`/`degraded`/`unavailable`; not a truth signal |
| Selection | Composition root only |

### 6.1 OpenRouter adapter obligations (future, not created)

- implement `LLMProvider` exactly;
- map vendor errors into the frozen taxonomy;
- never retry internally;
- never inject retrieval or hidden context;
- never log credentials or raw payloads;
- respect caller timeout/cancellation;
- return usage/cost markers honestly;
- expose capabilities;
- remain replaceable without domain edits.

OpenRouter is an adapter, not a domain dependency, not a model authority, and
not a source of CEREBUS truth.

---

## 7. DEPENDENCY OWNERSHIP MATRIX

| Dependency | Owner | IV.4 may | IV.4 may not |
|---|---|---|---|
| IV.3 package/manifest | IV.3 | consume read-only, verify identity | re-retrieve, mutate, widen |
| IV.3 trust labels | IV.3 / IV.5 | preserve | relabel or promote |
| Book II LLM port | Book II | implement/consume | fork port or vendor types |
| Error taxonomy | Book II | map into | invent new provider classes |
| Fallback/circuit | Book II + OPS | invoke declared policy | auto-discover or fail open |
| Prompt policy | IV.4 + IV.5 | version and apply | encode truth in prompt |
| Truth validation | IV.5 | mark `UNVALIDATED` | validate or claim factual pass |
| Evaluation | IV.6 | expose scenarios/trace | declare production quality |
| Entitlement | Book VI / IV.3 | preserve denial | infer or grant access |
| Pricing | OPS + PROV | record reported/estimated | claim billing truth |
| Retention/training | SEC + PROV | enforce gate | assume terms |
| Credentials | User/Sites secrets | read via approved runtime only | print, commit, log or hardcode |

---

## 8. FAILURE AND REFUSAL CODES

Proposed stable codes, to be frozen in Rung 2:

| Code | Meaning |
|---|---|
| `CONTEXT_VERSION_REFUSED` | package contract mismatch |
| `MANIFEST_REQUIRED` | missing/invalid manifest |
| `PACKAGE_IDENTITY_MISMATCH` | package/manifest/plan disagreement |
| `UPSTREAM_REFUSED` | IV.3 refused package |
| `PACKAGE_INCOMPLETE` | required section absent |
| `DEPTH_UNSUPPORTED` | unknown/unsupported effective depth |
| `ROUTE_UNSUPPORTED` | no declared route for task/capability |
| `CAPABILITY_MISMATCH` | provider lacks structured output |
| `BUDGET_REFUSED` | input/output/cost/latency budget cannot be met |
| `PROVIDER_TIMEOUT` | per-attempt or total deadline exceeded |
| `PROVIDER_UNAVAILABLE` | unavailable/rate-limited after bounded policy |
| `PROVIDER_MALFORMED` | malformed structured output |
| `CANCELLED` | caller cancelled |
| `DRAFT_SCHEMA_INVALID` | draft cannot satisfy structural contract |
| `CITATION_OUTSIDE_PACKAGE` | unknown/foreign citation |
| `NUMERIC_EVIDENCE_MISSING` | material number lacks package link |
| `POLICY_DENIED` | no-go/authorization/entitlement refusal |
| `PROVIDER_NOT_CONFIGURED` | selected provider unavailable by config |

A refusal is a bounded outcome, never a success-shaped draft.

---

## 9. F3/F4 DEPENDENCIES

| Gate | Owner | Blocks | Closure |
|---|---|---|---|
| Route catalog/budget policy (R7) | OPS + GW | production routing | accepted policy ID + owner |
| Declared alternate policy (R31) | OPS + GW | production fallback | approved alternate list |
| Cost allocation (R42) | OPS | account/feature billing view | allocation design |
| Exact tokenizer (R18) | PROV | exact token accounting | per-model evidence |
| Authoritative pricing (R41) | OPS + PROV | billing accuracy | priced catalog/effective date |
| Retention/training (R48) | SEC + PROV | real provider use | signed terms/approval |
| Candidate matrix (R55) | PROV + EV | provider selection | approved real runs |

No F3/F4 gate may be “closed” by prose, fake data or a model-name assumption.

---

## 10. IMPLEMENTATION SEQUENCE FOR RUNG 2

1. Freeze enums/versions and `ASK_GATEWAY_CONTRACT_V1`.
2. Typed `RoutePlan`, `GatewayDraft`, `GatewayRefusal`, `GatewayTrace`.
3. Deterministic package admission and minimization.
4. Versioned THREE-depth prompts and trusted/untrusted envelope.
5. Structured draft schema + package-local citation/number links.
6. Budget, timeout, retry, cancellation and trace.
7. Declared fallback with same-package enforcement.
8. Fake scripts and 24 Q4 fixtures.
9. 72 tests, one-to-one or cross-cutting mapping.
10. Composition-root OpenRouter adapter seam (no real call).
11. IV.5 validation boundary and IV.6 harness handoff.
12. CI, frozen-hash checks and final report.

No step may modify Books I–III, IV.1–IV.3, routes or migrations.

---

## 11. VERIFICATION HANDOFF

Required before Rung 2 is declared complete:

- all 72 names collected and passing;
- all 24 Q4 scenarios deterministic;
- no network call;
- no credential present;
- contract hashes unchanged;
- routes/migrations unchanged;
- IV.1/IV.2/IV.3 suites unchanged;
- full repository regression green;
- both CI jobs green at final head;
- F3/F4 status reported honestly;
- IV.5 and IV.6 acceptance criteria acknowledged.

---

## 12. STOP / ESCALATION RULES

Stop and escalate if:

- an upstream contract must change;
- a real credential or external call is required;
- a provider cannot satisfy the frozen port;
- a model would need to retrieve or authorize;
- a draft requires validation inside IV.4 to “pass”;
- fallback would need broader context or entitlement;
- provider retention/pricing/tokenizer facts are unknown;
- test success would depend on a real provider being available.

---

## 13. HANDOFF VERDICT

**IV.5:** ready to consume `GatewayDraft(status=UNVALIDATED)` with package-local
citations, numeric links, labels and no-go markers.

**IV.6:** ready to receive 72 tests and 24 Q4 scenarios; real provider
evaluation remains blocked on F4.

**Book II:** no port change requested; OpenRouter remains an adapter.

**Overall:** **RUNG 2 MAY PROCEED; PRODUCTION REMAINS BLOCKED.**
