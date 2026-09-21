"""Evaluate saved predictions on the held-out sets. Every number in reports/evaluation.md comes from here.

Run: python -m roadmind.evaluate
The hand-written interpretation lives in reports/evaluation_notes.md and is appended verbatim.
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score, roc_curve)

from roadmind.config import MODELS_DIR, PROCESSED_DIR, REPORTS_DIR

MODELS = ["logreg", "random_forest", "xgboost"]
LABEL = {"logreg": "Logistic Regression", "random_forest": "Random Forest", "xgboost": "XGBoost"}
COLORS = {"logreg": "#2a78d6", "random_forest": "#eb6834", "xgboost": "#1baf7a"}
SPLIT_DESC = {"stratified": "PRIMARY: stratified random 80/20 split (stratified on the target)",
              "time": "STRESS TEST: train 2016-2021, test 2022-2023"}


def tier(p, th):
    return np.where(p >= th["medium_high"], "High", np.where(p >= th["low_medium"], "Medium", "Low"))


def evaluate_split(split: str, log: dict) -> dict:
    preds = pd.read_parquet(PROCESSED_DIR / f"preds_{split}.parquet")
    y = preds["y"].to_numpy()
    out = {"n_test": int(len(y)), "base_rate": float(y.mean()), "models": {}}
    for m in MODELS:
        p, th = preds[m].to_numpy(), log[f"{split}/{m}"]
        t = tier(p, th)
        alert = (t == "High").astype(int)  # "High risk" alert = top tier
        tn, fp, fn, tp = confusion_matrix(y, alert).ravel()
        tiers = {k: {"n": int((t == k).sum()), "share_of_test": float((t == k).mean()),
                     "observed_high_impact_rate": float(y[t == k].mean()) if (t == k).any() else None}
                 for k in ["Low", "Medium", "High"]}
        out["models"][m] = {
            "thresholds": {k: th[k] for k in ["low_medium", "medium_high"]},
            "roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
            "brier": brier_score_loss(y, p),
            "brier_baseline_constant": brier_score_loss(y, np.full_like(p, y.mean())),
            "mean_predicted": float(p.mean()),
            "high_tier": {"accuracy": accuracy_score(y, alert), "precision": precision_score(y, alert, zero_division=0),
                          "recall": recall_score(y, alert), "f1": f1_score(y, alert),
                          "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}},
            "medium_plus_recall": recall_score(y, (t != "Low").astype(int)),
            "tiers": tiers,
            "tier_lift_high_vs_base": tiers["High"]["observed_high_impact_rate"] / y.mean(),
        }
    return out


def plots(res: dict):
    out = REPORTS_DIR / "eval"
    out.mkdir(parents=True, exist_ok=True)
    for split in res:
        preds = pd.read_parquet(PROCESSED_DIR / f"preds_{split}.parquet")
        fig, ax = plt.subplots(figsize=(5, 4.6))
        for m in MODELS:
            fpr, tpr, _ = roc_curve(preds["y"], preds[m])
            ax.plot(fpr, tpr, color=COLORS[m], lw=2, label=f"{LABEL[m]} (AUC {res[split]['models'][m]['roc_auc']:.3f})")
        ax.plot([0, 1], [0, 1], color="#9a9890", lw=1, ls="--", label="Chance")
        ax.set(xlabel="False positive rate", ylabel="True positive rate", title=f"ROC - {split} split")
        ax.legend(frameon=False, fontsize=8, loc="lower right")
        fig.savefig(out / f"roc_{split}.png", dpi=130, bbox_inches="tight")
        plt.close(fig)
        fig, axs = plt.subplots(1, 3, figsize=(11, 3.4))
        for ax, m in zip(axs, MODELS):
            c = res[split]["models"][m]["high_tier"]["confusion"]
            cm = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
            ax.imshow(cm, cmap="Blues")
            for (i, j), v in np.ndenumerate(cm):
                ax.text(j, i, f"{v:,}", ha="center", va="center", color="white" if v > cm.max() / 2 else "black")
            ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["not High tier", "High tier"],
                   yticklabels=["Sev 1-2", "Sev 3-4"], title=LABEL[m])
        fig.suptitle(f"Confusion matrix: 'High' risk tier vs actual high impact ({split} split)")
        fig.savefig(out / f"confusion_{split}.png", dpi=130, bbox_inches="tight")
        plt.close(fig)


def fmt_report(res: dict) -> str:
    L = ["# Evaluation (all numbers computed by `python -m roadmind.evaluate` on held-out data)\n",
         "Task: predict **high delay impact (Severity 3-4)** for an accident, given the conditions. "
         "Risk tiers: Low / Medium / High are terciles of the predicted probability, with thresholds taken "
         "from out-of-fold predictions on the training set. The 'High' tier is therefore the top third of "
         "predictions, by construction.\n"]
    for split, r in res.items():
        L += [f"## {SPLIT_DESC[split]}\n",
              f"Test rows: {r['n_test']:,}. Observed high-impact rate in the test set: **{r['base_rate']:.1%}**.\n",
              "### Threshold-free ranking quality\n",
              "| Model | ROC-AUC | PR-AUC | Brier | Brier (constant base rate) | Mean predicted P |",
              "|---|---|---|---|---|---|"]
        for m in MODELS:
            x = r["models"][m]
            L.append(f"| {LABEL[m]} | {x['roc_auc']:.3f} | {x['pr_auc']:.3f} | {x['brier']:.4f} | "
                     f"{x['brier_baseline_constant']:.4f} | {x['mean_predicted']:.3f} |")
        L += ["", "PR-AUC of a random ranker = the base rate above.\n",
              "### 'High' tier as an alert (positive class = Severity 3-4)\n",
              "| Model | Accuracy | Precision | **Recall (High-risk class)** | F1 | Recall if Medium+High flagged |",
              "|---|---|---|---|---|---|"]
        for m in MODELS:
            h = r["models"][m]["high_tier"]
            L.append(f"| {LABEL[m]} | {h['accuracy']:.3f} | {h['precision']:.3f} | **{h['recall']:.3f}** | "
                     f"{h['f1']:.3f} | {r['models'][m]['medium_plus_recall']:.3f} |")
        L += ["", "### Confusion matrices (High tier vs actual Severity 3-4)\n",
              "| Model | TN | FP | FN | TP |", "|---|---|---|---|---|"]
        for m in MODELS:
            c = r["models"][m]["high_tier"]["confusion"]
            L.append(f"| {LABEL[m]} | {c['tn']:,} | {c['fp']:,} | {c['fn']:,} | {c['tp']:,} |")
        L += ["", "### Risk-tier thresholds (from training data) and observed high-impact rate per tier on the test set\n",
              "| Model | Low/Medium cut | Medium/High cut | Low tier | Medium tier | High tier | High-tier lift vs base rate |",
              "|---|---|---|---|---|---|---|"]
        for m in MODELS:
            x = r["models"][m]
            tt = x["tiers"]
            L.append(f"| {LABEL[m]} | {x['thresholds']['low_medium']:.4f} | {x['thresholds']['medium_high']:.4f} | "
                     + " | ".join(f"{tt[k]['observed_high_impact_rate']:.1%} ({tt[k]['share_of_test']:.0%} of rows)" for k in ["Low", "Medium", "High"])
                     + f" | {x['tier_lift_high_vs_base']:.2f}x |")
        L += ["", f"Plots: `reports/eval/roc_{split}.png`, `reports/eval/confusion_{split}.png`\n"]
    notes = REPORTS_DIR / "evaluation_notes.md"
    if notes.exists():
        L += ["", notes.read_text()]
    return "\n".join(L)


if __name__ == "__main__":
    log = json.loads((MODELS_DIR / "train_log.json").read_text())
    res = {s: evaluate_split(s, log) for s in ["stratified", "time"]}
    (REPORTS_DIR / "metrics.json").write_text(json.dumps(res, indent=2))
    plots(res)
    text = fmt_report(res)
    (REPORTS_DIR / "evaluation.md").write_text(text)
    print(text)
