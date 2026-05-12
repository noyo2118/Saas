import { AnimatePresence, motion } from "framer-motion";
import { ACTIVITY, type Severity } from "@/lib/mock-data";
import { useEffect, useState } from "react";
import { ShieldAlert, Bug, Zap, AlertTriangle, Info } from "lucide-react";

const tones: Record<Severity, { color: string; ring: string; icon: typeof ShieldAlert }> = {
  critical: { color: "text-neon-red",    ring: "ring-neon-red/30",    icon: ShieldAlert },
  high:     { color: "text-neon-amber",  ring: "ring-neon-amber/30",  icon: AlertTriangle },
  medium:   { color: "text-neon-violet", ring: "ring-neon-violet/30", icon: Bug },
  low:      { color: "text-neon-cyan",   ring: "ring-neon-cyan/30",   icon: Zap },
  info:     { color: "text-muted-foreground", ring: "ring-border",   icon: Info },
};

export function ActivityFeed() {
  const [items, setItems] = useState(ACTIVITY);
  useEffect(() => {
    const id = setInterval(() => {
      setItems((prev) => {
        const head = prev[prev.length - 1];
        const newItem = { ...head, time: "now" };
        const rest = prev.slice(0, -1).map((p, i) => ({ ...p, time: `${(i + 1) * 4}s` }));
        return [newItem, ...rest].slice(0, 8);
      });
    }, 3200);
    return () => clearInterval(id);
  }, []);
  return (
    <ul className="space-y-2">
      <AnimatePresence initial={false}>
        {items.map((it, i) => {
          const t = tones[it.severity];
          const Icon = t.icon;
          return (
            <motion.li
              key={`${it.target}-${i}-${it.time}`}
              initial={{ opacity: 0, y: -8, filter: "blur(6px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="flex items-center gap-3 rounded-xl border border-border bg-[color-mix(in_oklab,var(--surface-1)_60%,transparent)] px-3 py-2.5 backdrop-blur"
            >
              <div className={`flex h-8 w-8 items-center justify-center rounded-lg ring-2 bg-[color-mix(in_oklab,var(--surface-2)_80%,transparent)] ${t.ring}`}>
                <Icon className={`h-4 w-4 ${t.color}`} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{it.type}</div>
                <div className="truncate text-xs text-muted-foreground font-mono">{it.target}</div>
              </div>
              <div className="text-[11px] tabular-nums text-muted-foreground">{it.time}</div>
            </motion.li>
          );
        })}
      </AnimatePresence>
    </ul>
  );
}
