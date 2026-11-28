/**
 * Issue #211 (mapper M1): the scene map on graph paper, and drawing a move.
 *
 * Display only. Opening, closing or auto-opening the map changes no Turn:
 * Sojourn consults the scene on every Turn either way, and reading the view
 * writes nothing. A drawn route goes to the server with the hash of the view
 * it was drawn on; the server walks it again and decides what happens.
 *
 * Look (graph-paper doc): straight grid lines, Rough.js wobble on walls and
 * features only (orderly for worked stone, looser for natural rock),
 * charcoal crosshatching for solid rock, lettered SVG tokens.
 */
import { useEffect, useMemo, useState } from "react";
import rough from "roughjs";

import { api, ApiRequestError } from "./api/client";
import type { MovePath, SceneAllowance, SceneView } from "./api/client";
import { localStorageState } from "./localStorage";
import {
  asSnapshot,
  extendRoute,
  label,
  moverSquare,
  parseLabel,
  sameSquare,
} from "./mapModel";
import type { MapSnapshot, Square } from "./mapModel";

const CELL = 28;
const PAD = 18;
const INK = "#3a3a3a";
const GRID = "#b9c8d6";

const generator = rough.generator();

function seedFor(key: string): number {
  let h = 2166136261;
  for (let i = 0; i < key.length; i++) {
    h ^= key.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) % 2147483646 || 1;
}

function roughPaths(
  drawable: ReturnType<typeof generator.line>,
  key: string,
): JSX.Element[] {
  return generator
    .toPaths(drawable)
    .map((p, i) => (
      <path
        key={`${key}-${i}`}
        d={p.d}
        stroke={p.stroke}
        strokeWidth={p.strokeWidth}
        fill={p.fill ?? "none"}
      />
    ));
}

function areaSetting(snap: MapSnapshot, sq: Square): "worked" | "natural" {
  const area = snap.areas.find(
    (a) =>
      sq[0] >= a.bounds[0] &&
      sq[0] < a.bounds[0] + a.bounds[2] &&
      sq[1] >= a.bounds[1] &&
      sq[1] < a.bounds[1] + a.bounds[3],
  );
  return area?.setting ?? "worked";
}

/** The server's warning on a square whose cheapest route needs Dash. */
const USES_DASH = "uses your Dash";

function usesDash(allowance: SceneAllowance, square: string): boolean {
  return allowance.warnings[square] === USES_DASH;
}

function x(col: number): number {
  return PAD + col * CELL;
}
function y(row: number): number {
  return PAD + row * CELL;
}

function Paper({ snap, mapId }: { snap: MapSnapshot; mapId: string }) {
  const elements = useMemo(() => {
    const out: JSX.Element[] = [];
    const opts = (key: string, sq: Square) => {
      const natural = areaSetting(snap, sq) === "natural";
      return {
        seed: seedFor(`${mapId}:${key}`),
        stroke: INK,
        strokeWidth: 2,
        roughness: natural ? 1.8 : 0.6,
        bowing: natural ? 2 : 0.5,
      };
    };
    snap.terrain.forEach((line, r) => {
      [...line].forEach((ch, c) => {
        if (ch === "#") {
          const key = `rock-${c}-${r}`;
          out.push(
            ...roughPaths(
              generator.rectangle(x(c), y(r), CELL, CELL, {
                ...opts(key, [c, r]),
                strokeWidth: 0.6,
                fill: INK,
                fillStyle: "cross-hatch",
                hachureGap: 5,
              }),
              key,
            ),
          );
        } else if (ch === "~") {
          out.push(
            <path
              key={`water-${c}-${r}`}
              d={`M${x(c) + 4} ${y(r) + 14} q5 -5 10 0 t10 0`}
              stroke="#6b8aa6"
              fill="none"
            />,
          );
        } else if (ch === ",") {
          out.push(
            <path
              key={`rough-${c}-${r}`}
              d={`M${x(c) + 8} ${y(r) + 18} l2 -6 M${x(c) + 16} ${y(r) + 20} l2 -6`}
              stroke="#7a7a5a"
            />,
          );
        }
      });
    });
    snap.hwalls.forEach((line, r) => {
      [...line].forEach((ch, c) => {
        if (ch !== "-") return;
        const key = `hw-${c}-${r}`;
        out.push(
          ...roughPaths(
            generator.line(x(c), y(r), x(c + 1), y(r), opts(key, [c, r])),
            key,
          ),
        );
      });
    });
    snap.vwalls.forEach((line, r) => {
      [...line].forEach((ch, c) => {
        if (ch !== "|") return;
        const key = `vw-${c}-${r}`;
        out.push(
          ...roughPaths(
            generator.line(x(c), y(r), x(c), y(r + 1), opts(key, [c, r])),
            key,
          ),
        );
      });
    });
    for (const pit of snap.pits) {
      for (const [c, r] of pit.squares) {
        const key = `pit-${pit.pit_id}-${c}-${r}`;
        out.push(
          ...roughPaths(
            generator.rectangle(x(c) + 3, y(r) + 3, CELL - 6, CELL - 6, {
              ...opts(key, [c, r]),
              strokeWidth: 1.2,
              fill: INK,
              fillStyle: "hachure",
              hachureGap: 4,
            }),
            key,
          ),
        );
      }
    }
    for (const f of snap.features) {
      if (f.edge) {
        const { orient, col, row } = f.edge;
        const open = f.state === "open";
        const key = `door-${f.feature_id}`;
        const [x1, y1, w, h] =
          orient === "v"
            ? [x(col) - 3, y(row) + 6, 6, CELL - 12]
            : [x(col) + 6, y(row) - 3, CELL - 12, 6];
        out.push(
          <rect
            key={`${key}-gap`}
            x={x1}
            y={y1}
            width={w}
            height={h}
            fill="#fbfaf5"
          />,
          ...roughPaths(
            generator.rectangle(x1, y1, w, h, {
              ...opts(key, [col, row]),
              strokeWidth: 1.4,
              fill: open ? undefined : "#c9b48a",
              fillStyle: "solid",
            }),
            key,
          ),
        );
      }
      for (const [c, r] of f.squares) {
        const key = `feat-${f.feature_id}-${c}-${r}`;
        out.push(
          ...roughPaths(
            generator.circle(x(c) + CELL / 2, y(r) + CELL / 2, CELL - 8, {
              ...opts(key, [c, r]),
              strokeWidth: 1.4,
            }),
            key,
          ),
        );
      }
    }
    return out;
  }, [snap, mapId]);
  return <g aria-hidden="true">{elements}</g>;
}

export default function MapView({
  storyId,
  refreshKey,
  disabled,
  onSendMove,
}: {
  storyId: string;
  refreshKey: number;
  disabled: boolean;
  onSendMove: (movePath: MovePath) => Promise<boolean>;
}) {
  const [view, setView] = useState<SceneView | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [autoOpen, setAutoOpen] = useState(() =>
    localStorageState.getMapAutoOpen(),
  );
  const [open, setOpen] = useState(autoOpen);
  const [route, setRoute] = useState<Square[]>([]);
  const [dash, setDash] = useState(false);
  const [disengage, setDisengage] = useState(false);

  useEffect(() => {
    let live = true;
    api
      .getScene(storyId)
      .then((v) => {
        if (!live) return;
        setView(v);
        setLoadError(null);
        setRoute([]);
        setDash(false);
      })
      .catch((err: unknown) => {
        if (!live) return;
        setLoadError(
          err instanceof ApiRequestError
            ? err.apiError.message
            : "The map couldn't be read.",
        );
      });
    return () => {
      live = false;
    };
  }, [storyId, refreshKey]);

  if (view === null) {
    return loadError ? (
      <p className="map-error" role="alert">
        {loadError}
      </p>
    ) : null;
  }

  const snap = asSnapshot(view.snapshot);
  const allowance = view.allowance ?? null;
  const start = moverSquare(snap, allowance);
  const end = route.length > 1 ? route[route.length - 1] : null;
  const endCost = end && allowance ? allowance.costs[label(end)] : undefined;
  // The server says which squares need Dash: a Swim or Climb Speed can carry
  // a route past the walking Speed without it (glossary.speed › switching).
  const needsDash =
    end && endCost !== undefined && allowance !== null
      ? usesDash(allowance, label(end))
      : false;
  const warning = end && allowance ? allowance.warnings[label(end)] : undefined;

  function tap(sq: Square) {
    if (disabled || !allowance || !start) return;
    if (route.length === 0) {
      if (sameSquare(sq, start)) setRoute([start]);
      else {
        const next = extendRoute(snap, allowance, [start], sq);
        setRoute(next.length > 1 ? next : []);
      }
      return;
    }
    setRoute(extendRoute(snap, allowance, route, sq));
  }

  async function send() {
    if (route.length < 2) return;
    const ok = await onSendMove({
      squares: route.map(label),
      dash,
      disengage,
      view_hash: view!.view_hash,
      schema_version: 1,
    });
    if (ok) {
      setRoute([]);
      setDash(false);
      setDisengage(false);
    }
  }

  const width = PAD * 2 + snap.width * CELL;
  const height = PAD * 2 + snap.height * CELL;

  return (
    <section className="map-view" aria-label="Scene map">
      <div className="map-controls">
        <button type="button" onClick={() => setOpen((o) => !o)}>
          {open ? "Hide map" : "Show map"}
        </button>{" "}
        <label>
          <input
            type="checkbox"
            checked={autoOpen}
            onChange={(e) => {
              setAutoOpen(e.target.checked);
              localStorageState.setMapAutoOpen(e.target.checked);
            }}
          />{" "}
          Open the map automatically
        </label>
      </div>
      {open && (
        <>
          <svg
            role="img"
            aria-label={`Map of ${view.label}`}
            width={width}
            height={height}
            viewBox={`0 0 ${width} ${height}`}
            style={{ background: "#fbfaf5", maxWidth: "100%" }}
          >
            {Array.from({ length: snap.width + 1 }, (_, c) => (
              <line
                key={`gc-${c}`}
                x1={x(c)}
                y1={y(0)}
                x2={x(c)}
                y2={y(snap.height)}
                stroke={GRID}
                strokeWidth={0.5}
              />
            ))}
            {Array.from({ length: snap.height + 1 }, (_, r) => (
              <line
                key={`gr-${r}`}
                x1={x(0)}
                y1={y(r)}
                x2={x(snap.width)}
                y2={y(r)}
                stroke={GRID}
                strokeWidth={0.5}
              />
            ))}
            {allowance &&
              Object.keys(allowance.costs).map((sq) => {
                const at = parseLabel(sq);
                if (at === null) return null;
                const [col, row] = at;
                return (
                  <rect
                    key={`reach-${sq}`}
                    data-reach={sq}
                    x={x(col)}
                    y={y(row)}
                    width={CELL}
                    height={CELL}
                    fill={usesDash(allowance, sq) ? "#e8dc9a" : "#9fd4a6"}
                    opacity={0.35}
                  />
                );
              })}
            <Paper snap={snap} mapId={view.map_id} />
            {route.length > 1 && (
              <polyline
                data-testid="route"
                points={route
                  .map(([c, r]) => `${x(c) + CELL / 2},${y(r) + CELL / 2}`)
                  .join(" ")}
                stroke="#b5462f"
                strokeWidth={3}
                strokeDasharray="6 4"
                fill="none"
              />
            )}
            {snap.tokens
              .filter((t) => t.square !== null)
              .map((t) => {
                const [c, r] = t.square as Square;
                const party = t.side === "party";
                return (
                  <g key={t.token_id} aria-label={t.label || t.token_id}>
                    <circle
                      cx={x(c) + CELL / 2}
                      cy={y(r) + CELL / 2}
                      r={CELL / 2 - 3}
                      fill={party ? INK : "#fbfaf5"}
                      stroke={INK}
                      strokeWidth={1.5}
                    />
                    <text
                      x={x(c) + CELL / 2}
                      y={y(r) + CELL / 2 + 5}
                      textAnchor="middle"
                      fontSize={14}
                      fontFamily="Georgia, serif"
                      fill={party ? "#fbfaf5" : INK}
                    >
                      {t.glyph}
                    </text>
                  </g>
                );
              })}
            {Array.from({ length: snap.height }, (_, r) =>
              Array.from({ length: snap.width }, (_, c) => (
                <rect
                  key={`hit-${c}-${r}`}
                  data-square={label([c, r])}
                  aria-label={label([c, r])}
                  x={x(c)}
                  y={y(r)}
                  width={CELL}
                  height={CELL}
                  fill="transparent"
                  onClick={() => tap([c, r])}
                />
              )),
            )}
          </svg>
          {allowance && (
            <div className="map-move">
              <p>
                {end
                  ? `Route to ${label(end)}${
                      endCost !== undefined ? ` (${endCost} ft)` : ""
                    }.`
                  : "Tap your square or a destination to draw a move."}
                {warning ? ` ${warning}` : ""}
              </p>
              <label>
                <input
                  type="checkbox"
                  checked={dash}
                  disabled={disabled}
                  onChange={(e) => setDash(e.target.checked)}
                />{" "}
                Dash
              </label>{" "}
              <label>
                <input
                  type="checkbox"
                  checked={disengage}
                  disabled={disabled}
                  onChange={(e) => setDisengage(e.target.checked)}
                />{" "}
                Disengage
              </label>{" "}
              {needsDash && !dash && <span>This route needs a Dash.</span>}{" "}
              <button
                type="button"
                disabled={disabled || route.length < 2 || (needsDash && !dash)}
                onClick={() => send()}
              >
                Send move
              </button>{" "}
              <button
                type="button"
                disabled={route.length === 0}
                onClick={() => setRoute([])}
              >
                Clear route
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
