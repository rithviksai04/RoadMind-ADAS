"use client";

import { motion } from "framer-motion";
import { ArrowDown, ArrowUp } from "lucide-react";
import type { ShapFactor } from "@/lib/types";

interface ShapChartProps {
  factors: ShapFactor[];
}

/**
 * Diverging bar list centred on zero: bars to the right raise risk, to the left lower it.
 * Bar length is relative to the largest |contribution| in this prediction.
 */
export function ShapChart({ factors }: ShapChartProps) {
  const data = [...factors].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const maxAbs = Math.max(1e-9, ...data.map((f) => Math.abs(f.contribution)));

  if (!data.length) return <p className="text-sm text-muted-foreground">No contributing factors.</p>;

  return (
    <ul className="space-y-2.5">
      {data.map((f, i) => {
        const up = f.contribution > 0;
        const width = `${(Math.abs(f.contribution) / maxAbs) * 100}%`;
        return (
          <li key={`${f.feature}-${i}`} className="grid grid-cols-1 items-center gap-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] sm:gap-3">
            <span className="flex min-w-0 items-center gap-1.5 text-sm text-foreground" title={f.feature}>
              {up ? (
                <ArrowUp className="size-3.5 shrink-0 text-accent" aria-label="raises risk" />
              ) : (
                <ArrowDown className="size-3.5 shrink-0 text-muted-foreground" aria-label="lowers risk" />
              )}
              <span className="truncate">{f.feature}</span>
            </span>
            <div className="flex items-center gap-2">
              <div className="relative h-5 flex-1">
                <div className="absolute inset-y-0 left-1/2 w-px bg-border" aria-hidden />
                <motion.div
                  className="absolute inset-y-0.5 rounded-sm"
                  style={{
                    background: up ? "var(--color-accent)" : "var(--color-border-grey)",
                    [up ? "left" : "right"]: "50%",
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `calc(${width} / 2)` }}
                  transition={{ duration: 0.6, delay: 0.05 * i, ease: [0.16, 1, 0.3, 1] }}
                />
              </div>
              <span className={`w-12 text-right text-xs tabular-nums ${up ? "text-accent" : "text-muted-foreground"}`}>
                {up ? "+" : ""}
                {f.contribution.toFixed(2)}
              </span>
            </div>
          </li>
        );
      })}
      <li className="flex justify-between pt-1 text-[11px] text-muted-foreground">
        <span>Values are log-odds</span>
        <span>← lowers risk · raises risk →</span>
      </li>
    </ul>
  );
}
