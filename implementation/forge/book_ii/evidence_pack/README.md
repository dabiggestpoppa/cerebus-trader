# BOOK II — CONSOLIDATED EVIDENCE PACK (Step 8 of the frozen Book II order)

Status: EVIDENCE PACK — PREPARED FOR OPERATOR REVIEW
Date: 2026-10-11
Evidence head: `ae352762a0ef6b9a277b3e112e8826cd8feb96f1` (= `origin/forge` at pack time, verified)
Closure-repair update (2026-10-12): `origin/forge` advanced through the
authorized closure-repair ladder (GAP-01/02/05, GAP_ADR_001) — rows updated
below cite their own heads/runs; see `../closure_repair/EVIDENCE.md` §1.
Planning freeze head: `60e067547b9d9165d94e4f074e0db0ba58e59e24` (ancestor, verified)

**This packet does NOT ratify or freeze Book II, does NOT authorize Book III,
and issues no Book-level PASS document.** It consolidates committed evidence
and states contract-freeze readiness honestly. `GAP_ADR_001` remains OPEN.

## Scope authorization

Build Agent #12 — Book II Consolidated Evidence Pack & Contract-Freeze
Readiness (step 8). Steps 9 (ratify/freeze Book II) and all Book III work
remain unauthorised.

## Contents (the seven required deliverables)

| # | Deliverable | File |
|---|---|---|
| 1 | Book II consolidated acceptance matrix | `ACCEPTANCE_MATRIX.md` |
| 2 | Book II evidence summary (six blocs reconciled) | `EVIDENCE_SUMMARY.md` |
| 3 | Cross-bloc proof index (X1–X9, F1–F12, laws) | `CROSS_BLOC_PROOF_INDEX.md` |
| 4 | CI / PostgreSQL verification ledger | `CI_POSTGRESQL_LEDGER.md` |
| 5 | Open-gap register (classified) | `OPEN_GAP_REGISTER.md` |
| 6 | Contract-freeze readiness assessment | `CONTRACT_FREEZE_READINESS.md` |
| 7 | Proposed Book-level ratification checklist | `RATIFICATION_CHECKLIST.md` |

## Naming / structure provenance

Follows the established `implementation/forge/book_ii/` convention: packet
directories (`bloc_ii_1` … `bloc_ii_6`, `cross_bloc`) hold plain uppercase
section files; Book-level artifacts elsewhere use the `_V1` suffix
(`BOOK_I_FREEZE_MANIFEST_V1.md`, `COVERAGE_REPORT_V1.md`). This packet is a
directory packet like `cross_bloc/`, because it holds seven distinct
deliverables.

## Frozen sources read (never modified)

- `planning/forge/GLX_FORGE_MASTER_BUILD_PLAN_V1.md` (pinned `945b8c3`)
- `planning/forge/books/BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md` (pinned `22c6711`)
- `planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` (pinned `2719357`)
- `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md`
- `corpus/canonical/BOOKS_BLOCS_READINESS_GATE_V1.md` (pinned `7cab91d`)

All 23 manifest-pinned frozen files verified byte-identical to their pinned
freeze commits at the evidence head (Phase 8 validation, recorded in
`CONTRACT_FREEZE_READINESS.md` §9).

## Verdict headline

**BOOK II RATIFICATION BLOCKED — REPAIR REQUIRED**

Basis updated 2026-10-12 after the Book II closure-repair packet
(`implementation/forge/book_ii/closure_repair/`): **GAP-01 and GAP-02 are
CLOSED by executed repair** (CI run 38188302328 on `914cc04`, postgres job
1002 passed — vector substrate + backup/restore smoke) and **GAP_ADR_001 is
DISPOSED** (interpretation recorded, frozen plans unchanged). The remaining
ratification blocker is **GAP-05**: its ownership was RULED (Book II owns
durable operational/security audit infrastructure) and the durable
audit/event ledger is still unimplemented. The repaired pack now awaits
**evidence re-audit** before any readiness verdict can change — see
`CONTRACT_FREEZE_READINESS.md` §10 and `OPEN_GAP_REGISTER.md`.

## Phase 8 validation record (executed at `ae35276`, this packet)

| Check | Method | Result |
|---|---|---|
| Evidence head | `git rev-parse HEAD origin/forge` | both `ae352762a0ef6b9a277b3e112e8826cd8feb96f1`; tracked tree clean before this packet |
| Planning-freeze ancestry | `git merge-base --is-ancestor 60e0675 HEAD` | freeze head is an ancestor |
| Frozen-file integrity | `git show <pinned-commit>:<path>` vs worktree for all 23 manifest-pinned files | 23/23 content-identical (raw bytes differ only by `core.autocrlf=true` CRLF worktree normalization; identical after EOL normalization) |
| Bloc/cross-bloc ancestry | `merge-base --is-ancestor` for `598b34c 438a35e ea1ca46 ebda556 1496c16 fec9be0 cfd69d0 5c58414` | all ancestors of HEAD |
| Acceptance-reference integrity | every full-path reference in all seven files resolved on disk | no unresolved references |
| Commit-SHA references | `git cat-file -e <sha>^{commit}` for every backticked SHA | all valid (the only non-matches were GitHub Actions run IDs, verified separately) |
| CI run provenance | live `gh run list --branch forge` re-query | every run ID in `CI_POSTGRESQL_LEDGER.md` present with the recorded head SHA and conclusion (incl. failures `37989879501`/`37991271771` preserved as FAIL(infra)) |
| Test-name existence | backticked `test_*` names vs `pytest --collect-only -q` (965 collected) | all 66 cited test names exist |
| Matrix totals | programmatic recount of disposition cells per section | 116 rows = 41 A + 56 B + 19 C; **99 D / 14 Q / 3 ND** at `ae35276` — matched the Totals line then; recounted to **105 D / 10 Q / 1 ND** after the closure-repair update (G-D1/G-D4/G-D5/CH-II.2.4/CH-II.2.9/C-DEF5 moved on executed CI evidence) |
| Gap-register consistency | `GAP-01..14` + `GAP_ADR_001` cross-reference scan across all files | 15 defined, 0 used-but-undefined, 0 defined-but-unused (re-run after the closure-repair reclassifications: still 15, 0/0) |
| Unsupported-PASS scan | `\bPASS\b` scan of all seven files | only per-CI-run classifications and bloc-as-committed verdicts (sourced); no Book-level PASS assertion |
| Full regression | `python -m pytest tests/ -q` | **946 passed, 19 skipped** in 12.23s (matches CI `test` job at the evidence head; 19 = CI-only PostgreSQL tests, see ledger L-13 for executed-PG evidence) |
| Closure-repair validation (2026-10-12) | same battery re-run after `implementation/forge/book_ii/closure_repair/` + this update | local **975 passed, 27 skipped**; CI `test` 975/27; CI `postgres` **1002 passed, 0 skipped** (L-17); matrix recount 116 = 105/10/1; register 15 IDs 0/0 orphans; no unsupported Book-level PASS introduced |

At the time of the Phase 8 record above, no application logic was modified.
The later closure-repair packet changed `app/forge/persistence/*` and the CI
service image under its own explicit operator authorization (GAP-01/GAP-02);
that change history is append-only in `closure_repair/EVIDENCE.md` §1.
