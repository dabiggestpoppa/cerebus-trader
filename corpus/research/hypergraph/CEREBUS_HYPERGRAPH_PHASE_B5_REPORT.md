# CEREBUS Hypergraph Phase B5 — Execution / Expectancy Research

## Objective
Convert the B4 prediction layer into a first execution test.

The question is no longer only:
> Will a 200% deep extension repair?

It is:
> If we enter on a reclaim node, where does the trade have positive chronological OOS expectancy?

## Test design
Assets:
- EURUSD
- XAUUSD

Entry candidates after a 200% extension:
- 185 reclaim
- 168 reclaim
- 132 reclaim

Stop candidates:
- 200 re-extension
- 220 re-extension
- observed pre-entry extreme + 0.05 Asian-range buffer

The observed-extreme stop is fully causal: it uses only the deepest extension already seen before the entry.

Targets:
- 100
- 50
- 0

Context split:
- PROPAGATION GATE OFF
- PROPAGATION GATE ON

Evaluation:
- primary OOS window: 2024–2026
- friction included:
  - EURUSD: 0.2 pip round-trip research friction
  - XAUUSD: $0.25 round-trip research friction
- same-bar stop/target collisions resolved conservatively as stop-first
- unresolved trades are closed at 17:00 New York and scored at mark-to-market R

Research promotion filter:
- n >= 20
- net PF >= 1.20
- positive average net R
- max drawdown <= 12R

## Main result
Only one configuration passed the full B5 research gate:

### EURUSD — propagation gate OFF
Entry:
- 132 reclaim after a 200% deep extension

Stop:
- deepest observed pre-entry extension + 0.05 Asian-range buffer

Target:
- 100 reclaim

2024–2026 OOS:
- n = 204
- win rate = 73.04%
- average net expectancy = +0.0377R/trade
- PF = 1.214
- total = +7.70R
- max drawdown = 5.09R
- median nominal RR = 0.315R
- median hold = 25 minutes

This is not a high-RR setup. It is a high-hit-rate repair trade with a small positive edge.

## Year stability — EURUSD gate OFF, 132 -> 100
2022:
- n 14
- avg +0.0157R
- PF 1.088

2023:
- n 87
- avg +0.0031R
- PF 1.016

2024:
- n 89
- avg +0.0300R
- PF 1.165

2025:
- n 63
- avg +0.0394R
- PF 1.223

2026:
- n 52
- avg +0.0490R
- PF 1.294

The edge is small, but its sign remained positive every year in the EUR sample.

## Propagation gate effect
The gate is not merely predictive. It is economically decisive.

Same EURUSD execution:
132 reclaim -> 100
observed-extreme + 0.05R stop

Gate OFF:
- 2024–26 expectancy positive
- PF > 1

Gate ON:
2023:
- avg -0.3956R, PF 0.233

2024:
- avg -0.2093R, PF 0.427

2025:
- avg -0.1714R, PF 0.520

2026:
- avg -0.5339R, PF 0.111

Therefore:
**The same 132 reclaim is a different trade depending on the higher-timeframe propagation hyperedge.**

This validates the B4 architecture in execution space.

## Earlier entries
The 185 and 168 reclaim entries often produced larger nominal R:R and some positive average-R cells on EURUSD gate-OFF, but they failed the full research gate because drawdown and/or PF stability were weaker.

Examples in 2024–26:
- 185 -> 100, observed-extreme stop:
  - avg +0.110R
  - PF 1.17
  - max DD ~24.4R
- 168 -> 100:
  - avg +0.060R
  - PF 1.13
  - max DD ~8.5R

So earlier entries have more convexity but less reliability.

## Gold result
No XAUUSD configuration passed the B5 research promotion filter.

For the equivalent 132 -> 100, observed-extreme stop, gate-OFF setup:
2024:
- ~flat

2025:
- positive

2026:
- materially negative

This confirms the B1–B4 warning:
**Gold's reversal geometry is real, but its execution edge is regime-dependent and not stable enough for a universal live rule.**

## Scientific interpretation
B5 supports a hierarchical execution doctrine:

1. Check higher-timeframe propagation state first.
2. If PROPAGATION GATE ON:
   - suppress deep-extension fade logic.
   - 132 reclaim is often only partial repair.
3. If PROPAGATION GATE OFF:
   - 200 extension
   - recovery through 185/168
   - 132 reclaim
   - 100 becomes a tradable repair objective on EURUSD.
4. 50 and 0 remain lower-probability continuation targets and did not outperform 100 strongly enough under the current execution rules.

## Important nuance
The surviving EUR setup has:
- high win rate
- low nominal R:R
- small positive expectancy

That means execution costs, slippage, and broker spread matter a lot.

It should not be promoted directly to production yet.

## Promotion status
PROMOTE TO NEXT RESEARCH STAGE:
- EURUSD gate-OFF 132 reclaim -> 100 repair branch
- observed-extreme + 0.05R invalidation architecture
- propagation gate as mandatory context

REJECT FOR NOW:
- gate-ON fade trades
- universal XAU deep-extension fade
- blind 185/168 entries
- full 50/0 targeting as default

## Next recommended phase — B6
Robustness and execution stress test:
- realistic spread/slippage grid
- alternative 0.025R / 0.05R / 0.075R extreme buffers
- time-of-day filters
- tier/day/news ablation
- one-trade-per-day enforcement
- Monte Carlo sequence reshuffling
- bootstrap confidence intervals for expectancy and PF
- walk-forward threshold stability

Only if the EUR 132->100 edge survives B6 should it move into a live signal prototype.