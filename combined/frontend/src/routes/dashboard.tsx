import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Activity, ShieldAlert, Eye, Radar, ArrowUpRight } from "lucide-react";

import { AppShell } from "@/components/layout/AppShell";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { GlowBadge, StatusDot } from "@/components/ui-custom/GlowBadge";
import { StatCounter } from "@/components/ui-custom/StatCounter";
import { TrustScoreRing } from "@/components/viz/TrustScoreRing";
import { ThreatMap } from "@/components/viz/ThreatMap";
import { CyberRadar } from "@/components/viz/CyberRadar";
import { ThreatAreaChart } from "@/components/viz/ThreatAreaChart";
import { ActivityFeed } from "@/components/viz/ActivityFeed";
import { Terminal } from "@/components/viz/Terminal";
import { RiskBars } from "@/components/viz/RiskBars";
import { RECENT_SCANS } from "@/lib/mock-data";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Command Center — TrustScan" },
      { name: "description", content: "Live cyber intelligence command center: trust scores, world threat map, AI activity and streaming logs." },
      { property: "og:title", content: "TrustScan Command Center" },
      { property: "og:description", content: "Real-time threat surface, AI verdicts and live SOC feed." },
    ],
  }),
  component: DashboardPage,
});

const kpis = [
  { label: "Active threats", value: 2841,  tone: "amber" as const, icon: ShieldAlert },
  { label: "Scans today",    value: 187420, tone: "cyan" as const,  icon: Eye },
  { label: "Mean trust",     value: 78,    tone: "green" as const, icon: Activity, suffix: "/100" },
  { label: "Live sensors",   value: 1284,  tone: "violet" as const,icon: Radar },
];

function DashboardPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
              <StatusDot tone="green" /> Live · synced 2s ago
            </div>
            <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">Command center</h1>
            <p className="text-sm text-muted-foreground">Real-time cyber intelligence across your monitored surface.</p>
          </div>
          <div className="flex items-center gap-2">
            <GlowBadge tone="cyan">84 feeds online</GlowBadge>
            <GlowBadge tone="violet">AI v4.2</GlowBadge>
          </div>
        </div>

        {/* KPI strip */}
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {kpis.map((k, i) => {
            const Icon = k.icon;
            return (
              <motion.div key={k.label}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <GlassCard className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{k.label}</div>
                    <Icon className={`h-4 w-4 text-neon-${k.tone}`} />
                  </div>
                  <div className="mt-3 font-display text-3xl font-semibold tabular-nums text-gradient">
                    <StatCounter value={k.value} suffix={k.suffix} />
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>

        {/* Hero row */}
        <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
          <GlassCard variant="holographic" className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Global threat map</div>
                <div className="font-display text-lg font-semibold">7-region telemetry</div>
              </div>
              <GlowBadge tone="cyan">Streaming</GlowBadge>
            </div>
            <ThreatMap height={360} />
          </GlassCard>

          <GlassCard className="flex flex-col items-center justify-center p-6">
            <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Aggregate trust</div>
            <TrustScoreRing score={78} size={220} label="Healthy" />
            <div className="mt-4 grid w-full grid-cols-2 gap-3 text-center">
              <div className="rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-3">
                <div className="text-xs text-muted-foreground">Trusted</div>
                <div className="font-display text-xl font-semibold text-neon-green">62%</div>
              </div>
              <div className="rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-3">
                <div className="text-xs text-muted-foreground">Flagged</div>
                <div className="font-display text-xl font-semibold text-neon-amber">38%</div>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Mid row */}
        <div className="grid gap-5 lg:grid-cols-3">
          <GlassCard className="p-5 lg:col-span-2">
            <div className="mb-2 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Threats vs blocked · 28h</div>
              <GlowBadge tone="cyan">+12.4%</GlowBadge>
            </div>
            <ThreatAreaChart height={260} />
          </GlassCard>

          <GlassCard className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Sensor radar</div>
              <GlowBadge tone="violet">6 anomalies</GlowBadge>
            </div>
            <div className="flex justify-center"><CyberRadar size={220} /></div>
          </GlassCard>
        </div>

        {/* Bottom row */}
        <div className="grid gap-5 lg:grid-cols-3">
          <GlassCard className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Live activity</div>
              <GlowBadge tone="green">Streaming</GlowBadge>
            </div>
            <ActivityFeed />
          </GlassCard>

          <GlassCard className="p-5 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Operator console</div>
              <span className="font-mono text-[11px] text-muted-foreground">trustscan@sentinel:~</span>
            </div>
            <Terminal />
          </GlassCard>
        </div>

        {/* Last row */}
        <div className="grid gap-5 lg:grid-cols-3">
          <GlassCard className="p-5">
            <div className="mb-3 font-display text-base font-semibold">Risk breakdown</div>
            <RiskBars />
          </GlassCard>
          <GlassCard className="p-5 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Recent scans</div>
              <Link to="/dashboard" className="text-xs text-muted-foreground hover:text-foreground">View all</Link>
            </div>
            <div className="overflow-hidden rounded-xl border border-border">
              <table className="w-full text-sm">
                <thead className="bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)] text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 text-left font-normal">Target</th>
                    <th className="px-4 py-2 text-left font-normal">Type</th>
                    <th className="px-4 py-2 text-left font-normal">Score</th>
                    <th className="px-4 py-2 text-left font-normal">Verdict</th>
                    <th className="px-4 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {RECENT_SCANS.map((s) => (
                    <tr key={s.target} className="border-t border-border/70 hover:bg-[color-mix(in_oklab,var(--surface-2)_30%,transparent)]">
                      <td className="px-4 py-3 font-mono text-xs">{s.target}</td>
                      <td className="px-4 py-3 text-muted-foreground">{s.type}</td>
                      <td className="px-4 py-3">
                        <span className={
                          s.score >= 85 ? "text-neon-green" :
                          s.score >= 60 ? "text-neon-cyan" :
                          s.score >= 35 ? "text-neon-amber" : "text-neon-red"
                        }>{s.score}</span>
                      </td>
                      <td className="px-4 py-3">
                        <GlowBadge tone={s.score >= 85 ? "green" : s.score >= 60 ? "cyan" : s.score >= 35 ? "amber" : "red"}>{s.verdict}</GlowBadge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link to="/scan/$target" params={{ target: s.target }} className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
                          Open <ArrowUpRight className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
}
