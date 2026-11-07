# BOOK III — III.1 PROVIDER COMPATIBILITY AMENDMENT — FEASIBILITY GATE

**Packet:** BA-25 Rung 1 · **Status:** GATE OPEN (implementation not authorized)
**Question:** for each requirement, can the existing interface or the adapter
satisfy it, or is a frozen change or operator decision genuinely required?

---

## 1. Classes

| Class | Definition | Evidence required |
|---|---|---|
| **F1** | existing interface already supports it | current code + existing behavior |
| **F2** | additive adapter implementation is sufficient | adapter-only design, no frozen edit |
| **F3** | frozen III.1 modification genuinely required | why F1/F2 fail, exact diff, hash impact |
| **F4** | missing canonical source or operator decision | named owner + closure artifact |

No requirement is classified F3 without a demonstrated F1/F2 failure.

---

## 2. Classification (R1–R24)

| ID | Requirement | Class | Why this class | Owner / closure |
|---|---|---|---|---|
| R1 | Provider identity per bar | F1 | `Bar.provider` is required and already populated | — |
| R2 | Source symbol retained at adapter | F1 | `RawCandle.source_symbol`; `Bar` intentionally excludes it | — |
| R3 | Source timestamp preserved | F1 | `Bar.source_timestamp` is distinct and already set | — |
| R4 | Volume optional | F1 | `volume: Decimal \| None`; absence is not zero | — |
| R5 | Unknown provider fails closed | F1 | `provider_schema` raises `UnsupportedProviderError` | — |
| R6 | Cutoff is sole finality authority | F1 | `assess_finality` / `finalize_for_cutoff` | — |
| R7 | Revision ordering by later timestamp | F1 | `reconcile` picks the later source timestamp, emits `REVISED` | — |
| R8 | Twelve Data `values` envelope | F2 | adapter can flatten before the kernel; no canonical semantics involved | adapter |
| R9 | Polygon `results` envelope | F2 | same; `status` refusal handled at adapter | adapter |
| R10 | Kraken array rows | F2 | adapter maps positions to names; no kernel rule changes | adapter |
| R11 | Request-context symbol/timeframe | F2 | values come from the declared request; adapter injects | adapter |
| R12 | Revision id extraction | F2 | `RawCandle.source_revision` already exists | adapter |
| R13 | Trailing provisional hint | F2 | `RawCandle.finality_hint` already exists; kernel cutoff still decides | adapter |
| R14 | Envelope provenance | F2 | `adapter_version`/`source_ref` live on the raw observation | adapter |
| R15 | JPY registry composition | F2 | public `Instrument`/`InstrumentRegistry` constructors + injection | composition root |
| R16 | Derived close time | **F3** | `close_time` is a literal required key; no derivation hook exists | III.1 amendment |
| R17 | Conditional required keys | **F3** | `required_keys` unconditionally includes close time and clock | III.1 amendment |
| R18 | Optional clock key | **F3** | `normalize_record` line 219 reads `payload[schema.clock]`; no "no clock claim" path | III.1 amendment |
| R19 | Epoch milliseconds | **F3** | `TimestampStyle` has only seconds and ISO; ms would be truncated or misread | III.1 amendment |
| R20 | Three schema entries | **F3** | `PROVIDER_SCHEMAS` is a closed module-level table; registration is the amendment | III.1 amendment |
| R21 | Production default registry promotion | **F4** | policy decision; injection already works, promotion is not | operator |
| R22 | JPY precision/pip/tick authority | **F4** | market convention, not corpus-backed; requires written confirmation | operator + source authority |
| R23 | Higher-timeframe rollup | **F4** | no canonical rollup/finalization rule exists | canonical research |
| R24 | Vendor licensing | **F4** | commercial terms; no technical fix | operator + vendor |

**Counts: F1 = 7, F2 = 8, F3 = 5, F4 = 4 (total 24).**

---

## 3. Why F1/F2 fail for each F3

### R16/R17 — derived close time

`normalize_record` checks `schema.required_keys` before reading anything, and
`ProviderFieldMap` has a literal `close_time` string. All three vendors omit a
close column. Deriving in the adapter and writing a synthetic `close_time` key
would work mechanically, but it would fabricate a **source field**: the record
would claim the vendor supplied a close time it did not. The kernel is the
right place to declare "this interval boundary is derived", and it already owns
`TIMEFRAME_MINUTES`.

### R18 — optional clock

The kernel converts `payload[schema.clock]` to a string and calls
`instrument.supports_clock`. None of the three vendors emits a clock id. The
adapter could inject `America/New_York`, but that would assert a vendor clock
claim that does not exist — exactly the remap G4 forbids. The honest model is
"the row carries no clock claim", which the field map cannot express today.

### R19 — epoch milliseconds

`_parse_timestamp` has two branches. A millisecond value under
`EPOCH_SECONDS` becomes a year-~58000 timestamp (or raises `OverflowError`,
which is caught and refused), and `ISO_OFFSET` would stringify it. Converting
ms to ISO in the adapter would erase the native unit and defeat the unit-mixup
test. A bounded enum member with explicit conversion is the minimal honest fix.

### R20 — schema registration

`PROVIDER_SCHEMAS` is the only registry `provider_schema` consults. There is no
public registration function, no entry-point hook, and no request-level schema
override. The adapter cannot make `normalize_feed(records, "twelvedata", ...)`
work without an entry. This is a genuine table extension, not a convenience.

---

## 4. Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Adapter writes derived `close_time` into each record | fabricates a source field; hides derivation |
| Adapter injects a platform clock id | invents a provider clock claim; violates G4 |
| Adapter rewrites ms to ISO before the kernel | erases the unit; prevents A-09 |
| Adapter keeps using `canonical.py` forever and never registers schemas | leaves `normalize_feed`/`replay_historical`/`stream_live` unable to accept real providers; WP-3B stays PARTIAL by construction |
| Extend `instruments.py` for JPY now | unnecessary; injection already works and promotion needs authority |
| Add a rollup rule to unblock | no canonical source; would invent semantics |

---

## 5. F4 owners and closure evidence

| ID | Owner | Closure artifact |
|---|---|---|
| R21 | Operator | signed registry-promotion decision |
| R22 | Operator + canonical source | convention confirmation (precision/pip/tick) |
| R23 | Canonical research owner | approved rollup/finalization rule |
| R24 | Operator + vendor | recorded licence/redistribution terms |

Until these exist, the related tests assert the **governed unavailable**
behavior (A-40 provisional, A-41 unchanged, A-23 refusal, A-49 licence gate),
not a fabricated success.

---

## 6. Gate decision

- F3 count is **5**, all inside `normalize.py` plus the package export.
- No F3 requirement touches `bars.py`, `quality.py`, `instruments.py`,
  sessions, clocks or research day.
- The amendment is therefore **minimal and backward-compatible by design**.

**Gate verdict: OPEN — design feasible, implementation not authorized.**
Closure requires `CHANGE_CONTROL.md` decisions 1–2 and the release sequence in
`PLAN.md` §11.
