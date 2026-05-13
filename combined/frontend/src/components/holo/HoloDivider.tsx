import { cn } from "@/lib/utils";

/**
 * HoloDivider — segmented horizontal line with a single heartbeat-driven
 * traveling pulse.
 */
export function HoloDivider({ className }: { className?: string }) {
  return <div aria-hidden className={cn("holo-pulse-line my-4", className)} />;
}
