# GLX FORGE — MASTER DEPENDENCY & ACCEPTANCE AUDIT V1

Status: PLANNING INTEGRATION AUDIT — PASSED WITH DEFERRED IMPLEMENTATION PROOFS
Date: 2026-10-05
Scope: Books I-VIII
Branch: forge

## 1. Purpose

Audit the eight detailed Book plans as one executable program before planning freeze and agent handoff.

This audit asks:
1. Does every runtime truth have one owner?
2. Are cross-Book contracts explicit?
3. Is there a build order without circular dependency?
4. Does every Bloc have an acceptance gate?
5. Are launch-critical dependencies defined?
6. Can an implementation agent work Bloc-by-Bloc without inventing architecture?

Planning completeness is not implementation proof. Any test requiring running code, current provider contracts, production infrastructure, legal review, OOS/reproduction or security evidence remains a build/launch gate.

## 2. Audited Books

I — Corpus & Canonical Knowledge
II — FORGE Core / Platform
III — CEREBUS Market Intelligence
IV — Ask CEREBUS
V — Indicator Vault & Operator Interface
VI — Licensing / Accounts / Whop
VII — Publishing & Research Engine
VIII — Security / Hardening / Launch

All eight have explicit objective, Blocs, chapter-level work, invariants, exclusions, acceptance/ratification gates and recommended execution order.

## 3. Single-Owner Truth Matrix

| Truth / Capability | Authoritative Owner | Consumers |
|---|---|---|
| Canonical object identity/status | Book I | III, IV, V, VII, VIII |
| Claim/evidence truth | Book I | III, IV, V, VII |
| Exposure metadata | Book I | II policy, IV, V, VII |
| User/account identity | Book II | IV, V, VI, VIII |
| Runtime authorization policy | Book II | IV, V, VI, VII |
| Provider ports | Book II | IV LLM, VI commerce, infrastructure |
| Current market measurements/state | Book III | IV, V, VIII |
| Setup eligibility/no-go | Book III | IV, V |
| Natural-language explanation | Book IV | V |
| Numerical answer validation | Book IV | V, VIII |
| Indicator release identity | Book V | VII publishing/release, VIII |
| Operator UI presentation/preferences | Book V | users |
| Product/plan/capability catalog | Book VI | II policy, V UI |
| License/entitlement projection | Book VI | II policy |
| Provider commerce state normalization | Book VI | internal license domain |
| Study/research identity | Book VII | I promotion pipeline |
| Canonical promotion workflow | Book VII governance over Book I objects | I, III, IV, V |
| Publication identity | Book VII | V/library surfaces |
| Retrieval build promotion | Book VII | IV |
| Security/launch decision | Book VIII | whole program |

Audit result: no runtime truth requires two independent authoritative implementations.

## 4. Critical Cross-Book Contracts

### C01 — Canonical Registry Contract
Producer: I
Consumers: III, IV, V, VII
Must expose stable IDs, versions, status, exposure, relationships and source/provenance.

### C02 — Claim/Evidence Contract
Producer: I; governed updates: VII
Consumers: IV primarily; III/V where evidence status is displayed.
Numerical research claims cannot bypass it.

### C03 — Retrieval Object Contract
Producer/compiler definition: I
Build/promotion: VII
Consumer: IV.
Structured fields remain authority; semantic text is support.

### C04 — Identity/Principal Contract
Producer: II
Consumers: IV-VIII.
External provider identity is mapped, never authoritative internal PK.

### C05 — Authorization Decision Contract
Producer: II
Inputs: principal/account + VI entitlements + I exposure/status + capability/context.
Consumers: IV/V/VII.
Deny-by-default and pre-provider filtering.

### C06 — Provider Port Contract
Producer: II.
Concrete adapters: IV OpenRouter, VI Whop.
Domain cannot import provider implementations.

### C07 — Intelligence Snapshot Contract
Producer: III
Consumers: IV/V.
Includes model/version, as_of/data cutoff, quality, layer/state/path/levels/setup/no-go/evidence refs.

### C08 — Setup Contract
Canonical definition: I Setup Card
Runtime eligibility: III
Explanation: IV
Rendering: V.
No consumer may invent eligibility.

### C09 — Ask CEREBUS Contract
Producer: IV
Consumer: V.
Includes answer mode, text/structured sections, evidence/canonical refs, current snapshot refs, warnings, versions.

### C10 — Capability Contract
Definition/catalog: VI
Evaluation: II
Rendering: V
Ask depth: IV.
UI plan labels never authorize access.

### C11 — Commerce Event Contract
Port: II
Adapter/normalization/ledger: VI.
Checkout success is not entitlement.

### C12 — Research Promotion Contract
Producer/workflow: VII
Mutates/version-bumps canonical objects through Book I rules.
Must trigger downstream impact/rebuild, never direct runtime mutation.

### C13 — Release Contract
Indicator/UI release: V
Research/model change source: VII
Launch/security approval: VIII.

### C14 — Audit/Observability Contract
Foundation: II
Domain events: III/IV/VI/VII
Launch review: VIII.
Protected payloads are minimized/redacted.

Audit result: all launch-critical cross-Book flows have an owning contract. Exact code schemas remain implementation deliverables, not planning gaps.

## 5. Dependency Graph

Foundation:
I.1-I.2 -> II.1-II.4

Knowledge:
I.3-I.5 -> III.1-III.3 -> III.4-III.6

Commercial foundation:
II identity/policy/ports -> VI.1-VI.2 -> VI.3-VI.4

Conversational:
I retrieval + II policy + III snapshots -> IV.1-IV.5 -> IV.6

Product UI:
III + IV + II policy -> V.1-V.4
VI capabilities plug into V entitlement gates.
V.5 release pipeline follows stable model/UI contracts.

Research loop:
I schemas + II persistence/policy -> VII.1-VII.3
VII.5 retrieval rebuild depends on IV evaluation contract.
VII.4 publishing can then feed V/library surfaces.
VII.6 closes feedback/governance loop.

Launch:
I-VII ratified implementation -> VIII.

There is a deliberate feedback loop VII -> I/III/IV/V, but it is a governed post-foundation change cycle, not a bootstrapping circular dependency.

## 6. Circular-Ownership Audit

### Potential cycle A: I <-> VII
Resolution:
I owns canonical schema/truth representation.
VII owns proposal/review/promotion workflow.
VII changes I only through versioned promotion contract.
PASS.

### Potential cycle B: II <-> VI
Resolution:
II owns generic policy/identity/provider ports.
VI owns commercial product/license/entitlement domain.
II evaluates VI capability output without knowing Whop.
PASS.

### Potential cycle C: III <-> IV
Resolution:
III calculates market truth.
IV explains it.
IV cannot feed prose back into III state.
PASS.

### Potential cycle D: IV <-> VII
Resolution:
IV evaluation/feedback supplies research signals.
VII may create reviewed fixtures/promotions.
Conversation output is never evidence by itself.
PASS.

### Potential cycle E: V <-> VI
Resolution:
V consumes capabilities; VI does not depend on UI labels.
PASS.

No blocking circular ownership found.

## 7. Acceptance Coverage Audit

Every Book contains a Book-level ratification gate.
Every planned Bloc contains acceptance criteria.

Cross-cutting acceptance coverage exists for:
- schema/identity
- provenance
- model determinism
- clock/data quality
- setup/no-go
- evidence integrity
- authorization
- entitlement/revocation
- provider replacement
- retrieval grounding
- AI hallucination/status laundering
- corpus extraction
- UI version compatibility
- research promotion
- backup/restore
- performance/cost
- legal review
- production GO/NO-GO.

PASS.

## 8. Deferred Proofs — EXPECTED, NOT PLANNING FAILURES

These cannot be honestly closed during planning:

1. Current Whop API/webhook contract validation.
2. Current OpenRouter production configuration/data-policy review.
3. Current Railway deployment capability/configuration validation.
4. Actual market-data provider/runtime contract.
5. Database migration/backup/restore measurements.
6. Performance/load/cost measurements.
7. Security scans/red-team evidence.
8. Exact implementation parity for model/indicator releases.
9. OOS/reproduction for research claims where still required.
10. Attorney review of terms/license/privacy/disclaimers.
11. Exact R15 Range Birth production eligibility if Fib execution is promoted.
12. Dedicated BTC Game evidence/artifact package if later promoted.
13. ST automation parity — intentionally NOT a launch requirement because ST is manual/operator only.
14. Production P90 automated performance claims require evidence/version identity if surfaced as current verified performance.

Each belongs to a named Book gate. None requires a ninth architecture Book.

## 9. Launch-Scope Truth

Launch-candidate model families:
- EUR Daily News+Rekey
- EUR Weekly
- EUR Higher Order
- XAU Game L1-L3
- BTC Daily/Weekly/Monthly Tracker
- JPY Carry Game as manual/operator family subject to implementation parity
- Fib/Range Birth as governed research/operator surface; execution promotion remains gated.

Research/historical surfaces remain explicitly classified:
- Oil active research
- Hypergraph research/negative evidence
- BTC Game active research/artifact not launch-canonical
- old P90/Atomic/Base80/Wednesday/Afternoon historical lineage unless exact current release/evidence says otherwise
- ST valid manual/operator framework; autonomous execution not approved.

No plan silently upgrades these statuses.

## 10. Program Build Order

The implementation agent should not build eight Books serially as giant monoliths. Execute dependency-ready Blocs.

### Phase A — Truth Kernel
I.1 Canonical Registry Kernel
I.2 Source & Provenance
II.1 Service Skeleton
II.2 Persistence

### Phase B — Identity, Policy & Corpus
II.3 Identity/Account/Session
II.4 Policy/Exposure
I.3 Canonical Backfill
I.4 Retrieval Compiler
I.5 Corpus QA/Freeze

### Phase C — Market Intelligence Foundation
III.1 Data/Clock
III.2 Measurements
III.3 Common Model Runtime + launch models
III.4 State/Path
III.5 Setup Engine
III.6 Intelligence API

### Phase D — Commercial Domain Foundation
VI.1 Catalog/Capabilities
VI.2 License/Entitlement
II.5 Provider Ports/Fakes
VI.4 Generic Event Ledger/Reconciler
II.6 Observability

### Phase E — Ask CEREBUS
IV.1 Interpreter
IV.2 Retrieval
IV.3 Context
IV.4 Fake LLM/Gateway
IV.5 Compiler/Validator
IV.6 Evaluation
then concrete OpenRouter adapter.

### Phase F — Product Surfaces
V.1 Indicator Registry
V.2 Vault
V.3 Dashboards
V.4 Operator Workspace
V.5 Release Pipeline

### Phase G — Commerce Provider
Current Whop contract audit
VI.3 Whop Adapter
VI.5 Account/License UX
VI.6 Legal/IP hooks
VI.7 commerce/security/replacement tests.

### Phase H — Continuous Research
VII.1 Intake
VII.2 Evidence
VII.3 Promotion
VII.5 Retrieval Rebuild
VII.4 Publishing
VII.6 Admin/Feedback.

### Phase I — Launch Hardening
VIII.1 -> VIII.7 in planned order.

Parallel work is permitted only where contracts are already frozen and commits/tests remain independently reviewable.

## 11. Agent Work-Packet Law

Each implementation packet must contain:
- exact Book/Bloc/Chapter scope
- inputs/contracts
- files expected to change
- explicit non-goals
- acceptance tests
- evidence artifacts
- migration/security implications
- dependency head/commit
- completion status.

Each Bloc follows:
PLAN -> ACCEPTANCE -> IMPLEMENT -> TEST -> EVIDENCE -> RATIFY.

Do not amend/squash/rebase evidence ladders unless governance explicitly changes this rule.
Do not silently repair unrelated files from another work packet.
Do not self-promote research/model status.

## 12. Change-Control Law After Planning Freeze

A build agent may:
- implement the frozen contract
- add tests/evidence
- make local implementation choices consistent with it.

A build agent may NOT silently:
- change ontology
- merge Model/Claim/Evidence/Setup
- change product exposure semantics
- change L1/L2/L3 ownership
- promote research
- automate ST
- invent BTC Game
- alter licensing doctrine
- make Whop/OpenRouter authoritative domain dependencies
- add brokerage execution.

If implementation reveals a true architecture conflict:
STOP affected packet -> write GAP/ADR -> identify impacted Books/contracts -> obtain/record decision -> version the plan if required -> resume.

## 13. Audit Findings

Blocking planning defects: NONE.

Nonblocking implementation risks:
- provider contracts can drift
- current source/data adapters need exact selection
- Fib Range Birth exact production gate remains research-dependent
- JPY code/evidence parity must be proven before stable release
- legal review cannot be simulated
- launch economics depend on measured LLM usage
- corpus extraction controls require empirical red-team tuning.

All have owners/gates.

## 14. Audit Decision

**MASTER PLANNING AUDIT: PASS**

The eight-Book architecture is sufficiently complete to freeze as the V1 implementation specification.

Required next artifacts:
1. AGENT_EXECUTION_HANDOFF_V1.md
2. PLANNING_FREEZE_MANIFEST_V1.md

The freeze manifest must pin the exact planning/canonical head and identify this audit plus all eight Book plans. Implementation begins from that frozen identity.
