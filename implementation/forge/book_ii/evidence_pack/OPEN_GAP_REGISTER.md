# BOOK II — OPEN GAP REGISTER

Evidence head: `ae35276`. Nothing here is closed silently. Classifications:
**B** = Book II ratification blocker · **D** = downstream dependency ·
**N** = accepted nonblocking limitation · **O** = operator governance
decision · **C** = closed by the Book II closure repair (executed evidence,
`implementation/forge/book_ii/closure_repair/`) · **DISPOSED** = governance
question answered and recorded (no implementation claim). Evidence column
names committed files/tests/queries used. Rows updated 2026-10-12 after the
closure-repair packet; historical dispositions are preserved in the repair
EVIDENCE/GOVERNANCE records, never overwritten silently. GAP-05 row updated
2026-10-12 after the Build Agent #14 GAP-05 implementation packet
(`implementation/forge/book_ii/closure_repair_gap05/`, plan+acceptance
committed before implementation; CI run 38261712088 green on `3529a0d`).
**2026-10-12 re-audit (BA-15, `1041787`): the pack re-audit is now COMPLETE**
(`implementation/forge/book_ii/evidence_reaudit/RE_AUDIT.md`) — all C rows
re-verified against executed evidence, no reclassification changed, B-class
blocker list remains empty, and the re-audit verdict is
**BOOK II READY FOR RATIFICATION AUTHORIZATION** (operator decisions D1–D5
still to be recorded at ratification).

| ID | Gap | Classification | Evidence | What would close it |
|---|---|---|---|---|
| GAP-01 | **Vector/embedding persistence family absent.** Frozen Ch II.2.4 (retrieval/embedding storage incl. embedding vector + model/version) was unimplemented; gate bullets G-D1 (`empty Postgres+pgvector → current schema`), G-D4 (`vector projection rebuilds independently`) and G-P3’s vector sub-clause were ND/Q. | **C** | Closed by closure repair (option A: implementation): `003_vector_projection.sql` (pgvector, dimension CHECK, canonical FK, owner FK), `VectorProjectionRecord` + validation + canonical cross-checks on both gateways, deny-before-content-load reads, SQL-side filtered search, deterministic rebuild. Executed proof: closure_repair EVIDENCE §3/§4; CI run **38188302328** on `914cc04` — postgres job **1002 passed**, incl. `test_empty_database_applies_pgvector_schema`, the rebuild trio, `test_isolation_matrix_on_postgres` | Closed by implementation + CI execution; embedding generation/model selection remain Book VII (frozen ownership). **Re-audit COMPLETE 2026-10-12** (BA-15 `1041787`): row re-verified, stays C |
| GAP-02 | **Backup/restore smoke never executed.** Gate bullet G-D5 required “backup/restore smoke passes”; II.2 delivered mechanism only (migration-replayable schema + `forge_schema_migrations` version ledger); no smoke test existed. | **C** | Closed by closure repair (executed smoke): `tests/test_forge_backup_restore.py` — pg_dump `-Fc` → restore into fresh `forge_restore_smoke` DB → verification on the restored DB only (tables, counts, canonical hash multiset, head `[1,2,3]`, vector rows/dims, canonical↔projection reconciliation, migration no-op, source unchanged). CI run **38188302328** postgres job green. Closure_repair EVIDENCE §6 | Executed + independently verified; local execution is a recorded infra gap (no CREATEDB/pgvector, never substituted). Launch-scale drills remain Book VIII (frozen plan split) |
| GAP-03 | **Entitlement production and resolver rules do not exist** (expiration/grace/revocation resolution, capability catalog C10 definition). Gate bullet G-P4 (`entitlement revocation observed promptly`) is only demonstrated at the seam: capability exact-match deny + session-revocation immediacy + revoke-event audit vocabulary. | **D** | Book II plan handoff “Book VI may assume … policy consumes internal capabilities”; II.4 RATIFICATION statement 2 (no Plan/Subscription/Price objects); II.6 RATIFICATION 4 (entitlement audit is record-only); S4 `test_capability_atoms_exact_match`, S3 revocation tests, S6 `TestEntitlementAudit`, XB F1–F3 | Book VI implementation; at ratification, operator confirms seam-level demonstration satisfies G-P4 within frozen Book II ownership (not a Book II code change). |
| GAP-04 | **No one-command FORGE local stack** for Ch II.1.7’s description (Postgres+pgvector, fakes, seed fixtures). Its five explicit “Acceptance II.1” bullets are all demonstrated; the harness itself was not built (repo `docker-compose.yml` predates FORGE and contains no FORGE services). | **N** | `git log --diff-filter=A -- docker-compose.yml` = `af45cc7` (2026-04-26, Signal Guard); compose contains no forge/postgres/vector entries; II.1 ACCEPTANCE bullets (boot from empty env, no paid provider, import isolation, migration-before-ready) tested in S1/S2 | Optional harness work; pgvector portion rides on GAP-01. No gate bullet depends on it. |
| GAP-05 | **Durable audit/event ledger absent** (Book-VI-owned business tables portion reclassified below). Frozen Ch II.2.6 wants append-oriented audit/event records; the implementation has typed **in-process** append-only trails (II.6) and 8+1 tables — no durable audit, provider-event or application-job tables. **Ownership ruled** by the operator and verified against frozen contracts (closure_repair/GOVERNANCE §2): Book II owns durable, content-minimized operational/security audit infrastructure; Book VI owns commercial entitlement decisions; Book I owns evidence provenance; no alternative licensing/evidence authority exists or may be created. | **C** (was B — ownership ruling resolved scope; the implementation now exists. Book-VI-owned products/plans/licenses/entitlements **business-tables** portion remains **D**/Book VI, unchanged) | Closed by the Build Agent #14 packet: portable `004_audit_ledger.sql` (`forge_audit_events`, append-only, content-minimized) + `AuditEventPort`/`coerce_audit_event` + `observability/audit_ledger.py` `DurableAuditLedger` (bounded cache, redaction-before-storage, `best_effort` failover markers vs `require_durable` typed failure) + durable mirrors across all six Ch II.2.6 record classes. Executed: `tests/test_forge_audit_ledger.py` (41 passed local + 2 PG on CI), full local `1016 passed/29 skipped`, CI run **38261712088** on `3529a0d` — test job **1016/29**, postgres job **1045/0**; recovery evidence (restart survival + migration fault) in `implementation/forge/book_ii/closure_repair_gap05/EVIDENCE.md` §6–§8 | **Fulfilled by implementation + CI execution**; pack re-audit (performed 2026-10-12 by BA-15, see below; this packet did NOT ratify Book II). Operator decisions remaining (retention policy, write-policy promotion, migration-before-enable procedure, container persistence wiring) are listed in that EVIDENCE §11 and `G-P4_GAP-03_RECONCILIATION.md` §3, consolidated with recommendations as D1–D5 in `../evidence_reaudit/RE_AUDIT.md` §5. **Re-audit COMPLETE 2026-10-12** (BA-15 `1041787`, incl. an out-of-suite probe): row re-verified, stays C |
| GAP-06 | **No concrete provider adapters** (OpenRouter = Book IV, Whop = Book VI); provider contract versions = `fake` implementations only. | **D** | Book II plan `# BOOK II EXCLUSIONS` (no production Whop behavior); II.5 RATIFICATION statement 5 + “Limitations carried forward”; readiness discloses `openrouter`/`whop` `NOT_CONFIGURED` | Books IV/VI; Book II’s replacement tests are neutral-port level by design (matrix G-F4). |
| GAP-07 | **Alias / historical-version leakage fail-closed is indirect.** G-P3’s direct-ID sub-clause is proven (S4 Z1); alias/status-laudering (QA `test_b4_alias_expansion_never_rewrites_status_tokens`) and generation/ranking invariants are proven, but there is no dedicated “alias-bypass”/“historical-version access-bypass” adversarial test. | **N** | S retrieval `test_status_and_exposure_filters`, `test_deny_before_load_zero_loads_on_deny`, `test_generation_is_retained_from_the_source`, `test_ranking_never_changes_status_or_exposure`; uniform per-candidate authorization (XB `test_authorization_precedes_content_access`) | Optional dedicated bypass-adversarial tests in a later hardening packet. |
| GAP-08 | **CI `postgres` job exposed to Docker Hub unauthenticated rate limits.** Two Book II heads (L-07/L-08) failed at image pull with **zero tests executed**. | **N** | Ledger §3 verbatim `toomanyrequests`; recovery routes L-09 (unchanged rerun) and L-13 (local PG). Closure repair moved the service image to `pgvector/pgvector:pg16` (required by frozen G-D1) — same registry, same exposure class (ledger L-15…L-17) | Optional workflow hardening (authenticated pull / pinned mirror) — requires its own authorization; must not weaken PG tests. |
| GAP-09 | **Concurrency proof is deterministic sequential interleave** at the cross-bloc layer; true parallel SQL writer races are not exercised. | **N** | XB EVID §10.3; II.2 N-concurrency tests (optimistic `expected_version`); PG module stale-conflict test | Optional multithreaded writer-race suite on live PostgreSQL. |
| GAP-10 | **Book I corpus / research-status limitations** carried unchanged (existing corpus claims, status qualifications). | **D** | Book I packets (bloc_i_1…i_5 EVIDENCE “known gaps”); QA/claim authority tests remain green | Book VII governance / later corpus work per frozen order. |
| GAP-11 | **No Book III market runtime, no Book IV public Ask CEREBUS, no Book VI licensing, no Book VIII launch evidence.** | **D** | Master plan Book order; Book II exclusions; matrix C-EXCL | Later Books (explicitly outside this authorization). |
| GAP-12 | **No admin policy-explain tooling** (Ch II.4.9 mechanism = decision `detail` + reason codes + audit records, machine-readable and tested; no admin HTTP surface exists at Book II). | **N** | S4 S tests; XB A7; no admin routes (II.1 route-set test) | Admin surface belongs to a later Book; tooling can be added without changing the kernel. |
| GAP-13 | **Service identity has no consumers yet** (Ch II.3.7: constrained service principals for jobs/webhooks; `IdentityRole.SERVICE` exists and is tested). | **D** | S3 roles tests incl. SERVICE; no background jobs/provider callbacks exist at Book II (Ch II.3.7 requires them) | Book VI webhooks / later job infrastructure. |
| GAP-14 | **No final production security certification** (Book II gate exclusions + audit §8.7 security scans/red-team deferred). | **D** | Book II plan `# BOOK II EXCLUSIONS`; audit §8 deferred proofs | Book VIII. |
| GAP_ADR_001 | **Phase-order vs bloc-dependency contradiction** — recorded OPEN by II.5, carried byte-identical through II.6, step 7, and the evidence pack. **DISPOSED** by the closure repair: operator interpretation recorded verbatim — “executable dependency prerequisites govern authorization; phase labels do not override explicitly declared prerequisite contracts” — Book II closure precedes Book III; frozen planning documents remain unchanged (byte-identical re-verified). | **DISPOSED** (was O) | `implementation/forge/book_ii/bloc_ii_5/GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md` (untouched, append-only history); `implementation/forge/book_ii/closure_repair/GOVERNANCE.md` §1; VERIFICATION frozen-file re-check | Governance question answered and recorded; Book III still requires its own authorization under the frozen order |

## Summary by classification (updated after the closure repair)

- **Closed by repair (C):** GAP-01 (vector family: Ch II.2.4 + gate bullets
  G-D1/G-D4/G-P3-vector — implemented and executed on CI run 38188302328,
  postgres job 1002 passed), GAP-02 (backup/restore smoke executed and
  independently verified — same run). Closure evidence:
  `implementation/forge/book_ii/closure_repair/EVIDENCE.md`. **GAP-05**
  (durable operational/security audit + event ledger — Ch II.2.6)
  implemented and executed by the Build Agent #14 packet: CI run
  **38261712088** on `3529a0d`, test job 1016/29, postgres job 1045/0;
  evidence `implementation/forge/book_ii/closure_repair_gap05/EVIDENCE.md`.
- **Book II ratification blockers (B):** **none remain open.** GAP-05 was
  the last B-class row and is now C (above) — re-audit performed 2026-10-12
  (BA-15 `1041787`): re-verified, stays C; blocker list stays empty.
- **Governance disposed:** GAP_ADR_001 (interpretation recorded,
  frozen plans unchanged). No O-class item remains open.
- **Downstream dependencies (D):** GAP-03, GAP-06, GAP-10, GAP-11, GAP-13,
  GAP-14 — plus the products/plans/licenses/entitlements table share of
  former GAP-05 (Book VI) — all owned by later Books under the frozen order.
- **Accepted nonblocking limitations (N):** GAP-04, GAP-07, GAP-08, GAP-09,
  GAP-12 — disclosed, with no frozen gate bullet unmet solely by them.

Nothing in this register is closed without executed evidence or a recorded
governance record: every C/DISPOSED row names the committed proof, and no
reclassification is hidden by a test count. **The re-audit those closures
awaited was performed 2026-10-12 (BA-15 `1041787`): every C row re-verified,
no reclassification changed, and the consolidated pack verdict is now BOOK
II READY FOR RATIFICATION AUTHORIZATION** (`../evidence_reaudit/RE_AUDIT.md` §8).
