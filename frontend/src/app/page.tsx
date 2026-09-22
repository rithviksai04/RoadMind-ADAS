"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Brain, Radar, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

const FEATURES = [
  { icon: Radar, title: "Predictive, not just reactive", desc: "Forecasts elevated-risk conditions from weather, time and road context before a hazard is detected onboard." },
  { icon: Brain, title: "Explainable by design", desc: "Every prediction ships with a ranked SHAP breakdown of exactly what drove the score." },
  { icon: ShieldCheck, title: "Honest about its limits", desc: "Real held-out metrics, documented dataset gaps, and no claim of accident prevention." },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="hero-backdrop" aria-hidden />

      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <span className="font-serif-hero text-lg font-semibold tracking-tight text-foreground">RoadMind</span>
        <ThemeToggle />
      </header>

      <main className="relative z-10 mx-auto flex max-w-6xl flex-col items-center px-6 pb-24 pt-12 text-center sm:pt-20">
        <motion.span
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-border-subtle bg-muted/50 px-4 py-1.5 text-xs font-medium text-muted-foreground"
        >
          Explainable ML &middot; Research prototype &middot; Real trained model
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="font-serif-hero max-w-3xl text-4xl font-semibold leading-tight tracking-tight text-foreground sm:text-6xl"
        >
          RoadMind
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.12 }}
          className="mt-4 max-w-xl text-lg text-muted-foreground sm:text-xl"
        >
          Explainable Predictive AI Co-Pilot for ADAS
        </motion.p>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.18 }}
          className="mt-6 max-w-2xl text-balance text-base leading-relaxed text-muted-foreground"
        >
          RoadMind forecasts elevated accident-risk conditions from weather, time and road context, classifies the
          situation as Low, Medium or High risk, and explains every prediction with SHAP - so the driver gets a
          specific reason, not an opaque alert.
        </motion.p>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.26 }} className="mt-10">
          <Button asChild size="lg" className="group">
            <Link href="/dashboard">
              Try a Risk Assessment
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
            </Link>
          </Button>
        </motion.div>

        <div className="mt-24 grid w-full grid-cols-1 gap-5 sm:grid-cols-3">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + i * 0.08 }}
                className="card-elevated p-5 text-left"
              >
                <span className="mb-3 flex size-9 items-center justify-center rounded-full bg-accent/15 text-accent">
                  <Icon className="size-4" aria-hidden />
                </span>
                <h3 className="text-sm font-semibold text-foreground">{f.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
