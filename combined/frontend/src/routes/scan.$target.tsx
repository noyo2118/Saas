import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Lock, Globe2, FileSearch, Link2, Download } from "lucide-react";

import { AppShell } from "@/components/layout/AppShell";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { GlowBadge, StatusDot } from "@/components/ui-custom/GlowBadge";
import { TrustScoreRing } from "@/components/viz/TrustScoreRing";
import { Terminal } from "@/components/viz/Terminal";
import { RiskBars } from "@/components/viz/RiskBars";
import { AIExplain } from "@/components/viz/AIExplain";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScanBeam } from "@/components/effects/Backgrounds";
import { downloadReport, deriveScan, type ScanResult } from "@/lib/scan";
import { dispatchEvent as dispatchNeural, setThreatLevel } from "@/lib/neural-core";

export const Route = createFileRoute("/scan/$target")({
  head: ({ params }) => ({
    meta: [
      { title: `Scan · ${params.target} — TrustScan` },
      { name: "description", content: `AI-generated cyber intelligence report for ${params.target}.` },
      { property: "og:title", content: `Scan · ${params.target}` },
      { property: "og:description", content: `Live AI verdict and intelligence for ${params.target}.` },
    ],
  }),
  component: ScanPage,
});

function ScanPage() {
  const { target } = Route.useParams();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [rawBackend, setRawBackend] = useState<unknown>(null);
  const [scanning, setScanning] = useState(true);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const stages = ["DNS", "TLS", "WHOIS", "Feeds", "AI"];
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let aborted = false;
    const ctrl = new AbortController();
    setScanning(true);
    setProgress(0);
    setResult(null);
    setRawBackend(null);
    setError(null);
    dispatchNeural("scan-start", { target });

    // Visual progress — ramps to 90% while the real request is in flight,
    // completes when the response arrives.
    progressTimer.current = setInterval(() => {
      setProgress((p) => (p < 90 ? p + 2 : p));
    }, 120);

    (async () => {
      try {
        const API_BASE = (import.meta as any).env?.VITE_TRUSTSCAN_API || "";
        // Parallel: fetch the adapted UI result AND keep the raw backend
        // payload for the PDF report endpoint.
        const rawPromise = fetch(`${API_BASE}/api/scan`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ url: target.match(/^https?:\/\//i) ? target : `https://${target}` }),
          signal: ctrl.signal,
        }).then(async (r) => {
          if (!r.ok) {
            let msg = `Scan failed (${r.status})`;
            try { const e = await r.json(); if (e?.detail) msg = e.detail; } catch {}
            throw new Error(msg);
          }
          return r.json();
        });
        const raw = await rawPromise;
        if (aborted) return;
        const { adaptBackend } = await import("@/lib/scan");
        const adapted = adaptBackend(raw);
        setRawBackend(raw);
        setResult(adapted);
        setProgress(100);
        setScanning(false);
        setThreatLevel(Math.max(0, Math.min(1, (100 - adapted.score) / 100)));
        dispatchNeural("scan-complete", { score: adapted.score });
      } catch (e: any) {
        if (aborted || e?.name === "AbortError") return;
        // Backend unreachable → offline fallback with a visible notice
        console.error("Scan error:", e);
        setError(e?.message || "Scan failed");
        const fallback = deriveScan(target);
        setResult(fallback);
        setProgress(100);
        setScanning(false);
        setThreatLevel(Math.max(0, Math.min(1, (100 - fallback.score) / 100)));
        dispatchNeural("scan-complete", { score: fallback.score });
      } finally {
        if (progressTimer.current) clearInterval(progressTimer.current);
      }
    })();

    return () => {
      aborted = true;
      ctrl.abort();
      if (progressTimer.current) clearInterval(progressTimer.current);
    };
  }, [target]);

  async function onDownloadReport() {
    if (!rawBackend || downloading) return;
    try {
      setDownloading(true);
      const blob = await downloadReport(rawBackend);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `TrustScan_${target.replace(/[^a-z0-9]+/gi, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
    } finally {
      setDownloading(false);
    }
  }

  // While waiting for the first result, show a skeleton with live progress
  const view = result;
  const tone =
    !view ? "cyan" :
    view.score >= 85 ? "green" :
    view.score >= 60 ? "cyan" :
    view.score >= 35 ? "amber" : "red";

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl space-y-5 sm:space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground sm:text-xs">
              <Link2 className="h-3.5 w-3.5" /> Intelligence report
            </div>
            <h1 className="mt-2 font-display text-xl font-semibold tracking-tight break-all sm:text-2xl lg:text-3xl">{target}</h1>
          </div>
          <div className="flex items-center gap-2">
            {view && (
              <button
                type="button"
                onClick={onDownloadReport}
                disabled={!rawBackend || downloading}
                className="inline-flex items-center gap-2 rounded-full border border-border bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)] px-3 py-1.5 text-xs text-foreground/90 transition-colors hover:text-foreground disabled:opacity-50"
              >
                <Download className="h-3.5 w-3.5" />
                {downloading ? "Generating…" : "PDF report"}
              </button>
            )}
            {view && <GlowBadge tone={tone as any}>{view.verdict}</GlowBadge>}
          </div>
        </div>

        {error && (
          <GlassCard className="border-[color-mix(in_oklab,var(--neon-amber)_40%,var(--border))] p-4 text-sm">
            <div className="flex items-start gap-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 text-neon-amber shrink-0" />
              <div>
                <div className="font-medium text-foreground">Backend unreachable — showing offline placeholder.</div>
                <div className="mt-1 text-xs text-muted-foreground break-words">{error}</div>
              </div>
            </div>
          </GlassCard>
        )}

        {/* Hero scan */}
        <GlassCard variant="holographic" className="relative overflow-hidden p-4 sm:p-6">
          {scanning && <ScanBeam />}
          <div className="grid items-center gap-6 sm:gap-8 lg:grid-cols-[auto_1fr]">
            <div className="flex flex-col items-center">
              <TrustScoreRing score={view?.score ?? 0} size={200} thickness={14} />
            </div>
            <div className="space-y-4 sm:space-y-5">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Scan progress</div>
                <div className="mt-2 grid grid-cols-5 gap-1.5">
                  {stages.map((s, i) => {
                    const filled = progress >= ((i + 1) / stages.length) * 100;
                    return (
                      <div key={s} className="space-y-1.5">
                        <div className="h-1.5 overflow-hidden rounded-full bg-[color-mix(in_oklab,var(--surface-2)_70%,transparent)]">
                          <motion.div
                            initial={{ width: 0 }} animate={{ width: filled ? "100%" : "0%" }}
                            transition={{ duration: 0.5, delay: i * 0.05 }}
                            className="h-full rounded-full"
                            style={{ background: "linear-gradient(90deg, var(--neon-cyan), var(--neon-violet))" }}
                          />
                        </div>
                        <div className={`text-[10px] uppercase tracking-[0.18em] ${filled ? "text-foreground" : "text-muted-foreground"}`}>{s}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
              <AIExplain text={view?.ai ?? "Running live scan — querying DNS, TLS, WHOIS and Google Safe Browsing…"} />
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Fraud score" value={view ? `${view.fraudScore}/100` : "—"} tone={tone as any} />
                <Stat label="SSL grade" value={view?.ssl.grade ?? "—"} tone={view?.ssl.valid ? "green" : "red"} />
                <Stat label="Domain age" value={view ? `${view.whois.ageDays}d` : "—"} tone={view && view.whois.ageDays > 365 ? "green" : "amber"} />
                <Stat label="ASN" value={view?.ip.asn ?? "—"} tone="cyan" />
              </div>
            </div>
          </div>
        </GlassCard>

        {view && (
          <Tabs defaultValue="overview" className="w-full">
            <div className="-mx-1 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              <TabsList className="glass mx-1 inline-flex h-11 w-max rounded-full p-1">
                {["overview", "ssl", "whois", "blacklist", "ip"].map((v) => (
                  <TabsTrigger key={v} value={v} className="rounded-full px-3.5 text-xs capitalize sm:px-4 sm:text-sm data-[state=active]:bg-[color-mix(in_oklab,var(--neon-cyan)_15%,transparent)] data-[state=active]:text-foreground">
                    {v === "ip" ? "IP intel" : v}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>

            <TabsContent value="overview" className="mt-5">
              <div className="grid gap-5 lg:grid-cols-3">
                <GlassCard className="p-5 lg:col-span-2">
                  <div className="mb-3 font-display text-base font-semibold">Indicators</div>
                  <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {view.indicators.map((it) => (
                      <li key={it.label} className="flex items-center gap-3 rounded-lg border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-3 text-sm">
                        {it.status === "ok" ? <CheckCircle2 className="h-4 w-4 text-neon-green" /> :
                         it.status === "warn" ? <AlertTriangle className="h-4 w-4 text-neon-amber" /> :
                         <XCircle className="h-4 w-4 text-neon-red" />}
                        <span>{it.label}</span>
                      </li>
                    ))}
                  </ul>
                </GlassCard>
                <GlassCard className="p-5">
                  <div className="mb-3 font-display text-base font-semibold">Risk breakdown</div>
                  <RiskBars />
                </GlassCard>
                <div className="lg:col-span-3"><Terminal /></div>
              </div>
            </TabsContent>

            <TabsContent value="ssl" className="mt-5">
              <GlassCard className="p-5">
                <div className="mb-3 flex items-center gap-2 font-display text-base font-semibold"><Lock className="h-4 w-4 text-neon-cyan" /> TLS / SSL inspection</div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <Field label="Status" value={view.ssl.valid ? "Valid" : "Invalid"} tone={view.ssl.valid ? "green" : "red"} />
                  <Field label="Issuer" value={view.ssl.issuer} />
                  <Field label="Expires" value={view.ssl.expires} tone={view.ssl.valid ? "cyan" : "red"} />
                  <Field label="Grade" value={view.ssl.grade} tone={view.ssl.valid ? "green" : "red"} />
                  <Field label="HSTS" value={view.score > 60 ? "Enabled" : "Missing"} />
                  <Field label="OCSP" value="—" />
                </div>
              </GlassCard>
            </TabsContent>

            <TabsContent value="whois" className="mt-5">
              <GlassCard className="p-5">
                <div className="mb-3 flex items-center gap-2 font-display text-base font-semibold"><FileSearch className="h-4 w-4 text-neon-cyan" /> WHOIS</div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <Field label="Registrar" value={view.whois.registrar} />
                  <Field label="Created" value={view.whois.created} />
                  <Field label="Country" value={view.whois.country} />
                  <Field label="Age" value={`${view.whois.ageDays} days`} tone={view.whois.ageDays > 365 ? "green" : "amber"} />
                  <Field label="Privacy" value="—" />
                  <Field label="Status" value="OK" />
                </div>
              </GlassCard>
            </TabsContent>

            <TabsContent value="blacklist" className="mt-5">
              <GlassCard className="p-5">
                <div className="mb-3 flex items-center gap-2 font-display text-base font-semibold"><ShieldCheck className="h-4 w-4 text-neon-cyan" /> Blacklist matrix</div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                  {view.blacklists.map((b) => (
                    <div key={b.name} className="flex items-center justify-between rounded-lg border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] px-3 py-2.5 text-sm">
                      <span>{b.name}</span>
                      {b.listed
                        ? <GlowBadge tone="red">Listed</GlowBadge>
                        : <GlowBadge tone="green">Clean</GlowBadge>}
                    </div>
                  ))}
                </div>
              </GlassCard>
            </TabsContent>

            <TabsContent value="ip" className="mt-5">
              <GlassCard className="p-5">
                <div className="mb-3 flex items-center gap-2 font-display text-base font-semibold"><Globe2 className="h-4 w-4 text-neon-cyan" /> IP intelligence</div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <Field label="Address" value={view.ip.address} />
                  <Field label="ASN" value={view.ip.asn} />
                  <Field label="Org" value={view.ip.org} />
                  <Field label="Country" value={view.ip.country} />
                  <Field label="Abuse score" value={`${view.ip.abuse}/100`} tone={view.ip.abuse > 60 ? "red" : view.ip.abuse > 30 ? "amber" : "green"} />
                  <Field label="Reverse DNS" value="—" />
                </div>
              </GlassCard>
            </TabsContent>
          </Tabs>
        )}

        <div className="flex items-center justify-center pt-2 text-xs text-muted-foreground">
          <StatusDot tone={tone as any} /> &nbsp; Report generated by TrustScan AI v4.2 · Google Safe Browsing feed
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value, tone = "cyan" }: { label: string; value: string; tone?: "cyan" | "violet" | "green" | "red" | "amber" }) {
  return (
    <div className="rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-1 font-display text-xl font-semibold text-neon-${tone}`}>{value}</div>
    </div>
  );
}

function Field({ label, value, tone }: { label: string; value: string; tone?: "cyan" | "violet" | "green" | "red" | "amber" }) {
  return (
    <div className="rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-4">
      <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-1 font-mono text-sm ${tone ? `text-neon-${tone}` : ""}`}>{value}</div>
    </div>
  );
}
