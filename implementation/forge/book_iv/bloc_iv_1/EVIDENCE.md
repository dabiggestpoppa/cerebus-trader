# BOOK IV / BLOC IV.1 — IMPLEMENTATION EVIDENCE

**Bloc:** IV.1 · **Rung:** BA-26 Rung 2 · **Mode:** deterministic interpreter only

---

## 1. Starting head and foundation

| Check | Result |
|---|---|
| Starting HEAD == `origin/forge` | `6ca573d226b14100b9244b3a8d7bb92f68b5907f` |
| Rung 1 planning documents present | 4/4 |
| Provider seam | `NOT_CONFIGURED`, `required: false` |
| Migrations | `001`–`004` only; none added |
| Book I/II/III source changes | none |

## 2. Implemented modules

```
app/forge/ask_cerebus/__init__.py
app/forge/ask_cerebus/interpreter/__init__.py
app/forge/ask_cerebus/interpreter/versions.py
app/forge/ask_cerebus/interpreter/enums.py
app/forge/ask_cerebus/interpreter/context.py
app/forge/ask_cerebus/interpreter/entities.py
app/forge/ask_cerebus/interpreter/plan.py
app/forge/ask_cerebus/interpreter/intent.py
app/forge/ask_cerebus/interpreter/depth.py
app/forge/ask_cerebus/interpreter/temporal.py
app/forge/ask_cerebus/interpreter/actionability.py
app/forge/ask_cerebus/interpreter/numerical.py
app/forge/ask_cerebus/interpreter/generations.py
app/forge/ask_cerebus/interpreter/interpret.py
```

No LLM, network, retrieval, snapshot, persistence, route or migration code.

## 3. Requirement mapping

R1–R53 are implemented and covered exactly as bound by `ACCEPTANCE.md`:
12 intents, 8 entity/collision requirements, 4 depth, 6 temporal, 3
actionability, 3 numerical, 4 generation, 7 ambiguity, 6 typed-plan.

## 4. Test results

| Suite | Command | Result |
|---|---|---|
| IV.1 | `pytest tests/test_forge_ask_cerebus_interpreter.py -q` | **60 passed** |
| III.1 provider compatibility | `pytest tests/test_forge_market_data_provider_compatibility.py -q` | **49 passed** |
| WP-3B offline provider | `pytest tests/test_forge_market_data_provider_integration.py -q` | **66 passed** |
| Book III integration | `pytest tests/test_forge_book_iii_integration.py -q` | **96 passed** |
| Full repository | `pytest -q -p no:cacheprovider` | **2138 passed, 29 skipped** |

No test was renamed, skipped, xfailed or weakened. The 29 skips are the
pre-existing environment-dependent skips.

## 5. Fixture reproduction

`fixtures/generate.py` produced 12 plans (Q-01–Q-12), an expected JSON file
per fixture, `FIXTURE_MANIFEST.json` with SHA-256 per file, and
`PROVENANCE.md`. Test A-59 reloads every expected file and asserts:

- byte-hash equals the manifest entry;
- recomputed `plan.payload()` equals the stored plan;
- stored `plan_id` equals the recomputed one.

Regeneration uses no clock, network, randomness or provider state.

## 6. Canonical identity and collisions

- Instruments resolve to `EURUSD`, `XAUUSD`, `BTCUSD`, `USDJPY`, `AUDJPY`,
  `EURJPY`.
- `BTC Game` resolves to `BTC.GAME` (research artifact generation) and never
  to `BTC.TRACKER`; a comparison retains both distinct ids.
- `P90` retains `P90.ORIGINAL`/`P90.vN`; no promotion to current.
- `ST` retains `ST.MANUAL`; automation wording records
  `automation_not_approved`, never automation authority.
- Fib/R15 records `fib_production_gated` as a material ambiguity.
- Alias resolution is exact; `rekeyish` does not resolve to `TERM.REKEY`.

## 7. Depth and authorization

`requested_depth` is user intent; `effective_depth` is clamped by the
injected `max_authorized_depth`. A `DEPTH_CAPPED` ambiguity is recorded.
The plan contains no entitlement field and no way to raise the ceiling.
A researcher question under a beginner ceiling yields effective `BEGINNER`.

## 8. Temporal routing

`CURRENT` always sets `requires_live_intelligence = true`, including while
the provider is `NOT_CONFIGURED`. `AS_OF` pins lineage; historical and
explicit-version requests set lineage and never become current. No
historical corpus fact is used to satisfy a current request.

## 9. Actionability and evidence

Entry/stop/target/position language sets `actionable` and
`requires_setup_context`, except inside a statistic question (so “132%
target win rate” is evidence-classified, not actionable). Statistical
requests set `requires_evidence`; an unsupported percentage stat produces
`UNSUPPORTED_STATISTIC`. No numeric result is emitted.

## 10. Historical generations

P90/P90P, ST, Base80, Markov, Fib and Wednesday/Afternoon markers retain
their generation. Unknown retained versions (for example P90 v7) produce
`UNAVAILABLE_GENERATION`; no silent newest-version fallback.

## 11. Determinism

`plan_id` is SHA-256 over the canonical JSON payload (excluding the id),
truncated to 32 hex characters with the `PLAN.` prefix. Serialization uses
sorted keys, compact separators, no floats and no serve-time timestamps.
Two identical calls produce identical JSON and ids; all 12 fixtures
reproduce.

## 12. Remaining F3/F4 gaps (unchanged)

- **F3:** historical replay, no-substitution enforcement, deterministic
  measurement join, ST/Base80 and old Markov/Fib evidence, unavailable
  generation retention → IV.2/III.6/Book VII.
- **F4:** BTC Game canonical promotion, Book VI entitlement projection, P90
  current-performance provenance, cross-generation promotion authority.
- Live current data remains unavailable under `NOT_CONFIGURED`.

## 13. Frozen upstream hashes (EOL-normalised SHA-256)

| File | SHA-256 |
|---|---|
| `app/forge/canonical.py` | `fa984b4505113593232474c236d031870724bee185d7829cab4a7e2beff450d4` |
| `app/forge/retrieval/aliases.py` | `7452590ccca32bb80e43c913ab14a5992fd976f2a7310d81d2fb54d116249614` |
| `app/forge/model_runtime/contract.py` | `d0dc91f79e8183638d5eef606541c290b29d2cbdc759aef35341d1004c3f9056` |
| `app/forge/intelligence_api/contracts.py` | `7d8f90adf8aeca993b94d473f61fe16ea13170a1cd977cb47fb186d64697d4f0` |
| `app/forge/intelligence_api/requests.py` | `b2e484023dc55d1fafd90136a6654f07ba713ddfd8ca7d8da2b0ca4499237146` |
| `app/forge/service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

Test A-60 enforces these pins and rejects network/LLM imports in the new
package.

## 14. Defects found and root-cause repairs

| Finding | Root cause | Repair |
|---|---|---|
| Alias `Rekey` did not resolve | shared phrase matcher was case-sensitive | case-insensitive bounded matching in `entities.py` |
| `132% target win rate` was marked actionable | `target` action cue fired before intent context | statistic intent excluded from actionability in `interpret.py` |
| Model description wrongly required lineage | any generation tag counted as lineage | only historical generation tags set `requires_lineage` |
| Lowercase `MOD.*` unknown id was not detected | uppercase-only regex | case-insensitive detection with canonical upper output |
| Lowercase `SET.*` id was not retained | uppercase-only regex | case-insensitive detection with canonical upper output |

No defect was repaired by weakening a test or changing an upstream file.

## 15. Full regression

`2138 passed, 29 skipped` at the implementation head, including all
pre-existing Book I/II/III suites, audit/ledger, persistence, retrieval,
QA and service compositions.

## 16. CI evidence

See `CI_RECEIPT.md` for the final-head run, both jobs.
