import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ stories: [], schema_version: 1 }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      ),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("opens the selected story's own view, remembers it, and goes back", async () => {
    const story = {
      story_id: "s1",
      title: "First",
      mode: "branching",
      status: "in_play",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      schema_version: 1,
    };
    const bodies: Record<string, unknown> = {
      "/api/stories": { stories: [story], schema_version: 1 },
      "/api/stories/s1": story,
      "/api/stories/s1/turns": { turns: [], schema_version: 1 },
      "/api/stories/s1/visible-state": { visible_state: null },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          new Response(JSON.stringify(bodies[url.split("?")[0]!]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      ),
    );
    render(<App />);

    (await screen.findByRole("button", { name: /^First/ })).click();
    expect(
      await screen.findByPlaceholderText("What do you do?"),
    ).toBeInTheDocument();
    expect(localStorage.getItem("afterworlds:last-story-id")).toBe("s1");
    act(() => screen.getByRole("button", { name: "Back to stories" }).click());
    expect(await screen.findByText("Your stories")).toBeInTheDocument();
  });

  it("renders the story list by default", async () => {
    render(<App />);
    expect(screen.getByText("Afterworlds")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Your stories")).toBeInTheDocument(),
    );
  });
});
