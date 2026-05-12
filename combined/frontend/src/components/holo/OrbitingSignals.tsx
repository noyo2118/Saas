/**
 * OrbitingSignals — sparse particles orbiting an anchor, used as ambient
 * "signal flow" around a focal element (globe, score ring).
 */
export function OrbitingSignals({
  size = 320,
  count = 5,
  radiusRatio = 0.52,
}: {
  size?: number;
  count?: number;
  radiusRatio?: number;
}) {
  const r = (size / 2) * radiusRatio;
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 animate-orbit"
      style={{ width: size, height: size }}
    >
      {Array.from({ length: count }).map((_, i) => {
        const angle = (i / count) * Math.PI * 2;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        const tone = i % 2 === 0 ? "var(--neon-cyan)" : "var(--quantum-violet)";
        return (
          <span
            key={i}
            className="absolute left-1/2 top-1/2 block h-1 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full"
            style={{
              transform: `translate(${x}px, ${y}px) translate(-50%, -50%)`,
              background: tone,
              boxShadow: `0 0 8px ${tone}`,
            }}
          />
        );
      })}
    </div>
  );
}
