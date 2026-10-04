# SETUP CARD — XAU Quarter-Zone Operator V1

setup_id: SETUP.XAU.QUARTER_ZONE.V1
status: CANONICALIZATION_CANDIDATE
market_scope: XAUUSD
execution_class: MANUAL_OPERATOR
parent_model_ids: XAU.GAME.L1_L2_L3.V1
product_exposure: OPERATOR_ONLY

## Purpose
Express the active Gold distribution through an asymmetric quarter-zone entry only after location and local confirmation agree with the active model state.

## Eligibility
After03:00 NY.
Active Asian range and local direction established.
Relevant quarter zone active.
L2/L3 context must not be in explicit no-go/stand-down state.

## Entry lineage
Bearish Asian/local expression: seek sell excursion into quarter +10 to +15 zone.
Bullish: seek buy excursion into quarter -10 to -15 zone.
Do not enter merely because price is already beyond the level.
Require excursion into the zone and push/rejection back;5-minute close outside the zone or valid S/R flip may serve as confirmation according to operator generation.

## Ladder lineage
Historical operator ladder:
first entry around +/-10 location; second/deeper entry around +/-15 /80-style step depending active quarter mapping.
Per-step risk/invalidation must be rendered from the active implementation, not inferred from shorthand.

## Targets
Primary doctrine: next quarter / approximately25-point distribution, or next quarter discount/premium zone with source tolerance.
Smaller $5/$10 moves are confirmation/evidence states, not the core target doctrine.

## Invalidation
Local ladder historically used approximately5-point step invalidation.
80 family also appears as structural invalidation coordinate.
Exact active invalidation must come from current setup implementation.

## No-go
No blind touch entry.
No entry solely from L3 destination.
No automatic132->168 promotion.
No tiny scalp optimization presented as the primary Game doctrine.

## Evidence
State-promotion evidence belongs to L2 and does not equal this setup's WR:
EV.XAU.PROMOTION.68_80.V1
EV.XAU.PROMOTION.120_132.V1.

## Ask CEREBUS
Beginner: wait for Gold to enter the correct quarter zone and prove rejection in the direction of the active distribution.
Operator: return active quarter, side, zone, confirmation, invalidation, target and higher-layer conflicts.
Forbidden: "touch quarter +10 = sell"; quoting path completion rates as setup WR.
