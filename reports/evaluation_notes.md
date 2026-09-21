## Interpretation (written by hand from the numbers above - read this before quoting any metric)

**Bottom line: the models have modest, real predictive signal. They are not strong.**

- **Best model on the primary split is XGBoost:** ROC-AUC 0.781 and PR-AUC 0.474 (random ranker: 0.195). It beats Random Forest (0.772) and Logistic Regression (0.742).
  The gap between models is small, which suggests the ceiling is set by the information in the features, not by the model class.
- **What the tiers mean in practice (XGBoost, primary split):** among test accidents placed in the *High* tier, 39.3% were high-impact (Severity 3-4).
  In the *Low* tier it was 4.9%, against 19.5% overall. That is a ~2x lift in the High tier and a ~4x reduction in the Low tier.
  The High tier is still wrong about 6 times in 10.
- **Recall for the High-risk class:** XGBoost catches **67.1%** of high-impact accidents by flagging the top third of predictions. That leaves **32.9% missed**,
  and the High-tier precision is only **39.3%**. Flagging Medium+High raises recall to 91.8% but flags two thirds of all cases.
  Recall for the High class is only as good as it is because a third of all rows are labelled High by construction.
- **The time-based stress test is much weaker.** ROC-AUC falls to 0.68 (XGBoost), High-class recall to 41%, and precision to 13%. Two reasons, which we cannot cleanly separate:
  (1) the Severity label's meaning drifted over time by provider (base rate 24% in training vs 6.4% in test - see `reports/eda/FINDINGS.md`), so the test set has a different labelling regime;
  (2) genuine distribution shift. Because of (1), the tier thresholds learned on 2016-2021 also put only ~20% of 2022-23 rows in the High tier. The stress-test numbers should not be read as deployment performance, but they do show that the primary-split numbers are optimistic about generalising to new periods.
- **Probabilities are not well calibrated out of distribution** (time split: mean predicted 0.20 vs observed 0.064; Brier worse than a constant guess for all three models on that split).
  On the primary split, Brier improves on the constant baseline (0.1295 vs 0.1571 for XGBoost).
- **Where the skill comes from (`reports/robustness.md`):** AUC is 0.795 within Source1 rows and 0.734 within Source2 rows, so it is not purely a provider artefact.
  Dropping `state` reduces XGBoost AUC from 0.781 to 0.741, so a noticeable part of the signal is location, not weather or time.
- **What this is NOT:** the dataset has no non-accident rows, so this is not an accident-occurrence predictor, and Severity is delay impact, not injury severity. No claim of accident prevention can be made from these results.
- The hyper-parameters were fixed in advance and never tuned on the test set. There was one train/test evaluation per split and no repeated peeking.
  Only a single random seed was run, so differences of ~0.01 AUC between models should not be treated as established.
