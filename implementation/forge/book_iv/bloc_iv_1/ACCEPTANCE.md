# BOOK IV / BLOC IV.1 — QUERY INTERPRETER & ROUTER — ACCEPTANCE.md

**Bloc:** IV.1 · **Rung:** BA-26 Rung 1 (planning)
**Status:** PROPOSED — binding only after implementation authorization
**Companion:** `PLAN.md`, `FEASIBILITY_GATE.md`, `DEPENDENCY_HANDOFF.md`

**Inventory: 53 requirements (R1–R53), 60 tests (A-01–A-60), 12 golden
fixtures (Q-01–Q-12).** Counts are authoritative and reconciled in §6.

Core law under test: the interpreter determines what the user is asking. It
never answers, approves, computes, retrieves or grants.

---

## 1. Requirement acceptance (R1–R53)

| ID | Acceptance condition | Tests |
|---|---|---|
| R1 | definition/explanation question yields `DEFINITION` | A-01 |
| R2 | model-description question yields `MODEL_DESCRIPTION` | A-02 |
| R3 | current-state question yields `CURRENT_STATE` | A-03 |
| R4 | level/coordinate question yields `LEVEL_COORDINATE` | A-04 |
| R5 | setup/operator question yields `SETUP_CONTEXT` | A-05 |
| R6 | statistic/evidence question yields `STATISTIC_EVIDENCE` | A-06 |
| R7 | comparison question yields `COMPARISON` | A-07 |
| R8 | historical-lineage question yields `HISTORICAL_LINEAGE` | A-08 |
| R9 | methodology/research question yields `METHODOLOGY_RESEARCH` | A-09 |
| R10 | indicator/vault question yields `INDICATOR_NAVIGATION` | A-10 |
| R11 | troubleshooting question yields `TROUBLESHOOTING` | A-11 |
| R12 | general market-knowledge question yields `GENERAL_MARKET_KNOWLEDGE` | A-12 |
| R13 | `EURUSD`/`Gold`/`BTC` resolve to canonical instrument ids | A-13 |
| R14 | model family resolves to a canonical model id or stays unresolved | A-14 |
| R15 | setup identity resolves to a canonical setup id or stays unresolved | A-15 |
| R16 | term/alias resolution is exact and source-backed; no fuzzy match | A-16 |
| R17 | L1/L2/L3 resolves to `Layer`; unknown layer stays `None` | A-17 |
| R18 | timeframe/session resolves to canonical vocabulary | A-18 |
| R19 | generation/version token is retained on the entity reference | A-19 |
| R20 | `BTC Game` never resolves to `BTC Tracker` | A-20 |
| R21 | `BEGINNER` depth classified | A-26 |
| R22 | `OPERATOR` depth classified | A-27 |
| R23 | `RESEARCHER` depth classified | A-28 |
| R24 | effective depth never exceeds injected maximum; no entitlement grant | A-29 |
| R25 | “today/now/current” yields `CURRENT` and requires live intelligence | A-30 |
| R26 | explicit timestamp yields `AS_OF` with the cutoff | A-31 |
| R27 | historical/backtest wording yields `HISTORICAL_RESEARCH` | A-32 |
| R28 | explicit model version yields `MODEL_VERSION` | A-33 |
| R29 | definition/doctrine yields `GENERAL` and no live requirement | A-34 |
| R30 | no historical substitution for current; no silent latest version | A-35 |
| R31 | entry/target/stop/position language sets `actionable` | A-36, A-37, A-40 |
| R32 | actionable requests set `requires_setup_context` | A-38 |
| R33 | no verdict, eligibility or approval is emitted | A-39 |
| R34 | rate/probability/N/correlation/expectancy language is detected | A-41, A-42 |
| R35 | research statistics set `requires_evidence` | A-43, A-45 |
| R36 | authorized deterministic current measurement is distinguished, not answered | A-44 |
| R37 | P90 references retain their generation identity | A-21 |
| R38 | Atomic/ST/Base80 and Wednesday/Afternoon retain generation | A-22 |
| R39 | earlier Markov/Fib references retain generation | A-23 |
| R40 | historical generation is never promoted to current by wording | A-25 |
| R41 | one unambiguous reading yields `RESOLVED` | A-46 |
| R42 | disambiguated scope yields `RESOLVED_WITH_EXPLICIT_SCOPE` | A-47 |
| R43 | materially divergent readings yield `MATERIAL_AMBIGUITY` | A-48 |
| R44 | unknown identity yields `UNSUPPORTED_IDENTITY` | A-49 |
| R45 | unresolvable generation yields `UNAVAILABLE_GENERATION` | A-50 |
| R46 | candidates + structured reasons are preserved | A-51 |
| R47 | no numeric confidence and no silent substitution | A-51, A-57 |
| R48 | plan carries the frozen intent and `query_contract_version` | A-52 |
| R49 | resolved model/setup ids are separate from raw entities | A-53 |
| R50 | market/layer are carried, never invented | A-54 |
| R51 | time scope and depths are carried; plan is immutable | A-55, A-59 |
| R52 | live/evidence/lineage flags are consistent with scope and intent | A-56 |
| R53 | plan serialization is canonical; upstream source untouched | A-58, A-60 |

---

## 2. Test inventory (A-01–A-60)

All tests are offline, deterministic and use no LLM/provider/network.

### T1 — Intent taxonomy (12)

| ID | Name | Expected |
|---|---|---|
| A-01 | `test_intent_definition` | `DEFINITION` |
| A-02 | `test_intent_model_description` | `MODEL_DESCRIPTION` |
| A-03 | `test_intent_current_state` | `CURRENT_STATE` |
| A-04 | `test_intent_level_coordinate` | `LEVEL_COORDINATE` |
| A-05 | `test_intent_setup_context` | `SETUP_CONTEXT` |
| A-06 | `test_intent_statistic_evidence` | `STATISTIC_EVIDENCE` |
| A-07 | `test_intent_comparison` | `COMPARISON` |
| A-08 | `test_intent_historical_lineage` | `HISTORICAL_LINEAGE` |
| A-09 | `test_intent_methodology_research` | `METHODOLOGY_RESEARCH` |
| A-10 | `test_intent_indicator_navigation` | `INDICATOR_NAVIGATION` |
| A-11 | `test_intent_troubleshooting` | `TROUBLESHOOTING` |
| A-12 | `test_intent_general_market_knowledge` | `GENERAL_MARKET_KNOWLEDGE` |

### T2 — Entity identity (8)

| ID | Name | Expected |
|---|---|---|
| A-13 | `test_instrument_resolution` | canonical instrument ids |
| A-14 | `test_model_resolution` | canonical model id or unresolved |
| A-15 | `test_setup_resolution` | canonical setup id or unresolved |
| A-16 | `test_alias_resolution_is_exact` | exact alias only; near-miss unresolved |
| A-17 | `test_layer_resolution` | L1/L2/L3 or `None` |
| A-18 | `test_session_timeframe_resolution` | canonical M5/H1/D1 and session ids |
| A-19 | `test_generation_token_retained` | generation preserved |
| A-20 | `test_btc_game_not_tracker` | collision blocked |

### T3 — Historical collisions (5)

| ID | Name | Expected |
|---|---|---|
| A-21 | `test_p90_generation_preserved` | P90 lineage, not current |
| A-22 | `test_st_and_base80_generation` | generation retained; ST manual |
| A-23 | `test_old_markov_and_fib_generation` | old generations retained |
| A-24 | `test_historical_not_current` | historical scope, no live flag |
| A-25 | `test_generations_stay_distinct` | no promotion across generations |

### T4 — Depth (4)

| ID | Name | Expected |
|---|---|---|
| A-26 | `test_depth_beginner` | `BEGINNER` |
| A-27 | `test_depth_operator` | `OPERATOR` |
| A-28 | `test_depth_researcher` | `RESEARCHER` |
| A-29 | `test_depth_capped_by_entitlement` | effective ≤ maximum; no grant |

### T5 — Temporal routing (6)

| ID | Name | Expected |
|---|---|---|
| A-30 | `test_current_requires_book_iii` | `CURRENT`, live flag true |
| A-31 | `test_as_of_pins_cutoff` | `AS_OF` + cutoff |
| A-32 | `test_historical_research_scope` | `HISTORICAL_RESEARCH`, lineage flag |
| A-33 | `test_model_version_scope` | `MODEL_VERSION` + pinned version |
| A-34 | `test_general_scope_no_live` | `GENERAL`, live flag false |
| A-35 | `test_unavailable_not_substituted` | no corpus substitution, no latest fallback |

### T6 — Actionability (5)

| ID | Name | Expected |
|---|---|---|
| A-36 | `test_entry_question_actionable` | actionable true |
| A-37 | `test_target_stop_question_actionable` | actionable true |
| A-38 | `test_actionable_requires_setup_context` | setup flag true |
| A-39 | `test_no_action_approval` | no verdict/eligibility field |
| A-40 | `test_position_question_actionable` | actionable true |

### T7 — Numerical evidence (5)

| ID | Name | Expected |
|---|---|---|
| A-41 | `test_rate_probability_detected` | evidence flag true |
| A-42 | `test_sample_and_correlation_detected` | evidence flag true |
| A-43 | `test_evidence_flag_set_for_history_stats` | evidence flag true |
| A-44 | `test_deterministic_measurement_exception` | flagged, not answered |
| A-45 | `test_unsupported_statistic_not_invented` | no numeric payload |

### T8 — Ambiguity (6)

| ID | Name | Expected |
|---|---|---|
| A-46 | `test_ambiguity_resolved` | `RESOLVED` |
| A-47 | `test_ambiguity_resolved_with_scope` | `EXPLICIT_SCOPE` |
| A-48 | `test_material_ambiguity` | `MATERIAL_AMBIGUITY` |
| A-49 | `test_unsupported_identity` | `UNSUPPORTED_IDENTITY` |
| A-50 | `test_unavailable_generation` | `UNAVAILABLE_GENERATION` |
| A-51 | `test_candidates_and_no_confidence_number` | candidates kept, enum confidence |

### T9 — III.6 handoff (4)

| ID | Name | Expected |
|---|---|---|
| A-52 | `test_plan_maps_to_snapshot_request` | all III.6 key fields supplied |
| A-53 | `test_model_and_setup_ids_are_separate` | separate id tuples |
| A-54 | `test_layer_and_market_mapping` | Layer/identity compatible |
| A-55 | `test_requirement_flags_match_scope` | live/evidence/lineage consistent |

### T10 — Security and policy (3)

| ID | Name | Expected |
|---|---|---|
| A-56 | `test_no_entitlement_laundering` | max depth comes from context only |
| A-57 | `test_no_identity_substitution` | alias cannot swap instrument/model |
| A-58 | `test_no_authoritative_fields_injected` | no verdict/exposure/statistic field |

### T11 — Determinism (1)

| ID | Name | Expected |
|---|---|---|
| A-59 | `test_plan_is_deterministic` | identical input ⇒ identical `plan_id` and JSON |

### T12 — Frozen integrity (1)

| ID | Name | Expected |
|---|---|---|
| A-60 | `test_upstream_sources_untouched` | no Book I/II/III source or test change |

---

## 3. Golden question fixtures (Q-01–Q-12)

| ID | Question | Intent | Identity | Depth | Scope | Evidence | Actionable | Outcome |
|---|---|---|---|---|---|---|---|---|
| Q-01 | “What is rekey?” | DEFINITION | TERM/Rekey | BEGINNER | GENERAL | no | no | RESOLVED_WITH_SCOPE |
| Q-02 | “What does the Gold Game mean?” | MODEL_DESCRIPTION | XAU Game family | BEGINNER | GENERAL | no | no | RESOLVED |
| Q-03 | “What's EURUSD doing today?” | CURRENT_STATE | EURUSD | OPERATOR | CURRENT | no | no | RESOLVED |
| Q-04 | “What's the current Gold setup?” | SETUP_CONTEXT | XAUUSD + XAU setup | OPERATOR | CURRENT | no | no | RESOLVED / UNAVAILABLE downstream |
| Q-05 | “Is BTC Game the same as BTC Tracker?” | COMPARISON | BTC Game vs BTC Tracker | OPERATOR | GENERAL | no | no | RESOLVED (distinct) |
| Q-06 | “What's the 132% target win rate?” | STATISTIC_EVIDENCE | XAU/Fib target, unresolved stat | RESEARCHER | GENERAL | yes | no | UNSUPPORTED_STATISTIC |
| Q-07 | “Show the original P90 model.” | HISTORICAL_LINEAGE | P90 generation | RESEARCHER | HISTORICAL_RESEARCH | yes | no | RESOLVED_WITH_SCOPE |
| Q-08 | “What was the EUR weekly state last Wednesday?” | HISTORICAL_LINEAGE | EUR Weekly + AS_OF | OPERATOR | AS_OF | no | no | RESOLVED |
| Q-09 | “Should I enter Gold now?” | SETUP_CONTEXT | XAUUSD | OPERATOR | CURRENT | no | yes | RESOLVED (no approval) |
| Q-10 | “Explain JPY carry confirmation.” | METHODOLOGY_RESEARCH | JPY Carry, USDJPY/AUDJPY/EURJPY roles | BEGINNER | GENERAL | no | no | RESOLVED |
| Q-11 | “Give me the historical ST automation results.” | STATISTIC_EVIDENCE | ST, historical | RESEARCHER | HISTORICAL_RESEARCH | yes | no | RESOLVED_WITH_SCOPE (manual doctrine noted) |
| Q-12 | “Show the Fib R15 production anchor.” | LEVEL_COORDINATE | Fib/Range Birth | OPERATOR | CURRENT | no | no | MATERIAL_AMBIGUITY / production gated |

Fixtures assert interpretation only. They do not assert that any market claim
is true and are not evidence of external parity.

---

## 4. Clause-to-test mapping rules

- Every R1–R53 has at least one named test.
- Every A-01–A-60 maps to at least one requirement.
- Seven tests are adversarial/negative cases in addition to their base
  requirement: A-16, A-20, A-25, A-29, A-35, A-51, A-57.
- No test asserts a market outcome, a probability, an eligibility verdict or a
  provider response.

---

## 5. Gate semantics

- **PASS:** 60/60 green; 53/53 requirements covered; no skipped/xfailed; style
  and imports respect the no-LLM/no-network boundary; frozen sources and
  50/50 Book II pins untouched; CI green.
- **PARTIAL:** tests green but a downstream dependency is unavailable for
  execution (see `FEASIBILITY_GATE.md`); this cannot authorize IV.2.
- **FAIL:** unknown intent, invented identity, promoted generation, numeric
  confidence, entitlement grant, or any upstream source edit.

---

## 6. Count reconciliation

| Group | Tests | Requirements |
|---|---|---|
| T1 | 12 | R1–R12 |
| T2 | 8 | R13–R20 |
| T3 | 5 | R37–R40, R30 |
| T4 | 4 | R21–R24 |
| T5 | 6 | R25–R30 |
| T6 | 5 | R31–R33 |
| T7 | 5 | R34–R36 |
| T8 | 6 | R41–R47 |
| T9 | 4 | R48–R52 |
| T10 | 3 | R24, R33, R47 |
| T11 | 1 | R51 |
| T12 | 1 | R53 |
| **Total** | **60** | **53/53 covered** |

---

## 7. Stop conditions

Stop and report if a test requires an LLM, a live provider, a fabricated
canonical id, a new intent outside the frozen taxonomy, an entitlement
decision, or a change to Book I/II/III source or acceptance tests.
