import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { VisibleState } from "./api/client";
import VisibleStatePanel from "./VisibleStatePanel";

function branchingVisibleState(
  overrides: Partial<
    Extract<VisibleState, { interaction_style: unknown }>
  > = {},
): VisibleState {
  return {
    schema_version: 1,
    interaction_style: "hybrid",
    branching_cadence: "balanced",
    branch_count_range: null,
    freeform_available: true,
    length_preference: null,
    last_branch_options: [
      { option_id: "opt_1", action_text: "Open the door." },
      { option_id: "opt_2", action_text: "Climb the wall." },
    ],
    ...overrides,
  };
}

describe("VisibleStatePanel branch-card selection (PR #126 round 8 P2)", () => {
  it("submits a resolver-supported token derived from option_id, not the action label", () => {
    const onBranchOptionClick = vi.fn();
    render(
      <VisibleStatePanel
        visibleState={branchingVisibleState()}
        onBranchOptionClick={onBranchOptionClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Climb the wall." }));

    expect(onBranchOptionClick).toHaveBeenCalledTimes(1);
    const submitted = onBranchOptionClick.mock.calls[0]?.[0] as string;
    expect(submitted).toMatch(/option 2|opt_2/);
    // Regression: must not submit only the free-text action label -- the
    // validator does not resolve it.
    expect(submitted).not.toBe("Climb the wall.");
    expect(submitted).not.toBe("I choose: Climb the wall.");
  });

  it("keeps the displayed button label as the option's action_text", () => {
    render(
      <VisibleStatePanel
        visibleState={branchingVisibleState()}
        onBranchOptionClick={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Open the door." }),
    ).toBeInTheDocument();
  });

  it("falls back to the raw option_id when it doesn't match the opt_N shape", () => {
    const onBranchOptionClick = vi.fn();
    render(
      <VisibleStatePanel
        visibleState={branchingVisibleState({
          last_branch_options: [
            { option_id: "weird-id", action_text: "Do something odd." },
          ],
        })}
        onBranchOptionClick={onBranchOptionClick}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Do something odd." }));

    expect(onBranchOptionClick).toHaveBeenCalledWith("I choose weird-id.");
  });
});
