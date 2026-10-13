# BOOK II — RATIFICATION EVIDENCE (Phases 0, 1, 5)

Status: CANONICAL (Book II ratification, Build Agent #16)
Date: 2026-10-12
Branch: `forge` · Authorized starting SHA:
`b44857ba800fcb7e76c2322345e1733703a92a3a`

## 1. Phase 0 — final precondition check (all executed at this head)

| # | Precondition | Method | Result |
|---|---|---|---|
| 1 | Exact starting SHA + clean remote-tracked tree | `git rev-parse HEAD origin/forge` after fetch; `git status --porcelain` | both `b44857ba…92a3a`; 0 tracked changes (only untracked scratch `.bu_tmp/`, never committed) |
| 2 | Planning-freeze ancestry + 23 pinned files | `git merge-base --is-ancestor 60e0675 HEAD`; `git show <pin>:<path>` vs worktree, EOL-normalized (same reading as all prior packets) | ancestor YES; **23/23 identical, 0 problems** |
| 3 | Six Bloc ratifications CLOSED — PASS on ancestry | ancestry check + each `RATIFICATION.md` read | II.1 `598b34c`, II.2 `438a35e`, II.3 `ea1ca46`, II.4 `ebda556`, II.5 `1496c16`, II.6 `fec9be0` — all ancestors; all six **CLOSED — PASS** |
| 4 | Cross-bloc adversarial PASS | `../cross_bloc/VERIFICATION.md` §5 | **CROSS-BLOC VALIDATION — PASS** (no ratification commit, by design) |
| 5 | GAP-01/02/05 closure evidence | register rows re-read; closure packets + executed CI | GAP-01/02 closed by executed repair (CI 38188302328, postgres 1002); GAP-05 closed by implemented+executed ledger (CI 38261712088, postgres 1045; BA-14 ladder 38255649571→38263395142 all green) |
| 6 | Consolidated pack + final re-audit | `../evidence_pack/` (7 deliverables), `../evidence_reaudit/RE_AUDIT.md` | present; re-audit verdict READY FOR RATIFICATION AUTHORIZATION |
| 7 | Exact final-head CI incl. executed PostgreSQL | `gh run list --branch forge`; `gh run view 38302099323 --json jobs`; log grep | run **38302099323** on `b44857b`: `test` ✅ **1016 passed / 29 skipped**; `postgres` ✅ **1045 passed / 0 skipped** (+19 PG-integration, +7 identity reruns); 0 failed steps |
| 8 | Complete 116-row matrix | programmatic recount | **116 rows = 106 D / 9 Q / 1 ND**, no duplicate IDs, zero drift |
| 9 | No B-class blockers | `OPEN_GAP_REGISTER.md` B-class scan | none; B-class list empty |
| 10 | Nine Q qualifications + G-F7 pending | non-D row extraction vs re-audit §2 table | 9 Q (G-P3, G-P4, CH-II.1.7, CH-II.3.2, CH-II.3.7, CH-II.4.3, CH-II.4.6, CH-II.4.9, C-C10) + G-F7 **ND** pending by design |

All ten preconditions passed at execution time; no stop condition triggered.

## 2. Phase 2 — sources read for packet construction (never modified)

Frozen: `planning/forge/books/BOOK_II_FORGE_CORE_PLATFORM_PLAN_V1.md`
(gate §"BOOK II ACCEPTANCE / RATIFICATION GATE"), `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md`,
`corpus/canonical/BOOKS_BLOCS_READINESS_GATE_V1.md`.
Evidence: `../evidence_pack/*` (all seven deliverables), `../evidence_reaudit/RE_AUDIT.md`,
`../closure_repair/{PLAN,ACCEPTANCE,EVIDENCE,GOVERNANCE}.md`,
`../closure_repair_gap05/{PLAN,ACCEPTANCE,EVIDENCE,VERIFICATION,G-P4_GAP-03_RECONCILIATION}.md`,
six `bloc_ii_*` packets, `../cross_bloc/*`. All SHAs cited in this packet
were validated (`git cat-file -e <sha>^{commit}`) or identified as GitHub
run IDs in the prior re-audit.

## 3. Phase 1 — D1–D5 consistency verification against frozen contracts

| # | Operator interpretation | Frozen anchor(s) read | Consistency |
|---|---|---|---|
| D1 | Book II freezes append-only audit infrastructure; no retention/compaction authorized; future changes need a governed packet | Plan Ch II.2.6 ("Append-oriented records…"); 004 table is append-only; re-audit §4.4 records retention as not-implemented/not-required-for-freeze | **Consistent** — no frozen clause requires retention; freeze + governed-packet rule matches audit §12 change control |
| D2 | Production security-critical audit ops must use `require_durable`; dev default is not a production certification | `audit_ledger.py` (both policies, typed `DurableAuditWriteError`); `config.py` validation; re-audit §4.1 | **Consistent** — the two-policy split exists exactly as described; nothing in frozen text certifies the default for production |
| D3 | Apply and verify migration 004 before enabling durable persistence; no automatic startup migration | `app/main.py` `_build_audit_persistence` docstring ("never as a side effect of import/startup. The operator applies migration 004 explicitly"); frozen `test_migration_runner_import_runs_nothing` | **Consistent** — matches the implemented dependency ordering exactly |
| D4 | Unwired container persistence seam is a Book II contract boundary; later composition needs its own authorization | `container.py` (unwired → NOT_CONFIGURED, never claimed healthy; frozen test pins `persistence is None`); `app/main.py` ("a separate, operator-scoped decision"); re-audit D4 | **Consistent** — the seam is deliberately unwired and honestly disclosed; re-audit already classified wiring as deployment-scoped |
| D5 | Book II satisfies its G-P4 portion via session revocation, fail-closed authorization, durable revocation/audit infra; G-P4 stays Q; GAP-03 stays Book VI; no Book VI entitlement/grace/subscription claim | Gate bullet "entitlement revocation observed promptly"; matrix G-P4 = Q (row untouched); register GAP-03 = D; `G-P4_GAP-03_RECONCILIATION.md` §3; GOVERNANCE §2; frozen `test_no_entitlement_state_machine_exists` | **Consistent** — exactly the frozen checklist's expected ratification act; no promotion, no reclassification, no Book VI claim |

**No interpretation conflicts with frozen language.** No stop condition.

## 4. Phase 2/3 — packet deliverables

- `RATIFICATION.md` — verdict, Phase 0 table, D1–D5 verbatim, G-P4
  confirmation, qualified-row acceptance, G-F7 statement, non-statements.
- `CONTRACT_FREEZE_MANIFEST_V1.md` — 8 surfaces, 50 files (45 application
  across surfaces 1–7 + 5 cross-bloc invariant files in surface 8), each
  with SHA-256 computed at the frozen head; migration head 4; policy hash
  `f10751e6…228fcc` (matches the frozen executable pin); change-control
  rules; Book I and planning freezes preserved.
- `ACCEPTANCE_COMPLETION.md` — demonstrated / qualified / governance
  separation; baseline not rewritten.
- `EVIDENCE.md` — this file.

## 5. Phase 5 — final verification battery (this head, local)

| Suite group | Command | Result |
|---|---|---|
| Six Book II focused suites | `pytest tests/test_forge_{service_composition,persistence,identity,policy,providers,observability}.py -q` | **422 passed** (36/56/66/86/74/104 — frozen counts) |
| Cross-bloc adversarial | `pytest tests/test_forge_cross_bloc.py -q` | **56 passed** |
| Book I canonical/retrieval/QA/backfill/provenance | `pytest tests/test_forge_{canonical,backfill,backfill_more,qa,retrieval,schemas,provenance,corpus_qa}.py -q` | **420 passed** |
| Signal Guard | `pytest tests/test_{ghost_signal,duplicate_signal,flip_logic,vision_confirm,vision_mcp,state_engine}.py -q` | **48 passed** |
| Vector + backup/restore + durable audit | `pytest tests/test_forge_{vector_projection,backup_restore,audit_ledger}.py -q` | **70 passed, 10 skipped** (all `FORGE_TEST_DATABASE_URL`-gated; executed in CI postgres job) |
| Full regression | `python -m pytest tests/ -q` | **1016 passed, 29 skipped, 0 failed** (exit 0) |
| Compile | `python -m compileall app -q` | clean |
| Migration head | `discover_migrations()` | `[1, 2, 3, 4]` |
| PostgreSQL CI (exact pre-ratification head) | `gh run view 38302099323` (live re-query) | `test` ✅ 1016/29; `postgres` ✅ **1045/0** |

**Baseline deviations: none.** Local 1016/29 and PG CI 1045/0 match the
expected pre-ratification baseline exactly. Skip accounting: 19 PG
integration + 7 pgvector + 1 backup smoke + 2 audit-ledger PG proofs = 29,
each `FORGE_TEST_DATABASE_URL`-gated with an explicit skip reason;
1016 + 29 = 1045.

## 6. Frozen-file integrity + append-only ancestry (re-verified)

- Planning freeze: 23/23 pinned files identical; `60e0675` ancestor.
- All seven historical ladders (six blocs + cross-bloc) remain on
  ancestry; no amend/squash/rebase/force-push exists on `forge`
  (`git log --oneline` linear through `b44857b`).
- The ratification ladder below is appended fast-forward only.

## 7. Ratification commit ladder (append-only; filled across rungs)

| Rung | Commit | Content | CI |
|---|---|---|---|
| 1 | **`e45d23371b14cca6b6dc1085dc56d8b9f2fe03aa`** (**is G-F7**) | `RATIFICATION.md`, `CONTRACT_FREEZE_MANIFEST_V1.md`, `ACCEPTANCE_COMPLETION.md`, `EVIDENCE.md` | run **38329326792** on `e45d233` — `test` ✅ success, `postgres` ✅ success (0 failed steps) |
| 2 | _recorded after final push below_ | this §7 filled in; final-head verification | _recorded after final push below_ |

Post-push verification of rung 1: `git push origin forge` was a fast-forward
(`b44857b..e45d233`, no force); `origin/forge` == `e45d233`; CI run 38329326792
queried live — both jobs success. G-F7 is satisfied by this ladder. The
frozen implementation head `b44857ba` (the pre-ratification tree) is the
head at which every hash in `CONTRACT_FREEZE_MANIFEST_V1.md` was computed;
rungs 1–2 add documentation only under `implementation/forge/book_ii/ratification/`
and touch no frozen surface (re-checkable by re-running the manifest
hashes — they still match at the final head).
