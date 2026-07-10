/**
 * The permitted browser-storage allowlist (Frontend State Discipline).
 * Exhaustive: last-selected story_id, unsent draft input per story, trivial
 * view preferences. Nothing else may be persisted client-side -- all other
 * state is server-derived and re-fetched, never reconstructed.
 */

const LAST_STORY_KEY = "afterworlds:last-story-id";
const draftKey = (storyId: string) => `afterworlds:draft:${storyId}`;
const SIDEBAR_COLLAPSED_KEY = "afterworlds:sidebar-collapsed";

export const localStorageState = {
  getLastStoryId: (): string | null => localStorage.getItem(LAST_STORY_KEY),
  setLastStoryId: (storyId: string): void =>
    localStorage.setItem(LAST_STORY_KEY, storyId),

  getDraft: (storyId: string): string =>
    localStorage.getItem(draftKey(storyId)) ?? "",
  setDraft: (storyId: string, text: string): void => {
    if (text) localStorage.setItem(draftKey(storyId), text);
    else localStorage.removeItem(draftKey(storyId));
  },

  getSidebarCollapsed: (): boolean =>
    localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true",
  setSidebarCollapsed: (collapsed: boolean): void =>
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed)),
};
