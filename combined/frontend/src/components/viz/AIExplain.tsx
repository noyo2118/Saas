import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export function AIExplain({ text }: { text: string }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] p-5 backdrop-blur">
      <div aria-hidden className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full opacity-40 blur-3xl"
        style={{ background: "radial-gradient(circle, var(--neon-violet), transparent 60%)" }} />
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-neon-violet to-neon-cyan">
          <Sparkles className="h-4 w-4 text-primary-foreground" />
        </div>
        <div>
          <div className="text-sm font-medium">TrustScan AI</div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">Threat reasoning</div>
        </div>
      </div>
      <motion.p
        initial={{ opacity: 0, y: 6 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
        transition={{ duration: 0.7 }}
        className="text-sm leading-relaxed text-foreground/90"
      >
        {text}
      </motion.p>
    </div>
  );
}
