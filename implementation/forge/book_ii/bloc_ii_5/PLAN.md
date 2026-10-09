# BOOK II / BLOC II.5 — PROVIDER PORTS & ADAPTER BOUNDARIES — PLAN.md

Status: PLAN
Date: 2026-10-09
Start SHA: `218c521013a2c3513d4a4409aff69188965492ec` (== `origin/forge`, tree clean)
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24` (verified ancestor)

Dependency ratifications (all verified ancestors of the start SHA):

| Dependency | Ratification head |
|---|---|
| I.1 Canonical Registry Kernel | `aca9438` |
| I.2 Source & Provenance Fabric | `5ce3246` |
| I.3 Canonical Backfill | `26e8635` |
| I.4 Retrieval Compiler | `017fc96` |
| I.5 Corpus QA/Freeze | `686faa7` |
| II.1 Service Skeleton | `598b34c` |
| II.2 Persistence | `772a0d2` |
| II.3 Identity & Session | `cad9cd7` |
| II.4 Policy & Access Control | `ebda556` |

Frozen specification: Book II plan `# BLOC II.5` chapters **Ch II.5.1–II.5.10**
plus the five verbatim **Acceptance II.5** clauses
(`planning/forge/books/BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md`).
Scoped conflict record: `GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md`
(phase grouping vs. dependency law) — recorded, OPEN, non-blocking for II.5.

---

## 1. Objective (Ch II.5.1 — provider contract doctrine)

External vendors are replaceable implementation details. Domain/application
code imports FORGE provider ports, never OpenRouter/Whop-specific clients.

Every provider contract defines all eight elements (Ch II.5.1), machine-checked
via a `ProviderContractSpec` per port so the doctrine is executable, not prose:

1. request  2. response  3. timeout  4. retry ownership  5. idempotency
expectations  6. error taxonomy  7. health semantics  8. redaction rules

**Layering law** (tested by AST scan): `app/forge/providers/*` imports only
stdlib + `app.forge.config` (registry/factory); no FastAPI/Starlette/httpx/
requests/psycopg anywhere in the package. Domain modules (`canonical`,
`schemas`, `provenance`, `policy`, `retrieval`, `qa`, `persistence`,
`backfill`, `service/*` outside composition) never import
`app.forge.providers` — ports are consumed only at the composition root and by
future blocs' application services, never as domain PKs or hidden singletons.

## 2. Package architecture

```
app/forge/providers/
  __init__.py      public re-exports
  doctrine.py      ProviderContractSpec, PORT_CONTRACTS, ProviderHealth,
                   failure-class names (frozen 8), retry-ownership law
  errors.py        ProviderError hierarchy (one class per frozen failure
                   class + ProviderCancelledError control-flow signal)
  llm.py           LLMRequest/LLMResponse/LLMUsage/LLMProvider (Ch II.5.2)
  commerce.py      CommerceCustomer/Subscription/CheckoutSession/ProviderEvent/
                   CommerceProvider (Ch II.5.3)
  notification.py  NotificationRequest/Result/NotificationProvider (Ch II.5.4)
  storage.py       StoredObject/AccessStrategy/StorageProvider (Ch II.5.5)
  resilience.py    CircuitBreaker, FallbackPolicy, run_with_fallback (Ch II.5.8)
  fakes.py         deterministic fakes + SimulatedClock (Ch II.5.9)
  registry.py      ProviderRegistry + ProviderFactory + providers_from_config
                   (Ch II.5.6)
```

Seam edits outside the package: `app/forge/config.py` (provider selection +
credential presence + redaction), `app/forge/service/container.py`
(`providers` ownership), `app/forge/service/lifecycle.py` (docstring + health
log), `app/main.py` (composition root wires config-selected fakes).

## 3. Failure taxonomy (Ch II.5.7 — exact frozen set)

`FAILURE_CLASSES = ("unavailable", "timeout", "rate_limited", "invalid_request",
"authentication_failed", "upstream_rejected", "malformed_response", "unknown")`

A test asserts this tuple **exactly** (set and order). One exception class per
class: `ProviderUnavailableError`, `ProviderTimeoutError`,
`ProviderRateLimitedError`, `ProviderInvalidRequestError`,
`ProviderAuthenticationFailedError`, `ProviderUpstreamRejectedError`,
`ProviderMalformedResponseError`, `ProviderUnknownError`.

Retry ownership (Ch II.5.1 element 4): **adapters never retry**; the caller
owns retries. `ProviderError.retryable` is True only for `timeout`,
`unavailable`, `rate_limited`; `retry_after_seconds` set only for
`rate_limited`. Messages are doctrine-safe text only — never provider payloads,
credentials, URLs with tokens, or stack traces (`redacted_summary()`).

Cancellation (Ch II.5.2 "timeout/cancel"): `ProviderCancelledError` is
caller-initiated **control flow, not a provider failure** — it carries
`failure_class = None` and is asserted *outside* the frozen taxonomy.

## 4. Ports (Ch II.5.2–II.5.5)

**LLM (II.5.2)** — transport/provider abstraction only; prompts/retrieval
intelligence belong to Book IV. `generate(request, *, timeout_seconds, cancel)`
→ `LLMResponse(text, model, usage, structured, finish_reason)`; `LLMUsage`
carries token counts + deterministic `cost_usd`; `capabilities()` advertises
`structured_output` (optional capability, requested via
`LLMRequest.response_schema`); model identifier in request and echoed in
response; normalized errors only. OpenRouter adapter: **excluded** (Book IV).

**Commerce (II.5.3)** — provider-neutral operations Book VI needs:
`create_checkout(customer_id, idempotency_key)` (handoff), `get_customer`,
`get_subscription` (lookup/reconciliation reads), `parse_event(raw, signature)`
→ normalized `ProviderEvent(event_id, event_type, occurred_at, payload)`
(signature + shape validation live here), `health()`. Internal entitlement
mutation does NOT live in the adapter — enforced by an exact method-set test.
Whop adapter: **excluded** (Book VI).

**Notification (II.5.4)** — transactional only: `send(request)` →
`NotificationResult(message_id, status)` with normalized statuses
(`delivered|failed`); `health()`. No marketing automation — exact method-set
test. "Only if needed by launch": port + fake ship now because Book II freezes
the contract; no vendor.

**Storage (II.5.5)** — `put(key, data, content_type)` → `StoredObject(version,
size, checksum)` (version increments), `get(key, version=None)`, `delete(key)`
(delete/version behavior), `access_strategy(key, ttl)` →
`AccessStrategy(kind="signed_url"|"authorized_stream", target, expires_at)`
(signed/authorized access strategy). Library/GitHub recovery sources are NOT
blob storage (doctrine note; no such adapter here).

## 5. Registry / factory (Ch II.5.6)

`ProviderRegistry`: `register(port, name, impl)` with runtime type check
(`TypeError` naming the port), `get(port)`, `implementations()`, `freeze()`
(frozen ⇒ mutation raises). `ProviderFactory`: name → builder table;
`providers_from_config(config)` selects each port's implementation **at the
composition root** from `config.provider_llm/commerce/notification/storage`.
Unknown name ⇒ `ProviderConfigurationError` (fail-closed). No
`if provider == "whop"` anywhere in domain code (AST/string scan test).
Extension point for later concrete adapters: register a builder — composition
change, never domain rewrite (proved by the replacement test).

## 6. Circuit / fallback (Ch II.5.8)

`CircuitBreaker(failure_threshold, recovery_seconds, clock)` — CLOSED → OPEN at
N consecutive failures (OPEN short-circuits with `ProviderUnavailableError`
without invoking the call), HALF_OPEN probe after `recovery_seconds` on the
injected (simulated) clock, success closes. Per-port `FallbackPolicy`:

- **LLM**: alternate model/provider allowed (`run_with_fallback` tries the
  alternate on retryable failure).
- **Commerce**: `none` — failure propagates; a success receipt is never
  synthesized (commerce outage cannot fabricate success).
- **Notification**: `record` — outage yields `NotificationResult(status="failed")`,
  never `delivered`.
- **Storage**: `none`.

`run_with_fallback` **never returns a fabricated success** for any policy
(behavioral test per policy). "Authorization never fails open because a
provider is down": policy decisions (II.4 kernel) are asserted identical under
healthy vs. downed provider state — no provider state is an input to the
policy engine (structure test + decision-equality test).

## 7. Deterministic fakes (Ch II.5.9)

One fake per port, all driven by `FakeBehavior` + `SimulatedClock` (fakes
advance a simulated clock — **no real sleeping**, no randomness; ids/digests are
`sha256` of inputs). Scenario matrix (each its own test):

| Scenario | Behavior |
|---|---|
| success | deterministic output, stable ids |
| latency | clock advances by configured delay (wall-clock stays ~0) |
| timeout | `latency > timeout` ⇒ `ProviderTimeoutError` |
| duplicate events | same `event_id` emitted twice (dedup key stable) |
| out-of-order events | scripted `occurred_at` inversions |
| invalid signature | `parse_event` ⇒ `ProviderAuthenticationFailedError` |
| invalid event shape | `parse_event` ⇒ `ProviderInvalidRequestError` |
| rate limit | `ProviderRateLimitedError` + `retry_after_seconds` |
| hard failure | mapped class per configured `failure_class` |

## 8. Container / config seam

- `ForgeConfig` gains: `provider_llm/commerce/notification/storage` (default
  `"fake"`, env `FORGE_PROVIDER_*`, validated token regex),
  `provider_timeout_seconds`, `circuit_failure_threshold`,
  `circuit_recovery_seconds`, and credential fields `openrouter_api_key`,
  `whop_api_key` (env `FORGE_OPENROUTER_API_KEY` / `FORGE_WHOP_API_KEY`,
  `repr=False`, **never** in diagnostics — presence booleans only). Credentials
  are carried but unread: concrete adapters that consume them arrive with
  Book IV / Book VI.
- `ForgeServiceContainer.providers: ProviderRegistry | None` — II.5 owns the
  seam; the II.1-era `RuntimeError("…II.5…")` guard is superseded exactly as
  II.2/II.4 superseded theirs: a real `ProviderRegistry` is accepted, a
  non-conforming value raises `TypeError("providers must be a ProviderRegistry")`.
  Default remains `None` (explicit composition, no hidden singleton).
- Readiness: new honest entries `llm`, `commerce`, `notification`, `storage` —
  not wired ⇒ `NOT_CONFIGURED`/`required=False`; wired ⇒ live `health()` probe
  (`READY` / `UNAVAILABLE`, exceptions never crash `/ready`), `required=False`
  with note that the consuming bloc flips the flag when a serving path depends
  on it. `openrouter`/`whop` entries stay `NOT_CONFIGURED` (concrete vendor
  adapters are Book IV/VI) with updated notes. Overall status semantics
  unchanged (providers never block at II.5).
- `app.main._build_forge_container` wires `providers_from_config(config)` —
  the core application runs on fakes only.
- Lifecycle: startup logs provider wiring + probes health; failure logs the
  exception class name only (no payloads/credentials).

## 9. Replacement tests (Ch II.5.10)

A shared contract harness `tests/provider_contract.py` exposes
`run_llm_contract / run_commerce_contract / run_notification_contract /
run_storage_contract(provider)`. The focused suite runs the identical harness
against every fake **and** against a locally-defined alternate adapter
registered through the factory (the stand-in for a future concrete adapter —
none exists until Book IV/VI). Adding a concrete adapter later = add a
builder + a harness invocation; zero suite rewrites, zero domain changes.

Frozen **Acceptance II.5** clauses (verbatim) get dedicated tests:

1. *core application passes with only fake providers* — TestClient over
   `app.main` (health/ready/meta 200) with credentials **unset**, and config
   built with credential env present still selects fakes.
2. *no provider identifier is required as core domain PK* — AST/string scan:
   no domain module imports providers; no domain schema field/literal carries
   whop/openrouter/stripe-style provider identifiers.
3. *commerce outage cannot grant access* — downed commerce port ⇒ exception or
   explicit failure result, never a success/grant-shaped object; II.4 DENY
   decisions unchanged while commerce is down.
4. *LLM outage cannot corrupt canonical state* — canonical registry snapshot
   identical before/after a failed `generate`, and AST: canonical/schemas/
   provenance/persistence never import the LLM port.
5. *adapter replacement requires composition/config change, not domain
   rewrite* — alternate adapter registered via factory passes the same harness;
   registry binding swaps without touching domain modules.

## 10. Test matrix (focused suite `tests/test_forge_providers.py` + harness)

| Area | Chapters | Planned tests |
|---|---|---|
| A. Doctrine, specs, taxonomy, redaction, purity | II.5.1, II.5.7 | 6 |
| B. LLM port | II.5.2 | 7 |
| C. Commerce port | II.5.3 | 9 |
| D. Notification port | II.5.4 | 3 |
| E. Storage port | II.5.5 | 5 |
| F. Registry/factory/config selection | II.5.6 | 7 |
| G. Circuit/fallback/authorization safety | II.5.8 | 7 |
| H. Fake scenario matrix + determinism | II.5.9 | 11 |
| I. Container seam, readiness, diagnostics, endpoints | seam | 8 |
| J. Frozen Acceptance II.5 clauses | Acceptance | 5 |
| **Focused total** | | **≥68** |
| Legacy supersessions (existing suites, in place) | seam | 4 |
| Full regression | all | baseline 712 passed / 19 skipped ⇒ strictly greater passed, 0 failures |

Legacy supersessions (each edited in place with an explicit II.5
supersession comment, per the II.2/II.4 precedent):
`test_forge_service_composition.py::test_container_rejects_wired_providers_at_ii_1`,
`test_forge_persistence.py::test_container_still_rejects_policy_and_providers`
(RuntimeError ⇒ TypeError/ProviderRegistry), and
`test_forge_retrieval.py::test_no_commercial_or_provider_object_is_created`
(composition root now wires deterministic fakes; still no commercial vendor
object, no credential, no network client).

## 11. Exclusions (fail-closed if encountered)

- OpenRouter / Whop / any real vendor adapter, SDK, or network client.
- Live network calls of any kind (providers are in-process at II.5).
- Credential *use* (credentials are carried + redacted only).
- Retry engines, rate limiters, queueing, rate-limit budget accounting.
- Entitlement mutation, policy logic, identity (II.3/II.4/Book VI own them).
- Observability/metrics/tracing/log shipping (II.6 owns).
- Ask CEREBUS prompt/retrieval intelligence (Book IV), market-data ports
  (Book III), auth (Book IV wiring).
- Migration/schema changes (none — II.5 adds no tables).

## 12. Commit sequence (append-only ladder)

1. `II.5 plan + acceptance + GAP/ADR: …` (this file, ACCEPTANCE.md, GAP_ADR_001)
2. `II.5 provider ports: …` (providers package)
3. `II.5 composition seam: …` (config/container/lifecycle/app.main)
4. `II.5 tests: …` (harness + focused suite + legacy supersessions)
5. `II.5 evidence: …` (EVIDENCE.md, exact counts)
6. `II.5 ratification: …` (RATIFICATION.md verdict)
7. `II.5 verification record: CI green on final SHA` (after remote verification)

No amend/squash of the ladder (master build discipline).

## 13. Stop conditions (fail-closed)

Any frozen clause unproven; any non-frozen requirement discovered; any
predecessor found not-ancestor; any dependency ratification ≠ PASS; any full-
suite failure; live network/credential use required; scope needing II.6+
(first-seen discipline). `GAP_ADR_001` stays OPEN either way — it is reported,
not resolved unilaterally.
