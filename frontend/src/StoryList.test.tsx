import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import StoryList from "./StoryList";

const mocks = vi.hoisted(() => ({
  listStories: vi.fn(),
  createStory: vi.fn(),
}));

vi.mock("./api/client", async () => {
  const actual =
    await vi.importActual<typeof import("./api/client")>("./api/client");
  return {
    ...actual,
    api: { listStories: mocks.listStories, createStory: mocks.createStory },
  };
});

describe("StoryList new-story modes (ADR-017b)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listStories.mockResolvedValue([]);
    mocks.createStory.mockResolvedValue({ story_id: "s1" });
  });

  it("offers only Branching and RPG, defaulting to Branching", async () => {
    render(<StoryList onSelect={() => {}} />);
    const select = screen.getByRole("combobox");
    expect(select).toHaveValue("branching");
    const options = screen
      .getAllByRole("option")
      .map((o) => (o as HTMLOptionElement).value);
    expect(options).toEqual(["branching", "rpg"]);
    expect(screen.queryByText(/writing/i)).not.toBeInTheDocument();
  });

  it("submits the default as a Branching story", async () => {
    const onSelect = vi.fn();
    render(<StoryList onSelect={onSelect} />);
    fireEvent.change(screen.getByPlaceholderText("Title"), {
      target: { value: "New tale" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    await waitFor(() => expect(onSelect).toHaveBeenCalledWith("s1"));
    expect(mocks.createStory).toHaveBeenCalledWith(
      expect.objectContaining({ title: "New tale", mode: "branching" }),
    );
  });
});
