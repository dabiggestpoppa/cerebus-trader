# FORGE RECOVERY PASS 11 — ILM / MAE / MODEL-SYNTHESIS / VISUAL FRAMEWORK

**Date:** 2026-10-04
**Branch:** forge

## 1. EUR ILM retest recovered and pushed

Artifact:
`CEREBUS_EU_ILM_RETEST_REPORT.md`

Dataset:
- EURUSD M5;
- Nov 2022–Sep 2026;
- fixed server→NY -7h research clock;
- daily candle 17:00 NY→17:00 NY;
- weekly Monday–Friday.

Geometry:
bullish prior candle:
50 = H-.50R
61.8 = H-.618R
72 = H-.72R
80 = H-.80R
directional -25 = H+.25R
directional -50 = H+.50R
with bearish mirrored.

Recovered result:
- previous-day 50–61.8 touch D+1 ~71.08%;
- Monday→Tuesday ~74.11%;
- 2026 OOS ~73.14%.

But standalone continuation execution failed badly:
- 50 entry target-before-stop ~27.66%;
- 61.8 ~15.93%;
- 72 ~6.65%.

Conclusion:
**location can be statistically recurrent without being a standalone trade.**

The 80 stop was too tight for unconditional continuation.

This is a major conceptual bridge to later MAE / recovery-confirmation work.

## 2. MAE is not one model

Recovery indicates “MAE” appears in at least two meanings:
1. Maximum Adverse Excursion as a diagnostic/risk statistic.
2. Later entry research using adverse excursion/recovery behavior to improve entry timing.

Do not create a single artifact called “the MAE model” until exact source definitions are recovered.

## 3. XAU gives mature MAE-aware promotion examples

Final XAU Freeze records:
- 68+8h→80 promoted: 42/48 = 87.5%, median MAE ~0.040 M1;
- 120+8h→132 primary: 24/25 = 96.0%, median MAE ~0.035 M1;
- 132→168 parked: ~35% at 8h and ~53% at 24h.

This demonstrates modern promotion logic:
high hit rate + bounded adverse excursion + clear invalidation + sufficient N + temporal acceptance.

## 4. Recovered ILM lesson for FORGE

Separate these probabilities:

A. **Touch probability** — will price visit the zone?
B. **Conditional continuation probability** — after touch, does it continue?
C. **Execution probability** — does target occur before structural invalidation?
D. **Economic expectancy** — after stop distance, target distance, costs and management, is the trade worthwhile?

A 70% touch rate can coexist with a terrible mechanical trade.

This should be a first-class educational doctrine in Ask CEREBUS.

## 5. Old model-synthesis workbook discovered

Artifact:
`cerebus 3 market hoily grail (3).xlsx`

Search metadata indicates a sheet:
`PHASE 7 - MODEL SYNTHESIS & INTEGRATION`

and a historical `PHASE 2 VALIDATION RESULTS` surface spanning roughly Jan 2020–May 2025 with:
- sessions analyzed;
- claims validated;
- pass rates;
- claim name;
- claimed %;
- actual %;
- variance;
- status.

This workbook is potentially a major missing bridge between old deterministic hypotheses and later scientific re-audit.

It needs dedicated spreadsheet recovery rather than snippet-based interpretation.

Status:
**HIGH-PRIORITY DISCOVERED BINARY / NOT YET INGESTED**

## 6. Trading Framework infographic recovered as conceptual evidence

Named visual:
`Cerebus Trading Framework Infographic.png`

It preserves a mature two-edge framing:

### Forecasting edge
**STATE → EXPECTED DISTRIBUTION**
- range-tier relationships;
- time windows;
- regime logic;
- multi-market validation.

### Execution edge
**LOCATION → ASYMMETRIC ENTRY**
- normalized structural locations;
- cheap invalidation relative to remaining move.

Top-level language:
`RANGE • TIME • STATE • LOCATION • EXECUTION • DELIVERY`

This visual is valuable because it compresses the modern CEREBUS operating philosophy better than many technical files.

## 7. Model-search result

No clean surviving artifact explicitly named “DTB model” or “XGBoost model” surfaced in this pass.

Do not invent them from vague conversation terminology.

Statuses:
- DTB: SEARCH_PENDING / TERM_NEEDS_DISAMBIGUATION
- XGBoost-specific artifact: SEARCH_PENDING / POSSIBLY_CONVERSATION_DERIVED

## 8. Scientific continuity

The modern EUR compendium reinforces why ILM could not be used blindly:
- M1 seed 50% retracement common;
- deeper rekeys not rare;
- path bias does not imply one-way continuation.

XAU similarly freezes:
- 25–50% normal macro rotation;
- 50–68% failure developing;
- 68%+ repair/deeper-rekey.

Thus the mature system treats pullback depth as a **state classification problem**, not merely an entry percentage.

## 9. Recovery priorities created by this pass

1. Fully inspect old “3 market holy grail” workbook sheet-by-sheet.
2. Recover claim IDs and determine which old hypotheses became:
   - validated,
   - falsified,
   - superseded,
   - absorbed into later models.
3. Search for companion workbooks/scripts around Phase 2 / Phase 7.
4. Recover MAE-specific entry studies rather than merging all MAE references.
5. Continue visual registry using the mature framework infographic.
6. Keep searching DTB/XGBoost terminology through conversation history and neighboring artifacts.
