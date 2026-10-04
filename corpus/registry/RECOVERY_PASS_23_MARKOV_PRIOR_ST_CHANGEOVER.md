# FORGE RECOVERY PASS 23 — MARKOV PRIOR AUDIT + ST CHANGEOVER

Date: 2026-10-04

## 1. Markov local result is NOT an independently learned result
The local runner explicitly says it uses Holy Grail priors as the transition matrix and simulates 10,000 weekly sequences from priors.

The delivery outputs .9096/.8768/.8084/.6269/.0382 are algebraic combinations of those priors, not fresh empirical estimates.

Disposition: HISTORICAL_PRIOR_PROPAGATION, not VALIDATED_MARKOV_EDGE.

The model class can fit observed sequences, but the recovered local result file does not demonstrate that fit path.

## 2. Priors are workbook-era numbers
Examples embedded in code:
T1 -25 .982
T2 -25 .964
T3 -25 .872
-25 -> -50 .964
-50 -> -100 .922
-50 -> REKEY .715
REKEY -> consolidation .85
consolidation -> extension .78.

This directly links Markov generation to Holy Grail/workbook claims recovered in earlier passes.

## 3. ST/P90 Markov is also downstream
The focused ST/P90 Markov file embeds prior backtest results such as ST .857/PF8.18 and P90 .787/PF3.09. Treat it as a probabilistic wrapper around engine backtests until its own event construction is audited.

## 4. May28 -> May31 ST changeover is now partially resolved
May28 reconstruction/calibration used earlier implementations and reported ST ~35-40% and Blind Chain 0%.

By May29 the repository contains a reconstructed 4-state FSM composite report with:
892 trades, 85.7% WR, PF8.18 on EURUSD M5.

By May31 Backtest Campaign v3 reports 19 ST assets, 14,563 trades, avg86.6%.

The May31 campaign explicitly attributes prior failures to:
- wrong default tier config
- CSV column mismatch
- wrong EST session grouping
- wrong engine API calls.

Therefore part of the apparent contradiction was infrastructure/configuration error, not necessarily a change in market edge.

## 5. But the engine itself also changed
A preserved file symmetry_trap_original_pre_change.py says:
- 12PM activation end
- close-only zero-buffer structural extreme.

Current symmetry_trap.py now says:
- wick-based zero-buffer impulse extreme
- activation end 16:00, marked optimized June4
- AR gate decoupled from tier, ar_max60 for all
- tier classified by impulse size rather than AR
- multiple TP modes exist.

So the name Symmetry Trap spans multiple materially different generations.

## 6. Critical semantics conflict
Historical docs/report call SL close-only.
Current engine header calls SL wick-based.
Backtest docs still contain close-only wording.

FORGE must not store one universal ST stop definition.
Need implementation-version-specific semantics.

## 7. May29 composite report itself has internal timing tension
It describes doctrine 12PM reset, while deployment checklist later lists entry window2AM-11AM and hard exit5PM. This may mix research engine and executor/deployment settings.

Status: DOCUMENT_INTERNAL_TIMING_CONFLICT.

## 8. Multi-asset high-WR campaign provenance
May31 v3:
ST 19 assets / 14,563 trades / avg86.6%.
P90 18 assets / 23,448 trades / avg83.0%.

It says the corrected campaign used:
symmetry_trap_backtest.py
p90_backtest.py
per-asset asset_configs.py
proper EST grouping.

These results are HISTORICAL_CAMPAIGN_EVIDENCE, not automatically modern canonical.

## 9. XAG calibration demonstrates asset-native tiering
XAG originally classified all sessions NO_GO because forex thresholds were reused.
Recalibration expanded its tier scale and produced 651 trades in that historical campaign.

This strongly supports modern doctrine:
structural form may transfer; thresholds require instrument-native calibration.

## 10. Provenance schema update
Add:
result_origin = empirical_backtest | prior_simulation | derived_algebra | monte_carlo_resample | manual_claim.
implementation_generation.
execution_semantics = close | wick | tick | market | limit.
session_generation.
config_generation.
infrastructure_validity.

## Next
- inspect notebook to see whether any real fitted Markov run exists
- diff pre-change vs May29 engine around SL/session/tier/loop mechanics
- inspect May29-May31 journals for exact fix sequence
- recover Quant Journal/Bible model chronology
- audit raw v3 result JSON and per-asset reports
