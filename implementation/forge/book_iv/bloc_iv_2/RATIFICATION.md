# BOOK IV / BLOC IV.2 — RATIFICATION
## HYBRID RETRIEVAL & EVIDENCE ROUTING — BA-27 RUNG 2

**Base HEAD:** `38b322b562317fdd42ad8ea61a9866b2931966a7`
**Contract:** `RETRIEVAL_CONTRACT_V1`
**Scope:** `AskCerebusQueryPlan → AuthorizedRetrievalBundle`
**Ratification date:** 2026-11-07

---

## 1. VERDICT

**PASS — IV.2 deterministic retrieval contract complete.**

This verdict covers the deterministic composition, authorization, evidence
routing, refusal and trace contract defined by the committed IV.2 planning
packet. It does **not** declare Book IV complete, close F3/F4, or certify
production retrieval.

---

## 2. BASIS

The ratification rests on the committed binding documents:

- `PLAN.md`
- `ACCEPTANCE.md`
- `FEASIBILITY_GATE.md`
- `DEPENDENCY_HANDOFF.md`

and the measured record in `EVIDENCE.md`.

| Gate | Result |
|---|---|
| 64 requirements reconciled | PASS — 64/64 |
| 72 exact drivers present | PASS — 72/72 |
| Exact names, no rename/merge/skip/xfail | PASS |
| Twelve test groups T1–T12 | PASS |
| Eighteen golden scenarios Q2-01–Q2-18 | PASS — 18/18 |
| Byte-identical fixture reproduction | PASS — A-64 |
| Structured canonical resolution | PASS |
| Authorization before protected load | PASS |
| Claim/evidence insufficiency behavior | PASS |
| III.6 typed routing and current refusal | PASS |
| Historical/current generation separation | PASS |
| Conflict/incomparable/negative evidence | PASS |
| Semantic port has no authority | PASS |
| Deterministic bundle/trace identity | PASS |
| Frozen upstream integrity | PASS |
| Full repository regression | PASS — 2210 passed, 29 pre-existing skips |

Measured IV.2 command:

`python -m pytest tests/test_forge_ask_cerebus_retrieval.py -q -p no:cacheprovider`

Result: **72 passed in 2.57s**.

---

## 3. SECURITY AND AUTHORITY FINDINGS

- Candidate headers are read before authorization; protected bodies load only
  after Book II permits the object.
- Denied direct ids, relationships, citations, setup objects, intelligence
  requests and semantic neighbours perform zero protected body loads.
- Denials do not disclose denied ids, names or existence in consumer output.
- Researcher depth is not treated as entitlement.
- Policy-engine failure fails closed.
- No second canonical store and no second policy matrix were created.
- Current market state remains `PROVIDER_NOT_CONFIGURED`; history is not
  substituted for CURRENT.

---

## 4. EVIDENCE-INTEGRITY FINDINGS

- Canonical identity is exact and source-backed.
- Semantic passages remain supporting context and cannot promote status or
  supply numbers.
- Claims lacking evidence return `EVIDENCE_INSUFFICIENT` with no numerical
  answer.
- Matched identities with conflicting values retain both references and emit
  `EVIDENCE_CONFLICT`; different identities emit `INCOMPARABLE_EVIDENCE`.
- Negative evidence retains original status and generation and is never a
  trading signal.
- The fixture generator reproduces all 18 payloads and the manifest
  byte-identically.

---

## 5. REMAINING DEPENDENCIES

The six frozen F3/F4 dependencies remain open with their original owners:

- **F3/R25** — OOS/reproduction verdicts (Book IV.5 / Book VII).
- **F3/R30** — durable historical snapshot retrieval (Book III / Book VI).
- **F3/R57** — enumeration/abuse governance (Book IV.6 / Book VIII).
- **F4/R12** — real semantic index and embeddings (Book VII / platform).
- **F4/R23** — governed statistical population/sample/period bodies (Book I
  corpus / Book VII).
- **F4/R53** — Book VI entitlement projection (Book VI).

They were not closed with synthetic fixtures, fakes or placeholder authority.
Their bounded refusals and limitations are part of the passing contract.

---

## 6. WHAT THIS RATIFICATION DOES NOT CLAIM

It does not claim:

- that Book IV is complete;
- that IV.3 or later blocs are implemented;
- that production semantic/vector retrieval exists;
- that every numerical claim has complete governed statistical metadata;
- that OOS/reproduction is verified for every claim;
- that historical snapshots are durably retrievable;
- that commercial entitlement is enforced;
- that enumeration/abuse resistance is production-grade;
- that the market-data provider is configured.

---

## 7. INTEGRITY ATTESTATION

- Changes are confined to the IV.2 package, its acceptance test and its fixture
  packet.
- Book I, Book II, Book III, III.6, IV.1, routes, migrations and the
  market-data seam are unmodified.
- Frozen hashes remain at their pinned values.
- `.bu_tmp/` and unrelated files were preserved.
- The commit ladder is append-only: fixtures/generator, implementation, tests,
  repairs, evidence/ratification, then CI receipt.
- No amend, squash, rebase, reset or force-push is authorized or used.
- Final CI evidence is recorded separately after both jobs complete.

---

## 8. AUTHORIZATION OUTCOME

BA-27 Rung 2 is ratified for the deterministic IV.2 retrieval contract only.

**Next authorized boundary:** none in this rung. IV.3 planning or
implementation requires a new operator directive.

**Final status:** `PASS — IV.2 deterministic retrieval contract complete.`
**Book IV status:** incomplete pending IV.3–IV.6.
**F3/F4 status:** open, bounded and correctly refused where authority is absent.
