import { Area, AreaChart as RAreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { THREAT_SERIES } from "@/lib/mock-data";

export function ThreatAreaChart({ height = 240 }: { height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RAreaChart data={THREAT_SERIES} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--neon-cyan)" stopOpacity={0.55} />
            <stop offset="100%" stopColor="var(--neon-cyan)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--neon-violet)" stopOpacity={0.45} />
            <stop offset="100%" stopColor="var(--neon-violet)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="color-mix(in oklab, var(--foreground) 8%, transparent)" vertical={false} />
        <XAxis dataKey="t" stroke="var(--muted-foreground)" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
        <YAxis stroke="var(--muted-foreground)" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{
            background: "color-mix(in oklab, var(--surface-1) 90%, transparent)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            backdropFilter: "blur(12px)",
            color: "var(--foreground)",
            fontSize: 12,
          }}
          cursor={{ stroke: "var(--neon-cyan)", strokeOpacity: 0.4 }}
        />
        <Area type="monotone" dataKey="threats" stroke="var(--neon-cyan)" strokeWidth={2} fill="url(#g1)" />
        <Area type="monotone" dataKey="blocked" stroke="var(--neon-violet)" strokeWidth={2} fill="url(#g2)" />
      </RAreaChart>
    </ResponsiveContainer>
  );
}
