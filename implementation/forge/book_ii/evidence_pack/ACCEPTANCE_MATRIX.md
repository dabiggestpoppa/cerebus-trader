# BOOK II — CONSOLIDATED ACCEPTANCE MATRIX

Evidence head: `ae35276`. Sources are frozen (byte-identical to pinned
commits). Dispositions: **D** = demonstrated by committed test/evidence;
**Q** = qualified (partial demonstration, qualification stated); **ND** =
not demonstrated at this head. A test count never substitutes for a
requirement row: every frozen requirement appears exactly once.

Suites referenced: `S1=test_forge_service_composition.py (36)`,
`S2=test_forge_persistence.py (56)`, `S3=test_forge_identity.py (66)`,
`S4=test_forge_policy.py (86)`, `S5=test_forge_providers.py (74, +
tests/provider_contract.py harness)`, `S6=test_forge_observability.py (104)`,
`XB=test_forge_cross_bloc.py (56)`, `PG=test_forge_postgres_integration.py (19+7)`,
`AUD=test_forge_audit_ledger.py (41 local + 2 PG; GAP-05 packet)`.

## Section A — Book-level ratification gate
(Frozen source: Book II plan, `# BOOK II ACCEPTANCE / RATIFICATION GATE`)

### Runtime

| ID | Requirement | Owner | Implementation | Executable test | Evidence / Ratification | Disp. | Qualification / gap |
|---|---|---|---|---|---|---|---|
| G-R1 | clean application boot in LOCAL/TEST | II.1 | `app/main.py`, `app/forge/service/*` | S1 (TestClient lifespan boot) | II.1 EVIDENCE §Exact commands; II.1 RATIFICATION A/J | D | — |
| G-R2 | readiness refuses incompatible/unavailable critical dependencies | II.1+II.2 | `service/health.py`, `service/container.py`, `service/lifecycle.py` | S2 `TestStartupAndReadiness` (4 states); XB `TestX9…I3` | II.1 RAT D; II.2 RAT L | D | — |
| G-R3 | graceful shutdown works | II.1 | `ForgeLifecycle.shutdown` on app lifespan | S1 lifecycle J tests | II.1 EVIDENCE §J | D | — |
| G-R4 | production config has no test bypass | II.1 | `config.py` (`ForgeConfig`, redacted diagnostics) | S1 F tests (malformed values fail, no credential fields, no env mutation) | II.1 RAT F | D | — |

### Database

| ID | Requirement | Owner | Implementation | Executable test | Evidence / Ratification | Disp. | Qualification / gap |
|---|---|---|---|---|---|---|---|
| G-D1 | empty Postgres+pgvector → current schema | II.2 (+closure repair) | `persistence/sql/001`, `002`, `003` + dialect-aware `migrations.py` | PG: migrations apply on empty Postgres+pgvector; extension/table/constraint assertions in `TestPostgresVectorProjection::test_empty_database_applies_pgvector_schema`; chain pins `[1,2,3,4]` | closure_repair EVIDENCE §3; ledger L-17 (run 38188302328); pins advanced by GAP-05 packet (run 38261712088) | D | pgvector half demonstrated on CI (GAP-01 closed by repair); 004 portable addition verified on both dialects |
| G-D2 | migration verification passes | II.2 | `check_compatibility`, `FORGE_MIGRATION_COMPATIBILITY_REQUIRED=1` | S2 J tests; CI postgres job runs with requirement=1 | II.2 RAT J; EVIDENCE §J | D | — |
| G-D3 | canonical projection loads | II.2 | canonical tables + gateway | S2 B/C/D round-trip matrix; PG round trip | II.2 RAT B/C/D | D | — |
| G-D4 | vector projection rebuilds independently | II.2 (+closure repair) | `003_vector_projection.sql` + `rebuild_vector_projection` (SQL + memory) | PG: `test_rebuild_deterministic_stale_and_corruption_recovery`, `test_projection_deletion_leaves_canonical_truth_intact`; contract rebuild trio | closure_repair EVIDENCE §3; ledger L-17 | D | Independent deterministic rebuild proven (wipe→canonical intact→restore; stale removal; corruption recovery) |
| G-D5 | backup/restore smoke passes | II.2 (+closure repair) | mechanism + executed smoke | `tests/test_forge_backup_restore.py::TestBackupRestoreSmoke` (dump → fresh-DB restore → independent verification) | closure_repair EVIDENCE §6; ledger L-17 | D | Smoke executed and verified on CI Postgres+pgvector; local execution is a recorded infra gap (no CREATEDB/pgvector); launch-scale drills remain Book VIII |
| G-D6 | duplicate/dangling critical records fail | II.2 | gateway integrity kernel | S2 F/G tests; XB D2 | II.2 RAT F/G | D | — |

### Identity

| ID | Requirement | Owner | Implementation | Executable test | Evidence / Ratification | Disp. | Qualification / gap |
|---|---|---|---|---|---|---|---|
| G-I1 | internal identity independent of provider | II.3 | `identity.py`, `service/authentication.py` | S3 A/B/C tests; XB `K3` | II.3 RAT (laws list) | D | — |
| G-I2 | session expiration/revocation works | II.3 | `ForgeSession.is_expired`, `revoke_session` | S3 G/E tests; XB A1/A2, F8 | II.3 RAT; XB EVID | D | — |
| G-I3 | role escalation tests fail | II.3+II.4 | roles are data only; no admin bypass | S3 R tests; S4 `test_role_is_not_a_capability` | II.3 RAT R; II.4 RAT | D | — |
| G-I4 | external identity collision/linking tests pass | II.3 | `link_external_identity` collision rule | S3 B tests; XB F3 | II.3 RAT B | D | — |

### Policy

| ID | Requirement | Owner | Implementation | Executable test | Evidence / Ratification | Disp. | Qualification / gap |
|---|---|---|---|---|---|---|---|
| G-P1 | deny-by-default | II.4 | `policy.py` `DefaultDenyPolicyEngine` | S4 A–N; XB 280-decision matrix | II.4 RAT clauses A–Z | D | — |
| G-P2 | protected objects filtered before provider boundary | II.4 (+I.4) | `service/policy_enforcement.py` guard | S4 P1–P3; XB B1, C1–C4 | II.4 RAT P/Q | D | — |
| G-P3 | direct-ID, alias, historical-version and vector leakage tests fail closed | II.4 + I.4 (+closure repair for vector) | per-candidate authorization; QA status authority; `retrieval_vectors` exposure/tenant SQL filters | direct-ID: S4 Z1; alias: S retrieval `test_status_and_exposure_filters`, `test_deny_before_load_zero_loads_on_deny`, QA `test_b4_alias_expansion_never_rewrites_status_tokens`; historical-version: `test_generation_is_retained_from_the_source`, `test_ranking_never_changes_status_or_exposure`; **vector: `test_isolation_matrix_zero_leakage` + `TestPostgresVectorProjection::test_isolation_matrix_on_postgres` (deny ≡ missing, zero cross-tenant/cross-exposure leakage)** | II.4 RAT Z; I.4 EVID; closure_repair EVIDENCE §3; ledger L-17 | **Q** | Vector sub-clause **D** (GAP-01 closed by repair); residual: alias/historical fail-closed is indirect (uniform per-candidate authz), no dedicated bypass-adversarial test → GAP-07 (minor) |
| G-P4 | entitlement revocation observed promptly | II.4 (state: Book VI) | `AuthorizationContext` seam (stateless, exact atoms) | capability exact-match + deny tests (S4 E/O); session revocation immediacy (S3, XB F8); revoke event vocabulary (S6 `TestEntitlementAudit`) | II.4 RAT 2; II.6 RAT 4; Book II handoff “Book VI owns entitlement” | **Q** | No entitlement state exists in Book II; promptness proven at seam + session level → GAP-03 (downstream) |
| G-P5 | decision reason/audit available | II.4+II.6 | `PolicyDecision.reason_code/detail`, `PolicyAuditRecord` | S4 S tests; XB A7 | II.4 RAT S; II.6 RAT 4 | D | — |

### Providers

| ID | Requirement | Owner | Implementation | Executable test | Evidence / Ratification | Disp. | Qualification / gap |
|---|---|---|---|---|---|---|---|
| G-V1 | complete application core runs against deterministic fakes | II.5 | `providers/fakes.py`, `registry.py` | S5 (74) + full CI runs entirely on fakes | II.5 RAT 1–3 | D | — |
| G-V2 | fake LLM swappable without domain change | II.5 | `ProviderFactory` config selection | S5 replacement tests; XB H1/H2 | II.5 RAT 1 | D | — |
| G-V3 | fake commerce swappable without entitlement-domain change | II.5 | commerce port + fakes (no entitlement domain exists to change) | S5; XB H1 | II.5 RAT 1–2 | D | — |
| G-V4 | provider outage never grants access | II.5+II.6 | resilience + policy isolation | XB C1–C4, F1/F5/F10; S5 circuit tests | II.5 EVID §5; XB EVID §5–6 | D | — |

### Observability

| ID | Requirement | Owner | Implementation | Executable test | Evidence / Ratification | Disp. | Qualification / gap |
|---|---|---|---|---|---|---|---|
| G-O1 | request correlation works end-to-end | II.6 | `observability/correlation.py` + routes | S6 correlation A tests; XB B4 | II.6 RAT 1 | D | — |
| G-O2 | protected access is auditable | II.6 | retrieval access audit (II.6.5) | S6 E tests; XB B3/B4/B5 | II.6 RAT 4 | D | — |
| G-O3 | secrets/protected corpus absent from normal logs | II.6 | redaction at construction (incl. typed fields after `4b2d4ae`) | S6 J/redaction tests; XB G1–G4 | II.6 RAT 6; XB EVID §7 (RED→GREEN) | D | Demonstrated after the cross-bloc-found repair; no other leak found |
| G-O4 | dependency failures normalize correctly | II.6 | `errors.py` taxonomy + mapping | S6 G tests; XB C2, F5, F6 | II.6 RAT 5 | D | — |

### Evidence pack (per-bloc deliverables)

| ID | Requirement | Owner | Reference | Disp. | Qualification |
|---|---|---|---|---|---|
| G-E1 | `PLAN.md` per Bloc | all | `bloc_ii_1..6/PLAN.md`, `cross_bloc/PLAN.md` | D | — |
| G-E2 | `ACCEPTANCE.md` per Bloc | all | `bloc_ii_1..6/ACCEPTANCE.md`, `cross_bloc/ACCEPTANCE.md` | D | — |
| G-E3 | implementation commit ladder | all | ladders in each EVIDENCE/VERIFICATION (append-only, SHAs recorded) | D | — |
| G-E4 | test output | all | per-bloc EVIDENCE §Exact tests; ledger | D | — |
| G-E5 | `EVIDENCE.md` per Bloc | all | `bloc_ii_1..6/EVIDENCE.md`, `cross_bloc/EVIDENCE.md` | D | — |
| G-E6 | unresolved issue list | all | each packet’s “Known gaps” + `OPEN_GAP_REGISTER.md` | D | — |
| G-E7 | ratification record per Bloc | all | `bloc_ii_1..6/RATIFICATION.md` (all CLOSED — PASS); cross-bloc has VERIFICATION only, by design | D | Cross-bloc is a packet, not a Bloc; no ratification expected |

### Final Book II evidence records (gate §Evidence pack, book level)

| ID | Required record | Value at evidence head | Disp. | Qualification |
|---|---|---|---|---|
| G-F1 | schema version | domain `FORGE_DOMAIN_V1`; event schema `FORGE_EVENT_V1` | D | — |
| G-F2 | migration head | SQL chain `001_initial_schema.sql` + `002_identity_session.sql` → head **2** (compatibility OK in CI) | D | — |
| G-F3 | test counts | local 946 passed/19 skipped; PG-attached 965/0 (ledger) | D | — |
| G-F4 | provider contract versions | `providers/doctrine.py` `ProviderContractSpec` (8 Ch II.5.1 elements) × 4 ports; implementations = `fake` only | D | Concrete adapters (IV/VI) intentionally absent → GAP-06 |
| G-F5 | policy version/hash | `POLICY_MODULE_SHA256 = f10751e6ba6144d807abc151dbcbd7a06320a3d1ab82279fe1cac26b8a228fcc`, asserted green in `test_forge_retrieval.py:1585` | D | Policy byte-identical since the I.4 pin |
| G-F6 | known exclusions | `EVIDENCE_SUMMARY.md` §6 | D | — |
| G-F7 | Book II ratification commit | **does not exist** | **ND** | Ratification not authorized by this assignment (by design, not a defect) |

## Section B — Chapter requirements (Ch II.1.1 – II.6.10)

### Bloc II.1 — Service Skeleton

| ID | Chapter | Owner/Impl ref | Executable test | Disp. | Qualification |
|---|---|---|---|---|---|
| CH-II.1.1 | Repository/runtime layout | `app/forge/service/*`, `/forge/v1` | S1 A/B | D | — |
| CH-II.1.2 | Configuration contract | `config.py` | S1 F | D | — |
| CH-II.1.3 | Environment profiles | `ForgeConfig.is_local/test/production` | S1 F/E | D | — |
| CH-II.1.4 | Application lifecycle | `service/lifecycle.py` | S1 J | D | — |
| CH-II.1.5 | Health/readiness/liveness | `service/health.py` | S1 C/D; XB I1–I4 | D | — |
| CH-II.1.6 | Migration runner | `persistence/sql/migrations.py` | S2 J; PG | D | — |
| CH-II.1.7 | Local developer harness | partial: `Dockerfile`, workflow; no FORGE compose stack | S1 acceptance bullets (boot from empty env, no paid provider, import isolation, migration-before-ready) tested | **Q** | “One-command stack with Postgres+pgvector and seed fixtures” not built (repo compose predates FORGE, no FORGE services) → GAP-04 |

### Bloc II.2 — Persistence

| ID | Chapter | Owner/Impl ref | Executable test | Disp. | Qualification |
|---|---|---|---|---|---|
| CH-II.2.1 | Database foundation | `001/002`, gateway | S2 A; PG | D | — |
| CH-II.2.2 | Canonical projection tables | `canonical_objects`, `canonical_references` | S2 B/C | D | — |
| CH-II.2.3 | Provenance/relationship graph | `artifacts`, `provenance_edges` | S2 E | D | — |
| CH-II.2.4 | Retrieval/embedding storage | `003_vector_projection.sql` `retrieval_vectors` + `VectorProjectionRecord` (storage substrate only) | vector contract (29) + PG (7) suites; PG schema test | D | Storage only — embedding generation/model selection remain Book VII (frozen ownership, PLAN §7 exclusions held) |
| CH-II.2.5 | Account and access tables | `forge_users`, `external_identity_links`, `forge_sessions` | S3 I/J; PG identity 7 | D | Accounts = internal users only; org/billing accounts are Book VI (excluded) → GAP-03-related |
| CH-II.2.6 | Audit/event ledger | durable `004_audit_ledger.sql` (`forge_audit_events`, append-only, content-minimized) + `observability/audit_ledger.py` (`DurableAuditLedger`) + II.6 durable mirrors across all six Ch II.2.6 record classes, over `AuditEventPort` (persistence-side coercion; observability stays persistence/provenance-free) | `test_forge_audit_ledger.py` (41 local + 2 PG); S6 E/F trails; redaction tests; failure matrix + restart recovery | D | Durability executed on SQLite (schema contract, five seams, redaction-before-storage, fault/recovery matrix, restart survival) and on real PostgreSQL in CI run **38261712088** (`3529a0d`, postgres job 1045 passed). Streams stay in frozen `STREAMS`; no Book VI business table; provider-event/entitlement **business tables** remain Book VI (GOVERNANCE §2). GAP-05 closed; pack re-audit pending |
| CH-II.2.7 | Transaction/concurrency rules | `transaction()`, optimistic versions | S2 G/N; XB D1–D5, F9 | D | — |
| CH-II.2.8 | Migration discipline | first-party runner, ledger | S2 J | D | — |
| CH-II.2.9 | Backup/restore contract | mechanism (replayable migrations + version ledger) + executed smoke | `test_forge_backup_restore.py` | D | Smoke executed on CI (GAP-02 closed by repair); launch-scale drills remain Book VIII |
| CH-II.2.10 | Persistence test matrix | S2 + PG + closure-repair suites | S2 (56) + PG (19) + vector (36) + backup smoke (1) | D | — |

### Bloc II.3 — Identity & Session

| ID | Chapter | Owner/Impl ref | Executable test | Disp. | Qualification |
|---|---|---|---|---|---|
| CH-II.3.1 | Internal identity model | `identity.py` `ForgeUser` | S3 A | D | — |
| CH-II.3.2 | Account model | user lifecycle ACTIVE/DISABLED | S3 A + state-transition tests | **Q** | Minimal user account only; billing/org account excluded to Book VI (plan exclusions) |
| CH-II.3.3 | Authentication adapter | `service/authentication.py` | S3 M/O; XB A1–A5 | D | — |
| CH-II.3.4 | Session contract | `ForgeSession`, opaque tokens | S3 E–H | D | — |
| CH-II.3.5 | Account linking | `link_external_identity` | S3 B; XB F3 | D | — |
| CH-II.3.6 | Roles | `IdentityRole` (data only) | S3 R; S4 role-not-capability | D | — |
| CH-II.3.7 | Service identity | `IdentityRole.SERVICE` primitive | S3 (roles tests include SERVICE) | **Q** | No background jobs/provider callbacks exist yet to receive constrained service principals → GAP-06-related (downstream) |
| CH-II.3.8 | Revocation | session revoke (+all) | S3; XB F8 | D | — |
| CH-II.3.9 | Identity security tests | S3 R + PG identity | S3 (66); PG 7 | D | — |

### Bloc II.4 — Policy & Access Control

| ID | Chapter | Owner/Impl ref | Executable test | Disp. | Qualification |
|---|---|---|---|---|---|
| CH-II.4.1 | Exposure taxonomy | `ProductExposure` matrix | S4 F–L | D | — |
| CH-II.4.2 | Capability registry | `REGISTERED_CAPABILITIES` exact atoms | S4 E; XB F1 | D | — |
| CH-II.4.3 | Entitlement resolver | consumption seam only (`AuthorizationContext`) | S4 E/O deny rules; XB F1–F3 | **Q** | Expiration/grace/revocation resolution needs Book VI entitlement state → GAP-03 |
| CH-II.4.4 | Object authorization | `guard`/`authorize` | S4 P; XB B1/B5 | D | — |
| CH-II.4.5 | Lifecycle/status policy (exposure ≠ epistemic status) | status authority stays Book I (retrieval/QA) | S retrieval `test_status_and_exposure_filters`; QA `test_g7_no_status_change_by_relevance_wording_or_ranking` | D | Separation proven; no status-based policy rule needed by design (kernel is exposure-only) |
| CH-II.4.6 | Depth/mode policy | depths are presentation, never trust tiers | S4 (role/depth assertions) + QA depth routing | **Q** | Consumer depth routing (Ask CEREBUS) is Book IV input; Book II proves depth cannot bypass exposure |
| CH-II.4.7 | Deny-by-default | `DefaultDenyPolicyEngine` | S4 M/N/L; XB matrix | D | — |
| CH-II.4.8 | Policy reason codes | `PolicyReason` vocabulary | S4 R; XB A7 | D | — |
| CH-II.4.9 | Policy simulation/explain | `PolicyDecision.detail/reason_code` + audit records | S4 S tests; XB A7 | **Q** | Explain data machine-readable and tested; no admin HTTP tooling (no admin surface exists at Book II) → GAP-04-related (nonblocking) |
| CH-II.4.10 | Policy adversarial suite | S4 | S4 (86) incl. Z1/Z2; XB A/X2 | D | — |

### Bloc II.5 — Provider Ports

| ID | Chapter | Owner/Impl ref | Executable test | Disp. | Qualification |
|---|---|---|---|---|---|
| CH-II.5.1 | Provider contract doctrine | `providers/doctrine.py` `ProviderContractSpec` | S5 contract specs | D | — |
| CH-II.5.2 | LLM port | `providers/llm.py` | S5 port tests | D | — |
| CH-II.5.3 | Commerce port | `providers/commerce.py` | S5 port tests | D | — |
| CH-II.5.4 | Notification port | `providers/notification.py` | S5 port tests | D | — |
| CH-II.5.5 | Object/blob storage port | `providers/storage.py` | S5 port tests | D | — |
| CH-II.5.6 | Provider registry/factory | `registry.py`, config selection | S5; XB H1 | D | — |
| CH-II.5.7 | Failure normalization | 8-class taxonomy | S5; XB C2/F5/F6 | D | — |
| CH-II.5.8 | Circuit/fallback policy | `resilience.py` | S5; XB C3/C4/F10 | D | — |
| CH-II.5.9 | Fake providers (9 scenarios) | `fakes.py` scripted | S5 §4 scenario map; XB F1/F3/F4 | D | — |
| CH-II.5.10 | Replacement tests | shared contract harness (`tests/provider_contract.py`) + XB H1/H2 | S5; XB | D | Replacement proven at neutral ports; real vendor SDKs absent → GAP-06 |

### Bloc II.6 — Observability

| ID | Chapter | Owner/Impl ref | Executable test | Disp. | Qualification |
|---|---|---|---|---|---|
| CH-II.6.1 | Request correlation | `correlation.py`, routes | S6 A; XB B4 | D | — |
| CH-II.6.2 | Structured logging | `events.py` frozen fields + redaction | S6 B/C/J; XB G1–G3 | D | Typed-field scrub added by repair `4b2d4ae` |
| CH-II.6.3 | Tracing | component/operation boundary vocabulary | S6 C | D | In-process boundary events only; no vendor tracing (by design) |
| CH-II.6.4 | Metrics | `metrics.py` frozen names | S6 D; XB G2 | D | — |
| CH-II.6.5 | Retrieval access audit | `RetrievalAccessAuditRecord` | S6 E; XB B3/B4 | D | — |
| CH-II.6.6 | Entitlement audit vocabulary | `EntitlementAuditRecord` (records only) | S6 F; XB F2/F3 | D | Mutation intentionally absent (Book VI) |
| CH-II.6.7 | Error taxonomy (9 classes) | `errors.py` | S6 G; XB C2 | D | — |
| CH-II.6.8 | Safe error responses | `safe_error_response` | S6 G/H; XB G1/G3 | D | — |
| CH-II.6.9 | Cost/usage ledger | `usage.py` | S6 I; XB G2 | D | — |
| CH-II.6.10 | Observability tests | S6 | S6 (104) | D | — |

## Section C — Cross-cutting frozen requirements

| ID | Frozen source | Requirement | Reference / test | Disp. | Qualification |
|---|---|---|---|---|---|
| C-MP1 | Master plan, Book II gate | core runs with mock providers | G-V1; all CI runs on fakes | D | — |
| C-MP2 | Master plan, Book II gate | database rebuilds cleanly | G-D1/D2 (empty-PG rebuild in CI) | D | pgvector dimension → GAP-01 |
| C-MP3 | Master plan, Book II gate | policies deny unauthorized retrieval before LLM invocation | G-P2; S4 P/Q; XB B1 | D | — |
| C-MP4 | Master plan, Book II gate | provider replacement tests pass | G-V2/V3; XB H1–H3 | D | — |
| C-MI5 | Master plan global invariants | exposure/entitlement filtering before LLM context | S4 P/Q, XB B1–B3 | D | — |
| C-MI6 | Master plan global invariants | provider IDs never become core domain identity | XB K3; S3 B | D | — |
| C-MI7 | Master plan global invariants | replaceable LLM/commerce providers | G-V2/V3 | D | — |
| C-MI8 | Master plan global invariants | every Book defines migration/observability/security/acceptance | S2 J, S6, security reviews, ACCEPTANCE A–Z sets | D | — |
| C-FZ5 | Freeze manifest invariant 5 | exposure/entitlement filtering before LLM context | as C-MI5 | D | — |
| C-FZ17/18/19 | Freeze manifest invariants 17–19 | providers replaceable; checkout ≠ entitlement; provider IDs ≠ identity | XB F1–F3, H1; S5 | D | — |
| C-FZ22 | Freeze manifest invariant 22 | no brokerage execution in V1 | XB `test_no_brokerage_execution_api` (AST over `app/forge`) | D | — |
| C-C04 | Audit contract C04 | Identity/Principal contract (II owns; provider mapped not authoritative) | S3; XB K3 | D | — |
| C-C05 | Audit contract C05 | Authorization decision (deny-by-default, pre-provider filtering) | S4; XB | D | — |
| C-C06 | Audit contract C06 | provider ports (domain cannot import adapters) | XB `test_import_discipline` (AST) | D | — |
| C-C10 | Audit contract C10 | capability contract: evaluation in II, catalog in VI | S4 E/XB F1 (evaluation); catalog absent (VI) | Q | Definition/catalog owned by Book VI → GAP-03 |
| C-C11 | Audit contract C11 | commerce event contract: port in II, adapter/ledger in VI | S5 port; XB F3–F4 (no grant state) | D | Adapter/ledger intentionally Book VI |
| C-C14 | Audit contract C14 | audit/observability foundation in II | S6; XB G1–G4 | D | — |
| C-DEF5 | Audit §8 deferred proofs | backup/restore measurements deferred (expected) | GAP-02 | D | Smoke executed + independently verified by closure repair; launch-scale measurements remain Book VIII |
| C-EXCL | Book II plan `# BOOK II EXCLUSIONS` | no market math, no TradingView, no Whop behavior, no pricing, no frontend, no promotion, no execution, no advice, no final security certification | AST/scope reviews in each EVIDENCE §Exclusions; XB K6 | D | Book VIII owns launch security |

**Totals:** 41 requirement rows (Section A: gate §Runtime–§Final evidence
records), 56 chapter rows (Section B: Ch II.1.1–II.6.10), 19 cross-cutting
rows (Section C) = **116 frozen requirement rows: 106 D, 9 Q, 1 ND**
(ND = G-F7, the ratification commit, pending by design). Re-counted
programmatically after the Book II closure-repair update (ledger L-15…L-17;
GAP-01 and GAP-02 rows moved to D on executed CI evidence; G-D4/CH-II.2.4
were ND before that repair) and again after the GAP-05 packet (CH-II.2.6
Q → D on executed CI evidence, run 38261712088). Row-level detail above is
authoritative; the only ND row is **G-F7**. Residual Q rows (9): G-P3
(vector sub-clause now D; GAP-07 minor remains), G-P4 (GAP-03), CH-II.1.7
(GAP-04), CH-II.3.2, CH-II.3.7, CH-II.4.3, CH-II.4.6, CH-II.4.9
(Book-VI-owned or deferred scope), C-C10 (GAP-03).
