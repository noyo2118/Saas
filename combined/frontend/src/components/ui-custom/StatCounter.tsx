import { motion, useInView, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useRef } from "react";

export function StatCounter({
  value,
  decimals = 0,
  prefix = "",
  suffix = "",
  duration = 1.6,
  className,
}: {
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-10% 0px" });
  const mv = useMotionValue(0);
  const display = useTransform(mv, (v) => {
    const n = decimals ? v.toFixed(decimals) : Math.floor(v).toLocaleString();
    return `${prefix}${n}${suffix}`;
  });

  useEffect(() => {
    if (inView) animate(mv, value, { duration, ease: [0.16, 1, 0.3, 1] });
  }, [inView, value, mv, duration]);

  return <motion.span ref={ref} className={className}>{display}</motion.span>;
}
