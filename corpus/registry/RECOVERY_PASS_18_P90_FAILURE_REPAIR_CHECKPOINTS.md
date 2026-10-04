# FORGE RECOVERY PASS 18 — P90 ENGINE, FAILURE/REPAIR, P90P CHECKPOINTS

Date: 2026-10-04
Source tree: dabiggestpoppa/larger-lab / quant-lab

## 1. Exact P90 detector recovered
Historical P90 definition:
M5 candle must:
1. close during 02:00-11:00 EST;
2. meet time-window body threshold;
3. close outside Asian band.

Thresholds:
- 02-04 >=4.1p
- 04-06 >=4.6p
- 06-08 >=4.6p
- 08-10 >=5.9p
- 10-11 >=6.2p

Wicks do not count.
This confirms the later V1.1 P90 merge inherited an exact historical detector rather than arbitrary display thresholds.

## 2. P90 was a momentum activation model
Source explicitly warns:
P90 is MOMENTUM, not mean reversion.
-25/-50 are distribution extension targets.
Initial bi-directional logic was intended to simplify measurement before bias confirmation.

This distinction matters for FORGE teaching.

## 3. Cascade engine recovered
Historical cascade statistics:
Initial: N3262, WR83.3%, avg extension18.4p, avg hold89m.
2nd: N1847, WR87.8%, extension22.6p, hold76m.
3rd: N892, WR84.2%, extension19.8p, hold82m.
4th+: N318, WR76.4%, extension16.2p, hold94m -> AVOID.

Timing:
15-30m N412 WR82.4
30-45 N687 WR86.8
45-60 N524 WR88.2 BEST
60-90 N224 WR85.4
90-120 N98 WR79.8

These are historical backtest/report claims; raw JSON exists and should be separately reproduced.

## 4. 45-minute add
Historical:
+45m from initial P90 AND resolution output +8p.
Reported WR91.2%, frequency64.3%, avg extension26.8p.
Cascade P90 reported WR87.8%, frequency56.6%, avg extension22.6p.
Both together claimed 93.4%.

Important: time-based and signal-based confirmations were treated as complementary observations of same process.

## 5. Exact historical tier engine
Asian Range 7PM-3AM EST:
T1 <20p; expected daily ~72p; factor3.12x
T2 20-30p; ~58p; factor2.68x
T3 30-45p; ~48p; factor2.18x
>45 NO-GO.

This is historical EUR daily range/P90 generation and should be linked to, but not confused with, later Weekly Engine tiers.

## 6. Failure/repair model recovered
From CEREBUS_STRATEGY_ANALYSIS:

After valid 2h acceptance hold, failure = first M5 close back inside Asian band before 1x target.

N465 valid 2h-hold setups:
- 52.0% hit 1x before failure
- 45.2% failed first
Among failures:
- midpoint hit first 73.8%
- opposite band edge 51.0%
- full flip to opposite 1x 20.0%

Three states:
1 Soft Failure -> midpoint/compression
2 Internal Reset -> midpoint, reclaim original side, second 2h acceptance
3 Regime Flip -> midpoint, opposite edge, violation, second 2h hold, opposite 1x.

Second signal:
- valid 2h hold 50.5%
- second accepted WR69.8%
- same-side reacceptance WR67.7%
- opposite-side flip WR84.6%

This is a strong ancestor of later reset/rekey/state-transition doctrine.

## 7. Failure timing
Historical:
~35% failures 0-15m
~30% 15-30m
~20% 30-60m
~15% 60-120m

Thus source summarized:
65% fake violations fail within30m
80% within60m.

This is early state-age logic and should connect to later semi-Markov research, but not be treated as identical methodology.

## 8. Opposite P90 reversal protocol
Default opposite P90 = ignore.
Historical valid reversal required BOTH:
- close beyond 200% Deep State of initial P90
- 132% Kill-Switch also triggered.

Reported:
unconfirmed reversal WR52.4
confirmed reversal WR68.2
frequency1.4% sessions.

Again historical; reproduction required.

## 9. P90P Distribution Tracker recovered
Historical target model:
FINAL TARGET = Asian Range × Weighted Expansion Factor

Weighted Expansion:
0.40 Base Tier Factor
+0.25 Regime Adjustment
+0.20 P90 Confirmation
+0.10 Cascade Timing
+0.05 Time Decay.

6AM checkpoint:
expected ~65% of final; +5% if P90 confirmed.

9AM:
Regime Ratio = Daily Range(3-9) / Asian Range
>=1.50 CONFIRMED -> completion90.2%
1.45-1.49 CAUTION ->86.1%
<1.45 FAILED ->73.8%.

This recovers the exact historical source of the 6/9/12 checkpoint numbers.

## 10. P90P claimed accuracy ladder
Historical report claims:
pre-session base ±10p 78%
pre-session +P90 ±7p 84%
6AM base ±7p 82%
6AM +P90 ±4p 89%
9AM base ±5p 85%
9AM +regime ±3p 91%
9AM +regime+P90 ±2.5p 94-95%
11AM all conditions ±2p 96%.

These must be tagged HISTORICAL_REPORT_CLAIM / REPRODUCTION_REQUIRED.

## 11. Parts 6-15 map recovered
P6 Monte Carlo
P7 Monday Asian Range Float
P8 Daily Asian Range Float
P9 Full-Day Range Regime Tracker
P10 Dual-Engine Execution
P11 Failure Sequence / Repair
P12 Two Plays
P13 Triple-Engine Monte Carlo
P14 Blind Structural Chain Law / Recursive Loop Engine
P15 Fractal Resolution Engine / Nested Cycle Analysis
then Daily Setups 1-6.

This is likely one of the best maps for recovering the “Bible” generation.

## 12. Key lineage interpretation
Historical P90 generation already contains ancestors of several later ideas:
- time-dependent thresholding
- state acceptance/failure
- reset/reacceptance
- state-age/failure timing
- range tiering
- remaining distribution estimation
- checkpoint updates
- conditional target recalculation
- extension/rekey kill states.

Modern CEREBUS should not simply inherit its claimed probabilities.
The concepts can survive while the calibration is re-tested.

## 13. Next targets in larger-lab
Prioritize:
- P14 Blind Structural Chain Law
- P15 Fractal Resolution Engine
- P7/P8 Float mechanisms
- P9 Regime Tracker
- P10 Dual Engine
- P12 Two Plays
- P13 Triple Engine
- exact Daily Setups 1-6
- raw p90_cascade_results.json
- strategy implementation
- search repository history/other paths for Markov/Quant Journal/Bible naming variants.
