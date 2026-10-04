# FORGE RECOVERY PASS 17 — LARGER-LAB / QUANT-LAB DISCOVERY

Date: 2026-10-04

## 1. Repository location corrected
The requested historical Quant Lab corpus is NOT primarily inside cerebus-trader/master.

Connected GitHub inventory confirms two separate repositories:
- dabiggestpoppa/larger-lab
- dabiggestpoppa/quant-lab

The large historical corpus is embedded under:
larger-lab/quant-lab/

This explains why earlier searches of cerebus-trader/master did not surface Quant Journal / Bible / P90 / ST material.

## 2. High-value CEREBUS artifacts confirmed in larger-lab/quant-lab

Recovered paths include:
- quant-lab/reports/ATOMIC_STRUCTURE.txt
- quant-lab/reports/CEREBUS_ATOMIC_STRUCTURE.txt
- quant-lab/reports/CEREBUS_P1-5_P90_CORE.txt
- quant-lab/reports/CEREBUS_P6-10_ADVANCED.txt
- quant-lab/reports/CEREBUS_P11-15_META.txt
- quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt
- quant-lab/reports/P90_STRATEGY_GUIDE.md
- quant-lab/reports/PART_5___P90P_Distribution_Tracker.txt
- quant-lab/research/CEREBUS_STRATEGY_ANALYSIS.md
- quant-lab/research/P90_DEEP_DIVE.md
- quant-lab/backtests/p90_cascade_activation_20260517_010329.json
- quant-lab/backtests/p90_cascade_activation_20260517_012625.json
- quant-lab/backtests/p90_cascade_results.json
- quant-lab/strategies/CEREBUS_V5_LIVE_PERFECT_FORM.pine
- quant-lab/strategies/p90_cascade_activation.py

This is a major corpus expansion.

## 3. Atomic Structure source recovered
ATOMIC_STRUCTURE.txt and CEREBUS_ATOMIC_STRUCTURE.txt preserve an April-2026 EURUSD M5 “Cerebus Cycle — Final Form” generation.

Historical components:
- Atomic Unit:
  T1 10p / T2 12p / T3 15p
- Tier Threshold:
  T1 10p / T2 15p / T3 19p
- Density Zone:
  overlap of AU completion and Tier Threshold resolution
- Convergence Factor PHI:
  0.40 Regime + 0.25 P90 + 0.20 Cascade + 0.15 Float
- historical PHI mapping:
  1.0 -> claimed 98.7%
  >=.8 -> 91-94%
  >=.6 -> 85%
  <.6 -> NO-GO
- EWS filter:
  opposite P90 within 30-90m
- hard exit:
  12 PM EST
- kill switch:
  132% Asian Range violation
- shift target:
  1.44x runner target

These are HISTORICAL MODEL CLAIMS and require modern reproduction.

## 4. Seven-state Atomic execution machine
Recovered explicitly:
1. IMPULSE DETECTED
2. WAIT FOR PULLBACK
3. DENSITY ZONE CONFIRMED
4. OPPOSITE CANDLE PRINTS
5. ENTER
6. TARGET
7. CLOSE AND RESET

This is important because it gives an exact historical state-machine implementation rather than only conceptual descriptions.

It may be related to later ASE state-transition research but should not be conflated without lineage proof.

## 5. First Impulse Predictor
Historical model claims a 3-4 AM early tier predictor:
- early range <10p + impulse >=12p -> T2, claimed 91%
- early range <15p + impulse >=18p -> T3, claimed 89%
- early range <20p + impulse >=25p -> NO-GO/extreme T3, claimed 94%
- below threshold -> current tier, claimed 85%

This is a concrete predecessor candidate for later velocity/tier-state research.

Status:
HISTORICAL_CLAIM / REPRODUCTION_REQUIRED.

## 6. Fixed Dollar Expectancy doctrine
Historical Atomic source also contains “FDE — Target-First Sizing”:
size position by desired fixed-dollar target divided by atomic target distance and pip value.

This is execution/risk doctrine, not structural market evidence.

Its justification relies on historical 98.7% accuracy/EWS claims and must not be presented as current validated risk doctrine.

## 7. Critical scientific lineage
This source helps explain why later ASE re-audit mattered.

The April-2026 text uses strong language:
- “certainty filter”
- “pure physics”
- deterministic PHI-to-win-rate mapping
- near-certain resolution

Later research challenged exactly this style of claim:
- legacy Symmetry Trap execution did not reproduce cleanly;
- deterministic locks failed;
- richer state variables sometimes added no information;
- range-left/distance/state-age approaches became more defensible.

FORGE should preserve this contrast as intellectual history.

## 8. P90 corpus confirmed
The repository contains dedicated:
P1-5 core
P6-10 advanced
P11-15 meta
P90 deep dive
P90 strategy guide
P90 cascade backtests
P90 cascade implementation
P90 distribution tracker

Therefore future P90 recovery should come from this source tree rather than relying on old manual summaries.

## 9. Crypto Foundry / later state research also present
The same larger-lab tree contains:
- semi-Markov audits
- directional asymmetry surfaces
- field modeling bible
- extensive mechanism/result directories

This may contain later descendants relevant to CEREBUS state/duration/asymmetry doctrine, but must be separated from direct CEREBUS artifacts unless lineage is explicit.

## 10. Next pass priorities
Now search this repository directly for:
- Quant Journal
- Bible/master manuals
- Markov model/notebooks
- ST engines / Symmetry Trap engines
- P90 exact panel definitions and raw backtest outputs
- Atomic configs and calibration scripts
- model versions / experiment logs
- notebooks and result JSON/CSV

Do not spend recovery cycles on the old workbook unless needed for a specific lineage conflict.
