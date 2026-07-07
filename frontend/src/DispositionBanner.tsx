import type { TurnSubmissionResponse } from "./api/client";

/**
 * Renders every non-DELIVERED/OOC_HANDLED disposition per the spec's
 * normative Disposition -> UI Behavior table. The `never` branch below
 * makes an unhandled disposition a compile error (Binding Decision 11),
 * not a silent fallback.
 */
export default function DispositionBanner({
  response,
}: {
  response: TurnSubmissionResponse;
}) {
  switch (response.disposition) {
    case "delivered":
    case "ooc_handled":
      return null; // rendered into the transcript instead, not banner text
    case "blocked_input_safety":
      return (
        <Banner kind="safety">
          This input was blocked by the safety filter.
        </Banner>
      );
    case "blocked_output_safety":
      return (
        <Banner kind="safety">
          The generated response was blocked by the safety filter.
        </Banner>
      );
    case "blocked_contradiction":
      return (
        <Banner kind="continuity">
          That action would contradict established canon and was not applied.
        </Banner>
      );
    case "refused_by_provider":
      return (
        <Banner kind="refusal">
          {response.provider_refusal
            ? `The AI provider declined to respond${response.provider_refusal.coarse_reason ? `: ${response.provider_refusal.coarse_reason}` : "."}`
            : "The AI provider declined to respond."}
        </Banner>
      );
    case "pipeline_error":
      return (
        <Banner kind="error">
          {response.pipeline_error_summary ??
            "Something went wrong processing that turn."}{" "}
          Please try submitting again.
        </Banner>
      );
    case "blocked_pending_roll":
      return (
        <Banner kind="pending-roll">
          {response.pending_roll_redirect_message ??
            "Resolve the pending dice roll before continuing."}
        </Banner>
      );
    case "interaction_rejected":
      return (
        <Banner kind="rejected">
          {response.interaction_rejection_message ??
            "That input was not a valid choice."}
        </Banner>
      );
    default: {
      // Exhaustiveness guard: a new PipelineDisposition value fails tsc here.
      const _exhaustive: never = response.disposition;
      throw new Error(`Unhandled disposition: ${String(_exhaustive)}`);
    }
  }
}

function Banner({
  kind,
  children,
}: {
  kind: string;
  children: React.ReactNode;
}) {
  return (
    <div className="disposition-banner" data-kind={kind} role="alert">
      {children}
    </div>
  );
}
