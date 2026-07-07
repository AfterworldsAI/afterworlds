import type { VisibleState } from "./api/client";

/**
 * Compact per-mode sidebar. RPG dice UI (inline rolls, dice-expression
 * subsystem, pending-roll consume/scorecard/animation/rehydration) is
 * intentionally out of scope here -- deferred to Issue 19b per
 * AW_Dice_Subsystem_CRD. This renders only the plain read-only fields
 * RpgVisibleState already carries.
 */
export default function VisibleStatePanel({
  visibleState,
  onBranchOptionClick,
}: {
  visibleState: VisibleState | null;
  onBranchOptionClick?: (actionText: string) => void;
}) {
  if (visibleState === null) {
    return (
      <p className="visible-state-empty">
        Complete setup to see story state here.
      </p>
    );
  }

  if ("character" in visibleState) {
    const {
      character,
      inventory,
      location,
      relationship_meters,
      known_objectives,
    } = visibleState;
    return (
      <div className="visible-state rpg-visible-state">
        <h3>{character.character_name}</h3>
        <p>
          {character.character_class}, level {character.level}
        </p>
        <p>
          HP {character.current_hp} / {character.maximum_hp}
        </p>
        {character.active_conditions.length > 0 && (
          <p>Conditions: {character.active_conditions.join(", ")}</p>
        )}
        {location && <p>Location: {location.name}</p>}
        {inventory.length > 0 && (
          <ul>
            {inventory.map((item) => (
              <li key={item.name}>
                {item.name} x{item.quantity}
              </li>
            ))}
          </ul>
        )}
        {relationship_meters.length > 0 && (
          <ul>
            {relationship_meters.map((r, i) => (
              <li key={i}>{JSON.stringify(r)}</li>
            ))}
          </ul>
        )}
        {known_objectives.length > 0 && (
          <ul>
            {known_objectives.map((o, i) => (
              <li key={i}>{o}</li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  if ("interaction_style" in visibleState) {
    const {
      interaction_style,
      branching_cadence,
      freeform_available,
      last_branch_options,
    } = visibleState;
    return (
      <div className="visible-state branching-visible-state">
        <p>Interaction style: {interaction_style}</p>
        <p>Cadence: {branching_cadence}</p>
        <p>Freeform input {freeform_available ? "allowed" : "not allowed"}</p>
        {last_branch_options && last_branch_options.length > 0 && (
          <div className="branch-cards">
            {last_branch_options.map((opt) => (
              <button
                key={opt.option_id}
                type="button"
                className="branch-card"
                onClick={() =>
                  onBranchOptionClick?.(`I choose: ${opt.action_text}`)
                }
              >
                {opt.action_text}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="visible-state writing-visible-state">
      <h3>{visibleState.persona_display_name}</h3>
      <p>{visibleState.ui_short_description}</p>
      <p>Critique intensity: {visibleState.critique_intensity}</p>
    </div>
  );
}
