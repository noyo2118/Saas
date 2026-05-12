// Minimal stub — TrustScan uses Recharts directly via custom viz components.
// The original shadcn chart wrapper is incompatible with Recharts v3 typings.
import * as React from "react";

export type ChartConfig = Record<string, { label?: string; color?: string; icon?: React.ComponentType }>;

export function ChartContainer({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
  config?: ChartConfig;
  id?: string;
}) {
  return <div className={className}>{children}</div>;
}

export const ChartTooltip = (() => null) as unknown as React.FC<unknown>;
export const ChartTooltipContent = (() => null) as unknown as React.FC<unknown>;
export const ChartLegend = (() => null) as unknown as React.FC<unknown>;
export const ChartLegendContent = (() => null) as unknown as React.FC<unknown>;
export const ChartStyle = (() => null) as unknown as React.FC<unknown>;
