import { cn } from "@/lib/utils";

const tones = {
  cyan:   { color: "var(--neon-cyan)" },
  violet: { color: "var(--quantum-violet)" },
  green:  { color: "var(--neon-green)" },
  red:    { color: "var(--signal-crimson)" },
  amber:  { color: "var(--signal-amber)" },
} as const;

export type Tone = keyof typeof tones;

/**
 * GlowBadge — instrument-style pill with a thin tone-tinted rim and a
 * single soft pulse marker. Calm by default.
 */
export function GlowBadge({
  children,
  tone = "cyan",
  className,
}: {
  children: React.ReactNode;
  tone?: Tone;
  className?: string;
}) {
  const c = tones[tone].color;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-[0.14em] backdrop-blur",
        className,
      )}
      style={{
        color: c,
        border: `1px solid color-mix(in oklab, ${c} 32%, var(--alloy-edge))`,
        background: `color-mix(in oklab, ${c} 6%, color-mix(in oklab, var(--surface-1) 50%, transparent))`,
      }}
    >
      <span
        className="block h-1 w-1 rounded-full"
        style={{ background: c, boxShadow: `0 0 6px ${c}` }}
      />
      {children}
    </span>
  );
}

export function StatusDot({ tone = "green", className }: { tone?: Tone; className?: string }) {
  const c = tones[tone].color;
  return (
    <span className={cn("relative inline-flex h-2 w-2", className)}>
      <span
        className="absolute inset-0 rounded-full opacity-50 animate-ping"
        style={{ background: c }}
      />
      <span
        className="relative inline-block h-2 w-2 rounded-full"
        style={{ background: c, boxShadow: `0 0 6px ${c}` }}
      />
    </span>
  );
}
