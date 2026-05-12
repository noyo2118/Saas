import { motion } from "framer-motion";
import { RISK_BREAKDOWN } from "@/lib/mock-data";

export function RiskBars() {
  const max = Math.max(...RISK_BREAKDOWN.map((r) => r.value));
  return (
    <div className="space-y-3">
      {RISK_BREAKDOWN.map((r, i) => (
        <div key={r.label}>
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{r.label}</span>
            <span className="font-mono text-foreground">{r.value}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[color-mix(in_oklab,var(--surface-2)_80%,transparent)]">
            <motion.div
              initial={{ width: 0 }}
              whileInView={{ width: `${(r.value / max) * 100}%` }}
              viewport={{ once: true, margin: "-10% 0px" }}
              transition={{ duration: 1, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="h-full rounded-full"
              style={{
                background: "linear-gradient(90deg, var(--neon-cyan), var(--neon-violet))",
                boxShadow: "0 0 12px color-mix(in oklab, var(--neon-cyan) 50%, transparent)",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
