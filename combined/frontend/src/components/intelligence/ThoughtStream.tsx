import { useEffect, useRef, useState } from "react";
import { useNeuralEvent, useNeuralCore } from "@/hooks/useNeuralCore";

const CALM = [
  "analyzing packet drift…",
  "cross-referencing 14,221 vectors",
  "anomaly ψ-3 below threshold",
  "confidence 0.82 ↑",
  "idle scan: 192.0.2.0/24",
  "trust manifold stable",
  "neural mesh synchronized",
  "lattice integrity nominal",
  "watching ASN 13335 · clean",
  "no signal regression detected",
  "perimeter telemetry quiet",
];

const ALERT = [
  "anomaly ψ-7 escalating",
  "deviation +1.6σ on cluster Δ",
  "tracing root vector 0xA1F2…",
  "shadow ASN appeared · investigating",
  "entropy spike on edge node",
  "trust gradient destabilized",
  "rerouting inference threads",
  "containment lattice tightened",
];

interface Line {
  id: number;
  text: string;
  alert: boolean;
}

let id = 1;

/**
 * ThoughtStream — corner overlay streaming AI cognition lines on a Poisson
 * cadence driven by the Neural Core. Tone shifts with threat level.
 */
export function ThoughtStream() {
  const threat = useNeuralCore((s) => s.threat);
  const reduced = useNeuralCore((s) => s.reduced);
  const [lines, setLines] = useState<Line[]>([]);
  const wrapRef = useRef<HTMLDivElement>(null);

  useNeuralEvent(["thought"], () => {
    const alert = Math.random() < 0.1 + threat * 0.7;
    const pool = alert ? ALERT : CALM;
    const text = pool[Math.floor(Math.random() * pool.length)];
    setLines((prev) => [{ id: id++, text, alert }, ...prev].slice(0, 7));
  });

  // Burst on anomalies — a flurry of 2-4 quick lines.
  useNeuralEvent(["anomaly"], () => {
    const burst = 2 + Math.floor(Math.random() * 3);
    for (let i = 0; i < burst; i++) {
      window.setTimeout(() => {
        const alert = Math.random() < 0.4 + threat * 0.5;
        const pool = alert ? ALERT : CALM;
        const text = pool[Math.floor(Math.random() * pool.length)];
        setLines((prev) => [{ id: id++, text, alert }, ...prev].slice(0, 7));
      }, i * 140);
    }
  });

  // Seed an initial line so it doesn't feel empty.
  useEffect(() => {
    setLines([{ id: id++, text: "neural core online · listening", alert: false }]);
  }, []);

  if (reduced) return null;

  return (
    <div
      ref={wrapRef}
      aria-hidden
      className="pointer-events-none fixed bottom-3 left-3 z-[55] hidden max-w-xs select-none font-mono text-[10px] leading-relaxed sm:block"
      style={{ textShadow: "0 0 8px color-mix(in oklab, var(--neon-cyan) 35%, transparent)" }}
    >
      <div className="mb-1 flex items-center gap-1.5 text-[9px] uppercase tracking-[0.2em] text-muted-foreground/70">
        <span
          className="inline-block h-1.5 w-1.5 rounded-full"
          style={{
            background: "var(--neon-cyan)",
            boxShadow: "0 0 8px var(--neon-cyan)",
            opacity: "calc(0.4 + var(--neural-arousal, 0.2) * 0.8)",
          }}
        />
        cognition stream
      </div>
      <ul className="space-y-0.5">
        {lines.map((l, i) => (
          <li
            key={l.id}
            className="truncate"
            style={{
              opacity: Math.max(0.15, 1 - i * 0.14),
              color: l.alert
                ? "color-mix(in oklab, var(--neon-amber) 80%, white)"
                : "color-mix(in oklab, var(--neon-cyan) 70%, white)",
              animation: "ts-in 320ms ease-out",
            }}
          >
            <span className="mr-1 text-muted-foreground/60">›</span>
            {l.text}
          </li>
        ))}
      </ul>
      <style>{`@keyframes ts-in { from { opacity: 0; transform: translateX(-6px); } }`}</style>
    </div>
  );
}
