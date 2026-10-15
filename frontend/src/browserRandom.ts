import type { Uint32Source } from "./dice-core";

/**
 * The browser's secure randomness for dice-core, or null when it is missing.
 * There is deliberately no Math.random fallback: without secure randomness
 * the digital roll is unavailable and physical entry remains.
 */
export function browserRandomSource(): Uint32Source | null {
  const crypto = globalThis.crypto;
  if (typeof crypto?.getRandomValues !== "function") return null;
  return () => crypto.getRandomValues(new Uint32Array(1))[0]!;
}
