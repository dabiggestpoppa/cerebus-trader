# BOOK III — III.1 PROVIDER COMPATIBILITY AMENDMENT — PLAN

**Packet:** BA-25 Rung 1 · **Status:** PROPOSED — planning only
**Branch:** `forge` · **Starting head:** `46dc2fb52cd1e7430c3de185a1ec5070ec0a3f4e`
**Scope:** III.1 provider-normalization compatibility only
**Authority:** amendment design. **No frozen file is modified by this rung.**

> A frozen contract may be extended only through explicit governance, preserved
> history, compatibility evidence and renewed ratification. A green offline
> adapter does not establish live-feed readiness.

---

## 1. Phase 0 — verified state

| # | Check | Result |
|---|---|---|
| 1 | `forge` HEAD == `origin/forge` | PASS — `46dc2fb` |
| 2 | Append-only ancestry from `c104945` | PASS |
| 3 | Book I corpus freeze manifest | PASS — `BOOK_I_FREEZE_MANIFEST_V1.md` |
| 4 | Book II 50 hashes + 23 pins | PASS — ≥50 64-hex entries |
| 5 | 79 Book III modules | PASS — 11/12/13/13/16/14 |
| 6 | WP-3B adapter package | PASS — 18 files present |
| 7 | WP-3B contract tests | PASS — 66/66 |
| 8 | Migrations `001`–`004` | PASS |
| 9 | Frozen router | PASS — sha256 `145757e0…d190af` |
| 10 | Market-data readiness | PASS — `NOT_CONFIGURED`, `required: false` |
| 11 | WP-3B ratification | PASS — PARTIAL recorded |
| 12 | Final-head CI | PASS — run `42321638642` (`test` + `postgres`) |
| 13 | Working tree / `.bu_tmp/` | PASS — only `?? .bu_tmp/` |

Local re-verification at `46dc2fb`: fixtures reproduce byte-identically
(14 files), focused `66 passed`, full regression `2029 passed, 29 skipped`,
default registry `3` instruments, ingest registry `6`, seam unchanged.

---

## 2. Reproduced incompatibility matrix

The WP-3B evidence is confirmed against the actual code, not the summary.
`app/forge/market_data/normalize.py` (sha256 `04c4ecfc…`) declares
`TimestampStyle` at line 60, `ProviderFieldMap` at line 66,
`PROVIDER_SCHEMAS` at line 103, `provider_schema` at line 137,
`normalize_record` at line 190 and `normalize_feed` at line 319.

| Dimension | Twelve Data | Polygon Currencies | Kraken | Owner of the gap |
|---|---|---|---|---|
| Close-time column | absent | absent | absent | **kernel** (`ProviderFieldMap.close_time` is a literal required key) |
| Clock id per row | absent | absent | absent | **kernel** (line 219: `str(payload[schema.clock])` then `supports_clock`) |
| Response envelope | `{"values": [...]}` | `{"results": [...]}` | `{"result": {"XXBTZUSD": [...]}}` | adapter (flatten before kernel) |
| Row shape | mapping | mapping | positional array | adapter (array → mapping) |
| Timestamp unit | ISO-8601 with offset | epoch **milliseconds** | epoch seconds | kernel for ms (only `EPOCH_SECONDS` / `ISO_OFFSET` exist) |
| Symbol / timeframe | in row | request context only | request context only | adapter injects; kernel maps fields |
| Finality signal | none | none | trailing candle provisional | adapter hint + existing cutoff rule |

Confirmed: the **envelopes and row shapes do not require a kernel change** once
the adapter flattens them; the **missing close time, missing clock and
millisecond unit do**, because `normalize_record` reads them unconditionally
from `schema.required_keys`.

Existing behavior that must not change: the two scripted fake schemas
(`fake_alpha`, `fake_beta`), the refusal vocabulary, the eight quality flags,
cutoff-derived finality, and unknown-provider fail-closed.

---

## 3. Ownership law

| Layer | Owns | Must not own |
|---|---|---|
| Provider adapter (`market_data_ingest`) | transport, envelope extraction, row mapping, request-context injection, revision id, finality **hint**, adapter version | canonical finality, sessions, research day, quality outcome |
| III.1 kernel (`market_data`) | instrument identity, timestamp interpretation policy, bar contract, precision, finality, reconcile, gaps, quality vocabulary | vendor envelopes, vendor row shapes, vendor credentials |
| Operator | vendor ratification, licence terms, JPY convention authority, registry promotion | code-level refusals or silent remaps |

Deriving `close_time = open + timeframe` is an **interval boundary**, not a
finality decision. The cutoff rule in `assess_finality`/`finalize_for_cutoff`
remains the only finalizer.

---

## 4. Minimal amendment architecture

### 4.1 Kernel types (one file: `normalize.py`)

```python
class CloseTimeRule(str, Enum):
    SOURCE = "SOURCE"
    OPEN_PLUS_TIMEFRAME = "OPEN_PLUS_TIMEFRAME"
```

`ProviderFieldMap` gains, **at the end, with defaults**:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `close_time` | `str \| None` | (required position preserved) | literal key, or `None` when derived |
| `clock` | `str \| None` | `None` | literal key, or `None` when the provider has no clock claim |
| `close_time_rule` | `CloseTimeRule` | `CloseTimeRule.SOURCE` | explicit derivation declaration |

`required_keys` becomes conditional but stays **order-identical** for the two
fakes: `symbol, timeframe, open_time, close_time, open_price, high, low,
close_price, source_timestamp, clock`; `close_time` is omitted only when
`close_time_rule is OPEN_PLUS_TIMEFRAME`; `clock` is omitted only when it is
`None`.

`TimestampStyle` gains `EPOCH_MILLISECONDS`. Parsing is explicit:
integer-like values only; `value / 1000` at UTC; anything else refuses rather
than truncating.

`PROVIDER_SCHEMA_REGISTRY_VERSION = "PROVIDER_SCHEMAS_V2"` is added and
exported. `Bar` shape and `MARKET_DATA_SCHEMA_VERSION` do **not** change, so no
downstream schema migration is implied.

### 4.2 Schema entries (same file)

All three entries set `clock=None`, derive close time, and use the adapter to
inject `symbol`/`timeframe` after flattening.

| Provider | symbol | timeframe | open/source | prices | volume | style |
|---|---|---|---|---|---|---|
| `twelvedata` | `symbol` | `interval` | `datetime` | `open/high/low/close` | `volume` | `ISO_OFFSET` |
| `polygon` | `symbol` | `timeframe` | `t` | `o/h/l/c` | `v` | `EPOCH_MILLISECONDS` |
| `kraken` | `symbol` | `timeframe` | `t` | `o/h/l/c` | `v` | `EPOCH_SECONDS` |

`PROVIDER_SCHEMAS` remains a module-level constant; both fake entries are
unchanged, and unknown providers still raise `UnsupportedProviderError`.

### 4.3 `normalize_record` changes

1. Missing-key check uses the conditional `required_keys`.
2. Clock: if `schema.clock is None`, skip the key and the `supports_clock`
   check; the bar carries no clock claim. Otherwise current behavior.
3. Close: `SOURCE` parses the field; `OPEN_PLUS_TIMEFRAME` computes
   `open_time + timedelta(minutes=TIMEFRAME_MINUTES[timeframe])`.
4. Everything after the close time — OHLC validation, precision, volume,
   finality, `Bar` construction — is untouched.

### 4.4 Export surface

`app/forge/market_data/__init__.py` (sha256 `7d57349b…`) adds `CloseTimeRule`
and `PROVIDER_SCHEMA_REGISTRY_VERSION` to imports and `__all__`. This is the
second and only other frozen file affected.

---

## 5. Adapter-side obligations (no kernel change)

- Flatten `values`, `results` and `result[key]` envelopes into row mappings.
- Map Kraken positional arrays to named keys.
- Inject request `symbol` and `timeframe` into each row.
- Keep the vendor revision id on the raw observation; canonical lineage is
  still carried by later `source_timestamp` + `REVISED`.
- Mark the Kraken trailing candle `NONFINAL` as a hint only.
- Preserve adapter version and source reference at the raw boundary.

These are F2. They must not be pushed into `normalize.py` merely for
convenience.

---

## 6. Instrument registry decision

**Recommendation: do not modify `instruments.py` (sha256 `8c6d6ad0…`).**

- The additive `build_ingest_registry()` already composes six instruments with
  provider mappings through public constructors and is injected at the
  composition boundary.
- The production default registry stays at three instruments. Promoting JPY
  into it is an operator decision (F4/R21), not a prerequisite for provider
  normalization.
- JPY precision `3`, pip `0.01`, tick `0.001` remain provisional conventions
  (F4/R22) until an authoritative source or operator decision records them.

---

## 7. Backward-compatibility analysis

| Surface | Impact |
|---|---|
| `fake_alpha` / `fake_beta` behavior | none — same keys, same order, same parsing |
| `required_keys` tuple for fakes | identical content and order |
| `normalize_record` callers | unchanged signature; existing records behave identically |
| `normalize_feed`, `replay_historical`, `stream_live` | unchanged signatures and semantics |
| `RefusalReason` / `QualityFlag` | unchanged; no new members |
| `Bar` / `MARKET_DATA_SCHEMA_VERSION` | unchanged |
| Unknown providers | still fail closed |
| Existing tests (`test_forge_market_data.py`, 60 names) | must remain byte-identical in outcome |
| WP-3B suite (66 names) | must remain green unchanged |

New enum members are additive. `ProviderFieldMap` gains defaulted fields at the
end; all repository constructions use keywords, so positional compatibility is
not relied upon.

---

## 8. Hash and freeze impact (planning inventory)

| Artifact | Current sha256 | Expected after amendment |
|---|---|---|
| `app/forge/market_data/normalize.py` | `04c4ecfc…d026b` | changes |
| `app/forge/market_data/__init__.py` | `7d57349b…11fd0` | changes (exports only) |
| `app/forge/market_data/instruments.py` | `8c6d6ad0…7ed94d` | **unchanged** |
| `app/forge/market_data/bars.py` | `97fc99e4…366366` | **unchanged** |
| `app/forge/market_data/quality.py` | `6b77c6df…b58687` | **unchanged** |
| `app/forge/service/routes.py` | `145757e0…d190af` | **unchanged** |
| Package digest `market_data` | `28d14ae61de9d189` (16-hex, WP-3A §2) | changes; new value recorded after implementation |

There is no per-file III.1 freeze manifest; the nearest recorded baseline is
the package digest in `provider_integration/PLAN.md` §2 plus git blobs
(`b547b00d…` for `normalize.py`, `bb4f9a93…` for `__init__.py`). The
implementation rung must create a versioned record that preserves the old
digest; it must not overwrite WP-3A/WP-3B evidence.

---

## 9. Acceptance program (49 tests, offline)

Proposed file: `tests/test_forge_market_data_provider_compatibility.py`.
Full names and expected results are binding in `ACCEPTANCE.md` §3; the coverage
matrix is §5 there.

| Family | Tests | Focus |
|---|---|---|
| T1 backward compatibility | 6 | fake schemas, unknown provider, suite guards |
| T2 timestamps | 6 | seconds, milliseconds, ISO, naive, unit refusal |
| T3 derived close | 5 | M5/H1, source-wins, finality separation, DST instant |
| T4 schemas | 6 | three providers, unknown provider, immutability, rollup refusal |
| T5 envelopes | 5 | three envelopes, provenance, malformed |
| T6 lineage | 5 | provider, revision, timestamps, symbol, adapter version |
| T7 finality | 4 | trailing, hint vs cutoff, post-cutoff final, no authority |
| T8 JPY | 4 | injection, aliases, provisional conventions, default unchanged |
| T9 refusals | 4 | clock, timeframe, timestamp, absent field |
| T10 frozen integrity | 4 | Book I/II, authorized files, hash record, re-ratification |

No test requires a network, credential or vendor account.

---

## 10. Feasibility summary

24 requirements, classified F1–F4 in `FEASIBILITY_GATE.md`:

| Class | Count | Meaning |
|---|---|---|
| F1 | 7 | existing interface already supports it |
| F2 | 8 | additive adapter implementation sufficient |
| F3 | 5 | frozen III.1 modification genuinely required |
| F4 | 4 | canonical source or operator decision blocks it |

---

## 11. Dependency and release gates

1. Amendment design approval (this packet).
2. Separate written authorization for the frozen-surface change.
3. Implementation + 49 compatibility tests.
4. Recomputed hashes and package digest.
5. New versioned freeze record (old baseline preserved).
6. Full III.1 regression (`test_forge_market_data.py`).
7. Full WP-3B regression (66).
8. Full Book III integration regression (96).
9. New amendment evidence + ratification.
10. WP-3B PASS reconsideration.
11. WP-3C external-provider prerequisites (operator + credentials + captures).

No step may be skipped or reordered; step 2 is a hard gate.

---

## 12. Risks and refusal triggers

- **Silent semantic drift** — mitigated by keeping derived close explicitly
  separate from finality and by byte-identical fake-schema tests.
- **Timestamp unit confusion** — mitigated by refusing integer values whose
  magnitude cannot be the declared unit (R19/A-09).
- **Clock invention** — mitigated by `clock=None` rather than injecting a
  platform clock into the provider record.
- **Scope creep into rollup** — refused; no canonical rule exists.
- **Evidence overwrite** — refused; new record is versioned and additive.

Stop and report if: a fake schema changes behavior; a refusal is weakened; the
default registry is promoted without authority; or the amendment grows beyond
the two files named here.

---

## 13. Non-goals

No live network, credentials, vendor account, licence acceptance, readiness
change, rollup implementation, JPYY canonical promotion, WP-3C test execution,
or production registry change in this rung or its immediate implementation.

---

## 14. Deliverables of this rung

`amendment/PLAN.md`, `amendment/ACCEPTANCE.md`,
`amendment/FEASIBILITY_GATE.md`, `amendment/CHANGE_CONTROL.md`. Per
`RATIFICATION_WP3B.md` §4, implementation waits on operator decisions 1–2.
