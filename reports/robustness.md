# Robustness checks

| Check | XGBoost ROC-AUC (stratified test) | n |
|---|---|---|
| All rows (reference) | 0.781 | 79,732 |
| Only Source1 rows in test set (model trained on all sources) | 0.795 | 44,725 |
| Only Source2 rows in test set (model trained on all sources) | 0.734 | 33,997 |
| Retrained WITHOUT `state` | 0.741 | 79,732 |
