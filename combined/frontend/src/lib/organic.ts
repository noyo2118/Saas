// Organic motion + probabilistic helpers for the sentient layer.

export function jitter(value: number, pct = 0.08) {
  return value * (1 + (Math.random() * 2 - 1) * pct);
}

export function clamp(v: number, lo = 0, hi = 1) {
  return Math.max(lo, Math.min(hi, v));
}

export function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

// Exponentially decay `current` toward `target` with given rate (per second).
export function expSmooth(current: number, target: number, dt: number, rate = 4) {
  const k = 1 - Math.exp(-rate * dt);
  return current + (target - current) * k;
}

// Time between events for a Poisson process with given mean (ms).
export function poissonInterval(meanMs: number) {
  const u = Math.max(1e-6, Math.random());
  return -Math.log(u) * meanMs;
}

// Sine + low-frequency noise blend — feels like breath, not a metronome.
export function breathe(t: number, periodMs = 4200, depth = 1) {
  const phase = (t % periodMs) / periodMs;
  const main = Math.sin(phase * Math.PI * 2);
  const wobble = Math.sin((t / (periodMs * 1.7)) * Math.PI * 2) * 0.25;
  return ((main + wobble) / 1.25) * depth;
}

// Cheap deterministic 1D noise (hashed sin) for drift paths.
export function pseudoNoise(seed: number, t: number) {
  const x = Math.sin(seed * 127.1 + t * 0.001) * 43758.5453;
  return (x - Math.floor(x)) * 2 - 1;
}

export function prefersReducedMotion() {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
