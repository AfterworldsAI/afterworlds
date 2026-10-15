import { useState } from "react";

import StoryList from "./StoryList";
import StoryView from "./StoryView";
import { localStorageState } from "./localStorage";

export default function App() {
  const [storyId, setStoryId] = useState<string | null>(() =>
    localStorageState.getLastStoryId(),
  );

  function selectStory(id: string) {
    localStorageState.setLastStoryId(id);
    setStoryId(id);
  }

  return (
    <main>
      <header>
        <h1>Afterworlds</h1>
        {storyId && (
          <button type="button" onClick={() => setStoryId(null)}>
            Back to stories
          </button>
        )}
      </header>
      {storyId ? (
        // Keyed: another story is a fresh view, so no late response or
        // pending candidate of the previous one can populate it.
        <StoryView key={storyId} storyId={storyId} />
      ) : (
        <StoryList onSelect={selectStory} />
      )}
    </main>
  );
}
