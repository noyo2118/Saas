import * as React from "react";
import { cn } from "@/lib/utils";
import { Slot } from "@radix-ui/react-slot";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "violet";
  size?: "sm" | "md" | "lg";
  asChild?: boolean;
};

/**
 * NeonButton — restrained instrument-grade action surface. Soft alloy fill
 * with thin energy rim that brightens on hover; no aggressive bloom.
 */
export const NeonButton = React.forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = "primary", size = "md", asChild, children, ...rest }, ref) => {
    const sizes = {
      sm: "h-9 px-4 text-sm",
      md: "h-11 px-6 text-sm",
      lg: "h-12 px-7 text-base",
    }[size];
    const base =
      "group relative inline-flex items-center justify-center gap-2 rounded-full font-medium tracking-tight transition-[transform,border-color,background-color] duration-400 overflow-hidden whitespace-nowrap will-change-transform active:translate-y-[1px]";
    const variants = {
      primary: cn(
        "text-foreground",
        "border border-[color-mix(in_oklab,var(--neon-cyan)_45%,transparent)]",
        "bg-[linear-gradient(180deg,color-mix(in_oklab,var(--plasma-blue)_22%,transparent),color-mix(in_oklab,var(--plasma-blue)_8%,transparent))]",
        "hover:border-[color-mix(in_oklab,var(--neon-cyan)_70%,transparent)]",
        "shadow-[inset_0_1px_0_color-mix(in_oklab,var(--neural-silver)_18%,transparent),0_8px_24px_-12px_color-mix(in_oklab,var(--neon-cyan)_55%,transparent)]",
      ),
      violet: cn(
        "text-foreground",
        "border border-[color-mix(in_oklab,var(--quantum-violet)_45%,transparent)]",
        "bg-[linear-gradient(180deg,color-mix(in_oklab,var(--quantum-violet)_22%,transparent),color-mix(in_oklab,var(--quantum-violet)_8%,transparent))]",
        "hover:border-[color-mix(in_oklab,var(--quantum-violet)_70%,transparent)]",
        "shadow-[inset_0_1px_0_color-mix(in_oklab,var(--neural-silver)_18%,transparent),0_8px_24px_-12px_color-mix(in_oklab,var(--quantum-violet)_55%,transparent)]",
      ),
      ghost: cn(
        "text-foreground/90 border border-[var(--alloy-edge)]",
        "bg-[color-mix(in_oklab,var(--surface-1)_40%,transparent)] backdrop-blur-md",
        "hover:border-[color-mix(in_oklab,var(--neon-cyan)_35%,var(--alloy-edge))] hover:text-foreground",
      ),
    }[variant];
    const renderInner = (content: React.ReactNode) => (
      <>
        <span className="relative z-10 inline-flex items-center gap-2">{content}</span>
        {variant !== "ghost" && (
          <span
            aria-hidden
            className="pointer-events-none absolute inset-0 -translate-x-full transition-transform duration-700 group-hover:translate-x-full"
            style={{
              background:
                "linear-gradient(115deg, transparent 30%, color-mix(in oklab, var(--neural-silver) 18%, transparent) 50%, transparent 70%)",
            }}
          />
        )}
      </>
    );
    if (asChild) {
      const child = React.isValidElement(children)
        ? (children as React.ReactElement<{ children?: React.ReactNode }>)
        : null;
      const childContent = child ? (child.props.children as React.ReactNode) : children;
      return (
        <Slot ref={ref as never} className={cn(base, sizes, variants, className)} {...rest}>
          {child
            ? React.cloneElement(child, undefined, renderInner(childContent))
            : <span>{renderInner(childContent)}</span>}
        </Slot>
      );
    }
    return (
      <button ref={ref} className={cn(base, sizes, variants, className)} {...rest}>
        {renderInner(children)}
      </button>
    );
  },
);
NeonButton.displayName = "NeonButton";
