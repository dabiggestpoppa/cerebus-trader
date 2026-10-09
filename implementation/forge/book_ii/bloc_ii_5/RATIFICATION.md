# BOOK II / BLOC II.5 — PROVIDER PORTS & ADAPTER BOUNDARIES — RATIFICATION.md

## RATIFICATION

Ratified: 2026-10-09
Ladder (append-only from the accepted start SHA `218c521`): `218c521` →
`a6bdc9f` (plan + acceptance + GAP/ADR) → `eb6a7b8` (provider ports) →
`11aa9cf` (composition seam + legacy supersessions) → `7c52ff1` (tests) →
`90ede0f` (export fix) → `e02b4db` (evidence) → this ratification commit.

**Verdict: PASS — CLOSED**

## Explicit ratification statements

1. **Frozen specification met.** Book II plan Ch II.5.1–II.5.10 is implemented
   in full: executable 8-element contract specs for all four ports, the exact
   frozen eight-class failure taxonomy with caller-owned retry semantics, the
   LLM/commerce/notification/storage ports with their frozen method sets, the
   config-driven registry/factory at the composition root, per-port explicit
   fallback policy with structural never-fabricate semantics, deterministic
   fakes covering all nine Ch II.5.9 scenarios on a simulated clock, and the
   shared Ch II.5.10 contract harness run identically across implementations.
2. **The five verbatim Acceptance II.5 clauses are proven executable**
   (EVIDENCE §5): core application passes on fakes only; no provider
   identifier is required as core domain PK; commerce outage cannot grant
   access; LLM outage cannot corrupt canonical state; adapter replacement is a
   composition/config change, never a domain rewrite.
3. **All ACCEPTANCE A–K clauses verified** — 74 focused tests, 216
   supersession-suite tests, 786-test full regression green locally
   (EVIDENCE §3); review clauses recorded in EVIDENCE §6/§8.
4. **Seam ownership is honest.** `container.providers` accepts only a frozen
   `ProviderRegistry` (the II.1 RuntimeError guard superseded fail-closed as a
   TypeError, exactly as II.2/II.4 superseded theirs); readiness discloses all
   four ports with live health, `required=False`, never blocking, never
   claiming vendor adapters (`openrouter`/`whop` stay `NOT_CONFIGURED`);
   credential presence is carried unread and never leaks to repr, diagnostics
   or logs.
5. **No scope creep.** No vendor adapter, network call, credential use,
   migration, observability, entitlement, prompt-intelligence, or market-data
   code exists in this bloc (EVIDENCE §8 exclusion review, AST-enforced where
   testable). Nothing of II.6 or later was implemented.
6. **Predecessor authority untouched.** All nine ratification heads verified
   ancestors of the start SHA; no frozen planning, canonical, or prior-bloc
   artifact was modified; ladder append-only, no amend/squash.
7. **Deviations and limitations are on the record, not hidden**: staging
   placement notes, the extra export-fix rung, count deltas vs PLAN §10, the
   test-local nature of the alternate adapters, and the 19 CI-only PostgreSQL
   tests (EVIDENCE §7/§9).
8. **GAP_ADR_001 (phase grouping vs dependency law) is recorded OPEN** and is
   not resolved by this ratification; it requires operator/CC decision before
   Phase C start and does not affect II.5's dependency legality.

## Limitations carried forward

- PostgreSQL integration executes in CI only (19 local skips) — same standing
  limitation as I.5/II.4; CI evidence lands in the verification-record rung.
- Concrete adapters (OpenRouter → Book IV, Whop → Book VI) and their real
  contract-matrix runs remain future-bloc work by design.

## Handoff

II.5 is CLOSED. The next dependency-ready Book II bloc is **II.6
(Observability, Auditability & Error Contract)** under the Book II topological
order; the Phase C gate question stays with the operator via GAP_ADR_001.
Consumer blocs (Book IV LLM wiring, Book VI commerce/entitlement, Book III's
declared provider-port input) may now bind against the frozen ports in
`app/forge/providers/`.
