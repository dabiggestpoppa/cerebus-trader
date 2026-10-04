# EVIDENCE CARD — EUR Daily Phase1 Range Calibration

evidence_id: EV.EUR.DAILY.PHASE1_TIERS.V1
claim_id: CL.EUR.DAILY.TIER_CALIBRATION
status: VALIDATED
evidence_type: RAW_RESEARCH_LEDGER
source_artifact: corpus/research/eur/daily_range_tracker/PHASE_1_LEDGER.md
market: EURUSD
sample_n:995 research days
data_period: M5 source Nov2022-Sep2026 lineage

## Exact claim
For the recorded Phase1 session construction, Asian range magnitude was operationally segmented:
T1 <20p
T2 20-30p
T3 30-45p
>45p excluded/no-go.
Associated historical expansion multipliers were approximately3.12,2.68,2.18.

## Interpretation
Supports an asset-native tier calibration for this EUR Daily generation and decreasing expansion multiple as seed range widens.

## Does not support
Universal FX tiers.
Guaranteed final ranges.
Transfer to BTC/XAU/Oil.
Trade WR.

## Identity warning
Session19:00-03:00 NY/research-day ownership and final-bar convention are part of this claim. Recalibration is required if clock construction changes.
