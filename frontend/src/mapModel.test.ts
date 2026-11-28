import { describe, expect, it } from "vitest";

import type { SceneView } from "./api/client";
import scene from "./fixtures/millYardScene.json";
import {
  asSnapshot,
  extendRoute,
  label,
  moverSquare,
  parseLabel,
  stepAllowed,
  traceRoute,
} from "./mapModel";
import type { Square } from "./mapModel";

const view = scene as unknown as SceneView;
const snap = asSnapshot(view.snapshot);
const allowance = view.allowance!;
const B5: Square = [1, 4];

describe("mapModel (issue #211)", () => {
  it("labels squares the way the server does", () => {
    expect(label([0, 0])).toBe("A1");
    expect(label([7, 4])).toBe("H5");
    expect(label([26, 9])).toBe("AA10");
    expect(parseLabel("AA10")).toEqual([26, 9]);
    expect(parseLabel("H5")).toEqual([7, 4]);
    expect(parseLabel("not")).toBeNull();
  });

  it("finds the mover's square from the allowance", () => {
    expect(moverSquare(snap, allowance)).toEqual(B5);
    expect(moverSquare(snap, null)).toBeNull();
  });

  it("a far tap fills the route the server priced", () => {
    const route = traceRoute(allowance, B5, [7, 4])!;
    expect(route.map(label)).toEqual([
      "B5",
      "C5",
      "D5",
      "E5",
      "F5",
      "G5",
      "H5",
    ]);
    expect(traceRoute(allowance, B5, [20, 20])).toBeNull();
  });

  it("keeps the server's route even where the costs suggest another", () => {
    // Codex round 9: a cheaper-looking way can need Dash or a second door,
    // so the far tap never rebuilds the route from costs.
    const detour = { ...allowance, routes: { ...allowance.routes } };
    detour.routes["E5"] = ["B5", "B6", "C7", "D7", "E6", "E5"];
    const route = traceRoute(detour, B5, [4, 4])!;
    expect(route.map(label)).toEqual(["B5", "B6", "C7", "D7", "E6", "E5"]);
    expect(extendRoute(snap, detour, [B5], [4, 4]).map(label)).toEqual(
      route.map(label),
    );
    // A route that doesn't start at the mover is not used.
    detour.routes["E5"] = ["C5", "D5", "E5"];
    expect(traceRoute(detour, B5, [4, 4])).toBeNull();
  });

  it("taps add a step, cut the route back, or fill to a far square", () => {
    let route: Square[] = [B5];
    route = extendRoute(snap, allowance, route, [2, 3]);
    expect(route.map(label)).toEqual(["B5", "C4"]);
    route = extendRoute(snap, allowance, route, [4, 2]);
    expect(route[route.length - 1]).toEqual([4, 2]);
    expect(route[0]).toEqual(B5);
    route = extendRoute(snap, allowance, route, [2, 3]);
    expect(route.map(label)).toEqual(["B5", "C4"]);
  });

  it("the garden wall blocks a drawn step but the line of a door does not", () => {
    // Wall on the line between B8 and C8.
    expect(stepAllowed(snap, [1, 7], [2, 7])).toBe(false);
    expect(stepAllowed(snap, [1, 6], [2, 6])).toBe(true);
    // The mill door's line between H5 and I5.
    expect(stepAllowed(snap, [7, 4], [8, 4])).toBe(true);
    expect(stepAllowed(snap, [1, 4], [3, 4])).toBe(false);
  });
});
