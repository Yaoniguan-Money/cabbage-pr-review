import type { ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";

import { readMotionTokens } from "./readMotionTokens";

interface RevealProps {
  children: ReactNode;
  className?: string;
}

/** 区块入场：参数来自 :root --motion-* */
export function Reveal({ children, className }: RevealProps) {
  const reduce = useReducedMotion();
  const tokens = readMotionTokens();

  if (reduce) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: tokens.enterY }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: tokens.enterDuration, ease: tokens.ease }}
    >
      {children}
    </motion.div>
  );
}

interface RevealStaggerProps {
  children: ReactNode;
  className?: string;
}

/** 网格子项依次入场；不改变子元素语义标签 */
export function RevealStagger({ children, className }: RevealStaggerProps) {
  const reduce = useReducedMotion();
  const tokens = readMotionTokens();

  if (reduce) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="show"
      variants={{
        hidden: {},
        show: {
          transition: { staggerChildren: tokens.staggerStep },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

interface RevealStaggerItemProps {
  children: ReactNode;
  className?: string;
}

export function RevealStaggerItem({ children, className }: RevealStaggerItemProps) {
  const reduce = useReducedMotion();
  const tokens = readMotionTokens();

  if (reduce) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: tokens.enterY },
        show: {
          opacity: 1,
          y: 0,
          transition: { duration: tokens.enterDuration, ease: tokens.ease },
        },
      }}
    >
      {children}
    </motion.div>
  );
}
