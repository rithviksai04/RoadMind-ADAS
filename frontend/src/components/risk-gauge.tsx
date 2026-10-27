"use client";

import { useEffect } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";
import { AnimatedNumber } from "./animated-number";
import { RiskBadge } from "./risk-badge";
import type { RiskLevel } from "@/lib/types";

interface RiskGaugeProps {
  probability: number; // 0-1
  riskLevel: RiskLevel;
  thresholds: { low_medium: number; medium_high: number };
}

const W = 300;
const CX = W / 2;
const CY = 158;
const R = 118;
const STROKE = 18;
const H = CY + 26;
const NEEDLE = R - STROKE - 6;

/**
 * Piecewise scale: each risk tier gets an equal third of the dial.
 * The model's tier thresholds are low (~0.11 / ~0.23), so a linear 0-1 dial packs Low + Medium into
 * the first quarter and the needle hardly moves. Mapping by tier keeps the dial readable and makes the
 * needle land in the zone that matches the badge.
 */
function makeScale(lowMed: number, medHigh: number) {
  const a = Math.min(Math.max(lowMed, 1e-6), 1);
  const b = Math.min(Math.max(medHigh, a + 1e-6), 1);
  return (p: number) => {
    const v = Math.min(1, Math.max(0, p));
    if (v < a) return (v / a) / 3;
    if (v < b) return 1 / 3 + ((v - a) / (b - a)) / 3;
    return 2 / 3 + (b >= 1 ? 1 : (v - b) / (1 - b)) / 3;
  };
}

/** Dial position 0..1 -> point on the top semicircle (0 = left, 1 = right). */
function point(pos: number, radius: number) {
  const t = Math.PI * (1 - pos); // pi (left) -> 0 (right), measured counter-clockwise from east
  return { x: CX + radius * Math.cos(t), y: CY - radius * Math.sin(t) };
}

function arc(from: number, to: number) {
  const s = point(from, R);
  const e = point(to, R);
  return `M ${s.x} ${s.y} A ${R} ${R} 0 0 1 ${e.x} ${e.y}`;
}

const pct = (v: number) => `${(v * 100).toFixed(v < 0.1 ? 1 : 0)}%`;

export function RiskGauge({ probability, riskLevel, thresholds }: RiskGaugeProps) {
  const v = Math.min(1, Math.max(0, probability));
  const scale = makeScale(thresholds.low_medium, thresholds.medium_high);
  const target = scale(v);

  // Animate the dial position itself, then derive the needle tip from it - no CSS transform-origin games.
  const pos = useMotionValue(0);
  useEffect(() => {
    const c = animate(pos, target, { type: "spring", stiffness: 60, damping: 13 });
    return () => c.stop();
  }, [pos, target]);
  const x2 = useTransform(pos, (p) => point(Math.min(1.02, Math.max(-0.02, p)), NEEDLE).x);
  const y2 = useTransform(pos, (p) => point(Math.min(1.02, Math.max(-0.02, p)), NEEDLE).y);

  const ticks = [
    { at: 1 / 3, label: pct(thresholds.low_medium) },
    { at: 2 / 3, label: pct(thresholds.medium_high) },
  ];
  const zones = [
    { from: 0, to: 1 / 3, color: "var(--color-risk-low)", level: "LOW" as const, name: "Low" },
    { from: 1 / 3, to: 2 / 3, color: "var(--color-risk-medium)", level: "MEDIUM" as const, name: "Medium" },
    { from: 2 / 3, to: 1, color: "var(--color-risk-high)", level: "HIGH" as const, name: "High" },
  ];

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full max-w-[320px]"
        role="img"
        aria-label={`Risk meter: ${(v * 100).toFixed(1)} percent, ${riskLevel.toLowerCase()} risk`}
      >
        {/* background track */}
        <path d={arc(0, 1)} fill="none" stroke="var(--color-muted)" strokeWidth={STROKE + 6} strokeLinecap="round" />
        {zones.map((z) => (
          <path
            key={z.level}
            d={arc(z.from, z.to)}
            fill="none"
            stroke={z.color}
            strokeWidth={STROKE}
            opacity={z.level === riskLevel ? 1 : 0.35}
            style={{ transition: "opacity 400ms ease" }}
          />
        ))}

        {/* tier boundaries = the model's real tercile thresholds */}
        {ticks.map((t) => {
          const inner = point(t.at, R - STROKE / 2 - 1);
          const outer = point(t.at, R + STROKE / 2 + 1);
          const lbl = point(t.at, R + STROKE / 2 + 13);
          return (
            <g key={t.at}>
              <line x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} stroke="var(--color-card)" strokeWidth={3} />
              <text x={lbl.x} y={lbl.y} textAnchor="middle" dominantBaseline="middle" className="fill-muted-foreground text-[10px] tabular-nums">
                {t.label}
              </text>
            </g>
          );
        })}
        <text x={point(0, R).x} y={CY + 18} textAnchor="middle" className="fill-muted-foreground text-[10px]">0%</text>
        <text x={point(1, R).x} y={CY + 18} textAnchor="middle" className="fill-muted-foreground text-[10px]">100%</text>

        {/* needle */}
        <motion.line
          x1={CX}
          y1={CY}
          x2={x2}
          y2={y2}
          stroke="var(--color-foreground)"
          strokeWidth={4}
          strokeLinecap="round"
        />
        <circle cx={CX} cy={CY} r={8} fill="var(--color-foreground)" />
        <circle cx={CX} cy={CY} r={3} fill="var(--color-card)" />
      </svg>

      <div className="-mt-1 flex flex-col items-center gap-2">
        <AnimatedNumber
          value={v * 100}
          decimals={1}
          suffix="%"
          className="text-5xl font-bold tracking-tight tabular-nums text-foreground"
        />
        <p className="max-w-xs text-center text-xs text-muted-foreground">
          Chance that an accident here would cause a high traffic impact
        </p>
        <RiskBadge level={riskLevel} className="mt-1" />
      </div>

      <div className="mt-5 grid w-full max-w-sm grid-cols-3 gap-2 text-center text-[11px]">
        {zones.map((z, i) => (
          <div
            key={z.level}
            className={`rounded-md border px-2 py-1.5 transition-colors ${z.level === riskLevel ? "border-transparent bg-muted text-foreground" : "border-border-subtle text-muted-foreground"}`}
          >
            <span className="mr-1 inline-block size-2 rounded-full align-middle" style={{ background: z.color }} />
            <span className="font-medium">{z.name}</span>
            <div className="tabular-nums opacity-80">
              {i === 0 ? `< ${pct(thresholds.low_medium)}` : i === 1 ? `${pct(thresholds.low_medium)}–${pct(thresholds.medium_high)}` : `≥ ${pct(thresholds.medium_high)}`}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
