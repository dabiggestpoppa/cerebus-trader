# CEREBUS EURUSD ILM Retest — Daily + Weekly

## Test definition
Price data: EURUSD M5, Nov 2022–Sep 2026.
Research clock: fixed server→NY -7h.
Daily candle: 17:00 NY → 17:00 NY.
Weekly candle: Monday-Friday trading week.

For a bullish prior candle:
- 50 = H - .50R
- 61.8 = H - .618R
- 72 = H - .72R
- 80 = H - .80R
- directional -25 = H + .25R
- directional -50 = H + .50R

Bearish is mirrored.

Entry test: first touch of 50 / 61.8 / 72 on the following period.
Stop: prior candle 80.
Targets: prior-direction -25 and -50.

## Main findings
1. Previous-day 50–61.8 ILM is a strong next-day touch zone:
   - all days D+1: 71.08%
   - Monday→Tuesday: 74.11%
   - 2026 OOS slice: 73.14%

2. But "enter 50–72, stop at 80, target prior -25" is not supported as a standalone mechanical trade.
   - 50 entry: 27.66% target-before-stop among resolved trades.
   - 61.8 entry: 15.93%.
   - 72 entry: 6.65%.
   The 80 stop is too tight for this unconditional continuation idea.

3. Prior-direction target reach WITHOUT requiring the pullback trade:
   - -25 next day: 43.27%
   - -50 next day: 26.20%
   - Monday -25 by Tuesday: 45.69%
   - Monday -50 by Tuesday: 26.40%

4. Unfilled ILM does not become a stronger magnet with age.
   Daily cumulative touch: 70.94% D+1, 79.41% by D+2, 83.96% by D+3, 86.98% by D+5.
   But conditional hazard decays sharply: 70.94% → 29.17% → 22.06% → 13.21% → 6.52%.
   Interpretation: ILM is strongest when fresh. A missed old ILM can persist as an open reference, but the data does not support "older = stronger magnet."

5. Close beyond prior 80 is a meaningful state change.
   There were 203 daily adverse closes beyond the prior-day 80 level.
   On the following day:
   - opposite-side 25% extension from the original range hit: 70.44%
   - old ILM zone retouched: 47.29%
   - original-direction -25 hit: 11.33%
   - closing direction itself continued only 50.25%
   So the useful information is structural reach, not simply next-candle color.

6. Weekly version behaves similarly:
   - prior-week 50–61.8 zone touched next week: 68.37%
   - by 2 weeks: 77.04%
   - by 4 weeks: 82.65%
   - conditional weekly hazard decays 68.37% → 27.42% → 17.78% → 8.11%.
   Weekly 50/61.8 therefore behaves as a fresh structural attractor, not an ever-strengthening magnet.

7. Weekly 80-close state shift:
   41 cases.
   Following week:
   - opposite 25% extension: 58.54%
   - old weekly ILM retouch: 34.15%
   - original -25: 7.32%.

## Practical state-machine interpretation
Fresh ILM:
prior candle closes → 50–61.8 zone has elevated next-period attraction.

If ILM is touched:
do not assume a blind continuation from 50–72 with an 80 stop. Require another confirmation layer.

If price closes through 80 against the prior candle:
treat the old directional thesis as structurally damaged. The next-period distribution strongly shifts toward the opposite 25% extension.

If ILM remains untouched:
keep it as a reference node, but decay its priority with age rather than increasing it.

This retest does not validate the very high historical workbook claims as direct trading win rates; several appear to refer to broader pattern/weekly delivery definitions rather than this exact entry/stop/target specification.