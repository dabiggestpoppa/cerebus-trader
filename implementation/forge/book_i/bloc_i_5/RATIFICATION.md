# Book I / Bloc I.5 — QA & Answer Contract — RATIFICATION

> Status: **PASS — RATIFIED (CLOSED)**
> Date: 2026-10-08
> Frozen gates: `implementation/forge/book_i/bloc_i_5/ACCEPTANCE.md` (A–R).
> Evidence: `implementation/forge/book_i/bloc_i_5/EVIDENCE.md`.

## Verdict

**PASS.** Every frozen acceptance clause A–R is executable-proven against
the committed code and tests. I.5 is CLOSED. No further work on I.5 is
authorized or required.

## Explicit ratification statements

1. **A (authority/input)** — the QA kernel consumes only governed
   `RetrievalService` results through a single seam; static seam proof
   (`test_a1_a2`), generation/index-hash audit identity (`test_a3`),
   byte-identical repeats (`test_a4`), deterministic resolution of
   unclassifiable input (`test_a5`).
2. **B (classification)** — pure token/grammar classification, exact
   canonical-id routing, DESCRIPTIVE safe fallback, crosswalk alias
   expansion without rewrites, unknown scope values fail closed
   (`test_b1`–`test_b5`).
3. **C (ladder)** — four booleans on every answer, monotonic by validation
   law, found-but-unsupported never implies supported, supported never
   implies unqualified assertion, explainable requires the citation chain,
   no authority promotion by ranking or wording (`test_c1`–`test_c6`).
4. **D (outcomes)** — exactly seven outcomes exist; UNSUPPORTED carries
   INSUFFICIENT_EVIDENCE; full support ⇒ ANSWERABLE; mandatory
   qualifications forbid plain ANSWERABLE; mixed ⇒ PARTIAL with every gap
   disclosed; 0-results/0-denials ⇒ content-free OUT_OF_CORPUS;
   0-results/denials ⇒ content-free RESTRICTED; abstention outcomes are
   successful results (`test_d1`–`test_d8`).
5. **E (identity)** — all eight dimensions verbatim on every numerical
   claim assertion; canonical comparison only (PARALLEL vs SAME_POPULATION);
   result values cannot enter identity (no such field); each dimension
   mismatch independently keeps claims distinct; incomplete identity is
   refused (`test_e1`–`test_e6`, parametrized over all eight dimensions).
6. **F (citations)** — complete claim → evidence → artifact chains with
   sha256 identity and locator; artifacts verified to belong to their
   claim's own provenance; visual/conversation sources never cite;
   descriptive answers explicit; missing links disclosed as gaps;
   wrong-source citations rejected by validation (`test_f1`–`test_f6`).
7. **G (status authority)** — FALSIFIED only as negative evidence;
   HISTORICAL generation-bound and qualified; CANDIDATE/RESEARCH_FLAG never
   unqualified; small-N travels with N; DESCRIPTIVE never numerical;
   SUPERSEDED/PARKED labeled; status never changes with wording or ranking
   (`test_g1`–`test_g7`).
8. **H (contradictions)** — contradiction only on SAME_POPULATION;
   matched divergence ⇒ CONTRADICTED exposing both statuses, generations
   and evidence ids; different populations never a contradiction;
   no averaging, no strongest-result selection; conflict notes bounded,
   auditable and content-free (`test_h1`–`test_h5`).
9. **I (numerical safety)** — no forbidden conversion phrases on any
   answer; every numeral traceable to governed text; unsupported numerical
   generalization refused; identity-mismatched numbers never combined
   (`test_i1`–`test_i4`).
10. **J (exposure)** — single authorized boundary; no research-lab body on
    any member content surface; mixed questions build only from authorized
    results; denials content-free (exact three fields); errors content-free
    and questions never raise (`test_j1`–`test_j5`).
11. **K (truth fixtures)** — symmetry, P90, BTC, EURUSD, XAU layers, JPY
    asymmetry, Fib negative evidence, research statistics all proven by
    kernel tests AND by the 18 golden fixtures (`test_k1`–`test_k8`,
    `tests/test_forge_corpus_qa.py`).
12. **L (corpus detectors)** — I.5.1–I.5.4 detectors exit 0 with zero
    findings over the real corpus; deterministic rebuild answers identical
    from QA's perspective; known gaps labeled, never invented
    (`tests/test_forge_corpus_qa.py`, `tools/corpus_qa.py`).
13. **M (coverage/freeze)** — golden fixtures exist for all seven launch
    models and the eight traps and execute through the kernel;
    `COVERAGE_REPORT_V1.md` generated and committed;
    `BOOK_I_FREEZE_MANIFEST_V1.md` committed outside `corpus/`.
14. **N (structured contract)** — frozen fields on every answer;
    deterministic sorted-key JSON with content_hash and no timestamps;
    references by id only (no duplicated authority); assertion text is
    governed retrieval_text; validation fails closed, never repairs
    (`test_n1`–`test_n5`).
15. **O (boundary)** — no LLM/provider/dependency; FORGE routes remain
    exactly `{health, ready, meta}`; `discover_migrations() == [1, 2]`; no
    commercial objects; no new enum values (`test_o1`–`test_o5`).
16. **P (reproducibility)** — identical questions produce identical
    field-by-field output and content_hash; ordering total and stable
    (`test_p1`, `test_p2`).
17. **Q (PostgreSQL/CI)** — full suite green locally (712 passed,
    19 skipped = PG-only); CI `test` + `postgres` jobs verified green on
    the final head and recorded in the post-push verification record.
18. **R (regression)** — I.1–I.4 and II.1–II.4 focused suites, persistence,
    policy and Signal Guard all green (299 + 223 + 48); full suite green;
    no existing test weakened or deleted.

## Adversarial closure

All eleven Phase 11 attempts (invent statistic, unrelated citation,
ignored negative result, candidate upgrade, manual→automated promotion,
restricted leak through citation, parallel-population merge,
historical→current, visual-as-proof, BTC Game fabrication, shotgun
nonsense) either produced a properly qualified answer or failed closed.
Recorded in EVIDENCE §7.

## Handoffs

- **Next frozen dependency:** Book II / Bloc II.5 (or the next bloc named
  by the operator) is **NOT started**. Book IV consumption of the frozen
  `Answer` interface is authorized only via EVIDENCE §13 handoff notes.
- **STOP:** this bloc ends here per operator handoff. No Book IV, Book VI
  or other bloc is begun without a new handoff.
