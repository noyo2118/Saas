import { createFileRoute } from "@tanstack/react-router";
import { BarChart3, Users, DollarSign, Activity } from "lucide-react";

import { AppShell } from "@/components/layout/AppShell";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { GlowBadge } from "@/components/ui-custom/GlowBadge";
import { StatCounter } from "@/components/ui-custom/StatCounter";
import { ThreatAreaChart } from "@/components/viz/ThreatAreaChart";
import { RiskBars } from "@/components/viz/RiskBars";
import { ThreatMap } from "@/components/viz/ThreatMap";

export const Route = createFileRoute("/admin")({
  head: () => ({
    meta: [
      { title: "Admin Analytics — TrustScan" },
      { name: "description", content: "Tenant-wide analytics: usage, revenue, top threats and growth." },
      { property: "og:title", content: "Admin Analytics — TrustScan" },
      { property: "og:description", content: "Operational intelligence for tenant administrators." },
    ],
  }),
  component: AdminPage,
});

const KPIS = [
  { label: "MAU",          value: 28412, icon: Users,      tone: "cyan" as const },
  { label: "Scans / mo",   value: 38400000, icon: Activity, tone: "violet" as const },
  { label: "MRR",          value: 1284000, prefix: "$", icon: DollarSign, tone: "green" as const },
  { label: "Top threats",  value: 1284,  icon: BarChart3,  tone: "amber" as const },
];

function AdminPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
            <BarChart3 className="h-3.5 w-3.5" /> Tenant analytics
          </div>
          <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">Admin analytics</h1>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {KPIS.map((k) => {
            const Icon = k.icon;
            return (
              <GlassCard key={k.label} className="p-5">
                <div className="flex items-center justify-between">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{k.label}</div>
                  <Icon className={`h-4 w-4 text-neon-${k.tone}`} />
                </div>
                <div className="mt-3 font-display text-3xl font-semibold tabular-nums text-gradient">
                  <StatCounter value={k.value} prefix={k.prefix ?? ""} />
                </div>
              </GlassCard>
            );
          })}
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          <GlassCard className="p-5 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Usage trend</div>
              <GlowBadge tone="cyan">+8.4% MoM</GlowBadge>
            </div>
            <ThreatAreaChart height={280} />
          </GlassCard>
          <GlassCard className="p-5">
            <div className="mb-3 font-display text-base font-semibold">Top threat classes</div>
            <RiskBars />
          </GlassCard>
        </div>

        <GlassCard className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-display text-base font-semibold">Customer geography</div>
            <GlowBadge tone="violet">7 regions</GlowBadge>
          </div>
          <ThreatMap height={340} />
        </GlassCard>
      </div>
    </AppShell>
  );
}
