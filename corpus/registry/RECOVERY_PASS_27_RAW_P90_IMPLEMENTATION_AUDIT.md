# FORGE RECOVERY PASS 27 — RAW P90 IMPLEMENTATION AUDIT

Date: 2026-10-04

Sources:
- larger-lab/quant-lab/backtests/p90_cascade_results.json
- larger-lab/quant-lab/backtests/p90_cascade_activation_20260517_010329.json
- larger-lab/quant-lab/backtests/p90_cascade_activation_20260517_012625.json
- larger-lab/quant-lab/strategies/p90_cascade_activation.py
- larger-lab/quant-lab/strategies/CEREBUS_V5_LIVE_PERFECT_FORM.pine

## Executive result
The repository contains a REAL implemented P90 lineage, but the raw reconstructed automation does NOT reproduce the manual's 83-93% cascade win-rate claims.

This does NOT falsify the P90 phenomenon or operator research. It proves that claim identity and implementation identity must be separated.

## 1. Raw result artifact A
p90_cascade_results.json:
EURUSD M5
249,484 bars
2023-01-02 to 2026-05-06
1,153 trades
645 sessions
502 wins /651 losses
WR43.5%
PnL +430.02p
avg win9.37p
avg loss-6.57p
max DD -180.36p
PF1.10.

By activation:
initial645 /34.9% / -151.45p
cascade1 295 /51.2% / +127.05p
cascade2 183 /60.1% / +422.32p
45m add30 /53.3% / +32.1p.

This is important:
the implemented cascade hierarchy shows increasing conditional performance from initial -> cascade1 -> cascade2 in this artifact, even though absolute WR is far below manual claims.

## 2. Raw result artifact B
p90_cascade_activation_20260517_012625.json:
1,284 trades
746 sessions
430 wins
WR33.5%
PnL -2322.05p
PF0.62.

initial29.1
cascade1 43.0
cascade2 30.6
45m add50.0.

Earlier timestamp artifact generated zero trades.

Therefore at least THREE implementation states exist:
zero-trade broken run
negative33.5% run
later43.5% / PF1.10 run.

This is implementation evolution, not one frozen backtest.

## 3. Manual vs code mismatch
Manual historical claims:
initial83.3
cascade1/second87.8
third84.2
45-60 sweet88.2
cascade+45m93.4.

Raw automation does not reproduce these.

Disposition:
MANUAL_CLAIMS = HISTORICAL_REPORT_CLAIM / REPRODUCTION_REQUIRED.
RAW AUTOMATION = IMPLEMENTATION_EVIDENCE.
Do not merge their statistics.

## 4. Python reconstruction has material semantic differences
The Python strategy adds:
- candle body >60% of total candle range as P90 quality filter
- fixed UTC-5 conversion
- daily calendar reset
- 120m trade exit tied to initial P90 time
- its own execution/SL/TP semantics.

Most importantly, P90 detector in Python checks body magnitude/direction but the detector itself does not encode "close outside Asian band" as part of _check_p90_signal. That condition must be verified elsewhere in entry logic before claiming parity.

## 5. Session clock risk
Python:
if timezone-aware, tz info is stripped, then hour is mapped UTC->EST by subtracting5.
This assumes input bars are UTC before stripping and uses fixed EST, not DST-aware America/New_York.

V5 Pine similarly:
get_est_hour = UTC hour -5.
Thus both implementations intentionally/implicitly use fixed EST rather than NY DST.

Modern CEREBUS session research explicitly treats clock/DST/day ownership/final bar as part of the data definition.
Therefore old P90 result identity MUST include FIXED_EST clock semantics.

## 6. Asian range implementation risk in Python
Python resets state on calendar date, while Asian range spans 19:00-03:00.
This deserves a dedicated session-ownership audit because a midnight reset can split the intended Asian session depending on input-date handling.

Do not use the Python result as definitive P90 falsification until session ownership is reproduced correctly.

## 7. V5 Pine is not the same implementation as Python
V5 Pine:
- computes Asian range 19:00-03:00 fixed EST
- P90 bull/bear signal = directional body threshold in window
- uses in_hold_period to block repeated signals
- tracks -25/-50 extensions
- 132 violation
- two simultaneous positions plus45m add
- P90P visual tracker.

V5 P90 candle logic shown does NOT require body/range >60%.
Python DOES.

That alone changes signal population.

V5 also contains a likely implementation hazard:
strategy.entry IDs shown as "P90_Pos1_Long", "P90_Pos2_Long", "P90_Pos3_Long" while direction handling must be audited to verify shorts are actually submitted as shorts rather than only represented in target math.
Do not declare bug until full code path is checked, but flag IMPLEMENTATION_AUDIT_REQUIRED.

## 8. V5 P90P tracker is explicitly visualization-only
This is important for FORGE:
2AM/6AM/9AM targets and "Accuracy Est." displayed in Pine are a visualization layer populated by historical constants.
They are not independent live validation.

FORGE must distinguish:
MEASURED LIVE STATE vs HISTORICAL LOOKUP/CONSTANT vs MODEL OUTPUT.

## 9. Strong surviving P90 insight
Even with poor raw parity, the 43.5% artifact shows:
initial34.9
cascade1 51.2
cascade2 60.1.

This supports a weaker but meaningful structural hypothesis:
repeated same-direction qualifying impulses may carry incremental conditional information.

It does NOT reproduce 83-88% claims.
This should be retested from raw candles with corrected session ownership and exact event definitions.

## 10. Why this differs from ST status
ST:
manual strategy/operator rules retained;
automation post-deployment not approved;
stop spending recovery time debugging it.

P90:
actual automation artifacts exist and evolved;
raw implementation produced trades;
one artifact is slightly profitable PF1.10;
the mechanism remains worth auditing/reproducing because it is an automation-capable lineage.

Thus P90 status = ACTIVE RECOVERY / REPRODUCTION CANDIDATE, not CANONICAL VALIDATED yet.

## 11. FORGE evidence schema update
Every quantitative claim should carry:
CLAIM_SOURCE = manual | raw_backtest | scientific_retest | live_operator | simulation | visualization_constant
IMPLEMENTATION = script/version/hash
CLOCK = fixed_EST | NY_DST | UTC | unknown
SESSION_OWNER = definition
SIGNAL_POPULATION = exact filters
TARGET = exact definition
EXIT = exact definition
SAMPLE = N/date range
STATUS.

This prevents recurrence of manual-number vs code-number collapse.

## Next
- inspect complete V5 long/short order semantics
- inspect Python Asian session/date ownership and entry outside-band condition
- derive P90_LINEAGE_REGISTRY
- derive V4_TO_MODERN_CROSSWALK
- design clean reproduction test rather than patching old scripts.
