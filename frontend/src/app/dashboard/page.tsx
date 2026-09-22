"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeToggle } from "@/components/theme-toggle";
import { ConditionForm } from "@/components/condition-form";
import { ResultsPanel } from "@/components/results-panel";
import { ModelTransparencyPanel } from "@/components/model-transparency-panel";
import { AboutLimitations } from "@/components/about-limitations";
import { getPrediction } from "@/lib/api";
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

  async function handleAssess() {
    setLoading(true);
    setError(null);
    try {
      const r = await getPrediction(conditions);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Prediction failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <Link href="/" className="text-muted-foreground transition-colors hover:text-foreground" aria-label="Back to home">
                <ArrowLeft className="size-4" />
              </Link>
              <span className="font-serif-hero text-base font-semibold tracking-tight text-foreground">RoadMind</span>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-6 py-8">
          <Tabs defaultValue="assess">
            <TabsList className="w-full sm:w-auto">
              <TabsTrigger value="assess">Risk Assessment</TabsTrigger>
              <TabsTrigger value="model">Model Transparency</TabsTrigger>
              <TabsTrigger value="about">About &amp; Limitations</TabsTrigger>
            </TabsList>

            <TabsContent value="assess">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] xl:grid-cols-[440px_minmax(0,1fr)]">
                <section aria-label="Condition input" className="card-elevated p-6">
                  <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-muted-foreground">Conditions</h2>
                  <ConditionForm value={conditions} onChange={setConditions} onAssess={handleAssess} loading={loading} />
                </section>

                <section aria-label="Results">
                  <ResultsPanel result={result} loading={loading} error={error} />
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
