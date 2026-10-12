# BOOK II — FINAL EVIDENCE RE-AUDIT (Build Agent #15)

**Branch:** `forge` · **Start/final code head:** `1041787754e3aa1c9780f8e0947001f9e5c35c3b`
**Scope:** independent re-audit of the consolidated Book II evidence pack
after the GAP-05 durable audit-ledger repair. **This packet does NOT ratify
or freeze Book II and does NOT authorize Book III+** — ratification remains
the operator's separate act (frozen order step 9). Frozen planning
documents and the six ratified Bloc packets were read, never modified.

---

## 1. Phase 0 — repository truth (all verified at `1041787`)

| Check | Method | Result |
|---|---|---|
| HEAD == `origin/forge` | `git rev-parse HEAD origin/forge` after fetch | both `1041787754e3aa1c9780f8e0947001f9e5c35c3b` |
| Clean tracked tree | `git status --porcelain` | 0 tracked changes (only this packet's scratch) |
| Planning freeze ancestry | `git merge-base --is-ancestor 60e0675 origin/forge` | YES |
| 23 manifest-pinned frozen files | `git show <pinned>:<path>` vs worktree (byte compare, EOL-normalized — same reading as prior packets; checkout has `core.autocrlf=true`) | **23/23 identical**, 0 problems |
| Six Bloc ratifications on ancestry | `merge-base --is-ancestor` | II.1 `598b34c`, II.2 `438a35e`, II.3 `ea1ca46`, II.4 `ebda556`, II.5 `1496c16`, II.6 `fec9be0` — all YES; all six files read, each **CLOSED — PASS** |
| Cross-bloc validation | `../cross_bloc/VERIFICATION.md` §5 | **CROSS-BLOC VALIDATION — PASS** (no ratification commit, by design) |
| GAP-01 vector repair | `003_vector_projection.sql`, closure_repair EVIDENCE, CI 38188302328 | present, executed (postgres job 1002 at `914cc04`) |
| GAP-02 backup/restore repair | `tests/test_forge_backup_restore.py` smoke; CI | present, executed same run |
| GAP-05 durable audit ledger | migration 004 + `audit_ledger.py` + II.6 mirrors; CI 38261712088 | present, executed (postgres job **1045** at `3529a0d`) |
| CI on the exact final head | `gh run view 38263395142` | **both jobs success** on `1041787` (test 1016/29; postgres 1045/0 + reruns 19/7) |
| GAP-05 ladder CI provenance | `gh run view` for every rung | 38255649571 (`6d1de17`) ✅ · 38261712088 (`3529a0d`) ✅ · 38262811797 (`7ae6dba`) ✅ · 38263059238 (`0d9cd85`) ✅ · 38263395142 (`1041787`) ✅ |

## 2. Phase 1 — independent recount of the 116-row frozen matrix

Method: programmatic extraction of every requirement row
(`G-*`, `CH-II.*`, `C-*`) from `../evidence_pack/ACCEPTANCE_MATRIX.md` with
the disposition cell resolved per row; no row skipped, no duplicate IDs.

**Result: 116 rows = 41 Section A + 56 Section B + 19 Section C →
106 D / 9 Q / 1 ND — matches the reported baseline exactly.**

### The nine qualified rows and the one ND row (clause-by-clause)

| Row | Exact frozen source clause | Required for Book II ratification? | Delegated downstream? | Qualification supported by evidence? | Operator decision? | Blocks ratification? |
|---|---|---|---|---|---|---|
| **G-P3** | Gate §Policy: "direct-ID, alias, historical-version and vector leakage tests fail closed" | Yes (gate bullet) — vector sub-clause now **D** | Alias/historical bypass-adversarial tests optional (GAP-07, N) | Yes: direct-ID S4 Z1; vector `test_isolation_matrix_zero_leakage` + `TestPostgresVectorProjection::test_isolation_matrix_on_postgres` (deny ≡ missing); alias QA `test_b4_alias_expansion_never_rewrites_status_tokens` + retrieval `test_status_and_exposure_filters`; historical `test_generation_is_retained_from_the_source` / `test_ranking_never_changes_status_or_exposure`; uniform per-candidate authz (`test_authorization_precedes_content_access`) | No (accepted nonblocking limitation) | **No** |
| **G-P4** | Gate §Policy: "entitlement revocation observed promptly" | Yes (gate bullet) — see §3 | Entitlement *state* = Book VI (GAP-03, D) | Yes at seam+session level: S4 `test_capability_atoms_exact_match`, S3 revocation immediacy, XB F8, S6 `TestEntitlementAudit`; strengthened by durable revocation records (§4) | **Yes — D5, ratification-time confirmation** (frozen checklist item) | **No**, provided the confirmation is recorded at ratification |
| **G-F7** | Gate §Evidence pack: "Book II ratification commit" | It *is* the ratification output | n/a | Correctly ND: created only by the authorized ratification act; not a defect | n/a (ratification itself) | **No** — cannot block the decision to ratify |
| **CH-II.1.7** | Ch II.1.7: "One-command local stack using: Postgres + pgvector … deterministic seed corpus/account fixtures" | The five explicit "Acceptance II.1" bullets are the gate-relevant part — all demonstrated (S1/S2) | Harness itself optional (GAP-04, N) | Yes: compose file predates FORGE (`af45cc7`), contains no FORGE services — recorded honestly, never faked | No | **No** |
| **CH-II.3.2** | Ch II.3.2: "Separate person/user identity from account/license ownership where needed … Do not overbuild organization UX in Book II; preserve the domain seam" | The frozen clause itself limits Book II scope to the seam | Yes — org/institutional accounts, seats = Book VI (plan exclusions) | Yes: user lifecycle ACTIVE/DISABLED tested; seam preserved | No | **No** |
| **CH-II.3.7** | Ch II.3.7: "Background jobs/provider callbacks receive constrained service principals and scopes" | Primitive required; consumers do not exist at Book II | Yes — jobs/webhooks = Book VI (GAP-13, D) | Yes: `IdentityRole.SERVICE` exists + tested; no consumer exists to wire | No | **No** |
| **CH-II.4.3** | Ch II.4.3: "Resolve active capabilities from internal entitlement state. Rules: expiration respected, revocation wins, grace state explicit …" | Resolver *rules* need entitlement state Book II does not own | Yes — Book VI (GAP-03, D) | Yes: consumption seam (`AuthorizationContext`) + deny rules tested; no entitlement state machine exists (frozen XB `test_no_entitlement_state_machine_exists` green) | Shares D5 | **No** |
| **CH-II.4.6** | Ch II.4.6: "Beginner/Operator/Researcher are presentation/retrieval depths, not automatic trust tiers. Entitlement may grant a depth; depth cannot bypass object exposure" | The Book II half ("depth cannot bypass exposure") is demonstrated | Consumer depth routing = Book IV input | Yes: S4 role/depth assertions + QA depth routing prove depth never bypasses exposure | No | **No** |
| **CH-II.4.9** | Ch II.4.9: "Admin/test tooling can explain a decision without exposing secrets: principal class + capability + policy rule + result" | Mechanism required; admin surface does not exist at Book II | Admin tooling later (GAP-12, N) | Yes: `PolicyDecision.detail`/reason codes + audit records, machine-readable, tested (S4 S, XB A7) | No | **No** |
| **C-C10** | Master audit contract C10: "Definition/catalog: VI · Evaluation: II · Rendering: V" | Evaluation half demonstrated (S4 E, XB F1) | Yes — catalog = Book VI (GAP-03, D) | Yes: Book II evaluates exact capability atoms; no catalog exists to define | Shares D5 | **No** |

No Q/ND row hides an unmet frozen gate bullet. GAP-05 was the last B-class
blocker and is closed by executed evidence (§4); the B-class blocker list is
empty.

## 3. Phase 2 — G-P4 / GAP-03 (no silent promotion)

Frozen anchors read verbatim (plan gate line 828 "entitlement revocation
observed promptly"; Ch II.4.3 rules; handoff "Book VI may assume … policy
consumes internal capabilities"; audit contract C10 split; matrix G-P4 row =
**Q**; register GAP-03 = **D/Book VI**).

- **Book II persistence capability (what exists):** durable, ordered,
  idempotent, restart-surviving *records* of revocation and entitlement
  facts (`session_revoked`, `sessions_revoked_all` in `security_audit`;
  `entitlement.{grant,renew,grace,expire,revoke,admin_correction}` in
  `entitlement_audit`, RECORD-only), plus session-revocation immediacy at
  the state level and exact-match capability deny.
- **Book VI entitlement semantics (what does not exist):** entitlement
  state, expiration/grace *resolution*, revocation-wins resolution across a
  request, the C10 capability catalog. None may be invented in Book II
  (GOVERNANCE §2; frozen `test_no_entitlement_state_machine_exists`).
- **Recommendation (D5):** at ratification the operator records the
  checklist confirmation that the seam-level demonstration — now backed by
  the durable ledger — satisfies "entitlement revocation observed promptly"
  within frozen Book II ownership. G-P4 stays **Q** until that act; this
  re-audit does not promote it.

## 4. Phase 3 — durable audit-ledger acceptance (independently validated)

Beyond the committed suite, an **independent probe outside pytest**
(file-backed SQLite, own script) reproduced every acceptance property:

| Property | Independent observation |
|---|---|
| Migration 004 | `discover_migrations() == [1,2,3,4]`, identity `004_audit_ledger`, `postgresql_only=False` (portable); apply → `APPLIED`, compat `OK`, re-apply `CURRENT` |
| Six record classes durable | policy decisions, retrieval access, entitlement records, provider usage, authentication vocabulary (5 exact members), admin revocations — all wrote durable rows with expected streams (`security_audit`, `entitlement_audit`, `usage_ledger`) |
| Redaction before persistence | planted secret (`sk-…` + Bearer token) in details → **not present anywhere in the stored row** |
| Event idempotency | same `event_id` appended twice → `True, False`, exactly **1 row** on the real UNIQUE constraint |
| Record-before-read | appended fact immediately returned by `list_events()` |
| Restart recovery | dispose → reopen: all 7 rows survive, seq continues (`8`), seqs strictly monotonic + unique |
| `best_effort` failure markers | dropped table → append returns `False`, `status=NOT_OK`, `FallbackAuditMarker(stream, event_type, PERSISTENCE_UNAVAILABLE)` retained |
| `require_durable` failure | typed `DurableAuditWriteError(kind=PERSISTENCE_UNAVAILABLE)`; message contains **no** URL/DB/payload (redaction asserted) |
| Recovery | re-apply after fault → next append `True`, `status=OK` (recovery is observable) |
| Tenant/exposure boundary | audit rows are **not reachable over any HTTP route** (only `/health`, `/ready`, `/meta` exist; no durable-audit exposure); read-back is operator/test-facing only |
| No authority escalation | ledger records facts other modules decided; frozen guards green: no Book VI business table, streams ⊆ frozen `STREAMS`, auth vocabulary frozen, no entitlement state machine |
| Import-law violations | AST scan: observability imports persistence/provenance = **NONE**; persistence imports observability = **NONE** (the lone grep hit in `audit.py:11` is a docstring citation, not an import) |

Committed-suite confirmation: `tests/test_forge_audit_ledger.py` →
**41 passed, 2 skipped** (the 2 = PG-gated, executed in CI postgres job).

### Production-enforcement requirements to decide before freeze/deploy

1. Write-policy promotion (D2) — default `best_effort`; `require_durable`
   is an explicit production config decision.
2. Migration-before-enable (D3) — 004 must be applied before
   `FORGE_AUDIT_DURABLE_ENABLED=1`; until then appends degrade to bounded
   fallback markers (visible, never silent).
3. Serving-path audit wiring (D2 production half): at Book II no HTTP route
   invokes the `record_*` seams (Ask CEREBUS is Book IV); when Books IV/VI
   add serving paths, those paths must call the seams and security-critical
   classes should run `require_durable`. This is correctly a downstream
   obligation, recorded here so it is not lost.
4. Retention/compaction (D1) — not implemented, not required for freeze.

## 5. Phase 4 — operator decision register

| # | Decision | Recommendation | Contract-freeze necessity | Production-deployment necessity |
|---|---|---|---|---|
| **D1** | Retention/compaction on `forge_audit_events` | **No retention job at freeze.** Table is append-only; rows are content-minimized so unbounded growth is an operational, not privacy, concern. Any retention job = its own authorized packet under audit §12 change control (archive-then-delete; immutability of retained history never rewritten) | Record the stance in the ratification record; no code | Yes — schedule a retention packet before launch-scale volume (Book VIII horizon) |
| **D2** | Durable enforcement split | Default stays `best_effort` (telemetry serves; faults contained + `NOT_OK` visible). **Production obligation:** deployments handling real security events set `FORGE_AUDIT_DURABLE_WRITE_POLICY=require_durable` for the security-audit path; usage/telemetry mirrors may remain `best_effort`. Today the policy is ledger-global (one flag), so promoting = whole-ledger strictness; a per-stream policy would need its own authorized packet | Record the default + promotion rule; no code | **Yes** — promotion is an explicit deployment config act, made after D3 |
| **D3** | Migration activation | Dependency is enforced by design: migrations never run as a startup/import side effect (frozen rule; `test_migration_runner_import_runs_nothing`); enabling without 004 degrades to bounded fallback markers, never a crash, never silently in-memory. Operator runbook: apply 004 → `check_compatibility()==OK` → then set `FORGE_AUDIT_DURABLE_ENABLED=1` | Record the ordering rule in the ratification record | **Yes** — executed per deployment; acceptance evidence = `forge_schema_migrations` head `[1,2,3,4]` + compat `OK` + first durable append `True` |
| **D4** | Container persistence wiring | The unwired seam is a **deliberate Book II contract boundary**, not an unresolved readiness defect: frozen test pins `_build_forge_container().persistence is None`; the ledger builds its own gateway; whole-app persistence/lifecycle migration-status wiring is composition-root work owned by a deployment-scoped change | Record the ruling (boundary affirmed) | Wiring itself is deployment-scoped; no Book II code change |
| **D5** | G-P4 / GAP-03 disposition | Operator records the ratification-time confirmation (§3); G-P4 stays **Q**, GAP-03 stays **D/Book VI** until Book VI implements entitlement state | **Yes — required by the frozen checklist pre-condition** | No |

N-class limitations accepted as nonblocking (already classified in the
register): GAP-04 (harness), GAP-07 (bypass-adversarial tests), GAP-08
(Docker Hub rate limit), GAP-09 (deterministic concurrency interleave),
GAP-12 (admin explain tooling). Downstream D-class: GAP-03, GAP-06,
GAP-10, GAP-11, GAP-13, GAP-14 + the Book-VI business-table share of
GAP-05.

## 6. Phase 5 — end-to-end verification (this head)

| Suite group | Command | Result |
|---|---|---|
| Six Book II suites (S1–S6) | `pytest tests/test_forge_{service_composition,persistence,identity,policy,providers,observability}.py -q` | **422 passed** (matches frozen per-suite counts 36/56/66/86/74/104) |
| Cross-bloc adversarial | `pytest tests/test_forge_cross_bloc.py -q` | **56 passed** |
| Vector projection + backup smoke + audit ledger | `pytest tests/test_forge_{vector_projection,backup_restore,audit_ledger}.py -q` | **70 passed, 10 skipped** (all skips = `FORGE_TEST_DATABASE_URL`-gated, executed in CI postgres job) |
| Book I canonical/retrieval/QA/backfill/provenance | `pytest tests/test_forge_{canonical,backfill,backfill_more,qa,retrieval,schemas,provenance,corpus_qa}.py -q` | **420 passed** |
| Signal Guard (legacy suite) | `pytest tests/test_{ghost_signal,duplicate_signal,flip_logic,vision_confirm,vision_mcp,state_engine}.py -q` | **48 passed** |
| Policy-hash pin | `pytest -k "policy_module or hash"` | **4 passed** (`POLICY_MODULE_SHA256` green; policy byte-identical since I.4) |
| Durable audit ledger | `pytest tests/test_forge_audit_ledger.py -q` | **41 passed, 2 skipped** |
| Full regression | `python -m pytest -q` | **1016 passed, 29 skipped, 0 failed** (exit 0) |
| Compile | `python -m compileall app` | clean |
| CI on exact remote head | `gh run view 38263395142` (re-queried) | `test` ✅ **1016 passed, 29 skipped**; `postgres` ✅ **1045 passed, 0 skipped** (+ evidence reruns 19, 7) |

**Every count difference explained.** Local 1016/29 vs CI postgres 1045/0:
the 29 local skips are exclusively the `FORGE_TEST_DATABASE_URL`-gated
tests (19 `test_forge_postgres_integration` + 7 pgvector vector-suite +
1 backup/restore smoke + 2 audit-ledger PG proofs), each with an explicit
skip reason; the postgres job sets that env var, so 1016 + 29 = 1045 with
**0 skipped** — arithmetic exact, no hidden skips, no xfail. Baseline
movement since the reported baseline is zero: 1016/29 local and 1045/0 PG
match the BA-14 GAP-05 packet exactly (re-verified, no drift). The two
PG-gated audit-ledger tests executed in CI on the exact final head.

## 7. Evidence-pack reconciliation performed (this packet)

Appended/updated only where executed evidence supports it (never
rewriting historical rows): matrix totals note reconfirmed at this head
(116 = 106/9/1) and stale book-level record rows G-F2 (migration head → 4)
and G-F3 (counts → 1016/29, 1045/0) corrected; gap register GAP-01/GAP-05
"re-audit pending" → re-audited here; CI ledger rows L-18…L-21 appended
(the BA-14 ladder runs re-queried live); ratification checklist
pre-conditions re-verified at `1041787`; README/CONTRACT_FREEZE_READINESS
verdict basis updated by this re-audit. Frozen planning documents, the six
Bloc packets, `cross_bloc/` and both `closure_repair*` packets are
untouched.

## 8. Phase 7 — verdict

**BOOK II READY FOR RATIFICATION AUTHORIZATION**

No B-class blocker remains; every frozen gate bullet is either demonstrated
(106 D) or legitimately qualified with downstream delegation and executed
evidence (9 Q), and the single ND row is the ratification commit itself,
which exists only by the ratification act. The operator decisions that must
be **recorded as part of the final ratification**:

1. **D5 / G-P4 confirmation** (frozen checklist pre-condition — the one
   decision that gates the ratification record itself).
2. **D1** retention stance: no retention at freeze; retention job =
   future authorized packet.
3. **D2** write-policy record: `best_effort` default; `require_durable`
   promotion rule for production security events.
4. **D3** migration-before-enable runbook recorded as the activation
   dependency (004 applied → compat OK → enable).
5. **D4** ruling recorded: the unwired container persistence seam is an
   affirmed Book II contract boundary; whole-app wiring is deployment-scoped.

Plus the standard non-statements: ratification ≠ production readiness
(Book VIII), ≠ provider validation (GAP-06), ≠ Book III+ authorization.

This packet ratifies nothing. Stop after re-audit, per authorization.
