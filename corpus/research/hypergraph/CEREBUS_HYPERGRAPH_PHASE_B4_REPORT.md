# CEREBUS Hypergraph Phase B4 — Hierarchical Propagation Gate OOS

## Objective
Test whether the higher-timeframe propagation state discovered in B3 improves chronological out-of-sample prediction of same-day deep-extension repair after a 200% hit.

Decision checkpoint:
- 30 minutes after the first 200% hit.
- Any target already reached by +30m is excluded for that target.
- Only information observable by +30m is allowed.

Targets:
- 100 reclaim
- 50 reclaim
- 0 reclaim

Models:
1. B1_BASE
   - weekday
   - side
   - hit time
   - news state
   - Asian-range scale
   - 200 rejection within 30m
   - 185/168/132 reclaim status by +30m

2. B3_GATE
   - all B1_BASE features
   - prior-day 80% break
   - propagation alignment between the 80-break direction and the 200% extension

3. HYPERGRAPH_GATE
   - all B3_GATE features
   - explicit higher-order interactions:
     rejection × 168 reclaim,
     propagation gate × rejection,
     propagation gate × 168 reclaim,
     propagation gate × rejection × 168 reclaim

Validation:
- expanding chronological OOS
- test years 2024, 2025, 2026
- no random split
- 2026 news state marked UNKNOWN rather than silently treated as no-news

## Main finding
The hierarchical propagation gate improves prediction across both assets and across all three repair targets.

### EURUSD pooled chronological OOS
100 reclaim:
- B1 AUC 0.7252
- B3 gate AUC 0.7600
- Hypergraph gate AUC 0.7681
- Brier 0.2059 -> 0.1911
- Log loss 0.5989 -> 0.5577

50 reclaim:
- B1 AUC 0.7612
- B3 gate AUC 0.7970
- Hypergraph gate AUC 0.8075
- Brier 0.1468 -> 0.1348
- Log loss 0.4443 -> 0.4099

0 reclaim:
- B1 AUC 0.7495
- B3 gate AUC 0.7817
- Hypergraph gate AUC 0.7841
- Brier 0.1241 -> 0.1171
- Log loss 0.3974 -> 0.3777

### XAUUSD pooled chronological OOS
100 reclaim:
- B1 AUC 0.8119
- B3 gate AUC 0.8386
- Hypergraph gate AUC 0.8396
- Brier 0.1481 -> 0.1375
- Accuracy 77.87% -> 80.24%

50 reclaim:
- B1 AUC 0.8564
- B3 gate AUC 0.8801
- Hypergraph gate AUC 0.8777
- Brier 0.1097 -> 0.1009

0 reclaim:
- B1 AUC 0.8003
- B3 gate AUC 0.8243
- Hypergraph gate AUC 0.8260
- Brier 0.0758 -> 0.0695

## State separation
The strongest practical result is not merely model-score improvement. The propagation gate sharply separates two different deep-extension populations.

### EURUSD
Future 100 reclaim after +30m:
- no propagation gate: 42.08%
- propagation gate ON: 16.00%

With reject30:
- no gate: 48.42%
- gate ON: 25.76%

With reject30 + 168 reclaimed by +30m:
- no gate: 54.24%
- gate ON: 31.25%

Future 50 reclaim:
- no gate: 26.14%
- gate ON: 6.72%

Future 0 reclaim:
- no gate: 18.35%
- gate ON: 4.32%

### XAUUSD
Future 100 reclaim:
- no propagation gate: 35.36%
- propagation gate ON: 13.25%

With reject30:
- no gate: 47.73%
- gate ON: 23.53%

With reject30 + 168:
- no gate: 47.92%
- gate ON: 28.00%

Future 50 reclaim:
- no gate: 23.32%
- gate ON: 4.82%

Future 0 reclaim:
- no gate: 15.11%
- gate ON: 2.40%

## Scientific interpretation
B3 was correct: higher-timeframe propagation must gate the intraday reversal engine.

The same intraday evidence has different meaning depending on whether propagation is active.

Without propagation:
200 -> reject -> 168 reclaim
is a genuine mean-reversion candidate.

With propagation:
80-break -> aligned 200 -> reject/168
is much more often only a partial repair inside an ongoing directional regime.

This is a true higher-order conditional interaction.

## Promotion decision
PROMOTE:
- propagation gate as a context feature for the deep-extension reversal engine
- hierarchical architecture:
  higher-TF propagation -> intraday extension -> recovery sequence -> target probabilities

DO NOT PROMOTE YET:
- any direct trade entry rule
- any single fixed probability across regimes
- Gold full-repair probabilities without additional regime control

## Practical state machine candidate
1. PROPAGATION GATE OFF
   200 hit
   -> reject30
   -> 168 reclaim
   -> 132 reclaim
   -> 100 / 50 / 0 repair ladder

2. PROPAGATION GATE ON
   200 hit in same direction as prior-day 80-break
   -> treat rejection/reclaim as partial repair unless stronger evidence appears
   -> suppress 50/0 expectations
   -> preserve continuation bias

## Next test
Phase B5 should move from destination prediction to execution research:
- define first actionable checkpoint after 200
- compare entry candidates at 185 / 168 / 132 reclaim
- stop candidates at re-extension 200 / 220 / event extreme
- targets 100 / 50 / 0
- stratify by propagation gate ON/OFF
- chronological OOS expectancy, PF, drawdown, and time-to-resolution
- only then decide whether this can become a trade-calling layer