# FORGE RECOVERY PASS 10 — MARKOV / SEMI-MARKOV / ML NEGATIVE EVIDENCE / RESET SEARCH

**Date:** 2026-10-04
**Branch:** forge

## Search outcome

The exact legacy `CEREBUS_Markov_Chain_Colab.ipynb` still did not surface as a Library artifact.

The exact six ASE cycle expressions also remain unrecovered.

However, this pass found the later scientific successor to the Markov idea and additional evidence explaining why the architecture changed.

## 1. Markov idea survived — but matured into semi-Markov state age

The Research Supplement explicitly contains:
**TIME AS STATE AGE: FROM MARKOV TO SEMI-MARKOV**

Recovered structural-duration test:
- mechanical H1 major-swing detector;
- ~35p prominence;
- minimum 12h separation;
- 769 major extrema;
- median duration 27h;
- Q25 13h;
- Q75 64h;
- <24h 44.7%;
- 24–72h 35.2%;
- >72h 20.2%.

Robustness:
- 30p prominence → median 23h / 32.3% in 24–72h;
- 35p → 27h / 35.2%;
- 40p → 32h / 36.2%.

Interpretation:
24–72h is a dense structural duration zone, NOT a universal timer.

This is the mature descendant of the early Markov/state-transition intuition:
transition probability depends not only on current state but on **how long the state has existed**.

## 2. ML / higher-order interaction negative evidence recovered

`CEREBUS_HYPERGRAPH_RESEARCH_V0_1.md` was discovered.

Pilot:
EURUSD Daily 08:00 range-forecast residual correction.
- train through 2025;
- test 2026, n=163;
- existing baseline MAE 11.34p;
- median AE 9.55p;
- <=10p hit 52.76%.

Hypergraph categorical residual correction:
- order 1 MAE 12.09p;
- order 2 12.08p;
- order 3 12.10p;
- order 4 12.09p.

Verdict in artifact:
reject adding the hypergraph residual layer to this forecast because it degraded the existing baseline.

This is another critical negative result:
more state interactions do not automatically improve prediction.

## 3. Modern Daily Model explicitly rejects weak ML additions

The recovered Daily Model V1 says:
**Do not promote pace, regime labels, or ML residuals unless they beat the live range-left baseline.**

This connects directly to ASE:
- deterministic locks failed;
- ornate state hierarchy failed;
- residual/hypergraph correction can fail;
- simple observable range-left + distance can outperform richer stories.

## 4. Modern state-transition ladder

Daily Model V1 preserves the mature transition language:

100 = Asian boundary interaction
125 = activation / pre-commitment
132 = first confirmed extension
168 = expansion
185 = deep continuation / acceptance

Any-side historical reach:
- 100 ~99.3%;
- 125 ~92.0%;
- 132 ~89.1%;
- 168 ~70.9%;
- 185 ~62.0%.

125→132:
- ~49.8% same M5 bar;
- ~45.1% later bar;
- ~5.0% fail by noon;
- conditional on not same-bar, later continuation ~90%;
- median later lag ~10m.

This is not the same state machine as the unrecovered legacy `RESET → AR_SET ...` notebook. Preserve as a later generation.

## 5. Residual-event state transition

Modern event logic:
- freeze event band at release;
- measure realized envelope;
- recalculate remaining Q50/Q75/Q90 budget;
- reclassify unresolved states at +15/+30/+60/+90/+120m;
- downgrade states beyond remaining Q90.

Recovered OOS summary:
- structural snapshot AUC ~0.824;
- residual-news field AUC ~0.840;
- residual field improved ranking at tested age checkpoints.

This is effectively a state-age / remaining-budget process and belongs conceptually beside the semi-Markov work.

## 6. Hypergraph later recovered as conditional context, not universal predictor

Passes 4–5 recovered B4/B5 where higher-order propagation state did improve some repair probabilities, while the earlier V0.1 residual-correction pilot failed.

Therefore the scientific lineage is:

**Hypergraph as generic feature expansion → rejected where it degrades baseline.**

**Hypergraph as narrowly specified higher-order propagation context → retained where chronological OOS evidence improves calibration/prediction.**

This distinction is crucial for FORGE users.

## 7. Early-week information-gain lineage

Research Supplement Phase 9B–9C preserved a progressive early-week search:
- Monday Asian baseline OOS MAE ~46.1p;
- Monday London no improvement;
- Tuesday Asian no improvement;
- Tuesday London combination ~42.3p;
- Wednesday Asian stricter ~39.7p;
- Wednesday London full early-week envelope ~35.1p.

Thursday/Friday were excluded from discovery to avoid late-information leakage.

Concept:
**information is valuable only if it arrives early enough to matter.**

This belongs in the same user-facing doctrine as path-state and range-left.

## 8. Old infinite-ladder / reset doctrine surfaced

Legacy FX v4 manual contains:
- nested distribution-phase framing across intraday / intraweek / macro;
- reset on Day 15;
- carry-one-position language;
- 60/80 threshold grid;
- old claim that identical Fibonacci architecture scales unchanged.

This is HISTORICAL DOCTRINE, not current validated architecture.

The later research repeatedly shows calibration/state behavior can be instrument- and regime-specific.

## 9. Artifact-transfer note

The Hypergraph V0.1 Markdown was read/discovered, but an attempted GitHub transfer was blocked by the safety layer. Do not mark it repository-pushed.

Status:
**DISCOVERED + READ / NOT PUSHED**

## 10. Recovery interpretation

The scattered research now reveals a coherent methodological evolution:

1. deterministic field/loop language;
2. Markov transition intuition;
3. failed deterministic-lock tests;
4. distance beats ornate lock variables;
5. state age matters → semi-Markov framing;
6. generic higher-order feature expansion can hurt;
7. narrowly causal higher-order context can help;
8. range-left + unresolved distance + clock + consumed state + residual budget becomes core.

This intellectual evolution should be exposed in FORGE as research history rather than erased by the latest model.

## 11. Still unresolved

- legacy Markov notebook;
- exact RESET→AR_SET transition vocabulary;
- exact six ASE expressions;
- ASE notebooks/source/configs;
- XGBoost-specific surviving experiment artifact if any;
- exact MAE-entry study artifacts;
- DTB named-model artifact;
- P90 Panels 1–4 originals;
- raw checkpoint tables.
