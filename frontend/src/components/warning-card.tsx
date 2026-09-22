"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Info, ShieldAlert, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RiskLevel, WarningPayload } from "@/lib/types";

const STYLE: Record<RiskLevel, { icon: typeof ShieldCheck; border: string; iconBg: string }> = {
  LOW: { icon: ShieldCheck, border: "border-l-risk-low", iconBg: "bg-risk-low" },
  MEDIUM: { icon: AlertTriangle, border: "border-l-risk-medium", iconBg: "bg-risk-medium" },
  HIGH: { icon: ShieldAlert, border: "border-l-risk-high", iconBg: "bg-risk-high" },
};

export function WarningCard({ level, warning, notes }: { level: RiskLevel; warning: WarningPayload; notes?: string }) {
  const s = STYLE[level];
  const Icon = s.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35 }}
      className={cn("card-elevated border-l-4 p-5", s.border)}
    >
      <div className="flex items-start gap-3">
        <span className={cn("mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full", s.iconBg)}>
          <Icon className="size-4 text-white" strokeWidth={2.25} aria-hidden />
        </span>
        <div className="flex-1 space-y-3">
          <p className="font-semibold leading-snug text-card-foreground">{warning.headline}</p>
          {warning.reasons.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {warning.reasons.map((r, i) => (
                <span
                  key={i}
                  className="rounded-full border border-border-subtle bg-muted px-2.5 py-0.5 text-xs text-muted-foreground"
                >
                  {r}
                </span>
              ))}
            </div>
          )}
          <p className="text-sm">
            <span className="font-medium text-card-foreground">Suggested response: </span>
            <span className="text-muted-foreground">{warning.suggested_response}</span>
          </p>
          {notes && (
            <p className="flex items-start gap-1.5 pt-1 text-xs text-muted-foreground/80">
              <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              {notes}
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
