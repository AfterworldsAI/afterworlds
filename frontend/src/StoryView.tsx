import { useEffect, useRef, useState } from "react";

import { api, ApiRequestError } from "./api/client";
import type {
  PendingInteraction,
  RollSubmission,
  StoryDetail,
  TranscriptTurn,
  TurnSubmissionResponse,
  VisibleState,
} from "./api/client";
import DispositionBanner from "./DispositionBanner";
import RpgPendingInteraction from "./RpgPendingInteraction";
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
  // CRD Issue 15b: the RPG story's pending interaction, exactly as the
  // backend reports it (never inferred locally), and the failure of one of
  // its operations -- shown inline like turnError, never replacing the view.
  const [pending, setPending] = useState<PendingInteraction | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  // CRD Issue 19b: after a refused or uncertain operation the shown
  // interaction may be stale, so its controls stay disabled until a pending
  // read succeeds -- never a replayed POST or an automatic re-roll.
  const [pendingStale, setPendingStale] = useState(false);
  // A ref, not inFlight state: two clicks in one tick both see the same
  // render's inFlight, but only one operation may start.
  const operating = useRef(false);
  // Only the newest pending read or operation result is shown, so a slow
  // read can't overwrite a later advancement.
  const pendingEpoch = useRef(0);
  const mounted = useRef(true);
  const pendingRef = useRef<HTMLDivElement>(null);
  const [focusRequest, setFocusRequest] = useState(0);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (focusRequest) pendingRef.current?.focus();
  }, [focusRequest]);

  async function readPending(mode: string | undefined) {
    return mode === "rpg"
      ? ((await api.getPendingInteraction(storyId)) ?? null)
      : null;
  }

  function showPending(epoch: number, interaction: PendingInteraction | null) {
    if (epoch !== pendingEpoch.current) return;
    setPending(interaction);
    setPendingStale(false);
  }

  async function refresh() {
    const epoch = ++pendingEpoch.current;
    const [s, t, v] = await Promise.all([
      api.getStory(storyId),
      api.getLatestTranscript(storyId),
      api.getVisibleState(storyId),
    ]);
    // A ready sequence found on load only shows its resume affordance: an
    // automatic resume here could loop on a failing narration (15b-31).
    const p = await readPending(s.mode);
    setStory(s);
    setTurns(t);
    setVisibleState(v);
    showPending(epoch, p);
  }

  // Post-submit refresh only (no story re-fetch -- the turn didn't change
  // story metadata) -- reused by submitTurn and by the refresh-retry button
  // so a refresh failure can be recovered without re-submitting the turn.
  async function refreshTranscriptAndVisibleState() {
    setRefreshError(null);
    const epoch = ++pendingEpoch.current;
    try {
      const [t, v, p] = await Promise.all([
        api.getLatestTranscript(storyId),
        api.getVisibleState(storyId),
        readPending(story?.mode),
      ]);
      setTurns(t);
      setVisibleState(v);
      showPending(epoch, p);
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
    let response: TurnSubmissionResponse;
    try {
      // Only the mutation itself is in this try/catch (round 10
      // remediation, PR #126 P2): a failure here means the turn was never
      // persisted, so the draft stays and turnError is the right signal.
      response = await api.submitTurn(storyId, userInput);
      setLastResponse(response);
      // The mutation response already carries server-refreshed visible state
      // (PR #126 P2 round 14, sibling of the round-10 mutation-success-vs-
      // refresh-failure split): consume it now so the sidebar reflects the
      // successful POST even if the follow-up read below fails, instead of
      // leaving stale/null state. Coalesced to null (not left stale) when
      // the response itself carries none, so this never invents state the
      // backend didn't report. The follow-up refresh below still overwrites
      // this with the read-path's own value as the eventual reconciliation.
      setVisibleState(response.visible_state ?? null);
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
    // CRD Issue 19b: the backend held an in-character action (or a choice)
    // for the unresolved interaction -- take the Sojourner to it. The client
    // classifies nothing; out-of-character input was never held.
    if (response.disposition === "blocked_pending_roll") {
      setFocusRequest((n) => n + 1);
    }
  }

  function errorMessage(err: unknown, fallback: string) {
    if (err instanceof ApiRequestError) return err.apiError.message;
    return err instanceof Error ? err.message : fallback;
  }

  // A roll, adjustment or decision: no Turn, no provider call. When it
  // leaves the action ready for narration, the narration is requested at
  // once (15b-31). A refused operation changes nothing server-side; the
  // pending interaction is re-read so a stale revision is rehydrated.
  // A failed or uncertain operation is never retried: the controls stay
  // disabled until the re-read shows what the backend actually holds.
  async function advance(operation: () => Promise<PendingInteraction>) {
    if (operating.current) return;
    operating.current = true;
    setInFlight(true);
    setActionError(null);
    try {
      let result: PendingInteraction;
      try {
        result = await operation();
      } catch (err) {
        if (!mounted.current) return;
        setActionError(errorMessage(err, "The action could not be applied."));
        setPendingStale(true);
        await refreshTranscriptAndVisibleState();
        return;
      }
      // Left the story meanwhile: its reload shows the resume affordance.
      if (!mounted.current) return;
      showPending(++pendingEpoch.current, result);
      if (result.interaction_phase === "ready_for_narration") {
        await narrate(result.sequence_id);
      }
    } finally {
      operating.current = false;
      if (mounted.current) setInFlight(false);
    }
  }

  // The resume turn. An already-narrated sequence (a repeat, or a reply lost
  // in transit) is success-equivalent: no error, only a refetch (15b-32). A
  // failed narration is shown by its disposition; the ready affordance stays
  // for a deliberate retry.
  async function narrate(sequenceId: string) {
    try {
      const response = await api.resumeSequence(storyId, sequenceId);
      setLastResponse(response);
      setVisibleState(response.visible_state ?? null);
    } catch (err) {
      if (
        err instanceof ApiRequestError &&
        err.apiError.error_code === "action_sequence_already_completed"
      ) {
        // Success-equivalent: an earlier failed narration's banner no
        // longer describes this action.
        setLastResponse(null);
      } else {
        setActionError(errorMessage(err, "The action could not be narrated."));
      }
    }
    // Whatever the resume did -- narrated, failed, or lost in transit -- the
    // shown ready affordance is unconfirmed until the re-read lands: no
    // further resume is offered from it before then.
    setPendingStale(true);
    await refreshTranscriptAndVisibleState();
  }

  async function resumeFromAffordance(sequenceId: string) {
    if (operating.current) return;
    operating.current = true;
    setInFlight(true);
    setActionError(null);
    try {
      await narrate(sequenceId);
    } finally {
      operating.current = false;
      if (mounted.current) setInFlight(false);
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
  // non-null visible state, silently re-entering play view for a story
  // whose turns stay forced to SETUP_CONFIRMATION/NON_CANON_SUPPORT
  // forever -- the exact defect round 5 fixed, resurfacing via this bypass
  // instead of the original path. The durable "structured setup genuinely
  // complete" signal is a nonblank specific_goals, which can only be true
  // once both persona_id and a real, Sojourner-authored specific_goals are
  // persisted together (WritingSetupRequest always requires both on every
  // call).
  //
  // Round 13 boundary decision (owner-approved): this signal was
  // previously play_status === "in_play", matching turns.py's
  // derive_writing_turn_request. That stopped being correct once POST
  // /setup itself stopped promoting play_status (ADR-017 Decision 9 /
  // ADR-018 D6 require the story to stay SETUP until the setup-confirmation
  // turn genuinely lands) -- checking play_status here would have bounced
  // a Sojourner who reloads between completing setup and submitting that
  // first turn back to the setup form, even though setup was already
  // genuinely complete. specific_goals is unaffected by that timing: it is
  // persisted (nonblank, by the same request) before play_status ever
  // changes.
  const structuredSetupPersisted =
    story.status === "setup" &&
    ((story.mode === "branching" && visibleState !== null) ||
      (story.mode === "writing" &&
        visibleState !== null &&
        "specific_goals" in visibleState &&
        !!visibleState.specific_goals?.trim()));

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
        {pending && (
          <div ref={pendingRef} tabIndex={-1}>
            <RpgPendingInteraction
              interaction={pending}
              disabled={inFlight || pendingStale}
              onRoll={(body: RollSubmission) =>
                advance(() => api.submitRoll(storyId, body))
              }
              onAdjust={(optionId) =>
                advance(() =>
                  api.applyAdjustment(storyId, {
                    pending_roll_request_id:
                      pending.pending_roll?.pending_roll_request_id ?? "",
                    expected_instruction_revision:
                      pending.pending_roll?.instruction_revision ?? 0,
                    option_id: optionId,
                    schema_version: 1,
                  }),
                )
              }
              onDecide={(optionId) =>
                advance(() =>
                  api.submitDecision(storyId, {
                    decision_request_id:
                      pending.pending_decision?.decision_request_id ?? "",
                    expected_decision_revision:
                      pending.pending_decision?.decision_revision ?? 0,
                    option_id: optionId,
                    schema_version: 1,
                  }),
                )
              }
              onResume={() => resumeFromAffordance(pending.sequence_id)}
            />
          </div>
        )}
        {actionError && (
          <p className="action-error" role="alert">
            {actionError}
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
