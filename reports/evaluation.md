# Evaluation (all numbers computed by `python -m roadmind.evaluate` on held-out data)

Task: predict **high delay impact (Severity 3-4)** for an accident, given the conditions. Risk tiers: Low / Medium / High are terciles of the predicted probability, with thresholds taken from out-of-fold predictions on the training set. The 'High' tier is therefore the top third of predictions, by construction.

## PRIMARY: stratified random 80/20 split (stratified on the target)

Test rows: 79,732. Observed high-impact rate in the test set: **19.5%**.

### Threshold-free ranking quality

| Model | ROC-AUC | PR-AUC | Brier | Brier (constant base rate) | Mean predicted P |
|---|---|---|---|---|---|
| Logistic Regression | 0.742 | 0.403 | 0.1380 | 0.1571 | 0.196 |
| Random Forest | 0.772 | 0.455 | 0.1326 | 0.1571 | 0.196 |
| XGBoost | 0.781 | 0.474 | 0.1295 | 0.1571 | 0.196 |

PR-AUC of a random ranker = the base rate above.

### 'High' tier as an alert (positive class = Severity 3-4)

| Model | Accuracy | Precision | **Recall (High-risk class)** | F1 | Recall if Medium+High flagged |
|---|---|---|---|---|---|
| Logistic Regression | 0.716 | 0.368 | **0.633** | 0.465 | 0.881 |
| Random Forest | 0.728 | 0.385 | **0.658** | 0.486 | 0.904 |
| XGBoost | 0.733 | 0.393 | **0.671** | 0.495 | 0.918 |

### Confusion matrices (High tier vs actual Severity 3-4)

| Model | TN | FP | FN | TP |
|---|---|---|---|---|
| Logistic Regression | 47,246 | 16,925 | 5,716 | 9,845 |
| Random Forest | 47,819 | 16,352 | 5,323 | 10,238 |
| XGBoost | 48,005 | 16,166 | 5,113 | 10,448 |

### Risk-tier thresholds (from training data) and observed high-impact rate per tier on the test set

| Model | Low/Medium cut | Medium/High cut | Low tier | Medium tier | High tier | High-tier lift vs base rate |
|---|---|---|---|---|---|---|
| Logistic Regression | 0.1150 | 0.2219 | 7.0% (33% of rows) | 14.5% (33% of rows) | 36.8% (34% of rows) | 1.88x |
| Random Forest | 0.1143 | 0.2123 | 5.5% (34% of rows) | 14.8% (32% of rows) | 38.5% (33% of rows) | 1.97x |
| XGBoost | 0.0934 | 0.2130 | 4.9% (33% of rows) | 14.2% (34% of rows) | 39.3% (33% of rows) | 2.01x |

Plots: `reports/eval/roc_stratified.png`, `reports/eval/confusion_stratified.png`

## STRESS TEST: train 2016-2021, test 2022-2023

Test rows: 103,503. Observed high-impact rate in the test set: **6.4%**.

### Threshold-free ranking quality

| Model | ROC-AUC | PR-AUC | Brier | Brier (constant base rate) | Mean predicted P |
|---|---|---|---|---|---|
| Logistic Regression | 0.644 | 0.112 | 0.0861 | 0.0600 | 0.206 |
| Random Forest | 0.676 | 0.126 | 0.0834 | 0.0600 | 0.206 |
| XGBoost | 0.683 | 0.128 | 0.0869 | 0.0600 | 0.198 |

PR-AUC of a random ranker = the base rate above.

### 'High' tier as an alert (positive class = Severity 3-4)

| Model | Accuracy | Precision | **Recall (High-risk class)** | F1 | Recall if Medium+High flagged |
|---|---|---|---|---|---|
| Logistic Regression | 0.778 | 0.119 | **0.383** | 0.181 | 0.798 |
| Random Forest | 0.803 | 0.130 | **0.366** | 0.192 | 0.839 |
| XGBoost | 0.790 | 0.132 | **0.410** | 0.200 | 0.847 |

### Confusion matrices (High tier vs actual Severity 3-4)

| Model | TN | FP | FN | TP |
|---|---|---|---|---|
| Logistic Regression | 77,987 | 18,881 | 4,096 | 2,539 |
| Random Forest | 80,677 | 16,191 | 4,206 | 2,429 |
| XGBoost | 79,041 | 17,827 | 3,914 | 2,721 |

### Risk-tier thresholds (from training data) and observed high-impact rate per tier on the test set

| Model | Low/Medium cut | Medium/High cut | Low tier | Medium tier | High tier | High-tier lift vs base rate |
|---|---|---|---|---|---|---|
| Logistic Regression | 0.1524 | 0.2896 | 3.7% (35% of rows) | 6.0% (44% of rows) | 11.9% (21% of rows) | 1.85x |
| Random Forest | 0.1491 | 0.2978 | 2.9% (35% of rows) | 6.5% (47% of rows) | 13.0% (18% of rows) | 2.03x |
| XGBoost | 0.1227 | 0.2985 | 2.8% (35% of rows) | 6.2% (45% of rows) | 13.2% (20% of rows) | 2.07x |

Plots: `reports/eval/roc_time.png`, `reports/eval/confusion_time.png`


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
