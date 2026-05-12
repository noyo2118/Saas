import { useEffect, useRef } from "react";
import { useNeuralCore } from "@/hooks/useNeuralCore";

/**
 * QuantumAtmosphere — single global background layer mounted once in __root.
 * Composes void field, neural mesh canvas, quantum fog, scanlines, signal
 * particles and depth vignette. Everything is restrained: low opacities,
 * slow periods, capped element counts. All cycles are heartbeat-anchored.
 */
export function QuantumAtmosphere() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden quantum-tint"
      style={{ contain: "strict" }}
    >
      <VoidField />
      <NeuralMesh />
      <QuantumFog />
      <HoloScanlines />
      <SignalParticles />
      <DepthVignette />
    </div>
  );
}

/* ────────────────────────────── VoidField ────────────────────────────── */
function VoidField() {
  return (
    <>
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(110% 70% at 50% -10%, color-mix(in oklab, var(--plasma-blue) 8%, transparent), transparent 60%)," +
            "radial-gradient(80% 60% at 100% 110%, color-mix(in oklab, var(--quantum-violet) 7%, transparent), transparent 60%)," +
            "radial-gradient(80% 60% at 0% 100%, color-mix(in oklab, var(--neon-cyan) 5%, transparent), transparent 60%)",
        }}
      />
      <div
        className="absolute inset-0 depth-bg"
        style={{
          background:
            "radial-gradient(50% 40% at 30% 30%, color-mix(in oklab, var(--quantum-violet) 5%, transparent), transparent 70%)",
          opacity: 0.6,
        }}
      />
    </>
  );
}

/* ────────────────────────────── NeuralMesh ────────────────────────────── */
function NeuralMesh() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const isMobile = window.innerWidth < 768;
    const NODE_COUNT = isMobile ? 24 : 56;
    const LINK_DIST = isMobile ? 140 : 180;

    type Node = { x: number; y: number; vx: number; vy: number; seed: number };
    let nodes: Node[] = [];
    let w = 0, h = 0;
    let raf = 0;
    let last = performance.now();
    let alpha = 0; // fade-in

    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      nodes = Array.from({ length: NODE_COUNT }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.08,
        vy: (Math.random() - 0.5) * 0.08,
        seed: Math.random() * 1000,
      }));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const tick = (now: number) => {
      const dt = Math.min(50, now - last);
      last = now;
      alpha = Math.min(1, alpha + dt / 1400);
      ctx.clearRect(0, 0, w, h);

      // Drift
      for (const n of nodes) {
        n.x += n.vx * dt * 0.06;
        n.y += n.vy * dt * 0.06;
        if (n.x < -20) n.x = w + 20;
        if (n.x > w + 20) n.x = -20;
        if (n.y < -20) n.y = h + 20;
        if (n.y > h + 20) n.y = -20;
      }

      // Read neural threat from CSS var for tint
      const root = document.documentElement;
      const threat = parseFloat(getComputedStyle(root).getPropertyValue("--neural-threat") || "0");

      const cool = "200, 230, 255";
      const warm = "255, 175, 130";
      const blend = (a: string, b: string, t: number) => {
        const aa = a.split(",").map(Number);
        const bb = b.split(",").map(Number);
        return aa.map((v, i) => Math.round(v + (bb[i] - v) * t)).join(",");
      };
      const rgb = blend(cool, warm, threat * 0.6);

      // Edges
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d = Math.hypot(dx, dy);
          if (d < LINK_DIST) {
            const op = (1 - d / LINK_DIST) * 0.10 * alpha;
            ctx.strokeStyle = `rgba(${rgb}, ${op})`;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }

      // Nodes
      ctx.fillStyle = `rgba(${rgb}, ${0.55 * alpha})`;
      for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, 0.9, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    const onVis = () => {
      if (document.hidden) cancelAnimationFrame(raf);
      else { last = performance.now(); raf = requestAnimationFrame(tick); }
    };
    document.addEventListener("visibilitychange", onVis);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      className="absolute inset-0 h-full w-full"
      style={{ opacity: 0.7, mixBlendMode: "screen" }}
    />
  );
}

/* ────────────────────────────── QuantumFog ────────────────────────────── */
function QuantumFog() {
  return (
    <>
      <div
        className="absolute inset-0 depth-bg"
        style={{
          background:
            "radial-gradient(40% 30% at 20% 30%, color-mix(in oklab, var(--plasma-blue) 12%, transparent), transparent 70%)",
          filter: "blur(40px)",
          animation: "drift 31s ease-in-out infinite",
        }}
      />
      <div
        className="absolute inset-0 depth-mid"
        style={{
          background:
            "radial-gradient(35% 28% at 80% 70%, color-mix(in oklab, var(--quantum-violet) 10%, transparent), transparent 70%)",
          filter: "blur(50px)",
          animation: "drift 18s ease-in-out infinite reverse",
        }}
      />
    </>
  );
}

/* ────────────────────────────── HoloScanlines ────────────────────────────── */
function HoloScanlines() {
  const arousal = useNeuralCore((s) => s.arousal);
  if (arousal < 0.35) return null;
  return (
    <>
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent 0 3px, color-mix(in oklab, var(--neon-cyan) 4%, transparent) 3px 4px)",
          opacity: 0.5,
        }}
      />
      <div
        className="absolute inset-x-0 h-px"
        style={{
          top: 0,
          background:
            "linear-gradient(90deg, transparent, color-mix(in oklab, var(--neon-cyan) 60%, transparent), transparent)",
          animation: "scan-sweep 12s ease-in-out infinite",
        }}
      />
    </>
  );
}

/* ────────────────────────────── SignalParticles ────────────────────────────── */
function SignalParticles() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const isMobile = window.innerWidth < 768;
    const N = isMobile ? 8 : 22;
    type P = { x: number; y: number; vx: number; vy: number; r: number };
    let particles: P[] = [];
    let w = 0, h = 0;
    let raf = 0;
    let last = performance.now();

    const resize = () => {
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr); canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      particles = Array.from({ length: N }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.04,
        vy: -0.04 - Math.random() * 0.05,
        r: 0.6 + Math.random() * 1.1,
      }));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const tick = (now: number) => {
      const dt = Math.min(50, now - last); last = now;
      ctx.clearRect(0, 0, w, h);
      const root = document.documentElement;
      const cx = parseFloat(root.style.getPropertyValue("--neural-cx") || "50") / 100 * w;
      const cy = parseFloat(root.style.getPropertyValue("--neural-cy") || "50") / 100 * h;

      for (const p of particles) {
        // Gentle gravity toward cursor
        const dx = cx - p.x, dy = cy - p.y;
        const d2 = Math.max(2000, dx * dx + dy * dy);
        p.vx += (dx / d2) * 0.5 * dt;
        p.vy += (dy / d2) * 0.5 * dt;
        // friction
        p.vx *= 0.985; p.vy *= 0.985;
        p.x += p.vx * dt; p.y += p.vy * dt;
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; p.vy = -0.04; }
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(190, 225, 255, 0.55)";
        ctx.fill();
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    const onVis = () => {
      if (document.hidden) cancelAnimationFrame(raf);
      else { last = performance.now(); raf = requestAnimationFrame(tick); }
    };
    document.addEventListener("visibilitychange", onVis);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      document.removeEventListener("visibilitychange", onVis);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      className="absolute inset-0 h-full w-full"
      style={{ opacity: 0.6, mixBlendMode: "screen" }}
    />
  );
}

/* ────────────────────────────── DepthVignette ────────────────────────────── */
function DepthVignette() {
  return (
    <div
      className="absolute inset-0"
      style={{
        background:
          "radial-gradient(60% 40% at var(--neural-cx, 50%) var(--neural-cy, 50%), transparent 0%, color-mix(in oklab, var(--background) 50%, transparent) 100%)",
        transition: "background 800ms ease",
      }}
    />
  );
}
