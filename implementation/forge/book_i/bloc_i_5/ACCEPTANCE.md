# Book I / Bloc I.5 — QA & Answer Contract — ACCEPTANCE

> Status: FROZEN GATES
> Date: 2026-10-08
> These clauses are frozen before implementation. I.5 passes ONLY when every
> clause is executable-proven. Clause letters are stable; evidence maps 1:1.

## A. QA AUTHORITY AND INPUT

A1. The QA kernel consumes ONLY governed `RetrievalService` results
    (`exact`, `retrieve`, `navigate`) — never a gateway, never a corpus file,
    never Markdown, never the backfill package.
A2. The kernel holds no persistence gateway, no repository root, no corpus
    path, and never invokes `run_backfill` or `run_index_build`.
A3. Every answer records the index `generation` and `index_hash` it was
    computed against (audit identity).
A4. Same question + same index generation + same `(principal, context)` ⇒
    byte-identical answer (`content_hash` equal) — no clock, randomness,
    dict-order or hostname influence.
A5. A question that cannot be classified deterministically still resolves
    deterministically (never a guess, never partial randomness).

## B. QUESTION CLASSIFICATION

B1. Classification is pure token/grammar logic; the same question always
    classifies identically.
B2. An explicit canonical id in the question routes exact (never fuzzy).
B3. `DESCRIPTIVE`, `EMPIRICAL`, `ACTIONABLE`, `COMPARATIVE` are
    distinguished, and `DESCRIPTIVE` is the safe fallback class (it can never
    assert a number).
B4. Query alias expansion uses the frozen Ontology Crosswalk via I.4 and
    never rewrites status, identity, population or evidence class.
B5. Market/family scope tokens become exact structured filters; unknown
    filter values match nothing (fail closed).

## C. THE FOUR-STATE LADDER

C1. Every answer carries the four booleans `retrieved, supported,
    assertable, explainable`.
C2. Ladder monotonicity: `assertable ⇒ supported ⇒ retrieved`;
    `explainable ⇒ assertable`.
C3. FOUND/retrieved never implies supported: a found-but-unsupported target
    yields `retrieved=true, supported=false`.
C4. supported never implies assertable: status authority (D/section 4) is
    evaluated independently — e.g. a supported CANDIDATE is assertable=false.
C5. explainable requires a fully resolvable citation chain for every
    empirical assertion; otherwise the rung is false and a gap is disclosed.
C6. No rung, ranking position, routing weight, or lexical hit ever changes a
    status, exposure, identity or evidence class (no authority promotion).

## D. ANSWERABILITY OUTCOMES

D1. Exactly seven outcomes exist: `ANSWERABLE, ANSWERABLE_QUALIFIED,
    PARTIAL, UNSUPPORTED, CONTRADICTED, OUT_OF_CORPUS, RESTRICTED`; no
    others may be produced.
D2. `UNSUPPORTED` carries epistemic label `INSUFFICIENT_EVIDENCE`.
D3. Fully supported + identity-complete + labeled + cited ⇒ `ANSWERABLE`.
D4. Any mandatory qualification (small-N, FORWARD_OOS, CANDIDATE,
    RESEARCH_FLAG, HISTORICAL, missing label, action gap) ⇒
    `ANSWERABLE_QUALIFIED`, never plain `ANSWERABLE`.
D5. Mixed pass/gap assertions ⇒ `PARTIAL`, with every gap disclosed.
D6. Resolves nothing and no denial ⇒ `OUT_OF_CORPUS` with zero corpus
    content beyond the classification echo.
D7. Zero results with denials ⇒ `RESTRICTED`, content-free (counts + reason
    codes only).
D8. Abstention outcomes (`UNSUPPORTED`, `OUT_OF_CORPUS`, `RESTRICTED`,
    `PARTIAL`) are successful results: they carry honest gaps and no
    fabricated content.

## E. CLAIM IDENTITY (EIGHT DIMENSIONS)

E1. Every numerical assertion carries all eight `ClaimIdentity` dimensions
    verbatim (`NOT_SPECIFIED_IN_SOURCE` where the source is silent).
E2. Claims compare only through `compare_claim_identity`; different
    populations are never merged, averaged, or reconciled.
E3. Result/statistic values never enter identity.
E4. Near-identical prose with different populations remains distinct
    assertions with distinct ids.
E5. If the necessary dimensions cannot be preserved for a requested
    numerical answer, the kernel qualifies or abstains — it never presents an
    unconditional statistic.

## F. CITATION AND EVIDENCE CHAINS

F1. Every empirical assertion traces `assertion → claim → evidence → source
    artifact` with artifact id, locator, content identity, relation and
    source state.
F2. Citations come only from policy-guarded `navigate()` hops over authorized
    records (deny stops the chain; no hop loads on deny).
F3. Visual or conversation-derived sources never satisfy an empirical
    citation.
F4. Descriptive answers are explicitly `answer_class=DESCRIPTIVE` and make
    no empirical claim.
F5. Missing links are disclosed with their reason code; links are never
    manufactured from similarity or a similar retrieved document.
F6. A citation names the actual supporting artifact of that claim — citing
    an unrelated artifact for a claim is rejected.

## G. STATUS AUTHORITY (NO PROMOTION)

G1. `FALSIFIED` can only appear as a negative/falsified statement
    (`NEGATIVE_EVIDENCE`) and never as a current positive trading rule.
G2. `HISTORICAL` answers are generation-bound and never presented as
    current.
G3. `CANDIDATE` and `RESEARCH_FLAG` are never unqualified; research content
    is returned AS research (status unchanged).
G4. Small-N/research qualifiers survive into the answer; N is present when
    small-N materially changes interpretation.
G5. `DESCRIPTIVE` never becomes a numerical assertion.
G6. `SUPERSEDED` is labeled; `PARKED` never reads as active guidance.
G7. Upgrading a candidate to validated, or any status change by relevance,
    similarity, ranking or question wording, never occurs.

## H. CONTRADICTION HANDLING

H1. Two claims may be called a contradiction only after identity match
    (`SAME_POPULATION`).
H2. Matched identity + divergent evidence/status ⇒ `CONTRADICTED` (or a
    mandatory conflict qualification) exposing BOTH sides with statuses,
    generations and evidence ids.
H3. Different populations are never reported as a contradiction; both are
    presented separately.
H4. Conflicting statistics are never averaged; no strongest-result
    selection; adverse/negative evidence is never silently discarded.
H5. Conflict notes are bounded and auditable (basis, both statuses, both
    generations, resolution) and contain no protected content.

## I. NUMERICAL SAFETY

I1. None of the frozen forbidden conversions occur (correlation→probability,
    target completion→WR, state agreement→WR, basket confirmation→WR,
    simulation→empirical, visual constant→validated statistic, historical
    report→current result).
I2. Every numeral appearing in answer text is traceable to governed claim or
    evidence text — no fabricated numerical claims.
I3. An unsupported numerical generalization is refused (qualify or abstain).
I4. Identity-mismatched numbers from different populations are never
    combined into one statement.

## J. EXPOSURE AND INFORMATION FLOW

J1. QA consumes only content authorized through the I.4 boundary; there is no
    second retrieval path.
J2. Forbidden content appears in NONE of: answer text, citations, summaries,
    debug traces, conflict descriptions, follow-up suggestions, error
    messages.
J3. A mixed public/protected question builds its answer only from authorized
    results; denied candidates surface solely as content-free denial entries.
J4. A denial is never explained by revealing the protected material (or its
    content identity/locator/snippet).
J5. Errors are content-free (fixed message + machine kind; no question echo,
    no corpus content).

## K. CEREBUS TRUTH FIXTURES

K1. Symmetry trap: manual/operator validity stays separate from failed
    automation parity; no `AUTOMATION_APPROVED` is ever produced;
    `MANUAL_OPERATOR`/`RESEARCH_ONLY` survive.
K2. P90 remains automation lineage, version-bound and evidence-bound — never
    a performance statistic.
K3. BTC: Tracker never establishes Game; missing BTC Game artifacts are
    disclosed as gaps, never invented.
K4. EURUSD: Daily / Weekly / Higher-Order remain distinct populations in
    answers — no family collapse.
K5. XAU: L3 destination, L2 path, L1 execution remain distinct layers;
    layer answers never bleed.
K6. JPY: USDJPY master, AUDJPY risk/execution, EURJPY referee — EURJPY is
    never promoted to an equal directional vote.
K7. Fib: Range Birth doctrine not reduced to coordinates; R11 overgeneration
    negative evidence survives as FALSIFIED + NEGATIVE_EVIDENCE.
K8. Research statistics: small-sample and research qualifiers survive into
    the answer; a qualified answer and a misleadingly confident answer are
    distinguished by test.

## L. CORPUS QA DETECTORS (frozen chapters I.5.1–I.5.4)

L1. Orphan detector: zero dangling launch references (every parent, related
    id, evidence id and provenance target resolves).
L2. Unsupported-number detector: 100% of launch numerical claims are
    evidence-linked or explicitly non-promoted.
L3. Status/generation leakage: index status == canonical status for all 30
    records; source generation retained where stated.
L4. Exposure leakage: the subscriber retrieval build contains zero
    forbidden-exposure objects, and no internal body/marker appears on any
    answer surface.
L5. Deterministic rebuild: two QA evaluations over the same generation are
    identical; index rebuild laws from I.4 still hold from QA's perspective
    (answers follow generation changes).
L6. Known research gaps are labeled by the detectors, never invented away.

## M. GOLDEN FIXTURES, COVERAGE, FREEZE (I.5.5–I.5.7)

M1. Golden fixtures exist for all seven launch models with question →
    expected object routes and are executed by tests through the kernel.
M2. The eight truth traps (K) are explicit fixtures.
M3. A coverage report with exact counts is generated and committed.
M4. The Book freeze manifest (schema versions, object counts, hashes, known
    gaps, exclusions) is committed outside `corpus/` (the frozen inventory
    must not change).

## N. STRUCTURED ANSWER CONTRACT

N1. Every answer validates against the frozen fields: outcome, answer class,
    ladder, epistemic label, assertions, claim refs, evidence refs,
    citations, qualifications, conflicts, gaps, limitations, denials,
    follow-ups, generation, index hash, content hash.
N2. Serialization is deterministic sorted-key JSON with `content_hash`;
    no timestamps or random values.
N3. The answer references canonical objects by id and governed statement
    only — it never embeds a duplicated canonical object as a new authority.
N4. No raw protected source body appears in the answer structure; assertion
    text is governed `retrieval_text` only.
N5. Validation fails closed: an invalid answer is rejected, not repaired
    silently.

## O. BOUNDARY INTEGRITY

O1. No LLM, chatbot, prompt interface, OpenRouter, embedding or provider
    call exists anywhere in I.5.
O2. No route is added: FORGE routes remain `{health, ready, meta}`;
    `/answer`, `/ask`, `/qa`, `/query` all 404.
O3. No new third-party dependency and no new migration
    (`discover_migrations() == [1, 2]`, 001 SHA pin unchanged).
O4. No commercial, entitlement, plan, license or Whop object is created.
O5. No new ontology value or evidence-status enum: I.5 imports and reuses
    frozen enums only.

## P. REPRODUCIBILITY

P1. Two identical questions against the same generation and context produce
    identical `content_hash` and identical field-by-field output.
P2. Result ordering is total and stable (sorted ids); no dict-iteration,
    clock or randomness enters output or ordering.

## Q. POSTGRESQL / CI

Q1. The full suite is green against live PostgreSQL (CI postgres job).
Q2. CI `test` and `postgres` jobs are green on the final head.

## R. REGRESSION

R1. I.1, I.2, I.3, I.4, II.1–II.4 focused suites, persistence, policy and
    Signal Guard tests are green; no existing test is weakened or deleted.
R2. The full repository suite is green with no new failures.
