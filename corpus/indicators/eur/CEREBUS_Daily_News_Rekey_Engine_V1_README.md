# CEREBUS Daily News + Rekey Engine V1

## Install
1. Open TradingView Pine Editor.
2. Paste the contents of `CEREBUS_Daily_News_Rekey_Engine_V1.pine`.
3. Save and Add to chart.
4. Use EURUSD on M5 for the research-matched configuration.

## What it contains
- Forex Factory EUR/USD medium + high impact feed through the toodegrees Pine Seeds framework.
- Official-Euro-area filter for the CEREBUS model layer.
- Asian Range 19:00-03:00 New York.
- EURUSD tiers: T1 <20p, T2 20-30p, T3 30-45p, >45p NO_GO.
- State ladder: 100 / 125 / 132 / 168 / 185.
- Directional 50% extension and opposite-rekey downgrade state.
- Live distance-asymmetry directional confidence.
- M5-derived daily remaining-range Q50/Q75/Q90 surface from 03:00-12:00.
- Event-family 15/30/60/120m Q25/Q50/Q75/Q90 movement bands.
- Two-clock active / residue / exhausted news state.
- Remaining event-budget reach zone for the next structural state.
- Optional Forex Factory event markers/table and news-candle high/low tracking.
- Alerts for modeled releases, 125 activation, 132 confirmation, and strong live asymmetry.

## Model doctrine
Geometry supplies branch direction. Distribution supplies reach. News reweights kinetic feasibility. Time decays the event field.

## Important
The indicator uses pinned public library versions from the supplied reference architecture. If TradingView later deprecates those versions, update the two import version numbers together with the corresponding decoder/utility pair.