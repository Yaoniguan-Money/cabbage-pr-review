/** 与 styles.css :root 默认值保持一致，仅作读取失败时的保护 */
const CSS_FALLBACKS = {
  "--motion-enter-duration": "0.65s",
  "--motion-enter-y": "1.75rem",
  "--motion-stagger-step": "0.06s",
  "--motion-route-duration": "0.38s",
  "--motion-route-y": "0.75rem",
  "--motion-section-duration": "0.28s",
  "--motion-section-y": "0.5rem",
  "--motion-ease": "cubic-bezier(0.16, 1, 0.3, 1)",
} as const;

type MotionCssVar = keyof typeof CSS_FALLBACKS;

function readCssVar(name: MotionCssVar): string {
  if (typeof document === "undefined") {
    return CSS_FALLBACKS[name];
  }
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || CSS_FALLBACKS[name];
}

function parseDurationSeconds(raw: string): number {
  const trimmed = raw.trim();
  if (trimmed.endsWith("ms")) {
    return parseFloat(trimmed) / 1000;
  }
  if (trimmed.endsWith("s")) {
    return parseFloat(trimmed);
  }
  const n = parseFloat(trimmed);
  return Number.isFinite(n) ? n : 0.5;
}

function parseLengthPx(raw: string): number {
  const trimmed = raw.trim();
  const rootPx =
    typeof document !== "undefined"
      ? parseFloat(getComputedStyle(document.documentElement).fontSize) || 16
      : 16;
  if (trimmed.endsWith("rem")) {
    return parseFloat(trimmed) * rootPx;
  }
  if (trimmed.endsWith("px")) {
    return parseFloat(trimmed);
  }
  const n = parseFloat(trimmed);
  return Number.isFinite(n) ? n : rootPx;
}

const DEFAULT_EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];

function parseEase(raw: string): [number, number, number, number] {
  const match = raw.match(/cubic-bezier\(\s*([^)]+)\s*\)/i);
  if (!match) {
    return DEFAULT_EASE;
  }
  const parts = match[1].split(",").map((s) => parseFloat(s.trim()));
  if (parts.length === 4 && parts.every((n) => Number.isFinite(n))) {
    return parts as [number, number, number, number];
  }
  return DEFAULT_EASE;
}

export interface MotionTokens {
  enterDuration: number;
  enterY: number;
  staggerStep: number;
  routeDuration: number;
  routeY: number;
  sectionDuration: number;
  sectionY: number;
  ease: [number, number, number, number];
}

export function readMotionTokens(): MotionTokens {
  const ease = parseEase(readCssVar("--motion-ease"));
  return {
    enterDuration: parseDurationSeconds(readCssVar("--motion-enter-duration")),
    enterY: parseLengthPx(readCssVar("--motion-enter-y")),
    staggerStep: parseDurationSeconds(readCssVar("--motion-stagger-step")),
    routeDuration: parseDurationSeconds(readCssVar("--motion-route-duration")),
    routeY: parseLengthPx(readCssVar("--motion-route-y")),
    sectionDuration: parseDurationSeconds(readCssVar("--motion-section-duration")),
    sectionY: parseLengthPx(readCssVar("--motion-section-y")),
    ease,
  };
}
