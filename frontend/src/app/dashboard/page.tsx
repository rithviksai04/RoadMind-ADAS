"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Zap } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Switch } from "@/components/ui/switch";
import { ThemeToggle } from "@/components/theme-toggle";
import { ConditionForm } from "@/components/condition-form";
import { ResultsPanel } from "@/components/results-panel";
import { ModelTransparencyPanel } from "@/components/model-transparency-panel";
import { AboutLimitations } from "@/components/about-limitations";
import { getPrediction, USE_MOCK } from "@/lib/api";
import type { ConditionInput, PredictionResponse } from "@/lib/types";

const DEFAULT_CONDITIONS: ConditionInput = {
  weather_condition: "Fair",
  temperature_f: 65,
  visibility_mi: 10,
  wind_speed_mph: 5,
  precipitation_in: 0,
  hour: 17,
  day_of_week: 2,
  month: 6,
  state: "CA",
};

export default function DashboardPage() {
  const [conditions, setConditions] = useState<ConditionInput>(DEFAULT_CONDITIONS);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [live, setLive] = useState(true);
  const requestId = useRef(0);
  const resultsRef = useRef<HTMLElement>(null);
  const assessedOnce = useRef(false);

  const assess = useCallback(async (c: ConditionInput) => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const r = await getPrediction(c);
      if (id !== requestId.current) return; // a newer request superseded this one
      setResult(r);
      assessedOnce.current = true;
    } catch (e) {
      if (id !== requestId.current) return;
      setError(e instanceof Error ? e.message : "Prediction failed.");
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, []);

  // Live mode: once the user has run one assessment, re-run it whenever an input changes.
  useEffect(() => {
    if (!live || !assessedOnce.current) return;
    const t = setTimeout(() => assess(conditions), 350);
    return () => clearTimeout(t);
  }, [conditions, live, assess]);

  function reset() {
    setConditions(DEFAULT_CONDITIONS);
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
            <div className="flex items-center gap-3">
              <Link href="/" className="rounded p-1 text-muted-foreground transition-colors hover:text-foreground" aria-label="Back to home">
                <ArrowLeft className="size-4" />
              </Link>
              <span className="font-serif-hero text-base font-semibold tracking-tight text-foreground">RoadMind</span>
              {USE_MOCK && (
                <span className="rounded-full border border-risk-medium/50 bg-risk-medium/10 px-2 py-0.5 text-[11px] font-medium text-risk-medium">
                  Mock data
                </span>
              )}
            </div>
            <ThemeToggle />
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
          <Tabs defaultValue="assess">
            <TabsList className="w-full sm:w-auto">
              <TabsTrigger value="assess">Risk assessment</TabsTrigger>
              <TabsTrigger value="model">Model transparency</TabsTrigger>
              <TabsTrigger value="about">About &amp; limitations</TabsTrigger>
            </TabsList>

            <TabsContent value="assess">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] xl:grid-cols-[460px_minmax(0,1fr)]">
                <section aria-label="Condition input" className="card-elevated p-6">
                  <div className="mb-5 flex items-center justify-between gap-3">
                    <h2 className="text-sm font-semibold text-foreground">Driving conditions</h2>
                    <label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
                      <Zap className="size-3.5 text-accent" aria-hidden />
                      Update live
                      <Switch checked={live} onCheckedChange={setLive} aria-label="Update prediction as inputs change" />
                    </label>
                  </div>
                  <ConditionForm
                    value={conditions}
                    onChange={setConditions}
                    onAssess={() => {
                      assess(conditions);
                      // Single-column layout: the result sits below the form, so bring it into view.
                      if (window.matchMedia("(max-width: 1023px)").matches) {
                        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                      }
                    }}
                    onReset={reset}
                    loading={loading}
                  />
                </section>

                <section ref={resultsRef} aria-label="Results" className="scroll-mt-20 lg:sticky lg:top-20 lg:self-start">
                  <ResultsPanel result={result} loading={loading} error={error} onRetry={() => assess(conditions)} />
                </section>
              </div>
            </TabsContent>

            <TabsContent value="model">
              <ModelTransparencyPanel />
            </TabsContent>

            <TabsContent value="about">
              <AboutLimitations />
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </TooltipProvider>
  );
}
