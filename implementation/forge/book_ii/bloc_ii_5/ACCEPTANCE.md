# BOOK II / BLOC II.5 — PROVIDER PORTS & ADAPTER BOUNDARIES — ACCEPTANCE.md

Status: ACCEPTANCE
Date: 2026-10-09
Start SHA: `218c521013a2c3513d4a4409aff69188965492ec`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, I.3 `26e8635`,
I.4 `017fc96`, I.5 `686faa7`, II.1 `598b34c`, II.2 `772a0d2`, II.3 `cad9cd7`,
II.4 `ebda556`

Each clause names its verification. "test" = executable in the focused II.5
suite (`tests/test_forge_providers.py` + `tests/provider_contract.py` harness)
or the pre-existing regression suites; "review" = inspection recorded in
EVIDENCE.md. Frozen chapters cited are Book II plan Ch II.5.1–II.5.10.

## A. Provider contract doctrine (Ch II.5.1)

- A1 All four ports publish a `ProviderContractSpec` — test: every spec
  carries all eight elements (request, response, timeout, retry ownership,
  idempotency, error taxonomy, health semantics, redaction), none empty.
- A2 Ports are transport-neutral — test (AST): `app/forge/providers/*` imports
  no FastAPI/Starlette/httpx/requests/psycopg.
- A3 Domain never imports providers — test (AST): canonical, schemas,
  provenance, policy, retrieval, qa, persistence, backfill, service modules
  contain no `app.forge.providers` import.
- A4 Health semantics exist on every port — test: each protocol declares
  `health()`; each fake returns `ProviderHealth` with a bounded status.

## B. Failure taxonomy (Ch II.5.7)

- B1 Frozen failure classes exactly — test: `FAILURE_CLASSES` equals the
  eight frozen names, set and order.
- B2 One exception class per failure class — test: each subclass reports its
  class and is classified into the frozen set only.
- B3 Retry ownership — test: adapters never retry internally (fake call
  counters); `retryable` True only for timeout/unavailable/rate_limited;
  `retry_after_seconds` set only for rate_limited.
- B4 Redaction — test: error text/`redacted_summary()` never contains injected
  payload/credential sentinel strings.
- B5 Cancellation is control flow, not taxonomy — test:
  `ProviderCancelledError.failure_class is None` and it is absent from
  `FAILURE_CLASSES`.

## C. LLM port (Ch II.5.2)

- C1 `generate` returns deterministic text for identical requests — test
  (harness + direct).
- C2 Model identifier round-trips; usage/cost metadata present and
  deterministic — test.
- C3 Optional structured output capability — test: advertised via
  `capabilities()`; schema request validated; malformed schema ⇒
  `ProviderInvalidRequestError`.
- C4 Timeout — test: simulated latency > timeout ⇒ `ProviderTimeoutError`
  (class `timeout`), no output produced.
- C5 Cancel — test: cancel predicate ⇒ `ProviderCancelledError`.
- C6 Normalized hard failure — test: `failure_class="unavailable"` ⇒
  `ProviderUnavailableError`, retryable.
- C7 Prompt/retrieval intelligence absent — review: no prompt-assembly or
  retrieval logic in the port (Book IV scope), recorded in EVIDENCE.

## D. Commerce port (Ch II.5.3)

- D1 Checkout/session handoff — test: `create_checkout` returns a session with
  stable id.
- D2 Idempotency — test: same `idempotency_key` ⇒ same session, no duplicate.
- D3 Customer/subscription lookup — test (harness).
- D4 Provider event normalization — test: `parse_event` valid path yields
  `ProviderEvent` with event_id/type/occurred_at/payload.
- D5 Invalid signature ⇒ `ProviderAuthenticationFailedError`; invalid shape ⇒
  `ProviderInvalidRequestError` — test (two scenarios).
- D6 Duplicate and out-of-order event scripts — test: duplicate emits identical
  event_id; a dedup+sort reducer reaches identical final state from in-order,
  duplicate, and out-of-order deliveries.
- D7 Rate limit — test: `ProviderRateLimitedError` with `retry_after_seconds`.
- D8 No entitlement mutation in the adapter — test: `CommerceProvider` method
  set is exactly the frozen operations (create_checkout, get_customer,
  get_subscription, parse_event, health).
- D9 Health/reconciliation reads — test (harness): `health()` bounded status.

## E. Notification port (Ch II.5.4)

- E1 Transactional send — test (harness): success yields `NotificationResult`
  with message id.
- E2 Normalized delivery result — test: statuses ⊆ {delivered, failed}; outage
  under `record` policy ⇒ `failed`, never `delivered`.
- E3 No marketing automation — test: `NotificationProvider` method set is
  exactly {send, health}.

## F. Object/blob storage port (Ch II.5.5)

- F1 put/get round-trip with deterministic checksum — test.
- F2 Version behavior — test: repeated put increments version; `get(version=)`
  returns prior bytes.
- F3 Delete behavior — test: get after delete raises classified error
  (`invalid_request`), prior-version reads retained while version exists.
- F4 Signed/authorized access strategy — test: `access_strategy` returns
  bounded kind + deterministic target, no secret material in target.
- F5 No library/GitHub recovery source masquerades as blob storage — review:
  no such adapter exists; recorded in EVIDENCE.

## G. Registry / factory (Ch II.5.6)

- G1 Register/get/freeze — test: bindings resolve; mutation after freeze
  raises; unknown port/name fails closed (`ProviderConfigurationError`).
- G2 Type enforcement — test: non-conforming impl ⇒ `TypeError` naming the
  port.
- G3 Config selects adapters at composition root — test:
  `providers_from_config` binds each port from `config.provider_*`; unknown
  name ⇒ `ProviderConfigurationError`.
- G4 No `if provider == "whop"` spread — test (AST/string): no provider
  identifier branching in domain modules.
- G5 Factory extension without domain change — test: locally defined alternate
  builder registers and binds.

## H. Circuit / fallback policy (Ch II.5.8)

- H1 Breaker opens at threshold and short-circuits without invoking the call
  — test (call counters, simulated clock).
- H2 Recovery → half-open probe → close — test on simulated clock.
- H3 LLM fallback may select another model/provider — test: primary failure ⇒
  alternate used, response returned.
- H4 Commerce must not fabricate success when unavailable — test: hard failure
  ⇒ exception; no success-shaped result is ever constructed.
- H5 Notification outage records `failed` — test.
- H6 Authorization never fails open because a provider is down — test: II.4
  `DefaultDenyPolicyEngine` decisions identical under healthy vs. downed
  provider state; no provider state is an engine input.
- H7 No fabricated success under any policy — test: for every port policy,
  failure outcomes are exception or explicit failure result only.

## I. Fake providers (Ch II.5.9)

- I1 All nine scenarios — test (one each): success, latency, timeout,
  duplicate events, out-of-order events, invalid signature, invalid shape,
  rate limit, hard failure.
- I2 Determinism — test: two fresh fakes under identical config produce
  identical outputs; ids are input-derived.
- I3 No real sleeping — test: latency scenario completes in bounded wall-clock
  (simulated clock only).
- I4 Harness runs the identical contract suite against every fake and the
  alternate adapter — test (parametrized harness invocation).

## J. Container/config seam and frozen Acceptance II.5

- J1 Seam ownership — test: container accepts a real `ProviderRegistry`;
  `providers=object()` ⇒ `TypeError("…ProviderRegistry…")` (supersedes the
  II.1 RuntimeError guard in both legacy tests, in place).
- J2 Honest readiness entries — test: unwired ⇒ `NOT_CONFIGURED`/`required=False`
  for llm/commerce/notification/storage; wired+healthy ⇒ `READY`; scripted
  outage/health exception ⇒ `UNAVAILABLE` without crashing `/forge/v1/ready`;
  overall status stays `ready`; `openrouter`/`whop` remain `NOT_CONFIGURED`.
- J3 Diagnostics redaction — test: provider names present, credential values
  absent from `redacted_diagnostics()` and from `repr(ForgeConfig)`.
- J4 Config parsing — test: `FORGE_PROVIDER_*` defaults/overrides; invalid
  provider token or timeout ⇒ ValueError (fail-closed).
- J5 **Frozen Acceptance II.5 (verbatim, five clauses)** — tests:
  1. *core application passes with only fake providers* — TestClient over
     `app.main`: health/ready/meta 200 with credentials unset; credential env
     present does not change fake selection.
  2. *no provider identifier is required as core domain PK* — AST/string scan
     of domain schemas and modules.
  3. *commerce outage cannot grant access* — downed commerce never yields a
     grant-shaped success; DENY decisions unchanged.
  4. *LLM outage cannot corrupt canonical state* — canonical snapshot equality
     across failed generate + AST isolation.
  5. *adapter replacement requires composition/config change, not domain
     rewrite* — alternate adapter registered via factory passes the identical
     harness without touching domain files.

## K. Regression & discipline

- K1 Full suite green (test + postgres CI jobs), focused counts recorded in
  EVIDENCE; PG tests CI-executed.
- K2 Append-only ladder, no rewrites of predecessor artifacts; GAP_ADR_001
  recorded OPEN; exclusions in PLAN §11 held (review in EVIDENCE).
