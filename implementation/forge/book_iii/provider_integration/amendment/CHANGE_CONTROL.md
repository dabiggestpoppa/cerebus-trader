# BOOK III — III.1 PROVIDER COMPATIBILITY AMENDMENT — CHANGE CONTROL

**Packet:** BA-25 Rung 1 · **Status:** PROPOSED — no change executed
**Starting head:** `46dc2fb52cd1e7430c3de185a1ec5070ec0a3f4e`

This document is the control record a future implementation rung must satisfy.
It is not authorization to edit ratified source.

---

## 1. Change inventory

| Change | Files | Class | Authorized now? |
|---|---|---|---|
| C1 close-time derivation + conditional required keys | `normalize.py` | FROZEN CONTRACT AMENDMENT | No |
| C2 optional clock key | `normalize.py` | FROZEN CONTRACT AMENDMENT | No |
| C3 `EPOCH_MILLISECONDS` | `normalize.py` | FROZEN CONTRACT AMENDMENT | No |
| C4 three schema entries + registry version | `normalize.py` | FROZEN CONTRACT AMENDMENT | No |
| C5 export new names | `market_data/__init__.py` | FROZEN CONTRACT AMENDMENT (surface) | No |
| C6 envelope/row adaptation | `market_data_ingest/` | ADDITIVE ADAPTER CHANGE | No (WP-3C/rung 2) |
| C7 JPY composition | `market_data_ingest/registry.py` | ADDITIVE ADAPTER CHANGE | Already present; no change |
| C8 default registry promotion | `instruments.py` | FROZEN + OPERATOR DECISION | No |
| C9 rollup | kernel | CANONICAL RESEARCH BLOCKER | No |

---

## 2. Per-file control records

### 2.1 `app/forge/market_data/normalize.py`

1. **Path:** `app/forge/market_data/normalize.py` (374 lines).
2. **Current SHA-256:** `04c4ecfc97e111e281d90158df5ee7b6cff1aeb25e4df6eaf81f93a66e9d026b`.
3. **Freeze entry:** package digest `market_data 28d14ae61de9d189` in
   `provider_integration/PLAN.md` §2; git blob `b547b00d…`; no per-file
   manifest exists for III.1.
4. **Required behavior:** represent real vendor records (missing close, missing
   clock, epoch ms) without fabricating source fields.
5. **Why the adapter cannot supply it:** see `FEASIBILITY_GATE.md` §3. The
   adapter would have to invent a close-time field, a clock claim, or rewrite
   the timestamp unit.
6. **Exact proposed change:**
   - add `CloseTimeRule(str, Enum)` with `SOURCE`, `OPEN_PLUS_TIMEFRAME`;
   - add `TimestampStyle.EPOCH_MILLISECONDS`;
   - `ProviderFieldMap`: `close_time: str | None`,
     `clock: str | None = None`,
     `close_time_rule: CloseTimeRule = CloseTimeRule.SOURCE`;
   - conditional `required_keys` preserving the fake-schema order;
   - `_parse_timestamp` ms branch with integer-like validation;
   - `normalize_record`: optional clock check, derived close;
   - `PROVIDER_SCHEMA_REGISTRY_VERSION = "PROVIDER_SCHEMAS_V2"`;
   - three schema entries.
7. **Backward compatibility:** fake schemas and `required_keys` unchanged;
   existing signatures and refusals unchanged; no new flags.
8. **Callers affected:** `normalize_record`, `normalize_feed`,
   `replay_historical`, `stream_live`, `parity`, `market_data/__init__.py`
   exports; no signature change.
9. **Tests:** new 49-name suite; existing 60-name III.1 suite and 66-name WP-3B
   suite must pass unmodified.
10. **Expected hash change:** yes — new digest recorded by the implementation
    evidence; old digest preserved in the versioned record.
11. **Version bump:** `PROVIDER_SCHEMAS_V2`; `MARKET_DATA_SCHEMA_VERSION` is
    **not** bumped because the `Bar` contract does not change.
12. **Rollback:** revert the single implementation commit; restore the prior
    package digest; no data migration, no persisted state.
13. **Re-ratification evidence:** amendment `EVIDENCE.md` + `RATIFICATION.md`,
    hash delta table, full III.1/WP-3B/Book III runs, CI receipt.

### 2.2 `app/forge/market_data/__init__.py`

1. **Path:** `app/forge/market_data/__init__.py`.
2. **Current SHA-256:** `7d57349bba68c6a090ab2f7739e9bd095e436ba01bf110da1ed1c1aa22611fd0`.
3. **Freeze entry:** package digest above; git blob `bb4f9a93…`.
4. **Required behavior:** expose `CloseTimeRule` and
   `PROVIDER_SCHEMA_REGISTRY_VERSION` to importers.
5. **Why the adapter cannot supply it:** the public package surface is frozen;
   an adapter cannot add canonical exports.
6. **Exact proposed change:** two imports and two `__all__` entries.
7. **Backward compatibility:** additive exports only.
8. **Callers affected:** importers gain names; no removals.
9. **Tests:** import/version test (A-04), frozen-integrity tests (A-46–A-48).
10. **Expected hash change:** yes (exports only).
11. **Version bump:** none beyond the schema registry constant.
12. **Rollback:** same revert as C1.
13. **Re-ratification:** same record.

### 2.3 `app/forge/market_data/instruments.py` — **no change**

1. Path: `app/forge/market_data/instruments.py`.
2. Current SHA-256: `8c6d6ad05db973122265bca76ea6b3c0c3e248974fa26cb6409ef4cce67ed94d`.
3. Freeze entry: package digest above.
4. Required behavior: none for this amendment; JPY composition already works.
5. Why modification is unnecessary: `Instrument` and `InstrumentRegistry`
   public constructors plus `build_ingest_registry()` injection cover it.
6. Proposed change: **none**.
7–13. No hash change, no version bump, no rollback, no re-ratification.

### 2.4 `bars.py` / `quality.py` / sessions / clocks / research day — **no change**

Current hashes: `bars.py 97fc99e4…366366`, `quality.py 6b77c6df…b58687`.
`service/routes.py` (`145757e0…d190af`) is Book II-frozen and outside this
amendment. No `Bar` field, flag, refusal reason or finality rule changes. Any
proposal to change them is out of scope and must return to design.

---

## 3. Freeze record update procedure

1. Preserve the WP-3A package digest record unchanged.
2. Create a **new versioned record** (implementation rung) containing:
   old digest, new digest, per-file old/new hashes, authorizing decision id,
   date, commit SHAs.
3. Never edit or delete WP-3A/WP-3B evidence.
4. Update no Book II manifest; `routes.py` remains untouched.
5. If any hash outside C1/C5 changes, stop: the change is out of scope.

---

## 4. Authorization gates

| Gate | Required artifact | May proceed without it? |
|---|---|---|
| G1 design approval | this packet ratified | No |
| G2 frozen-surface authorization | written decision naming C1/C5 | **No** |
| G3 implementation | code + 49 tests | only after G2 |
| G4 hash re-record | versioned freeze record | No |
| G5 re-ratification | amendment evidence/ratification | No |
| G6 WP-3B reconsideration | updated WP-3B verdict | No |
| G7 WP-3C | operator vendor + licence + credentials | No |

Design approval does **not** imply G2.

---

## 5. Re-ratification checklist

- [ ] 49/49 amendment tests green.
- [ ] 60/60 III.1 tests green unmodified.
- [ ] 66/66 WP-3B tests green unmodified.
- [ ] 96/96 Book III integration green.
- [ ] Full repository regression green.
- [ ] Only C1/C5 files changed; all other hashes identical.
- [ ] Old and new package digests recorded.
- [ ] Seam still `market_data: NOT_CONFIGURED`.
- [ ] No credential, network or vendor account used.
- [ ] CI `test` and `postgres` green at the final head.

---

## 6. WP-3B closure criteria

WP-3B may move from PARTIAL to PASS only when:

1. Amendment PASS (all checklist items above).
2. A fresh WP-3B evidence/ratification entry references the new digest and the
   amendment decision id.
3. `normalize_feed`/`replay_historical`/`stream_live` accept the three real
   provider ids under the new schemas (proven offline).
4. No external test is claimed; the six WP-3C names remain NOT EXECUTED.

Until then, `RATIFICATION_WP3B.md` stays authoritative and WP-3B is PARTIAL.

---

## 7. WP-3C dependency handoff

WP-3C still requires, independently of this amendment:

- operator vendor ratification and recorded licence terms (R24);
- credentials injected through the environment, never committed;
- licensed `SOURCE_SLICE` captures with `licence_ref`/`source_ref`;
- the six external tests, run only in a governed environment;
- tolerance decisions for cross-provider parity.

The amendment suite itself stays offline and credential-free.

---

## 8. Commit discipline

Planning rung: four documents only, append-only, fast-forward push, CI verified.
Implementation rung (if authorized): one code commit touching C1/C5, one test
commit, one evidence/hash-record commit. No amend, squash, rebase, reset or
force-push. `.bu_tmp/` preserved.

---

## 9. Stop conditions

Stop and report if: G2 is absent; a fake schema changes; a refusal is weakened;
`Bar`/quality/sessions must change; an unauthorized file changes; the old
digest would be overwritten; or the seam would be flipped.
