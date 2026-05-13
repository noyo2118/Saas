import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Globe2, Search } from "lucide-react";
import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { GlowBadge } from "@/components/ui-custom/GlowBadge";
import { NeonButton } from "@/components/ui-custom/NeonButton";
import { ThreatMap } from "@/components/viz/ThreatMap";
import { CyberRadar } from "@/components/viz/CyberRadar";
import { ThreatAreaChart } from "@/components/viz/ThreatAreaChart";

export const Route = createFileRoute("/ip-intelligence")({
  head: () => ({
    meta: [
      { title: "IP Intelligence — TrustScan" },
      { name: "description", content: "Lookup any IP for ASN, geo-location, abuse history and botnet correlation." },
      { property: "og:title", content: "IP Intelligence — TrustScan" },
      { property: "og:description", content: "Real-time IP reputation and forensics." },
    ],
  }),
  component: IPPage,
});

const SAMPLE = [
  { ip: "203.0.113.41",  asn: "AS13335", org: "Cloudflare",  country: "US", abuse: 84, tag: "Botnet C2" },
  { ip: "198.51.100.77", asn: "AS16509", org: "AWS",         country: "DE", abuse: 71, tag: "Phishing host" },
  { ip: "192.0.2.18",    asn: "AS14061", org: "DigitalOcean",country: "FR", abuse: 12, tag: "Clean" },
  { ip: "203.0.113.221", asn: "AS9009",  org: "M247",        country: "RU", abuse: 92, tag: "Malware C2" },
];

function IPPage() {
  const nav = useNavigate();
  const [ip, setIp] = useState("203.0.113.41");
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
            <Globe2 className="h-3.5 w-3.5" /> Forensic lookup
          </div>
          <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">IP intelligence</h1>
          <p className="text-sm text-muted-foreground">Resolve any IP into ASN, geo, abuse and behaviour signals.</p>
        </div>

        <GlassCard variant="holographic" className="p-4">
          <form
            className="flex flex-wrap items-center gap-2"
            onSubmit={(e) => { e.preventDefault(); nav({ to: "/scan/$target", params: { target: ip } }); }}
          >
            <Search className="ml-2 h-4 w-4 text-neon-cyan" />
            <input
              value={ip} onChange={(e) => setIp(e.target.value)}
              placeholder="203.0.113.41"
              className="flex-1 bg-transparent py-2 font-mono text-sm placeholder:text-muted-foreground focus:outline-none"
            />
            <NeonButton size="sm" type="submit">Lookup</NeonButton>
          </form>
        </GlassCard>

        <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
          <GlassCard className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Geo distribution</div>
              <GlowBadge tone="cyan">7 regions</GlowBadge>
            </div>
            <ThreatMap height={340} />
          </GlassCard>
          <GlassCard className="p-5">
            <div className="mb-3 font-display text-base font-semibold">Abuse history (90d)</div>
            <ThreatAreaChart height={260} />
          </GlassCard>
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          <GlassCard className="p-5 lg:col-span-2">
            <div className="mb-3 font-display text-base font-semibold">Recent flagged IPs</div>
            <div className="overflow-hidden rounded-xl border border-border">
              <table className="w-full text-sm">
                <thead className="bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)] text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 text-left font-normal">IP</th>
                    <th className="px-4 py-2 text-left font-normal">ASN · Org</th>
                    <th className="px-4 py-2 text-left font-normal">Country</th>
                    <th className="px-4 py-2 text-left font-normal">Abuse</th>
                    <th className="px-4 py-2 text-left font-normal">Tag</th>
                  </tr>
                </thead>
                <tbody>
                  {SAMPLE.map((r) => (
                    <tr key={r.ip} className="border-t border-border/70 hover:bg-[color-mix(in_oklab,var(--surface-2)_30%,transparent)]">
                      <td className="px-4 py-3 font-mono text-xs">{r.ip}</td>
                      <td className="px-4 py-3 text-muted-foreground">{r.asn} · {r.org}</td>
                      <td className="px-4 py-3">{r.country}</td>
                      <td className={`px-4 py-3 font-mono ${r.abuse > 70 ? "text-neon-red" : r.abuse > 30 ? "text-neon-amber" : "text-neon-green"}`}>{r.abuse}/100</td>
                      <td className="px-4 py-3"><GlowBadge tone={r.abuse > 70 ? "red" : r.abuse > 30 ? "amber" : "green"}>{r.tag}</GlowBadge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
          <GlassCard className="p-5">
            <div className="mb-3 font-display text-base font-semibold">Sensor radar</div>
            <div className="flex justify-center"><CyberRadar size={220} /></div>
          </GlassCard>
        </div>
      </div>
    </AppShell>
  );
}
