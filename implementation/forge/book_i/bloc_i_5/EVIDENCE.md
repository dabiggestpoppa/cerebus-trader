# Book I / Bloc I.5 — QA & Answer Contract — EVIDENCE

> Status: EXECUTED EVIDENCE RECORD
> Date: 2026-10-08
> Every claim below is reproducible from the repository at the recorded SHAs.

## 1. Starting point and lineage

- Operator starting HEAD: `b61a29c67d861bcfcbc27d228006e54ac405254e`
  (I.4 verification record; `origin/forge` fast-forward ancestor).
- Planning freeze: `60e067547b9d9165d94e4f074e0db0ba58e59e24`.
- Clean tracked tree at Phase 0; ratifications I.1–I.4 and II.1–II.4 present
  and PASS before any I.5 edit.
- Append-only ladder produced by this bloc (each commit a strict child of
  the previous; no amend/reset/rebase/squash/force):

| # | Rung | Commit subject |
|---|-------|----------------|
| 1 | PLAN + ACCEPTANCE | I.5 plan + acceptance (frozen A–R gates) |
| 2 | QA CONTRACT | frozen answerability/class/verdict/qualification/gap/conflict vocabularies, bounded Answer model, fail-closed validation |
| 3 | QA ENGINE (seams) | governed qualifier flags projected into retrieval records; policy-guarded `load_record()` preserving deny-before-load |
| 4 | QA ENGINE | deterministic question classification, answer-authority table, QA kernel, 18 golden fixtures |
| 5 | QA ENGINE (corpus) | corpus QA detectors I.5.1–I.5.4, `corpus_qa.py` harness, committed coverage report, Book I freeze manifest, 32 corpus tests |
| 6 | TESTS | 109-test kernel suite (clauses A–P) + 11 adversarial attempts + missing-evidence gap disclosure in the kernel |
| 7 | TESTS (supplement) | unknown status/label refusal (#25) + conversation-derived provenance (#33) |
| 8 | EVIDENCE | this file |
| 9 | RATIFICATION | PASS ratification |

## 2. Contract interpretation (frozen vocabulary, no new enums)

- The kernel uses exactly the frozen `EvidenceStatus` I.1 enum (import
  identity: `qa.contract.EvidenceStatus is canonical.EvidenceStatus` —
  proven by `test_o5_no_new_enum_values_reuse_frozen_vocabularies`).
- Seven answerability outcomes, verbatim: `ANSWERABLE,
  ANSWERABLE_QUALIFIED, PARTIAL, UNSUPPORTED, CONTRADICTED, OUT_OF_CORPUS,
  RESTRICTED` (no others exist; proven by `test_d1`).
- PLAN §6 decision order implemented literally: 0 results + 0 denials ⇒
  OUT_OF_CORPUS; 0 results + >0 denials ⇒ RESTRICTED; conflicts ⇒
  CONTRADICTED; all-GAP ⇒ UNSUPPORTED; mixed ⇒ PARTIAL; qualification ⇒
  ANSWERABLE_QUALIFIED; all-ASSERT + cited ⇒ ANSWERABLE.
- The four-state ladder is monotonic by pydantic validation law
  (`assertable ⇒ supported ⇒ retrieved`, `explainable ⇒ assertable`);
  supported and status authority are evaluated independently — a supported
  CANDIDATE is never unqualified (clause C4, `test_c4`).
- Status authority is a pure function of status (`authority_for`): PLAIN /
  QUALIFIED / DESCRIPTIVE_ONLY / NEGATIVE_ONLY. Relevance, ranking and
  question wording never enter (`test_c6`, `test_g7`).
- Known interpretation note: I.4-style lexical retrieval returns governed
  records for any multi-token question (OR-token semantics, frozen in I.4);
  per frozen PLAN §6 the OUT_OF_CORPUS branch applies only to the
  0-results/0-denials case, which is what `test_d6` proves with an
  all-entitled context. A member asking a no-match question with denied
  candidates lands on RESTRICTED (D7), also proven.

## 3. Exact answerability outcomes observed

Golden fixtures (18) executed through the real kernel — 0 failures:

| Outcome | Count |
|---|---|
| ANSWERABLE_QUALIFIED | 12 |
| PARTIAL | 3 |
| ANSWERABLE | 1 |
| RESTRICTED | 1 |
| UNSUPPORTED | 1 |

Answer classes across the same 18: DESCRIPTIVE 5, EMPIRICAL 7, ACTIONABLE
3, COMPARATIVE 3.

All seven outcomes are exercised by the suite: CONTRADICTED via the
identity-matched synthetic conflict (`test_h2`), OUT_OF_CORPUS via the
no-match question (`test_d6`), RESTRICTED via the anon ask (`test_d7`) and
the member XAU-120 fixture.

## 4. Claim / evidence / source traceability

- Every empirical assertion resolves `assertion → claim → evidence → source
  artifact` with artifact id, locator, `sha256:` content identity, relation
  and source state (`test_f1`, `test_f2` verifies each cited artifact
  belongs to the cited claim's own provenance chain).
- Citations originate only from policy-guarded `navigate()`/`_load()` hops
  (kernel holds one seam: `RetrievalService`; static proof in
  `test_a1_a2`).
- Missing links are disclosed, never manufactured: an evidence id that does
  not resolve to a loadable governed record produces a
  `NO_SOURCE_ARTIFACT` gap and no citation (kernel change in rungh 6,
  proven by `test_c5` and adversarial `test_adv1`).
- Descriptive answers are explicitly `answer_class=DESCRIPTIVE` with
  `numerical=False` assertions (`test_b3_descriptive`,
  `test_k7_fib_negative_evidence_and_range_birth_doctrine`).

## 5. Corpus QA detectors and freeze (frozen chapters I.5.1–I.5.7)

`PYTHONPATH=. python implementation/forge/book_i/bloc_i_5/tools/corpus_qa.py`
— exit 0, `findings=0`:

- objects 30 (MODEL 7, CLAIM 10, EVIDENCE 10, SETUP 3), artifacts 29,
  edges 38, quarantined 9, card-quarantines 0
- claims 10, evidence-linked 10/10; digit-bearing 6, evidence-linked 6/6
- exposure inventory: SUBSCRIBER_MODEL 24, RESEARCH_LAB 4, OPERATOR_ONLY 2
  (PUBLIC_TEACHING / INTERNAL_* = 0)
- index: generation 1, source_fingerprint
  `9675431033dd1fa667e3ef3d7ea65526c7bf5a545bf073875af11496236fa226`,
  index_hash `28be01dbab570f9391df23540ee0a35618f95ebed5a0e7345094de2e850dac9b`

Committed artifacts: `COVERAGE_REPORT_V1.md` (deterministic regeneration,
byte-identical across runs — `test_coverage_report_is_deterministic_and_all_pass`)
and `BOOK_I_FREEZE_MANIFEST_V1.md` outside `corpus/` (frozen I.3 inventory
untouched — `test_freeze_manifest_exists_and_matches_live_state`).
Detector tamper-sensitivity proven: missing parent, claim route gap,
promoted-unlinked number, index/canonical status divergence, PUBLIC_TEACHING
default, internal body, membership, quarantine (8 negative tests in
`test_forge_corpus_qa.py`).

## 6. Qualification and abstention results

- Mandatory qualifications observed in real fixtures: SMALL_N (with N),
  RESEARCH_SAMPLE, RELATIONSHIP_STATISTIC, FORWARD_OOS, CANDIDATE_STATUS,
  RESEARCH_FLAG, NEGATIVE_EVIDENCE, IDENTITY_UNSPECIFIED; synthetic
  HISTORICAL_GENERATION / SUPERSEDED / PARKED proven (`test_g2`, `test_g6`).
- `ANSWERABLE` refuses any qualification or gap at validation
  (`test_d4`, `test_n5`).
- Abstention outcomes all carry honest disclosure and never fabricate:
  UNSUPPORTED carries `INSUFFICIENT_EVIDENCE` (`test_d2`), OUT_OF_CORPUS is
  content-free (`test_d6`), RESTRICTED is content-free with denials only
  (`test_d7`), PARTIAL discloses every gap (`test_d5`), parametrized
  `test_d8`.

## 7. Adversarial results (Phase 11) — 11/11 held

| Attempt | Result |
|---|---|
| invent a missing statistic | assertion text identical to governed record text; gap detail contains no numerals beyond the governed set (`test_adv1`) |
| cite an unrelated artifact | `AnswerValidationError` (`test_adv2`, `test_f6`) |
| ignore a negative result | FALSIFIED + NEGATIVE_EVIDENCE survive (`test_adv3`) |
| upgrade candidate to validated | status stays CANDIDATE, label CANDIDATE (`test_adv4`) |
| manual setup → automated signal | no `AUTOMATION_APPROVED`; action limitation present (`test_adv5`) |
| reveal restricted via citation | no `N=25`, no restricted evidence id in citations (`test_adv6`, `test_j4`) |
| combine parallel populations | one assertion = one record's own text (`test_adv7`) |
| infer current from historical | HISTORICAL_GENERATION qualification, never plain ANSWERABLE (`test_adv8`) |
| visual/conversation artifact as proof | VISUAL_ONLY and CONVERSATION_DERIVED ⇒ GAP, no citations (`test_adv9`, `test_f3`) |
| fabricate BTC Game rules | no CLAIM assertions invented; gap disclosed (`test_adv10`) |
| shotgun nonsense questions | every ask returns one of the seven outcomes; forbidden phrases never appear (`test_adv11`, `test_j5`) |

## 8. Exposure safety

- Deny-before-load preserved: the kernel loads only through
  `RetrievalService.load_record` behind the II.4 guard (seams rungh 3).
- Member never sees research-lab bodies on any content surface; citation
  locators of restricted evidence never appear (`test_j1`, `test_j2`).
- Mixed authorized/restricted question: authorized side contributes,
  restricted side surfaces only as content-free denial/gap (`test_j3`,
  `test_j4` — denial entries carry exactly `{object_id, exposure,
  reason_code}`).
- Internal markers (`INTERNAL_METHOD`, `INTERNAL_CODE`) rejected on every
  content surface by `validate_answer` (`test_n5`, `test_j2`).
- Errors are content-free: `IndexNotBuilt` fixed message carries no
  question echo or corpus content (`test_j5`).

## 9. Model-family truth fixtures (K clauses)

- Symmetry: no `AUTOMATION_APPROVED` ever; setup qualifier flags survive
  verbatim (`test_k1`).
- P90: lineage vocabulary only; `P90 win rate `/`P90 performance` never
  appear (`test_k2`).
- BTC: no `CL.BTC*`/`*GAME*` ids, `NO_EVIDENCE_REFERENCE` gap, no invented
  rules (`test_k3`, `test_adv10`).
- EURUSD: daily/weekly/HO identities pairwise PARALLEL (`test_k4`).
- XAU: assertion layer fields identical to index records — no layer bleed
  (`test_k5`).
- JPY: role text present, `EURJPY is the master`/`equal directional vote`
  absent, no EURJPY claim asserted (`test_k6`).
- Fib: R11 stays FALSIFIED + NEGATIVE_EVIDENCE; Range Birth answers are
  descriptive doctrine (`test_k7`, `test_adv3`).
- Research statistics: RESEARCH_FLAG + SMALL_N + `N=25` survive for
  research context; member receives UNSUPPORTED/RESTRICTED without `N=25`
  (`test_k8`).

## 10. Exact tests

| Suite | Count | Result |
|---|---|---|
| `tests/test_forge_qa.py` (kernel + adversarial) | 110 | pass |
| `tests/test_forge_corpus_qa.py` (detectors + golden + freeze) | 32 | pass |
| **I.5 focused total** | **142** | **pass** |
| Book I regressions (retrieval/backfill/canonical/identity) | 299 | pass |
| persistence/policy/provenance/schemas/service | 223 | pass |
| Signal Guard + signal/state/vision suites | 48 | pass |
| **Full suite `python -m pytest -q`** | **712 passed, 19 skipped** | **green** |

The 19 skips are the PostgreSQL integration tests (require a live PG; they
run in CI's `postgres` job — same arrangement as I.1–I.4). No test was
weakened or deleted; all pre-existing tests unchanged (diff touches only
`app/forge/qa/*`, new `tests/test_forge_qa.py`, new
`tests/test_forge_corpus_qa.py`, new `implementation/forge/book_i/bloc_i_5/*`).

Checklist 1–46 → tests: 1→d3/f1, 2→c3, 3→c5, 4→f5, 5→f6/f2, 6→h1/h2,
7→g1, 8→g2, 9→c4/g3, 10→k8/g4, 11/34→k1/adv5, 12→e2/k4,
13–18→`test_e4_e12_to_e18_dimension_mismatch_stays_parallel[8 dims]`,
19→g5/i3, 20→g4/k2, 21→d5, 22→d8/d6/d7/d2, 23→d6, 24→b2/j5,
25→e6, 26→d2, 27→j3, 28→j5, 29→j4, 30→a4/p1/p2/l5, 31→c6/g7,
32→f3/adv9, 33→f3/adv9, 35→k2, 36→k3, 37→k4, 38→k5, 39→k6, 40→g1/k7,
41→i2/adv1, 42→o2, 43→o1, 44→§10 regressions, 45→§10 Signal Guard,
46→§10 full suite.

## 11. CI / PostgreSQL evidence

- Local full suite (Windows, Python 3.11): 712 passed, 19 skipped —
  recorded above.
- **CI verification (post-push record):** workflow `FORGE Tests`
  (`forge-tests.yml`) run **37872174840** on final head
  `686faa7627d36d502351d90eae41aadd6a81f49e`:
  - `test` job ✓ — `712 passed, 19 skipped` (3.94s)
  - `postgres` job ✓ — full suite against live PostgreSQL:
    `731 passed` (0 failed = 712 + all 19 PG tests), plus PG integration
    evidence `19 passed` and II.3 identity/session evidence `7 passed,
    12 deselected`.
  - Remote `origin/forge` verified at `686faa7` after fast-forward push
    `b61a29c..686faa7` (strict descendant; no force).
- QA adds no persistence, retrieval-boundary or policy-behavior change
  (the only engine change is inside `app/forge/qa/kernel.py`), so the PG
  job runs the whole suite unchanged.

## 12. Known gaps (never invented away)

1. DOCTRINE/TERM/LINEAGE compiler = 0 lines; no canonical catalog files
   exist. Declared unsupported until a catalog is ratified.
2. AUC-001 claim identity gap: metric is `NOT_SPECIFIED_IN_SOURCE` —
   labeled by the kernel (`IDENTITY_UNSPECIFIED`) rather than filled.
3. 9 quarantined out-of-scope sources remain absent from persistence by
   construction.
4. Membership must-exist/must-not-exist lists were never frozen.
5. No natural contradiction exists in the frozen corpus; CONTRADICTED is
   proven with a synthetic identity-matched twin claim (index-level tamper),
   which is the strongest available controlled experiment.
6. Weak OR-token lexical retrieval (frozen I.4 behavior) can return
   governed records for off-corpus multi-token questions; the kernel then
   answers from governed content only — no fabricated knowledge — and the
   frozen PLAN §6 assigns the 0-results case to OUT_OF_CORPUS/RESTRICTED as
   proven.
7. PostgreSQL integration tests are skipped locally and proven by the CI
   `postgres` job.

## 13. Later Book IV handoff

- The frozen `Answer` representation (PLAN §10, clause N) is the stable
  machine-readable interface: outcome, class, ladder, label, assertions
  with eight-dimension identity, claim/evidence refs, citations,
  qualifications, conflicts, gaps, limitations, denials, follow-ups,
  generation, index_hash, content_hash.
- Book IV may consume `QAService.ask(principal, context, question)` only;
  it must not re-implement retrieval, identity comparison, status authority
  or exposure decisions.
- `generation` + `index_hash` on every answer tie any consumer output to an
  exact index state for audit.
