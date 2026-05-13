import { motion, useInView, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { OrbitingSignals } from "@/components/holo/OrbitingSignals";

/**
 * TrustScoreRing — three concentric segmented rings rotating at differing
 * rates around a quantum core. Score arc reveals once on enter; rings
 * communicate ongoing computation.
 */
export function TrustScoreRing({
  score,
  size = 220,
  thickness = 14,
  className,
  label,
}: {
  score: number;
  size?: number;
  thickness?: number;
  className?: string;
  label?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-10% 0px" });
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const mv = useMotionValue(0);
  const dash = useTransform(mv, (v) => `${(v / 100) * c} ${c}`);
  const display = useTransform(mv, (v) => Math.round(v).toString());

  useEffect(() => {
    if (inView) animate(mv, score, { duration: 1.6, ease: [0.16, 1, 0.3, 1] });
  }, [inView, score, mv]);

  const tone =
    score >= 85 ? "var(--neon-green)" :
    score >= 60 ? "var(--neon-cyan)"  :
    score >= 35 ? "var(--signal-amber)" : "var(--signal-crimson)";

  const verdict =
    score >= 85 ? "Trusted" :
    score >= 60 ? "Suspicious" :
    score >= 35 ? "High risk" : "Critical";

  // Outer decorative ring radii
  const r2 = r + thickness * 0.9;
  const r3 = r + thickness * 1.8;

  // Tick marks (segmented quantum dial) — 60 ticks
  const ticks = Array.from({ length: 60 });

  return (
    <div ref={ref} className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size + 40, height: size + 40 }}>
      <div
        aria-hidden
        className="absolute inset-0 rounded-full blur-3xl opacity-40"
        style={{ background: `radial-gradient(circle, ${tone}, transparent 60%)` }}
      />

      {/* Outer slow ring with ticks */}
      <svg
        width={size + 40} height={size + 40}
        className="absolute inset-0 animate-orbit-slow"
        style={{ transformOrigin: "center" }}
      >
        <g transform={`translate(${(size + 40) / 2} ${(size + 40) / 2})`}>
          {ticks.map((_, i) => {
            const a = (i / ticks.length) * Math.PI * 2;
            const r1a = r3;
            const r1b = r3 + (i % 5 === 0 ? 6 : 3);
            return (
              <line
                key={i}
                x1={Math.cos(a) * r1a} y1={Math.sin(a) * r1a}
                x2={Math.cos(a) * r1b} y2={Math.sin(a) * r1b}
                stroke="color-mix(in oklab, var(--neon-cyan) 30%, transparent)"
                strokeWidth={i % 5 === 0 ? 1 : 0.5}
              />
            );
          })}
        </g>
      </svg>

      {/* Mid segmented ring (counter-rotating) */}
      <svg
        width={size + 40} height={size + 40}
        className="absolute inset-0 animate-orbit-rev"
      >
        <g transform={`translate(${(size + 40) / 2} ${(size + 40) / 2})`}>
          {Array.from({ length: 12 }).map((_, i) => {
            const a0 = (i / 12) * Math.PI * 2;
            const a1 = a0 + (Math.PI * 2) / 12 * 0.55;
            const x0 = Math.cos(a0) * r2, y0 = Math.sin(a0) * r2;
            const x1 = Math.cos(a1) * r2, y1 = Math.sin(a1) * r2;
            return (
              <path
                key={i}
                d={`M ${x0} ${y0} A ${r2} ${r2} 0 0 1 ${x1} ${y1}`}
                stroke="color-mix(in oklab, var(--quantum-violet) 40%, transparent)"
                strokeWidth={1}
                fill="none"
              />
            );
          })}
        </g>
      </svg>

      {/* Score arc */}
      <svg width={size} height={size} className="absolute" style={{ transform: "rotate(-90deg)" }}>
        <defs>
          <linearGradient id={`tg-${size}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={tone} />
            <stop offset="100%" stopColor="var(--quantum-violet)" />
          </linearGradient>
        </defs>
        <circle cx={size/2} cy={size/2} r={r} stroke="color-mix(in oklab, var(--foreground) 6%, transparent)" strokeWidth={thickness} fill="none" />
        <motion.circle
          cx={size/2} cy={size/2} r={r}
          stroke={`url(#tg-${size})`} strokeWidth={thickness} fill="none" strokeLinecap="round"
          style={{ strokeDasharray: dash, filter: `drop-shadow(0 0 8px ${tone})` }}
        />
      </svg>

      <OrbitingSignals size={size + 40} count={4} radiusRatio={0.46} />

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.div className="font-display text-5xl font-light tabular-nums" style={{ color: tone }}>
          {display}
        </motion.div>
        <div className="mt-1 holo-mono">{label ?? verdict}</div>
      </div>
    </div>
  );
}
