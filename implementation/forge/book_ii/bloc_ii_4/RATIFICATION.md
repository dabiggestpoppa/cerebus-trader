# Book II / Bloc II.4 — Policy & Access Control

## RATIFICATION

**Book II / Bloc II.4 — Policy & Access Control
CLOSED — PASS**

Ratified: 2026-10-07
Final local HEAD at ratification: `40cac47` (ladder from `cad9cd7`, append-only)

## Explicit ratification statements

1. **Authentication remains II.3.** All identity, session, token, revocation,
   disabled-user, and external-identity-link authority stays in
   `app/forge/identity.py` and `app/forge/service/authentication.py` (Bloc
   II.3). II.4 created no second authentication implementation; the policy
   kernel consumes an `II.3 ForgePrincipal` as given and never reconstructs
   identity from email, provider subjects, request headers, or raw request JSON.

2. **Commercial entitlement remains Book VI.** II.4 introduced no Plan,
   Subscription, Price, BillingStatus, License, or Whop domain object; no
   checkout/payment/billing state; no provider integration. The
   `AuthorizationContext` is a provider-neutral capability-fact seam that Book
   VI will later populate from commercial state. Capability atoms are permission
   facts, not product marketing names; no FREE/PRO/PREMIUM atoms exist.

3. **Policy consumes trusted authorization context.** The
   `AuthorizationContext` may be constructed only from trusted service input;
   no untrusted request field can grant capability; missing or malformed
   context fails closed (`MALFORMED_CONTEXT` / `ENTITLEMENT_MISSING`).

4. **Protected resource loading occurs only after ALLOW.** The enforcement
   service orders authorization before any loader invocation; DENY ⇒ loader
   never called, proven by spy-loader and the 100+ attempt adversarial
   extraction barrage across id/type/exposure/action variation.

5. **INTERNAL_METHOD / INTERNAL_CODE fail closed for ordinary customer
   contexts.** Anonymous, authenticated-no-capability, member, operator,
   research, any combination of ordinary capabilities, and admin atoms all DENY
   internal classes (explicitly and adversarially tested). Only the reserved
   `forge.internal` capability admits them; no staff-role mechanism was
   invented.

## Acceptance verification

All ACCEPTANCE.md clauses A–Z are satisfied and executable-proven by
`tests/test_forge_policy.py` (86 tests) plus the unchanged-baseline regression
gate: I.1 41, I.2 41, II.1 36, II.2 51, II.3 66, Signal Guard 48, full
repository **369 passed, 14 skipped** (baseline 283 + 86 new; skips are the
PG integration module only). No migration added (versions `[1, 2]`, 001
SHA-256 pin unchanged). No routes added or changed. Deterministic, pure,
stateless policy kernel. Security review (Phase 9) recorded in EVIDENCE.md §17
with no unresolved findings. Two append-only repairs recorded honestly
(EVIDENCE.md §18): kernel matrix fidelity (`d768d87`) and superseded II.2
guard test (`7b9e2df`).

## Handoffs

- **I.3 (Canonical Backfill):** authorized to proceed. Corpus surfaces must
  pass every canonical read through the enforcement boundary (policy before
  retrieval; exposure filtering before any LLM context). See EVIDENCE.md §21.
- **Book VI:** owns entitlement/capability production into the
  `AuthorizationContext` seam. See EVIDENCE.md §22.
