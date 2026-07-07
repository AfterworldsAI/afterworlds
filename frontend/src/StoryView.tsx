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
  // Two distinct failure classes (Binding Decision 6): a page-load failure
  // (loadError) fails closed over the whole view, no draft to preserve yet.
  // A turn-submission failure (turnError) must NOT replace the play view --
  // transcript, visible state, and the draft all stay exactly as they were.
  const [loadError, setLoadError] = useState<string | null>(null);
  const [turnError, setTurnError] = useState<string | null>(null);
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
      api.getTranscript(storyId),
      api.getVisibleState(storyId),
    ]);
    setStory(s);
    setTurns(t);
    setVisibleState(v);
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
    try {
      const response = await api.submitTurn(storyId, userInput);
      setLastResponse(response);
      if (
        response.disposition === "delivered" ||
        response.disposition === "ooc_handled"
      ) {
        setDraft(""); // clear only on confirmed persistence (Binding Decision 6)
      }
      const [t, v] = await Promise.all([
        api.getTranscript(storyId),
        api.getVisibleState(storyId),
      ]);
      setTurns(t);
      setVisibleState(v);
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
    } finally {
      setInFlight(false);
    }
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
  // interaction_style+branching_cadence, or persona_id, are configured) is
  // a server-derived signal that survives reload. RPG visible state stays
  // null until a concrete character sheet exists, so RPG must not use this
  // signal to skip its own setup screen -- this is still only a client-
  // local view-routing decision, not an assertion about backend play_status.
  const structuredSetupPersisted =
    story.status === "setup" &&
    (story.mode === "branching" || story.mode === "writing") &&
    visibleState !== null;

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
          refresh();
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
