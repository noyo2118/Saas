import { REGIONS } from "@/lib/mock-data";

export function ThreatMap({ height = 360 }: { height?: number }) {
  return (
    <div className="relative w-full overflow-hidden rounded-xl" style={{ height }}>
      <div className="absolute inset-0 cyber-grid opacity-40" />
      <svg viewBox="0 0 100 60" className="absolute inset-0 h-full w-full" preserveAspectRatio="xMidYMid meet">
        <defs>
          <radialGradient id="mapGlow">
            <stop offset="0%" stopColor="color-mix(in oklab, var(--neon-cyan) 40%, transparent)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <linearGradient id="arc" x1="0" x2="1">
            <stop offset="0%" stopColor="var(--neon-cyan)" stopOpacity="0.9" />
            <stop offset="100%" stopColor="var(--neon-violet)" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        {/* Stylised continents – soft blobs */}
        {[
          "M10,20 Q20,12 30,18 T40,30 Q35,40 22,38 Q12,36 10,28 Z",
          "M30,42 Q40,36 44,46 T36,56 Q30,58 28,50 Z",
          "M48,18 Q58,10 66,18 T72,30 Q66,38 56,36 Q48,32 48,24 Z",
          "M68,30 Q82,22 92,30 T88,46 Q78,52 70,46 Q66,40 68,34 Z",
          "M52,38 Q60,36 62,46 T54,54 Q48,52 50,44 Z",
        ].map((d, i) => (
          <path key={i} d={d} fill="color-mix(in oklab, var(--surface-2) 80%, transparent)" stroke="color-mix(in oklab, var(--neon-cyan) 25%, transparent)" strokeWidth="0.2" />
        ))}
        {REGIONS.map((r) => (
          <g key={r.name}>
            <circle cx={r.x} cy={r.y * 0.6} r="3" fill="url(#mapGlow)" />
            <circle cx={r.x} cy={r.y * 0.6} r="0.9" fill="var(--neon-cyan)" />
            <circle cx={r.x} cy={r.y * 0.6} r="0.9" fill="none" stroke="var(--neon-cyan)">
              <animate attributeName="r" values="0.9;3.5;0.9" dur="2.2s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" values="0.9;0;0.9" dur="2.2s" repeatCount="indefinite" />
            </circle>
          </g>
        ))}
        {/* Arcs */}
        {[
          [22, 22, 74, 25], [52, 20, 60, 26], [22, 22, 32, 41], [74, 25, 84, 43],
        ].map(([x1, y1, x2, y2], i) => {
          const mx = (x1 + x2) / 2; const my = Math.min(y1, y2) - 12;
          return (
            <path key={i} d={`M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`} stroke="url(#arc)" strokeWidth="0.35" fill="none" strokeDasharray="2 2">
              <animate attributeName="stroke-dashoffset" values="0;-20" dur={`${3 + i}s`} repeatCount="indefinite" />
            </path>
          );
        })}
      </svg>
    </div>
  );
}
