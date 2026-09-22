"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertCircle, Brain, Database, Filter, MessageSquareWarning, ShieldQuestion, Sparkles } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getMetrics } from "@/lib/api";
import type { MetricsResponse } from "@/lib/types";

const MODEL_LABEL: Record<string, string> = { xgboost: "XGBoost", random_forest: "Random Forest", logreg: "Logistic Regression" };

const STEPS = [
  { label: "Data", icon: Database, desc: "US-Accidents 2016-2023, 400k stratified sample" },
  { label: "Preprocessing", icon: Filter, desc: "De-dup, leakage guard, impute, encode" },
  { label: "Model", icon: Brain, desc: "XGBoost / Random Forest / Logistic Regression" },
  { label: "Risk tier", icon: ShieldQuestion, desc: "Tercile thresholds from training predictions" },
  { label: "SHAP", icon: Sparkles, desc: "TreeExplainer, per-prediction attribution" },
  { label: "Warning", icon: MessageSquareWarning, desc: "Plain-language driver message" },
];

export function ModelTransparencyPanel() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMetrics()
      .then(setMetrics)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load metrics"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>How this works</CardTitle>
          <CardDescription>End-to-end pipeline from raw accident records to a driver-facing warning.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-stretch sm:gap-0">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={s.label} className="flex flex-1 items-center">
                  <motion.div
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="flex flex-1 flex-col items-center gap-2 rounded-lg px-2 py-3 text-center"
                  >
                    <span className="flex size-10 items-center justify-center rounded-full bg-accent/15 text-accent">
                      <Icon className="size-5" aria-hidden />
                    </span>
                    <span className="text-sm font-medium text-foreground">{s.label}</span>
                    <span className="text-xs leading-snug text-muted-foreground">{s.desc}</span>
                  </motion.div>
                  {i < STEPS.length - 1 && <div className="mx-1 hidden h-px flex-1 self-center bg-border sm:block" />}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model evaluation - real held-out results</CardTitle>
          <CardDescription>
            {metrics ? `${metrics.n_test.toLocaleString()} held-out rows, ${metrics.split}. Base rate: ${(metrics.base_rate * 100).toFixed(1)}%.` : "Computed by python -m roadmind.evaluate on real held-out data."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-sm text-muted-foreground">Loading metrics...</p>}
          {error && (
            <div className="flex items-start gap-2 rounded-md border border-dashed border-border bg-muted/50 p-4 text-sm text-muted-foreground">
              <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
              <span>
                No metrics available yet. {error}. Run <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">python -m roadmind.evaluate</code> to generate them.
              </span>
            </div>
          )}
          {metrics && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="py-2 pr-4 font-medium">Model</th>
                    <th className="py-2 pr-4 font-medium">ROC-AUC</th>
                    <th className="py-2 pr-4 font-medium">PR-AUC</th>
                    <th className="py-2 pr-4 font-medium">Accuracy</th>
                    <th className="py-2 pr-4 font-medium">Precision</th>
                    <th className="py-2 pr-4 font-medium">Recall (High)</th>
                    <th className="py-2 pr-4 font-medium">F1</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(metrics.models).map(([key, m]) => (
                    <tr key={key} className="border-b border-border-subtle last:border-0">
                      <td className="py-2.5 pr-4 font-medium text-foreground">{MODEL_LABEL[key] ?? key}</td>
                      <td className="py-2.5 pr-4 tabular-nums">{m.roc_auc.toFixed(3)}</td>
                      <td className="py-2.5 pr-4 tabular-nums">{m.pr_auc.toFixed(3)}</td>
                      <td className="py-2.5 pr-4 tabular-nums">{m.accuracy.toFixed(3)}</td>
                      <td className="py-2.5 pr-4 tabular-nums">{m.precision.toFixed(3)}</td>
                      <td className="py-2.5 pr-4 tabular-nums font-medium text-accent">{m.recall.toFixed(3)}</td>
                      <td className="py-2.5 pr-4 tabular-nums">{m.f1.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-3 text-xs text-muted-foreground">
                These are modest, real numbers - not tuned to look better than they are. See{" "}
                <code className="rounded bg-muted px-1 py-0.5 font-mono">reports/evaluation.md</code> for the full write-up,
                including the time-based stress test and known limitations.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
