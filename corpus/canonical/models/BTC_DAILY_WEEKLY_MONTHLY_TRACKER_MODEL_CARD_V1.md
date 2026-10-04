# MODEL CARD — BTC Daily/Weekly/Monthly Tracker V1

model_id: BTC.TRACKER.DWM.V1
status: ACTIVE_RESEARCH_IMPLEMENTED
market_scope: BTCUSD
layer: CROSS_LAYER_CONTEXT
model_type: DISTRIBUTION + PATH + STATE
product_exposure: SUBSCRIBER_MODEL

## Purpose
Track BTC distribution across daily, weekly and monthly horizons while preserving each clock and avoiding premature fusion with the separate BTC Game research branch.

## Daily core
Asian window19:00-03:00 NY research frame.
Modern BTC native tiers:
T1 < $750
T2 $750-$1,700
T3 $1,700-$3,000
> $3,000 NO-GO.
AU205/545/1160.
Triggers246/654/1392.
Density zones164-246 /436-654 /928-1392.
These belong to the BTC calibration generation and are not FX pip equivalents.

## Daily path surface
Modern research extends slot x tier / range-left context from03:00 through19:00 NY.
12PM no-new-extreme research is a checkpoint inside the larger daily cycle, not the entire model.

## Weekly context
Research includes Friday/Thu-Fri anchor behavior, weekly MLR/rekey work,48h rules after daily/weekly rekey events and weekend transition studies.
Exact promoted setup status remains evidence-dependent.

## Monthly context
Monthly range prediction/tracking exists as context layer. Do not infer that every monthly displayed level is scientifically promoted.

## Separation rule
BTC Daily Tracker and BTC Game remain distinct during validation.
Old Gold Game setups or old BTC Atomic setups may not be inserted into BTC Game/Tracker merely because geometry resembles them.

## Implementation
CEREBUS_BTC_Daily_Weekly_Monthly_Tracker_V1.pine.

## Evidence safety
Raw hit rate, call lead time and executable RR are separate metrics.
Weekend/weekly transition definitions require exact research-day ownership.
News/event effect, rekey excursion and deep violations require Evidence Cards.

## Ask CEREBUS
Beginner: Tracker tells you the current BTC range regime and what distribution remains across several clocks.
Operator: Return daily tier, active range-left state, rekey/extension context and weekly/monthly anchors with status.
Researcher: Return calibration period, exact clock/session, event definitions and whether a field is measured, display-only or experimental.
Forbidden: claiming a current BTC Game exists from Tracker data; importing Gold setups without validation.
