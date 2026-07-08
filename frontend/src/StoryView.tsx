import { useEffect, useState } from "react";

import { api, ApiRequestError } from "./api/client";
import type {
  StoryDetail,
  TranscriptTurn,
  TurnSubmissionResponse,
  VisibleState,
} from "./api/client";
import DispositionBanner from "./DispositionBanner";
import SetupForm from "./SetupForm";
import Transcript from "./Transcript";
import VisibleStatePanel from "./VisibleStatePanel";
import { localStorageState } from "./localStorage";

export default function StoryView({ storyId }: { storyId: string }) {
  const [story, setStory] = useState<StoryDetail | null>(null);
  const [turns, setTurns] = useState<TranscriptTurn[]>([]);
  const [visibleState, setVisibleState] = useState<VisibleState | null>(null);
  const [draft, setDraft] = useState(() => localStorageState.getDraft(storyId));
  const [inFlight, setInFlight] = useState(false);
  const [lastResponse, setLastResponse] =
    useState<TurnSubmissionResponse | null>(null);
  // Three distinct failure classes (Binding Decision 6): a page-load failure
  // (loadError) fails closed over the whole view, no draft to preserve yet.
  // A turn-submission failure (turnError) must NOT replace the play view --
  // transcript, visible state, and the draft all stay exactly as they were.
  // A post-submit refresh failure (refreshError, round 10 remediation, PR
  // #126 P2) is neither: the turn was already persisted, so it must not be
  // reported as a submission failure or restore the draft -- only the
  // follow-up transcript/visible-state read failed.
  const [loadError, setLoadError] = useState<string | null>(null);
  const [turnError, setTurnError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  // Structured setup fields (this story's /setup call) and setup
  // *confirmation* are different things: per ADR-016 Decision 3 / ADR-017
  // Decision 9, confirmation is an ordinary narrative turn that the
  // orchestrator processes -- play_status only flips server-side once that
  // turn lands. This flag just decides which screen to show locally after
  // structured fields are saved; it never asserts a backend fact the server
  // hasn't recorded (Frontend State Discipline).
  const [structuredSetupSaved, setStructuredSetupSaved] = useState(false);

  async function refresh() {
    const [s, t, v] = await Promise.all([
      api.getStory(storyId),
      api.getLatestTranscript(storyId),
      api.getVisibleState(storyId),
    ]);
    setStory(s);
    setTurns(t);
    setVisibleState(v);
  }

  // Post-submit refresh only (no story re-fetch -- the turn didn't change
  // story metadata) -- reused by submitTurn and by the refresh-retry button
  // so a refresh failure can be recovered without re-submitting the turn.
  async function refreshTranscriptAndVisibleState() {
    setRefreshError(null);
    try {
      const [t, v] = await Promise.all([
        api.getLatestTranscript(storyId),
        api.getVisibleState(storyId),
      ]);
      setTurns(t);
      setVisibleState(v);
    } catch (err) {
      setRefreshError(
        err instanceof Error
          ? err.message
          : "Failed to refresh transcript/visible state.",
      );
    }
  }

  // Shared by the initial load and the Retry button so the two paths can't
  // drift apart again (P2 remediation, PR #126 round 3): a retry that only
  // called refresh() left loadError truthy even after a successful refresh,
  // since refresh() never touches loadError itself.
  async function loadStory() {
    setLoadError(null);
    try {
      await refresh();
    } catch (err) {
      setLoadError(
        err instanceof Error ? err.message : "Failed to load story.",
      );
    }
  }

  useEffect(() => {
    loadStory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storyId]);

  useEffect(() => {
    localStorageState.setDraft(storyId, draft);
  }, [storyId, draft]);

  async function submitTurn(userInput: string) {
    if (inFlight || !userInput.trim()) return;
    setInFlight(true);
    setTurnError(null);
    setRefreshError(null);
    try {
      // Only the mutation itself is in this try/catch (round 10
      // remediation, PR #126 P2): a failure here means the turn was never
      // persisted, so the draft stays and turnError is the right signal.
      const response = await api.submitTurn(storyId, userInput);
      setLastResponse(response);
      if (
        response.disposition === "delivered" ||
        response.disposition === "ooc_handled"
      ) {
        setDraft(""); // clear only on confirmed persistence (Binding Decision 6)
      }
    } catch (err) {
      // Draft/transcript/visible-state are untouched -- typed error surfaces
      // inline, the play view stays exactly as it was (Binding Decision 6).
      if (err instanceof ApiRequestError) {
        setTurnError(err.apiError.message);
      } else {
        setTurnError(
          err instanceof Error ? err.message : "Turn submission failed.",
        );
      }
      setInFlight(false);
      return;
    }
    setInFlight(false);
    // The turn already succeeded above -- a failure here is a separate,
    // non-fatal refresh problem, not a submission failure. lastResponse and
    // the (possibly just-cleared) draft are left exactly as the successful
    // submission set them; the refresh-retry button re-runs this without
    // re-submitting the turn.
    await refreshTranscriptAndVisibleState();
  }

  if (loadError) {
    return (
      <div className="story-view-error" role="alert">
        <p>{loadError}</p>
        <button type="button" onClick={() => loadStory()}>
          Retry
        </button>
      </div>
    );
  }

  if (!story) {
    return <p>Loading...</p>;
  }

  // Branching/Writing setup handoff must survive reload/resume (P2
  // remediation, PR #126 round 3): structuredSetupSaved is in-memory only
  // and resets to false on every reload, while story.status legitimately
  // stays "setup" until the confirmation turn lands (ADR-016 Decision 3 /
  // ADR-017 Decision 9). Persisted visible state (non-null once
  // interaction_style+branching_cadence are configured) is a server-derived
  // signal that survives reload. RPG visible state stays null until a
  // concrete character sheet exists, so RPG must not use this signal to
  // skip its own setup screen -- this is still only a client-local
  // view-routing decision, not an assertion about backend play_status.
  //
  // Writing is intentionally NOT symmetric with Branching here (PR #126
  // round 5 follow-up): visibleState !== null only means persona_id is set
  // -- it says nothing about specific_goals. A pre-round-5 story (or any
  // row with persona_id set but a still-blank specific_goals) would have
  // non-null visible state while play_status never promotes past SETUP,
  // silently re-entering play view for a story whose turns stay forced to
  // SETUP_CONFIRMATION/NON_CANON_SUPPORT forever -- the exact defect round
  // 5 fixed, resurfacing via this bypass instead of the original path. For
  // Writing, the durable "structured setup genuinely complete" signal is
  // play_status === "in_play" (the same signal turns.py's
  // derive_writing_turn_request uses), which can only be true once both
  // persona_id and a real, Sojourner-authored specific_goals are persisted.
  const structuredSetupPersisted =
    story.status === "setup" &&
    ((story.mode === "branching" && visibleState !== null) ||
      (story.mode === "writing" &&
        visibleState !== null &&
        "play_status" in visibleState &&
        visibleState.play_status === "in_play"));

  if (
    story.status === "setup" &&
    !structuredSetupSaved &&
    !structuredSetupPersisted
  ) {
    return (
      <SetupForm
        story={story}
        onComplete={() => {
          setStructuredSetupSaved(true);
          // Sibling audit (round 11, same "mutation success vs. follow-up
          // read" defect family as submitTurn): setup itself already
          // succeeded by the time onComplete fires (SetupForm's own
          // submit() only calls this after a successful api.submitSetup),
          // so a refresh() failure here must not surface as a setup error
          // or throw an unhandled promise rejection -- refreshError already
          // covers this same "stale play view, recoverable via Retry" case.
          refresh().catch((err) => {
            setRefreshError(
              err instanceof Error
                ? err.message
                : "Failed to refresh transcript/visible state.",
            );
          });
        }}
      />
    );
  }

  return (
    <div className="story-play-view">
      <div className="story-main">
        <Transcript turns={turns} />
        {lastResponse && <DispositionBanner response={lastResponse} />}
        {turnError && (
          <p className="turn-error" role="alert">
            {turnError}
          </p>
        )}
        {refreshError && (
          <p className="refresh-error" role="alert">
            {refreshError}{" "}
            <button
              type="button"
              onClick={() => refreshTranscriptAndVisibleState()}
            >
              Retry
            </button>
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submitTurn(draft);
          }}
        >
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={inFlight}
            placeholder="What do you do?"
          />
          <button type="submit" disabled={inFlight || !draft.trim()}>
            {inFlight ? "Submitting..." : "Submit"}
          </button>
        </form>
      </div>
      <aside className="story-sidebar">
        <VisibleStatePanel
          visibleState={visibleState}
          onBranchOptionClick={(text) => submitTurn(text)}
        />
      </aside>
    </div>
  );
}
