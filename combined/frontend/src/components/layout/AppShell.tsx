import { Link, useRouter, useRouterState } from "@tanstack/react-router";
import { ArrowLeft, LayoutDashboard, Globe2, Link2, Settings, BarChart3, Shield, Search, Bell, ShieldCheck } from "lucide-react";
import { StatusDot } from "@/components/ui-custom/GlowBadge";
import { CognitionPulse } from "@/components/intelligence/CognitionPulse";
import { useState } from "react";

const nav = [
  { to: "/dashboard",       label: "Command center", icon: LayoutDashboard },
  { to: "/url-analysis",    label: "URL analysis",   icon: Link2 },
  { to: "/ip-intelligence", label: "IP intelligence",icon: Globe2 },
  { to: "/admin",           label: "Analytics",      icon: BarChart3 },
  { to: "/settings",        label: "Settings",       icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = useRouterState({ select: (s) => s.location.pathname });
  const router = useRouter();
  const [q, setQ] = useState("");

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-border glass-strong lg:flex">
        <div className="flex h-16 items-center gap-2 border-b border-border px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet">
            <Shield className="h-4 w-4 text-primary-foreground" />
          </div>
          <div className="leading-tight">
            <div className="font-display text-sm font-semibold">TrustScan</div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Sentinel · v4.2</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {nav.map((n) => {
            const active = path === n.to;
            const Icon = n.icon;
            return (
              <Link
                key={n.to}
                to={n.to}
                className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? "bg-[color-mix(in_oklab,var(--neon-cyan)_10%,transparent)] text-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)]"
                }`}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-r bg-neon-cyan shadow-[0_0_8px_var(--neon-cyan)]" />
                )}
                <Icon className={`h-4 w-4 ${active ? "text-neon-cyan" : ""}`} />
                <span>{n.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="m-3 rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_70%,transparent)] p-3">
          <div className="flex items-center gap-2 text-xs">
            <StatusDot tone="green" />
            <span className="text-muted-foreground">All sensors nominal</span>
          </div>
          <div className="mt-2 flex items-end justify-between">
            <div>
              <div className="font-display text-xl font-semibold text-neon-green">99.7%</div>
              <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Uptime · 90d</div>
            </div>
            <ShieldCheck className="h-6 w-6 text-neon-green/80" />
          </div>
        </div>
      </aside>

      <div className="relative lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-[color-mix(in_oklab,var(--background)_70%,transparent)] px-4 backdrop-blur-xl md:px-6">
          <button
            type="button"
            aria-label="Go back"
            onClick={() => (window.history.length > 1 ? router.history.back() : router.navigate({ to: "/" }))}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border text-foreground/80 transition-colors hover:text-foreground lg:hidden"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <Link to="/" className="lg:hidden flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-display text-sm font-semibold">TrustScan</span>
          </Link>
          <form
            className="relative flex flex-1 items-center"
            onSubmit={(e) => {
              e.preventDefault();
              if (!q) return;
              window.location.href = `/scan/${encodeURIComponent(q)}`;
            }}
          >
            <Search className="pointer-events-none absolute left-3 h-4 w-4 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Scan a URL, domain or IP…"
              className="h-10 w-full rounded-full border border-border bg-[color-mix(in_oklab,var(--surface-1)_70%,transparent)] pl-9 pr-32 text-sm placeholder:text-muted-foreground focus:border-[color-mix(in_oklab,var(--neon-cyan)_50%,var(--border))] focus:outline-none focus:ring-2 focus:ring-[color-mix(in_oklab,var(--neon-cyan)_25%,transparent)]"
            />
            <kbd className="pointer-events-none absolute right-3 hidden rounded-md border border-border bg-[color-mix(in_oklab,var(--surface-2)_80%,transparent)] px-2 py-0.5 text-[10px] text-muted-foreground sm:inline">⌘K</kbd>
          </form>
          <div className="hidden items-center gap-2 rounded-full border border-border px-3 py-1.5 md:flex" title="Neural Core synchronized">
            <CognitionPulse />
            <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Neural</span>
          </div>
          <button className="flex h-10 w-10 items-center justify-center rounded-full border border-border text-muted-foreground hover:text-foreground">
            <Bell className="h-4 w-4" />
          </button>
          <div className="flex h-10 items-center gap-2 rounded-full border border-border px-1 pr-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-neon-violet to-neon-cyan text-xs font-semibold text-primary-foreground">MO</div>
            <span className="hidden text-xs text-muted-foreground sm:inline">Maya · Admin</span>
          </div>
        </header>
        <main className="px-4 py-6 md:px-6 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
