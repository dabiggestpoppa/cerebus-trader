# IV.3 FIXTURE PROVENANCE

**Contract:** `CONTEXT_CONTRACT_V1`
**Base HEAD:** `0d64fa8cf6d1c568dae6d7110281d38b5587705a`

These twenty fixtures are synthetic structural inputs. They do not assert live
prices, current provider availability, empirical performance or commercial
entitlement.

| ID | Purpose | Synthetic input | Expected boundary |
|---|---|---|---|
| Q3-01 | Rekey definition | FIB term, model and lineage | Canonical facts only; no answer |
| Q3-02 | Beginner Gold Game | Canonical model, claim/evidence without stats | Detail absent; no invented number |
| Q3-03 | Authorized EUR snapshot | Synthetic snapshot detail | Snapshot id/hash and synthetic quality |
| Q3-04 | Gold provider unavailable | Provider limitation only | No current values |
| Q3-05 | Unsupported 132% | Claim with no evidence | Missing-evidence control; no 132% |
| Q3-06 | Complete governed claim | Claim + evidence + stats detail | Metric/population/N/period retained |
| Q3-07 | Missing evidence | Model + unsupported claim | Known model retained; no statistic |
| Q3-08 | Small N=8 | Governed threshold ref | Actual N preserved, no invention |
| Q3-09 | Missing N | Stats detail with N absent | N not provided; threshold unresolved |
| Q3-10 | L3/L1 separation | L3 claim + L1 setup | Separate layers; no merged result |
| Q3-11 | XAU WATCH/no-go | Setup + active no-go | Mandatory no-go and not-eligible |
| Q3-12 | Fib research-only | Research setup | No production surface |
| Q3-13 | JPY manual | Manual setup | No execution or automation grant |
| Q3-14 | BTC Game/Tracker | Two model/claim identities | No merged statistic |
| Q3-15 | Historical P90 | Historical claim/lineage | No current substitution |
| Q3-16 | Evidence conflict | Two opposing claims/evidence | Both sides retained |
| Q3-17 | Negative research | Falsified claim/negative ref | Negative remains visible |
| Q3-18 | Malicious text | Instruction-like semantic passage | Hashed untrusted data only |
| Q3-19 | Denied internal method | Forbidden exposure source | Refusal; no identifier |
| Q3-20 | Mandatory overflow | Query + no-go with tiny budget | Bounded refusal; no narrative |

Regenerate with:

```bash
python implementation/forge/book_iv/bloc_iv_3/fixtures/generate.py
```

`FIXTURE_MANIFEST.json` records the LF-normalized SHA-256 and byte count of each
expected package. Test `C-86` separately proves identical-input retry identity.
