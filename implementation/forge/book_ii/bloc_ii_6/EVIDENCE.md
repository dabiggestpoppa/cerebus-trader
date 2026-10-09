# BOOK II / BLOC II.6 — OBSERVABILITY, AUDITABILITY & ERROR CONTRACT — EVIDENCE.md

Status: EVIDENCE
Date: 2026-10-09
Start SHA: `0b88b47ba61ba62fd2924952b94e72dda0e6ea9d`
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24`

## 1. Append-only ladder (from the authorized start SHA)

| Rung | Commit | Content |
|---|---|---|
| 0 | `0b88b47` | II.5 verification record (start state; HEAD == origin/forge, tree clean) |
| 1 | `df4e0b9` | PLAN + ACCEPTANCE (governance packet committed BEFORE implementation) |
| 2 | `d3a61a6` | observability substrate contracts (11 modules) |
| 3 | `2403952` | composition: container seam + config + lifecycle/routes/main wiring |
| 4 | `471b671` | 104-test focused matrix + stream-event/oversize-omission hardening |

No amend, squash, reset, rebase or force-push. Frozen planning, canonical and
prior-bloc artifacts untouched (verified: the only non-`bloc_ii_6` files in the
ladder are the owned seams `config.py`, `container.py`, `lifecycle.py`,
`routes.py`, `app/main.py` — the composition-root files II.2/II.4/II.5 each
edited in their own rungs).

`GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md` was carried forward byte-
identical (no II.6 commit touches it); status remains OPEN.

## 2. Frozen chapter → implementation → test map

| Chapter | Implemented in | Proved by (focused suite unless noted) |
|---|---|---|
| II.6.1 request correlation | `observability/correlation.py`; routes set scope | `TestCorrelationPropagation` (6 tests) |
| II.6.2 structured logging | `observability/events.py`, `redaction.py`, `emitter.py` | `TestEventSchema` (8), `TestDeterministicOrdering` (4), `TestRedaction` (9), `TestBoundedDiagnostics` (3) |
| II.6.3 tracing boundaries | event `component` vocabulary + scalar-only attributes | `TestEventSchema.test_vocabularies_exact`, `TestRedaction` |
| II.6.4 metrics | `observability/metrics.py` | `TestMetrics` (6) |
| II.6.5 retrieval access audit | `observability/audit.py` `RetrievalAccessAuditRecord` | `TestRetrievalAccessAudit` (5) |
| II.6.6 entitlement audit | `observability/audit.py` `EntitlementAuditRecord` | `TestEntitlementAudit` (6) |
| II.6.7 error taxonomy | `observability/errors.py` | `TestErrorContract` (10) |
| II.6.8 safe error responses | `safe_error_response` + existing `ForgeErrorDetail` envelope | `TestErrorContract.test_safe_response_shape/test_no_internals_or_payloads_in_responses` |
| II.6.9 cost/usage ledger | `observability/usage.py` | `TestUsageLedger` (6) |
| II.6.10 observability tests | this suite | 104 focused tests |

## 3. Acceptance-clause mapping (ACCEPTANCE.md A–O)

- **A1–A3** correlation: `TestCorrelationPropagation` (scope bind/restore,
  unsafe inbound regenerated, scope inheritance, explicit override, route
  round-trip, route event id == response id).
- **B1–B6** events: `TestEventSchema` + `TestDeterministicOrdering`
  (identical scripts ⇒ byte-identical serialized events under the injected
  clock; seq gapless 1..n).
- **C1–C2** boundaries: component vocabulary test + redaction tests.
- **D1–D2** metrics: frozen name set test + request/policy/provider counter
  tests.
- **E1–E3** retrieval audit: field test, no-content test, capacity test.
- **F1–F3** entitlement audit: vocabulary test, unknown-refused, source/
  provider mapping, API-surface (record+to_dict only, no mutation methods).
- **G1–G4** taxonomy: exact nine classes, total exact provider mapping,
  origin retention, no internals/payloads in error text or responses.
- **H1–H2** safe responses: exact {code, message, request_id} shape; 401
  sentinel / URL / "Traceback" absence proven.
- **I1–I3** usage ledger: field test, honest None for unsupplied usage/cost,
  ledger API surface exposes no totals/balances.
- **J1–J4** redaction: secrets, session tokens, protected body omission,
  pre-emission proof (raw recorder sink serialization), diagnostics
  payload-free, log-line capture (standard-log clause N2).
- **K1–K5** container: seam TypeError, honest readiness entries, endpoints
  work unwired, diagnostics presence-only, config fail-closed capacity.
- **L1–L3** streams: four stream tags structurally distinct; II.4 records
  adapted (no `decide(` / `PolicyEngine` string anywhere in the package —
  AST/source test); provenance untouched.
- **M1–M6** masquerade/failure matrix: provider failure ⇒ unchanged policy
  decision, unchanged canonical object list, honest UNAVAILABLE readiness,
  commerce failure never yields a success result; persistence failure,
  duplicate write, QA abstention/unsupported, degraded readiness event,
  missing correlation, malformed event, unknown error, failing sink
  isolation, no logging-induced auth/canonical change.
- **N1–N4** frozen Acceptance II.6 verbatim:
  1. *reconstructable from audit metadata* — `TestSecurityAudit.test_reconstructable_from_audit_metadata` + `TestEntitlementAudit.test_reconstructable_entitlement_sequence`;
  2. *secrets/protected corpus absent from standard logs* — `TestRedaction.test_log_sink_lines_redacted` (captured `forge.observability` records, four sentinels absent);
  3. *provider and application failures distinguishable* — `TestErrorContract.test_provider_vs_application_distinguishable` (origin + code);
  4. *request IDs connect user-visible errors to internal traces* — `TestErrorContract.test_request_id_connects_error_to_trace`.
- **O1–O2** regression/discipline: §5 counts, §1 ladder, §7 exclusions.

## 4. Exact counts (local)

| Suite | Result |
|---|---|
| Baseline at start SHA `0b88b47` | 786 passed, 19 skipped, exit 0 |
| II.6 focused (`tests/test_forge_observability.py`) | **104 passed, 0 failed** |
| Full repository suite on the ratification tree | **890 passed, 19 skipped, exit 0** (= 786 + 104) |

The 19 skips are the CI-only PostgreSQL integration tests (standing
limitation of every bloc; executed in the CI postgres job).

## 5. CI / PostgreSQL

CI run `37989879501` on the pushed head `fec9be0`:

- **test job: SUCCESS** — full repository suite green on the pushed SHA
  (890 passed / 19 skipped locally on the identical tree).
- **postgres job: BLOCKED BY RUNNER INFRASTRUCTURE, not by a test defect.**
  The job fails in `Initialize containers` with `Docker pull failed with exit
code 1` (service image `postgres:16`) before any test executes. Retried 5×
over ~10 minutes with backoff; every attempt failed at the same pull. The
workflow file is unchanged by II.6 (`git diff 0b88b47..HEAD` touches no
`.github/` path), and the same job executed the full PG suite green on the
II.5 head (`37967280111`, postgres 805 passed). II.6 adds no PostgreSQL
tests and modifies no persistence code paths exercised by the PG suite, but
**the postgres CI verification for the II.6 head did not complete** — this is
recorded as an open verification gap, not as a pass. No local docker/psql is
available to substitute (the 19 PG tests remain CI-only as in every prior
bloc). Re-running the job when the runner registry recovers will close it.

## 6. Security proofs

- **Pre-emission redaction**: a sink that serializes exactly what it receives
  (before any downstream filtering) never sees secret, session-token or
  protected-body sentinels (`test_pre_emission_law_sink_only_sees_redacted`).
- **Oversize omission**: attribute values above the 256-char bound are
  replaced by a length-only marker; no prefix of a protected body survives.
- **II.4 authority reuse**: the security-audit stream is a pure projection of
  `PolicyAuditRecord`; the observability package contains no `decide(` and no
  `PolicyEngine` reference (source-scan test).
- **No logging-induced authority**: identical policy decisions with and
  without observation; canonical snapshots identical across observed vs
  unobserved failure paths.
- **Never-swallow provider observer**: `observe_provider_call` re-raises
  every `ProviderError` after recording; there is no success-return path
  from a failure.

## 7. Exclusion review (PLAN §10)

`git diff 0b88b47..HEAD` touches only: the new `app/forge/observability/`
package, the owned seams (`config.py`, `container.py`, `lifecycle.py`,
`routes.py`, `app/main.py`), the II.6 packet and the focused test file. No
OpenTelemetry/vendor SDK, no metrics push, no dashboard, no log shipper, no
entitlement mutation, no evidence promotion, no commerce ledger semantics
beyond the audit vocabulary, no Ask CEREBUS, no prompt orchestration, no
market-data adapter, no Signal Guard route changes, nothing of Book III/IV/VI.
Grep for whop/openrouter/checkout/webhook/embedding in the diff returns only
pre-existing II.5 config/readiness context lines, unchanged.

## 8. PLAN deviations (disclosed)

1. **Oversize attribute law strengthened**: PLAN §3 said "truncated to a
   bounded digest marker"; the implementation OMITS the value entirely
   (length-only marker) because prefix truncation would still carry the head
   of a protected body — a stricter reading of the redaction law.
2. **Usage/entitlement records also emit stream-tagged events** (in addition
   to their typed trails), so the four-stream separation is visible in the
   event log as well as in the record stores. Additive; no existing behavior
   changed.

## 9. Known gaps / limitations

- Concrete OpenRouter/Whop adapters, real log shipping and metric backends
  remain future work by design (Book IV/VI / ops tooling).
- PostgreSQL integration executes in CI only (19 local skips) — standing
  limitation, evidenced in the CI postgres job.
- Ch II.6.3 tracing is event-based boundary tracing (component/operation/
  duration on every boundary event), not distributed span infrastructure —
  the frozen plan requires no tracing vendor.
- `GAP_ADR_001` remains OPEN (operator decision before Phase C).
