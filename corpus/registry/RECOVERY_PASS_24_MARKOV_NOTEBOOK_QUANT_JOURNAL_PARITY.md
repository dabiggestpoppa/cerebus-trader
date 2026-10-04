# FORGE RECOVERY PASS 24 — MARKOV NOTEBOOK + QUANT JOURNAL + PARITY CONTRADICTION

Date: 2026-10-04

## Executive finding
The larger-lab Quant Journal/Bible are a major chronology source, but they also expose a severe evidence-lineage issue: the same Aug-09 Symmetry Trap parity artifact family contains contradictory performance summaries.

## 1. Markov notebook was never executed
CEREBUS_Markov_Chain_Colab.ipynb:
- says it intends to learn transitions from actual price data across 18 assets;
- loads *_training.parquet files;
- defines Holy Grail priors;
- begins a learn_transitions_from_data function;
- every notebook execution_count is null;
- no cell outputs;
- final cells empty/incomplete.

Disposition: ABANDONED/UNEXECUTED_RESEARCH_PROTOTYPE.

There is no evidence in this notebook that the 18-asset learned Markov matrix was ever produced.

## 2. Local Markov result confirmed prior-only
markov_local_results.json is from the prior-based local runner, not notebook fitting.
Its matrix construction is also structurally questionable because the initializer overwrites/distributes rows repeatedly for each prior transition. Many rows show nearly uniform mass rather than the intuitive prior transition stated in comments.

Disposition: DO_NOT_PRODUCTIZE_AS_EMPIRICAL_MARKOV.

## 3. ST/P90 Markov is simulation/wrapper evidence
st_p90_markov_results.json:
ST traded WR 77.69%; P90 traded WR 59.90%.
It separately records comparison backtests ST .857 and P90 .787.
Therefore the simulated state machine outcomes are not reproductions of the source backtest WRs.

Disposition: EXPERIMENTAL_WRAPPER / NOT CANONICAL PERFORMANCE.

## 4. Quant Journal chronology recovered
Quant Journal updated Aug09 contains:
- failed EURCHF triangular basis test with explicit negative result;
- ST live parity claim;
- June08 9K unlock config;
- June07 cost-adjusted backtest;
- June04 frequency normalization and max-accuracy sweeps;
- forward-test plan.

This is high-value historical evidence because it records both successes and failures.

## 5. ST evolved materially after May31
June/Aug generation includes:
- ar_max=999 in 9K unlock test;
- per-asset trigger coefficients;
- 4PM cutoff;
- flat DZ 20-50%;
- later parity configuration ar_max60 all tiers;
- production/live hard exit 5PM;
- realistic wick/touch-based stop semantics.

This is not the same exact implementation as the original May29 12PM/close-only reconstruction.

## 6. Major parity contradiction
PARITY_REPORT.md claims:
3120 trades
79.13% WR
+15101.36p
0 divergences.

But parity_summary.json in the same artifact directory says:
1947 canonical trades
55.880842% WR
-889.129p
1947 live trades
same negative result
0 divergences
parity_achieved=true.

This is critical.

Important distinction:
PARITY means live == backtest under the same implementation/config.
It does NOT establish that the implementation is profitable.

Both artifact versions can prove parity while disagreeing completely about strategy performance.

Status: ARTIFACT_FAMILY_INTERNAL_CONTRADICTION.

## 7. Quant Journal/Bible repeat the positive parity numbers
Both documents promote 3120 / 79.13% / +15101.36p.
Therefore those documents are downstream of the positive parity report and are not independent corroboration.

## 8. Evidence rule for FORGE
A summary document must never outrank its machine-readable artifact automatically.
When report.md and result.json disagree:
1 raw trade/event ledger
2 executable config + code hash
3 machine-generated result
4 report
5 journal/bible summary
must be reconciled before canonical promotion.

## 9. Historical campaign remains distinct
May31 full_backtest_campaign_v3.json contains per-asset historical outputs, e.g. EURUSD 1163 trades/85.0%, GBPUSD1259/85.7%, etc.
These are a separate config/generation from Aug parity and must not be merged.

## 10. New lineage labels
ST-G0 ontology reconstruction: 12PM, close-only semantics.
ST-G1 May29 composite.
ST-G2 May31 corrected multi-asset campaign.
ST-G3 June optimization/calibration family.
ST-G4 9K unlock / AR gate relaxation.
ST-G5 Aug live parity/deployment family.
Exact boundaries remain provisional until git-history diff.

## 11. Productization consequence
FORGE must version model identity as:
engine_name + implementation_generation + config_generation + data_generation + execution_semantics.

Never answer "Symmetry Trap WR is X" without those qualifiers.

## Next
- inspect parity trace/raw ledger and git history around Aug09 to determine which parity summary is newer/valid
- inspect June optimization reports and 9K raw JSON
- inspect Quant Journal older sections / git history for mutation chronology
- audit actual MLR Markov JSON separately from abandoned Holy Grail notebook
- recover Bible references to P14/P15/Blind Chain and separate them from ST lineage.
