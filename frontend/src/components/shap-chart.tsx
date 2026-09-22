"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts";
import { motion } from "framer-motion";
import type { ShapFactor } from "@/lib/types";

interface ShapChartProps {
  factors: ShapFactor[];
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: ShapFactor }[] }) {
  if (!active || !payload?.length) return null;
  const f = payload[0].payload;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-xs shadow-md">
      <p className="font-medium text-card-foreground">{f.feature}</p>
      <p className="text-muted-foreground">
        {f.direction} &middot; {f.contribution > 0 ? "+" : ""}
        {f.contribution.toFixed(3)} log-odds
      </p>
    </div>
  );
}

export function ShapChart({ factors }: ShapChartProps) {
  const data = [...factors].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const height = Math.max(180, data.length * 42);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
      style={{ height }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 4 }} barCategoryGap={10}>
          <XAxis type="number" hide domain={["dataMin", "dataMax"]} />
          <YAxis
            type="category"
            dataKey="feature"
            width={190}
            tick={{ fill: "var(--color-muted-foreground)", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine x={0} stroke="var(--color-border)" />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--color-muted)" }} />
          <Bar dataKey="contribution" radius={4} isAnimationActive animationDuration={700}>
            {data.map((f, i) => (
              <Cell key={i} fill={f.direction === "raises risk" ? "var(--color-accent)" : "var(--color-border-grey)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
