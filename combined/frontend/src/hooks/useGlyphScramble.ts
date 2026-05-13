import { useEffect, useState } from "react";

const GLYPHS = "ΣΩΞΨΦΔΘΛΠ01<>/\\#%@";

/**
 * useGlyphScramble — reveals a string by cycling through random glyphs per
 * character, settling left-to-right. Used once on mount for ignition reveals.
 */
export function useGlyphScramble(target: string, durationMs = 700, active = true) {
  const [out, setOut] = useState(active ? "" : target);

  useEffect(() => {
    if (!active) { setOut(target); return; }
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setOut(target);
      return;
    }
    const start = performance.now();
    let raf = 0;
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const settled = Math.floor(target.length * t);
      let s = "";
      for (let i = 0; i < target.length; i++) {
        if (i < settled || target[i] === " ") s += target[i];
        else s += GLYPHS[(Math.floor(now / 30) + i) % GLYPHS.length];
      }
      setOut(s);
      if (t < 1) raf = requestAnimationFrame(step);
      else setOut(target);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs, active]);

  return out;
}
