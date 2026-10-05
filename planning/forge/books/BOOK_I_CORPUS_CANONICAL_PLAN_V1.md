# BOOK I PLAN — CORPUS & CANONICAL KNOWLEDGE

Status: DETAILED PLANNING V1
Parent: GLX_FORGE_MASTER_BUILD_PLAN_V1

## Book objective
Produce a deterministic, versioned CEREBUS knowledge substrate from the recovered corpus. Book I owns truth representation, not live market calculation, LLM generation, commerce or UI.

## BLOC I.1 — CANONICAL REGISTRY KERNEL
### Ch I.1.1 IDs and enums
Implement stable IDs for MODEL/CLAIM/EVIDENCE/SETUP/DOCTRINE/TERM/LINEAGE/ARTIFACT and controlled statuses/exposure/layers.
Tests: uniqueness, invalid enums, immutable identity.

### Ch I.1.2 Object schemas
Machine-readable schemas matching current canonical MD contracts.
Tests: all existing seven model cards and current evidence/setup cards parse.

### Ch I.1.3 References
Parent/child and model->claim->evidence->source constraints.
Tests: dangling IDs fail; historical objects may be explicitly partial but not silently dangling.

### Ch I.1.4 Lifecycle
Draft/candidate/validated/OOS/research/historical/parked/superseded/falsified/no-go transitions.
Tests: illegal promotion fails.

### Ch I.1.5 Conflict identity
Encode comparison key: market,event,condition,clock,horizon,tolerance,eligibility,implementation semantics.
Tests: mismatched claims remain parallel rather than contradiction.

Acceptance I.1: canonical objects validate deterministically and current hand-authored corpus is representable without schema exceptions.

## BLOC I.2 — SOURCE & PROVENANCE FABRIC
### Ch I.2.1 Artifact registry
PDF/MD/Pine/CSV/XLSX/visual/notebook/conversation-derived.
### Ch I.2.2 Content identity
Hashes, source generation, version, repository/library locator, materialization status.
### Ch I.2.3 Object provenance edges
Artifact supports/defines/implements/visualizes/supersedes object.
### Ch I.2.4 Visual semantics
Infographics allowed as teaching/relationship evidence, never automatic statistical proof.
### Ch I.2.5 Incomplete source states
LOCATED,READ,VERIFIED,MATERIALIZED,MISSING,PARTIAL,CONVERSATION_DERIVED.
### Ch I.2.6 Provenance audit
Generate source coverage and orphan reports.

Acceptance I.2: every launch numerical claim can route to evidence and provenance; missing sources are explicit.

## BLOC I.3 — CANONICAL BACKFILL
### Ch I.3.1 EUR
Daily News+Rekey, Weekly, Higher Order, ILM/MAE, supporting claims.
### Ch I.3.2 XAU
Game/freeze, scientific promotions, operator setup.
### Ch I.3.3 BTC
Tracker and native tiers; BTC Game remains separate ACTIVE_RESEARCH/NOT_LOCATED where applicable.
### Ch I.3.4 Fib
R11-R15 lineage, Range Birth, Rekey setup, anchor negative evidence.
### Ch I.3.5 JPY
Carry roles, native tiers, basket evidence; manual/automation parity state.
### Ch I.3.6 Foundational doctrine
Tier/AU, P90 lineage, manual ST, clocks, range-left, first delivery, negative evidence.
### Ch I.3.7 Historical archive map
Base80, Wednesday, Afternoon, Atomic, V4, old Markov, workbook.
### Ch I.3.8 Research Lab
Oil, Hypergraph, optional WMA/ATR, optional SPX.

Acceptance I.3: launch corpus coverage report has no UNKNOWN launch-critical family.

## BLOC I.4 — RETRIEVAL OBJECT COMPILER
### Ch I.4.1 Compiler
Canonical object -> normalized retrieval object.
### Ch I.4.2 Structured exact fields
Numbers, tiers, levels, versions, N, status, relationships.
### Ch I.4.3 Safe semantic text
Generate concise explanatory text stripped of INTERNAL_METHOD/INTERNAL_CODE.
### Ch I.4.4 Alias resolver
Historical aliases map to canonical terms with generation retained.
### Ch I.4.5 Exposure compiler
Stamp retrieval objects with entitlement/exposure metadata.
### Ch I.4.6 Incremental rebuild
Changed canonical object invalidates/rebuilds dependent retrieval objects.
### Ch I.4.7 Determinism
Same canonical version -> same retrieval payload/hash.

Acceptance I.4: compiler produces stable launch retrieval corpus; internal-only fields absent from subscriber-safe output.

## BLOC I.5 — CORPUS QA & FREEZE
### Ch I.5.1 Orphan checks
### Ch I.5.2 Unsupported number checks
### Ch I.5.3 Cross-generation leakage checks
### Ch I.5.4 Exposure leakage checks
### Ch I.5.5 Golden fixtures
Questions/expected object routes for seven launch models.
### Ch I.5.6 Coverage dashboard/report
### Ch I.5.7 Book freeze manifest
Record schema versions, object counts, hashes, known gaps and exclusions.

Acceptance I.5 / BOOK I DONE:
- 100% launch model cards schema-valid.
- 100% launch numerical claims either evidence-linked or explicitly non-promoted.
- zero forbidden exposure objects in subscriber retrieval build.
- zero dangling launch references.
- deterministic rebuild passes.
- known research gaps remain labeled, not invented.
- freeze manifest committed.

## Book I exclusions
No live price feed.
No LLM.
No Whop.
No billing.
No frontend.
No autonomous trading.
No broad recovery restart.

## Agent evidence requirements
Every Bloc ends with test command/output, changed-file inventory, object counts, unresolved gaps and a ratification artifact.
