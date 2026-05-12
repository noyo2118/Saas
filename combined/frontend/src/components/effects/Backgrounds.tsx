import { cn } from "@/lib/utils";

// Legacy backgrounds — kept as no-ops / tame versions so old route imports
// don't break. The global QuantumAtmosphere now provides all ambience.

export function CyberGrid({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("pointer-events-none absolute inset-0 cyber-grid opacity-40", className)}
    />
  );
}

export function Aurora({ className: _className }: { className?: string }) {
  return null;
}

export function NoiseOverlay({ className: _className }: { className?: string }) {
  return null;
}

export function ScanBeam({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("pointer-events-none absolute inset-x-0 top-0 h-24 scan-beam animate-scan-sweep", className)}
    />
  );
}

export function VignetteEdges() {
  return null;
}
