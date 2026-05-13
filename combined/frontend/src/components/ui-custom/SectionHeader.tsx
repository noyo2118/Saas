import { cn } from "@/lib/utils";

export function SectionHeader({
  eyebrow,
  title,
  subtitle,
  align = "center",
  className,
}: {
  eyebrow?: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  align?: "center" | "left";
  className?: string;
}) {
  return (
    <div
      className={cn(
        "max-w-3xl",
        align === "center" ? "mx-auto text-center" : "text-left",
        className,
      )}
    >
      {eyebrow && (
        <div
          className={cn(
            "inline-flex items-center gap-2 rounded-full border border-border bg-[color-mix(in_oklab,var(--surface-1)_70%,transparent)] px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-neon-cyan backdrop-blur",
          )}
        >
          <span className="h-1 w-1 rounded-full bg-neon-cyan" />
          {eyebrow}
        </div>
      )}
      <h2 className="mt-5 font-display text-3xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-4xl md:text-5xl">
        {title}
      </h2>
      {subtitle && (
        <p className="mt-4 text-base leading-relaxed text-muted-foreground md:text-lg text-pretty">
          {subtitle}
        </p>
      )}
    </div>
  );
}
