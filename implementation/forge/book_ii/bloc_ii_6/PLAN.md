# BOOK II / BLOC II.6 — OBSERVABILITY, AUDITABILITY & ERROR CONTRACT — PLAN.md

Status: PLAN (committed before implementation)
Date: 2026-10-09
Start SHA: `0b88b47ba61ba62fd2924952b94e72dda0e6ea9d`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`
Dependency ratifications: I.1 `aca9438`, I.2 `5ce3246`, I.3 `26e8635`,
I.4 `017fc96`, I.5 `686faa7`, II.1 `598b34c`, II.2 `772a0d2`, II.3 `cad9cd7`,
II.4 `ebda556`, II.5 `1496c16`.

`GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md` (II.5 packet) is carried
forward **unchanged and OPEN**. II.6 neither resolves nor closes it; the Phase C
gate question stays with the operator.

## 1. Objective and governing law

Make every important FORGE decision traceable without logging secrets or
leaking proprietary corpus content (frozen Book II plan, Bloc II.6 objective).

Governing law for this bloc:

> Observability **describes what happened**. It never creates business,
> security, evidence, or commercial authority of its own.

Concretely:

- An emitted event never changes an authorization decision.
- An emitted event never mutates canonical state.
- No core execution path requires telemetry infrastructure to run.
- Redaction happens **before emission**, never by trusting a downstream
  dashboard to hide fields.

## 2. Frozen authorities implemented (Ch II.6.1–II.6.10)

| Chapter | Frozen requirement | Where implemented |
|---|---|---|
| II.6.1 | Request correlation ID propagated API → identity → policy → persistence → provider → response | `observability/correlation.py` (context propagation) + FORGE routes set/consume `X-Request-Id` |
| II.6.2 | Structured events with the frozen field list; never raw secrets/protected context | `observability/events.py` + `observability/redaction.py` |
| II.6.3 | Trace high-value boundaries (auth, policy, DB, retrieval, provider, jobs); no proprietary payloads in attributes | event `component`/`operation` vocabulary + bounded attribute allowlist |
| II.6.4 | Foundation metrics list | `observability/metrics.py` (exact frozen metric names) |
| II.6.5 | Retrieval access audit (who/service, capability, object IDs, exposure, decision, timestamp; no source documents) | `observability/audit.py` `RetrievalAccessAuditRecord` |
| II.6.6 | Entitlement audit vocabulary (grant/renew/grace/expire/revoke/admin correction + source event/provider mapping) | `observability/audit.py` `EntitlementAuditRecord` (records only; mutation belongs to Book VI) |
| II.6.7 | Stable 9-class application error taxonomy; provider errors map without leaking internals | `observability/errors.py` |
| II.6.8 | Safe error responses: stable code + safe message + request ID | `observability/errors.py` `safe_error_response`, integrated with the existing II.1 `ForgeErrorDetail` envelope |
| II.6.9 | Cost/usage ledger (request, provider/model, usage if supplied, normalized cost if known, latency, success) | `observability/usage.py` |
| II.6.10 | Observability tests | `tests/test_forge_observability.py` |

## 3. Architecture — new package `app/forge/observability/`

Service-layer substrate. Deterministic, in-process, no vendor, no network, no
external telemetry infrastructure. Modules:

- **`events.py`** — frozen `ForgeEvent` record. Fields (Ch II.6.2, exact):
  `schema_version`, `seq`, `timestamp`, `environment`, `request_id`, `job_id`,
  `actor_class`, `actor_id`, `component`, `operation`, `object_type`,
  `object_id`, `capability`, `outcome`, `reason_code`, `duration_ms`,
  `provider_type`, `provider_name`, `model_id`, `error_class`,
  `provider_failure_class`, `attributes`. Severity vocabulary
  (DEBUG/INFO/WARNING/ERROR/CRITICAL). All strings bounded; `attributes` is a
  bounded scalar-only map (no nested structures, no free-form dumps).
- **`redaction.py`** — pre-emission redaction: bounded attribute values,
  secret-shaped string scrubbing (bearer tokens, `token=`/`key=` pairs,
  long opaque high-entropy runs), never-full-content law (long text is
  truncated to a bounded digest marker, never carried).
- **`emitter.py`** — `EventSink` protocol, `InMemoryEventSink` (bounded ring,
  deterministic), `StructuredLogSink` (stdlib logging, sorted-key JSON, safe
  fields only), `ForgeEventEmitter` (validation, seq assignment, injected
  clock, redaction). Malformed events are refused deterministically;
  `safe_emit` converts a malformed event into a bounded counter, never a
  crash of the caller.
- **`metrics.py`** — foundation metric registry (counters + bounded
  histograms) with the exact Ch II.6.4 names; deterministic snapshot.
- **`correlation.py`** — contextvar-based correlation scope
  (`correlation_scope(request_id)`), used as the emitter's default request id.
  Missing context degrades to a deterministic `unattributed` bucket +
  counter — never a crash, never a fabricated id.
- **`audit.py`** — the auditability layer (see §4).
- **`usage.py`** — Ch II.6.9 ledger records; append-only, bounded.
- **`errors.py`** — the error contract (see §5).
- **`integration.py`** — `observe_provider_call(...)`: times one provider
  call, emits the provider event, counts metrics, and **re-raises**; it can
  never convert a failure into a success.
- **`service.py`** — `ForgeObservabilityService` facade (the type owned by
  `container.observability`) + `observability_from_config(...)` composition
  factory.

Import law (AST-enforced): the package imports no FastAPI/Starlette/httpx/
requests/psycopg; canonical, schemas, provenance, identity, policy, retrieval,
qa, persistence and backfill modules import no `app.forge.observability`
(domain purity — the service layer observes, the domain does not); the
providers package imports no observability (no cycles).

## 4. Auditability — four preserved streams (Phase 3)

One generic log is forbidden. The substrate keeps four distinguishable
streams, each with its own record type and trail:

1. **Operational telemetry** — `ForgeEvent` (`stream="telemetry"`): what a
   component did.
2. **Security audit** — authorization decisions. **Reused, not rebuilt**: the
   II.4 `PolicyAuditRecord` trail remains the single policy authority; the
   observability service adapts those records into its security-audit stream
   (`stream="security_audit"`) without re-deciding anything. II.4's bounded,
   content-free audit is preserved verbatim.
3. **Evidence provenance** — Book I `app.forge.provenance` remains the only
   "why a CEREBUS claim is supported" authority. II.6 adds **nothing** here
   and never copies evidence content into telemetry.
4. **Commercial ledger** — entitlement audit *vocabulary* only
   (`EntitlementAuditRecord`: grant/renew/grace/expire/revoke/admin_correction
   + source event id/provider mapping). II.6 records; Book VI mutates. No
   entitlement semantics are invented here.

## 5. Error contract (Phase 4)

Frozen Ch II.6.7 taxonomy — exact set and names:

`AUTHENTICATION, AUTHORIZATION, VALIDATION, NOT_FOUND, CONFLICT, RATE_LIMIT,
DEPENDENCY, DATA_INTEGRITY, INTERNAL`

Provider-failure → application-taxonomy mapping (exact, test-enforced; the
provider failure class is retained on the error so the two taxonomies stay
distinguishable, satisfying Acceptance II.6 clause 3):

| Provider failure class (II.5) | Application class (II.6.7) |
|---|---|
| `unavailable` | `DEPENDENCY` |
| `timeout` | `DEPENDENCY` |
| `rate_limited` | `RATE_LIMIT` |
| `invalid_request` | `VALIDATION` |
| `authentication_failed` | `AUTHENTICATION` |
| `upstream_rejected` | `DEPENDENCY` |
| `malformed_response` | `DATA_INTEGRITY` |
| `unknown` | `DEPENDENCY` |

`ForgeApplicationError` carries: application class, stable safe code, safe
message, optional request id, `origin` (`application` | `provider`) and
bounded provider metadata (type/name/failure class only). Safe responses
(Ch II.6.8) expose exactly `code`, `message`, `request_id` — never stack
traces, SQL, secrets, hidden object existence, or provider credential detail.

Masquerade law (proved by tests): a provider failure can never present as a
successful commerce operation, a successful authorization, a validated
empirical claim, a successful canonical write, or a healthy capability.

## 6. Redaction and data minimization (Phase 5)

- Redaction is applied inside the emitter, before any sink sees the event.
- Test sentinels prove absence of: raw secrets, session tokens, protected
  corpus text, restricted research content, raw provider payloads, private
  user content in events, log lines, diagnostics, error responses and health
  summaries.
- Long/provenance-bearing values are replaced by bounded markers; the full
  value never reaches a sink even when a caller passes it by mistake.

## 7. Container integration (Phase 6)

- `ForgeServiceContainer.observability` is owned by II.6: typed as
  `ForgeObservabilityService | None`, structural `TypeError` on foreign
  objects (same discipline as persistence/policy/providers).
- Readiness gains an `observability` entry: `READY` when wired,
  `NOT_CONFIGURED` otherwise; `required=False` always — telemetry never blocks
  serving and its absence never degrades readiness.
- `ForgeLifecycle.startup/shutdown` emit lifecycle events when wired.
- FORGE routes set the correlation scope, emit request events, and surface
  the request id on responses as today.
- Config adds `observability_enabled` (default true) and
  `observability_event_capacity` (default 512), disclosed in redacted
  diagnostics as presence/booleans only.
- Composition root (`app.main._build_forge_container`) wires
  `observability_from_config(forge_config)` — in-process sinks only.

## 8. Deterministic test matrix (Phase 7)

`tests/test_forge_observability.py` covers the directive matrix items 1–25 and
26–29 targeted, with 30–32 from Signal Guard / full suite / CI postgres:

1 correlation propagation · 2 request identity · 3 structured event schema ·
4 deterministic event output (identical inputs ⇒ identical records, injected
clock) · 5 bounded diagnostics · 6 secret redaction · 7 session-token
redaction · 8 restricted-content redaction · 9 policy deny audit · 10 policy
allow audit · 11 provider timeout · 12 provider rate limit · 13 provider
circuit-open · 14 provider recovery · 15 persistence failure · 16 canonical
write rejection · 17 QA abstention · 18 QA unsupported answer · 19 health
degradation · 20 missing correlation context · 21 malformed event · 22 unknown
error · 23 no logging-induced authorization change · 24 no logging-induced
canonical mutation · 25 no telemetry dependency required for core execution ·
26 existing service/container regressions · 27 existing provider contract
suite · 28 existing identity/policy regressions · 29 Book I QA/retrieval
regressions · 30 Signal Guard · 31 full repository suite · 32 PostgreSQL CI.

Plus frozen-chapter additions: Ch II.6.4 metric emission, Ch II.6.5/II.6.6
audit trails, Ch II.6.7 mapping exactness, Ch II.6.8 safe responses,
Ch II.6.9 usage ledger, and the four verbatim Acceptance II.6 clauses.

## 9. Book II cross-bloc readiness (Phase 8)

After II.6, the frozen Book II recommended order requires, before Book II can
be called complete: (1) II.1–II.6 implementation complete [now true], (2) a
cross-bloc adversarial suite, (3) a Book II evidence pack, (4) Book II
contract ratification/freeze. **II.6 passing does not complete Book II.** The
remaining closure requirements are recorded explicitly in EVIDENCE/RATIFICATION
and in the final report.

## 10. Non-goals / explicit exclusions (Phase 11 discipline)

No OpenTelemetry/vendor telemetry, no metrics push, no dashboards, no log
shipping, no tracing backend, no entitlement mutation (Book VI), no evidence
promotion, no commerce ledger semantics beyond the audit vocabulary, no Ask
CEREBUS, no prompt orchestration, no market-data adapters, no new exposure
classes, no canonical ontology changes, no changes to Signal Guard routes,
no changes to frozen planning/canonical/prior-bloc artifacts, and nothing of
Book III/IV/VI.

## 11. Governance

Append-only ladder: PLAN/ACCEPTANCE → contracts → composition → tests →
evidence → ratification, inspectable commits, no amend/squash/reset/rebase,
fast-forward push only, CI verified on the pushed head.
