import { useEffect, useState } from "react";

import { api } from "./api/client";
import type { StoryListItem } from "./api/client";

export default function StoryList({
  onSelect,
}: {
  onSelect: (storyId: string) => void;
}) {
  const [stories, setStories] = useState<StoryListItem[]>([]);
  const [title, setTitle] = useState("");
  const [mode, setMode] = useState<"rpg" | "branching" | "writing">("writing");
  const [characterName, setCharacterName] = useState("");
  const [error, setError] = useState<string | null>(null);

  function load() {
    api
      .listStories()
      .then(setStories)
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Failed to load stories.",
        ),
      );
  }

  useEffect(load, []);

  async function createStory(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      const story = await api.createStory({
        title,
        mode,
        character_name: mode === "rpg" ? characterName || null : null,
        schema_version: 1,
      });
      setTitle("");
      setCharacterName("");
      load();
      onSelect(story.story_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create story.");
    }
  }

  return (
    <div className="story-list">
      <h2>Your stories</h2>
      {error && <p className="form-error">{error}</p>}
      <ul>
        {stories.map((s) => (
          <li key={s.story_id}>
            <button type="button" onClick={() => onSelect(s.story_id)}>
              {s.title} ({s.mode}, {s.status})
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={createStory}>
        <h3>New story</h3>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title"
        />
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as typeof mode)}
        >
          <option value="writing">Writing</option>
          <option value="branching">Branching</option>
          <option value="rpg">RPG</option>
        </select>
        {mode === "rpg" && (
          <input
            value={characterName}
            onChange={(e) => setCharacterName(e.target.value)}
            placeholder="Character name"
          />
        )}
        <button type="submit" disabled={!title.trim()}>
          Create
        </button>
      </form>
    </div>
  );
}
