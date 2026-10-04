# EVIDENCE CARD — EUR Residual News Field Incremental Information

evidence_id: EV.EUR.DAILY.NEWS_AUC.V1
claim_id: CL.EUR.DAILY.NEWS_INCREMENT
status: CANDIDATE
evidence_type: SCIENTIFIC_RESEARCH_RESULT
source_generation: Daily News + Rekey research
market: EURUSD

## Exact claim
Adding the recovered residual news/event field improved the referenced classification AUC from .824 to .840 relative to the baseline feature set.

## Result
Baseline AUC .824.
With residual news field .840.
Delta +.016.

## Interpretation
Supports news/event information as an incremental conditioning feature rather than a replacement for geometry.

## Does not support
News causes direction.
A1.6 percentage-point WR increase.
Universal event impact.
Use of non-EUR releases without explicit model definition.

## Status note
Keep CANDIDATE until exact train/OOS split, target label and feature implementation are attached to this evidence object.
