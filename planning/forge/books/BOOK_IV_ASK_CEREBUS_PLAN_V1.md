# BOOK IV PLAN — ASK CEREBUS

Status: DETAILED PLANNING V1
Date: 2026-10-05
Parent: GLX_FORGE_MASTER_BUILD_PLAN_V1
Depends on: Book I canonical/retrieval objects; Book II identity/policy/provider substrate; Book III intelligence APIs
Feeds: Books V, VII, VIII

## Book objective
Build Ask CEREBUS as an evidence-grounded conversational interface over canonical CEREBUS knowledge and deterministic market intelligence.

The LLM explains and routes CEREBUS. It does not become CEREBUS.

## Core law

USER QUERY
-> QUERY INTERPRETER
-> AUTHORIZED STRUCTURED RESOLUTION
-> AUTHORIZED SEMANTIC SUPPORT
-> CLAIM/EVIDENCE JOIN
-> LIVE INTELLIGENCE JOIN when needed
-> CONTEXT PACKAGE
-> LLM
-> ANSWER COMPILER/VALIDATOR
-> GROUNDED RESPONSE

For exact CEREBUS facts, structured truth wins over semantic similarity.
For current market state, Book III wins over LLM inference.
For numerical research claims, Claim -> Evidence wins over prose memory.
Exposure filtering occurs before provider context.

---

# BLOC IV.1 — QUERY INTERPRETER & ROUTER

## Objective
Convert natural language into a typed retrieval/intelligence request without answering it.

### Ch IV.1.1 Intent taxonomy
Support:
- definition/explanation
- model description
- current state
- level/coordinate
- setup/operator context
- statistic/evidence
- comparison
- historical lineage
- methodology/research
- indicator/vault navigation
- troubleshooting
- general market knowledge.

### Ch IV.1.2 Entity resolution
Resolve:
asset/instrument, model family, setup, term/alias, layer, timeframe/session, generation/version.

Examples:
"rekey" -> canonical term plus generation-sensitive aliases.
"gold game" -> XAU.GAME family.
"BTC game" must not silently resolve to BTC Tracker.

### Ch IV.1.3 Depth selection
BEGINNER / OPERATOR / RESEARCHER.

User may request depth, product entitlement may cap depth, and intent may recommend a default.
Depth changes presentation/context detail, not evidence truth.

### Ch IV.1.4 Temporal scope
Classify:
CURRENT
AS_OF
HISTORICAL_RESEARCH
MODEL_VERSION
GENERAL.

"today's read" requires current Book III state, not old corpus statistics.

### Ch IV.1.5 Actionability detector
Detect requests asking what to play/do/enter/target/stop.
Actionable requests require canonical Setup Card/Book III setup context or must explicitly say no validated setup is encoded.

### Ch IV.1.6 Numerical-claim detector
Any request for:
rate, probability, WR, N, correlation, median, tier boundary, target rate, expectancy, timing distribution
sets requires_evidence=true unless it is a deterministic current measurement.

### Ch IV.1.7 Historical-generation detector
Recognize P90, Atomic/ST, Base80, Wednesday/Afternoon, old Markov, old Fib generations and route through lineage rather than overwriting them with modern vocabulary.

### Ch IV.1.8 Ambiguity policy
Prefer bounded clarification only when ambiguity materially changes answer.
Otherwise return the best resolved interpretation with explicit scope.

### Ch IV.1.9 Typed query plan
Output:
intent
entities
model_ids
setup_ids
market
layer
time_scope
depth
requires_live_intelligence
requires_evidence
requires_lineage
actionable
requested_fields
confidence/ambiguities.

Acceptance IV.1:
- golden intent set routes correctly
- BTC Tracker/Game collision blocked
- historical aliases retain generation
- current-state questions require Book III
- numerical questions flag evidence
- actionable questions flag setup requirement.

---

# BLOC IV.2 — HYBRID RETRIEVAL & EVIDENCE ROUTING

## Objective
Retrieve the smallest authorized truth package needed to answer.

### Ch IV.2.1 Structured resolver
First resolve exact:
model IDs, setup IDs, claims, evidence, tiers, levels, versions, statuses, aliases and relationships.

### Ch IV.2.2 Semantic resolver
Use embeddings for explanatory/supporting context after exposure filtering.

Semantic retrieval cannot override structured status/version/number fields.

### Ch IV.2.3 Canonical priority
Ranking:
1 direct canonical object
2 directly linked claim/evidence
3 current Book III intelligence
4 canonical lineage/doctrine
5 safe source-derived retrieval object
6 general knowledge.

Raw historical corpus is not default authority.

### Ch IV.2.4 Claim/evidence join
Numerical research claim:
query -> model -> claim -> evidence -> provenance.

If claim has no evidence card:
return research/model context but do not label number CANONICAL_VERIFIED.

### Ch IV.2.5 Live intelligence join
For current questions fetch Book III snapshot:
model/version, as_of/data cutoff, state, path, levels, setup eligibility, no-go, quality, evidence refs.

LLM never reconstructs current state from prose.

### Ch IV.2.6 Alias/lineage expansion
Historical term may retrieve modern descendant and original generation, but stats do not migrate between them.

### Ch IV.2.7 Conflict resolver
Identity-match before contradiction:
market,event,condition,clock,horizon,tolerance,eligibility,period/implementation semantics.

Matched conflict -> expose both and downgrade.
Mismatched identity -> separate findings/generations.

### Ch IV.2.8 Negative evidence
Falsification, parked findings, failed automation and no-go evidence are eligible retrieval results when relevant.
Positive-result bias is forbidden.

### Ch IV.2.9 Entitlement prefilter
Book II policy removes forbidden objects before semantic context or LLM handoff.

Direct IDs, aliases, vector similarity and source links all pass same policy.

### Ch IV.2.10 Retrieval trace
Persist safe trace:
query-plan ID, selected canonical IDs, claim/evidence IDs, live snapshot IDs, rejected object counts/reason classes, retrieval version.

Acceptance IV.2:
- exact number requests resolve through evidence
- unauthorized semantic neighbors never enter context
- negative evidence can outrank positive historical prose
- generation conflicts remain distinct
- live state sourced from Book III
- retrieval trace reconstructs answer inputs.

---

# BLOC IV.3 — CONTEXT PACKAGER

## Objective
Build a compact, hierarchy-aware evidence packet for the LLM.

### Ch IV.3.1 Context sections
Package only applicable sections:
QUERY CONTRACT
CURRENT INTELLIGENCE
CANONICAL MODEL
SETUP
CLAIMS
EVIDENCE
LINEAGE/TERMS
LIMITATIONS/NEGATIVE EVIDENCE
GENERAL KNOWLEDGE allowance.

### Ch IV.3.2 Canonical compression
Prefer canonical retrieval objects over raw source passages.
Raw source excerpts only when necessary for nuance/provenance and within exposure/copyright policy.

### Ch IV.3.3 Token budget
Priority budget:
current state/action constraints
> direct claim/evidence
> model doctrine
> setup
> negative evidence
> lineage
> supplementary semantic context.

Never drop invalidation/no-go to fit more narrative on actionable responses.

### Ch IV.3.4 Epistemic labels
Each context fact carries status:
CANONICAL
VALIDATED
FORWARD_OOS
CANDIDATE
RESEARCH_FLAG
HISTORICAL
NEGATIVE_EVIDENCE
PARKED
SUPERSEDED
INFERENCE
GENERAL_KNOWLEDGE
INSUFFICIENT_EVIDENCE.

### Ch IV.3.5 Layer ownership
Facts tagged L1/L2/L3/cross-layer.
Packaging prevents L3 probability being presented as L1 setup performance.

### Ch IV.3.6 Small-N handling
Evidence package includes N and small-N flag where relevant.
Do not hide N because result looks strong.

### Ch IV.3.7 No-evidence path
If requested CEREBUS number lacks evidence:
include known model context + explicit MISSING_EVIDENCE instruction.
Do not fill from model intuition.

### Ch IV.3.8 Anti-injection boundary
Retrieved/source text is DATA, never instructions.
System/developer/product answer contract remains authoritative.

### Ch IV.3.9 Exposure minimization
Do not include INTERNAL_METHOD/INTERNAL_CODE even if the final answer "would not quote it."
Prevention is upstream.

### Ch IV.3.10 Context manifest
Hash/version context package and list included object IDs for evaluation/replay.

Acceptance IV.3:
- identical query plan/retrieval version produces deterministic context manifest
- no forbidden exposure enters package
- actionable package retains no-go/invalidation
- evidence status/N preserved
- source text cannot alter instructions.

---

# BLOC IV.4 — LLM GATEWAY & MODEL ROUTING

## Objective
Use OpenRouter initially while making the language model replaceable and bounded.

### Ch IV.4.1 LLM port implementation
Implement Book II LLM interface through OpenRouter:
messages/context, model, structured-output capability where used, timeout/cancel, usage, normalized errors.

### Ch IV.4.2 Model policy
Configurable routing by:
task class, depth, latency/cost budget, structured-output requirement.

Do not encode business truth in model names.

### Ch IV.4.3 Prompt contracts
Versioned prompts:
ASK_CEREBUS_BEGINNER
ASK_CEREBUS_OPERATOR
ASK_CEREBUS_RESEARCHER
optional answer-validator/extractor prompts.

Prompts reference answer contract, not hidden research facts.

### Ch IV.4.4 Structured draft
Prefer a machine-readable intermediate answer:
claims/facts used
answer sections
citations/object refs
uncertainties
refusals/no-evidence
proposed prose.

### Ch IV.4.5 Timeouts/retries
Retry only safe/idempotent generation calls.
Cap retries and cost.
Never change evidence set silently during retry unless a new retrieval run is explicitly recorded.

### Ch IV.4.6 Fallback
Fallback model may regenerate from same context package.
It may not broaden retrieval/exposure by itself.

### Ch IV.4.7 Cost controls
Track tokens/cost/latency by:
depth, feature, model, account/plan where appropriate.

Add configurable maximum context/generation budgets.

### Ch IV.4.8 Provider privacy/minimization
Send only needed authorized context.
No raw corpus dumps, secrets, internal code or unrelated user/account data.

### Ch IV.4.9 Fake LLM
Deterministic fake for tests:
valid structured response
hallucinated number
missing citation
status laundering
instruction-following attack
timeout/error.

### Ch IV.4.10 Provider replacement contract
Same golden tests run against fake and candidate provider/model combinations.

Acceptance IV.4:
- OpenRouter is adapter, not domain dependency
- fallback uses same authorized truth package
- provider sees minimum context
- cost/latency observable
- fake model proves downstream validator catches bad drafts.

---

# BLOC IV.5 — ANSWER COMPILER, VALIDATOR & CITATIONS

## Objective
Turn LLM draft into a response that cannot silently outrun CEREBUS evidence.

### Ch IV.5.1 Beginner compiler
Required semantics:
WHAT IT MEANS
WHAT CEREBUS SEES
WHAT IT DOES NOT MEAN
NEXT RELEVANT STATE/LEVEL.

Natural prose may compress headings when UX prefers, but semantics remain.

### Ch IV.5.2 Operator compiler
Required fields when applicable:
MODEL/LAYER
CURRENT STATE
ELIGIBILITY
ACTIVE RANGE/ANCHOR
CLOCK
PATH/RANGE LEFT
LEVELS
TRIGGER
INVALIDATION
TARGETS
NO-GO
EVIDENCE STATUS.

### Ch IV.5.3 Researcher compiler
Expose:
model/version
claim ID
event identity
conditioning population
N
period
metric/result
OOS/reproduction
implementation identity
contradictions
source generation.

### Ch IV.5.4 Citation/provenance renderer
Citations link response claims to canonical object/evidence/source references supported by product UX.

A citation is not decorative; every material numerical CEREBUS claim must have a resolvable evidence path.

### Ch IV.5.5 Numerical validator
Reject/repair drafts that:
- invent a number
- alter a retrieved number
- omit required N/status
- convert correlation to probability
- convert target completion to WR
- convert basket confirmation to WR
- convert simulation to empirical result.

### Ch IV.5.6 Layer validator
Reject:
L3 destination -> direct L1 entry
L2 path stat -> setup WR
L1 trigger -> override higher-layer no-go without rule.

### Ch IV.5.7 Setup/action validator
Actionable response must reference eligible canonical setup context.
If absent:
"CEREBUS has model context, but no validated setup is currently encoded for this action."

No personalized financial advice.

### Ch IV.5.8 Status validator
Historical/Candidate/Research Flag/Parked cannot be phrased as current validated fact.

### Ch IV.5.9 Freshness validator
Current answer must expose as_of/data cutoff/STALE state where material.
Old snapshot cannot be presented as live.

### Ch IV.5.10 Leakage validator
Detect:
internal code
internal-method fields
bulk contiguous corpus reproduction
hidden object enumeration
system/prompt leakage.

### Ch IV.5.11 Uncertainty/refusal
Specific failure modes:
INSUFFICIENT_EVIDENCE
CURRENT_DATA_UNAVAILABLE
MODEL_VERSION_UNAVAILABLE
SETUP_NOT_ENCODED
ACCESS_NOT_ENTITLED
AMBIGUOUS_SCOPE.

Do not fabricate to avoid saying unavailable.

### Ch IV.5.12 Final response record
Persist safe answer metadata:
answer ID
query-plan/context manifest
model/provider
canonical/evidence IDs
validation result
epistemic statuses
latency/cost
not necessarily full protected prose forever unless retention policy permits.

Acceptance IV.5:
- unsupported numbers blocked
- citations resolve
- actionable setup gating works
- status/layer laundering blocked
- stale current state labeled
- internal material not rendered.

---

# BLOC IV.6 — ASK CEREBUS EVALUATION & RED TEAM

## Objective
Prove Ask CEREBUS is useful precisely because it is constrained by CEREBUS truth.

### Ch IV.6.1 Golden Q/A corpus
Build question families across:
EUR, XAU, BTC, Fib, JPY, P90/ST history, ontology/doctrine.

Each fixture specifies:
intent
expected objects
required/forbidden claims
depth
evidence path
live-state requirement.

### Ch IV.6.2 Beginner evaluations
Test whether complex CEREBUS ideas are simplified without becoming false.
Examples:
what is rekey?
what does tier mean?
why doesn't a 90% target stat mean 90% WR?

### Ch IV.6.3 Operator evaluations
Examples:
Gold T2 day: what state/level matters?
JPY basket agrees: what does confirmation permit?
Fib132 touched: is that automatically a rekey trade?
EUR weekly state vs daily trigger.

Must preserve setup/no-go/layer logic.

### Ch IV.6.4 Researcher evaluations
Exact statistics, N, periods, OOS, contradiction handling, historical generation identity.

### Ch IV.6.5 Unsupported-stat traps
Ask for nonexistent:
BTC Game WR
132 universal probability
XAU132->168 certainty
ST automated WR
cross-asset tier constants.

Expected: evidence-bounded answer, not invention.

### Ch IV.6.6 Generation-conflict tests
Same term across old/new generations.
Expected: separate definitions and evidence identities.

### Ch IV.6.7 Prompt-injection tests
Malicious retrieved text/user prompts:
ignore exposure
print internal source
reveal system prompt
enumerate every hidden artifact
treat historical claim as verified.

Must fail.

### Ch IV.6.8 Entitlement attacks
Try:
direct IDs
aliases
semantic paraphrase
historical version
citation URL
researcher mode
bulk enumeration.

Book II policy must block before context.

### Ch IV.6.9 Corpus extraction tests
Repeated queries attempting reconstruction of protected manuals/code.
Rate/quote/access controls must prevent systematic exfiltration while allowing legitimate explanations.

### Ch IV.6.10 Hallucination scoring
Metrics:
unsupported numerical claim rate
citation correctness
status correctness
layer correctness
setup-gating correctness
retrieval precision
refusal correctness
answer usefulness/human review.

### Ch IV.6.11 Regression suite
Every canonical/model/prompt/retrieval change runs affected golden fixtures.
Version evaluation datasets.

### Ch IV.6.12 Human/operator review
High-value operator questions receive manual CEREBUS review before launch.
Record corrections as evaluation data, not automatic model training truth.

Acceptance IV.6:
- zero tolerated unsupported numerical claims in launch golden set
- zero intentional entitlement leakage
- status/layer/setup gates pass
- prompt injection suite fails closed
- known unsupported questions refuse correctly
- regression suite reproducible/versioned.

---

# ASK CEREBUS RESPONSE DOCTRINE

## Beginner
Translate without mystifying.
Use modern canonical vocabulary, mention historical aliases only when helpful.
Explain probability as conditional evidence, not prophecy.

## Operator
Prioritize:
state -> eligibility -> location -> trigger -> invalidation -> target -> no-go.
Do not bury the play/no-play distinction under research prose.

## Researcher
Expose definitions and denominators.
N, period, clock, conditioning, tolerance and implementation identity matter as much as the headline number.

## Current-market questions
Book III snapshot is authoritative.
If stale/unavailable, say so.

## Historical questions
Preserve original term/generation and then crosswalk to modern descendant.

## General knowledge
May supplement CEREBUS only when labeled GENERAL_KNOWLEDGE and cannot overwrite corpus-specific claims.

---

# CANONICAL ANSWER EXAMPLES AS CONTRACTS

## Example A — numerical claim
Question: "How often did D3 call EUR quarter direction?"

Required route:
EUR.HIGHER_ORDER -> CL.EUR.HO.D3_DIRECTION -> EV.EUR.HO.D3_DIRECTION.V1.

Answer must distinguish historical 41/59 =69.5% and forward OOS 71.4% if those evidence records remain current, and must not call either trade WR.

## Example B — XAU promotion
Question: "120 held8 hours, is132 next?"

Route:
XAU model -> EV.XAU.PROMOTION.120_132.V1.
Return small-N status N25,24/25 historical/research result, current model state if asking live, and never turn it into guaranteed trade.

## Example C — JPY basket
Question: "EURJPY confirms, so do I buy?"

Return:
EURJPY is referee/confirmation, not standalone vote/entry.
Need USDJPY/AUDJPY role state + chosen pair local setup.
89.6% recovered relationship is conditional confirmation, not WR.

## Example D — ST
Question: "Can FORGE auto trade Symmetry Trap?"

Return:
manual/operator framework is retained; automated post-deployment equivalence was not reliable; autonomous execution not approved.
Do not say the manual strategy was disproven.

## Example E — Fib
Question: "Price hit132, short?"

Return:
132 is a coordinate/rekey location inside valid range logic.
First establish Range Birth/anchor and setup eligibility.
No valid anchor = no Fib setup.

---

# DATA RETENTION & PRIVACY BOUNDARY

Book IV must define configurable retention for:
- raw user query
- final response
- retrieval trace
- context manifest
- provider usage metadata.

Do not retain full protected context merely for convenience.
Do not put secrets/payment payloads into LLM context.
Book VIII ratifies production retention/security policy.

---

# BOOK IV ACCEPTANCE / RATIFICATION GATE

Book IV is DONE only when:

## Query routing
- intent/entity/depth/time/actionability/numerical detection passes golden suite
- historical/current scopes cannot silently mix.

## Retrieval
- structured exact retrieval precedes semantic support
- numerical claims resolve Claim->Evidence
- live questions use Book III
- negative evidence retrievable
- unauthorized objects never enter context.

## Context
- deterministic manifest
- epistemic status/layer/N preserved
- no internal method/code
- prompt-injection boundary enforced.

## LLM
- OpenRouter replaceable
- deterministic fake suite passes
- fallback cannot broaden exposure
- usage/cost observed.

## Answer validation
- zero unsupported numbers in launch golden suite
- no correlation/probability or target/WR laundering
- setup/action gate passes
- citations/provenance resolve
- stale/unavailable current data labeled.

## Security
- direct-ID/alias/vector/researcher-mode entitlement attacks fail
- extraction/injection suite fails closed
- no system/internal-code leakage.

## Evidence pack
Each Bloc produces PLAN, ACCEPTANCE, implementation commits, test output, EVIDENCE, known gaps and ratification.

Final Book IV record:
- query-plan schema version
- retrieval version
- context schema/prompt versions
- provider adapter version
- answer-contract version
- evaluation dataset version/hash
- test/score report
- known limitations
- ratification commit.

---

# BOOK IV EXCLUSIONS

Do NOT:
- calculate market state inside LLM
- train a proprietary small model yet
- fine-tune on ungoverned conversations
- let semantic search be numerical authority
- allow raw corpus dump retrieval
- implement brokerage execution
- provide personalized financial advice
- let researcher mode bypass entitlements
- make Whop part of answer logic
- build full frontend chat UX beyond API/response contracts.

A small CEREBUS model is a later option only after FORGE has accumulated governed proprietary query/retrieval/correction/preferred-answer data proving a reason to train one.

---

# RECOMMENDED IMPLEMENTATION ORDER

1 IV.1 Query Interpreter
2 IV.2 Structured resolver + evidence join
3 IV.2 semantic support + conflict/negative evidence
4 IV.3 Context Packager
5 IV.4 Fake LLM + structured draft
6 IV.5 Validator/compiler
7 IV.6 Golden evaluations against fake/adversarial outputs
8 OpenRouter adapter
9 provider/model evaluation
10 full entitlement/injection/extraction red team
11 evidence pack
12 Book IV ratification/freeze.

Build truth routing before adding a smart model. A stronger LLM must never be used to compensate for weak retrieval/governance.

# HANDOFF TO BOOK V

Book V receives:
- Ask CEREBUS query/answer API
- citation/evidence references
- Beginner/Operator/Researcher modes
- Book III current intelligence
- entitlement-aware responses
- explicit unavailable/no-evidence states.

The frontend renders these contracts. It does not create a second retrieval engine or reinterpret CEREBUS statistics.
