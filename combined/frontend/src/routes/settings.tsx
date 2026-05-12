import { createFileRoute } from "@tanstack/react-router";
import { Settings as SettingsIcon, Key, Bell, User, Copy } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { GlassCard } from "@/components/ui-custom/GlassCard";
import { GlowBadge } from "@/components/ui-custom/GlowBadge";
import { NeonButton } from "@/components/ui-custom/NeonButton";
import { Switch } from "@/components/ui/switch";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — TrustScan" },
      { name: "description", content: "Manage your TrustScan profile, API keys and notifications." },
      { property: "og:title", content: "Settings — TrustScan" },
      { property: "og:description", content: "Profile, API keys and notification preferences." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
            <SettingsIcon className="h-3.5 w-3.5" /> Console preferences
          </div>
          <h1 className="mt-2 font-display text-3xl font-semibold tracking-tight">Settings</h1>
        </div>

        <GlassCard className="p-6">
          <SectionTitle icon={User}>Profile</SectionTitle>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Input label="Full name" defaultValue="Maya Okafor" />
            <Input label="Work email" defaultValue="maya@halcyon.bank" />
            <Input label="Organization" defaultValue="Halcyon Bank" />
            <Input label="Role" defaultValue="CISO" />
          </div>
          <div className="mt-5 flex justify-end"><NeonButton size="sm">Save changes</NeonButton></div>
        </GlassCard>

        <GlassCard className="p-6">
          <SectionTitle icon={Key}>API keys</SectionTitle>
          <div className="mt-4 space-y-2">
            {[
              { name: "Production", key: "ts_live_•••••••••••••a8c2", tone: "cyan" as const },
              { name: "Staging",    key: "ts_test_•••••••••••••42de", tone: "violet" as const },
            ].map((k) => (
              <div key={k.name} className="flex items-center justify-between rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] px-4 py-3">
                <div>
                  <div className="text-sm font-medium">{k.name}</div>
                  <div className="font-mono text-xs text-muted-foreground">{k.key}</div>
                </div>
                <div className="flex items-center gap-2">
                  <GlowBadge tone={k.tone}>Active</GlowBadge>
                  <button className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground hover:text-foreground"><Copy className="h-3.5 w-3.5" /></button>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4"><NeonButton variant="ghost" size="sm">+ Generate new key</NeonButton></div>
        </GlassCard>

        <GlassCard className="p-6">
          <SectionTitle icon={Bell}>Notifications</SectionTitle>
          <div className="mt-4 space-y-3">
            {[
              { l: "Critical threat alerts",  d: "Immediate notification on critical verdicts.", on: true },
              { l: "Weekly intelligence digest", d: "Curated AI summary every Monday.", on: true },
              { l: "Sensor anomalies",         d: "Alert when sensor health drops below 99.5%.", on: false },
              { l: "Marketing updates",        d: "Product launches and security research.", on: false },
            ].map((n) => (
              <div key={n.l} className="flex items-center justify-between rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-2)_50%,transparent)] px-4 py-3">
                <div>
                  <div className="text-sm font-medium">{n.l}</div>
                  <div className="text-xs text-muted-foreground">{n.d}</div>
                </div>
                <Switch defaultChecked={n.on} />
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
}

function SectionTitle({ icon: Icon, children }: { icon: typeof User; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 font-display text-base font-semibold">
      <Icon className="h-4 w-4 text-neon-cyan" /> {children}
    </div>
  );
}

function Input({ label, ...rest }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
      <input {...rest}
        className="h-10 w-full rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] px-3 text-sm focus:border-[color-mix(in_oklab,var(--neon-cyan)_50%,var(--border))] focus:outline-none focus:ring-2 focus:ring-[color-mix(in_oklab,var(--neon-cyan)_25%,transparent)]" />
    </label>
  );
}
