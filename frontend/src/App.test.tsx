import { render, screen, waitFor } from "@testing-library/react";
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

  it("renders the story list by default", async () => {
    render(<App />);
    expect(screen.getByText("Afterworlds")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("Your stories")).toBeInTheDocument(),
    );
  });
});
