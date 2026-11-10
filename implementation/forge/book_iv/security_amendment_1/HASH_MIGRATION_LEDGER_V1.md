# Hash canonicalization — migration ledger V1

Every constant below is **unchanged**. Under the approved policy each
frozen digest equals the SHA-256 of the canonical (CRLF→LF) content, which
equals the SHA-256 of the committed blob for every governed file. The defect
was in the *measurement*, not in the recorded identity, so no baseline was
re-derived and no integrity guarantee was loosened.

| Field | Value |
|---|---|
| Policy | `CANONICAL_TEXT_V1` (`tests/_support/canonical_bytes.py`) |
| Old algorithm | `hashlib.sha256(path.read_bytes())` over working-tree bytes |
| New algorithm | `hashlib.sha256(canonical_bytes(path))`, CRLF→LF only |
| Lone CR | preserved (never normalized) |
| Constants changed | **none** (65/65 old == new) |
| Guarded files | 65 |
| Files where committed blob == canonical content | 65/65 |

## 1. The seventeen guards

| Test | Book | Guarded files | Old mechanism | New mechanism |
|---|---|---|---|---|
| `TestInternalMaterial::test_policy_module_is_untouched` | Book I | policy.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `TestScopeGuards::test_001_and_002_unchanged` | Book II | persistence/sql/001_initial_schema.sql | hashlib.sha256(wt.read_bytes()) | canonical_bytes(path) then sha256 |
| `TestT12Boundaries::test_cross_platform_hash_stability` | setup engine | bloc_iii_5 FIXTURE_MANIFEST 12 fixtures | hashlib.sha256(wt.read_bytes()) | canonical_sha256(fixture) |
| `TestT12Boundaries::test_frozen_upstream_hashes_unchanged` | setup engine | bloc_iii_5 FROZEN_BASELINE 49 files | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_a55_same_golden_suite_runs_against_candidate_provider` | IV.4 | 24 Q4 fixture files | raw read_bytes() vs LF-normalised build | canonical_bytes(fixture) vs build |
| `test_a70_frozen_iv3_context_contract_unchanged` | IV.4 | context/schema.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_a71_routes_migrations_and_provider_seams_unchanged` | IV.4 | service/routes.py + migration versions | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_a74_frozen_upstream_hashes_routes_and_migrations_unchanged` | IV.5 | 7 inline FROZEN | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_boundary_frozen_upstream_hashes_unchanged` | Book III | 4 upstream packages (aggregate over modules) | name + b'
' + read_bytes() | name + b'
' + canonical_bytes(path) |
| `test_c87_frozen_iv1_plan_contract_unchanged` | IV.3 | interpreter/plan.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_c88_frozen_iv2_bundle_refs_trace_unchanged` | IV.3 | retrieval/{bundle,refs,trace,service}.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_c89_frozen_book_i_ii_iii_contracts_unchanged` | IV.3 | policy.py, service/policy_enforcement.py, intelligence_api/contracts.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_c91_routes_migrations_and_provider_seam_unchanged` | IV.3 | service/routes.py + migration versions | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_hash_record_updated` | Book III WP-3B | market_data/normalize.py, __init__.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_only_authorized_frozen_files_changed` | Book III WP-3B | 11 market_data files + routes.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_routes_hash_unchanged` | provider integration | service/routes.py | hashlib.sha256(wt.read_bytes()) | canonical_sha256(path) |
| `test_wp3b_contract_suite_green` | Book III WP-3B | runs the integration module (inherits its guards) | subprocess pytest | subprocess pytest (now green) |

## 2. Constant reconciliation (65 governed files)

`raw` is the digest this CRLF checkout produced before the repair — the value
that failed the guards. `canonical` is the repaired measurement and `blob` is
the SHA-256 of the committed blob: they agree everywhere.

| Guarded file | Old constant | raw (CRLF checkout) | canonical | committed-blob sha256 | blob id |
|---|---|---|---|---|---|
| `app/forge/ask_cerebus/context/enums.py` | `9c614f178707` | `9c0a284e8218` | `9c614f178707` = | `c30d2c3929a4` | `c30d2c3929a4` |
| `app/forge/ask_cerebus/context/schema.py` | `499dbdfb0054` | `ced734ee366a` | `499dbdfb0054` = | `2700cbd89353` | `2700cbd89353` |
| `app/forge/ask_cerebus/context/versions.py` | `0beaa9b0d3d1` | `4b22cfd31b49` | `0beaa9b0d3d1` = | `1a85fab753e1` | `1a85fab753e1` |
| `app/forge/ask_cerebus/interpreter/plan.py` | `c43a34ba6ef0` | `13c919c8256d` | `c43a34ba6ef0` = | `f898665cb804` | `f898665cb804` |
| `app/forge/ask_cerebus/llm_gateway/draft.py` | `9aac55a78f78` | `7b1450899fb1` | `9aac55a78f78` = | `a7c70c61db07` | `a7c70c61db07` |
| `app/forge/ask_cerebus/llm_gateway/enums.py` | `52fb6475631f` | `31a7993907b6` | `52fb6475631f` = | `bafda994ed77` | `bafda994ed77` |
| `app/forge/ask_cerebus/llm_gateway/versions.py` | `01dac8b25417` | `4522aeb7d6c7` | `01dac8b25417` = | `24f46987adcc` | `24f46987adcc` |
| `app/forge/ask_cerebus/retrieval/bundle.py` | `b38b356e01b3` | `203b876d4763` | `b38b356e01b3` = | `7ed72505ea81` | `7ed72505ea81` |
| `app/forge/ask_cerebus/retrieval/refs.py` | `bbe1b937d6aa` | `845477d33f54` | `bbe1b937d6aa` = | `51c335aee67f` | `51c335aee67f` |
| `app/forge/ask_cerebus/retrieval/service.py` | `d4ef64f9d3f9` | `23089c91e765` | `d4ef64f9d3f9` = | `1b69cd5e578f` | `1b69cd5e578f` |
| `app/forge/ask_cerebus/retrieval/trace.py` | `6f8f08009da6` | `0452b9c6861f` | `6f8f08009da6` = | `ecbabf197a32` | `ecbabf197a32` |
| `app/forge/intelligence_api/contracts.py` | `7d8f90adf8ae` | `fd9e4e44fbb6` | `7d8f90adf8ae` = | `07f9f494ae66` | `07f9f494ae66` |
| `app/forge/market_data/__init__.py` | `94c88cd73abd` | `217e196ba76c` | `94c88cd73abd` = | `5dccc8ade6b9` | `5dccc8ade6b9` |
| `app/forge/market_data/bars.py` | `97fc99e44c7a` | `b1819fb308e0` | `97fc99e44c7a` = | `b2bc3b1fafb1` | `b2bc3b1fafb1` |
| `app/forge/market_data/clocks.py` | `2698d527f6cf` | `a448e2dfa972` | `2698d527f6cf` = | `696a6b28b9ea` | `696a6b28b9ea` |
| `app/forge/market_data/errors.py` | `52f108165f5b` | `787bf8ab9ccc` | `52f108165f5b` = | `f432c143d784` | `f432c143d784` |
| `app/forge/market_data/instruments.py` | `8c6d6ad05db9` | `ae54bf3080cf` | `8c6d6ad05db9` = | `46a1656991c2` | `46a1656991c2` |
| `app/forge/market_data/normalize.py` | `9b7ea855a3a9` | `13161a23d198` | `9b7ea855a3a9` = | `c153a32da607` | `c153a32da607` |
| `app/forge/market_data/parity.py` | `0bb765af9943` | `5f1dd207f11f` | `0bb765af9943` = | `4d478af923a5` | `4d478af923a5` |
| `app/forge/market_data/quality.py` | `6b77c6dfa11e` | `befb4bc4b08e` | `6b77c6dfa11e` = | `cc9a525bfc81` | `cc9a525bfc81` |
| `app/forge/market_data/research_day.py` | `b5c82e4098ea` | `14c071dce7df` | `b5c82e4098ea` = | `a8b51e316c1f` | `a8b51e316c1f` |
| `app/forge/market_data/sessions.py` | `037dbaaa308e` | `afcb72d2d68f` | `037dbaaa308e` = | `852cae03aa90` | `852cae03aa90` |
| `app/forge/market_data/versions.py` | `9e502d7f9e95` | `2ee10af3ea22` | `9e502d7f9e95` = | `e7e9d70f60f6` | `e7e9d70f60f6` |
| `app/forge/measurements/__init__.py` | `2b243ddec1d0` | `a47d5c97eb9c` | `2b243ddec1d0` = | `524cc6e12d0f` | `524cc6e12d0f` |
| `app/forge/measurements/anchors.py` | `227a17d112cc` | `8cffbe2d6362` | `227a17d112cc` = | `fa921d0d074e` | `fa921d0d074e` |
| `app/forge/measurements/calibration.py` | `62a53d65b589` | `3edc7f7f80b1` | `62a53d65b589` = | `90246efbcfc3` | `90246efbcfc3` |
| `app/forge/measurements/contracts.py` | `847074d84825` | `8e364e249f71` | `847074d84825` = | `602539c219e0` | `602539c219e0` |
| `app/forge/measurements/coordinates.py` | `c224d775c68c` | `d158c9ed812d` | `c224d775c68c` = | `2e7c16a98a1c` | `2e7c16a98a1c` |
| `app/forge/measurements/errors.py` | `974fe1ae769c` | `88c0d5e77ed8` | `974fe1ae769c` = | `ef7f91373de1` | `ef7f91373de1` |
| `app/forge/measurements/events.py` | `306093100ed0` | `7db5fa0e172d` | `306093100ed0` = | `d89bc21d01ca` | `d89bc21d01ca` |
| `app/forge/measurements/higher_order.py` | `554061988e98` | `ed9e7d3878fc` | `554061988e98` = | `7aa0e91e66c3` | `7aa0e91e66c3` |
| `app/forge/measurements/path_metrics.py` | `f55dcc24f662` | `8a96344b92c0` | `f55dcc24f662` = | `128c35dbd34e` | `128c35dbd34e` |
| `app/forge/measurements/ranges.py` | `1addf5d06626` | `48f003973d48` | `1addf5d06626` = | `96a63aafbbeb` | `96a63aafbbeb` |
| `app/forge/measurements/state_age.py` | `3c4e45f83381` | `d0b290d198f8` | `3c4e45f83381` = | `89c5ea49ec2e` | `89c5ea49ec2e` |
| `app/forge/measurements/versions.py` | `f139b51ca24e` | `ff45187c4b7f` | `f139b51ca24e` = | `c1f907c1466e` | `c1f907c1466e` |
| `app/forge/model_runtime/__init__.py` | `4d742dea51e4` | `87829ef1b14c` | `4d742dea51e4` = | `0bbabb1bc11d` | `0bbabb1bc11d` |
| `app/forge/model_runtime/btc_tracker.py` | `603409300770` | `df4463c23d8b` | `603409300770` = | `2b8bad97e194` | `2b8bad97e194` |
| `app/forge/model_runtime/contract.py` | `d0dc91f79e81` | `a065bab9f8a4` | `d0dc91f79e81` = | `c00860e10ac1` | `c00860e10ac1` |
| `app/forge/model_runtime/errors.py` | `9a29936df628` | `3a2b523bd85b` | `9a29936df628` = | `b956b8493128` | `b956b8493128` |
| `app/forge/model_runtime/eur_daily.py` | `4cb0fb57b0f5` | `deb750f1299d` | `4cb0fb57b0f5` = | `a9c3383652f3` | `a9c3383652f3` |
| `app/forge/model_runtime/eur_higher_order.py` | `19621c53daed` | `0bfa5332df96` | `19621c53daed` = | `55b2b849ac81` | `55b2b849ac81` |
| `app/forge/model_runtime/eur_weekly.py` | `f532d2633c2a` | `06a602a67d53` | `f532d2633c2a` = | `10672b3e82e4` | `10672b3e82e4` |
| `app/forge/model_runtime/fib_range_birth.py` | `c64ebf9057af` | `7dd4f8e0b502` | `c64ebf9057af` = | `431ed649d4af` | `431ed649d4af` |
| `app/forge/model_runtime/jpy_carry.py` | `bde7aa387987` | `013cf6edf4ad` | `bde7aa387987` = | `3ae2d10ae6a6` | `3ae2d10ae6a6` |
| `app/forge/model_runtime/registry.py` | `3ce67bf4e782` | `cf963beec776` | `3ce67bf4e782` = | `a5c19b8219e5` | `a5c19b8219e5` |
| `app/forge/model_runtime/replay.py` | `c6a14aca8853` | `deacf8cc8709` | `c6a14aca8853` = | `1ec4ed304d8e` | `1ec4ed304d8e` |
| `app/forge/model_runtime/versions.py` | `87823a050528` | `d725d64551b7` | `87823a050528` = | `b7cf1f2c6eb6` | `b7cf1f2c6eb6` |
| `app/forge/model_runtime/xau_game.py` | `3255d6d1275a` | `1cad9b4a4805` | `3255d6d1275a` = | `ecc94f229a07` | `ecc94f229a07` |
| `app/forge/persistence/sql/001_initial_schema.sql` | `d91c2ea2ec45` | `cf6639eaad2c` | `d91c2ea2ec45` = | `0f470aa39619` | `0f470aa39619` |
| `app/forge/policy.py` | `f10751e6ba61` | `7c2928a8005c` | `f10751e6ba61` = | `11e60ea2a19e` | `11e60ea2a19e` |
| `app/forge/service/policy_enforcement.py` | `9ccc3b72f77f` | `571f8f2542a3` | `9ccc3b72f77f` = | `42e8d47f5132` | `42e8d47f5132` |
| `app/forge/service/routes.py` | `145757e0f2b1` | `1f8d53f48567` | `145757e0f2b1` = | `e83fa101f97b` | `e83fa101f97b` |
| `app/forge/state_engine/__init__.py` | `6c009b036812` | `f08ee8ca9b09` | `6c009b036812` = | `8f0475aaf596` | `8f0475aaf596` |
| `app/forge/state_engine/delivery.py` | `ae912568b577` | `ba6b26eb9312` | `ae912568b577` = | `adee2b3c78e7` | `adee2b3c78e7` |
| `app/forge/state_engine/errors.py` | `91f14ea70ceb` | `b58b35c4ee2b` | `91f14ea70ceb` = | `fac48686667a` | `fac48686667a` |
| `app/forge/state_engine/failure_repair.py` | `776de84f6f2f` | `25ef5365e765` | `776de84f6f2f` = | `abda28ec8bd3` | `abda28ec8bd3` |
| `app/forge/state_engine/handoff.py` | `b8e404ed2f5b` | `36eda9257632` | `b8e404ed2f5b` = | `06b32ed4afb9` | `06b32ed4afb9` |
| `app/forge/state_engine/history.py` | `acf2b518458e` | `604d0eefc9eb` | `acf2b518458e` = | `5c098974ebae` | `5c098974ebae` |
| `app/forge/state_engine/invariants.py` | `891481822db0` | `44dbbc1a9d29` | `891481822db0` = | `94d5142789f8` | `94d5142789f8` |
| `app/forge/state_engine/range_left.py` | `61d0789ed9d3` | `a97272f47087` | `61d0789ed9d3` = | `53d5106460e4` | `53d5106460e4` |
| `app/forge/state_engine/rekey.py` | `2a9ac377fe47` | `7140904fecc1` | `2a9ac377fe47` = | `60d6ead8efbd` | `60d6ead8efbd` |
| `app/forge/state_engine/snapshot.py` | `5e6d8c0274db` | `95dea696bfd5` | `5e6d8c0274db` = | `ab1f8e5daee0` | `ab1f8e5daee0` |
| `app/forge/state_engine/stand_down.py` | `31ed18dcbb92` | `d9d45962008a` | `31ed18dcbb92` = | `6c39b1e58a2a` | `6c39b1e58a2a` |
| `app/forge/state_engine/versions.py` | `af648a64c09a` | `f6d8a597a273` | `af648a64c09a` = | `54e6bf04751e` | `54e6bf04751e` |
| `app/forge/state_engine/vocabulary.py` | `c5a559d4bb65` | `ac89f127b708` | `c5a559d4bb65` = | `ab65cebeb105` | `ab65cebeb105` |

## 3. Resolution

- Every guarded file resolved: 65/65 constants reproduce from canonical content.
- Every guarded file is committed as canonical content: 65/65.
- Unresolved constants: none.
- Migration bytes and route bytes are untouched; their guards keep exact content identity, now measured canonically.
