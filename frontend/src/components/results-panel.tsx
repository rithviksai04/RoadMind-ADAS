"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Gauge, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RiskGauge } from "@/components/risk-gauge";
import { ShapChart } from "@/components/shap-chart";
import { WarningCard } from "@/components/warning-card";
import type { PredictionResponse } from "@/lib/types";

interface ResultsPanelProps {
  result: PredictionResponse | null;
  loading: boolean;
  error: string | null;
}

export function ResultsPanel({ result, loading, error }: ResultsPanelProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Risk assessment</CardTitle>
            {result && (
              <Badge variant="outline" className="font-mono text-[11px]">
                {result.model.name} &middot; {result.model.version}
              </Badge>
            )}
          </div>
          <CardDescription>Real-time SHAP-explained prediction from the trained model.</CardDescription>
        </CardHeader>
        <CardContent>
          <AnimatePresence mode="wait">
            {!result && !loading && !error && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center gap-3 py-14 text-center text-muted-foreground"
              >
                <Gauge className="size-10 text-border" aria-hidden />
                <p className="text-sm">Set conditions on the left and click &ldquo;Assess Risk&rdquo; to see a live prediction.</p>
              </motion.div>
            )}
            {loading && (
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
            {error && !loading && (
              <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="py-8 text-center text-sm text-risk-high">
                {error}
              </motion.div>
            )}
            {result && !loading && (
              <motion.div key="result" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
                <RiskGauge probability={result.risk_probability} riskLevel={result.risk_level} thresholds={result.thresholds} />
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>

      {result && !loading && (
        <>
          <WarningCard level={result.risk_level} warning={result.warning} notes={result.notes} />

          <Card>
            <CardHeader>
              <CardTitle>SHAP contribution</CardTitle>
              <CardDescription>Ranked by magnitude &middot; log-odds impact on the high-impact prediction.</CardDescription>
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
