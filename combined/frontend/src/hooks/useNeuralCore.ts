import { useSyncExternalStore } from "react";
import {
  getNeuralState,
  subscribe,
  subscribeEvents,
  type NeuralEvent,
  type NeuralState,
} from "@/lib/neural-core";
import { useEffect, useRef, useState } from "react";

const serverSnap: NeuralState = {
  heartbeat: 0.5,
  arousal: 0.2,
  threat: 0,
  cursorX: 0.5,
  cursorY: 0.5,
  cursorVel: 0,
  lastEvent: null,
  tick: 0,
  reduced: true,
};

export function useNeuralCore<T>(selector: (s: NeuralState) => T): T {
  return useSyncExternalStore(
    subscribe,
    () => selector(getNeuralState()),
    () => selector(serverSnap),
  );
}

export function useHeartbeat() {
  return useNeuralCore((s) => s.heartbeat);
}

export function useArousal() {
  return useNeuralCore((s) => s.arousal);
}

export function useThreatLevel() {
  return useNeuralCore((s) => s.threat);
}

export function useCursorVelocity() {
  return useNeuralCore((s) => s.cursorVel);
}

// Subscribe to discrete neural events (anomaly, thought, scan-*, route-change).
export function useNeuralEvent(
  kinds: NeuralEvent["kind"][],
  handler: (e: NeuralEvent) => void,
) {
  const ref = useRef(handler);
  ref.current = handler;
  const key = kinds.join(",");
  useEffect(() => {
    const set = new Set(kinds);
    const unsub = subscribeEvents((e) => {
      if (set.has(e.kind)) ref.current(e);
    });
    return () => { unsub(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
}

// Convenience: rolling buffer of recent events for stream-style UIs.
export function useRecentEvents(kinds: NeuralEvent["kind"][], max = 12) {
  const [list, setList] = useState<NeuralEvent[]>([]);
  useNeuralEvent(kinds, (e) => {
    setList((prev) => [e, ...prev].slice(0, max));
  });
  return list;
}
