import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(null, { status: 200 }))),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders and reports API health", async () => {
    render(<App />);
    expect(screen.getByText("Afterworlds")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId("health-status")).toHaveTextContent("ok"),
    );
  });
});
