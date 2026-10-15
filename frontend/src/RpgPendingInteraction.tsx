import { useState } from "react";

import type {
  PendingInteraction,
  PendingRoll,
  RollSubmission,
} from "./api/client";
import { browserRandomSource } from "./browserRandom";
import { DiceError, parseFaceList, rollTerms, score } from "./dice-core";
import type { Scorecard } from "./dice-core";
import "./dice.css";

/**
 * The pending-interaction surface (CRD Issue 15b's minimum controls, with
 * CRD Issue 19b's dice): the backend's player view rendered as-is, with the
 * operations it offers. Browser dice and the scorecard are a player-supplied
 * report and its preview -- the backend validates the raw faces and derives
 * selections, totals and outcomes itself.
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
          // A revised instruction is a new form: no stale values or digital
          // candidate carry over to another request or revision.
          key={`${roll.pending_roll_request_id}:${roll.instruction_id}:${roll.instruction_revision}`}
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

function signed(n: number) {
  return n < 0 ? `- ${-n}` : `+ ${n}`;
}

function termName(term: PendingRoll["terms"][number]) {
  const dice = `${term.count}d${term.sides}`;
  const rule =
    term.selection_rule === "sum_all"
      ? ""
      : ` keep ${term.selection_rule === "keep_highest" ? "highest" : "lowest"} ${term.keep_count}`;
  const sign = term.contribution === "subtract" ? "minus " : "";
  return `${sign}${term.label ? `${term.label} (${dice}${rule})` : `${dice}${rule}`}`;
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
  const terms = roll.terms;
  // One digital candidate for this request and revision: generated before
  // any animation, kept until this form is replaced, never re-rolled here.
  const [candidate, setCandidate] = useState<Scorecard | null>(null);
  const [diceError, setDiceError] = useState<string | null>(null);
  const [faces, setFaces] = useState<Record<string, string>>({});
  const parsed = terms.map((term) =>
    parseFaceList(faces[term.term_id] ?? "", term.count, term.sides),
  );
  const progress = roll.progress;

  function rollDigital() {
    const source = browserRandomSource();
    if (!source) {
      setDiceError(
        "Secure browser randomness is unavailable. Enter the faces you rolled instead.",
      );
      return;
    }
    try {
      const next = score(
        terms,
        rollTerms(terms, source),
        roll.visible_modifier_total,
      );
      // A second same-tick click never replaces the first candidate.
      setCandidate((current) => current ?? next);
    } catch (err) {
      setDiceError(
        err instanceof DiceError
          ? `Digital dice are unavailable for this roll: ${err.message} Enter the faces you rolled instead.`
          : "Secure browser randomness failed. Enter the faces you rolled instead.",
      );
    }
  }

  function submit(
    source: "inline_ui" | "physical_self_report",
    values: number[][],
  ) {
    onRoll({
      source,
      pending_roll_request_id: roll.pending_roll_request_id,
      expected_instruction_revision: roll.instruction_revision,
      term_results: terms.map((term, i) => ({
        term_id: term.term_id,
        values: values[i]!,
        schema_version: 1,
      })),
      schema_version: 1,
    });
  }

  return (
    <div className="pending-roll">
      <p>
        Roll needed: {roll.display_label} ({roll.display_expression})
      </p>
      <p>
        Step {progress.step_index}
        {progress.known_step_count != null &&
          ` of ${progress.known_step_count}`}
        {progress.sequence_label && ` — ${progress.sequence_label}`}
        {progress.step_label && `: ${progress.step_label}`}
      </p>
      <ul aria-label="Dice">
        {terms.map((term) => (
          <li key={term.term_id}>{termName(term)}</li>
        ))}
      </ul>
      {roll.visible_modifiers.length > 0 && (
        <ul aria-label="Visible modifiers">
          {roll.visible_modifiers.map((m) => (
            <li key={m.modifier_id}>
              {m.label} {signed(m.value)}
            </li>
          ))}
        </ul>
      )}
      <p>Visible modifiers total: {signed(roll.visible_modifier_total)}</p>

      <div className="digital-roll">
        {!candidate && (
          <button
            type="button"
            disabled={disabled || diceError !== null}
            onClick={rollDigital}
          >
            Roll dice
          </button>
        )}
        {diceError && <p role="status">{diceError}</p>}
        {candidate && (
          <>
            <RollScorecard roll={roll} card={candidate} />
            <button
              type="button"
              disabled={disabled}
              onClick={() =>
                submit(
                  "inline_ui",
                  candidate.terms.map((t) => t.values),
                )
              }
            >
              Submit digital roll
            </button>
          </>
        )}
      </div>

      <form
        className="physical-roll"
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          if (parsed.every((p) => p.ok)) {
            submit(
              "physical_self_report",
              parsed.map((p) => (p.ok ? p.values : [])),
            );
          }
        }}
      >
        <p>Or enter the faces you rolled with physical dice:</p>
        {terms.map((term, i) => {
          const text = faces[term.term_id] ?? "";
          const result = parsed[i]!;
          const invalid = text.trim() !== "" && !result.ok;
          const hintId = `faces-hint-${term.term_id}`;
          return (
            <label key={term.term_id}>
              {termName(term)} faces rolled
              <input
                value={text}
                inputMode="numeric"
                disabled={disabled}
                aria-invalid={invalid}
                aria-describedby={invalid ? hintId : undefined}
                onChange={(e) =>
                  setFaces({ ...faces, [term.term_id]: e.target.value })
                }
              />
              {invalid && !result.ok && (
                <span id={hintId} role="status">
                  {result.error}
                </span>
              )}
            </label>
          );
        })}
        <button type="submit" disabled={disabled || !parsed.every((p) => p.ok)}>
          Submit physical roll
        </button>
      </form>

      {roll.adjustment_options.map((option) => (
        <button
          key={option.option_id}
          type="button"
          disabled={disabled}
          onClick={() => onAdjust(option.option_id)}
        >
          {option.player_visible_label}
          {option.resource_preview && ` (${option.resource_preview})`}
        </button>
      ))}
    </div>
  );
}

/**
 * The unsubmitted digital candidate: every raw face, kept and discarded,
 * signed term subtotals and the visible modifiers once. The CSS tumble is
 * decoration over these final faces; it never changes or delays them.
 */
function RollScorecard({ roll, card }: { roll: PendingRoll; card: Scorecard }) {
  return (
    <div className="dice-scorecard" role="group" aria-label="Roll preview">
      <p>
        Unsubmitted preview — the result is decided when the roll is accepted.
      </p>
      {card.terms.map((scored, t) => (
        <p key={scored.term_id}>
          {termName(roll.terms[t]!)}:{" "}
          {scored.values.map((value, i) => (
            <span
              key={i}
              className="dice-face"
              data-kept={scored.kept[i]}
              aria-label={scored.kept[i] ? `${value}` : `${value} discarded`}
            >
              {value}
            </span>
          ))}{" "}
          subtotal {signed(scored.subtotal)}
        </p>
      ))}
      <p>Visible modifiers {signed(roll.visible_modifier_total)}</p>
      <p>Preview total: {card.total}</p>
    </div>
  );
}
