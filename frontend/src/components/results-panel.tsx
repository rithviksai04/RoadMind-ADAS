"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Gauge, Loader2, RefreshCw } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RiskGauge } from "@/components/risk-gauge";
import { ShapChart } from "@/components/shap-chart";
import { WarningCard } from "@/components/warning-card";
import type { PredictionResponse } from "@/lib/types";

interface ResultsPanelProps {
  result: PredictionResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export function ResultsPanel({ result, loading, error, onRetry }: ResultsPanelProps) {
  const firstLoad = loading && !result;

  return (
    <div className="space-y-6">
      <Card className="relative overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>Risk meter</CardTitle>
            <div className="flex items-center gap-2">
              {loading && result && <Loader2 className="size-4 animate-spin text-accent" aria-label="Updating" />}
              {result && (
                <Badge variant="outline" className="font-mono text-[11px]">
                  {result.model.name} &middot; {result.model.version}
                </Badge>
              )}
            </div>
          </div>
          <CardDescription>SHAP-explained prediction from the trained model.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div role="alert" className="mb-4 flex items-start gap-3 rounded-md border border-risk-high/40 bg-risk-high/10 p-3 text-sm">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-risk-high" aria-hidden />
              <div className="flex-1 space-y-2">
                <p className="text-foreground">{error}</p>
                <Button type="button" size="sm" variant="outline" onClick={onRetry}>
                  <RefreshCw /> Retry
                </Button>
              </div>
            </div>
          )}
          <AnimatePresence mode="wait">
            {!result && !firstLoad && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-3 py-14 text-center text-muted-foreground"
              >
                <Gauge className="size-10 text-border" aria-hidden />
                <p className="max-w-xs text-sm">
                  Pick a scenario or set conditions, then press <span className="font-medium text-foreground">Assess risk</span>.
                </p>
              </motion.div>
            )}
            {firstLoad && (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-3 py-14 text-muted-foreground"
              >
                <Loader2 className="size-8 animate-spin text-accent" aria-hidden />
                <p className="text-sm">Running the model...</p>
              </motion.div>
            )}
            {result && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: loading ? 0.6 : 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                aria-live="polite"
                aria-busy={loading}
              >
                <RiskGauge probability={result.risk_probability} riskLevel={result.risk_level} thresholds={result.thresholds} />
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>

      {result && (
        <>
          <WarningCard level={result.risk_level} warning={result.warning} notes={result.notes} />

          <Card>
            <CardHeader>
              <CardTitle>What drove this score</CardTitle>
              <CardDescription>
                SHAP contributions, largest first. <span className="text-accent">Teal</span> pushes risk up, grey pulls it down.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ShapChart factors={result.shap_factors} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
