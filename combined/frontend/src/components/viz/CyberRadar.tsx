import { useMemo } from "react";
import { useNeuralCore } from "@/hooks/useNeuralCore";

/**
 * CyberRadar — sweep beam locked to neural heartbeat phase. Mesh overlay
 * stays subtle (≤15% opacity).
 */
export function CyberRadar({ size = 240 }: { size?: number }) {
  const heartbeat = useNeuralCore((s) => s.heartbeat);
  const blips = useMemo(
    () =>
      Array.from({ length: 6 }, () => ({
        x: 0.15 + Math.random() * 0.7,
        y: 0.15 + Math.random() * 0.7,
        d: Math.random() * 4,
      })),
    [],
  );
  const cx = size / 2, cy = size / 2, r = size / 2 - 4;
  const angle = heartbeat * 360;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <defs>
          <radialGradient id="radarBg">
            <stop offset="0%" stopColor="color-mix(in oklab, var(--neon-cyan) 10%, transparent)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="100%" stopColor="color-mix(in oklab, var(--neon-cyan) 60%, transparent)" />
          </linearGradient>
        </defs>
        <circle cx={cx} cy={cy} r={r} fill="url(#radarBg)" stroke="color-mix(in oklab, var(--neon-cyan) 22%, transparent)" />
        {[0.25, 0.5, 0.75].map((f) => (
          <circle key={f} cx={cx} cy={cy} r={r * f} fill="none" stroke="color-mix(in oklab, var(--neon-cyan) 10%, transparent)" />
        ))}
        <line x1={cx} y1={4} x2={cx} y2={size - 4} stroke="color-mix(in oklab, var(--neon-cyan) 10%, transparent)" />
        <line x1={4} y1={cy} x2={size - 4} y2={cy} stroke="color-mix(in oklab, var(--neon-cyan) 10%, transparent)" />
        <g style={{ transform: `rotate(${angle}deg)`, transformOrigin: `${cx}px ${cy}px`, transition: "transform 240ms linear" }}>
          <path
            d={`M ${cx} ${cy} L ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx + r * Math.sin(Math.PI/3)} ${cy - r * Math.cos(Math.PI/3)} Z`}
            fill="url(#sweep)"
          />
        </g>
        {blips.map((b, i) => (
          <g key={i}>
            <circle cx={size * b.x} cy={size * b.y} r="2.2" fill="var(--neon-cyan)" />
            <circle cx={size * b.x} cy={size * b.y} r="2.2" fill="none" stroke="var(--neon-cyan)">
              <animate attributeName="r" values="2.2;12;2.2" dur="3.4s" begin={`${b.d}s`} repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" values="0.6;0;0.6" dur="3.4s" begin={`${b.d}s`} repeatCount="indefinite" />
            </circle>
          </g>
        ))}
      </svg>
    </div>
  );
}
