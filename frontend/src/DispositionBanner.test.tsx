import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { TurnSubmissionResponse } from "./api/client";
import DispositionBanner from "./DispositionBanner";

function response(
  overrides: Partial<TurnSubmissionResponse>,
): TurnSubmissionResponse {
  return {
    disposition: "delivered",
    turn_id: null,
    delivered_output: null,
    stable_prefix_cache_warmed: false,
    interaction_rejection_reason: null,
    interaction_rejection_message: null,
    pipeline_error_summary: null,
    provider_refusal: null,
    pending_roll_redirect_message: null,
    settlement_warning: null,
    visible_state: null,
    schema_version: 1,
    ...overrides,
  };
}

describe("DispositionBanner", () => {
  it.each(["delivered", "ooc_handled"] as const)(
    "renders nothing for %s",
    (disposition) => {
      const { container } = render(
        <DispositionBanner response={response({ disposition })} />,
      );
      expect(container).toBeEmptyDOMElement();
    },
  );

  it.each(["delivered", "ooc_handled"] as const)(
    "renders the settlement warning for %s instead of nothing",
    (disposition) => {
      render(
        <DispositionBanner
          response={response({
            disposition,
            settlement_warning: "Your credit balance could not be updated.",
          })}
        />,
      );
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Your credit balance could not be updated.",
      );
    },
  );

  it("renders a safety banner for blocked_input_safety", () => {
    render(
      <DispositionBanner
        response={response({ disposition: "blocked_input_safety" })}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/safety filter/);
  });

  it("renders the pipeline error summary", () => {
    render(
      <DispositionBanner
        response={response({
          disposition: "pipeline_error",
          pipeline_error_summary: "boom",
        })}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
  });

  it("renders the interaction rejection message for True CYOA", () => {
    render(
      <DispositionBanner
        response={response({
          disposition: "interaction_rejected",
          interaction_rejection_message: "Pick a listed option.",
        })}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Pick a listed option.",
    );
  });

  it("throws on an unhandled disposition (exhaustiveness guard)", () => {
    const bad = response({
      // @ts-expect-error -- deliberately simulating an unmodeled disposition
      disposition: "some_future_disposition",
    });
    expect(() => render(<DispositionBanner response={bad} />)).toThrow();
  });
});
