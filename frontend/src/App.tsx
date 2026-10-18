import { useEffect, useState } from "react";

import AccountPanel from "./AccountPanel";
import { api, setSignedOutListener, type SessionStatus } from "./api/client";
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
  const [session, setSession] = useState<SessionStatus | null>(null);
  const [sessionKnown, setSessionKnown] = useState(false);
  const [signInNotice, setSignInNotice] = useState<string | null>(null);

  function signedOut(notice: string | null) {
    localStorageState.clearAccountState();
    setStoryId(null);
    setShowAccount(false);
    setSignInNotice(notice);
    setSession((s) => (s ? { ...s, signed_in: false, account_id: null } : s));
  }

  useEffect(() => {
    // A failed status read falls back to the local layout: any protected
    // request then answers 401 and lands here.
    api
      .getSessionStatus()
      .then(setSession)
      .catch(() => setSession(null))
      .finally(() => setSessionKnown(true));
    setSignedOutListener(() =>
      signedOut("Your session ended. Sign in again to continue."),
    );
    return () => setSignedOutListener(null);
  }, []);

  if (!sessionKnown) {
    return (
      <main>
        <header>
          <h1>Afterworlds</h1>
        </header>
        <p>Loading…</p>
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
              onClick={() =>
                void api
                  .signOut()
                  .catch(() => undefined)
                  .then(() => signedOut(null))
              }
            >
              Sign out
            </button>
          </>
        )}
      </header>
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
