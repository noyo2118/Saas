import { cn } from "@/lib/utils";

/**
 * HoloLabel — instrument-style micro label with a leading bracket tick.
 * Use for section eyebrows, field labels, status markers.
 */
export function HoloLabel({
  children,
  className,
  tone = "cyan",
}: {
  children: React.ReactNode;
  className?: string;
  tone?: "cyan" | "violet" | "amber" | "muted";
}) {
  const color =
    tone === "violet" ? "var(--quantum-violet)" :
    tone === "amber" ? "var(--signal-amber)" :
    tone === "muted" ? "color-mix(in oklab, var(--muted-foreground) 80%, transparent)" :
    "var(--neon-cyan)";
  return (
    <span
      className={cn("holo-mono inline-flex items-center gap-1.5", className)}
      style={{ color }}
    >
      <span
        aria-hidden
        style={{
          display: "inline-block",
          width: 8, height: 1,
          background: color,
          boxShadow: `0 0 6px ${color}`,
        }}
      />
      {children}
    </span>
  );
}
