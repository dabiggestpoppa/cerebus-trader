# BOOK II — POST-RATIFICATION ACCEPTANCE DISPOSITION (Phase 4)

Status: CANONICAL (Book II ratification, Build Agent #16)
Date: 2026-10-12
Ratification record: `RATIFICATION.md`
Acceptance baseline: `../evidence_pack/ACCEPTANCE_MATRIX.md` — **116 rows,
106 D / 9 Q / 1 ND**, frozen as written and **not rewritten** by this act.

This disposition separates what the ratification establishes into the
three required classes. It does not edit the historical matrix, any Bloc
packet, the cross-bloc packet, either closure-repair packet or the re-audit
packet — all remain byte-identical as committed.

## 1. Demonstrated implementation (frozen, executable)

The 106 D rows of the acceptance matrix, each backed by executed tests at
the frozen implementation head `b44857ba`:

- **Service lifecycle** — intentional composition, typed config,
  liveness/readiness/meta, safe error envelope, explicit lifecycle,
  container seam (`test_forge_service_composition.py`, 36).
- **Persistence** — port/injection, canonical storage, integrity kernel,
  optimistic concurrency, atomic transactions, migrations 001–004
  (`test_forge_persistence.py` 56 + 19 PG integration).
- **Identity/session** — digest-only tokens, expiry vs injected clock,
  revocation (single + all), link collision rejection, roles as data
  (`test_forge_identity.py`, 66).
- **Policy/exposure** — central exposure matrix, exact-match capability
  atoms, deny-by-default, authorize-then-load enforcement, bounded policy
  audit (`test_forge_policy.py`, 86).
- **Provider ports** — 4 ports × 8-element specs, 8-class failures,
  registry/factory, per-port fallback modes, 9 scripted fakes on a
  simulated clock (`test_forge_providers.py`, 74 + contract harness).
- **Observability** — correlation, frozen events/metrics, four audit
  streams, 9-class error taxonomy, usage ledger
  (`test_forge_observability.py`, 104).
- **Closure-repair families** — vector projection (003, pgvector,
  deterministic rebuild, deny ≡ missing leakage proofs), backup/restore
  smoke on live PostgreSQL, durable audit/event ledger (004 +
  `DurableAuditLedger`, redaction-before-storage, idempotency, restart
  survival, `best_effort`/`require_durable` behavior)
  (`test_forge_vector_projection.py`, `test_forge_backup_restore.py`,
  `test_forge_audit_ledger.py`).
- **Cross-bloc invariants** — X1–X9 / F1–F12 and the executable laws
  (`test_forge_cross_bloc.py`, 56).

Counts at ratification: local **1016 passed / 29 skipped**; PostgreSQL CI
**1045 passed / 0 skipped** (run 38302099323 on `b44857b`; skips are
exclusively the `FORGE_TEST_DATABASE_URL`-gated tests, executed in the
postgres job — 1016 + 29 = 1045, arithmetic exact).

## 2. Qualified downstream obligations (9 Q rows — accepted, not promoted)

Each remains **Q** in the frozen matrix; each has executed seam-level
evidence and a frozen downstream owner (derivations:
`../evidence_reaudit/RE_AUDIT.md` §2):

| Row | Book II demonstrates | Downstream owner |
|---|---|---|
| G-P3 | direct-ID / vector / alias / historical fail-closed proofs | GAP-07 (optional adversarial extras) |
| G-P4 | session revocation, fail-closed deny, durable revocation/audit records (D5 confirmation recorded) | GAP-03 — Book VI entitlement state |
| CH-II.1.7 | all five "Acceptance II.1" bullets | GAP-04 — optional one-command harness |
| CH-II.3.2 | user lifecycle + preserved domain seam | Book VI org/account model |
| CH-II.3.7 | `SERVICE` role exists + tested | GAP-13 — Book VI job/callback consumers |
| CH-II.4.3 | consumption seam + deny rules; no entitlement state machine exists | GAP-03 — Book VI resolver rules |
| CH-II.4.6 | depth never bypasses object exposure | Book IV consumer depth routing |
| CH-II.4.9 | `PolicyDecision.detail` + reason codes + audit | GAP-12 — later admin tooling |
| C-C10 | exact capability-atom evaluation | GAP-03 — Book VI capability catalog |

No Q row hides an unmet frozen gate bullet. The B-class blocker list is
empty; GAP-03, GAP-06, GAP-10, GAP-11, GAP-13, GAP-14 and the Book-VI
business-table share of GAP-05 remain **D** (downstream), unchanged.

## 3. Completed governance/ratification output

- **G-F7** — Book II ratification commit: satisfied by rung 1 of this
  packet's ladder (exact SHA recorded append-only in `EVIDENCE.md` §7).
- **D1–D5** — operator decision record: recorded verbatim in
  `RATIFICATION.md`, consistency-verified against frozen sources
  (`EVIDENCE.md` §3).
- **G-P4 confirmation** — the frozen checklist pre-condition is
  discharged by the operator in `RATIFICATION.md` (D5).
- **Contract freeze** — `CONTRACT_FREEZE_MANIFEST_V1.md` freezes 50 files
  across the eight Book II contract surfaces at the frozen implementation
  head, with per-file SHA-256 and §12 change control.
- **Historical baseline preserved** — the 116-row matrix keeps G-F7 as
  **ND as written** ("does not exist" at pack time). The transition
  ND → satisfied-by-ratification is recorded here and in `RATIFICATION.md`
  §G-F7, never by rewriting the baseline row: the matrix documents what
  was demonstrated *before* the ratification act, and this file documents
  what the act itself completes.

## 4. G-F7 mechanics (why the baseline row is not rewritten)

G-F7 names a commit; a packet cannot contain its own commit SHA. The
established repository pattern (Book I I.5 ratification; every Book II
packet ladder) resolves this append-only: the ratification ladder's rung 1
commit **is** the ratification commit, and rung 2 records that SHA plus the
post-push CI verification in `EVIDENCE.md`. The frozen matrix row's text
("does not exist … by design, not a defect") remains historically accurate
for the head at which it was written; the post-ratification disposition
(this file) is the single authoritative statement of G-F7's completion.
