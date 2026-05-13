import * as React from "react";
import { cn } from "@/lib/utils";

type Props = React.HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "elevated" | "holographic";
  interactive?: boolean;
};

/**
 * GlassCard — backwards-compatible API that now renders translucent alloy
 * panels with engineered corner brackets and an optional rotating conic rim.
 * No constant glow, no heavy bloom — restraint by default.
 */
export const GlassCard = React.forwardRef<HTMLDivElement, Props>(
  ({ className, variant = "default", interactive = false, children, ...rest }, ref) => {
    const isHolo = variant === "holographic";
    const base =
      variant === "elevated"
        ? "alloy-strong"
        : isHolo
          ? "alloy-strong holo-rim"
          : "alloy";
    return (
      <div
        ref={ref}
        className={cn(
          "relative rounded-2xl",
          base,
          isHolo && "holo-corners",
          interactive &&
            "holo-refract transition-[border-color,transform] duration-500 hover:-translate-y-[2px] hover:border-[color-mix(in_oklab,var(--neon-cyan)_28%,var(--alloy-edge))]",
          className,
        )}
        {...rest}
      >
        {children}
      </div>
    );
  },
);
GlassCard.displayName = "GlassCard";
