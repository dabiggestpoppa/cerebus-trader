# CEREBUS DATA INTERPRETATION & USER UNDERSTANDING DOCTRINE

**Book:** I — Corpus  
**Status:** Recovery record / explanatory doctrine  
**Purpose:** Preserve not only datasets and outputs, but what the data was understood to mean while the research was being developed.

## 1. Data is not the model

A CSV, price series, hit-rate table, or backtest is evidence. CEREBUS is the interpretation layer built from reproducible relationships in that evidence.

FORGE must preserve four separate objects:

1. **Observation** — what price/data actually did.
2. **Measurement** — how the observation was transformed: range, excursion, tier, time slot, fib coordinate, etc.
3. **Inference** — the statistical relationship found in those measurements.
4. **Operator doctrine** — what action, if any, the inference justifies.

Persuasive prose is not a signal. Every promoted interpretation must ultimately be traceable to evidence.

## 2. CEREBUS is a distribution engine, not a prediction oracle

The central question is not simply “up or down?”

The system repeatedly asks:

- What distribution was printed?
- How large is it relative to comparable states?
- Where are we inside that distribution?
- How much range is statistically left?
- Which side has already delivered?
- Which side remains unresolved?
- What state transition would invalidate or promote the current path?

Probabilities describe empirical behavior, not guarantees.

## 3. The three-layer grammar

The durable cross-model doctrine is:

> **L3 defines destination. L2 defines path. L1 defines entry.**

Higher-timeframe information should not be collapsed into one opaque confluence score merely because multiple layers agree.

- **L3 / macro / quarter-month:** destination, regime, larger distribution.
- **L2 / weekly:** path, timing state, range-left, weekly location and exhaustion.
- **L1 / daily/intraday:** execution feasibility, entry geometry, rekey, confirmation and invalidation.

Agreement raises confidence in a path hypothesis; it does not create truth.

## 4. Timeframes are nested sampling windows

Daily, weekly, monthly and quarterly structures are not separate universes. They are different sampling scales of the same price process.

FORGE should teach users to distinguish:

- **scale** — how much market history a state represents;
- **clock** — when the measurement begins/locks;
- **geometry** — where price sits relative to the measured range;
- **state** — the currently observed configuration;
- **transition** — movement from one state to another.

This is why a daily entry can express a weekly or quarterly thesis without forcing the daily model to become the quarterly model.

## 5. Range normalization is the translation layer

Many CEREBUS models normalize price behavior relative to a seed range.

A raw move of 20 pips, $20, or 100 index points is not inherently comparable. A move expressed as a fraction/multiple of the active range can be.

This enables structural concepts such as:

- 50–72 / 50–80 retracement areas;
- 80 invalidation;
- 100 boundary;
- 120 / 125 / 132 rekey states;
- 168 / 185 deeper states;
- -25 / -50 / -85 extensions;
- range-left and completion ratios.

The numbers are coordinates inside a measured distribution, not mystical constants.

## 6. Rekey concept

A **rekey** is a structural remapping event: price retraces deeply enough relative to the active range that the original distribution can no longer be interpreted using only its initial directional geometry.

The research therefore treats rekey levels as state-transition candidates, not automatic reversal buttons.

Different studies test:

- probability of reaching a rekey;
- depth after reaching it;
- acceptance versus rejection;
- time spent beyond a level;
- first-delivery ordering;
- whether deeper nodes become promoted targets;
- whether a rekey restores, reverses, or merely delays the prior path.

## 7. Range-left is more useful than static target worship

A target level matters differently when a distribution has 80% of its expected range left than when it is statistically exhausted.

The Hour×Tier work formalizes this with:

- printed range;
- comparable-state median;
- MAD / robust sigma;
- remaining-range Q50/Q75/Q90;
- probability of another extreme;
- location inside the weekly range;
- pace state: Behind / Normal / Ahead / Extreme Ahead.

This is an example of CEREBUS moving from static levels toward conditional state intelligence.

## 8. Tiering is compression of continuous behavior

Tiers are not claims that markets naturally exist in exactly three boxes. They are operational partitions that compress a continuous distribution into usable states.

A tier definition must therefore retain:

- instrument;
- source window;
- sample period;
- unit;
- thresholds;
- sample count;
- calibration method;
- outlier/no-go rule;
- version.

A BTC dollar tier cannot be copied numerically to EURUSD pips or XAU points. What transfers is the architecture, not necessarily the calibration.

## 9. First delivery and path dependence

Two sessions can reach the same final high and low while offering completely different trades.

Therefore CEREBUS research frequently records **which boundary delivered first**, when it delivered, and what happened before/after the hit.

First-delivery ordering matters for:

- expectancy;
- invalidation;
- whether a pullback was tradable;
- whether a target was available before adverse excursion;
- distinguishing continuation from recovery.

A raw “eventually hit” statistic is insufficient for execution claims.

## 10. Path state versus terminal outcome

FORGE must preserve the distinction between:

- **terminal outcome:** where a day/week/month/quarter ultimately finished;
- **path state:** the route taken to get there.

A model can be useful even when it does not predict the terminal direction if it reliably describes range-left, first delivery, exhaustion, rekey probability, or the order of likely transitions.

## 11. Confirmation and acceptance

A wick through a level is not equivalent to acceptance.

Research uses concepts such as closes, time beyond a node, M5/H1 confirmation, OCC, and duration thresholds to distinguish:

- touch;
- excursion;
- rejection;
- acceptance;
- promotion.

This prevents a geometric level from being treated as a deterministic signal merely because price printed through it.

## 12. Noise is timeframe-dependent

The afternoon-filter work is an example: lower-timeframe closes outside a band can contain materially more fakeouts than higher-timeframe acceptance.

User-facing explanations should make clear that “price crossed the level” and “the market accepted a new state” are different propositions.

## 13. Clock discipline is part of the data

Session definitions are model inputs, not presentation preferences.

Examples in the corpus include Asian windows, DT windows, Monday ranges, London ranges, 12 PM checkpoints, first-three-trading-day seeds, and month/quarter locks.

Changing the timezone, DST treatment, day ownership, final bar, or session boundary can change the research result.

Every study therefore needs a clock specification alongside its price specification.

## 14. Cross-asset transfer

CEREBUS searches for **structural invariants** and then recalibrates them per market.

Possible transferable structures:

- seed range → retracement → extension;
- tier → expected range;
- location × pace → range-left;
- rekey → acceptance → delivery;
- higher-order destination → lower-order path → execution.

Non-transferable until tested:

- exact tier thresholds;
- exact fib hit rates;
- exact time windows;
- exact target distances;
- exact news response;
- exact volatility assumptions.

## 15. Correlation does not erase expression

The crypto multi-market work treats correlated assets as potentially different expressions of a thesis because volatility, path and excursion can differ even when direction is related.

FORGE should therefore distinguish:

- directional dependence;
- volatility dependence;
- path dependence;
- true diversification.

Several correlated trades are not automatically independent bets.

## 16. News as a distribution perturbation

The Daily News + Rekey research treats news not as a narrative explanation but as a measurable perturbation to the active distribution.

Useful concepts include:

- event family;
- historical event-size distribution;
- Q50/Q75/Q90 response;
- tolerance band;
- decay;
- residue;
- normalization;
- post-event rekey.

The aim is to map how a known event class modifies expected surface area and path, not to predict headlines.

## 17. Negative evidence is first-class data

A setup that looked compelling but failed ablation is valuable.

FORGE must preserve:

- parked setups;
- small-N flags;
- failed promotions;
- regime-specific failures;
- versions superseded by stronger evidence;
- hypotheses that were descriptive but not executable.

This prevents future users—or future CEREBUS—from rediscovering and re-promoting discarded ideas without knowing their history.

## 18. Small-N/high-R findings

Rare high-R observations may be strategically interesting without being statistically mature.

They should be labeled as:

- research flag;
- candidate;
- small-N;
- non-promoted;

until sample size, stability, and out-of-sample behavior justify promotion.

The system should show N beside unusually strong percentages.

## 19. Data lineage required for user trust

Every important statistic should eventually expose a lineage chain:

`source data → session/clock → transformation → sample → test → result → model version → user-facing claim`

This allows a user to ask not only “What does CEREBUS say?” but also:

- Why?
- Based on what?
- Over which period?
- How many observations?
- Under which market state?
- Is this validated or experimental?
- What would falsify it?

## 20. User-facing vocabulary classes

FORGE should tag claims so the interface can communicate epistemic status without forcing users to read research papers:

- **OBSERVED** — direct measurement.
- **VALIDATED** — passed defined validation/OOS criteria.
- **CANDIDATE** — promising but not promoted.
- **RESEARCH FLAG** — notable, often small-N.
- **DESCRIPTIVE** — useful context, not an execution edge.
- **PARKED** — failed or insufficient.
- **SUPERSEDED** — historically important but replaced.
- **NO-GO** — outside calibrated operating domain.

## 21. Product implication

Ask CEREBUS should eventually be able to answer at three depths from the same lineage:

1. **Beginner:** what the state means.
2. **Operator:** levels, path, invalidation, range-left, setup state.
3. **Researcher:** exact sample, methodology, evidence, limitations, version and provenance.

The product should simplify the explanation—not erase the evidence.

## 22. Core mental model

CEREBUS is best understood as a hierarchy of conditional distributions and state transitions.

It does not need to know the future with certainty.

It needs to continuously answer:

> **Given what has already printed, what state are we in, what remains statistically available, which transition is being accepted, and what evidence would make us change the map?**
