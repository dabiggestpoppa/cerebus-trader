# Book I / Bloc I.5 — QA & Answer Contract — PLAN

> Status: ACTIVE
> Date: 2026-10-08
> Governing law: **RETRIEVED ≠ SUPPORTED ≠ ASSERTABLE ≠ EXPLAINABLE.** An
> answer is a deterministic, auditable projection of governed canonical truth
> through the ratified retrieval boundary. It never becomes a new source of
> truth, never promotes a status by relevance or similarity, and abstention is
> a valid successful result.

## 0. Source inventory (Phase 0 truth)

Verified at `b61a29c67d861bcfcbc27d228006e54ac405254e` (I.4 ratified head;
remote `origin/forge` in sync; freeze `60e067547b9d9165d94e4f074e0db0ba58e59e24`
is an ancestor). Ratifications verified present and passing: I.1, I.2
(Decision PASS), I.3, I.4, II.1, II.2, II.3, II.4 — all CLOSED/PASS. Baseline
at this head: **570 passed, 19 skipped**.

Frozen contracts read (no design may contradict them):

| Contract | Path | Role in I.5 |
|---|---|---|
| Book I plan (BLOC I.5 chapters I.5.1–I.5.7 + Acceptance I.5 / BOOK I DONE) | `planning/forge/books/BOOK_I_CORPUS_CANONICAL_PLAN_V1.md` | corpus-QA scope + book gate |
| Master build plan (Bloc I.5 Corpus QA; Book I gate) | `planning/forge/GLX_FORGE_MASTER_BUILD_PLAN_V1.md` | chapter scope |
| Master dependency acceptance audit (Phase B: I.5 before Phase C) | `planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` | ordering |
| Agent execution handoff (`…→ I.3 → I.4 → I.5`) | `planning/forge/AGENT_EXECUTION_HANDOFF_V1.md` | ordering |
| Ask CEREBUS Answer Contract V1 | `corpus/canonical/ANSWER_CONTRACT_V1.md` | answer vocabulary, numerical/layer/action safety, conflict + missing-evidence rules |
| Claim Registry V1 | `corpus/canonical/CLAIM_REGISTRY_V1.md` | claim→model→evidence routing, conflict rule, promotion rule |
| Retrieval Object Schema V1 | `corpus/canonical/RETRIEVAL_OBJECT_SCHEMA_V1.md` | retrieval record fields consumed by QA |
| Product Exposure Rules V1 | `corpus/canonical/PRODUCT_EXPOSURE_RULES_V1.md` | entitlement-before-retrieval; no fabricated certainty |
| CEREBUS Canonical Taxonomy V1 | `corpus/canonical/CEREBUS_CANONICAL_TAXONOMY_V1.md` | object/type vocabulary |
| Ontology Crosswalk V1 | `corpus/canonical/ONTOLOGY_CROSSWALK_V1.md` | alias/generation routing (verbatim, via I.4) |
| Planning freeze manifest | `planning/forge/PLANNING_FREEZE_MANIFEST_V1.md` | frozen lineage |

Ratified substrate reused (never re-implemented): I.1 `canonical.py` domain
kernel (`EvidenceStatus`, `ClaimIdentity`, `compare_claim_identity`), I.2
`provenance.py` (`classify_support`), I.3 `backfill/*` corpus state, II.2
`PersistenceGateway`, II.3 `ForgePrincipal`, II.4 `policy.py` +
`ForgePolicyEnforcementService`, I.4 `RetrievalService` (the ONLY content
path for answers).

Persisted/indexed state I.5 consumes (I.4 evidence): 30 canonical objects
(7 MODEL, 10 EVIDENCE, 3 SETUP, 10 CLAIM), 29 artifacts, 38 edges,
index `index_hash=e23cfeb4…d173`, 9 quarantined sources.

## 1. What I.5 is (and is not)

I.5 is two coupled deliverables under one frozen contract:

**A. The deterministic QA kernel** (how retrieved knowledge becomes a
defensible answer): question classification → governed retrieval intake →
claim/evidence/source binding → answerability decision → structured answer.

**B. Corpus QA & freeze** (the frozen Book I chapters):

- I.5.1 orphan detector — dangling launch references
- I.5.2 unsupported-number detector — every launch numerical claim
  evidence-linked or explicitly non-promoted
- I.5.3 status/generation (cross-generation) leakage detector — index status
  identical to canonical status; source generation retained
- I.5.4 exposure leakage detector — zero forbidden-exposure objects in the
  subscriber retrieval build; no internal body on any answer surface
- I.5.5 golden fixtures — questions/expected object routes for the seven
  launch models
- I.5.6 coverage report
- I.5.7 Book freeze manifest (schema versions, object counts, hashes, known
  gaps, exclusions)

**Explicitly out of scope:** any LLM, chatbot, prompt interface, OpenRouter or
provider integration; any public QA/search route or API surface; any
commercial/licensing object; live market calculation; embeddings/vectors
(Book VII VII.5); any new ontology value or evidence-status enum.

## 2. Frozen vocabulary — nothing invented

### 2.1 Evidence status (I.1 enum, verbatim)

`OBSERVED, VALIDATED, FORWARD_OOS, CANDIDATE, RESEARCH_FLAG, DESCRIPTIVE,
HISTORICAL, PARKED, SUPERSEDED, FALSIFIED, NO_GO, REPRODUCTION_REQUIRED,
INTERNAL_CONTRADICTION, IMPLEMENTATION_NOT_PARITY_SAFE` — used exactly as
stored; I.5 never rewrites a status.

### 2.2 Epistemic labels (Answer Contract V1, verbatim)

`CANONICAL, VALIDATED, FORWARD_OOS, CANDIDATE, RESEARCH_FLAG, HISTORICAL,
NEGATIVE_EVIDENCE, PARKED, SUPERSEDED, INFERENCE, GENERAL_KNOWLEDGE,
INSUFFICIENT_EVIDENCE`.

Frozen status → label mapping (used on every answer/assertion):

| EvidenceStatus | contract label |
|---|---|
| VALIDATED | VALIDATED |
| FORWARD_OOS | FORWARD_OOS |
| CANDIDATE | CANDIDATE |
| RESEARCH_FLAG | RESEARCH_FLAG |
| HISTORICAL | HISTORICAL |
| PARKED | PARKED |
| SUPERSEDED | SUPERSEDED |
| FALSIFIED | NEGATIVE_EVIDENCE |
| DESCRIPTIVE | CANONICAL |
| anything else (OBSERVED, NO_GO, REPRODUCTION_REQUIRED, INTERNAL_CONTRADICTION, IMPLEMENTATION_NOT_PARITY_SAFE) | **no label defined by the frozen contract** ⇒ label omitted and a qualification is mandatory; such an assertion can never be plain ANSWERABLE |

The claim's `EvidenceStatus` is always carried verbatim alongside the label;
the label never replaces it.

### 2.3 Answerability outcomes (I.5's frozen answer vocabulary)

Seven outcomes, exactly as required by the frozen answer contract's behavior —
these are **answerability outcomes, not evidence statuses**:

`ANSWERABLE, ANSWERABLE_QUALIFIED, PARTIAL, UNSUPPORTED, CONTRADICTED,
OUT_OF_CORPUS, RESTRICTED`.

- `UNSUPPORTED` carries epistemic label `INSUFFICIENT_EVIDENCE` (the
  contract's actual word for "cannot support").
- Each outcome is produced by exactly one documented trigger (§6).

### 2.4 Claim identity (I.1, eight dimensions, verbatim)

`market, event_definition, conditioning_event, clock_origin, horizon,
tolerance, eligibility, implementation_semantics` compared only with
`compare_claim_identity` ⇒ `SAME_POPULATION` / distinct. Numerical result
values never enter identity.

## 2.5 The four-state ladder

Every answer carries four booleans computed in order:

1. **retrieved** — at least one governed object resolved through I.4 for this
   question (authorized results exist).
2. **supported** — the resolved chain reaches at least one
   independent-empirical source per ratified I.2 `classify_support` (what I.4
   already computed as `support.supported`).
3. **assertable** — supported AND status-authority permits AND identity is
   complete for every numerical assertion AND no unresolved matched-identity
   conflict AND exposure allowed.
4. **explainable** — assertable AND every assertion has a fully resolvable
   citation chain (claim → evidence → source artifact with locator +
   content identity) AND all mandatory qualifications are derivable from
   governed fields.

Rungs never imply the next: FOUND never implies SUPPORTED; SUPPORTED never
implies ASSERTABLE (a supported claim may still require qualification);
ASSERTABLE without citations degrades to a gap, never to an unqualified
answer.

## 3. Question classification (deterministic, no model)

Input: the question string (plus optional explicit canonical id). Rules,
applied in order, all token/grammar based (reusing I.4 `normalize_query` /
`expand_query_text` tokenization and crosswalk alias expansion):

1. **Explicit id** — the question contains a token matching the canonical id
   grammar (`MODEL|CLAIM|EVIDENCE|SETUP`.`…`) ⇒ id-exact route.
2. **Question class** (single, from closed keyword sets):
   - `DESCRIPTIVE` — what/define/purpose/meaning/meaning-of/model-questions;
     answerable from canonical doctrine without an empirical claim.
   - `EMPIRICAL` — statistical/numerical language (accuracy, correlation,
     probability, rate, N=, %, "how often", backtest, win rate, validated
     result…); requires a claim → evidence chain.
   - `ACTIONABLE` — entry/trigger/target/no-go/setup/should-I/when-to;
     governed by Action Safety.
   - `COMPARATIVE` — "vs", "versus", "difference", "collapse" probes.
   Fallback: `DESCRIPTIVE` when nothing empirical/actionable matches, since
   descriptive wording is the weakest claim (it can never assert a number).
3. **Scope tokens** — market/family tokens (after alias expansion) become
   `RetrievalQuery(market=…, model_family=…)`; free tokens become `text`.
4. Unknown/gibberish questions still classify deterministically; if retrieval
   then resolves nothing ⇒ `OUT_OF_CORPUS` (never a guess).

## 4. Answer authority (Phase 2)

### 4.1 Status authority table (when may an assertion be asserted)

| Status | Authority |
|---|---|
| VALIDATED | assertable; carried qualifiers (e.g. `_SMALL_N` registry wording, sample_n present) still force `ANSWERABLE_QUALIFIED` when small-N materially changes interpretation |
| FORWARD_OOS | assertable **only qualified** — OOS/forward nature is a mandatory qualification |
| CANDIDATE | qualified only; never an unqualified assertion |
| RESEARCH_FLAG | qualified only; never phrased as production signal logic |
| DESCRIPTIVE | descriptive assertions only — never a numerical assertion |
| HISTORICAL | qualified + generation-bound; never presented as current |
| SUPERSEDED | qualified; must be labeled superseded |
| FALSIFIED | assertable only as a negative/falsified statement (NEGATIVE_EVIDENCE); **can never become a current positive trading rule** |
| PARKED | qualified; never active guidance |
| no-label statuses (§2.2) | qualified with mandatory limitation wording; never plain ANSWERABLE |

`FOUND`, `SUPPORTED`, ranking position, routing weights (`beginner_weight`,
`operator_weight`, `researcher_weight`), lexical hits and alias expansion
change **nothing** about authority (no semantic authority promotion).

### 4.2 Numerical assertion gate

An assertion is **numerical** if its governed text contains a digit or the
question asked for a number. Numerical assertions additionally require:

1. population measured (ClaimIdentity.market),
2. event defined (`event_definition`),
3. conditioning event, 4. clock origin, 5. horizon, 6. tolerance,
7. eligibility rules, 8. implementation semantics — each carried verbatim
   (`NOT_SPECIFIED_IN_SOURCE` where the source is silent, which is itself the
   honest value), AND
9. an evidence-linked chain (`support.supported` with ≥1 evidence id).

If any dimension cannot be preserved, the kernel **qualifies or abstains** —
it never presents an unconditional statistic.

## 5. Claim identity binding (Phase 3)

- Claims are compared only through `compare_claim_identity`; near-identical
  prose with different populations stays distinct (never merged, never
  averaged, never "reconciled").
- `SAME_POPULATION` is required before two claims may be called a
  contradiction (§7).
- Result/statistic values never enter identity.
- Every numerical assertion renders all eight dimensions in its identity
  block.

## 6. Answerability decision (Phase 5) — deterministic order

```
classify(question)
  -> resolve candidates (I.4 ONLY: exact() for id route, retrieve() otherwise)
  -> 0 results, 0 denials                      => OUT_OF_CORPUS
  -> 0 results, >0 denials                     => RESTRICTED (content-free)
  -> build assertions from authorized results only
       descriptive class  => doctrine assertion (no empirical claim)
       empirical class    => claim assertions + navigate() chains
       actionable class   => setup-card gate (Action Safety)
  -> per-assertion verdict:
       ASSERT | QUALIFY(reason) | GAP(reason)
  -> aggregate (first match wins):
       matched-identity conflict unresolved            => CONTRADICTED
       all assertions GAP: chain-less found            => UNSUPPORTED
       some ASSERT + some GAP                          => PARTIAL
       any QUALIFY or missing label or small-N         => ANSWERABLE_QUALIFIED
       all ASSERT with full citation chains            => ANSWERABLE
```

- **Abstention is success**: `UNSUPPORTED` / `OUT_OF_CORPUS` / `RESTRICTED` /
  `PARTIAL` answers carry honest gaps and never plausible filler.
- `OUT_OF_CORPUS` returns no corpus content beyond the echoed question
  classification.
- `RESTRICTED` discloses only that content was withheld (counts + reason
  codes) — never why-inside, never what.
- Action Safety (verbatim contract rule): with `ACTIONABLE` class, if no
  canonical Setup Card supports the requested action, the answer states that
  the model supplies context but a validated setup is not currently encoded.
- Descriptive/empirical class is recorded explicitly on every answer
  (`answer_class`), because the frozen contract allows descriptive/doctrinal
  answers without empirical claims.

## 7. Contradiction handling (Phase 6)

1. **Identity first.** Two claims are compared only on
   `SAME_POPULATION`. Different populations ⇒ never a contradiction; both are
   presented separately with their own identity (parallel populations are not
   contradictions).
2. **Matched identity, divergent outcomes** (e.g. VALIDATED vs FALSIFIED on
   the same population) ⇒ `CONTRADICTED` (or a mandatory conflict
   qualification when one side still asserts): inspect evidence authority
   (`support.classification`), version/time (`conflict.generation`,
   `canonical_version`, `supersedes_ids`), implementation semantics, and
   negative evidence.
3. **Never**: average conflicting statistics, pick the stronger-sounding
   number, or silently drop adverse evidence. The FALSIFIED/negative side is
   always exposed.
4. Conflict notes are bounded and auditable: claim ids, matched identity
   dimensions, both statuses, both generations, evidence ids, and the
   resolution (`DOWNGRADE_AND_EXPOSE_BOTH` or `SEPARATE_POPULATIONS`).
5. `conflict.contradicts_ids` on a record triggers the same path.

## 8. Citation and evidence chains (Phase 4)

- Empirical assertions require the traceable path **answer assertion →
  canonical claim → evidence → source artifact**, produced exclusively by
  I.4 `navigate()` (policy-guarded hop by hop).
- A citation carries: claim id, evidence id, artifact id, locator,
  `content_identity`, relation, source class/state — routing facts, never a
  body.
- Visual and conversation-derived sources never satisfy an empirical citation
  (they are never `classify_support`-empirical — asserted again in I.5
  fixtures).
- Missing link ⇒ disclosed as a gap with its reason code
  (`NO_EVIDENCE_REFERENCE`, `NO_SOURCE_ARTIFACT`, `NOT_IN_INDEX`, …); links
  are never manufactured from similarity.
- Descriptive answers are an explicit class (`DESCRIPTIVE`) citing the
  defining artifact of the model card as doctrine, never as empirical proof.
- A citation names the actual supporting artifact for that claim — never a
  merely similar retrieved document.

## 9. Exposure and information flow (Phase 7)

- `QAService` receives only a `RetrievalService` — it holds no gateway, no
  repository root, no corpus path, never calls `run_backfill` /
  `run_index_build`, and imports no backfill module (asserted by test).
- All content enters through `retrieve/exact/navigate` with the caller's
  `(principal, context)`; the frozen sequence and deny-before-load of I.4
  apply unchanged. There is **no alternative retrieval path**.
- Forbidden-content surface list (all tested): answer text, citations,
  summaries, debug traces, conflict descriptions, suggested follow-up
  questions, error messages.
- Follow-up suggestions are generated only from **authorized** result
  titles/ids (safe header/ranked-result facts of records the caller could
  already see).
- Mixed public/protected questions: only authorized results contribute;
  denied candidates appear solely as content-free denial entries (id,
  exposure, reason).
- Errors are content-free: fixed message + machine `kind`; no question echo,
  no corpus content.

## 10. Structured answer contract (Phase 9)

`Answer` (frozen fields, deterministic sorted-key JSON + `content_hash`):

| Field | Content |
|---|---|
| `outcome` | one of the seven §2.3 outcomes |
| `answer_class` | `DESCRIPTIVE \| EMPIRICAL \| ACTIONABLE \| COMPARATIVE` |
| `ladder` | `retrieved / supported / assertable / explainable` |
| `epistemic_label` | contract label or `None` (§2.2) |
| `assertions` | bounded statements: text (governed `retrieval_text` only), object id, type, status (verbatim), label, identity block (8 dimensions when numerical), support facts |
| `claim_refs` / `evidence_refs` | ids only — references, never duplicated canonical objects |
| `citations` | the §8 chain facts |
| `qualifications` | mandatory wording derived from governed fields (small-N, OOS, historical generation, research framing, action gap…) |
| `conflicts` | §7 conflict notes |
| `gaps` | unsupported/missing disclosures with reason codes |
| `limitations` | implementation limitations present in governed routing/leakage fields (e.g. `requires_evidence_card`, manual/automation class) |
| `denials` | content-free denial entries |
| `follow_ups` | bounded suggestions from authorized titles only |
| `generation`, `index_hash` | audit: which index answered |
| `content_hash` | sha256 of sorted-key payload; **no timestamps, no randomness** |

Validation rules: outcome ∈ frozen set; ladder rungs monotonic
(`assertable ⇒ supported ⇒ retrieved`, `explainable ⇒ assertable`);
empirical answers with assertions must have citations or explicit gaps;
no `INTERNAL_METHOD`/`INTERNAL_CODE` marker may appear anywhere in the
serialized answer; no raw artifact body (assertions quote governed
`retrieval_text`, which is already leakage-stripped synthesis); answer never
duplicates a canonical object as a new authority (ids + governed statements
only).

## 11. Corpus QA detectors, fixtures, coverage, freeze (Ch I.5.1–I.5.7)

Executable in `implementation/forge/book_i/bloc_i_5/tools/corpus_qa.py`
(read-only over the applied store + built index; exit 1 on violation):

1. **Orphan detector (I.5.1):** every record's `parent_ids`,
   `related_ids.target_id`, evidence ids and provenance links resolve within
   the index or artifact set; every CLAIM routes to ≥1 EVIDENCE (or is
   explicitly flagged as a disclosed gap); zero dangling launch references.
2. **Unsupported-number detector (I.5.2):** every CLAIM whose governed text
   contains a digit is evidence-linked (`support.evidence_ids` non-empty) or
   explicitly non-promoted (status outside assertable set) — 100% coverage.
3. **Status/generation leakage (I.5.3):** for all 30 records, index status
   == canonical persistence status; `conflict.generation` retained wherever
   the source states one (P90, Daily News research generation).
4. **Exposure leakage (I.5.4):** a subscriber build (`corpus.read.member`)
   contains zero OPERATOR_ONLY/RESEARCH_LAB/INTERNAL records; serialized
   golden answers contain no internal markers; PUBLIC_TEACHING never
   assigned by default.
5. **Golden fixtures (I.5.5):** `app/forge/qa/golden.py` holds explicit
   question → expected route fixtures for the seven launch models (EUR Daily
   News Rekey, EUR Weekly Engine, EUR Higher Order, XAU Game L1-L2-L3, JPY
   Carry Game, BTC D/W/M Tracker, Fib Range Birth) plus the eight truth
   traps; tests execute every fixture through the kernel.
6. **Coverage report (I.5.6):** exact counts by type/status/exposure/family,
   chain coverage, answerability-outcome coverage across fixtures —
   committed as `COVERAGE_REPORT_V1.md`.
7. **Freeze manifest (I.5.7):** schema versions, object/artifact/edge
   counts, index fingerprint + hash, test counts, known gaps and exclusions —
   committed as `BOOK_I_FREEZE_MANIFEST_V1.md`. Written **outside** `corpus/`
   (adding files under `corpus/` would perturb the frozen I.3 inventory).

## 12. Truth fixtures (Phase 8) — the eight traps

Committed fixtures (kernel-level, in `golden.py` + tests) that distinguish an
accurately qualified answer from a misleadingly confident one:

1. **Symmetry trap** — manual/operator validity ≠ automation parity;
   `MANUAL_OPERATOR`/`RESEARCH_ONLY` survive; no `AUTOMATION_APPROVED`.
2. **P90** — lineage/version-bound, never a performance statistic.
3. **BTC** — Tracker does not establish Game; missing BTC Game artifacts are
   disclosed, never invented.
4. **EURUSD** — Daily/Weekly/Higher-Order are three populations; answers
   never collapse them.
5. **XAU** — L3 destination / L2 path / L1 execution stay distinct layers.
6. **JPY** — USDJPY master, AUDJPY risk/execution, EURJPY referee; never an
   equal directional vote.
7. **Fib** — Range Birth doctrine not reduced to coordinates; R11
   overgeneration negative evidence preserved and citable.
8. **Research statistics** — small-N and research qualifiers survive into the
   answer (N shown when it materially changes interpretation).

## 13. Testing strategy (Phase 10)

- `tests/test_forge_qa.py` — the kernel: every numbered test in the operator
  checklist (supported/unsupported/missing-source/missing-evidence/wrong
  citation/conflict/negative/historical/candidate/research/manual-automation/
  eight identity dimensions/qualifiers/partial/abstention/no-match/unknown
  id/unknown status/restricted/mixed/no-leakage/determinism/no-promotion/
  truth traps/no-fabrication/no-endpoint/no-provider) mapped 1:1 to
  ACCEPTANCE clauses.
- `tests/test_forge_corpus_qa.py` — detectors, golden-route fixtures for the
  seven models, coverage report, freeze manifest.
- Regressions: I.1, I.2, I.3, I.4, II.1–II.4 focused suites, persistence,
  policy, Signal Guard, then the full suite; PostgreSQL CI path (QA adds no
  persistence/retrieval/policy change, but the PG job runs the whole suite
  and must stay green).

## 14. Security review

Threats: answer leaking protected content behind a denial; citation used as a
side channel (locator/content identity of forbidden records); conflict notes
describing restricted material; follow-up suggestions enumerating internal
titles; error messages echoing corpus; fabricated numbers; falsified→positive
promotion; averaging parallel populations; a second retrieval path bypassing
II.4; a QA endpoint; an LLM seam. Mitigations: single input boundary
(`RetrievalService`), content-free denials and errors, citations only for
authorized chain hops, follow-ups only from authorized titles, frozen
vocabulary, identity-first conflict rules, structural refusal of provider
imports (no seam exists), route set unchanged, deterministic replay tests.
