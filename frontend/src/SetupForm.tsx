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
        submitting={submitting}
        error={error}
        onSubmit={submit}
      />
    );
  }
  return (
    <WritingSetupForm submitting={submitting} error={error} onSubmit={submit} />
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

function BranchingSetupForm({ submitting, error, onSubmit }: FormProps) {
  // Round 8 remediation (PR #126 P1): default to freeform_only and disable
  // hybrid/true_cyoa. BranchingWriterService is deliberately not wired for
  // Issue 19 (see Architecture Notes), and the orchestrator fails closed
  // with PIPELINE_ERROR for an in-play hybrid/true_cyoa session with no
  // branching writer -- offering them here would let a Sojourner configure
  // a story whose first Branching turn deterministically fails.
  const [interactionStyle, setInteractionStyle] = useState<
    "freeform_only" | "hybrid" | "true_cyoa"
  >("freeform_only");
  const [cadence, setCadence] = useState<
    "interactive" | "balanced" | "immersive"
  >("balanced");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({
          mode: "branching",
          interaction_style: interactionStyle,
          branching_cadence: cadence,
          clear_branch_count_range: false,
          schema_version: 1,
        });
      }}
    >
      <h2>Branching setup</h2>
      <label>
        Interaction style
        <select
          value={interactionStyle}
          onChange={(e) =>
            setInteractionStyle(e.target.value as typeof interactionStyle)
          }
        >
          <option value="freeform_only">Freeform only</option>
          <option value="hybrid" disabled>
            Hybrid (unsupported in this build)
          </option>
          <option value="true_cyoa" disabled>
            True CYOA (unsupported in this build)
          </option>
        </select>
      </label>
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
      {error && <p className="form-error">{error}</p>}
      <button type="submit" disabled={submitting}>
        Save setup
      </button>
    </form>
  );
}

function WritingSetupForm({ submitting, error, onSubmit }: FormProps) {
  const [personas, setPersonas] = useState<PersonaGallery | null>(null);
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [specificGoals, setSpecificGoals] = useState("");

  useEffect(() => {
    api
      .listPersonas()
      .then(setPersonas)
      .catch(() => setPersonas(null));
  }, []);

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
      <button type="submit" disabled={submitting || !personaId || !goalsReady}>
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
