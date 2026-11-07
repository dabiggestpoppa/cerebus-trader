# WP-3B — SUPPLEMENTAL RATIFICATION V2

**Supersedes:** the PARTIAL verdict in `RATIFICATION_WP3B.md` (original left
intact) · **Basis:** BA-25 Rung 2 amendment PASS at `937de27`

---

## 1. Verdict

**WP-3B: PASS** for the offline provider-adapter contract.

The earlier PARTIAL verdict existed because real provider ids could not be
registered without a frozen amendment. That blocker is removed by the
authorized C1–C5 change and is replaced by a recorded hash delta.

This verdict is limited to offline adapters and canonical normalization. It
does **not** assert a licensed feed, external parity, latency, cost or
production readiness.

---

## 2. Closure conditions

| Condition | Evidence |
|---|---|
| Amendment PASS | 49/49 amendment, 65/65 III.1, 66/66 WP-3B, 96/96 integration, full 2078 passed |
| Fresh evidence referencing the new digest | `amendment/EVIDENCE.md`, `amendment/FREEZE_DELTA_V2.md` (`9b7ea855…`, `94c88cd7…`, aggregate `6c8d903f…`, `PROVIDER_SCHEMAS_V2`) |
| `normalize_feed` / `replay_historical` / `stream_live` accept the three provider ids offline | recorded in `EVIDENCE.md` §3; replay/stream parity `overall = true` for each provider |
| No external test claimed | six WP-3C names remain **NOT EXECUTED** |

---

## 3. What changed for the adapter

`market_data_ingest.canonical` may now delegate to the canonical kernel for
real providers; the existing adapter module still owns envelopes, array rows,
request-context injection and revision/finality hints. The kernel owns close
derivation, timestamp units and canonical refusals.

No adapter file was modified in this rung.

---

## 4. Remaining WP-3C restrictions

- No vendor call, credential or licensed capture was used.
- R21 default-registry promotion, R22 JPY convention authority, R23 rollup and
  R24 licensing remain open operator decisions.
- The six external tests require separate written authorization and a governed
  environment; they are **NOT EXECUTED**.
- The `market_data` readiness seam remains `NOT_CONFIGURED` with
  `required: false`.
