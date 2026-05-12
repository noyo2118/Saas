import { motion } from "framer-motion";
import { OrbitingSignals } from "@/components/holo/OrbitingSignals";

/**
 * ThreatGlobe — wireframe globe with calm rotation, atmospheric halo and
 * sparse orbiting signal particles.
 */
export function ThreatGlobe({ size = 360 }: { size?: number }) {
  const meridians = Array.from({ length: 12 });
  const parallels = Array.from({ length: 7 });
  const r = size / 2 - 4;
  return (
    <div className="relative" style={{ width: size + 40, height: size + 40 }}>
      <div
        aria-hidden
        className="absolute inset-0 rounded-full blur-3xl opacity-50"
        style={{
          background:
            "radial-gradient(circle, color-mix(in oklab, var(--plasma-blue) 38%, transparent), transparent 60%)",
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.svg
          width={size} height={size} viewBox={`0 0 ${size} ${size}`}
          animate={{ rotate: 360 }} transition={{ duration: 120, ease: "linear", repeat: Infinity }}
        >
          <defs>
            <radialGradient id="globeFill" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="color-mix(in oklab, var(--plasma-blue) 18%, transparent)" />
              <stop offset="100%" stopColor="transparent" />
            </radialGradient>
          </defs>
          <circle cx={size/2} cy={size/2} r={r} fill="url(#globeFill)" />
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="color-mix(in oklab, var(--neon-cyan) 40%, transparent)" strokeWidth="1" />
          {parallels.map((_, i) => {
            const ry = (r * Math.cos((Math.PI * (i + 1)) / (parallels.length + 1)));
            return (
              <ellipse key={`p${i}`} cx={size/2} cy={size/2} rx={r} ry={Math.abs(ry)} fill="none" stroke="color-mix(in oklab, var(--neon-cyan) 16%, transparent)" strokeWidth="0.6" />
            );
          })}
          {meridians.map((_, i) => {
            const rot = (180 / meridians.length) * i;
            const rx = r * Math.cos((Math.PI * i) / meridians.length);
            return (
              <ellipse key={`m${i}`} cx={size/2} cy={size/2} rx={Math.abs(rx)} ry={r}
                fill="none" stroke="color-mix(in oklab, var(--neon-cyan) 16%, transparent)" strokeWidth="0.6"
                transform={`rotate(${rot} ${size/2} ${size/2})`} />
            );
          })}
          {[
            [size*0.32, size*0.38], [size*0.68, size*0.42], [size*0.55, size*0.6], [size*0.42, size*0.7], [size*0.74, size*0.66],
          ].map(([cx, cy], i) => (
            <g key={i}>
              <circle cx={cx} cy={cy} r="2" fill="var(--neon-cyan)" />
              <circle cx={cx} cy={cy} r="2" fill="none" stroke="var(--neon-cyan)" strokeOpacity="0.5">
                <animate attributeName="r" values="2;12;2" dur="3.4s" begin={`${i * 0.6}s`} repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" values="0.6;0;0.6" dur="3.4s" begin={`${i * 0.6}s`} repeatCount="indefinite" />
              </circle>
            </g>
          ))}
        </motion.svg>
      </div>

      {/* Orbiting signal particles */}
      <OrbitingSignals size={size + 40} count={6} radiusRatio={0.55} />

      {/* Counter-rotating outer ring */}
      <motion.div
        className="absolute inset-0 rounded-full border border-dashed"
        style={{ borderColor: "color-mix(in oklab, var(--quantum-violet) 22%, transparent)" }}
        animate={{ rotate: -360 }} transition={{ duration: 180, ease: "linear", repeat: Infinity }}
      />
    </div>
  );
}
