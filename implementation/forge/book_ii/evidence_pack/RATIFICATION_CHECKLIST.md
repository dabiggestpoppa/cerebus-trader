# BOOK II — PROPOSED BOOK-LEVEL RATIFICATION CHECKLIST

Status: **PROPOSAL ONLY** — this document is a checklist for a future
authorized ratification step (frozen order step 9). It is NOT a ratification,
NOT a freeze, and carries NO PASS decision. No signature, no commit-of-record
and no contract freeze is created by this file.

Evidence head when drafted: `ae35276`.

## Pre-conditions (must hold at the time of ratification)

- [ ] Evidence head is `origin/forge`, working tree clean, planning freeze
      head `60e0675` an ancestor (verified for this pack; re-verify at
      ratification).
- [ ] All 23 manifest-pinned frozen files byte-identical to their pinned
      commits (verified for this pack; re-verify at ratification).
- [ ] Six Bloc RATIFICATIONs present, CLOSED — PASS, on ancestry:
      II.1 `598b34c`, II.2 `438a35e`, II.3 `ea1ca46`, II.4 `ebda556`,
      II.5 `1496c16`, II.6 `fec9be0`.
- [ ] Cross-bloc packet complete with PASS VERIFICATION
      (`cross_bloc/VERIFICATION.md`) — no ratification commit, by design.
- [ ] CI both jobs green on the exact ratification SHA
      (pattern: L-12 on `ae35276`; re-run required if HEAD moves).
- [ ] PostgreSQL executed with recorded counts on or immediately before the
      ratification SHA (ledger rows; never a skipped-claimed run).

## Gate completeness (from ACCEPTANCE_MATRIX.md §A)

- [ ] **G-D1 / G-D4 / G-P3-vector (GAP-01) closed** — embedding storage +
      independent vector-projection rebuild + vector-leakage fail-closed
      test executed, **or** operator-approved plan amendment narrowing these
      bullets with recorded rationale (audit §12 change-control law).
- [ ] **G-D5 (GAP-02) closed** — backup→restore→verify smoke executed on
      live PostgreSQL and recorded, **or** explicit operator acceptance of
      the Ch II.2.9 mechanism/drill split as satisfying the bullet.
- [ ] **GAP-05 ruled** — operator decision recorded on durable audit/event
      ledger + Book-VI-owned persistence domains (implement at Book II vs
      defer with amendment).
- [ ] G-P4 reading confirmed by operator (seam-level demonstration accepted
      as satisfying “entitlement revocation observed promptly” within frozen
      Book II ownership) — GAP-03.
- [ ] All remaining gate rows still D at the ratification head (no regression
      since `ae35276`).

## Evidence-pack completeness (gate §Evidence pack)

- [x] PLAN.md / ACCEPTANCE.md / ladder / test output / EVIDENCE.md /
      unresolved-issue list / ratification record for each of the six Blocs.
- [x] Cross-bloc PLAN / ACCEPTANCE / ladder / EVIDENCE / VERIFICATION.
- [x] Consolidated acceptance matrix (`ACCEPTANCE_MATRIX.md`).
- [x] Consolidated evidence summary (`EVIDENCE_SUMMARY.md`).
- [x] Cross-bloc proof index (`CROSS_BLOC_PROOF_INDEX.md`).
- [x] CI/PostgreSQL verification ledger (`CI_POSTGRESQL_LEDGER.md`).
- [x] Open-gap register (`OPEN_GAP_REGISTER.md`).
- [x] Contract-freeze readiness assessment (`CONTRACT_FREEZE_READINESS.md`).
- [ ] Final Book II evidence records G-F7: **Book II ratification commit**
      (created only by the authorized ratification step).

## Book-level evidence records to embed at ratification (G-F1…G-F7)

- Schema/domain version: `FORGE_DOMAIN_V1`; event schema `FORGE_EVENT_V1`.
- Migration head: `001_initial_schema.sql`, `002_identity_session.sql`
  (head **2**), compatibility `OK` under
  `FORGE_MIGRATION_COMPATIBILITY_REQUIRED=1`.
- Test counts: capture at the ratification head (last recorded: 946
  passed/19 skipped local; 965/0 PostgreSQL-attached).
- Provider contract versions: `ProviderContractSpec` (8 elements) ×
  {llm, commerce, notification, storage}, implementations `fake` only.
- Policy version/hash: `POLICY_MODULE_SHA256 =
  f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`
  (asserted green by `test_forge_retrieval.py:1585`).
- Known exclusions: `EVIDENCE_SUMMARY.md` §6 + Book II plan exclusions.
- Ratification commit: pending (G-F7).

## Freeze semantics to confirm before freezing contracts

- [ ] What exactly freezes: the six Bloc contract surfaces
      (`app/forge/service/*`, `app/forge/persistence/*` port + migrations,
      `app/forge/identity.py` + `service/authentication.py`, `app/forge/policy.py`,
      `app/forge/providers/*`, `app/forge/observability/*`) at the
      ratification SHA.
- [ ] Change-control after freeze: audit §12 — later changes need GAP/ADR +
      plan versioning, never silent edits.
- [ ] GAP_ADR_001 disposition recorded (may remain OPEN with an explicit
      operator note; it must not be closed implicitly by ratification).
- [ ] Downstream consumers notified of exactly what Books III/IV/VI may
      assume (Book II plan `# HANDOFF TO BOOK III / VI`).

## Explicit non-statements for the ratification record

- Ratification ≠ production readiness (Book VIII owns launch security,
  performance, legal and GO/NO-GO).
- Ratification ≠ provider validation (no concrete adapters exist yet).
- Ratification ≠ Book III/IV/VI/VII/VIII authorization.
