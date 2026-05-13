import { useEffect, useRef, useState } from "react";
import { startNeuralCore } from "@/lib/neural-core";
import { useNeuralEvent, useNeuralCore } from "@/hooks/useNeuralCore";

interface Ripple {
  id: number;
  x: number;
  y: number;
  hue: "cool" | "alert";
  born: number;
}

interface Streak {
  id: number;
  edge: "top" | "bottom" | "left" | "right";
  pos: number; // 0..1 along the edge
  len: number; // px
  hue: "cool" | "alert";
}

let nextId = 1;

/**
 * SentientLayer — fixed, full-viewport overlay (pointer-events: none) that
 * paints autonomous neural activity: distant pulse ripples, edge signal
 * streaks, an observation eye that tracks the cursor, and a global cursor
 * halo. All cadences are Poisson-driven via the Neural Core.
 */
export function SentientLayer() {
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const [streaks, setStreaks] = useState<Streak[]>([]);
  const eyeRef = useRef<HTMLDivElement>(null);
  const haloRef = useRef<HTMLDivElement>(null);
  const arousal = useNeuralCore((s) => s.arousal);
  const threat = useNeuralCore((s) => s.threat);
  const cursorX = useNeuralCore((s) => s.cursorX);
  const cursorY = useNeuralCore((s) => s.cursorY);

  // Boot the engine once.
  useEffect(() => {
    startNeuralCore();
  }, []);

  // Cursor halo + eye tracking via direct style writes (no re-render storm).
  useEffect(() => {
    const halo = haloRef.current;
    const eye = eyeRef.current;
    if (halo) {
      halo.style.transform = `translate3d(calc(${cursorX * 100}vw - 50%), calc(${cursorY * 100}vh - 50%), 0)`;
      halo.style.opacity = String(0.25 + arousal * 0.5);
    }
    if (eye) {
      // Pupil deflects toward cursor relative to eye position (top-right).
      const ex = window.innerWidth - 56;
      const ey = 64;
      const dx = (cursorX * window.innerWidth - ex) / 220;
      const dy = (cursorY * window.innerHeight - ey) / 220;
      const m = Math.min(1, Math.hypot(dx, dy));
      const nx = m === 0 ? 0 : (dx / m) * Math.min(6, m * 6);
      const ny = m === 0 ? 0 : (dy / m) * Math.min(6, m * 6);
      const pupil = eye.querySelector<HTMLElement>("[data-pupil]");
      if (pupil) pupil.style.transform = `translate3d(${nx}px, ${ny}px, 0)`;
      eye.style.opacity = String(0.35 + arousal * 0.5);
    }
  }, [cursorX, cursorY, arousal]);

  // Anomaly events → ripples + streaks.
  useNeuralEvent(["anomaly"], () => {
    const id = nextId++;
    const hue: "cool" | "alert" = Math.random() < 0.18 + threat * 0.6 ? "alert" : "cool";
    const ripple: Ripple = {
      id,
      x: 8 + Math.random() * 84,
      y: 8 + Math.random() * 84,
      hue,
      born: performance.now(),
    };
    setRipples((prev) => [...prev.slice(-5), ripple]);
    if (Math.random() < 0.6) {
      const edges: Streak["edge"][] = ["top", "bottom", "left", "right"];
      const streak: Streak = {
        id: nextId++,
        edge: edges[Math.floor(Math.random() * 4)],
        pos: Math.random(),
        len: 60 + Math.random() * 220,
        hue,
      };
      setStreaks((prev) => [...prev.slice(-4), streak]);
      window.setTimeout(
        () => setStreaks((prev) => prev.filter((s) => s.id !== streak.id)),
        1400,
      );
    }
    window.setTimeout(
      () => setRipples((prev) => prev.filter((r) => r.id !== id)),
      2600,
    );
  });

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-[60] overflow-hidden"
      style={{
        // Subtle hue mixing driven by threat — the room "warms" under risk.
        background:
          "radial-gradient(120% 80% at var(--neural-cx,50%) var(--neural-cy,50%), color-mix(in oklab, var(--neon-cyan) calc(var(--neural-arousal,0.2) * 6%), transparent) 0%, transparent 55%), radial-gradient(140% 90% at 50% 110%, color-mix(in oklab, var(--neon-red) calc(var(--neural-threat,0) * 18%), transparent), transparent 60%)",
        mixBlendMode: "screen",
      }}
    >
      {/* Distant pulse ripples */}
      {ripples.map((r) => (
        <span
          key={r.id}
          className="absolute block rounded-full"
          style={{
            left: `${r.x}%`,
            top: `${r.y}%`,
            width: 8,
            height: 8,
            transform: "translate(-50%, -50%)",
            boxShadow:
              r.hue === "alert"
                ? "0 0 0 1px color-mix(in oklab, var(--neon-red) 60%, transparent)"
                : "0 0 0 1px color-mix(in oklab, var(--neon-cyan) 60%, transparent)",
            animation: "sl-ripple 2.4s cubic-bezier(.2,.7,.2,1) forwards",
            // CSS var consumed by keyframes
            ["--ring" as string]:
              r.hue === "alert" ? "var(--neon-red)" : "var(--neon-cyan)",
          }}
        />
      ))}

      {/* Edge signal streaks */}
      {streaks.map((s) => {
        const horizontal = s.edge === "top" || s.edge === "bottom";
        const color =
          s.hue === "alert" ? "var(--neon-red)" : "var(--neon-cyan)";
        const base: React.CSSProperties = {
          position: "absolute",
          background: `linear-gradient(${horizontal ? "90deg" : "180deg"}, transparent, color-mix(in oklab, ${color} 80%, transparent), transparent)`,
          opacity: 0,
          animation: "sl-streak 1.4s ease-out forwards",
        };
        if (horizontal) {
          base.height = 1;
          base.width = s.len;
          base.left = `${s.pos * 100}%`;
          base[s.edge as "top" | "bottom"] = 0;
        } else {
          base.width = 1;
          base.height = s.len;
          base.top = `${s.pos * 100}%`;
          base[s.edge as "left" | "right"] = 0;
        }
        return <span key={s.id} style={base} />;
      })}

      {/* Cursor halo */}
      <div
        ref={haloRef}
        className="absolute left-0 top-0 h-40 w-40 rounded-full"
        style={{
          background:
            "radial-gradient(closest-side, color-mix(in oklab, var(--neon-cyan) 22%, transparent), transparent 70%)",
          filter: "blur(6px)",
          transition: "opacity 600ms ease",
          willChange: "transform",
        }}
      />

      {/* Neural observation eye (top-right) */}
      <div
        ref={eyeRef}
        className="absolute right-6 top-6 h-9 w-9 rounded-full"
        style={{
          border: "1px solid color-mix(in oklab, var(--neon-cyan) 45%, transparent)",
          background:
            "radial-gradient(closest-side, color-mix(in oklab, var(--neon-cyan) 18%, transparent), transparent 70%)",
          boxShadow:
            "0 0 18px color-mix(in oklab, var(--neon-cyan) 25%, transparent)",
          transition: "opacity 800ms ease",
        }}
      >
        <span
          data-pupil
          className="absolute left-1/2 top-1/2 block h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{
            background:
              "radial-gradient(closest-side, var(--neon-cyan), color-mix(in oklab, var(--neon-violet) 60%, transparent))",
            boxShadow:
              "0 0 10px color-mix(in oklab, var(--neon-cyan) 70%, transparent)",
            transition: "transform 280ms cubic-bezier(.2,.7,.2,1)",
            animation: "sl-blink 12s ease-in-out infinite",
          }}
        />
      </div>

      {/* Scanline drift, intensified by threat */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent 0 2px, color-mix(in oklab, var(--neon-cyan) calc(var(--neural-threat,0) * 8% + 2%), transparent) 2px 3px)",
          opacity: 0.18,
          animation: "sl-scan-drift 8s linear infinite",
        }}
      />

      <style>{keyframes}</style>
    </div>
  );
}

const keyframes = `
@keyframes sl-ripple {
  0%   { transform: translate(-50%, -50%) scale(0.4); opacity: 0; box-shadow: 0 0 0 0 color-mix(in oklab, var(--ring) 60%, transparent); }
  20%  { opacity: 0.9; }
  100% { transform: translate(-50%, -50%) scale(28); opacity: 0; box-shadow: 0 0 0 1px color-mix(in oklab, var(--ring) 0%, transparent); }
}
@keyframes sl-streak {
  0%   { opacity: 0; filter: blur(0px); }
  20%  { opacity: 0.9; }
  100% { opacity: 0; filter: blur(2px); }
}
@keyframes sl-blink {
  0%, 92%, 100% { transform: translate(-50%, -50%) scaleY(1); }
  94%           { transform: translate(-50%, -50%) scaleY(0.05); }
}
@keyframes sl-scan-drift {
  0% { background-position: 0 0; }
  100% { background-position: 0 24px; }
}
`;
