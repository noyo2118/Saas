import { useEffect, useState } from "react";
import { TERMINAL_LINES } from "@/lib/mock-data";

export function Terminal({ lines = TERMINAL_LINES, autoLoop = true, speed = 28 }: { lines?: string[]; autoLoop?: boolean; speed?: number }) {
  const [idx, setIdx] = useState(0);
  const [shown, setShown] = useState<string[]>([]);
  const [typing, setTyping] = useState("");

  useEffect(() => {
    if (idx >= lines.length) {
      if (!autoLoop) return;
      const t = setTimeout(() => { setShown([]); setIdx(0); setTyping(""); }, 1800);
      return () => clearTimeout(t);
    }
    const line = lines[idx];
    let i = 0;
    const id = setInterval(() => {
      i++;
      setTyping(line.slice(0, i));
      if (i >= line.length) {
        clearInterval(id);
        setShown((s) => [...s, line]);
        setTyping("");
        setIdx((v) => v + 1);
      }
    }, speed);
    return () => clearInterval(id);
  }, [idx, lines, autoLoop, speed]);

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-[color-mix(in_oklab,#000_55%,var(--surface-1))] font-mono text-[12.5px] leading-relaxed">
      <div className="flex items-center gap-1.5 border-b border-border px-3 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-neon-red/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-neon-amber/80" />
        <span className="h-2.5 w-2.5 rounded-full bg-neon-green/80" />
        <span className="ml-2 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">trustscan ~ scan.log</span>
      </div>
      <div className="h-64 overflow-y-auto p-4">
        {shown.map((l, i) => (
          <div key={i} className={l.startsWith("[!]") ? "text-neon-amber" : l.startsWith("$") ? "text-neon-cyan" : "text-foreground/80"}>
            {l}
          </div>
        ))}
        {typing && (
          <div className={typing.startsWith("[!]") ? "text-neon-amber" : typing.startsWith("$") ? "text-neon-cyan" : "text-foreground/80"}>
            {typing}<span className="ml-0.5 inline-block h-3 w-1.5 translate-y-0.5 bg-neon-cyan animate-pulse" />
          </div>
        )}
      </div>
    </div>
  );
}
