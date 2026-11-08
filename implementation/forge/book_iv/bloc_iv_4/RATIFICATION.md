# BOOK IV / BLOC IV.4 — RATIFICATION
## LLM GATEWAY & MODEL ROUTING — BA-29 RUNG 2

**Ratified code head:** `b75dc7e`
**Starting head:** `5ace8dfcd57f12996d168120ca74ee20e20e3f52`
**Contract:** `ASK_GATEWAY_CONTRACT_V1`
**Verdict:** **PASS — deterministic fake-provider contract satisfied**
**Scope:** Book IV / Bloc IV.4 only

Code-head CI: run `42530782457`, `test` and `postgres` both SUCCESS.
Final documentation-head CI is recorded in the BA-29 final report.

---

## 1. RATIFICATION DECISION

The deterministic IV.4 gateway is ratified for the boundary:

`AuthorizedContextPackage + AuthorizedContextManifest + declared RoutingPolicy
→ GatewayDraft(status=UNVALIDATED) or GatewayRefusal`

The gateway composes the frozen Book II `LLMProvider` port. It does not retrieve,
re-read canonical bodies, validate facts or create an answer authority.

---

## 2. BINDING EVIDENCE

| Item | Measured result |
|---|---|
| Requirements | 60/60 (R1–R60) |
| Exact named drivers | 72/72 (A-01–A-72) |
| IV.4 suite | 72 passed |
| Golden fixtures | 24/24 byte-identical |
| IV.3 context | 93 passed |
| IV.2 retrieval | 72 passed |
| IV.1 interpreter | 60 passed |
| Book III integration | 96 passed |
| III.1 compatibility | 49 passed |
| WP-3B | 66 passed |
| Book II providers | 74 passed |
| Book I policy/retrieval | 86 + 124 passed |
| Full repository | 2,375 passed, 29 skipped |
| Real network/provider call | None |

No binding test is skipped, xfailed, renamed or a placeholder.

---

## 3. RATIFIED SURFACES

- `ASK_GATEWAY_CONTRACT_V1`.
- Frozen Book II `LLMRequest`/`LLMProvider`/`LLMResponse`/`LLMUsage` port.
- Declared, versioned routing with no production default.
- Separate BEGINNER/OPERATOR/RESEARCHER prompt contracts.
- Trusted-control/untrusted-data prompt envelope.
- `GatewayDraft` with mandatory `UNVALIDATED` status.
- Package-local citations and evidence-typed numeric links.
- Mandatory no-go, insufficiency, conflict, historical and research-only
  preservation.
- Bounded timeout, retry, cancellation and declared fallback.
- Deterministic usage/cost/latency accounting.
- Exposure-safe attempts and traces.
- Ordered scripted fake with adversarial and transport behaviors.
- Conforming provider replacement.

---

## 4. F3/F4 STATUS — REMAIN OPEN

| ID | Requirement | Status |
|---|---|---|
| R7 | Authorized route catalog/budget policy | F3 OPEN |
| R31 | Production alternate/fallback policy | F3 OPEN |
| R42 | Account/feature cost allocation | F3 OPEN |
| R18 | Provider-accurate tokenizer | F4 OPEN |
| R41 | Authoritative provider pricing | F4 OPEN |
| R48 | Provider retention/training terms | F4 OPEN |
| R55 | Real provider/model candidate matrix | F4 OPEN |

The fixtures use explicit local policies. They do not select a production
provider, approve a fallback catalogue, establish billing truth or authorize a
real request.

---

## 5. FROZEN INTEGRITY

No modification was made to:

- Book I corpus, policy or retrieval;
- Book II provider interfaces, registry, policy or resilience primitives;
- Book III intelligence contracts;
- IV.1 interpreter;
- IV.2 retrieval;
- IV.3 context packager, schema or fixtures;
- routes or SQL migrations;
- provider readiness configuration.

Frozen route/context hashes and migrations are rechecked by A-70/A-71.

---

## 6. IV.5 READINESS

**READY for validation, not validated.**

IV.5 must consume `GatewayDraft` as untrusted input and independently determine
whether any claim, number, status, layer, generation, metric, citation or
answer-level proposition may become a validated CEREBUS answer.

IV.4 deliberately preserves Q4-07 and Q4-11–Q4-16 as unvalidated drafts for
that purpose. A gateway draft is not a factual pass merely because its schema
and references are valid.

---

## 7. RATIFICATION VERDICT

**PASS** — the deterministic IV.4 fake-provider gateway contract is implemented,
tested, reproduced and frozen within its stated scope.

**PARTIAL** — F3/F4 production dependencies remain open.

**FAIL** — none in the authorized IV.4 contract.

A PASS does **not** approve production OpenRouter integration. A PASS does
**not** mean IV.5 has validated model output. This ratification does not close
Book IV.

---

## 8. APPEND-ONLY RECORD

Planning head: `5ace8dfcd57f12996d168120ca74ee20e20e3f52`

| Stage | Commit |
|---|---|
| 24 fixtures and generator | `f03788e` |
| Gateway implementation | `7b7c837` |
| 72 acceptance drivers | `b75dc7e` |
| Evidence and ratification | `413b9f3` |
| CI receipt | `CI_RECEIPT.md` — run `42530782457` |

No amend, squash, rebase, reset or force-push is used. `.bu_tmp/` is preserved.
