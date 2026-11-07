# BOOK III — WP-3B — RATIFICATION

**Packet:** BA-24 Rung 2 · **Branch:** `forge`
**Starting head:** `c104945fc8011d0b613ebdca0ac9493eeffcc9d1`
**Heads ratified:** `07f010f`, `023b87b`, `5c21b06`
**Decision:** **PARTIAL**

---

## 1. Decision

**PARTIAL — offline adapter works, but required registrations remain blocked.**

The offline contract is implemented and green: 66/66 WP-3B tests, twelve
synthetic fixtures reproducing byte-identically, frozen interfaces intact, the
readiness seam unchanged. Full ratification is withheld because ACCEPTANCE §2
requires written authorization for provider schema-table entries and the
production default registry, and this rung was explicitly forbidden from
modifying ratified III.1 source. A PASS here would misrepresent an unresolved
prerequisite.

No part of this decision authorizes live data, a vendor account, a licence or
production use.

## 2. What is ratified

| Item | Evidence |
|---|---|
| Offline adapter package (18 modules) | `EVIDENCE_WP3B.md` §4 |
| 66/66 contract tests, exact names | §5 |
| Twelve fixtures + manifest + baseline | §6 |
| Additive JPYY instruments and provider mappings | §3.2 |
| Offline parity, quality and finality behaviour | §7–§8 |
| Secret/network isolation | §9 |
| Frozen integrity (79 modules, routes, migrations, seam) | §10 |
| Six external names held NOT EXECUTED | §11 |

## 3. What is withheld

1. **Provider schema registration** — `normalize.py`'s `PROVIDER_SCHEMAS` is a
   closed two-fake table whose field map cannot express any of the three real
   feeds without structural change (§3.1). Not applied.
2. **Production default registry extension** — intentionally unchanged; the
   production registry still resolves three instruments.
3. **Higher-timeframe rollup** — no canonical rule exists; not implemented.
4. **Live/external acceptance** — six tests remain WP-3C.
5. **Licensing** — vendor display/redistribution rights remain unverified.

## 4. Required operator decisions

| # | Decision | Consequence if refused |
|---|---|---|
| 1 | Ratify Twelve Data as primary, Polygon/Kraken secondary | WP-3C cannot start |
| 2 | Authorize the §3.1 amendment to `normalize.py` (+ default registry) | adapters remain offline-only; no real provider id can be normalized |
| 3 | Confirm JPYY precision 3 / pip 0.01 / tick 0.001 | JPY acceptance stays provisional |
| 4 | Approve licensed `SOURCE_SLICE` captures and credential injection | external tests stay NOT EXECUTED |
| 5 | Decide whether to fund a vendor tier | no live feed; seam stays `NOT_CONFIGURED` |

## 5. Invariants held

- A mock feed is not a live provider; no adapter test is cited as licensed data.
- Provider finality is an observation; only III.1 finalizes.
- Missing bars are never filled; disagreements are never auto-resolved.
- No credential, key or account entered the repository, fixtures or reports.
- The Book II readiness seam was not modified.
- All commits are append-only; no amend, squash, rebase, reset or force-push.

## 6. Gate state

- Book III provider gate: **OPEN** (blocked on amendment + operator ratifications).
- Market data: `market_data: NOT_CONFIGURED` (unchanged).
- WP-3C: not started. WP-3D: not started.

**Stop after WP-3B evidence.**
