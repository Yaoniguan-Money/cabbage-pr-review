import type { MotionTokens } from "./readMotionTokens";

/** 路由转场 motion 属性（供 App 内 motion.div 使用） */
export function pageTransitionMotion(
  reduce: boolean,
  tokens: MotionTokens,
): {
  initial: { opacity: number; y: number };
  animate: { opacity: number; y: number };
  exit: { opacity: number; y: number };
  transition: { duration: number; ease: MotionTokens["ease"] };
} | null {
  if (reduce) {
    return null;
  }
  return {
    initial: { opacity: 0, y: tokens.routeY },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -tokens.routeY * 0.5 },
    transition: { duration: tokens.routeDuration, ease: tokens.ease },
  };
}
