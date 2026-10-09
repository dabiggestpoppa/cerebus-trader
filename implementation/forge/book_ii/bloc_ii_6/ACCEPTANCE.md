# BOOK II / BLOC II.6 — OBSERVABILITY, AUDITABILITY & ERROR CONTRACT — ACCEPTANCE.md

Status: ACCEPTANCE
Date: 2026-10-09
Start SHA: `0b88b47ba61ba62fd2924952b94e72dda0e6ea9d`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, I.3 `26e8635`,
I.4 `017fc96`, I.5 `686faa7`, II.1 `598b34c`, II.2 `772a0d2`, II.3 `cad9cd7`,
II.4 `ebda556`, II.5 `1496c16`.

Each clause names its verification. "test" = executable in the focused II.6
suite (`tests/test_forge_observability.py`) or the pre-existing regression
suites; "review" = inspection recorded in EVIDENCE.md. Frozen chapters cited
are Book II plan Ch II.6.1–II.6.10.

## A. Request correlation (Ch II.6.1)

- A1 Correlation scope propagates request id through the observed call chain —
  test: `correlation_scope` sets the context id; events emitted inside inherit
  it; nested scopes restore (TestCorrelationPropagation).
- A2 FORGE endpoints surface the effective request id — test: TestClient
  `X-Request-Id` header round-trips on `/forge/v1/health|ready|meta`;
  absent/invalid inbound id ⇒ generated `fg-` id (regression +
  TestCorrelationPropagation).
- A3 Request events carry the request id — test: route emission produces an
  event whose `request_id` equals the response's (TestCorrelationPropagation).

## B. Structured events (Ch II.6.2)

- B1 Frozen field set — test: `ForgeEvent` exposes exactly the frozen fields;
  schema_version is `FORGE_EVENT_V1` (TestEventSchema).
- B2 Structured, not free-form — test: attributes are scalar-only, bounded
  count, bounded value length; nested containers refused (TestEventSchema).
- B3 Bounded fields — test: every string field enforces its length bound;
  oversized values fail closed at construction (TestEventSchema).
- B4 Severity and outcome vocabulary — test: severity ∈ {DEBUG, INFO,
  WARNING, ERROR, CRITICAL}; outcome ∈ {success, failure, denied, degraded};
  unknown values refused (TestEventSchema).
- B5 Deterministic output — test: identical inputs + injected clock ⇒
  byte-identical serialized events; seq is monotonic and gapless
  (TestDeterministicOrdering).
- B6 Deterministic ordering — test: events sort by seq; two emitters over the
  same script produce identical sequences (TestDeterministicOrdering).

## C. Tracing boundaries (Ch II.6.3)

- C1 Boundary vocabulary — test: component ∈ {api, identity, policy,
  persistence, retrieval, provider, jobs, observability}; operation non-empty
  bounded (TestEventSchema).
- C2 No proprietary payloads in attributes — test: protected-text sentinel
  passed as an attribute value never reaches any sink (TestRedaction).

## D. Metrics (Ch II.6.4)

- D1 Exact frozen metric names — test: registry exposes the Ch II.6.4 list
  (request rate/errors/latency, DB latency/pool, policy allow/deny, auth
  failures, retrieval counts, provider latency/error/rate-limit, LLM
  token/cost, commerce event processing, job lag/failure) (TestMetrics).
- D2 Metrics emitted from observed activity — test: policy decision, provider
  call and request events increment the matching counters (TestMetrics).

## E. Retrieval access audit (Ch II.6.5)

- E1 Frozen record fields — test: who/service, capability, canonical and
  retrieval object ids, exposure, decision, timestamp, correlation
  (TestRetrievalAccessAudit).
- E2 No source documents in audit records — test: protected body sentinel
  absent from every serialized record (TestRetrievalAccessAudit).
- E3 Append-only bounded trail — test: capacity enforced, oldest evicted,
  append order preserved (TestRetrievalAccessAudit).

## F. Entitlement audit (Ch II.6.6)

- F1 Frozen event vocabulary — test: {grant, renew, grace, expire, revoke,
  admin_correction}; unknown event refused (TestEntitlementAudit).
- F2 Source event/provider mapping recorded — test: record carries
  source_event_id and provider mapping (TestEntitlementAudit).
- F3 No mutation authority — test: the audit trail type exposes record/snapshot
  only; no entitlement state machine exists in II.6 (review +
  TestEntitlementAudit API-surface test).

## G. Error taxonomy (Ch II.6.7)

- G1 Exact frozen nine classes — test: `ForgeErrorClass` set and names equal
  the frozen list (TestErrorContract).
- G2 Provider mapping exact — test: the eight II.5 failure classes map per
  PLAN §5 table; mapping is total and injective-enough to stay distinguishable
  (TestErrorContract).
- G3 Origin retained — test: a mapped provider error reports
  `origin="provider"` + provider type/name/failure class; application errors
  report `origin="application"` (TestErrorContract).
- G4 No internals leaked — test: error text/safe response never contains the
  injected payload/credential sentinels or exception internals
  (TestErrorContract).

## H. Safe error responses (Ch II.6.8)

- H1 Stable shape — test: `safe_error_response` returns exactly
  {code, message, request_id}; request id present whenever known
  (TestErrorContract).
- H2 No stack traces/SQL/secrets/hidden existence — test: raising through the
  FORGE envelope on a scripted failure yields the safe body only
  (TestErrorContract + route regression).

## I. Cost/usage ledger (Ch II.6.9)

- I1 Record fields — test: request id, provider/model ids, input/output usage
  when supplied, normalized cost when known, latency, success
  (TestUsageLedger).
- I2 Partial data stays honest — test: usage not supplied ⇒ fields None, never
  fabricated; failure ⇒ success=False (TestUsageLedger).
- I3 No financial accounting claims — test: ledger exposes no totals,
  balances or invoice semantics (review + API-surface test).

## J. Redaction & minimization (Phase 5)

- J1 Secrets — test: bearer/api-key sentinels scrubbed pre-emission from
  events, log lines and diagnostics (TestRedaction).
- J2 Session tokens — test: raw session-token sentinel never reaches a sink or
  health summary (TestRedaction).
- J3 Restricted/protected content — test: protected corpus sentinel absent
  from events, logs, error responses and readiness/health output
  (TestRedaction).
- J4 Pre-emission law — test: sink receives already-redacted events (a
  recording sink holding raw values would fail; the sink only ever sees
  scrubbed values) (TestRedaction).

## K. Container integration & honesty (Phase 6)

- K1 Seam ownership — test: container accepts `ForgeObservabilityService`;
  `observability=object()` ⇒ TypeError naming the seam (TestContainerIntegration).
- K2 Honest readiness — test: unwired ⇒ `NOT_CONFIGURED` + `required=False`;
  wired ⇒ `READY`; overall readiness never blocked or degraded by telemetry
  presence/absence (TestContainerIntegration).
- K3 No telemetry dependency for core execution — test: FORGE endpoints work
  with observability unwired; sink raising never breaks a response
  (TestContainerIntegration).
- K4 Diagnostics — test: `redacted_diagnostics` discloses observability
  presence/counts only; no event payload values leak (TestContainerIntegration).
- K5 Config — test: enabled/capacity parse from env; invalid capacity ⇒
  ValueError (fail-closed); disabled ⇒ factory returns the no-op wiring
  (TestContainerIntegration).

## L. Audit-stream separation & II.4 reuse (Phase 3)

- L1 Four streams distinguishable — test: telemetry, security_audit,
  usage_ledger, entitlement_audit records carry distinct stream tags and
  types; no single generic log (TestSecurityAudit).
- L2 II.4 authority reused — test: policy allow/deny decisions appear in the
  security-audit stream as adapters of `PolicyAuditRecord`; the II.4 engine
  remains the only decision authority (no second policy engine exists in
  II.6) (TestSecurityAudit).
- L3 Evidence provenance untouched — test: `app.forge.provenance` untouched by
  II.6; no evidence content in telemetry (review + AST).

## M. Masquerade law & failure matrix (Phase 4/7)

- M1 Provider failure never masquerades — tests: timeout/rate-limit/circuit
  open/unavailable through `observe_provider_call` raise or degrade
  explicitly; never a success-shaped commerce result, never a changed
  authorization decision, never a canonical write, never a READY health entry
  for the failed capability (TestProviderObservability).
- M2 Failure/recovery events — tests: provider timeout (11), rate limit (12),
  circuit-open (13), recovery (14), persistence failure (15), canonical write
  rejection (16), QA abstention (17), QA unsupported (18), health degradation
  (19), unknown error (22) each emit the classified event (TestFailureMatrix).
- M3 Missing correlation context (20) — test: deterministic `unattributed`
  bucket + counter, no crash (TestFailureMatrix).
- M4 Malformed event (21) — test: emitter refuses deterministically;
  `safe_emit` counts and never crashes the caller (TestFailureMatrix).
- M5 No logging-induced auth change (23) — test: identical policy decisions
  with and without observation; observation never feeds the engine
  (TestFailureMatrix).
- M6 No logging-induced canonical mutation (24) — test: canonical snapshot
  identical across observed vs unobserved failure paths (TestFailureMatrix).

## N. Frozen Acceptance II.6 (verbatim, four clauses)

- N1 *protected access and entitlement mutations are reconstructable from
  audit metadata* — tests: a guarded protected access can be fully rebuilt
  (who, capability, object ids, exposure, decision, timestamp, correlation)
  from the security-audit + retrieval-audit trails alone; an entitlement
  event sequence reconstructs grant→renew→revoke ordering from records
  (TestSecurityAudit, TestEntitlementAudit).
- N2 *secrets/protected corpus are absent from standard logs* — test: capture
  the `forge` logger output across a run with injected sentinels; zero
  occurrences (TestRedaction).
- N3 *provider and application failures are distinguishable* — test: origin
  field + mapping; a provider timeout and an application INTERNAL error never
  share code/origin (TestErrorContract).
- N4 *request IDs connect user-visible errors to internal traces* — test: the
  request id on a safe error response equals the correlation id on the
  emitted internal event (TestErrorContract + TestCorrelationPropagation).

## O. Regression & discipline

- O1 Full suite green (test + postgres CI jobs); focused counts recorded in
  EVIDENCE; PG tests CI-executed (directive items 26–32).
- O2 Append-only ladder; predecessor artifacts untouched; GAP_ADR_001 carried
  forward unchanged and OPEN; PLAN §10 exclusions held (review in EVIDENCE).
