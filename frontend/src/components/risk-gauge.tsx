"use client";

import { motion } from "framer-motion";
import { AnimatedNumber } from "./animated-number";
import { RiskBadge } from "./risk-badge";
import type { RiskLevel } from "@/lib/types";

interface RiskGaugeProps {
  probability: number; // 0-1
  riskLevel: RiskLevel;
  thresholds: { low_medium: number; medium_high: number };
}

const W = 280;
const CX = W / 2;
const CY = 148;
const R = 108;
const STROKE = 20;
const H = CY + STROKE;

/** Screen-space angle convention: 0deg = east, increases clockwise (matches CSS rotate()). Our gauge spans
 * the top semicircle from 180deg (west, value 0) through 270deg (north, value 0.5) to 360deg (east, value 1). */
function pointAt(thetaDeg: number) {
  const t = (thetaDeg * Math.PI) / 180;
  return { x: CX + R * Math.cos(t), y: CY + R * Math.sin(t) };
}

function arcPath(thetaStart: number, thetaEnd: number) {
  const s = pointAt(thetaStart);
  const e = pointAt(thetaEnd);
  const largeArc = Math.abs(thetaEnd - thetaStart) > 180 ? 1 : 0;
  return `M ${s.x} ${s.y} A ${R} ${R} 0 ${largeArc} 1 ${e.x} ${e.y}`;
}

const valueToTheta = (v: number) => 180 + 180 * Math.min(1, Math.max(0, v));

export function RiskGauge({ probability, riskLevel, thresholds }: RiskGaugeProps) {
  const v = Math.min(1, Math.max(0, probability));
  const lowEnd = valueToTheta(thresholds.low_medium);
  const medEnd = valueToTheta(thresholds.medium_high);
  const needleRotation = valueToTheta(v);

  return (
    <div className="flex flex-col items-center">
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Risk gauge showing ${(v * 100).toFixed(1)} percent, ${riskLevel} risk`}>
        <path d={arcPath(180, lowEnd)} fill="none" stroke="var(--color-risk-low)" strokeWidth={STROKE} strokeLinecap="round" />
        <path d={arcPath(lowEnd, medEnd)} fill="none" stroke="var(--color-risk-medium)" strokeWidth={STROKE} />
        <path d={arcPath(medEnd, 360)} fill="none" stroke="var(--color-risk-high)" strokeWidth={STROKE} strokeLinecap="round" />

        {/* threshold tick marks, from the real trained tercile cut-points */}
        {[thresholds.low_medium, thresholds.medium_high].map((t, i) => {
          const theta = valueToTheta(t);
          const inner = { x: CX + (R - STROKE / 2 - 2) * Math.cos((theta * Math.PI) / 180), y: CY + (R - STROKE / 2 - 2) * Math.sin((theta * Math.PI) / 180) };
          const outer = { x: CX + (R + STROKE / 2 + 2) * Math.cos((theta * Math.PI) / 180), y: CY + (R + STROKE / 2 + 2) * Math.sin((theta * Math.PI) / 180) };
          return (
            <line key={i} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} stroke="var(--color-background)" strokeWidth={2} />
          );
        })}

        <motion.line
          x1={CX}
          y1={CY}
          x2={CX + (R - STROKE - 4)}
          y2={CY}
          stroke="var(--color-foreground)"
          strokeWidth={3.5}
          strokeLinecap="round"
          style={{ transformOrigin: `${CX}px ${CY}px` }}
          initial={{ rotate: 180 }}
          animate={{ rotate: needleRotation }}
          transition={{ type: "spring", stiffness: 55, damping: 11 }}
        />
        <circle cx={CX} cy={CY} r={6} fill="var(--color-foreground)" />
        <circle cx={CX} cy={CY} r={2.5} fill="var(--color-background)" />
      </svg>

      <div className="-mt-2 flex flex-col items-center gap-3">
        <AnimatedNumber
          value={v * 100}
          decimals={1}
          suffix="%"
          className="text-5xl font-bold tracking-tight tabular-nums text-foreground"
        />
        <p className="text-xs text-muted-foreground">Predicted probability of high-impact outcome</p>
        <RiskBadge level={riskLevel} />
      </div>
    </div>
  );
}
