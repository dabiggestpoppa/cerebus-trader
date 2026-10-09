# BOOK II / BLOC II.6 — OBSERVABILITY, AUDITABILITY & ERROR CONTRACT — RATIFICATION.md

## RATIFICATION

Ratified: 2026-10-09
Ladder (append-only from the accepted start SHA `0b88b47`): `0b88b47` →
`df4e0b9` (plan + acceptance) → `d3a61a6` (substrate contracts) → `2403952`
(composition seam) → `471b671` (tests) → this evidence/ratification rung.

**Verdict: PASS — CLOSED**

## Explicit ratification statements

1. **Frozen specification met.** Book II plan Ch II.6.1–II.6.10 is implemented
   in full: correlation propagation with disclosed fallback; structured
   bounded events with the frozen Ch II.6.2 field set; boundary tracing via
   the component/operation vocabulary; the exact Ch II.6.4 foundation metric
   names; the Ch II.6.5 retrieval access audit and Ch II.6.6 entitlement
   audit vocabulary; the exact frozen nine-class Ch II.6.7 taxonomy with a
   total provider-failure mapping; Ch II.6.8 safe responses; the Ch II.6.9
   cost/usage ledger; and the Ch II.6.10 test discipline (EVIDENCE §2).
2. **The four verbatim Acceptance II.6 clauses are proven executable**
   (EVIDENCE §3.N): protected access and entitlement mutations reconstructable
   from audit metadata; secrets/protected corpus absent from standard logs;
   provider and application failures distinguishable; request IDs connecting
   user-visible errors to internal traces.
3. **All ACCEPTANCE A–O clauses verified** — 104 focused tests, full
   regression green locally (EVIDENCE §3/§4).
4. **Auditability preserves its four streams.** Telemetry, security audit,
   usage ledger and entitlement audit are structurally distinct record
   types/tags; II.4 remains the sole authorization-decision authority (the
   observability package contains no policy engine and no `decide(` —
   source-scanned); Book I provenance is untouched and holds evidence truth;
   entitlement semantics beyond the frozen audit vocabulary are not invented
   (Book VI owns mutation).
5. **The error contract integrates without collapsing taxonomies.** Provider
   failures map into the II.6 classes while retaining `origin="provider"` and
   their II.5 failure class, so provider and application failures stay
   distinguishable; safe responses expose exactly code/message/request_id.
6. **Redaction happens before emission.** A raw-recorder sink never sees
   secret, session-token or protected-body sentinels; oversized values are
   omitted entirely (EVIDENCE §8 deviation 1, stricter than PLAN).
7. **Seam ownership is honest.** `container.observability` accepts only the
   typed `ForgeObservabilityService`; readiness discloses
   READY/NOT_CONFIGURED with `required=False` and never blocks; core
   execution and all FORGE endpoints work with the seam unwired and with a
   failing sink.
8. **No scope creep.** No vendor telemetry, no metrics push, no entitlement
   mutation, no evidence promotion, no Ask CEREBUS, no market-data code,
   nothing of Book III/IV/VI (EVIDENCE §7 exclusion review).
9. **Predecessor authority untouched.** Frozen planning, canonical and
   prior-bloc artifacts unchanged; `GAP_ADR_001` carried forward byte-identical
   and remains **OPEN** — this ratification does not resolve it.
10. **Deviations disclosed, not hidden** (EVIDENCE §8): oversize-attribute
    omission strengthening; usage/entitlement records also emit stream-tagged
    events.

## Limitations carried forward

- PostgreSQL integration executes in CI only (19 local skips) — same standing
  limitation as every prior bloc; CI evidence recorded in the verification
  rung that follows this commit.
- Distributed span infrastructure, real log shipping and metric backends are
  out of scope by design (frozen plan requires no observability vendor).

## Remaining Book II closure requirements (Phase 8 assessment)

II.6 passing does **not** complete Book II. The frozen recommended order
(Book II plan, "RECOMMENDED IMPLEMENTATION ORDER") requires after II.6:

1. ~~II.1–II.6 implementation complete~~ — now true (all six blocs ratified).
2. **Cross-bloc adversarial integration suite** — NOT started; must exercise
   the three frozen integration paths (protected corpus request, entitlement
   change via fake commerce provider, provider failure) end-to-end across
   blocs, including the frozen Book II security invariants.
3. **Book II evidence pack** — NOT started; consolidated cross-bloc evidence.
4. **Book II contract ratification/freeze** — NOT started; freezes the Book
   II contracts before Books III/VI may depend on them.

Additionally the Phase C gate question stays with the operator via
GAP_ADR_001.

## Handoff

II.6 is CLOSED. Consumer blocs may now rely on the frozen observability
substrate (`app/forge/observability/`): request correlation, structured
events, metrics, the audit trails, the usage ledger and the error contract.
The next Book II step under the frozen order is the **cross-bloc adversarial
integration suite**, which is a separate authorization.
