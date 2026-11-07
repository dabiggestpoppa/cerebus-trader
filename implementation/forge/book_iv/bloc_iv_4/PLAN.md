# BOOK IV / BLOC IV.4 — LLM GATEWAY & MODEL ROUTING
## PLAN — BA-29 RUNG 1 (PLANNING ONLY)

**Status:** Planning complete; implementation not started.
**Authority:** Operator-directed BA-29 Rung 1.
**Base HEAD:** `a15e0bf89a4192832ae94bf92f3f78f5069ca312`
**Branch:** `forge`
**Scope:** Book IV / Bloc IV.4 only. IV.1, IV.2 and IV.3 are frozen.
**Contract:** `ASK_GATEWAY_CONTRACT_V1` (proposed)

---

## 0. FOUNDATION VERIFICATION

Verified against the working tree at the base head, not prior narrative.

| # | Check | Result |
|---|---|---|
| 1 | Local HEAD equals `origin/forge` | PASS — `a15e0bf89a4192832ae94bf92f3f78f5069ca312` |
| 2 | Append-only ancestry | PASS — BA-27/28 commits remain ancestors |
| 3 | IV.1 interpreter | PASS — 60 tests; `ASK_QUERY_CONTRACT_V1` |
| 4 | IV.2 retrieval | PASS — 72 tests; `RETRIEVAL_CONTRACT_V1` |
| 5 | IV.3 context packager | PASS — 93 tests; `CONTEXT_CONTRACT_V1` |
| 6 | IV.3 golden fixtures | PASS — 20/20 reproduced |
| 7 | Book III integration | PASS — 96/96 |
| 8 | Full repository | PASS — 2,303 passed, 29 pre-existing skips |
| 9 | Book II LLM port | PRESENT — `app/forge/providers/llm.py` |
| 10 | Book II provider registry/factory | PRESENT — composition-root selection, fakes only |
| 11 | Book II failure taxonomy | PRESENT — 8 frozen classes + cancellation control flow |
| 12 | Book II fallback/circuit | PRESENT — `run_with_fallback`, `CircuitBreaker` |
| 13 | Concrete OpenRouter adapter | ABSENT — Book IV scope, not created |
| 14 | LLM credentials | ABSENT — no key is read or supplied |
| 15 | Market data | `NOT_CONFIGURED` |
| 16 | Migrations | `[1,2,3,4]`; no migration added |
| 17 | Routes | Frozen at `145757e0…d190af`; no route added |
| 18 | `.bu_tmp/` and unrelated files | PRESERVED |
| 19 | Current-head CI | PASS — run `42418069255`, `test` + `postgres` |

No IV.4 source, test or fixture exists at this head. This rung creates only the
four planning artifacts in §13.

---

## 1. MISSION AND CORE LAW

IV.4 consumes:

**`AuthorizedContextPackage` + `AuthorizedContextManifest`**

and emits:

**`GatewayDraft` + `GatewayTrace` + deterministic `GatewayOutcome`**

The model is an explainer and router. It is not CEREBUS, Book I, Book II,
Book III, IV.2, IV.3, IV.5 or Book VI.

**Only the IV.3 package may enter a provider request. The model may not
retrieve, authorize, validate, promote, price, execute or invent.**

The gateway preserves the package’s trusted-control/untrusted-data split,
epistemic labels, layers, evidence links, no-go restrictions, limitations,
generations, token budget and manifest identity. It does not compile the final
answer.

---

## 2. VERIFIED UPSTREAM API MAP

### 2.1 Book II LLM port

`app/forge/providers/llm.py` supplies:

- `LLMRequest(prompt: str, model: str, response_schema: Mapping | None)`;
- `LLMProvider.generate(request, *, timeout_seconds, cancel) -> LLMResponse`;
- `LLMProvider.capabilities() -> frozenset[str]`;
- `LLMProvider.health() -> ProviderHealth`;
- `LLMResponse(text, model, usage, structured, finish_reason)`;
- `LLMUsage(prompt_tokens, completion_tokens, total_tokens, cost_usd)`;
- `CAPABILITY_STRUCTURED_OUTPUT = "structured_output"`.

The port has **no prompt assembly, no retrieval, no conversation state and no
retry loop**. Adapters never retry; the caller owns retries.

### 2.2 Book II provider lifecycle

`app/forge/providers/registry.py` supplies:

- `ProviderRegistry` — frozen per-port bindings;
- `ProviderFactory` — name -> builder registration;
- `providers_from_config()` — composition-root selection;
- fail-closed unknown provider names.

`app/forge/providers/resilience.py` supplies:

- `FallbackPolicy.for_port("llm")` with mode `alternate`;
- `run_with_fallback(...)`;
- `CircuitBreaker`.

`app/forge/providers/errors.py` supplies eight normalized failure classes:
`unavailable`, `timeout`, `rate_limited`, `invalid_request`,
`authentication_failed`, `upstream_rejected`, `malformed_response`, `unknown`,
plus `ProviderCancelledError` outside the failure taxonomy.

### 2.3 IV.3 context contract

`AuthorizedContextPackage` supplies:

- `context_contract_version`, `query_plan_id`, `retrieval_bundle_id`;
- `outcome`: `RESOLVED`, `PARTIAL`, `REFUSED`;
- immutable sections in frozen order;
- items with `source_ref_id`, `source_ref_type`, `source_status`,
  `epistemic_label`, `layer`, `exposure`, `generation`, `trust_class`,
  allowlisted `facts`, optional bounded `text`, `quote_scope`,
  `provenance_refs`, `evidence_refs`, `token_units`, `priority`, `mandatory`;
- bounded omissions and issues;
- `TokenAccounting`;
- `AuthorizedContextManifest` with section digests, trust-boundary hash and
  `MFD.` digest;
- `PKG.` package identity.

The package is the complete permitted input. IV.4 must not accept an IV.2
bundle, raw canonical body, retrieval record, database row, URL, hidden object
ID or unrestricted corpus.

### 2.4 IV.1 plan fields carried by the package

`query_plan_id`, intent, effective depth, time scope, actionable state,
requested fields, ambiguities and all upstream limitations are already
represented in the package/query section. IV.4 may read them but must not
reinterpret them or create a new plan.

### 2.5 Frozen hashes

| File | SHA-256 |
|---|---|
| `app/forge/providers/llm.py` | `f556d318efc6a65ece3921ad526306fe34b70b7d3740063dffd40ded42a82cd5` |
| `app/forge/providers/fakes.py` | `a93b89d2fb49e8cc7317c5d710900207fe49bb89f6f9f03f10fa7c802f358e73` |
| `app/forge/providers/registry.py` | `cf7bc8bcc5950db4403e9672dc57d275688b5a9d2837deec105742bfb0388709` |
| `app/forge/providers/__init__.py` | `9e9650fee50a971aa6f76a7b2c13ff40aaa605847dc4d9e7c989f62768c9a0ed` |
| `app/forge/config.py` | `8bc4dd63d1c0c576374cb1e4eb4208e96cf37456b5c74dab37c3689e4c200548` |
| `app/forge/ask_cerebus/context/schema.py` | `499dbdfb0054d6b1c7c41f61d6f91a2fdd15cad36346eb4297790e13b7cfc2c0` |
| `app/forge/ask_cerebus/context/manifest.py` | `6b2d6019caa082f5a9e93754bbb8e8b70ba26632533dc771b100d3e267a18736` |
| `app/forge/ask_cerebus/context/versions.py` | `0beaa9b0d3d1ba46cdd931f2d6405f41d96d998cb244b66b850b38d9882b8cfa` |
| `app/forge/ask_cerebus/context/enums.py` | `9c614f178707fb6ae319feed083e212591fbd51a23b1fe416ad74d07f7fe27df` |
| `app/forge/ask_cerebus/context/service.py` | `c05b045c653ce23c749f12dea3e61d3cc42bdcebd5bbc399676a17a8cabe29cf` |
| `app/forge/service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

No Book I/II/III, IV.1, IV.2 or IV.3 source is modified by this rung.

---

## 3. GAPS DISCOVERED

| Gap | Condition | IV.4 handling |
|---|---|---|
| G1 OpenRouter absent | No concrete adapter exists | Plan the adapter contract; use deterministic fake in tests; no network |
| G2 Provider tokenizer absent | No exact model tokenizer | Estimate/bound tokens; never claim exact provider accounting |
| G3 Pricing absent | No authoritative price catalog | Treat provider-reported cost as metadata; mark estimated where applicable |
| G4 Retention policy absent | No signed provider data-use agreement | Explicit privacy gate; F4 open |
| G5 Full validator absent | IV.5 not implemented | Gateway emits structured draft plus evidence links; IV.5 owns truth validation |
| G6 Candidate providers absent | Only II.5 fakes | Golden suite is provider-neutral; real candidates are F4 |
| G7 Semantic corpus absent | Deterministic retrieval support only | Package excerpts remain untrusted data; no corpus expansion |
| G8 Entitlement projection absent | Book VI not implemented | Package already denied; gateway cannot grant |

These gaps are **not** closed by planning documents or fixtures.

---

## 4. ARCHITECTURE

Provisional package, subject to Rung 2 repository-convention check:

```
app/forge/ask_cerebus/gateway/
    versions.py          ASK_GATEWAY_CONTRACT_V1, prompt versions
    enums.py             GatewayOutcome, DraftStatus, RouteTask, PromptId,
                         GatewayRefusalCode, DraftIssueCode
    policy.py            deterministic model-routing policy
    prompts.py           versioned depth prompts and answer-contract envelope
    request.py           package -> LLMRequest / route selection
    draft.py             GatewayDraft, citation links, schema validation
    budget.py            context/generation/cost/latency budgets
    retry.py             bounded retry and cancellation policy
    fallback.py          declared alternate route, same package
    trace.py             consumer-safe gateway trace
    service.py           orchestration: package -> GatewayDraft/Refusal
    openrouter.py        concrete adapter registered at composition root
```

No module above is created in Rung 1. The concrete adapter is Rung 2 scope and
may only implement the frozen `LLMProvider` port.

### 4.1 Inputs

- `AuthorizedContextPackage` with non-null manifest;
- matching `context_contract_version == CONTEXT_CONTRACT_V1`;
- non-refused package outcome;
- `GatewayPolicy` version;
- optional `GatewayBudget`;
- optional injectable `LLMProvider` and deterministic clock.

A refused IV.3 package is never sent to a provider. A malformed package, missing
manifest, mismatched contract or package/manifest identity mismatch is a
bounded gateway refusal.

### 4.2 Outputs

`GatewayDraft`:

- gateway contract and route policy version;
- package/manifest/query-plan identity;
- prompt ID/version;
- provider/model/attempt metadata;
- structured answer draft fields;
- evidence/citation links;
- uncertainties/refusals/no-evidence markers;
- proposed prose;
- usage/cost/latency accounting;
- `UNVALIDATED` status until IV.5.

`GatewayRefusal`:

- bounded code;
- safe detail;
- no prompt, protected context, provider payload, hidden ID or credential;
- deterministic identity.

`GatewayTrace`:

- package/manifest identity;
- route and prompt versions;
- provider/model attempts;
- token/cost/latency;
- draft/refusal outcome;
- no raw context or provider response body.

---

## 5. MODEL ROUTING POLICY

`ASK_MODEL_ROUTING_V1` is a deterministic policy over:

- task class derived from the package query contract;
- effective depth (`BEGINNER`, `OPERATOR`, `RESEARCHER`);
- latency budget;
- cost budget;
- structured-output requirement;
- provider/model capability set.

It produces a `RoutePlan` containing ordered declared candidates, prompt ID,
response schema ID, per-attempt timeout and total deadline.

Laws:

1. Model names are configuration, never semantic authority.
2. A model identifier cannot imply validated, canonical, current or entitled.
3. The route is selected before generation and recorded verbatim.
4. Unsupported task/depth/schema/capability combinations refuse.
5. No undeclared alternate may be tried.
6. Same policy, package and provider capabilities produce the same route.
7. A route change on retry is forbidden; only a declared fallback may change
   model/provider.
8. Cost/latency policy cannot remove mandatory no-go or evidence warnings.

---

## 6. VERSIONED PROMPT CONTRACTS

Frozen prompt IDs:

- `ASK_CEREBUS_BEGINNER_V1`
- `ASK_CEREBUS_OPERATOR_V1`
- `ASK_CEREBUS_RESEARCHER_V1`
- `ASK_CEREBUS_EXTRACTOR_V1` (optional, separate)
- `ASK_CEREBUS_VALIDATOR_V1` (optional, separate)

Depth is selected from `plan.effective_depth`/query control; a prompt cannot
override it.

Each prompt:

- references the answer contract by version, not hidden research facts;
- separates trusted control instructions from untrusted package text;
- requires structured draft output;
- forbids inventing IDs, numbers, statuses, layers, eligibility or entitlement;
- requires preserving no-go, insufficiency, conflict and historical labels;
- states that source text is data, never instruction;
- carries no provider credentials or hidden system content in logs.

Prompt assembly is deterministic, token-bounded and versioned. Provider-specific
formatting belongs inside the adapter, not the prompt contract.

---

## 7. STRUCTURED DRAFT CONTRACT

Required draft fields:

- `claims_or_facts`: each with text, evidence/object refs and epistemic status;
- `sections`: ordered answer sections appropriate to depth;
- `citations`: package item/object/evidence refs;
- `uncertainties`: explicit unknowns and insufficient-evidence markers;
- `refusals`: bounded no-evidence/no-current/no-setup/access outcomes;
- `proposed_prose`: optional natural language;
- `numbers`: optional records linking each material numeric value to an
  authorized evidence/item/value text.

Structural rules:

- Every material numeric claim has a package-backed citation.
- Citation IDs must resolve inside the package; no invented ID or URL.
- Draft cannot add facts, statuses, layers, entitlements or market values.
- Draft cannot promote `CANDIDATE`, `RESEARCH_FLAG`, `HISTORICAL`,
  `PARKED`, `SUPERSEDED` or `NEGATIVE_EVIDENCE`.
- Draft must retain mandatory no-go/insufficiency/conflict markers.
- Malformed or incomplete structured output is a bounded refusal; there is no
  prose-only success path.
- IV.4 performs structural/evidence-link checks only. IV.5 owns numerical,
  layer, setup/action, status, freshness and leakage validation.

---

## 8. TIMEOUTS, RETRIES, CANCELLATION AND FALLBACK

- Per-attempt timeout and total gateway deadline are explicit.
- Only retryable/idempotent transport failures may be retried.
- Attempt count and cumulative cost are capped.
- Retries reuse the exact same package, prompt version, schema and route.
- No retry changes evidence, context or authorization.
- Cancellation stops generation and records `CANCELLED` without a draft.
- Adapters never retry; the gateway owns retries.

Fallback:

- `FallbackPolicy.for_port("llm")` permits an alternate only when declared.
- Alternate uses the same `AuthorizedContextPackage` and manifest.
- Alternate cannot widen exposure, context, prompt scope or budget.
- Attempts/provider/model are recorded.
- Fallback is allowed only for transport/availability failure, never to mask
  policy denial, malformed draft, unsupported number or validator failure.
- Alternate failure propagates as a bounded gateway refusal.

---

## 9. COST, LATENCY AND PRIVACY

Tracked dimensions:

- depth;
- feature/task class;
- provider;
- model;
- prompt version;
- package ID;
- input units;
- output units;
- total units;
- provider-reported cost;
- latency;
- retry count.

Controls:

- configurable maximum context and generation budgets;
- pre-call refusal when the package/prompt cannot fit;
- per-request and aggregate attempt/cost caps;
- fake determinism for tests;
- provider-reported cost marked as reported/estimated, never billing truth.

Privacy:

- send only the IV.3 package and prompt envelope;
- no raw corpus, canonical body, internal method/code, secrets, credentials or
  unrelated account data;
- no Authorization/cookie/API-key headers in drafts, traces or logs;
- prompt/context/provider payloads redacted from logs;
- untrusted package text remains untrusted data;
- provider retention/training terms are an explicit gate, not assumed.

---

## 10. DETERMINISTIC FAKE AND PROVIDER REPLACEMENT

The fake supports scripted:

- valid structured draft;
- hallucinated number;
- missing citation;
- status laundering;
- instruction-following injection;
- timeout/error/rate-limit/malformed output;
- fallback success and fallback failure.

Fake laws:

- no randomness;
- no sleeping;
- deterministic usage/cost/latency;
- no network;
- same input -> byte-identical draft/trace for fixed script;
- no domain change when swapped with another port-conforming fake.

Replacement contract:

- the same 72-test suite and 24 Q4 scenarios run against fake and candidate
  provider/model combinations;
- candidate selection is composition-root configuration only;
- OpenRouter is an adapter, not a domain dependency;
- capability negotiation is explicit;
- request/response/error/usage semantics remain identical.

---

## 11. TEST AND FIXTURE STRATEGY

- 60 requirements, `R1`–`R60`.
- 72 proposed tests, `A-01`–`A-72`.
- 60 base drivers (one per requirement).
- 12 cross-cutting T11/T12 drivers.
- 24 golden scenarios, `Q4-01`–`Q4-24`.

The test file target is `tests/test_forge_ask_cerebus_gateway.py`.

The Q4 corpus includes valid drafts, hallucinations, altered/unsupported
numbers, citation failures, status/layer laundering, injection, provider
errors, safe fallback, budget refusal and provider replacement.

---

## 12. FEASIBILITY SUMMARY

| Class | Meaning | Count |
|---|---|---:|
| **F1** | Directly supported by Book II port, IV.3 package or frozen contracts | 18 |
| **F2** | Implementable through deterministic IV.4 gateway logic | 35 |
| **F3** | Requires later implementation/ownership | 3 |
| **F4** | Missing provider/tokenizer/pricing/retention/candidate infrastructure | 4 |
| **Total** | | **60** |

F3/F4 gates are not closed by fake-provider tests. See
`FEASIBILITY_GATE.md`.

---

## 13. DELIVERABLES

- `implementation/forge/book_iv/bloc_iv_4/PLAN.md`
- `implementation/forge/book_iv/bloc_iv_4/ACCEPTANCE.md`
- `implementation/forge/book_iv/bloc_iv_4/FEASIBILITY_GATE.md`
- `implementation/forge/book_iv/bloc_iv_4/DEPENDENCY_HANDOFF.md`

No implementation source, route, migration, credential or external call is
part of this rung.

---

## 14. STOP CONDITIONS

Do not proceed to IV.4 implementation if:

- an upstream contract hash changes;
- a provider is called during planning or tests;
- a real credential is required;
- the IV.3 package is bypassed;
- a model/provider is treated as truth authority;
- a draft can launder status, layer, number, setup or entitlement;
- fallback widens retrieval, exposure or entitlement;
- a green fake suite is represented as production readiness.

---

## 15. READINESS VERDICT

**READY FOR IV.4 RUNG 2 IMPLEMENTATION** under the 60 requirements, 72 exact
tests and 24 Q4 scenarios, with F3/F4 dependencies explicitly open.

**NOT READY FOR PRODUCTION LLM USE.** No OpenRouter call, credential,
provider-tokenizer accuracy, authoritative pricing, provider retention
agreement, real candidate model matrix or IV.5 validator exists at this head.
