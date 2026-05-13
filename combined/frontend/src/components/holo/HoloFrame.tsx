import * as React from "react";
import { cn } from "@/lib/utils";

type Props = React.HTMLAttributes<HTMLDivElement> & {
  variant?: "default" | "elevated" | "holographic";
  interactive?: boolean;
  /** Show engineered corner brackets. Default true for holographic. */
  corners?: boolean;
};

/**
 * HoloFrame — translucent alloy panel with optional rotating conic rim and
 * engineering corner brackets. Replaces GlassCard. Restrained by default:
 * no constant glow, refraction sweep only on hover.
 */
export const HoloFrame = React.forwardRef<HTMLDivElement, Props>(
  ({ className, variant = "default", interactive = false, corners, children, ...rest }, ref) => {
    const showCorners = corners ?? variant === "holographic";
    const base =
      variant === "elevated"
        ? "alloy-strong"
        : variant === "holographic"
          ? "alloy-strong holo-rim"
          : "alloy";
    return (
      <div
        ref={ref}
        className={cn(
          "relative rounded-2xl",
          base,
          showCorners && "holo-corners",
          interactive && "holo-refract transition-[border-color,transform] duration-500 hover:border-[color-mix(in_oklab,var(--neon-cyan)_30%,var(--alloy-edge))] hover:-translate-y-[2px]",
          className,
        )}
        {...rest}
      >
        {children}
      </div>
    );
  },
);
HoloFrame.displayName = "HoloFrame";
