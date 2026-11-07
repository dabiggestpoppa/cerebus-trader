# III.1 PROVIDER COMPATIBILITY — VERSIONED FREEZE DELTA V2

**Rung:** BA-25 Rung 2 · **Status:** IMPLEMENTED
**Authority:** explicit operator authorization of G1/G2, limited to C1–C5 of
`CHANGE_CONTROL.md`.
**Starting head:** `f47741fc76c232f0f28487f6ffe9f6c95e411f8e`
**Implementation commit:** `937de27401ac13ef0e42cd42e53d2eaa03044182`

This record is additive. The original III.1 ratification, the WP-3A package
digests in `provider_integration/PLAN.md` §2 and all WP-3B evidence remain
untouched.

---

## 1. Authorized surface

| Change | File | Class |
|---|---|---|
| C1 derived close + conditional required keys | `app/forge/market_data/normalize.py` | frozen contract amendment |
| C2 optional clock without remap | `app/forge/market_data/normalize.py` | frozen contract amendment |
| C3 `EPOCH_MILLISECONDS` | `app/forge/market_data/normalize.py` | frozen contract amendment |
| C4 three provider schemas + registry version | `app/forge/market_data/normalize.py` | frozen contract amendment |
| C5 new exports | `app/forge/market_data/__init__.py` | frozen surface (additive) |

No other source file changed. `Bar`, `Instrument`, quality vocabulary, session
rules, finality, parity, routes, migrations and the production default registry
are untouched.

---

## 2. SHA-256 delta

| File | Before | After |
|---|---|---|
| `app/forge/market_data/normalize.py` | `04c4ecfc97e111e281d90158df5ee7b6cff1aeb25e4df6eaf81f93a66e9d026b` | `9b7ea855a3a90994ae325c44af40898e842a6fbef838a6dc5490b5a505919c24` |
| `app/forge/market_data/__init__.py` | `7d57349bba68c6a090ab2f7739e9bd095e436ba01bf110da1ed1c1aa22611fd0` | `94c88cd73abd03053ac2ba0b90ee95f7d204929e4206ffce04606fb111015f0f` |

Unchanged, re-verified at the implementation head:

| File | SHA-256 |
|---|---|
| `instruments.py` | `8c6d6ad05db973122265bca76ea6b3c0c3e248974fa26cb6409ef4cce67ed94d` |
| `bars.py` | `97fc99e44c7abab0545a33e2b0fbf0b3d354ae5bae2b4c6e446ff3b336666366` |
| `quality.py` | `6b77c6dfa11e6b22013b7f128e0d6b8095b5e035b660c93c309df220bcb58687` |
| `service/routes.py` | `145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af` |

Git blobs before: `normalize.py b547b00d…`, `__init__.py bb4f9a93…`.

---

## 3. Aggregate digests

- **Original recorded package digest:** `market_data 28d14ae61de9d189`
  (WP-3A §2, 16 hex). WP-3A does not document its aggregation method, so this
  value is preserved as recorded and is **not** recomputable here.
- **Amended aggregate:** `6c8d903ff80887f9169824cc52613fc02a5790e5216e001db6d49be1230f2e80`
  using the Book III.6 frozen-baseline method: SHA-256 over the sorted
  `*.py` files of the package, feeding `filename + "\n" + bytes` for each.
  The same method reproduces the recorded aggregates of the four untouched
  packages, which is the method's control.

The two values are therefore not numerically comparable; both are recorded so
neither contract generation is ambiguous.

---

## 4. Schema registry version

`PROVIDER_SCHEMAS_V2` is exposed as
`PROVIDER_SCHEMA_REGISTRY_VERSION`. `MARKET_DATA_SCHEMA_VERSION` remains
`MARKET_DATA_SCHEMA_V1` because the `Bar` contract did not change.

`PROVIDER_SCHEMAS` is an immutable `MappingProxyType`. Registered providers:
`fake_alpha`, `fake_beta` (byte-identical behavior), `twelvedata`, `polygon`,
`kraken`. Fake `required_keys` tuples are unchanged in content and order.

---

## 5. Backward-compatibility evidence

| Check | Result |
|---|---|
| `fake_alpha` / `fake_beta` required-key order | unchanged (asserted in A-01/A-02) |
| Refusals / status vocabulary | unchanged; no new `RefusalReason` or `QualityFlag` |
| III.1 focused suite | 65 passed, no test edited |
| WP-3B contract suite | 66 passed, no test edited |
| Book III integration | 96 passed |
| Amendment suite | 49/49 |
| Full repository | 2078 passed, 29 skipped |
| Default registry | still EURUSD, XAUUSD, BTCUSD |
| Seam | `market_data: NOT_CONFIGURED`, `required: false` |

Cross-bloc whole-file hash pins were re-recorded (not weakened) because they
store SHA-256 of the two authorized files rather than interface identity:

| Record | Old | New |
|---|---|---|
| `bloc_iii_2/PLAN.md` hash list | `normalize.py 04c4ecfc…d026b`, `__init__.py 7d57349b…11fd0` | `9b7ea855…19c24`, `94c88cd7…15f0f` |
| `bloc_iii_3/PLAN.md` hash list | same two old values | same two new values |
| `bloc_iii_5/fixtures/FROZEN_BASELINE.json` | old file hashes | new file hashes |
| `bloc_iii_6/fixtures/FROZEN_BASELINE.json` | `market_data c78084bf…` | `6c8d903f…` |

Old values remain in git history and in §2/§3 above.

---

## 6. Affected callers

`normalize_record`, `normalize_feed`, `provider_schema`, `replay_historical`,
`stream_live` and package importers. No signature changed; new names are
additive. Behavior changes only for the three new provider ids and for schemas
that explicitly set `OPEN_PLUS_TIMEFRAME` or `clock=None`.

---

## 7. Rollback

1. Revert the implementation commit `937de27` (single commit, no data
   migration, no persisted state).
2. Revert the cross-bloc hash re-records to the values in §2/§5.
3. Restore `market_data` aggregate `28d14ae61de9d189`.
4. Re-run the 65 III.1 and 66 WP-3B suites; the 49 amendment tests are removed
   with the amendment.

Rollback returns the tree to `f47741f` behavior.

---

## 8. Required evidence

Amendment `EVIDENCE.md`, `RATIFICATION.md`, WP-3B
`RATIFICATION_WP3B_SUPPLEMENT_V2.md`, and both CI jobs (`test`, `postgres`)
green at the final pushed head.
