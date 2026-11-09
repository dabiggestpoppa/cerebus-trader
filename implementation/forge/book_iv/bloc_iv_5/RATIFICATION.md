# BOOK IV / BLOC IV.5 — RATIFICATION
## BA-30 RUNG 2

**Contract:** `ASK_ANSWER_CONTRACT_V1`
**Starting HEAD:** `5baec01ce089c4a65543b2887a8fc15088d6f195`
**Scope ratified:** the deterministic answer compiler, validator set, citation
renderer, refusal layer and response record.
**Scope not ratified:** production answering, entitlements, licensing,
retention and live market freshness.

---

## 1. VERDICT

| Dimension | Verdict |
|---|---|
| Deterministic binding requirements (F1/F2) | **PASS** |
| Non-regression of Books I–III and IV.1–IV.4 | **PASS** |
| Frozen integrity (hashes, routes, migrations) | **PASS** |
| Production answering | **NOT RATIFIED** |
| F3 owner decisions | **OPEN (5)** |
| F4 external prerequisites | **OPEN (2)** |
| IV.6 handoff | **READY** |

**IV.5 RUNG 2: PASS.** Every deterministic binding requirement passes, both
CI jobs are green at the final head, and the remaining open items are the five
F3 and two F4 gates named in `FEASIBILITY_GATE.md`.

---

## 2. WHAT WAS RATIFIED

1. Exactly one input contract: `GatewayDraft(status=UNVALIDATED)` with its
   originating `AuthorizedContextPackage` and `AuthorizedContextManifest`.
2. Exactly one terminal outcome: `ValidatedAnswer` xor
   `GovernedAnswerRefusal`, both carrying a `FinalResponseRecord`.
3. The fixed validator order: upstream, numerical, layer, setup, status,
   freshness, leakage, citation, assembly.
4. The six frozen answer refusal codes and their precedence.
5. 76 requirement drivers, 10 cross-cutting drivers, 86 acceptance tests.
6. 46 golden scenarios that reproduce byte-identically.
7. Presentation-only repair: no fact, number, status, layer, eligibility,
   entitlement or metric is added or altered.
8. No model, provider, retrieval or market call anywhere in the answer layer.

---

## 3. WHAT WAS NOT RATIFIED

The following remain explicitly outside this ratification:

- **R26** — the public citation presentation contract.
- **R39** — authority for an L1 trigger to override a higher-layer no-go.
- **R53** — current-state materiality and the required `as_of`/cutoff.
- **R55** — materiality of missing freshness.
- **R63** — production ratification of the refusal-precedence order.
- **R58** — corpus reproduction and licensing limits.
- **R71** — retention policy for answer prose.

Until those close:

- no citation surface beyond typed provenance is authorized;
- no cross-layer override is recognized (violations refuse);
- materiality uses a declared policy and refuses when unconfigured;
- missing freshness refuses rather than assuming a date;
- the documented precedence order is implemented but not product-ratified;
- corpus reproduction is bounded by a per-item quote ceiling, not a licence;
- answer prose is never persisted.

---

## 4. TEST AND EVIDENCE BASIS

```
python -m pytest tests/test_forge_ask_cerebus_answer.py -q     -> 86 passed
python -m pytest -q                                            -> 2461 passed, 29 skipped
```

Frozen integrity, fixture digests, refusal precedence, determinism and the
no-network guarantee are all asserted inside the suite, not merely described.
Full detail is in `EVIDENCE.md`.

---

## 5. CONDITIONAL PASS TERMS

1. A green deterministic suite is **contract evidence only** (`A-86`).
2. F3/F4 items may not be closed by prose, a fixture or a model assumption.
3. Any change to the six refusal codes, the validator order or the input
   contract requires a new ratification.
4. IV.6 must run the launch golden suite before any production answer claim.
5. Book V may render both outcomes but may not add or reinterpret content.

---

## 6. SIGN-OFF RECORD

| Role | Scope | Status |
|---|---|---|
| IV.5 answer owner | compiler, validators, citations, record | PASS |
| IV.4 gateway owner | draft contract consumed unchanged | acknowledged |
| IV.3 context owner | package/manifest contract consumed unchanged | acknowledged |
| IV.6 evaluation owner | 86 drivers + 46 scenarios received | ready |
| Product/UX (F3) | citation surface, materiality, precedence wording | OPEN |
| Security/Ops (F4) | retention, corpus licensing | OPEN |
| Book VI | entitlement propagation | out of scope |
