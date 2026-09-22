# Tests

One command from the project root:

```bash
./run_tests.sh            # all tests + regenerates tests/results/scenario_report.md
./run_tests.sh fast       # only the fast feature-rule unit tests (no model needed)
```

| File | What it checks | Needs |
|---|---|---|
| `test_features.py` | weather grouping, road-surface rule, plausibility clipping, wind/rounding rules, rush-hour/night/weekend flags | nothing |
| `test_explain.py` | `explain_prediction()` contract, proposal message format, tier == thresholds, sparse/odd input never crashes, un-supplied inputs never shown, no invented "speed/traffic" reasons, metric-unit conversion | trained model |
| `test_artifacts.py` | leakage guards, split integrity (disjoint, chronological), metric plausibility (beats chance, not suspiciously perfect), tiers ordered by observed risk, saved models load | pipeline outputs |
| `test_scenarios.py` | every scenario in `scenarios.json` (14 US weather/road/time cases) runs; bad sensor values behave like missing; **golden-snapshot regression** | trained model |
| `test_weather.py` | live-weather geocoding/unit mapping, state resolution, error handling - network calls monkeypatched, so this never needs the internet | nothing (mocked) |
| `test_fuzz.py` | 300+ randomized inputs (every US state individually, all weather keywords, extreme/out-of-range values, everything missing) never crash and always return a well-formed result | trained model |

**Add a scenario:** append an object to `scenarios.json` (`id`, `why`, `input`), then run
`python tests/run_scenarios.py --update-golden`. Open `tests/results/scenario_report.md` for the table of tiers, scores and SHAP reasons.

**After an intentional retrain** the golden snapshot will (rightly) fail: re-baseline with `--update-golden`.
The snapshot only detects *change*; it does not assert that a tier is *correct* - the model's ranking skill is what
`reports/evaluation.md` measures (modest: ROC-AUC 0.754). Tests that need a missing artefact are skipped with a message saying what to run.
