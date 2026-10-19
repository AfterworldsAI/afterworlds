import { useEffect, useState } from "react";

import AccountPanel from "./AccountPanel";
import {
  api,
  ApiRequestError,
  setSignedOutListener,
  type SessionStatus,
} from "./api/client";
import { localStorageState } from "./localStorage";
import SignIn from "./SignIn";
import StoryList from "./StoryList";
import StoryView from "./StoryView";

export default function App() {
  const [storyId, setStoryId] = useState<string | null>(() =>
    localStorageState.getLastStoryId(),
  );
  // CRD Issue 20: the account view is a separate screen, re-read whenever it
  // opens and whenever a turn completes (settlement may have changed it).
  const [showAccount, setShowAccount] = useState(false);
  const [settledTurns, setSettledTurns] = useState(0);
  // Prerequisite #205: remote deployments need a session; local ones never
  // do. Presentation only -- the server enforces every request regardless.
  // "unavailable" is an unanswered status read: never treated as local.
  const [discovery, setDiscovery] = useState<"loading" | "ok" | "unavailable">(
    "loading",
  );
  const [session, setSession] = useState<SessionStatus | null>(null);
  const [signInNotice, setSignInNotice] = useState<string | null>(null);
  const [signOutError, setSignOutError] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  // Server-confirmed end of the session (sign-out, expiry or revocation).
  // Only a remote deployment answers authentication_required.
  function signedOut(notice: string | null) {
    localStorageState.clearAccountState();
    setStoryId(null);
    setShowAccount(false);
    setSignInNotice(notice);
    setSignOutError(null);
    setSession(() => ({
      deployment: "remote",
      signed_in: false,
      account_id: null,
      contact_address: null,
      schema_version: 1,
    }));
    setDiscovery("ok");
  }

  function discover() {
    setDiscovery("loading");
    api
      .getSessionStatus()
      .then((status) => {
        // A confirmed remote signed-out answer ends any previous account's
        // local state through the same clearing as a confirmed sign-out.
        // Discovery runs only before any account view has opened, so the
        // remembered Story is the only view state to reset.
        if (status.deployment === "remote" && !status.signed_in) {
          localStorageState.clearAccountState();
          setStoryId(null);
        }
        setSession(status);
        setDiscovery("ok");
      })
      .catch(() => setDiscovery("unavailable"));
  }

  async function signOut() {
    setSigningOut(true);
    setSignOutError(null);
    try {
      await api.signOut();
      signedOut(null);
    } catch (err) {
      // The listener already handled a server-confirmed ended session.
      if (
        !(err instanceof ApiRequestError) ||
        err.apiError.error_code !== "authentication_required"
      ) {
        setSignOutError(
          "Sign-out could not be confirmed, so you may still be signed in. Try again.",
        );
      }
    } finally {
      setSigningOut(false);
    }
  }

  useEffect(() => {
    discover();
    setSignedOutListener(() =>
      signedOut("Your session ended. Sign in again to continue."),
    );
    return () => setSignedOutListener(null);
  }, []);

  if (discovery !== "ok") {
    return (
      <main>
        <header>
          <h1>Afterworlds</h1>
        </header>
        {discovery === "loading" ? (
          <p>Loading…</p>
        ) : (
          <p role="alert">
            The service could not be reached, so your sign-in state is unknown.{" "}
            <button type="button" onClick={discover}>
              Retry
            </button>
          </p>
        )}
      </main>
    );
  }

  const remote = session?.deployment === "remote";
  if (remote && !session?.signed_in) {
    return (
      <main>
        <header>
          <h1>Afterworlds</h1>
        </header>
        <SignIn
          notice={signInNotice}
          onSignedIn={(status) => {
            setSignInNotice(null);
            setSession(status);
          }}
        />
      </main>
    );
  }

  function selectStory(id: string) {
    localStorageState.setLastStoryId(id);
    setStoryId(id);
  }

  return (
    <main>
      <header>
        <h1>Afterworlds</h1>
        {storyId && !showAccount && (
          <button type="button" onClick={() => setStoryId(null)}>
            Back to stories
          </button>
        )}
        <button type="button" onClick={() => setShowAccount((v) => !v)}>
          {showAccount ? "Close account" : "Account & BYOK"}
        </button>
        {remote && (
          <>
            <span className="signed-in-as">{session?.contact_address}</span>
            <button
              type="button"
              disabled={signingOut}
              onClick={() => void signOut()}
            >
              Sign out
            </button>
          </>
        )}
      </header>
      {signOutError && <p role="alert">{signOutError}</p>}
      {showAccount ? (
        <AccountPanel refreshKey={settledTurns} />
      ) : storyId ? (
        // Keyed: another story is a fresh view, so no late response or
        // pending candidate of the previous one can populate it.
        <StoryView
          key={storyId}
          storyId={storyId}
          onTurnSettled={() => setSettledTurns((n) => n + 1)}
        />
      ) : (
        <StoryList onSelect={selectStory} />
      )}
    </main>
  );
}
