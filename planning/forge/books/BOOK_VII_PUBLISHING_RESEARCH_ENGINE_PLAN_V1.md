# BOOK VII PLAN — PUBLISHING & RESEARCH ENGINE

Status: DETAILED PLANNING V1
Date: 2026-10-05
Parent: GLX_FORGE_MASTER_BUILD_PLAN_V1
Depends on: Books I-VI
Feeds: Book VIII and continuous post-launch CEREBUS evolution

## Book objective
Build the governed pipeline that turns new CEREBUS research into durable evidence, canonical knowledge, retrieval objects, publications and release candidates.

Book VII is how FORGE keeps learning without turning every notebook, backtest, conversation insight or infographic into product truth.

## Core law

RAW RESEARCH
-> INTAKE
-> STUDY IDENTITY
-> CLAIM PROPOSAL
-> EVIDENCE
-> REVIEW / FALSIFICATION / OOS
-> CANONICAL DECISION
-> RETRIEVAL REBUILD
-> PUBLICATION / RELEASE CANDIDATE
-> AUDITABLE CHANGE

Publishing is downstream of evidence status.
A compelling result may be published as research without being promoted to canonical or operator status.

---

# BLOC VII.1 — RESEARCH INTAKE & STUDY REGISTRY

## Objective
Give every new experiment/artifact a durable identity before conclusions are promoted.

### Ch VII.1.1 Intake object
Fields:
research_id
title
market(s)
question/hypothesis
researcher/agent
created_at
source artifacts
data sources
clock/session assumptions
code/config refs
status
related models/claims.

### Ch VII.1.2 Artifact ingestion
Supported lineage classes:
CSV/parquet/data extract
notebook
script
Pine
MD/TXT
PDF/DOCX
XLSX
visual/infographic
conversation-derived note
external reference.

Ingestion records identity/hash/locator; it does not make content authoritative.

### Ch VII.1.3 Study status
IDEA
PLANNED
RUNNING
RESULTS_AVAILABLE
REVIEW
REPRODUCTION_REQUIRED
OOS_PENDING
ACCEPTED_RESEARCH
PARKED
FALSIFIED
SUPERSEDED
ABANDONED.

### Ch VII.1.4 Research question contract
Before promotion-quality testing, specify:
population
event definition
conditioning
clock
horizon
target/outcome
tolerance
eligibility/exclusions
metrics
intended layer.

Exploration may begin looser but cannot masquerade as confirmatory evidence.

### Ch VII.1.5 Data identity
Record:
provider/source
market
period
granularity
timezone/DST semantics
transformations
missing-data policy
sample exclusions
dataset hash/version where possible.

### Ch VII.1.6 Code/config identity
Record executable code/config hash, runtime/library versions where material, parameters and seed for stochastic work.

A result without reproducible implementation identity gets limited evidence status.

### Ch VII.1.7 Conversation-derived research
Insights originating in chat can enter as IDEA/RESEARCH_NOTE with conversation provenance.
They require evidence before numerical promotion.

### Ch VII.1.8 Visual intake
Infographics can preserve:
historical semantics
relationships
operator teaching
old constants/version clues.

They are not independent statistical proof.

### Ch VII.1.9 Duplicate/related study detection
Link reruns, variants, OOS extensions and superseding studies rather than spawning disconnected claims.

### Ch VII.1.10 Intake tests
- missing clock
- missing data period
- duplicate artifact
- changed code hash
- conversation-only claim
- infographic-only statistic
- stochastic result without seed/config.

Acceptance VII.1:
- every serious new study has identity before promotion
- data/code/clock lineage explicit
- weak-source artifacts remain usable without being promoted
- variants/reruns link to lineage.

---

# BLOC VII.2 — CLAIM & EVIDENCE PIPELINE

## Objective
Transform results into exact, reviewable claims instead of free-floating headline statistics.

### Ch VII.2.1 Claim proposal
Proposed claim includes Book I claim identity:
market
event definition
conditioning event/population
clock origin
horizon
tolerance
numerator/denominator
eligibility
period
calculation type
source generation
status.

### Ch VII.2.2 Evidence-card generation
Generate draft Evidence Card from study output:
claim ID
N
metric/result
period
data identity
calculation
implementation identity
validation type
limitations
does-not-support
source refs.

Human/agent review required before canonical promotion.

### Ch VII.2.3 Result-origin taxonomy
Enforce:
EMPIRICAL_BACKTEST
FORWARD_OOS
LIVE_OPERATOR
SIMULATION
MONTE_CARLO_RESAMPLE
DERIVED_ALGEBRA
MANUAL_CLAIM
HISTORICAL_REPORT
NEGATIVE_EVIDENCE.

Never collapse simulation into empirical validation.

### Ch VII.2.4 Negative evidence
First-class:
failed hypothesis
degraded OOS
overgeneration
poor expectancy
automation parity failure
unstable calibration
no incremental value
contradiction.

Negative evidence can block promotion.

### Ch VII.2.5 Small-N rules
Thresholds can be model/research-specific, but every small cell displays N and receives appropriate flag.
No hiding tiny samples behind percentages.

### Ch VII.2.6 Reach vs execution metrics
Keep separate:
touch/reach
first delivery
target-before-stop
WR
expectancy
MAE/MFE
time-to-delivery
conditional promotion.

### Ch VII.2.7 OOS/reproduction links
Evidence graph:
discovery -> reproduction -> OOS -> live/operator evidence.

A later failure does not erase the original artifact; it changes current disposition.

### Ch VII.2.8 Contradiction candidate
Only open direct contradiction when identity sufficiently matches.
Otherwise classify population/generation/clock difference.

### Ch VII.2.9 Evidence QA
Automated checks:
percentage numerator/denominator consistency
N consistency
period ordering
missing source
missing implementation
status/evidence-type mismatch
unsupported causal wording
layer laundering.

### Ch VII.2.10 Evidence review queue
Reviewer actions:
ACCEPT AS RESEARCH
REQUEST REPRODUCTION
REQUEST OOS
PARK
FALSIFY
SEND TO CANONICAL REVIEW.

Acceptance VII.2:
- numerical research can be traced to exact evidence identity
- negative evidence preserved
- simulation/manual/historical claims cannot auto-promote
- execution metrics cannot be substituted for reach statistics.

---

# BLOC VII.3 — CANONICAL PROMOTION & CHANGE CONTROL

## Objective
Decide what CEREBUS now believes while preserving historical lineage.

### Ch VII.3.1 Promotion proposal
Bundle:
proposed canonical object changes
claims/evidence
affected models/setups/terms
reason
expected downstream effects
risk/compatibility.

### Ch VII.3.2 Promotion classes
NEW
CALIBRATION_UPDATE
EVIDENCE_UPDATE
STATUS_CHANGE
MODEL_RULE_CHANGE
SETUP_CHANGE
TERMINOLOGY_CROSSWALK
SUPERSESSION
FALSIFICATION.

### Ch VII.3.3 Review gates
Check:
evidence sufficiency
OOS/reproduction where required
negative evidence
sample size
clock/data identity
implementation parity
cross-asset transfer claim
product exposure
operator impact.

### Ch VII.3.4 Canonical decision
PROMOTE
PROMOTE_WITH_FLAG
RESEARCH_ONLY
PARK
SUPERSEDE
FALSIFY
NO_GO
REPRODUCTION_REQUIRED.

Decision includes rationale and reviewer/agent evidence.

### Ch VII.3.5 Supersession
New canonical object points to prior version.
Old version remains historical/queryable.

Do not mutate history to make current model look inevitable.

### Ch VII.3.6 Downstream invalidation graph
Promotion can invalidate/rebuild:
retrieval objects
Book III runtime config
setup cards
indicator mappings
manuals
dashboards
Ask golden answers
publications.

### Ch VII.3.7 Breaking-change detection
Examples:
tier boundary changes
session clock changes
setup invalidation changes
Range Birth rule changes
layer ownership changes.

Require explicit release handling.

### Ch VII.3.8 Model freeze
Frozen families such as XAU require elevated change path:
research result -> proposal -> explicit unfreeze/version bump -> tests -> refreeze.

### Ch VII.3.9 Manual-vs-automation distinction
Research can validate manual/operator rules without granting automation approval.
ST remains key regression fixture for this rule.

### Ch VII.3.10 Promotion ledger
Append:
decision ID
proposal
before/after hashes
evidence
decision
reason
affected objects
approver/date.

Acceptance VII.3:
- canonical changes cannot happen from raw result alone
- superseded truth remains inspectable
- downstream impact known before promotion
- frozen models require explicit version action
- manual validity never implies automation parity.

---

# BLOC VII.4 — CEREBUS FILES & PUBLICATION ENGINE

## Objective
Turn governed research into readable subscriber/public material with correct status and exposure.

### Ch VII.4.1 Publication object
Fields:
publication_id
title
type
audience
status
exposure
canonical/model links
claim/evidence links
source research
version
published_at
supersedes.

### Ch VII.4.2 Publication types
CEREBUS FILE
RESEARCH NOTE
MODEL UPDATE
EVIDENCE UPDATE
OPERATOR NOTE
QUICK START
INFOGRAPHIC
CHANGELOG
PUBLIC EXCERPT.

### Ch VII.4.3 Audience/depth
PUBLIC
LIBRARY
PRO
RESEARCH/INSTITUTIONAL.

Publication access maps to capabilities, not Whop IDs.

### Ch VII.4.4 Research publication vs canonical statement
Every publication visibly distinguishes:
validated/canonical
experimental
research flag
historical
negative evidence
inference.

A Research Note may discuss an unpromoted idea without changing Book I truth.

### Ch VII.4.5 Automated draft assistance
FORGE may generate draft:
summary
methods
results
limitations
operator implications
claim/evidence references.

Draft generation cannot invent numbers or status.

### Ch VII.4.6 Human/agent review
Check:
numbers
N
status
source links
layer semantics
no overclaim
exposure
visual consistency.

### Ch VII.4.7 Infographic pipeline
Infographic specification is generated from canonical/evidence payload.
Rendered visual is linked back to source claims/version.

If evidence changes, visual becomes OUTDATED until regenerated/reviewed.

### Ch VII.4.8 Public excerpt
Generate deliberately reduced public version.
No subscriber/internal leakage.
Public marketing cannot use stronger certainty than source publication.

### Ch VII.4.9 Corrections
Correction creates new version/notice.
Do not silently edit material numerical conclusions without history.

### Ch VII.4.10 Publication archive/search
Users can find current and historical material according to entitlement/status.

Acceptance VII.4:
- publication status cannot outrun evidence
- every material number maps to claim/evidence
- outdated visuals detected
- public excerpts obey exposure
- corrections preserve history.

---

# BLOC VII.5 — RETRIEVAL & INDEX REBUILD PIPELINE

## Objective
Propagate approved knowledge changes into Ask CEREBUS safely and deterministically.

### Ch VII.5.1 Change detector
Canonical/published object change produces dependency set.

### Ch VII.5.2 Structured index rebuild
Update exact fields/relationships first.
Structured index is authoritative for IDs/status/numbers.

### Ch VII.5.3 Semantic object rebuild
Regenerate safe semantic text and embeddings only for affected objects where possible.

### Ch VII.5.4 Version pinning
Each retrieval build has:
build_id
canonical head/hash
compiler version
embedding provider/model
object counts
created_at
status.

### Ch VII.5.5 Staging index
New build evaluated before promotion to active.

### Ch VII.5.6 Retrieval regression
Run affected Book IV golden questions:
correct objects
correct numbers
negative evidence
status
entitlement.

### Ch VII.5.7 Cache invalidation
Invalidate Ask/model/publication caches tied to changed objects.

### Ch VII.5.8 Rollback
Switch active retrieval build back without changing canonical history.

### Ch VII.5.9 Orphan/stale detector
Find:
retrieval object referencing superseded claim as current
missing evidence
outdated semantic summary
wrong exposure
orphan embedding.

### Ch VII.5.10 Build evidence
Record counts/diffs/test results/hash.

Acceptance VII.5:
- approved change propagates deterministically
- staging prevents bad index going live
- rollback works
- stale/superseded retrieval cannot silently remain authoritative.

---

# BLOC VII.6 — RESEARCH ADMIN, GOVERNANCE & CONTINUOUS LEARNING

## Objective
Give the operator/research team a control room for what CEREBUS knows, questions and is testing.

### Ch VII.6.1 Research dashboard
Views:
active studies
review queue
OOS pending
reproduction required
negative evidence
contradictions
parked/falsified
recent promotions.

### Ch VII.6.2 Corpus coverage
By market/model:
source coverage
claim coverage
evidence coverage
implementation parity
publication coverage
retrieval coverage.

### Ch VII.6.3 Gap registry
Explicit unresolved items:
missing source
missing exact definition
small N
no OOS
implementation not parity-safe
artifact not located
unresolved contradiction
automation gap.

### Ch VII.6.4 Research lineage graph
Navigate:
idea -> study -> evidence -> canonical decision -> model version -> indicator -> publication.

### Ch VII.6.5 Ask CEREBUS feedback intake
Collect governed signals:
question
retrieval route
user correction/feedback where allowed
reviewer preferred answer
failure category.

Feedback is not automatically truth.

### Ch VII.6.6 Evaluation dataset growth
Reviewed failures/corrections can become Book IV golden fixtures.

### Ch VII.6.7 Future small-model dataset
Only reviewed/governed examples may enter a future training candidate dataset:
query
authorized context IDs
preferred answer
error labels
status.

No training decision in Book VII.

### Ch VII.6.8 Research prioritization
Rank work by:
launch/product impact
evidence gap
contradiction severity
usage/questions
model coverage
expected information gain.

Do not optimize only for exciting positive findings.

### Ch VII.6.9 Agent handoff
Generate bounded research task:
question
source scope
definitions
tests
required outputs
promotion forbidden until review.

### Ch VII.6.10 Governance audit
Periodic report:
what changed
why
evidence
who/what approved
affected users/models
open risks.

Acceptance VII.6:
- team can see what is known vs unresolved
- Ask feedback improves evaluations without auto-training truth
- research tasks inherit exact definitions
- promotion history reconstructable.

---

# CONTINUOUS CEREBUS RESEARCH LOOP

1 OBSERVE anomaly/question.
2 REGISTER study.
3 DEFINE event/population/clock/outcome.
4 RUN exploration.
5 RECORD positive AND negative results.
6 CREATE claim/evidence candidates.
7 REPRODUCE/OOS when required.
8 REVIEW.
9 PROMOTE/PARK/FALSIFY.
10 REBUILD retrieval.
11 UPDATE runtime/release candidate if needed.
12 PUBLISH at correct exposure/status.
13 MONITOR operator/use feedback.
14 Feed new questions back to step1.

This loop is the subscription moat: FORGE is not a folder of static PDFs. It is governed, continuously revised market intelligence.

---

# EXAMPLE RESEARCH FLOWS

## EUR new Daily calibration
New data -> study -> compare tier boundaries/multipliers -> OOS -> evidence -> calibration update proposal -> breaking-change check -> new model/calibration version -> Book III fixtures -> retrieval -> indicator release candidate -> CEREBUS File.

## XAU 132->168
Study may find attractive completion rate.
Because frozen doctrine currently says no automatic promotion:
result remains research until evidence/review explicitly changes model.
No dashboard rule changes from notebook result alone.

## BTC Game
Dedicated research can continue.
Tracker remains canonical product family.
BTC Game receives own study/model/setup identities.
Only after sufficient artifact/evidence/package exists can it enter launch model registry.

## ST
New automation work, if ever commissioned, is a separate parity study.
Manual/operator strategy status is not overwritten by automation failure/success without explicit review.

---

# BOOK VII SECURITY / INTEGRITY INVARIANTS

1. Uploaded artifact != trusted claim.
2. Conversation statement != verified evidence.
3. Infographic != statistical proof.
4. Simulation != empirical backtest.
5. Positive result != canonical promotion.
6. Publication != canonical promotion.
7. Canonical promotion != automation approval.
8. User feedback != truth.
9. Semantic embedding != authority.
10. Superseded evidence remains historical.
11. Negative evidence cannot be deleted to improve product appearance.
12. Internal research exposure remains policy-controlled.
13. Agent cannot self-promote its own result without review gate.
14. Retrieval build cannot change canonical source objects.

---

# BOOK VII ACCEPTANCE / RATIFICATION GATE

Book VII is DONE only when:

## Intake
- artifact/study identities work
- data/clock/code provenance represented
- conversation/visual weak evidence classified correctly.

## Evidence
- claim/evidence draft pipeline
- negative evidence
- small-N
- result-origin separation
- contradiction identity checks.

## Promotion
- review decision workflow
- supersession
- downstream impact graph
- frozen-model change gate
- append promotion ledger.

## Publishing
- CEREBUS File/research/update/infographic flows
- exposure controls
- evidence-linked numbers
- corrections/version history.

## Retrieval
- staged rebuild
- Book IV regression
- rollback
- stale/orphan detection.

## Admin
- coverage/gap dashboards
- lineage graph
- Ask feedback -> reviewed evaluation fixture path
- bounded research-agent handoff.

## End-to-end proof
Run at least:
A positive research result that is promoted.
A positive result that remains research-only.
A negative/falsified result.
A superseding result.
Each must propagate correctly through evidence, publication and retrieval.

## Evidence pack
Each Bloc produces PLAN, ACCEPTANCE, implementation commits, tests, EVIDENCE, known gaps and ratification.

Final Book VII record:
study schema version
evidence pipeline version
promotion policy version
publication schema version
retrieval build/compiler version
active retrieval build hash
coverage/gap report
E2E research-loop evidence
known exclusions
ratification commit.

---

# BOOK VII EXCLUSIONS

Do NOT:
- automatically promote statistically attractive findings
- train/fine-tune a CEREBUS model yet
- let agents modify canonical truth without review
- restart broad archaeology by default
- turn every research artifact into subscriber content
- delete negative evidence
- silently update published statistics
- let publications define Book III runtime behavior directly.

Recovery is now exception-based: targeted source recovery occurs only when canonicalization/research finds a material unresolved definition, claim or lineage gap.

---

# RECOMMENDED IMPLEMENTATION ORDER

1 VII.1 Intake/Study Registry
2 VII.2 Claim/Evidence Pipeline
3 VII.3 Promotion Workflow
4 VII.5 Retrieval Rebuild
5 VII.4 Publishing
6 VII.6 Research Admin/Feedback
7 four E2E research-loop scenarios
8 evidence pack
9 Book VII ratification/freeze.

Evidence governance comes before publishing UI. The product should become easy to publish only after it becomes hard to accidentally lie.

# HANDOFF TO BOOK VIII

Book VIII receives a system capable of:
- deterministic canonical knowledge
- live model intelligence
- grounded Ask CEREBUS
- licensed operator UI
- commerce/entitlements
- governed continuous research/publishing.

Book VIII's job is to attack it, restore it, load it, secure it, deploy it and decide whether it is actually launchable.
