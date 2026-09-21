# RoadMind - explainable predictive risk co-pilot (research prototype)

RoadMind estimates, from environmental / road / time conditions, how likely an accident is to have a **high traffic-delay
impact**, bins that into **Low / Medium / High** risk, and explains every prediction with **SHAP**.
It is a research prototype trained on a public dataset. It is **not** a validated safety system.

## Read this first: what the target really is

- Dataset: **US Accidents (2016-2023)**, Moosavi et al. - 7,728,394 rows, 46 columns, Feb 2016 - Mar 2023.
  Kaggle: `sobhanmoosavi/us-accidents`. Licence **CC BY-NC-SA 4.0: research / non-commercial use only**.
- Target: `Severity` (1-4) measures **traffic-flow delay impact, not injury severity**. We use it as a *risk-impact proxy*:
  `high_impact = Severity in {3, 4}` (19.5% of rows).
- The dataset contains **only accidents that occurred**. RoadMind therefore estimates
  *P(high delay-impact | an accident occurs under these conditions)*. It does **not** estimate the probability that an accident occurs.
- The dataset has **no driver-behaviour fields** (speed, braking, steering, ...) and **no real-time traffic-density field**. None were simulated.
  `is_rush_hour` (weekday 07-09 / 16-18) is a clearly-labelled *approximation* of congestion.
- Road-surface condition (`dry/wet/icy/unknown`) is **derived** from weather + precipitation + temperature; the rule is in `feature_dictionary.md`.

## Real results (held-out data, all computed by the code in this repo)

Full tables, confusion matrices, thresholds and interpretation: [`reports/evaluation.md`](reports/evaluation.md).

**Primary split - stratified random 80/20 (79,732 test rows, 19.5% high-impact):**

| Model | ROC-AUC | PR-AUC (random = 0.195) | High-tier precision | **High-tier recall** | F1 |
|---|---|---|---|---|---|
| Logistic Regression | 0.707 | 0.370 | 0.330 | 0.567 | 0.417 |
| Random Forest | 0.742 | 0.411 | 0.357 | 0.611 | 0.451 |
| **XGBoost** | **0.754** | **0.431** | 0.366 | **0.625** | 0.462 |

(High-tier = predicted probability above the training-set upper tercile. Accuracy for XGBoost: 0.716. See `reports/evaluation.md` for the exact figures of every model.)

- XGBoost **misses 37.5%** of high-impact accidents at the High tier (recall 62.5%) and **63% of its High alerts are false alarms**.
- Observed high-impact rate by XGBoost tier: Low 5.6% / Medium 16.2% / High 36.6% (base rate 19.5%): a useful ranking, not a sharp classifier.
- **Tier thresholds** (tertiles of out-of-fold *training* predictions, XGBoost): Low/Medium = **0.1108**, Medium/High = **0.2277**.

**Stress test - train 2016-2021, test 2022-2023 (103,503 rows, 6.4% high-impact):** XGBoost ROC-AUC **0.665**, High-tier recall 0.511, precision 0.111.
Much weaker; the Severity label's meaning drifted by data provider over time (below), and probabilities are badly miscalibrated on this split.

**Honest summary: modest signal, not strong.** Most of the signal is location (`state`, station pressure) and road annotations
(crossing / signal / junction), not weather. Weather ranks low in the SHAP importance (`reports/shap/`). A driver warning built on this
will often cite location or time of year rather than weather, and can rank a clear afternoon as riskier than night-time fog
(`reports/shap/example_explanations.json`). That reflects the data (delay impact), not physical hazard.

### Data-quality problems found (important)
1. **Severity labelling drifts by provider and year.** Provider "Source1" goes from ~33% Severity 3-4 (2016-18) to ~3% (2021+), while "Source2" stays ~35%
   ([`reports/eda/FINDINGS.md`](reports/eda/FINDINGS.md)). So `Source` and year are excluded from the features, and the time-based split is only a stress test.
   For that reason the **primary split is stratified-random**, not time-based. I initially planned time-based and changed it after seeing this.
2. **Provider fingerprints leak through feature quirks.** A `precip_missing` flag (a proxy for year), median-imputed wind (calm was stored as NaN before 2019) and numeric precision
   (Source1 reports whole numbers far more often) all let the model identify the provider. Each was removed or neutralised; that lowered XGBoost AUC from 0.781 to 0.754.
   Other fingerprints may remain. Details: `feature_dictionary.md`, `reports/evaluation.md`.
3. Robustness: [`reports/robustness.md`](reports/robustness.md) - AUC 0.748 / 0.740 inside Source1 / Source2 rows; 0.745 when trained and tested on Source2 only; 0.699 without `state`.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
```
Python 3.14 was used; `pyproject.toml` requires >= 3.11.

## Reproduce

```bash
# 1. Data: put YOUR OWN Kaggle credentials in ~/.kaggle/ (kaggle.json, or an access_token file) - nothing is hardcoded
./scripts/download_data.sh                 # ~3 GB CSV -> data/raw/ (git-ignored)
# 2. Chunked read of the full 7.7M rows -> exact stratified 400k sample (Severity x year), seed 42
python -m roadmind.sample                  # --n / --seed available
# 3. EDA plots + tables -> reports/eda/
python -m roadmind.eda
# 4. De-dup, feature engineering, splits -> data/processed/features.parquet
python -m roadmind.preprocess
# 5. Train LR / RF / XGBoost on both splits (~5 min on 16 cores) -> models/*.joblib (git-ignored)
python -m roadmind.train
# 6. Held-out metrics -> reports/evaluation.md, reports/metrics.json, reports/eval/*.png
python -m roadmind.evaluate
python -m roadmind.robustness              # -> reports/robustness.md
# 7. SHAP global plots + example explanations -> reports/shap/
python -m roadmind.explain
```

**Running on more data:** the sampler streams the CSV in 500k-row chunks, but it keeps a random over-sample of ~3x `--n` rows in memory.
`--n 1000000` should be fine on 16 GB (not tested); the *entire* 7.7M rows would not fit in ~14 GB of RAM. Everything downstream is size-agnostic.
Any change to the sample changes every number in this README, so re-run steps 2-7 and re-read `reports/evaluation.md`.

## Demo

```bash
streamlit run app.py                                   # sliders for weather / visibility / time / state / road features
python -m roadmind.cli --weather Fog --visibility 0.5 --hour 23 --state TX --temp 45 --precip 0.05
```
Programmatic: `from roadmind.explain import explain_prediction` returns
`{risk_level, probability, top_factors, suggested_message, notes}`. The message follows the proposal's format
(risk level, reasons, suggested response). Reasons are limited to features that exist in the data - no "high speed" or "heavy traffic".
Un-supplied inputs are imputed and are never quoted as reasons.

## Project layout
```
src/roadmind/  sample.py eda.py features.py preprocess.py train.py evaluate.py robustness.py explain.py cli.py
app.py                 Streamlit demo
feature_dictionary.md  every engineered feature and how it is computed
reports/               eda/  eval/  shap/  evaluation.md  robustness.md
```

## Method notes
- **Leakage:** `End_Time`, `End_Lat/Lng`, `Distance(mi)`, `Description`, `Weather_Timestamp` are dropped at sampling/feature time, and a guard asserts no forbidden column reaches the model. Raw lat/lng and street are also excluded (memorisation risk); only `state` is kept.
- **Models:** unweighted (probabilities stay interpretable; tertile tiers depend only on ranking). Hyper-parameters fixed a priori, never tuned on the test set; XGBoost's tree count comes from early stopping on 10% of the training set.
- **Risk tiers:** tertiles of 3-fold out-of-fold predicted probability on the training set (in-sample tree predictions are over-confident).
- **SHAP:** `TreeExplainer` on XGBoost, values in log-odds; one-hot columns are summed back to their parent feature for driver-facing reasons.
- **Caveat on the reported numbers:** one seed, one split per setting. I changed the feature set three times after seeing SHAP/robustness results (the artefacts above), so the held-out numbers are not fully independent of my choices.

## Known limitations
- Severity = delay impact, and the data is accident-only (see top). No claim of accident prevention or of injury-severity prediction is supported.
- Missing fields: driver behaviour, traffic density. Substitutes are approximations, marked as such.
- The POI flags (`junction`, `crossing`, ...) describe the accident location; using them for a road *ahead* assumes a map lookup that was not validated.
- Label drift across providers/years; weak out-of-time performance; probabilities uncalibrated out of distribution.
- Geography dominates; performance elsewhere (non-US) is unknown. Only US data, 2016-2023.
- **Licence:** CC BY-NC-SA 4.0 - research / non-commercial only; derivatives must be shared alike with attribution.

## What a production version would need
- Real-time inputs: live weather / road-surface sensing, traffic-density feeds, map/POI data for the road ahead.
- Vehicle telematics (speed, braking, steering) with the driver's consent, and a target that means something (crash or near-miss outcomes with exposure data, so that *occurrence* risk can be modelled).
- A dataset with consistent labelling (or provider-aware modelling), calibrated probabilities, and time-based / geographic cross-validation.
- Human-factors testing of the warnings (alert fatigue, given a High-tier precision of ~37%), safety case, and a licence that permits commercial use.

## Citation
Moosavi, S., Samavatian, M. H., Parthasarathy, S., Ramnath, R. (2019). *A Countrywide Traffic Accident Dataset.* arXiv:1906.05409.
Moosavi, S., Samavatian, M. H., Parthasarathy, S., Teodorescu, R., Ramnath, R. (2019). *Accident Risk Prediction based on Heterogeneous Sparse Data: New Dataset and Insights.* ACM SIGSPATIAL.
(Please verify the exact citation strings against the Kaggle dataset page before publishing.)
