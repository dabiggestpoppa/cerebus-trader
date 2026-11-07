# III.1 PROVIDER COMPATIBILITY AMENDMENT — EVIDENCE

**Rung:** BA-25 Rung 2 · offline, deterministic, credential-free
**Starting head:** `f47741f` · **Implementation:** `937de27`
**Scope:** C1–C5 only (`normalize.py`, `market_data/__init__.py`)

---

## 1. Test results (actual)

| Suite | Result |
|---|---|
| Amendment A-01–A-49 | **49 passed**, 0 skipped, 0 xfailed |
| III.1 focused (`test_forge_market_data.py`) | **65 passed** (no edits) |
| WP-3B offline provider (`test_forge_market_data_provider_integration.py`) | **66 passed** (no edits) |
| Book III integration (`test_forge_book_iii_integration.py`) | **96 passed** |
| Full repository | **2078 passed, 29 skipped** |

Command: `python -m pytest -q -p no:cacheprovider`.

---

## 2. Provider records accepted

| Provider | Envelope | Timestamp | Close | Clock |
|---|---|---|---|---|
| Twelve Data | `values` flattened by adapter | ISO offset | derived open + timeframe | absent — no claim |
| Polygon | `results` flattened by adapter | epoch ms | derived | absent — no claim |
| Kraken | array rows mapped by adapter | epoch s | derived | absent — no claim |

All three produce canonical bars with `provider` set, source timestamp equal to
the provider event time, and finality decided only by the observation cutoff.

---

## 3. Adapter-boundary proof (offline)

`normalize_feed`, `replay_historical` and `stream_live` accept the three real
provider ids through the canonical kernel with the injectable ingest registry:

```text
twelvedata: replay=1 stream=1 parity=OK close=2026-03-03T00:05:00+00:00
polygon:    replay=1 stream=1 parity=OK close=2026-03-03T00:05:00+00:00
kraken:     replay=1 stream=1 parity=OK close=2026-03-03T00:05:00+00:00
```

Parity was asserted with `compare_parity(...).overall`, not by comparing
`PipelineResult.digest()` (that digest intentionally includes the pipeline path
label, so replay and streaming digests are never equal).

---

## 4. Fixture reproduction

Twelve WP-3B fixtures were re-hashed against
`provider_integration/fixtures/FIXTURE_MANIFEST.json`:

```text
fixtures checked=12 mismatches=[]
```

No fixture was regenerated or edited.

---

## 5. Frozen integrity

- `git diff f47741f -- implementation/forge/book_i implementation/forge/book_ii app/forge/service/routes.py` → empty.
- Book II manifest still carries ≥50 pin hashes.
- Migrations remain `001`–`004`.
- 79 Book III modules across the six packages; counts unchanged.
- `market_data` package still has 11 modules.
- `instruments.py`, `bars.py`, `quality.py`, `routes.py` hashes unchanged.
- Seam `market_data: NOT_CONFIGURED`, `required: false`; readiness still `ready`.
- No credential, network call, vendor SDK or account was used.

---

## 6. Repairs made during implementation

1. **Forbidden numeric constant.** The first implementation introduced a
   module-level millisecond threshold. The frozen III.1 test
   `test_no_global_unit_constant` correctly rejected it; the threshold is now
   inline (`10**12`) and no module-level numeric constant exists.
2. **Cross-bloc hash pins.** Three suites compare whole-file SHA-256 for
   upstream packages. The authorized amendment changes two of those files, so
   the stored baselines were re-recorded to the new hashes — assertions were
   not relaxed. Old values are preserved in `FREEZE_DELTA_V2.md` §2/§5 and in
   git history. Records touched: `bloc_iii_2/PLAN.md`,
   `bloc_iii_3/PLAN.md`, `bloc_iii_5/fixtures/FROZEN_BASELINE.json`,
   `bloc_iii_6/fixtures/FROZEN_BASELINE.json`.
3. **Harness correction.** An initial adapter-parity check compared
   `PipelineResult.digest()` across paths; the amendment code was correct and
   the check was replaced with `compare_parity`.
4. **Shallow-checkout integrity checks.** Two frozen-integrity tests used
   `git diff <base-commit>`, which exits 128 on CI's shallow checkout. They now
   require a clean worktree against `HEAD` and pin all 11 `market_data` files:
   the two authorized files to their new hashes, the other nine to the recorded
   III.1 baseline. Coverage is unchanged; portability is fixed.

No prior acceptance test was weakened, skipped or deleted.

---

## 7. Hash record

| File | Old | New |
|---|---|---|
| `normalize.py` | `04c4ecfc…d026b` | `9b7ea855…19c24` |
| `market_data/__init__.py` | `7d57349b…11fd0` | `94c88cd7…15f0f` |

Package aggregate: recorded WP-3A `28d14ae61de9d189`; amended
`6c8d903ff80887f9` (Book III.6 method). `PROVIDER_SCHEMAS_V2`.

---

## 8. CI receipt

Run `42383847897` at head `ea5bf0aa`: `test` success, `postgres` success. The
final ladder commit records this receipt and is documentation-only; its own run
was checked green before the final report.

---

## 9. Limitations

- No live provider was contacted; no latency, depth, cost or licensing claim is
  made.
- The six WP-3C external tests are **NOT EXECUTED**.
- Vendor licence terms / redistribution (R24) are not granted by this evidence.
- JPY precision/pip/tick remain provisional (R22); the production default
  registry is not promoted (R21); higher-timeframe rollup is still refused
  (R23).

A green offline amendment is not a licensed live-data feed.
