import "@testing-library/jest-dom/vitest";

// Node's own built-in `localStorage` global (unflagged since ~v22) ships as
// a non-functional stub unless `--localstorage-file` is set, and jsdom
// doesn't override an already-present global -- so both `globalThis.
// localStorage` and `window.localStorage` resolve to the broken stub in
// this environment. Replace it with a minimal working in-memory
// implementation for tests.
class MemoryStorage implements Storage {
  private store = new Map<string, string>();
  get length(): number {
    return this.store.size;
  }
  clear(): void {
    this.store.clear();
  }
  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }
  key(index: number): string | null {
    return Array.from(this.store.keys())[index] ?? null;
  }
  removeItem(key: string): void {
    this.store.delete(key);
  }
  setItem(key: string, value: string): void {
    this.store.set(key, String(value));
  }
}

Object.defineProperty(globalThis, "localStorage", {
  value: new MemoryStorage(),
  configurable: true,
});
