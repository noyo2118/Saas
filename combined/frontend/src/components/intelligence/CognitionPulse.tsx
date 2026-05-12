import { useNeuralCore } from "@/hooks/useNeuralCore";

/**
 * CognitionPulse — tiny live waveform indicating the neural core is alive.
 * Amplitude tracks arousal; color shifts toward amber under threat.
 */
export function CognitionPulse({ className = "" }: { className?: string }) {
  const arousal = useNeuralCore((s) => s.arousal);
  const threat = useNeuralCore((s) => s.threat);
  const heartbeat = useNeuralCore((s) => s.heartbeat);

  const amp = 4 + arousal * 10;
  const color =
    threat > 0.5
      ? "var(--neon-amber)"
      : threat > 0.25
        ? "var(--neon-violet)"
        : "var(--neon-cyan)";

  // 8 bars, phase-shifted, scaled by heartbeat.
  const bars = Array.from({ length: 9 }, (_, i) => {
    const phase = (heartbeat + i * 0.11) % 1;
    const h = 2 + Math.abs(Math.sin(phase * Math.PI * 2)) * amp;
    return h;
  });

  return (
    <div
      title="Neural Core — synchronized"
      className={`inline-flex h-5 items-end gap-[2px] ${className}`}
      aria-hidden
    >
      {bars.map((h, i) => (
        <span
          key={i}
          style={{
            display: "inline-block",
            width: 2,
            height: h,
            borderRadius: 1,
            background: color,
            boxShadow: `0 0 6px ${color}`,
            transition: "height 120ms linear",
          }}
        />
      ))}
    </div>
  );
}
