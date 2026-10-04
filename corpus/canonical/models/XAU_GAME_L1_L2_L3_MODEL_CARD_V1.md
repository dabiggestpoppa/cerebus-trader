# MODEL CARD — XAU Game L1-L2-L3 V1

model_id: XAU.GAME.L1_L2_L3.V1
status: CANONICAL_FROZEN_FAMILY
market_scope: XAUUSD
layer: CROSS_LAYER
model_type: DESTINATION + PATH + EXECUTION_SUPPORT
product_exposure: SUBSCRIBER_MODEL

## Purpose
Route Gold decisions through explicit layer ownership instead of treating every level as an entry signal.

## Architecture
L3 DESTINATION: higher-order distribution / weekly-quarter destination.
L2 PATH: route/state between local seed and destination.
L1 EXECUTION: daily/local entry location, invalidation and confirmation.

## Modern operator doctrine
Primary target doctrine is next quarter / approximately25-point distribution, commonly expressed as next quarter discount/premium zone with tolerance, rather than optimizing for tiny $5 scalps.
Desired convexity historically targeted roughly1:3-1:10 depending setup; this is design doctrine, not a guaranteed return.

## Key coordinates
Quarter zones; -50 decision node;132 rekey;80 invalidation family;50-72 Asian-range entry family.
Coordinates require an earned/active range and state.

## Entry lineage
After3AM.
Asian direction supplies local bias.
Bearish local expression: sell excursion into quarter +10/+15 zone.
Bullish: buy excursion into quarter -10/-15.
Touch alone is insufficient; wait for excursion/rejection/close/flip according to setup generation.
Exact ladder/SL rules are operator setup rules and must live in Setup Cards rather than be inferred from this model card.

## Scientific state lineage
Recovered scientific XAU work includes D1-D3 seed, weekly sample238, spatial bands:
25-50 normal
50-68 failure
68+ repair
100-110 snap.
Promoted historical examples include 68+8h->80 and120+8h->132 with high conditional completion in their source samples. Exact N/results belong in Evidence Cards.

## Evidence safety
A destination-state completion rate is not a trade WR.
A quarter level is not automatically an entry.
Do not combine older Gold Game and WMA/ATR research without a lineage decision.

## Implementation
CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine
CEREBUS_XAU_FINAL_MODEL_FREEZE_V1.md.
Implementation is operator interface; scientific evidence remains separate.

## Ask CEREBUS
Beginner: Gold Game separates where price may ultimately travel from how it gets there and where an asymmetric entry can exist.
Operator: Return L3 destination, L2 path, L1 location/confirmation/invalidation and active quarter/rekey nodes.
Researcher: Return state definitions, sample, promoted/frozen status and evidence.
Forbidden: level=signal; completion rate=trade WR; importing EUR/BTC calibration.
