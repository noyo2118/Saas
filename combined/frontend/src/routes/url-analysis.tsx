import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Link2, Search, ArrowRight, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { GlowBadge } from "@/components/ui-custom/GlowBadge";
import { NeonButton } from "@/components/ui-custom/NeonButton";
import { Terminal } from "@/components/viz/Terminal";

export const Route = createFileRoute("/url-analysis")({
  head: () => ({
    meta: [
      { title: "URL Phishing Analysis — TrustScan" },
      { name: "description", content: "Inspect any URL for phishing kits, redirects and malicious payloads." },
      { property: "og:title", content: "URL Phishing Analysis — TrustScan" },
      { property: "og:description", content: "Detect phishing kits, redirects and malicious URLs." },
    ],
  }),
  component: URLPage,
});

const REDIRECTS = [
  { url: "https://acme-secure-portal.io/login",        status: 200, ok: true  },
  { url: "https://acme-secure-portal.io/auth/callback",status: 302, ok: true  },
  { url: "http://203.0.113.41/c?ref=acme",              status: 302, ok: false },
  { url: "http://evil-harvest.tk/collect",              status: 200, ok: false },
];

const INDICATORS = [
  { label: "Brand impersonation",   status: "bad" as const, msg: "Mimics 'Acme' login" },
  { label: "Hidden iframe",          status: "warn" as const, msg: "0px iframe to 3rd-party" },
  { label: "Form action mismatch",   status: "bad" as const, msg: "POST to raw IP" },
  { label: "TLS validation",         status: "ok"  as const, msg: "Cert valid · LE R3" },
  { label: "Open redirect",          status: "warn" as const, msg: "Redirect param exposed" },
  { label: "Obfuscated JS",          status: "bad" as const, msg: "Eval(atob(...)) detected" },
];

function URLPage() {
  const [url, setUrl] = useState("https://acme-secure-portal.io/login");
  const nav = useNavigate();
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
            <Link2 className="h-3.5 w-3.5" /> Phishing analysis
          </div>
          <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">URL phishing analysis</h1>
          <p className="text-sm text-muted-foreground">Deep inspection of redirects, payloads and behavioural signals.</p>
        </div>

        <GlassCard variant="holographic" className="p-4">
          <form className="flex flex-wrap items-center gap-2"
            onSubmit={(e) => { e.preventDefault(); nav({ to: "/scan/$target", params: { target: url } }); }}
          >
            <Search className="ml-2 h-4 w-4 text-neon-cyan" />
            <input value={url} onChange={(e) => setUrl(e.target.value)}
              className="flex-1 bg-transparent py-2 font-mono text-xs placeholder:text-muted-foreground focus:outline-none" />
            <NeonButton size="sm" type="submit">Analyse <ArrowRight className="h-4 w-4" /></NeonButton>
          </form>
        </GlassCard>

        <div className="grid gap-5 lg:grid-cols-3">
          <GlassCard className="p-5 lg:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <div className="font-display text-base font-semibold">Redirect chain</div>
              <GlowBadge tone="amber">2 untrusted hops</GlowBadge>
            </div>
            <ol className="relative space-y-3 border-l border-border pl-5">
              {REDIRECTS.map((r, i) => (
                <li key={i} className="relative">
                  <span className={`absolute -left-[27px] top-1.5 h-3 w-3 rounded-full ring-4 ${r.ok ? "bg-neon-cyan ring-neon-cyan/20" : "bg-neon-red ring-neon-red/20"}`} />
                  <div className="flex items-center justify-between rounded-lg border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] px-3 py-2">
                    <span className="truncate font-mono text-xs">{r.url}</span>
                    <span className={`ml-3 font-mono text-xs ${r.ok ? "text-neon-cyan" : "text-neon-red"}`}>{r.status}</span>
                  </div>
                </li>
              ))}
            </ol>
          </GlassCard>

          <GlassCard className="p-5">
            <div className="mb-3 font-display text-base font-semibold">Indicators</div>
            <ul className="space-y-2">
              {INDICATORS.map((it) => (
                <li key={it.label} className="flex items-start gap-3 rounded-lg border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-3 text-sm">
                  {it.status === "ok" ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-neon-green" /> :
                   it.status === "warn" ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-neon-amber" /> :
                   <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-neon-red" />}
                  <div className="min-w-0">
                    <div className="text-foreground">{it.label}</div>
                    <div className="text-xs text-muted-foreground">{it.msg}</div>
                  </div>
                </li>
              ))}
            </ul>
          </GlassCard>
        </div>

        <Terminal />
      </div>
    </AppShell>
  );
}
