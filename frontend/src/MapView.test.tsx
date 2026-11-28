import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { SceneView } from "./api/client";
import scene from "./fixtures/millYardScene.json";
import MapView from "./MapView";

const view = scene as unknown as SceneView;

const mocks = vi.hoisted(() => ({ getScene: vi.fn() }));

vi.mock("./api/client", async () => {
  const actual =
    await vi.importActual<typeof import("./api/client")>("./api/client");
  return { ...actual, api: { getScene: mocks.getScene } };
});

function tapSquare(container: HTMLElement, square: string) {
  const el = container.querySelector(`[data-square="${square}"]`);
  if (!el) throw new Error(`no square ${square}`);
  fireEvent.click(el);
}

describe("MapView (issue #211)", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.getScene.mockReset();
    mocks.getScene.mockResolvedValue(view);
  });

  it("shows nothing for a story with no active scene", async () => {
    mocks.getScene.mockResolvedValue(null);
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.getScene).toHaveBeenCalled());
    expect(container.querySelector("section")).toBeNull();
  });

  it("opening and closing the map only reads the view", async () => {
    const onSendMove = vi.fn();
    render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={onSendMove}
      />,
    );
    const show = await screen.findByRole("button", { name: "Show map" });
    expect(screen.queryByRole("img")).toBeNull();
    fireEvent.click(show);
    expect(screen.getByRole("img", { name: /mill yard/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Hide map" }));
    expect(screen.queryByRole("img")).toBeNull();
    expect(mocks.getScene).toHaveBeenCalledTimes(1);
    expect(onSendMove).not.toHaveBeenCalled();
  });

  it("auto-open is a saved view preference that only opens the map", async () => {
    const first = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={vi.fn()}
      />,
    );
    fireEvent.click(
      await screen.findByRole("checkbox", {
        name: /open the map automatically/i,
      }),
    );
    first.unmount();
    render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={vi.fn()}
      />,
    );
    expect(await screen.findByRole("img")).toBeInTheDocument();
    expect(mocks.getScene).toHaveBeenCalledTimes(2);
  });

  it("shades reachable squares and hides nothing it wasn't sent", async () => {
    localStorage.setItem("afterworlds:map-auto-open", "true");
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={vi.fn()}
      />,
    );
    await screen.findByRole("img");
    expect(container.querySelector('[data-reach="E5"]')).not.toBeNull();
    expect(container.innerHTML).not.toMatch(/hidden-pit|lurker|secret/);
  });

  it("a far tap draws the route and Send move posts it with the view hash", async () => {
    localStorage.setItem("afterworlds:map-auto-open", "true");
    const onSendMove = vi.fn().mockResolvedValue(true);
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={onSendMove}
      />,
    );
    await screen.findByRole("img");
    tapSquare(container, "H5");
    expect(screen.getByText(/Route to H5 \(30 ft\)/)).toBeInTheDocument();
    expect(screen.getByTestId("route")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: "Disengage" }));
    fireEvent.click(screen.getByRole("button", { name: "Send move" }));
    await waitFor(() => expect(onSendMove).toHaveBeenCalledTimes(1));
    expect(onSendMove).toHaveBeenCalledWith({
      squares: ["B5", "C5", "D5", "E5", "F5", "G5", "H5"],
      dash: false,
      disengage: true,
      view_hash: view.view_hash,
      schema_version: 1,
    });
    await waitFor(() => expect(screen.queryByTestId("route")).toBeNull());
  });

  it("a route past the mover's speed waits for a tapped Dash", async () => {
    localStorage.setItem("afterworlds:map-auto-open", "true");
    // The whole yard is within 30 ft of Kael, so this view has the server
    // say H5 needs Dash (display logic only; the server prices every move).
    mocks.getScene.mockResolvedValue({
      ...view,
      allowance: {
        ...view.allowance!,
        speed_ft: 20,
        warnings: { H5: "uses your Dash" },
      },
    });
    const far = ["H5"];
    const onSendMove = vi.fn().mockResolvedValue(true);
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={onSendMove}
      />,
    );
    await screen.findByRole("img");
    tapSquare(container, far[0] ?? "H5");
    expect(screen.getByText("This route needs a Dash.")).toBeInTheDocument();
    const send = screen.getByRole("button", { name: "Send move" });
    expect(send).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox", { name: "Dash" }));
    expect(send).toBeEnabled();
  });

  it("takes the Dash requirement from the server, not the walking Speed", async () => {
    // Codex round 7: Speed 10 with Swim Speed 60 swims 30 ft without Dash,
    // so a cost past speed_ft alone doesn't need it.
    localStorage.setItem("afterworlds:map-auto-open", "true");
    mocks.getScene.mockResolvedValue({
      ...view,
      allowance: { ...view.allowance!, speed_ft: 10, warnings: {} },
    });
    const onSendMove = vi.fn().mockResolvedValue(true);
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={onSendMove}
      />,
    );
    await screen.findByRole("img");
    tapSquare(container, "H5");
    expect(screen.queryByText("This route needs a Dash.")).toBeNull();
    expect(screen.getByRole("button", { name: "Send move" })).toBeEnabled();
    const shade = container.querySelector('[data-reach="H5"]');
    expect(shade?.getAttribute("fill")).toBe("#9fd4a6");
  });

  it("gives the server's figures only for the route it priced", async () => {
    // Codex round 9: cost and Dash depend on the way taken, so a hand-drawn
    // route that isn't the priced one is left for the server to price.
    localStorage.setItem("afterworlds:map-auto-open", "true");
    mocks.getScene.mockResolvedValue({
      ...view,
      allowance: { ...view.allowance!, warnings: { H5: "uses your Dash" } },
    });
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={vi.fn().mockResolvedValue(true)}
      />,
    );
    await screen.findByRole("img");
    for (const sq of ["B5", "C4", "D4", "E4", "F4", "G4", "H5"]) {
      tapSquare(container, sq);
    }
    expect(
      screen.getByText(/Route to H5\. Sojourn prices this route/),
    ).toBeInTheDocument();
    expect(screen.queryByText("This route needs a Dash.")).toBeNull();
    expect(screen.getByRole("button", { name: "Send move" })).toBeEnabled();
    // The priced route to H5 gets its cost and its Dash requirement.
    fireEvent.click(screen.getByRole("button", { name: "Clear route" }));
    tapSquare(container, "H5");
    expect(screen.getByText(/Route to H5 \(30 ft\)\./)).toBeInTheDocument();
    expect(screen.getByText("This route needs a Dash.")).toBeInTheDocument();
  });

  it("keeps the route when the server doesn't take the move", async () => {
    localStorage.setItem("afterworlds:map-auto-open", "true");
    const onSendMove = vi.fn().mockResolvedValue(false);
    const { container } = render(
      <MapView
        storyId="s"
        refreshKey={0}
        disabled={false}
        onSendMove={onSendMove}
      />,
    );
    await screen.findByRole("img");
    tapSquare(container, "D3");
    fireEvent.click(screen.getByRole("button", { name: "Send move" }));
    await waitFor(() => expect(onSendMove).toHaveBeenCalled());
    expect(screen.getByTestId("route")).toBeInTheDocument();
  });
});
