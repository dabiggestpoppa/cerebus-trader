# GLX FORGE MASTER BUILD PLAN V1

Status: BUILD PLANNING
Date: 2026-10-04
Branch: forge

## Mission
Build GLX FORGE as the licensed software interface to CEREBUS: canonical market intelligence, evidence, operator tools, indicators and Ask CEREBUS.

## Build law
RECOVER [sufficient] -> CLASSIFY [foundation complete] -> CANONICALIZE [foundation active] -> PRODUCTIZE [this plan].

Books are architectural programs.
Blocs are independently testable capability groups.
Chapters are agent-sized implementation packets.
No Book passes because UI exists; it passes only when its contracts, tests, evidence and failure behavior pass.

## Global invariants
- Canonical objects before raw RAG.
- Model != Claim != Evidence != Setup != Artifact.
- Structured-first exact retrieval.
- Exposure/entitlement filtering before LLM context assembly.
- Provider IDs never become core domain identity.
- CEREBUS statistics require claim/evidence provenance.
- Historical/manual/research status is never silently promoted.
- No personalized financial advice.
- Replaceable LLM and replaceable commerce providers.
- Append-only evidence/provenance where practical.
- Every Book defines migration, observability, security and acceptance.

# BOOK I — CORPUS & CANONICAL KNOWLEDGE
Goal: turn recovered CEREBUS into versioned machine-readable product truth.

## Bloc I.1 Canonical Registry Kernel
Chapters:
I.1.1 object IDs/version/status vocabulary
I.1.2 model/claim/evidence/setup/doctrine/term/lineage schemas
I.1.3 validation and referential integrity
I.1.4 canonical promotion/supersession workflow
I.1.5 conflict and identity-match rules

## Bloc I.2 Source & Provenance Fabric
Chapters:
I.2.1 artifact registry
I.2.2 source hashes/version identity
I.2.3 source->object links
I.2.4 conversation-derived provenance class
I.2.5 visual artifact semantics
I.2.6 missing/partial source handling

## Bloc I.3 Canonical Backfill
Chapters:
I.3.1 EUR stack
I.3.2 XAU Game/scientific
I.3.3 BTC Tracker
I.3.4 Fib/Range Birth
I.3.5 JPY Carry
I.3.6 doctrine/ontology/lineage
I.3.7 historical/P90/ST educational families
I.3.8 research-lab families

## Bloc I.4 Retrieval Object Compiler
Chapters:
I.4.1 canonical->retrieval transformation
I.4.2 structured fields
I.4.3 safe semantic text
I.4.4 alias/generation routing
I.4.5 exposure metadata
I.4.6 rebuild/version jobs

## Bloc I.5 Corpus QA
Chapters:
I.5.1 orphan detector
I.5.2 unsupported-number detector
I.5.3 status leakage detector
I.5.4 broken lineage detector
I.5.5 corpus coverage report
I.5.6 golden canonical fixtures

Book I gate: every launch model resolves model->claim->evidence/source; retrieval objects compile deterministically; no unsupported numerical claim in launch corpus.

# BOOK II — FORGE CORE / PLATFORM
Goal: create provider-independent backend, storage, identity and policy substrate.

## Bloc II.1 Service Skeleton
Chapters: app/runtime layout; config; environments; health/readiness; migrations; local dev.

## Bloc II.2 Persistence
Chapters: Postgres schema; pgvector; canonical tables; account/license tables; audit/event tables; migration discipline; backup/restore.

## Bloc II.3 Identity & Session
Chapters: user identity; auth/session adapter; account linking; roles; admin/service identity; revocation.

## Bloc II.4 Policy Engine
Chapters: exposure classes; entitlements; feature gates; model/setup permissions; researcher/operator depth; deny-by-default.

## Bloc II.5 Provider Adapter Layer
Chapters: LLM interface; commerce interface; email/notification interface if required; storage interface; provider health/fallback.

## Bloc II.6 Observability
Chapters: structured logs; traces; request IDs; retrieval audit; entitlement audit; model/provider cost/latency; error taxonomy.

Book II gate: core runs with mock providers, database rebuilds cleanly, policies deny unauthorized retrieval before LLM invocation, provider replacement tests pass.

# BOOK III — CEREBUS MARKET INTELLIGENCE
Goal: operationalize canonical models as deterministic state/level/context services.

## Bloc III.1 Market Data Contracts
Chapters: symbol/timeframe schema; clock/DST; session ownership; bar finality; data quality; asset-native units.

## Bloc III.2 Measurement Engine
Chapters: ranges/anchors; tiers/AU; coordinates; clocks/state age; MAE/MFE/range-left; event/news inputs.

## Bloc III.3 Model Runtime
Chapters: EUR Daily; EUR Weekly; EUR Higher Order; XAU; BTC; Fib; JPY.

## Bloc III.4 State/Path Engine
Chapters: state snapshots; transitions; first delivery; failure/repair; rekey; layer handoffs; no-go.

## Bloc III.5 Operator Setup Engine
Chapters: setup eligibility; triggers; invalidations; targets; stand-down; manual vs automation flags; explanation payload.

## Bloc III.6 Intelligence API
Chapters: current state endpoint; levels; model evidence; setup context; historical snapshot; deterministic response schemas.

Book III gate: frozen fixtures reproduce canonical state/level outputs; clock/session adversarial tests pass; model layer cannot fabricate unsupported setup action.

# BOOK IV — ASK CEREBUS
Goal: evidence-grounded conversational interface over canonical CEREBUS.

## Bloc IV.1 Query Interpreter
Chapters: intent; asset/model; depth; time scope; historical vs current; actionability detector.

## Bloc IV.2 Hybrid Retrieval
Chapters: structured resolver; semantic resolver; lineage/alias expansion; evidence join; entitlement filter; conflict resolver.

## Bloc IV.3 Context Packager
Chapters: token budget; canonical priority; claim/evidence packaging; source provenance; no-evidence path; anti-leakage.

## Bloc IV.4 LLM Gateway
Chapters: OpenRouter adapter; model selection; prompt contracts; retries/timeouts; cost controls; replaceability.

## Bloc IV.5 Answer Compiler
Chapters: Beginner; Operator; Researcher; epistemic labels; citations/provenance; numerical safety; uncertainty/refusal.

## Bloc IV.6 Evaluation
Chapters: golden Q/A; unsupported-stat traps; generation-conflict tests; leakage attacks; entitlement attacks; hallucination grading; regression suite.

Book IV gate: Ask CEREBUS answers launch golden set with correct model/claim/evidence routing and zero intentional internal-method leakage.

# BOOK V — INDICATOR VAULT & OPERATOR INTERFACE
Goal: licensed access to CEREBUS implementations and usable model surfaces.

## Bloc V.1 Indicator Registry
Chapters: indicator identity/version; supported markets; model links; status; TradingView/source metadata.

## Bloc V.2 Vault UX
Chapters: browse/filter; model detail; version history; manual/download/access instructions; entitlement.

## Bloc V.3 Market Dashboards
Chapters: L3 destination; L2 path; L1 execution; configurable panels; level toggles/colors/positions; status/evidence labels.

## Bloc V.4 Operator Workspace
Chapters: active state; setup eligibility; no-go; evidence drawer; historical comparison; saved preferences.

## Bloc V.5 Release Pipeline
Chapters: candidate->validated->released; changelog; rollback; compatibility; user notification.

Book V gate: users can identify exactly what an indicator implements, its evidence/status and version; revoked access removes protected vault/operator surfaces.

# BOOK VI — LICENSING / ACCOUNTS / WHOP
Goal: sell access without coupling FORGE identity or IP to Whop.

Reference: larger-lab/master historical MAD LABS Whop store audit.

## Bloc VI.1 Internal Product Catalog
Chapters: products; plans; billing cadence metadata; capabilities; exposure bundles; lifecycle; pricing config.

## Bloc VI.2 License & Entitlement Domain
Chapters: licenses; seats; start/end; grace; revocation; plan->capability mapping; account entitlements; audit history.

## Bloc VI.3 Whop Adapter
Chapters: provider customer/product/plan mapping; checkout handoff; verified webhooks; subscription lifecycle; idempotency; retries; signature verification.

## Bloc VI.4 Reconciliation
Chapters: event ledger; entitlement projection; periodic provider reconciliation; missed webhook recovery; duplicate/out-of-order events; manual admin correction.

## Bloc VI.5 Account/Billing UX
Chapters: current plan; access/features; upgrade/downgrade/cancel handoff; billing state; license terms acknowledgement.

## Bloc VI.6 Legal/IP Controls
Chapters: license grant; ownership reservation; acceptable use; account sharing; revocation; disclaimers; privacy/terms hooks; attorney-review placeholders.

## Bloc VI.7 Commerce Tests
Chapters: fake Whop provider; lifecycle matrix; webhook adversarial tests; provider outage; replacement-provider contract; entitlement security.

Book VI gate: complete subscription lifecycle can be simulated without Whop; Whop adapter can be removed without changing core entitlement semantics.

# BOOK VII — PUBLISHING & RESEARCH ENGINE
Goal: continuously convert new CEREBUS research into governed subscriber intelligence.

## Bloc VII.1 Research Intake
Chapters: artifact ingest; metadata; study registration; experimental status; source hashing.

## Bloc VII.2 Evidence Pipeline
Chapters: claim proposal; evidence card generation; negative evidence; small-N flags; reproduction/OOS; contradiction routing.

## Bloc VII.3 Canonical Promotion
Chapters: review queue; promote/park/supersede; versioning; downstream invalidation; release notes.

## Bloc VII.4 Publishing
Chapters: CEREBUS Files; research notes; model updates; infographics; subscriber summaries; public excerpts.

## Bloc VII.5 Retrieval Rebuild
Chapters: incremental compile; embeddings; structured index; cache invalidation; version pinning.

## Bloc VII.6 Research Admin
Chapters: dashboards; provenance graph; coverage/gaps; unresolved conflicts; launch/release approvals.

Book VII gate: a new research artifact can travel intake->claim/evidence->review->canonical promotion->retrieval/publishing without manual database surgery.

# BOOK VIII — SECURITY / HARDENING / LAUNCH
Goal: prove FORGE is safe, recoverable, observable and commercially operable.

## Bloc VIII.1 Threat Model
Chapters: corpus exfiltration; prompt injection; entitlement bypass; webhook fraud; credential abuse; scraping; admin compromise.

## Bloc VIII.2 Application Security
Chapters: secrets; auth hardening; CSRF/CORS; rate limits; input validation; dependency/SAST; secure headers.

## Bloc VIII.3 AI/Retrieval Security
Chapters: exposure prefilter; prompt injection defense; quote/extraction limits; systematic-enumeration detection; internal-code exclusion; red-team suite.

## Bloc VIII.4 Reliability
Chapters: backups; restore drill; provider outage; queue/retry; graceful degradation; migration rollback; disaster recovery.

## Bloc VIII.5 Performance/Cost
Chapters: retrieval latency; DB indexes; caching; LLM budgets; load test; concurrency; cost ceilings.

## Bloc VIII.6 Launch Operations
Chapters: Railway environments; domain/TLS; Whop production mapping; analytics; support/admin runbooks; incident response; launch checklist.

## Bloc VIII.7 Acceptance & Evidence
Chapters: end-to-end test; security test; entitlement test; corpus QA; model QA; launch evidence pack; final ratification.

Book VIII gate: restore drill passes; unauthorized corpus extraction tests fail closed; subscription lifecycle and Ask CEREBUS E2E pass; launch evidence signed off.

# Dependency order
I -> II -> III/VI foundations -> IV -> V -> VII -> VIII.
Book VI domain model may begin after II; production Whop activation waits for policy/identity.
Book VII uses Book I governance and Book II persistence.
Book V consumes III/IV and VI entitlements.

# Build discipline
Each Bloc gets:
PLAN.md
ACCEPTANCE.md
implementation commits
tests
EVIDENCE.md
ratification commit.
No amend/squash of evidence ladder during controlled build unless build policy explicitly changes.

# Immediate planning sequence
1 detail Book I
2 detail Book II
3 detail Book III
4 detail Book IV
5 detail Book V
6 detail Book VI using legacy Whop reference
7 detail Book VII
8 detail Book VIII
9 master dependency/acceptance audit
10 freeze planning head and issue agent execution prompt.
