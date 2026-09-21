## Interpretation (written by hand from the numbers above - read this before quoting any metric)

**Bottom line: the models have modest but real predictive signal. They are not strong, and most of the signal is
location and road-annotation information, not weather.**

- **Best model on the primary split is XGBoost:** ROC-AUC 0.754, PR-AUC 0.431 (a random ranker scores 0.195). Random Forest gets 0.742 and
  Logistic Regression 0.707. The gap between models is small, which suggests the ceiling is set by the information in the features,
  not by the model class. This is one seed and one split, so a ~0.01 AUC difference should not be treated as established.
- **What the tiers mean in practice (XGBoost, primary split):** among test accidents placed in the *High* tier, 36.6% were high-impact (Severity 3-4).
  In the *Low* tier it was 5.6%, against 19.5% overall. That is a 1.88x lift in the High tier and a ~3.5x reduction in the Low tier.
  The High tier is still wrong about 63% of the time.
- **Recall for the High-risk class:** XGBoost catches **62.5%** of high-impact accidents by flagging the top third of predictions, so **37.5% are missed**
  (5,843 of 15,561), and High-tier precision is only **36.6%** (16,820 false alarms against 9,718 true hits).
  Flagging Medium+High raises recall to 90.5%, but that flags two thirds of all cases.
  Recall for the High class is only this high because the High tier is a third of all rows by construction.
- **Threshold values used (XGBoost, primary split, from out-of-fold training predictions):** Low/Medium = 0.1108, Medium/High = 0.2277.
- **The time-based stress test is much weaker.** XGBoost ROC-AUC falls to 0.665, High-class recall is 51.1% and precision 11.1%. Two reasons, which cannot be cleanly separated:
  (1) the meaning of the Severity label drifted over time by provider (base rate 24% in training vs 6.4% in test, see `reports/eda/FINDINGS.md`), so the test set has a different labelling regime;
  (2) genuine distribution shift. The stress-test numbers should not be read as deployment performance, but they do show that the primary-split numbers are
  optimistic about generalising to new periods.
- **Probabilities are not calibrated out of distribution:** in the time split, mean predicted probability is 0.231 while the observed rate is 0.064, and Brier is worse than
  a constant guess for all three models (XGBoost 0.100 vs 0.060). On the primary split Brier does improve on the constant baseline (0.1354 vs 0.1571).
  The tiers rank conditions; the raw probability should not be shown to a driver as a literal chance.
- **Where the skill comes from:**
  - Global SHAP (`reports/shap/`) ranks `state` first, `pressure_in` second (station pressure largely encodes altitude/location), then `crossing`, `month`, `traffic_signal`, and only then `weather_group`, `temperature_f`, `hour`.
    Visibility and road surface rank much lower. **Weather is a weak driver in this data.**
  - Within a single provider the ranking skill holds (`reports/robustness.md`): AUC 0.748 on Source1 rows, 0.740 on Source2 rows, and 0.745 when trained AND tested on Source2 only (whose label regime is stable over time, without `state`).
  - Dropping `state` reduces XGBoost AUC from 0.754 to 0.699.
- **Data-provider artefacts found and removed while building this (they inflated earlier runs):**
  1. a `precip_missing` flag: it was a proxy for year (91% missing in 2016-18 vs 4% in 2021+);
  2. wind speed: NaN wind before 2019 means calm, but was median-imputed, leaving an era fingerprint. Missing wind is now set to 0;
  3. numeric precision: Source1 reports whole numbers far more often than Source2, letting trees decode the provider. Wind and temperature are now rounded to integers, and pressure and visibility to 0.1.
  Together these lowered XGBoost's primary-split ROC-AUC from 0.781 to 0.754. Other provider fingerprints may remain (for example in the road-annotation flags or `month`), and I cannot rule them out.
- **The model does not behave like driving common sense.** The three example inputs in `reports/shap/example_explanations.json` include a night-time fog case
  (visibility 0.5 mi) that scores only *Medium* and a clear afternoon in California that scores *High*. The target is traffic-delay impact given that an accident happened, and it is
  dominated by where the accident is and what road features exist, not by how hazardous the weather is.
  A driver-facing warning built on it will often cite location or time of year rather than weather.
- **What this is NOT:** the dataset has no non-accident rows, so this is not an accident-occurrence predictor, and Severity is delay impact, not injury severity.
  No claim of accident prevention can be made from these results.
- The hyper-parameters were fixed in advance, never tuned on the test set, and each split was evaluated once per final pipeline. However, I did change the feature set three times after looking at
  the SHAP output and robustness checks (the three artefacts above), so the held-out numbers are not fully independent of my choices.
