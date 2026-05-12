// Calculated, weightless motion presets for the year-3000 interface.

export const easeQuantum = [0.2, 0.8, 0.2, 1] as const;
export const easeCine = [0.16, 1, 0.3, 1] as const;

export const springInertial = {
  type: "spring" as const,
  stiffness: 110,
  damping: 22,
  mass: 0.9,
};

export const springHarmonic = {
  type: "spring" as const,
  stiffness: 180,
  damping: 26,
  mass: 0.7,
};

export const fadeRise = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, ease: easeCine },
};

export const stagger = (i: number, base = 0.06) => ({
  delay: i * base,
});
