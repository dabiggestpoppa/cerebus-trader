# MODEL CARD — EUR Daily News + Rekey V1

model_id: EUR.DAILY.NEWS_REKEY.V1
status: CANONICALIZATION_CANDIDATE
market_scope: EURUSD
layer: L1 / local distribution-execution context
model_type: DISTRIBUTION + STATE + EXECUTION_SUPPORT
product_exposure: SUBSCRIBER_MODEL

## Purpose
Estimate the remaining intraday distribution after the Asian seed range while accounting for range tier, distance/asymmetry, clock, consumed delivery states, rekey/extension state and EUR event perturbations.

## Inputs
Asian range 19:00-03:00 research-day frame; native tier; current price/distances; clock; consumed targets/states; rekey state; official EUR event family and historical event band where available.

## Core grammar
Asian seed -> tier/native scale -> path consumed -> distance asymmetry -> event perturbation -> remaining distribution -> operator context.

News modifies probability/remaining kinetic budget; it does not replace geometry.

## Outputs
Range-left / remaining distribution context; rekey/extension state; actionable levels; evidence/confidence labels. It is not a deterministic direction oracle.

## Eligibility / no-go
Historical Phase1 calibration:
T1 <20p
T2 20-30p
T3 30-45p
>45p NO-GO.
Threshold identity is calibration-specific and must be versioned.

## Rekey ladder lineage
100 /125 /132 /168 /185 appear in the modern Daily lineage. Exact operator meaning must be tied to setup/version; do not collapse reach, violation and target-before-stop statistics.

## Event doctrine
Only official EUR-relevant events belong in the EUR event layer unless a later model explicitly expands scope.
Residual event budget is subtractive: already-consumed movement changes what remains available.

## Evidence
Phase1 ledger: 995 qualifying research days under recorded session rules.
Modern scientific work found distance asymmetry more useful than static Asian directional bias.
Residual news field improved reported AUC .824 -> .840 in recovered research.
These claims require their own Evidence Cards before public numerical display.

## Known limitations
Clock/DST/day ownership are part of model identity.
AR>45 was excluded in the referenced calibration.
P90 merged indicator elements are lineage/context and do not import historical P90 win rates.
Range reach is not the same as trade expectancy.

## Lineage
Ancestors: Asian Range/Tier, Base80/P90P checkpoints, rekey ladder, failure/repair, event-distribution research.
Descendants/relations: EUR Weekly and Higher Order provide larger-layer context but must not overwrite Daily execution mechanics.

## Implementation
CEREBUS_Daily_News_Rekey_Engine_V1_1_P90_MERGED_FIX1.pine.
Implementation parity and displayed constants must be separated from empirical evidence.

## Operator interpretation
Use to answer: what intraday distribution remains, what structural nodes are active, and what has already been consumed?
Do not answer: guaranteed direction or guaranteed target.

## Ask CEREBUS
Beginner: The model measures the day's starting range, what price has already delivered, important events, and what movement is still statistically available.
Operator: Return tier, active path/rekey state, remaining distribution, clock, levels and invalidation/no-go context.
Researcher: Return exact calibration generation, sample, event identity and evidence links.
Forbidden: deterministic language; importing old P90 claims; treating target reach as executable WR.
