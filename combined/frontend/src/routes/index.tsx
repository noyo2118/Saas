import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, Search, Sparkles, ShieldCheck, Brain, Fish, Globe2, Lock, Shield, FileSearch, Quote } from "lucide-react";
import { useState } from "react";

import { MarketingShell } from "@/components/layout/MarketingShell";
import { CyberGrid, VignetteEdges } from "@/components/effects/Backgrounds";
import { ParticleField } from "@/components/effects/ParticleField";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { NeonButton } from "@/components/ui-custom/NeonButton";
import { GlowBadge, StatusDot } from "@/components/ui-custom/GlowBadge";
import { SectionHeader } from "@/components/ui-custom/SectionHeader";
import { ThreatGlobe } from "@/components/viz/ThreatGlobe";
import { TrustScoreRing } from "@/components/viz/TrustScoreRing";
import { ActivityFeed } from "@/components/viz/ActivityFeed";
import { ThreatAreaChart } from "@/components/viz/ThreatAreaChart";
import { Terminal } from "@/components/viz/Terminal";
import { CognitionPulse } from "@/components/intelligence/CognitionPulse";
import { FEATURES, TESTIMONIALS } from "@/lib/mock-data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TrustScan — AI Cyber Threat Intelligence Platform" },
      { name: "description", content: "Detect scam websites, malicious URLs, fraudulent IPs and cyber threats in real time using advanced AI security intelligence." },
      { property: "og:title", content: "TrustScan — AI Cyber Threat Intelligence" },
      { property: "og:description", content: "Real-time AI-powered cyber threat detection." },
    ],
  }),
  component: Landing,
});

const iconMap = { Brain, Fish, Globe2, Lock, Shield, FileSearch } as const;

function Hero() {
  const [target, setTarget] = useState("");
  const navigate = useNavigate();
  return (
    <section className="relative isolate overflow-hidden">
      <CyberGrid />
      <ParticleField />
      <VignetteEdges />

      <div className="relative mx-auto max-w-5xl px-5 pt-14 pb-20 sm:px-6 sm:pt-20 sm:pb-24 md:pt-28">
        <motion.div
          initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto max-w-3xl text-center"
        >
          {/* Instrument label */}
          <div className="mb-5 inline-flex items-center gap-3 rounded-full border border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-1)_55%,transparent)] px-3 py-1 text-[10px] uppercase tracking-[0.28em] text-muted-foreground backdrop-blur">
            <CognitionPulse />
            <span className="hidden sm:inline">Node 07 · Quantum Core · Listening</span>
            <span className="sm:hidden">Quantum Core · Live</span>
          </div>

          <GlowBadge tone="cyan" className="mx-auto"><Sparkles className="h-3 w-3" /> Live · Threat Intelligence v4.2</GlowBadge>

          <h1 className="mt-6 font-display text-[2.4rem] font-semibold leading-[1.02] tracking-tight text-balance sm:text-5xl md:text-6xl lg:text-7xl">
            <span className="text-gradient">AI-Powered</span>{" "}
            <span className="text-foreground">Cyber Threat</span>
            <br />
            <span className="relative inline-block">
              <span className="text-gradient-cyber">Intelligence Platform</span>
              <span
                aria-hidden
                className="absolute -bottom-2 left-1/2 h-px w-3/4 -translate-x-1/2"
                style={{
                  background:
                    "linear-gradient(90deg, transparent, color-mix(in oklab, var(--neon-cyan) 65%, transparent), transparent)",
                }}
              />
            </span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-sm leading-relaxed text-muted-foreground sm:mt-6 sm:text-base md:text-lg text-pretty">
            Detect scam websites, malicious URLs, fraudulent IPs and cyber threats in real time
            using advanced AI security intelligence trusted by governments and global enterprises.
          </p>

          {/* Scan bar */}
          <motion.form
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.7 }}
            onSubmit={(e) => { e.preventDefault(); if (target) navigate({ to: "/scan/$target", params: { target } }); }}
            className="relative mx-auto mt-7 flex max-w-2xl items-center gap-2 rounded-full border border-border bg-[color-mix(in_oklab,var(--surface-1)_70%,transparent)] p-1.5 backdrop-blur-xl shadow-[var(--shadow-elevated)] sm:mt-9"
          >
            <span aria-hidden className="pointer-events-none absolute inset-0 rounded-full glow-border" />
            <div className="flex flex-1 items-center gap-2 pl-3">
              <Search className="h-4 w-4 shrink-0 text-neon-cyan" />
              <input
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="example.com  ·  https://...  ·  203.0.113.41"
                className="h-10 min-w-0 flex-1 bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none sm:h-11"
              />
            </div>
            <NeonButton type="submit" size="sm" className="shrink-0">
              <span className="hidden sm:inline">Scan now</span>
              <ArrowRight className="h-4 w-4" />
            </NeonButton>
          </motion.form>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground sm:mt-5 sm:text-xs">
            <span className="inline-flex items-center gap-2"><StatusDot tone="green" /> 1.24M scans · 24h</span>
            <span className="hidden sm:inline">·</span>
            <span>99.7% accuracy</span>
            <span className="hidden sm:inline">·</span>
            <Link to="/dashboard" className="text-neon-cyan hover:underline">View live dashboard →</Link>
          </div>
        </motion.div>

        {/* Hero visual */}
        <motion.div
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35, duration: 0.9 }}
          className="relative mx-auto mt-14 grid max-w-5xl grid-cols-1 items-center gap-6 sm:mt-20 sm:gap-8 lg:grid-cols-[1.2fr_1fr]"
        >
          <GlassCard variant="holographic" className="relative overflow-hidden p-4 sm:p-6 order-2 lg:order-1">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground sm:text-[11px]">Live · Global threat surface</div>
                <div className="mt-1 truncate font-display text-lg font-semibold sm:text-2xl">Real-time intelligence feed</div>
              </div>
              <GlowBadge tone="green" className="shrink-0">Streaming</GlowBadge>
            </div>
            <div className="mt-5 grid grid-cols-1 gap-3 sm:mt-6 sm:gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)] p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Threats / hour</div>
                <ThreatAreaChart height={110} />
              </div>
              <div>
                <ActivityFeed />
              </div>
            </div>
          </GlassCard>

          <div className="relative order-1 flex flex-col items-center justify-center gap-5 lg:order-2">
            <div className="block sm:hidden">
              <ThreatGlobe size={220} />
            </div>
            <div className="hidden sm:block lg:hidden">
              <ThreatGlobe size={300} />
            </div>
            <div className="hidden lg:block">
              <ThreatGlobe size={340} />
            </div>
            <GlowBadge tone="violet">14 active campaigns</GlowBadge>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function Features() {
  return (
    <section className="relative mx-auto max-w-6xl px-5 py-20 sm:px-6 sm:py-28">
      <SectionHeader
        eyebrow="Capabilities"
        title={<>One platform. <span className="text-gradient-cyber">Every signal.</span></>}
        subtitle="A unified intelligence layer that fuses AI reasoning, threat feeds and behavioural analysis into one verdict."
      />
      <div className="mt-10 grid grid-cols-1 gap-3 sm:mt-14 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f, i) => {
          const Icon = (iconMap as Record<string, typeof Brain>)[f.icon] ?? Shield;
          return (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-10% 0px" }}
              transition={{ delay: i * 0.05, duration: 0.6 }}
            >
              <GlassCard interactive className="h-full p-5 sm:p-6">
                <div className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl sm:h-11 sm:w-11">
                  <span aria-hidden className="absolute inset-0 rounded-xl opacity-60 blur-md" style={{ background: "var(--gradient-cyber)" }} />
                  <span className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-1)_80%,transparent)] sm:h-11 sm:w-11">
                    <Icon className="h-5 w-5 text-neon-cyan" />
                  </span>
                </div>
                <div className="mt-4 font-display text-base font-semibold sm:mt-5 sm:text-lg">{f.title}</div>
                <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}

function DashboardPreview() {
  return (
    <section className="relative mx-auto max-w-6xl px-5 py-16 sm:px-6 sm:py-20">
      <SectionHeader
        eyebrow="Command center"
        title={<>Built for the modern <span className="text-gradient">SOC.</span></>}
        subtitle="An immersive operations interface designed with security analysts, not generic dashboard templates."
      />
      <motion.div
        initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="mt-10 sm:mt-14"
      >
        <GlassCard variant="holographic" className="overflow-hidden p-4 sm:p-6">
          <div className="grid gap-4 sm:gap-5 lg:grid-cols-[1fr_1.4fr]">
            <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-5 sm:p-6">
              <div className="block sm:hidden"><TrustScoreRing score={87} size={170} /></div>
              <div className="hidden sm:block"><TrustScoreRing score={87} size={220} /></div>
              <div className="mt-4 text-center">
                <div className="font-display text-base font-semibold sm:text-lg">acme-secure-portal.io</div>
                <div className="text-[11px] text-muted-foreground sm:text-xs">Last scanned 2s ago · 84 feeds</div>
              </div>
            </div>
            <div className="grid gap-4">
              <div className="rounded-2xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] p-3 sm:p-4">
                <div className="mb-2 flex items-center justify-between text-[10px] uppercase tracking-[0.2em] text-muted-foreground sm:text-xs">
                  <span>Threats over time</span><GlowBadge tone="cyan">Last 7d</GlowBadge>
                </div>
                <ThreatAreaChart height={150} />
              </div>
              <Terminal />
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </section>
  );
}

function Testimonials() {
  return (
    <section className="relative mx-auto max-w-6xl px-5 py-20 sm:px-6 sm:py-28">
      <SectionHeader
        eyebrow="Trusted globally"
        title={<>Operators choose <span className="text-gradient-cyber">TrustScan.</span></>}
      />
      <div className="mt-10 grid gap-3 sm:mt-12 sm:gap-4 md:grid-cols-3">
        {TESTIMONIALS.map((t, i) => {
          const initials = t.name.split(" ").map((p) => p[0]).slice(0, 2).join("");
          return (
            <motion.div key={t.name}
              initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.6 }}
            >
              <GlassCard interactive className="h-full p-5 sm:p-6">
                <div className="flex items-center justify-between">
                  <ShieldCheck className="h-5 w-5 text-neon-cyan" />
                  <Quote className="h-4 w-4 text-muted-foreground/60" />
                </div>
                <p className="mt-4 text-sm leading-relaxed text-foreground/90">"{t.quote}"</p>
                <div className="mt-5 flex items-center gap-3">
                  <span
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[var(--alloy-edge)] text-[11px] font-semibold uppercase tracking-wider text-neon-cyan"
                    style={{ background: "color-mix(in oklab, var(--plasma-blue) 12%, var(--surface-2))" }}
                  >
                    {initials}
                  </span>
                  <div className="text-xs text-muted-foreground">
                    <div className="text-foreground">{t.name}</div>
                    <div>{t.role}</div>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}

function FinalCTA() {
  return (
    <section className="relative mx-auto max-w-6xl px-5 py-16 sm:px-6 sm:py-24">
      <GlassCard variant="holographic" className="relative overflow-hidden p-8 text-center sm:p-12">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            background:
              "radial-gradient(ellipse at center, color-mix(in oklab, var(--plasma-blue) 14%, transparent), transparent 65%)",
          }}
        />
        <div className="relative">
          <h3 className="font-display text-3xl font-semibold leading-tight sm:text-4xl md:text-5xl">
            Bring <span className="text-gradient-cyber">cinematic clarity</span> to your threat surface.
          </h3>
          <p className="mx-auto mt-4 max-w-xl text-sm text-muted-foreground sm:text-base">
            Free for researchers. Ready for the world's most demanding security teams.
          </p>
          <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:mt-8 sm:flex-row">
            <NeonButton asChild className="w-full sm:w-auto">
              <Link to="/login">Sign in <ArrowRight className="h-4 w-4" /></Link>
            </NeonButton>
            <NeonButton variant="ghost" asChild className="w-full sm:w-auto">
              <Link to="/dashboard">Open dashboard</Link>
            </NeonButton>
          </div>
        </div>
      </GlassCard>
    </section>
  );
}

function Landing() {
  return (
    <MarketingShell>
      <Hero />
      <Features />
      <DashboardPreview />
      <Testimonials />
      <FinalCTA />
    </MarketingShell>
  );
}
