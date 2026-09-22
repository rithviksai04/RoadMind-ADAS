import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/lib/types";

const CONFIG: Record<RiskLevel, { label: string; icon: typeof ShieldCheck; bg: string; text: string }> = {
  LOW: { label: "LOW RISK", icon: ShieldCheck, bg: "bg-risk-low", text: "text-white" },
  MEDIUM: { label: "MEDIUM RISK", icon: AlertTriangle, bg: "bg-risk-medium", text: "text-white" },
  HIGH: { label: "HIGH RISK", icon: ShieldAlert, bg: "bg-risk-high", text: "text-white" },
};

export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  const c = CONFIG[level];
  const Icon = c.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-semibold tracking-wide shadow-sm",
        c.bg,
        c.text,
        className
      )}
    >
      <Icon className="size-4" strokeWidth={2.25} aria-hidden />
      {c.label}
    </span>
  );
}

export const RISK_COLOR: Record<RiskLevel, string> = {
  LOW: "var(--color-risk-low)",
  MEDIUM: "var(--color-risk-medium)",
  HIGH: "var(--color-risk-high)",
};
