import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { PersonaGallery, SetupRequest, StoryDetail } from "./api/client";

export default function SetupForm({
  story,
  onComplete,
}: {
  story: StoryDetail;
  onComplete: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(body: SetupRequest) {
    setSubmitting(true);
    setError(null);
    try {
      await api.submitSetup(story.story_id, body);
      onComplete();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Setup failed.");
    } finally {
      setSubmitting(false);
    }
  }

  if (story.mode === "rpg") {
    return (
      <RpgSetupForm
        storyId={story.story_id}
        submitting={submitting}
        error={error}
        onSubmit={submit}
      />
    );
  }
  if (story.mode === "branching") {
    return (
      <BranchingSetupForm
        storyId={story.story_id}
        submitting={submitting}
        error={error}
        onSubmit={submit}
      />
    );
  }
  // Writing is not offered in v1 (ADR-017b): no persona or setup controls.
  return (
    <p className="form-error" role="alert">
      Writing mode is not available in this release.
    </p>
  );
}

type FormProps = {
  submitting: boolean;
  error: string | null;
  onSubmit: (body: SetupRequest) => void;
};

function RpgSetupForm({
  storyId,
  submitting,
  error,
  onSubmit,
}: FormProps & { storyId: string }) {
  const [diceHandling, setDiceHandling] = useState<"player_rolls" | "ai_rolls">(
    "ai_rolls",
  );
  const [tone, setTone] = useState<
    "gritty" | "balanced" | "forgiving" | "danger_free"
  >("balanced");
  // Round 12 remediation (PR #126 P2): the hardcoded defaults above are
  // visible and submittable before getSetupState() resolves. A quick Save
  // during that window submitted ai_rolls/balanced and silently overwrote
  // persisted non-default setup (e.g. player_rolls/gritty). Save must stay
  // disabled until hydration has either applied persisted values or failed
  // visibly -- never while it's still in flight.
  const [hydrationStatus, setHydrationStatus] = useState<
    "loading" | "ready" | "error"
  >("loading");

  const hydrate = () => {
    setHydrationStatus("loading");
    api
      .getSetupState(storyId)
      .then((state) => {
        if (state && state.mode === "rpg") {
          if (state.dice_handling) setDiceHandling(state.dice_handling);
          if (state.tone) setTone(state.tone);
        }
        setHydrationStatus("ready");
      })
      .catch(() => {
        // Not silently swallowed (round 12 remediation): Save stays
        // disabled and the Sojourner sees why, with a way to retry.
        setHydrationStatus("error");
      });
  };

  // Hydrate from whatever RPG setup config is already persisted (PR #126
  // review round 5, P2) -- otherwise every reload resets these selects to
  // the hardcoded defaults above, and the next save silently overwrites a
  // prior non-default choice. RPG visible state cannot be used for this
  // (sheet-dependent by design, null until a concrete sheet exists);
  // GET .../setup reads RPG session state directly instead.
  useEffect(hydrate, [storyId]);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          mode: "rpg",
          dice_handling: diceHandling,
          tone,
          schema_version: 1,
        });
      }}
    >
      <h2>RPG setup</h2>
      <label>
        Dice handling
        <select
          value={diceHandling}
          onChange={(e) =>
            setDiceHandling(e.target.value as typeof diceHandling)
          }
        >
          <option value="ai_rolls">AI rolls</option>
          <option value="player_rolls">Player rolls</option>
        </select>
      </label>
      <label>
        Tone
        <select
          value={tone}
          onChange={(e) => setTone(e.target.value as typeof tone)}
        >
          <option value="gritty">Gritty</option>
          <option value="balanced">Balanced</option>
          <option value="forgiving">Forgiving</option>
          <option value="danger_free">Danger-free</option>
        </select>
      </label>
      {hydrationStatus === "error" && (
        <p className="form-error" role="alert">
          Could not load saved RPG setup. Retry before saving.{" "}
          <button type="button" onClick={hydrate}>
            Retry
          </button>
        </p>
      )}
      {error && <p className="form-error">{error}</p>}
      <button
        type="submit"
        disabled={submitting || hydrationStatus !== "ready"}
      >
        Save setup
      </button>
    </form>
  );
}

type BranchCountRange = "1-2" | "2-3" | "3-4" | "2-4" | "2-5";

// The ranges each card style allows (Design: Interaction Styles). The server
// validates them too (ADR-016b); Freeform-only has none.
const RANGES_BY_STYLE: Record<"hybrid" | "true_cyoa", BranchCountRange[]> = {
  hybrid: ["1-2", "2-3", "3-4"],
  true_cyoa: ["2-3", "2-4", "2-5"],
};

function BranchingSetupForm({
  storyId,
  submitting,
  error,
  onSubmit,
}: FormProps & { storyId: string }) {
  // CRD Issue 21 Prerequisite A (ADR-016b): every style is offered now that
  // the Branching writer, selection and OOC services are wired. Saving setup
  // does not start play; the separate Begin story control does.
  const [interactionStyle, setInteractionStyle] = useState<
    "freeform_only" | "hybrid" | "true_cyoa"
  >("freeform_only");
  const [cadence, setCadence] = useState<
    "interactive" | "balanced" | "immersive"
  >("balanced");
  const [countRange, setCountRange] = useState<BranchCountRange>("2-3");
  // ADR-016b permits a partially saved setup: restore what is persisted
  // before Save is enabled, so these defaults never overwrite saved choices
  // (the same hydration guard as the RPG form).
  const [hydrationStatus, setHydrationStatus] = useState<
    "loading" | "ready" | "error"
  >("loading");

  const hydrate = () => {
    setHydrationStatus("loading");
    api
      .getSetupState(storyId)
      .then((state) => {
        if (state && state.mode === "branching") {
          if (state.interaction_style)
            setInteractionStyle(state.interaction_style);
          if (state.branching_cadence) setCadence(state.branching_cadence);
          if (state.branch_count_range) setCountRange(state.branch_count_range);
        }
        setHydrationStatus("ready");
      })
      .catch(() => setHydrationStatus("error"));
  };

  useEffect(hydrate, [storyId]);
  const ranges =
    interactionStyle === "freeform_only"
      ? []
      : RANGES_BY_STYLE[interactionStyle];

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          mode: "branching",
          interaction_style: interactionStyle,
          branching_cadence: cadence,
          ...(interactionStyle === "freeform_only"
            ? { clear_branch_count_range: true }
            : {
                branch_count_range: countRange,
                clear_branch_count_range: false,
              }),
          schema_version: 1,
        });
      }}
    >
      <h2>Branching setup</h2>
      <label>
        Interaction style
        <select
          value={interactionStyle}
          onChange={(e) => {
            const style = e.target.value as typeof interactionStyle;
            setInteractionStyle(style);
            if (
              style !== "freeform_only" &&
              !RANGES_BY_STYLE[style].includes(countRange)
            ) {
              setCountRange(RANGES_BY_STYLE[style][0] ?? "2-3");
            }
          }}
        >
          <option value="freeform_only">Freeform only</option>
          <option value="hybrid">Hybrid (freeform + branch cards)</option>
          <option value="true_cyoa">True CYOA (choices only)</option>
        </select>
      </label>
      {ranges.length > 0 && (
        <label>
          Branch options per beat
          <select
            value={countRange}
            onChange={(e) => setCountRange(e.target.value as BranchCountRange)}
          >
            {ranges.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
      )}
      <label>
        Cadence
        <select
          value={cadence}
          onChange={(e) => setCadence(e.target.value as typeof cadence)}
        >
          <option value="interactive">Interactive</option>
          <option value="balanced">Balanced</option>
          <option value="immersive">Immersive</option>
        </select>
      </label>
      {hydrationStatus === "error" && (
        <p className="form-error" role="alert">
          Could not load saved Branching setup. Retry before saving.{" "}
          <button type="button" onClick={hydrate}>
            Retry
          </button>
        </p>
      )}
      {error && <p className="form-error">{error}</p>}
      <button
        type="submit"
        disabled={submitting || hydrationStatus !== "ready"}
      >
        Save setup
      </button>
    </form>
  );
}

// Retained for post-v1 Writing work (ADR-017b); not routed from SetupForm.
export function WritingSetupForm({ submitting, error, onSubmit }: FormProps) {
  const [personas, setPersonas] = useState<PersonaGallery | null>(null);
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [specificGoals, setSpecificGoals] = useState("");
  // Round 13 remediation (PR #126 P2, same read-failure class as the round-12
  // RPG setup hydration guard and post-submit refresh handling): the persona
  // gallery load previously swallowed its own failure (`.catch(() =>
  // setPersonas(null))`), which rendered as an empty gallery with no
  // explanation and no way to recover short of a full page reload. Track
  // load state explicitly instead.
  const [personaLoadStatus, setPersonaLoadStatus] = useState<
    "loading" | "ready" | "error"
  >("loading");

  const loadPersonas = () => {
    setPersonaLoadStatus("loading");
    api
      .listPersonas()
      .then((loaded) => {
        setPersonas(loaded);
        setPersonaLoadStatus("ready");
      })
      .catch(() => {
        setPersonas(null);
        setPersonaLoadStatus("error");
      });
  };

  useEffect(loadPersonas, []);

  const goalsReady = specificGoals.trim().length > 0;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!personaId || !goalsReady) return;
        onSubmit({
          mode: "writing",
          persona_id: personaId,
          specific_goals: specificGoals,
          schema_version: 1,
        });
      }}
    >
      <h2>Choose your Writing companion</h2>
      <label>
        What are you trying to write, revise, or accomplish?
        <textarea
          value={specificGoals}
          onChange={(e) => setSpecificGoals(e.target.value)}
          placeholder="e.g. Draft the opening chapter of a mystery novel"
          required
        />
      </label>
      {personaLoadStatus === "error" && (
        <p className="form-error" role="alert">
          Could not load Writing companions. Retry before saving.{" "}
          <button type="button" onClick={loadPersonas}>
            Retry
          </button>
        </p>
      )}
      {personas && (
        <div className="persona-gallery">
          <section>
            <h3>Mentors</h3>
            {personas.mentors.map((p) => (
              <PersonaCard
                key={p.persona_id}
                persona={p}
                selected={personaId === p.persona_id}
                onSelect={() => setPersonaId(p.persona_id)}
              />
            ))}
          </section>
          <section>
            <h3>Peers</h3>
            {personas.peers.map((p) => (
              <PersonaCard
                key={p.persona_id}
                persona={p}
                selected={personaId === p.persona_id}
                onSelect={() => setPersonaId(p.persona_id)}
              />
            ))}
          </section>
        </div>
      )}
      {error && <p className="form-error">{error}</p>}
      <button
        type="submit"
        disabled={
          submitting ||
          personaLoadStatus !== "ready" ||
          !personaId ||
          !goalsReady
        }
      >
        Save setup
      </button>
    </form>
  );
}

function PersonaCard({
  persona,
  selected,
  onSelect,
}: {
  persona: PersonaGallery["mentors"][number];
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      className="persona-card"
      aria-pressed={selected}
      onClick={onSelect}
    >
      <strong>{persona.display_name}</strong>
      <p>{persona.ui_short_description}</p>
    </button>
  );
}
