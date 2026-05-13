// Neural Core — single shared "consciousness" engine for the UI.
// One rAF loop drives heartbeat, arousal, threat decay, cursor velocity, and
// dispatches probabilistic anomaly/thought events. Components subscribe via
// useSyncExternalStore-based hooks (see src/hooks/useNeuralCore.ts).

import { clamp, expSmooth, poissonInterval, prefersReducedMotion } from "./organic";

export type NeuralEventKind =
  | "scan-start"
  | "scan-complete"
  | "route-change"
  | "anomaly"
  | "thought"
  | "burst";

export interface NeuralEvent {
  kind: NeuralEventKind;
  payload?: unknown;
  at: number;
}

export interface NeuralState {
  // 0..1 phase oscillating with imperfect cadence — the "heartbeat".
  heartbeat: number;
  // 0..1 calm → alert. Smoothed.
  arousal: number;
  // 0..1 threat saturation. Decays slowly toward 0.
  threat: number;
  // Smoothed cursor.
  cursorX: number;
  cursorY: number;
  cursorVel: number; // 0..1 normalized
  // Last event timestamp by kind, for ad-hoc reactions.
  lastEvent: NeuralEvent | null;
  // Monotonic tick counter (mostly for debugging).
  tick: number;
  // True when the engine is in reduced-motion mode (mostly static).
  reduced: boolean;
}

type Listener = () => void;
type EventListener = (e: NeuralEvent) => void;

const initial: NeuralState = {
  heartbeat: 0,
  arousal: 0.18,
  threat: 0.0,
  cursorX: 0.5,
  cursorY: 0.5,
  cursorVel: 0,
  lastEvent: null,
  tick: 0,
  reduced: false,
};

let state: NeuralState = { ...initial };
const listeners = new Set<Listener>();
const eventListeners = new Set<EventListener>();

function emitChange() {
  for (const l of listeners) l();
}

function emitEvent(e: NeuralEvent) {
  state = { ...state, lastEvent: e };
  for (const el of eventListeners) el(e);
  emitChange();
}

export function getNeuralState(): NeuralState {
  return state;
}

export function subscribe(l: Listener): () => void {
  listeners.add(l);
  return () => { listeners.delete(l); };
}

export function subscribeEvents(l: EventListener): () => void {
  eventListeners.add(l);
  return () => { eventListeners.delete(l); };
}

// --- public dispatch API --------------------------------------------------
export function dispatchEvent(kind: NeuralEventKind, payload?: unknown) {
  emitEvent({ kind, payload, at: performance.now() });
  // Side-effects on shared state.
  if (kind === "scan-start") {
    state = { ...state, arousal: clamp(state.arousal + 0.45) };
  } else if (kind === "anomaly") {
    state = { ...state, arousal: clamp(state.arousal + 0.12) };
  } else if (kind === "route-change") {
    state = { ...state, arousal: clamp(state.arousal + 0.2) };
  }
  emitChange();
}

export function setThreatLevel(v: number) {
  state = { ...state, threat: clamp(v) };
  emitChange();
}

export function bumpThreat(delta: number) {
  state = { ...state, threat: clamp(state.threat + delta) };
  emitChange();
}

// --- engine ---------------------------------------------------------------
let started = false;
let rafId: number | null = null;
let lastTime = 0;
let nextHeartbeatAt = 0;
let nextAnomalyAt = 0;
let nextThoughtAt = 0;

let lastCx = 0.5;
let lastCy = 0.5;
let cursorTargetX = 0.5;
let cursorTargetY = 0.5;
let rawVel = 0;

function onPointerMove(e: PointerEvent) {
  cursorTargetX = e.clientX / window.innerWidth;
  cursorTargetY = e.clientY / window.innerHeight;
}

function loop(now: number) {
  const dt = Math.min(0.1, (now - lastTime) / 1000 || 0.016);
  lastTime = now;

  // Heartbeat with jittered period (3.6–4.4s typical, faster when threat high)
  if (now >= nextHeartbeatAt) {
    const base = 4000 - state.threat * 1200; // 4s calm → 2.8s alert
    const period = base * (0.92 + Math.random() * 0.16);
    nextHeartbeatAt = now + period;
  }
  const hbPhase =
    1 - Math.max(0, (nextHeartbeatAt - now) / (4000 - state.threat * 1200));
  const heartbeat = 0.5 - 0.5 * Math.cos(hbPhase * Math.PI * 2);

  // Cursor smoothing + velocity.
  const nx = expSmooth(state.cursorX, cursorTargetX, dt, 14);
  const ny = expSmooth(state.cursorY, cursorTargetY, dt, 14);
  const dx = nx - lastCx;
  const dy = ny - lastCy;
  lastCx = nx;
  lastCy = ny;
  const instantaneous = Math.min(1, Math.hypot(dx, dy) * 60);
  rawVel = expSmooth(rawVel, instantaneous, dt, 6);

  // Arousal decays to a baseline shaped by threat + cursor activity.
  const baseline = 0.15 + state.threat * 0.45 + rawVel * 0.25;
  const arousal = expSmooth(state.arousal, baseline, dt, 0.9);

  // Threat decays slowly toward 0.
  const threat = expSmooth(state.threat, 0, dt, 0.12);

  state = {
    ...state,
    heartbeat,
    arousal: clamp(arousal),
    threat: clamp(threat),
    cursorX: nx,
    cursorY: ny,
    cursorVel: rawVel,
    tick: state.tick + 1,
  };

  // CSS tokens for global reactive styling.
  if (typeof document !== "undefined") {
    const root = document.documentElement;
    root.style.setProperty("--neural-heartbeat", heartbeat.toFixed(3));
    root.style.setProperty("--neural-arousal", state.arousal.toFixed(3));
    root.style.setProperty("--neural-threat", state.threat.toFixed(3));
    root.style.setProperty("--neural-cx", (state.cursorX * 100).toFixed(2) + "%");
    root.style.setProperty("--neural-cy", (state.cursorY * 100).toFixed(2) + "%");
  }

  // Probabilistic anomaly bursts (faster when threat or arousal high).
  if (now >= nextAnomalyAt) {
    const mean = 8000 / (1 + state.threat * 1.6 + state.arousal * 0.8);
    nextAnomalyAt = now + poissonInterval(mean);
    emitEvent({ kind: "anomaly", at: now });
  }
  if (now >= nextThoughtAt) {
    const mean = 5200 / (1 + state.arousal * 0.9);
    nextThoughtAt = now + poissonInterval(mean);
    emitEvent({ kind: "thought", at: now });
  }

  emitChange();
  rafId = requestAnimationFrame(loop);
}

function pause() {
  if (rafId != null) cancelAnimationFrame(rafId);
  rafId = null;
}

function resume() {
  if (rafId != null) return;
  lastTime = performance.now();
  nextHeartbeatAt = lastTime;
  nextAnomalyAt = lastTime + poissonInterval(6000);
  nextThoughtAt = lastTime + poissonInterval(4000);
  rafId = requestAnimationFrame(loop);
}

export function startNeuralCore() {
  if (started || typeof window === "undefined") return;
  started = true;
  state = { ...state, reduced: prefersReducedMotion() };
  if (state.reduced) {
    // Static mode — set tokens once and don't run the loop.
    if (typeof document !== "undefined") {
      const root = document.documentElement;
      root.style.setProperty("--neural-heartbeat", "0.5");
      root.style.setProperty("--neural-arousal", "0.2");
      root.style.setProperty("--neural-threat", "0");
      root.style.setProperty("--neural-cx", "50%");
      root.style.setProperty("--neural-cy", "50%");
    }
    return;
  }
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) pause();
    else resume();
  });
  resume();
}
