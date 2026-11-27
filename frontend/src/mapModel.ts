/**
 * Issue #211 (mapper M1): what the map view reads from the player view, and
 * the route-drawing helpers. Display only: nothing here decides a move. The
 * server walks every route again and refuses what it won't accept.
 */
import type { SceneAllowance } from "./api/client";

export type Square = [number, number];

export interface MapEdge {
  orient: "h" | "v";
  col: number;
  row: number;
}

export interface MapFeature {
  feature_id: string;
  kind: string;
  label?: string;
  squares: Square[];
  edge: MapEdge | null;
  state?: string | null;
  blocks_step?: boolean;
}

export interface MapPit {
  pit_id: string;
  squares: Square[];
  depth_ft: number;
}

export interface MapToken {
  token_id: string;
  glyph: string;
  side: "party" | "hostile" | "neutral";
  label?: string;
  square: Square | null;
  footprint?: number;
}

export interface MapArea {
  area_id: string;
  label: string;
  level: "coarse" | "gridded";
  setting: "worked" | "natural";
  indoors: boolean;
  bounds: [number, number, number, number];
}

export interface MapSnapshot {
  width: number;
  height: number;
  terrain: string[];
  hwalls: string[];
  vwalls: string[];
  areas: MapArea[];
  features: MapFeature[];
  pits: MapPit[];
  tokens: MapToken[];
}

/** The player view's snapshot, typed for drawing. */
export function asSnapshot(raw: { [key: string]: unknown }): MapSnapshot {
  const s = raw as Partial<MapSnapshot>;
  return {
    width: s.width ?? 0,
    height: s.height ?? 0,
    terrain: s.terrain ?? [],
    hwalls: s.hwalls ?? [],
    vwalls: s.vwalls ?? [],
    areas: s.areas ?? [],
    features: s.features ?? [],
    pits: s.pits ?? [],
    tokens: s.tokens ?? [],
  };
}

/** `[0, 4]` -> `"A5"` (the server's square labels). */
export function label([col, row]: Square): string {
  let letters = "";
  let n = col + 1;
  while (n > 0) {
    const rem = (n - 1) % 26;
    letters = String.fromCharCode(65 + rem) + letters;
    n = Math.floor((n - 1) / 26);
  }
  return `${letters}${row + 1}`;
}

/** `"A5"` -> `[0, 4]`; `null` for anything else. */
export function parseLabel(text: string): Square | null {
  const m = /^([A-Z]{1,2})([1-9][0-9]{0,2})$/.exec(text);
  if (!m || m[1] === undefined) return null;
  let col = 0;
  for (const ch of m[1]) col = col * 26 + (ch.charCodeAt(0) - 64);
  return [col - 1, Number(m[2]) - 1];
}

export function sameSquare(a: Square, b: Square): boolean {
  return a[0] === b[0] && a[1] === b[1];
}

function isDoorEdge(snap: MapSnapshot, edge: MapEdge): boolean {
  return snap.features.some(
    (f) =>
      f.edge !== null &&
      f.edge.orient === edge.orient &&
      f.edge.col === edge.col &&
      f.edge.row === edge.row,
  );
}

/** Whether a wall the party knows of stands between two orthogonal
 * neighbours. A door's line is a wall in the wall layer, but the door can be
 * passed, so it doesn't block a drawn step. */
function walled(snap: MapSnapshot, a: Square, b: Square): boolean {
  let edge: MapEdge;
  if (a[1] === b[1]) {
    edge = { orient: "v", col: Math.max(a[0], b[0]), row: a[1] };
    if (snap.vwalls[edge.row]?.[edge.col] !== "|") return false;
  } else {
    edge = { orient: "h", col: a[0], row: Math.max(a[1], b[1]) };
    if (snap.hwalls[edge.row]?.[edge.col] !== "-") return false;
  }
  return !isDoorEdge(snap, edge);
}

/** A single step the drawing allows (the server checks it again). */
export function stepAllowed(snap: MapSnapshot, a: Square, b: Square): boolean {
  const dc = b[0] - a[0];
  const dr = b[1] - a[1];
  if (Math.max(Math.abs(dc), Math.abs(dr)) !== 1) return false;
  if (dc === 0 || dr === 0) return !walled(snap, a, b);
  const viaCol: Square = [b[0], a[1]];
  const viaRow: Square = [a[0], b[1]];
  return (
    !walled(snap, a, viaCol) &&
    !walled(snap, viaCol, b) &&
    !walled(snap, a, viaRow) &&
    !walled(snap, viaRow, b)
  );
}

function costOf(allowance: SceneAllowance, sq: Square): number | undefined {
  return allowance.costs[label(sq)];
}

/** The cheapest route from the mover's square to *target* by the server's
 * allowance, traced back from the target; `null` when it isn't reachable. */
export function traceRoute(
  snap: MapSnapshot,
  allowance: SceneAllowance,
  start: Square,
  target: Square,
): Square[] | null {
  if (costOf(allowance, target) === undefined) return null;
  const path: Square[] = [target];
  let here = target;
  for (let guard = 0; guard < 256 && !sameSquare(here, start); guard++) {
    const cost = costOf(allowance, here) ?? Infinity;
    // Grid diagonals cost the same as straight steps, so many routes tie;
    // among the cheapest, take the step that stays nearest the straight
    // line back to the start.
    let best: Square | null = null;
    let bestCost = cost;
    let bestOff = Infinity;
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dc === 0 && dr === 0) continue;
        const next: Square = [here[0] + dc, here[1] + dr];
        const c = sameSquare(next, start) ? 0 : costOf(allowance, next);
        if (c === undefined || c > bestCost || c >= cost) continue;
        if (!stepAllowed(snap, next, here)) continue;
        const off = (next[0] - start[0]) ** 2 + (next[1] - start[1]) ** 2;
        if (c === bestCost && off >= bestOff) continue;
        best = next;
        bestCost = c;
        bestOff = off;
      }
    }
    if (best === null) return null;
    path.unshift(best);
    here = best;
  }
  return sameSquare(here, start) ? path : null;
}

/** The route after a tap on *target*: a tap on the route cuts it back
 * there, a tap beside its end adds one square, and a far tap fills the
 * cheapest route to the target (path drawing doc). */
export function extendRoute(
  snap: MapSnapshot,
  allowance: SceneAllowance,
  route: Square[],
  target: Square,
): Square[] {
  const first = route[0];
  const last = route[route.length - 1];
  if (first === undefined || last === undefined) return route;
  const at = route.findIndex((s) => sameSquare(s, target));
  if (at >= 0) return route.slice(0, at + 1);
  if (stepAllowed(snap, last, target)) return [...route, target];
  const traced = traceRoute(snap, allowance, first, target);
  if (traced === null) return route;
  const through = traced.findIndex((s) => sameSquare(s, last));
  return through >= 0 ? [...route, ...traced.slice(through + 1)] : traced;
}

/** The mover's square in the view, if it has one. */
export function moverSquare(
  snap: MapSnapshot,
  allowance: SceneAllowance | null | undefined,
): Square | null {
  if (!allowance) return null;
  return (
    snap.tokens.find((t) => t.token_id === allowance.token_id)?.square ?? null
  );
}
