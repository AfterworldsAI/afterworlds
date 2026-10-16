import { useState } from "react";

import AccountPanel from "./AccountPanel";
import StoryList from "./StoryList";
import StoryView from "./StoryView";
import { localStorageState } from "./localStorage";

export default function App() {
  const [storyId, setStoryId] = useState<string | null>(() =>
    localStorageState.getLastStoryId(),
  );
  // CRD Issue 20: the account view is a separate screen, re-read whenever it
  // opens and whenever a turn completes (settlement may have changed it).
  const [showAccount, setShowAccount] = useState(false);
  const [settledTurns, setSettledTurns] = useState(0);

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
