import type { ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";

import { readMotionTokens } from "./readMotionTokens";

interface SectionTransitionProps {
  sectionKey: string;
  children: ReactNode;
}

/** 详情主区 section 切换转场：参数来自 :root --motion-section-* */
export function SectionTransition({ sectionKey, children }: SectionTransitionProps) {
  const reduce = useReducedMotion();
  const tokens = readMotionTokens();

  if (reduce) {
    return <div className="section-transition">{children}</div>;
  }

  return (
    <motion.div
      key={sectionKey}
      className="section-transition"
      initial={{ opacity: 0, y: tokens.sectionY }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: tokens.sectionDuration, ease: tokens.ease }}
    >
      {children}
    </motion.div>
  );
}
