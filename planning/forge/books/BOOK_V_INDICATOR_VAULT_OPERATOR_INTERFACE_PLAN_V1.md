# BOOK V PLAN — INDICATOR VAULT & OPERATOR INTERFACE

Status: DETAILED PLANNING V1
Date: 2026-10-05
Parent: GLX_FORGE_MASTER_BUILD_PLAN_V1
Depends on: Books I-IV
Feeds: Books VI, VII, VIII

## Book objective
Build the licensed visual/operator surface of GLX FORGE: Indicator Vault, model dashboards, operator workspace, release/version UX and Ask CEREBUS integration.

Book V renders CEREBUS intelligence. It does not invent a second model engine in the frontend.

## Core law
CANONICAL REGISTRY + BOOK III INTELLIGENCE + BOOK IV ASK CEREBUS + BOOK II POLICY
-> VIEW MODELS
-> ENTITLED UI
-> OPERATOR WORKSPACE

Frontend display state may transform presentation; it may not recompute or reinterpret canonical market truth.

---

# BLOC V.1 — INDICATOR REGISTRY & RELEASE IDENTITY

## Objective
Make every CEREBUS indicator a versioned product object tied to the exact models, evidence and operator status it implements.

### Ch V.1.1 Indicator identity
Fields:
indicator_id
name
version
status
supported markets
supported timeframes
parent model IDs
setup IDs
implementation locator
manual/artifact IDs
release channel
product exposure
compatibility.

Indicator ID is not a TradingView script name.

### Ch V.1.2 Implementation identity
Track:
source hash/version
Pine version/runtime
build/release date
model/calibration versions
known parity gaps
last verification.

A visual with the same title but different code is not assumed identical.

### Ch V.1.3 Indicator status
DRAFT
RESEARCH
CANDIDATE
RELEASED
DEPRECATED
PARKED
SUPERSEDED.

Separate indicator release status from model evidence status.

### Ch V.1.4 Model/setup mapping
Every plotted level/panel/signal family maps to:
measurement/model/setup object.

No orphan "magic line."

### Ch V.1.5 Manual/operator mapping
Each released indicator links:
quick-start
operator manual
model explanation
known limitations
evidence drawer
changelog.

### Ch V.1.6 Vault metadata
Search/filter:
asset
model family
layer
status
release
indicator type
manual/automation classification.

### Ch V.1.7 Historical indicators
P90/V4/ST lineage can be preserved as historical/operator material with explicit generation/status.
Do not surface old high-performance copy as current verified release marketing.

### Ch V.1.8 Registry tests
- duplicate IDs/versions fail
- released indicator requires model links
- source hash required
- unsupported market rejected
- superseded release points to replacement
- parked setup cannot appear as released automated signal.

Acceptance V.1:
- every launch indicator has exact implementation identity
- model/setup/evidence relationships navigable
- historical/current releases cannot be confused
- no unlabeled signal/level family.

---

# BLOC V.2 — LICENSED INDICATOR VAULT UX

## Objective
Give members a clean library of CEREBUS tools without exposing protected source or confusing research artifacts with released products.

### Ch V.2.1 Vault home
Cards/list show:
name
asset/model
purpose
status
version
layer
access state
last updated.

Avoid overwhelming users with research internals.

### Ch V.2.2 Indicator detail
Sections:
WHAT IT DOES
MODEL
WHAT IT PLOTS
HOW TO USE
STATUS/EVIDENCE
SUPPORTED MARKETS
VERSION
CHANGELOG
MANUAL
KNOWN LIMITATIONS.

### Ch V.2.3 Access/install flow
Depending on delivery mechanism:
TradingView invite/access instructions
licensed file/artifact access
web-native tool launch.

Never expose source code unless entitlement/product explicitly permits it.

### Ch V.2.4 Entitlement UX
Book II policy decides access.
UI states:
AVAILABLE
LOCKED
RESEARCH_ONLY
DEPRECATED
COMING_SOON if product catalog supports it.

Locked UI must not leak protected descriptions beyond approved marketing metadata.

### Ch V.2.5 Version history
Show meaningful release lineage:
current
previous
superseded
breaking calibration/model changes.

### Ch V.2.6 Manuals
Render/download entitled manuals and quick-starts with version match.
Warn when manual version does not match active indicator.

### Ch V.2.7 Search/filter
Asset/model/layer/use/status.
Search results pass exposure policy before rendering.

### Ch V.2.8 Evidence drawer
Concise evidence status:
validated/research/historical/small-N etc.
Deep evidence access depends on entitlement.

Do not market a path statistic as setup WR.

### Ch V.2.9 Vault analytics
Track privacy-conscious:
view
open manual
launch/install action
version selected
error/access denial.

### Ch V.2.10 Vault tests
- entitlement revocation
- direct URL access
- hidden version access
- search leakage
- manual mismatch
- deprecated indicator.

Acceptance V.2:
- users know what each indicator does and does not do
- protected content is inaccessible through UI/direct routes
- versions/manuals align
- evidence/status visible enough to prevent false certainty.

---

# BLOC V.3 — MARKET DASHBOARDS

## Objective
Render CEREBUS layers and current intelligence as configurable dashboards without collapsing them into fake confluence.

### Ch V.3.1 Dashboard shell
Common:
instrument
as-of/data cutoff
data quality
active model versions
session/clock
refresh state
Ask CEREBUS entry point.

### Ch V.3.2 Layer layout
Visually preserve:
L3 DESTINATION/SCALE
L2 PATH/OPPORTUNITY
L1 EXECUTION.

Users may collapse/reposition panels but semantic ownership remains.

### Ch V.3.3 Level renderer
Typed:
range boundaries
midpoint
decision node
rekey
promotion
target
invalidation
entry zone
no-go.

Each level has model/source identity.

### Ch V.3.4 Plot customization
User can toggle:
level families
labels
panels
dashboard position
line visibility
line style/width where supported
colors.

Customization changes appearance only.

### Ch V.3.5 Color system
Every plotted family has user-configurable color where technically supported.
Defaults accessible/readable.
Persist preferences per user/account.

### Ch V.3.6 State panel
Show:
tier
range size
consumed state
range-left
clock/state age
active path
quality/no-go
setup eligibility.

### Ch V.3.7 EUR dashboard
Higher Order L3
Weekly L2
Daily News+Rekey L1.
No forced confluence score.

### Ch V.3.8 XAU dashboard
L3/L2/L1 Game.
Quarter zones
promotions
active setup eligibility
explicit 132->168 nonautomatic state.

### Ch V.3.9 BTC dashboard
Daily/Weekly/Monthly Tracker.
Native Asian tier/AU/trigger
slot x tier range-left.
No BTC Game controls until canonical Game exists.

### Ch V.3.10 JPY dashboard
Basket role view:
USDJPY master
AUDJPY risk/execution
EURJPY referee.
Chosen pair local tier/setup.
No equal-vote gauge.

### Ch V.3.11 Fib dashboard
Range Birth status
active A/B anchor
family
coordinates
rekey/path.
UNRESOLVED anchor visibly blocks setup.

### Ch V.3.12 Responsive/accessibility
Desktop-first operator density with functional mobile/tablet summaries.
Keyboard navigation, readable contrast, non-color-only status cues.

### Ch V.3.13 Dashboard tests
- stale state
- no-go
- missing layer
- permission-limited evidence
- plot preference persistence
- color customization
- model version switch
- direct URL entitlement.

Acceptance V.3:
- dashboards are faithful views of Book III
- customization never changes model calculation
- all major plots can be toggled/customized
- L1/L2/L3 remain distinct
- no unsupported BTC Game/monolithic score appears.

---

# BLOC V.4 — OPERATOR WORKSPACE

## Objective
Create the daily working surface where a trader can inspect CEREBUS state, setups, evidence and Ask CEREBUS without turning FORGE into an order-execution platform.

### Ch V.4.1 Workspace layout
Primary zones:
MARKET SELECTOR
CURRENT READ
L3/L2/L1
ACTIVE LEVELS
SETUP WATCHLIST
NO-GO
ASK CEREBUS
EVIDENCE/WHY
HISTORY.

### Ch V.4.2 Current read
Short mechanical summary generated from Book III facts:
state
path
range-left
next relevant transition
quality.

If prose is AI-generated, route through Book IV and preserve citations/status.

### Ch V.4.3 Setup watchlist
States:
ELIGIBLE
WATCH
BLOCKED
UNRESOLVED.

Show side/location/trigger/invalidation/targets only when Setup Card permits.

### Ch V.4.4 Setup detail
Explain:
why eligible
what must happen
what invalidates
what targets mean
what evidence supports
manual/research/automation classification.

### Ch V.4.5 No-go center
No-go gets equal visual importance to setups.
Reason codes and what would resolve them.

### Ch V.4.6 Ask CEREBUS sidecar
Context-aware questions can include current instrument/model/snapshot ID.
User can change Beginner/Operator/Researcher mode within entitlement.

Ask CEREBUS still retrieves independently; UI context is a hint, not authority.

### Ch V.4.7 Evidence/Why drawer
Show compact claim/evidence path.
Researcher access may expand definitions/N/period/OOS.

### Ch V.4.8 Historical state
Browse prior snapshots/transitions when retained.
Historical replay uses pinned version if available.

### Ch V.4.9 Preferences
Save:
markets
dashboard layout
panel visibility
plot colors
default Ask depth
watchlist.

Preferences never alter model rules/calibration.

### Ch V.4.10 Notifications hooks
Define hooks for future:
state change
setup eligible
no-go cleared
indicator release.
Actual delivery/cadence can be later; no high-frequency compulsive alert design.

### Ch V.4.11 No brokerage execution
No Buy/Sell order button in V1.
No account-size/risk auto-sizing.
No broker credentials.

### Ch V.4.12 Workspace tests
- eligible->blocked transition
- entitlement downgrade
- stale snapshot
- Ask context mismatch
- historical replay
- preferences
- no-go prominence
- setup classification.

Acceptance V.4:
- operator can answer "what state, what path, what setup, what invalidates, what next?"
- workspace never implies execution occurred
- no-go is clear
- Ask answers can be traced to current snapshot/evidence
- user preferences cannot modify intelligence truth.

---

# BLOC V.5 — RELEASE, CHANGELOG & COMPATIBILITY PIPELINE

## Objective
Ship indicators/models/UI changes without silently changing what users are trading or studying.

### Ch V.5.1 Release object
Fields:
release_id
component
version
channel
model/calibration dependencies
source hash
migration/compatibility
release notes
status
approved_by/date.

### Ch V.5.2 Channels
RESEARCH
BETA
STABLE
HISTORICAL/ARCHIVE.

Entitlement may control channels.

### Ch V.5.3 Release gates
Before STABLE:
registry valid
tests pass
model/setup references valid
manual/version updated
evidence/status reviewed
security/access tests
rollback path.

### Ch V.5.4 Changelog
Classify:
model logic
calibration
bug fix
visual-only
documentation
evidence/status
breaking.

A visual-only change cannot claim model improvement.

### Ch V.5.5 Compatibility
Detect:
indicator expects model vX but API serves incompatible vY
manual mismatch
dashboard schema mismatch
saved preference migration.

Fail visibly rather than silently reinterpret.

### Ch V.5.6 Rollback
Rollback release pointer/UI/backend compatibility without deleting historical release evidence.

### Ch V.5.7 Deprecation
Warn -> freeze -> archive.
Historical users can inspect lineage if entitled; new users default current.

### Ch V.5.8 User release notices
In-app concise:
what changed
whether calculations changed
who is affected
whether action required.

### Ch V.5.9 Release audit
Record promotion, rollback, deprecation, approval and source hashes.

### Ch V.5.10 Release tests
- incompatible model/API
- rollback
- old manual
- entitlement channel
- deprecated direct URL
- visual-only update.

Acceptance V.5:
- every stable indicator/operator surface has reproducible release identity
- users can distinguish calculation change from cosmetic change
- rollback preserves audit/history
- incompatible versions fail visibly.

---

# BOOK V DESIGN SYSTEM / BRAND BOUNDARY

GLX FORGE should feel like an intelligence workstation, not a casino dashboard.

Principles:
- information hierarchy before decoration
- evidence/status visible
- no flashing profit language
- no fake certainty meters
- no green/red-only meaning
- CEREBUS visual lineage can inspire styling, but semantic readability wins
- responsive, dense, configurable
- brand hierarchy preserved:
  GLX -> FORGE -> CEREBUS -> Model/Indicator.

Reusable components:
ModelBadge
LayerBadge
EvidenceBadge
StatusBadge
DataQualityBadge
LevelRow
SetupCard
NoGoCard
EvidenceDrawer
AskPanel
VersionChip
ReleaseBadge
EntitlementGate.

Book V planning does not freeze final art direction; it freezes semantic components.

---

# PRODUCT SURFACE MAP

## Public/marketing
Approved descriptions and selected teaching material only.

## Library/member
CEREBUS Files, model explanations, selected evidence, manuals according to exposure.

## Pro/operator
Market dashboards
operator workspace
indicator vault
Ask Operator depth
eligible setup context according to product rules.

## Research/institutional
Researcher evidence depth
research artifacts/advanced model context
future API access per Book VI product catalog.

Exact pricing/tier names remain Book VI product decisions; UI consumes capabilities, not hard-coded plan names.

---

# BOOK V SECURITY / LEAKAGE INVARIANTS

1. Hidden UI is not authorization; server policy controls access.
2. Direct routes/downloads require entitlement.
3. Source code is never embedded in client bundle unless intentionally licensed.
4. Locked cards expose only approved marketing metadata.
5. Ask CEREBUS context IDs cannot retrieve forbidden objects.
6. Evidence drawer obeys separate depth/exposure.
7. Historical versions do not bypass current entitlements.
8. Client-side preferences cannot alter server model inputs.
9. No secret/provider keys in frontend.
10. Analytics events contain IDs/status, not protected corpus dumps.

---

# BOOK V ACCEPTANCE / RATIFICATION GATE

Book V is DONE only when:

## Registry
- all launch indicators versioned/source-hashed
- model/setup/manual links valid
- release status distinct from evidence status.

## Vault
- entitlement/direct-route tests pass
- manuals/version history work
- locked/search states do not leak protected content.

## Dashboards
- EUR/XAU/BTC/JPY/Fib views render Book III fixtures
- L3/L2/L1 distinction preserved
- stale/no-go/data-quality states visible
- plot toggles, positions and colors persist
- BTC Game absent unless later promoted.

## Workspace
- setup WATCH/ELIGIBLE/BLOCKED/UNRESOLVED flows correct
- no-go prominent
- Ask sidecar uses snapshot IDs safely
- no brokerage/order execution.

## Release
- stable promotion gate
- changelog classifications
- compatibility failure visible
- rollback/deprecation tested.

## Accessibility/security
- keyboard/basic accessibility checks
- non-color status cues
- server authorization on protected routes
- protected code/content absent from client bundle.

## Evidence pack
Each Bloc produces PLAN, ACCEPTANCE, implementation commits, tests, EVIDENCE, known gaps and ratification.

Final Book V record:
indicator registry version/hash
UI schema/component version
supported model/API versions
release pipeline version
entitlement route test report
visual regression/accessibility report
known exclusions
ratification commit.

---

# BOOK V EXCLUSIONS

Do NOT:
- recalculate CEREBUS model logic in frontend
- create order execution
- connect brokerage accounts
- hard-code Whop product IDs into UI permissions
- expose source code by default
- invent BTC Game
- automate ST
- make research-only Fib setup look production-approved
- create a universal confidence meter
- optimize UI around P&L dopamine loops.

---

# RECOMMENDED IMPLEMENTATION ORDER

1 V.1 Indicator Registry
2 shared semantic UI components
3 V.2 Vault
4 V.3 common dashboard shell
5 EUR dashboard
6 XAU dashboard
7 BTC dashboard
8 JPY dashboard
9 Fib dashboard
10 V.4 Operator Workspace + Ask sidecar
11 V.5 Release Pipeline
12 entitlement/accessibility/visual regression suite
13 evidence pack
14 Book V ratification/freeze.

# HANDOFF TO BOOK VI

Book VI supplies products/plans/licenses/Whop mappings.
Book V consumes only capabilities/entitlements from Book II/VI.

Changing from Whop to another commerce provider must not require rewriting Vault or Dashboard permission logic.

# HANDOFF TO BOOK VII

Book VII can publish new CEREBUS Files, evidence, model updates and release candidates into the registries surfaced by Book V.
Nothing becomes STABLE merely because it appears in research publishing.
