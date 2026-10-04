# FORGE RECOVERY PASS 3 — SCIENTIFIC / OOS DISCOVERY

**Date:** 2026-10-04
**Branch:** forge

## Scientific freeze artifacts confirmed in Library

### EUR
- CEREBUS_EUR_Scientific_Research_Compendium_V2.pdf
- CEREBUS_EUR_Higher_Order_Model_Scientific_Review_V1.pdf
- EUR_L2_L3_LEGACY_ABLATION_2026-10-01.md
- eur_quarter_oos_2023_2026.csv
- EUR_Monthly_x_Weekly_H60_Ablation.csv (referenced by scientific reproducibility package)
- eurusd_hour.csv (referenced)
- EURUSD.PRO_M5_202211080000_202607140000(1).csv (referenced)

### XAU
- CEREBUS_XAU_Scientific_Research_Compendium_V1.pdf
- CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine

### Hypergraph / execution
- B4 hierarchical-gate/OOS family remains part of recovery queue.
- b5_oos_summary_2024_2026.csv confirmed in Library.
- B5 execution family remains part of recovery queue.

## EUR scientific architecture recovered

V2 explicitly freezes the cross-layer handoff:

Quarter opening first 3 trading days
→ directional prior
→ M1 direction + range
→ quarter multipliers / M1 geometry
→ M2 shaping
→ M3 continuation / repair / deep rekey
→ weekly Tier + Hour×Tier + location
→ local path + range-left
→ daily range-left + asymmetry + state + news
→ execution feasibility.

This confirms that later CEREBUS is intentionally sparse: higher layers do not become entries merely because their directional probability is strong.

## XAU scientific architecture recovered

The XAU compendium freezes:
- D1-D3 = Month-1 path seed.
- D2-D11 = quarter-direction prior.
- Full M1 = quarter-scale anchor.
- M2 = shaping.
- M3 = resolution.
- L2 weekly state narrows path.
- L1 daily structure executes.

It explicitly states that research penalized attempts to convert strong state probabilities directly into entries.

The final Pine implementation follows this scientific freeze rather than the earlier Gold Game matrix. Therefore older Gold Game artifacts must remain lineage, not silently overwrite the final scientific implementation.

## Legacy ablation significance

The recovered EUR L2/L3 legacy ablation demonstrates an important CEREBUS research behavior: older setup families were retested against newer state filters instead of simply being merged.

Examples include:
- Weekly Coiled Spring: strong observed outcomes but N=7 → retain only as small-N research flag.
- Weekly Deep Reset: N=2 → park.
- Weekly Standard Rekey: promising but parked as primary due to small N.

This should become a FORGE teaching example for why high win rate alone does not promote a model.

## Reproducibility doctrine

The scientific PDFs identify explicit reproducibility packages and minimum reproduction sequences. FORGE should preserve these as machine-readable study manifests.

A scientific study should eventually expose:
- discovery dataset;
- validation/OOS dataset;
- exact clock;
- transformation;
- anti-leakage rule;
- event ordering;
- output table;
- indicator implementation;
- supersession lineage.

## Binary / large artifact handling

PDFs and CSV result artifacts are confirmed but are not claimed as GitHub-pushed in this pass unless an exact successful write occurred. Recovery must distinguish:
1. discovered in Library;
2. read/verified;
3. materialized;
4. pushed to repository;
5. canonicalized.

This prevents false corpus-completeness claims.

## Next targets

1. Recover XAU final Pine through a safe staged path.
2. Recover B4/B5 result surfaces and CSV manifests.
3. Recover temporal-cycle registry and chapter.
4. Recover unified retrieval corpus through staged transfer.
5. Build visual/infographic inventory.
6. Search for BTC Daily Tracker/Game surviving code/results.
7. Search for recent EUR V1.6.x indicator lineage.
