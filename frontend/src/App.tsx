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
        <StoryView storyId={storyId} />
      ) : (
        <StoryList onSelect={selectStory} />
      )}
    </main>
  );
}
