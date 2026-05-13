import { Link, useRouterState, useRouter } from "@tanstack/react-router";
import { ArrowLeft, Menu, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { StatusDot } from "@/components/ui-custom/GlowBadge";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const links = [
  { to: "/", label: "Platform" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/url-analysis", label: "URL analysis" },
  { to: "/ip-intelligence", label: "IP intelligence" },
];

export function MarketingNav() {
  const path = useRouterState({ select: (s) => s.location.pathname });
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const isHome = path === "/";

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 32);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className="fixed inset-x-0 top-3 z-50 flex justify-center px-3 sm:top-4 sm:px-4">
      <nav
        className={`glass flex w-full max-w-6xl items-center justify-between rounded-full px-3 py-2 transition-[border-color,background-color,box-shadow] duration-500 sm:px-4 sm:py-2.5 ${
          scrolled
            ? "border-[color-mix(in_oklab,var(--neon-cyan)_28%,var(--alloy-edge))] shadow-[var(--shadow-elevated)]"
            : "shadow-[0_4px_24px_-12px_color-mix(in_oklab,var(--plasma-blue)_40%,transparent)]"
        }`}
      >
        <div className="flex items-center gap-2">
          {!isHome && (
            <button
              type="button"
              aria-label="Go back"
              onClick={() => (window.history.length > 1 ? router.history.back() : router.navigate({ to: "/" }))}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] text-foreground/80 transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          )}
          <Link to="/" className="flex items-center gap-2 pl-1">
            <div className="relative">
              <div className="absolute inset-0 rounded-md blur-md opacity-70" style={{ background: "var(--gradient-cyber)" }} />
              <div className="relative flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet">
                <Shield className="h-4 w-4 text-primary-foreground" />
              </div>
            </div>
            <span className="font-display text-base font-semibold tracking-tight">TrustScan</span>
          </Link>
        </div>

        <ul className="hidden items-center gap-1 lg:flex">
          {links.slice(0, 3).map((l) => {
            const active = path === l.to;
            return (
              <li key={l.to}>
                <Link
                  to={l.to}
                  className={`rounded-full px-3.5 py-1.5 text-sm transition-colors ${
                    active
                      ? "text-foreground bg-[color-mix(in_oklab,var(--surface-2)_70%,transparent)]"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {l.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="hidden rounded-full border border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] px-4 py-1.5 text-sm text-foreground/85 transition-colors hover:text-foreground sm:inline-block"
          >
            Sign in
          </Link>

          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <button
                aria-label="Open menu"
                className="flex h-9 w-9 items-center justify-center rounded-full border border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] text-foreground/80 transition-colors hover:text-foreground lg:hidden"
              >
                <Menu className="h-4 w-4" />
              </button>
            </SheetTrigger>
            <SheetContent
              side="right"
              className="w-[300px] border-l border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-1)_92%,transparent)] backdrop-blur-2xl"
            >
              <div className="mb-6 flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet">
                  <Shield className="h-4 w-4 text-primary-foreground" />
                </div>
                <span className="font-display text-base font-semibold tracking-tight">TrustScan</span>
              </div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)] px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                <StatusDot tone="green" /> Quantum core · operational
              </div>
              <nav className="flex flex-col">
                {links.map((l) => {
                  const active = path === l.to;
                  return (
                    <Link
                      key={l.to}
                      to={l.to}
                      onClick={() => setOpen(false)}
                      className={`flex items-center justify-between border-b border-[var(--alloy-edge)] px-1 py-3 text-sm transition-colors ${
                        active ? "text-neon-cyan" : "text-foreground/85 hover:text-foreground"
                      }`}
                    >
                      <span>{l.label}</span>
                      <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                        {String(links.indexOf(l) + 1).padStart(2, "0")}
                      </span>
                    </Link>
                  );
                })}
                <Link
                  to="/login"
                  onClick={() => setOpen(false)}
                  className="mt-6 text-sm text-neon-cyan hover:underline"
                >
                  Sign in →
                </Link>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  );
}

export function MarketingFooter() {
  const cols = [
    { title: "Platform", items: [
      { label: "Dashboard", to: "/dashboard" },
      { label: "URL analysis", to: "/url-analysis" },
      { label: "IP intelligence", to: "/ip-intelligence" },
    ]},
    { title: "Account", items: [
      { label: "Sign in", to: "/login" },
      { label: "Settings", to: "/settings" },
      { label: "Admin", to: "/admin" },
    ]},
  ] as const;
  return (
    <footer className="relative mt-24 sm:mt-32">
      <div
        aria-hidden
        className="absolute inset-x-0 top-0 h-px"
        style={{
          background:
            "linear-gradient(90deg, transparent, color-mix(in oklab, var(--neon-cyan) 45%, transparent), transparent)",
        }}
      />
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-14 sm:py-16 md:grid-cols-4">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-neon-cyan to-neon-violet">
              <Shield className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-display text-base font-semibold">TrustScan</span>
          </div>
          <p className="mt-4 max-w-sm text-sm text-muted-foreground">
            AI-powered cyber threat intelligence for governments, researchers and global enterprises.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-[var(--alloy-edge)] bg-[color-mix(in_oklab,var(--surface-2)_60%,transparent)] px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
            <StatusDot tone="green" /> All systems operational
          </div>
        </div>
        {cols.map((c) => (
          <div key={c.title}>
            <div className="mb-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">{c.title}</div>
            <ul className="space-y-2 text-sm">
              {c.items.map((i) => (
                <li key={i.label}>
                  <Link
                    to={i.to}
                    className="text-foreground/80 transition-colors hover:text-foreground"
                  >
                    {i.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-[var(--alloy-edge)] py-5 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} TrustScan Intelligence · All signals reserved.
      </div>
    </footer>
  );
}

export function MarketingShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <MarketingNav />
      <main className="pt-20 sm:pt-24">{children}</main>
      <MarketingFooter />
    </div>
  );
}
