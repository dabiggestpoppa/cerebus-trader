# G-P4 / GAP-03 Reconciliation — against the frozen sources (Build Agent #14)

Purpose: reconcile gate bullet **G-P4** and **GAP-03** with the frozen record
AFTER the GAP-05 durable-audit implementation, state exactly what this packet
changed for them, and list every operator decision still required. This
document does not reclassify G-P4 or GAP-03, does not ratify Book II, and
does not modify any frozen planning file.

## 1. The frozen sources (verbatim anchors)

| Source | Text (as frozen) | State |
|---|---|---|
| `planning/forge/books/BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md` (gate list) | "**entitlement revocation observed promptly**" — a Book II gate bullet (G-P4) | — |
| `implementation/forge/book_ii/evidence_pack/ACCEPTANCE_MATRIX.md` row **G-P4** | Owner "II.4 (state: Book VI)"; evidence: capability exact-match deny tests (S4 E/O), session revocation immediacy (S3, XB F8), revoke event vocabulary (S6 `TestEntitlementAudit`); **Disp. = Q**; qualification: "No entitlement state exists in Book II; promptness proven at seam + session level → GAP-03 (downstream)" | **Q** (unchanged by this packet) |
| `implementation/forge/book_ii/evidence_pack/OPEN_GAP_REGISTER.md` row **GAP-03** | "Entitlement production and resolver rules do not exist (expiration/grace/revocation resolution, capability catalog C10 definition)… Classification **D**… What would close it: **Book VI implementation; at ratification, operator confirms seam-level demonstration satisfies G-P4 within frozen Book II ownership (not a Book II code change)**." | **D** (unchanged by this packet) |
| `implementation/forge/book_ii/evidence_pack/RATIFICATION_CHECKLIST.md` (pre-conditions) | "[ ] G-P4 reading confirmed by operator (seam-level demonstration accepted as satisfying 'entitlement revocation observed promptly' within frozen Book II ownership) — GAP-03." | open (operator action) |
| `implementation/forge/book_ii/closure_repair/GOVERNANCE.md` §2 | "Book VI owns commercial entitlement decisions and their business meaning… Book II must not create an alternative licensing or evidence authority." | recorded interpretation |

Note on an early draft of this packet's PLAN: it paraphrased G-P4 as
"external token revocation observed promptly vs recorded-before-read
(Spec §8)". That phrasing does not appear in the frozen sources; the anchors
above are authoritative and this reconciliation uses them exclusively (the
PLAN's rung-2 amendment appendix records the correction trail).

## 2. What the GAP-05 ledger changes for G-P4 / GAP-03

**Strengthened (seam evidence gains durability — still Book II ownership):**

1. **Revocation events are now durable, ordered and restart-surviving.**
   - Session revocation/administrative revocation facts: `session_revoked`,
     `sessions_revoked_all` via the vocabulary-validated
     `record_authentication_event` → `forge_audit_events`
     (`security_audit` stream), monotonic `seq`, idempotent `event_id`
     (`tests/test_forge_audit_ledger.py::test_authentication_events_all_vocabulary_members`).
   - Entitlement `revoke` (and grant/renew/grace/expire/admin_correction)
     records: `record_entitlement_event` mirror → `entitlement_audit` stream
     rows — RECORD ONLY (II.6 RAT 4; no entitlement state exists or is
     created).
   - **Recorded-before-read** is now an executed property: an appended fact
     is immediately readable back, and survives process restart
     (`TestRestartRecovery`), so "observed promptly vs merely noted in
     memory" has a durable, ordered substrate instead of a bounded RAM trail.
2. **Promptness stays where the frozen row puts it:** session revocation
   immediacy remains proven by S3/XB F8 (in-process, state-level); the ledger
   adds durability for the RECORD, not a new promptness claim.

**Explicitly NOT changed (separation preserved):**

- G-P4 stays **Q** — no entitlement state, resolver or revocation-resolution
  semantics were added (Book VI). The matrix row is untouched.
- GAP-03 stays **D / Book VI** — this packet does not implement entitlement
  production, resolver rules or the C10 capability catalog, and its
  classification/evidence cells in the register are not edited by this
  reconciliation.
- No Book II code now makes any entitlement decision; the ledger stores
  content-minimized records other modules decided (GOVERNANCE §2 honored:
  no alternative licensing or evidence authority).

## 3. Operator decisions still required (none taken here)

1. **G-P4 confirmation at ratification** (frozen checklist item): the
   operator must still confirm that the seam-level demonstration (now with
   durable revocation/event records backing it) satisfies "entitlement
   revocation observed promptly" within frozen Book II ownership. This
   packet executes evidence; the confirmation remains an explicit ratify-time
   operator act — and ratification itself is not authorized by this packet.
2. **Ledger retention/compaction policy:** `forge_audit_events` is
   append-oriented with no retention job; adding one (and its bounds) needs
   its own authorized packet. Appends never rewrite history regardless.
3. **Production write policy:** `best_effort` (default; faults contained as
   markers + `NOT_OK`) vs `require_durable` (typed failure propagates).
   Promotion to `require_durable` in a deployment is an operator config
   decision (`FORGE_AUDIT_DURABLE_WRITE_POLICY`).
4. **Migration-before-enable procedure:** operator applies migration 004
   before setting `FORGE_AUDIT_DURABLE_ENABLED=1` (migrations never run as a
   startup/import side effect by frozen rule).
5. **Container-level persistence/readiness wiring:** the frozen seam
   (`_build_forge_container().persistence is None`) is preserved; whether and
   when whole-app persistence + lifecycle migration-status checks are wired
   is a separate operator-scoped decision.

## 4. Verdict

G-P4 (**Q**) and GAP-03 (**D**, Book VI) are reconciled against the frozen
sources with **no reclassification**: the GAP-05 packet closes GAP-05 only.
It measurably strengthens the G-P4 seam evidence (durable, ordered,
redacted, restart-surviving revocation/audit records; executed failure and
recovery matrix) while leaving every Book VI-owned obligation and every
operator confirmation explicitly open, as recorded above.
