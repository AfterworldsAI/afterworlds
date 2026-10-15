import { useState } from "react";

import type {
  PendingInteraction,
  PendingRoll,
  RollSubmission,
} from "./api/client";

/**
 * The minimum CRD Issue 15b pending-interaction affordance: the backend's
 * player view rendered as-is, with the operations it offers. Values the
 * Sojourner rolled are passed through unvalidated and uncomputed -- the
 * backend owns validation, totals and outcomes. The dice tray, scorecard and
 * browser dice belong to CRD Issue 19b.
 */
export default function RpgPendingInteraction({
  interaction,
  disabled,
  onRoll,
  onAdjust,
  onDecide,
  onResume,
}: {
  interaction: PendingInteraction;
  disabled: boolean;
  onRoll: (body: RollSubmission) => void;
  onAdjust: (optionId: string) => void;
  onDecide: (optionId: string) => void;
  onResume: () => void;
}) {
  const roll = interaction.pending_roll;
  const decision = interaction.pending_decision;
  return (
    <section className="rpg-pending-interaction" aria-label="Pending action">
      {roll && (
        <PendingRollForm
          // A revised instruction is a new form: no stale values carry over.
          key={`${roll.instruction_id}:${roll.instruction_revision}`}
          roll={roll}
          disabled={disabled}
          onRoll={onRoll}
          onAdjust={onAdjust}
        />
      )}
      {decision && (
        <div>
          <p>{decision.prompt}</p>
          {decision.options.map((option) => (
            <button
              key={option.option_id}
              type="button"
              disabled={disabled}
              onClick={() => onDecide(option.option_id)}
            >
              {option.player_visible_label}
            </button>
          ))}
        </div>
      )}
      {interaction.interaction_phase === "ready_for_narration" && (
        <button type="button" disabled={disabled} onClick={onResume}>
          Narrate the resolved action
        </button>
      )}
    </section>
  );
}

function PendingRollForm({
  roll,
  disabled,
  onRoll,
  onAdjust,
}: {
  roll: PendingRoll;
  disabled: boolean;
  onRoll: (body: RollSubmission) => void;
  onAdjust: (optionId: string) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onRoll({
          source: "physical_self_report",
          pending_roll_request_id: roll.pending_roll_request_id,
          expected_instruction_revision: roll.instruction_revision,
          term_results: roll.terms.map((term) => ({
            term_id: term.term_id,
            values: (values[term.term_id] ?? "")
              .split(/[\s,]+/)
              .filter(Boolean)
              .map(Number),
            schema_version: 1,
          })),
          schema_version: 1,
        });
      }}
    >
      <p>
        Roll needed: {roll.display_label} ({roll.display_expression})
      </p>
      {roll.terms.map((term) => (
        <label key={term.term_id}>
          {term.label ?? `${term.count}d${term.sides}`} faces rolled
          <input
            value={values[term.term_id] ?? ""}
            disabled={disabled}
            onChange={(e) =>
              setValues({ ...values, [term.term_id]: e.target.value })
            }
          />
        </label>
      ))}
      <button type="submit" disabled={disabled}>
        Submit roll
      </button>
      {roll.adjustment_options.map((option) => (
        <button
          key={option.option_id}
          type="button"
          disabled={disabled}
          onClick={() => onAdjust(option.option_id)}
        >
          {option.player_visible_label}
        </button>
      ))}
    </form>
  );
}
