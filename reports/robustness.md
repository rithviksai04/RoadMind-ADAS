# Robustness checks

| Check | XGBoost ROC-AUC (stratified test) | n |
|---|---|---|
| All rows (reference) | 0.754 | 79,732 |
| Only Source1 rows in test set (model trained on all sources) | 0.748 | 44,725 |
| Only Source2 rows in test set (model trained on all sources) | 0.740 | 33,997 |
| Retrained WITHOUT `state` | 0.699 | 79,732 |
| Trained AND tested on Source2 only (stable label regime; no `state`) | 0.745 | 34,153 |
