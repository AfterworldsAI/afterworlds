import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

type Call = { url: string; method: string; body: string | undefined };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const signedOut = {
  deployment: "remote",
  signed_in: false,
  account_id: null,
  contact_address: null,
  schema_version: 1,
};
const signedIn = {
  ...signedOut,
  signed_in: true,
  account_id: "acct-a",
  contact_address: "a@example.test",
};
const accepted = { status: "accepted", schema_version: 1 };
const failed = {
  error_code: "authentication_failed",
  message: "Authentication failed.",
  detail: null,
  schema_version: 1,
};
const expired = { ...failed, error_code: "authentication_required" };

function stub(routes: Record<string, (() => Response)[]>): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      calls.push({ url, method, body: init?.body as string | undefined });
      const queue = routes[`${method} ${url.split("?")[0]}`];
      const next = queue && (queue.length > 1 ? queue.shift() : queue[0]);
      if (!next) throw new Error(`unexpected ${method} ${url}`);
      return Promise.resolve(next());
    }),
  );
  return calls;
}

function type(label: RegExp, value: string) {
  const input = screen.getByLabelText(label) as HTMLInputElement;
  act(() => {
    const setter = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!;
    setter.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

beforeEach(() => localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("remote sign-in (prerequisite #205)", () => {
  it("signs in, sends the client header, and signs out clearing local state", async () => {
    const calls = stub({
      "GET /api/auth/session": [() => json(200, signedOut)],
      "POST /api/auth/sign-in": [
        () => json(401, failed),
        () => json(200, signedIn),
      ],
      "GET /api/stories": [() => json(200, { stories: [], schema_version: 1 })],
      "POST /api/auth/sign-out": [() => json(200, signedOut)],
    });
    localStorage.setItem("afterworlds:draft:old", "previous user's draft");
    render(<App />);
    await screen.findByRole("heading", { name: "Sign in" });
    type(/Email address/, "a@example.test");
    type(/^Password/, "wrong password!");
    act(() => screen.getByRole("button", { name: "Sign in" }).click());
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "That did not work",
    );
    type(/^Password/, "correct horse battery staple");
    act(() => screen.getByRole("button", { name: "Sign in" }).click());
    expect(await screen.findByText("Your stories")).toBeInTheDocument();
    const signIn = calls.filter((c) => c.url === "/api/auth/sign-in");
    expect(signIn).toHaveLength(2);
    const init = vi.mocked(fetch).mock.calls[1]![1]!;
    expect(
      (init.headers as Record<string, string>)["X-Afterworlds-Request"],
    ).toBe("1");

    act(() => screen.getByRole("button", { name: "Sign out" }).click());
    await screen.findByRole("heading", { name: "Sign in" });
    expect(localStorage.getItem("afterworlds:draft:old")).toBeNull();
  });

  it("returns to sign-in when the server reports the session ended", async () => {
    stub({
      "GET /api/auth/session": [() => json(200, signedIn)],
      "GET /api/stories": [() => json(401, expired)],
    });
    render(<App />);
    expect(await screen.findByText(/Your session ended/)).toBeInTheDocument();
  });

  it("enrolls with a mailed code without revealing whether the address exists", async () => {
    const calls = stub({
      "GET /api/auth/session": [() => json(200, signedOut)],
      "POST /api/auth/register": [() => json(202, accepted)],
      "POST /api/auth/register/complete": [() => json(200, accepted)],
    });
    render(<App />);
    const toMode = await screen.findByRole("button", {
      name: "Create an account",
    });
    act(() => toMode.click());
    type(/Email address/, "new@example.test");
    act(() => screen.getByRole("button", { name: "Send code" }).click());
    expect(
      await screen.findByText(/If this address can receive one/),
    ).toBeInTheDocument();
    type(/Code/, "the-code");
    type(/New password/, "a brand new passphrase");
    act(() => screen.getByRole("button", { name: "Create account" }).click());
    expect(await screen.findByText(/Account created/)).toBeInTheDocument();
    const complete = calls.find(
      (c) => c.url === "/api/auth/register/complete",
    )!;
    expect(JSON.parse(complete.body!)).toEqual({
      contact_address: "new@example.test",
      code: "the-code",
      password: "a brand new passphrase", // pragma: allowlist secret
    });
    expect(localStorage.length).toBe(0);
  });

  it("recovers an account and asks for a fresh sign-in", async () => {
    stub({
      "GET /api/auth/session": [() => json(200, signedOut)],
      "POST /api/auth/recovery": [() => json(202, accepted)],
      "POST /api/auth/recovery/complete": [() => json(200, accepted)],
    });
    render(<App />);
    const toMode = await screen.findByRole("button", {
      name: "Forgot password",
    });
    act(() => toMode.click());
    type(/Email address/, "a@example.test");
    act(() => screen.getByRole("button", { name: "Send code" }).click());
    await screen.findByLabelText(/Code/);
    type(/Code/, "recovery-code");
    type(/New password/, "another new passphrase");
    act(() => screen.getByRole("button", { name: "Set new password" }).click());
    await waitFor(() =>
      expect(screen.getByText(/every session signed out/)).toBeInTheDocument(),
    );
  });

  it("keeps the local layout when the deployment is local", async () => {
    stub({
      "GET /api/auth/session": [
        () => json(200, { ...signedOut, deployment: "local" }),
      ],
      "GET /api/stories": [() => json(200, { stories: [], schema_version: 1 })],
    });
    render(<App />);
    expect(await screen.findByText("Your stories")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sign out" })).toBeNull();
  });

  it("keeps the session visible when sign-out is not confirmed, and retries", async () => {
    let attempts = 0;
    stub({
      "GET /api/auth/session": [() => json(200, signedIn)],
      "GET /api/stories": [() => json(200, { stories: [], schema_version: 1 })],
      "POST /api/auth/sign-out": [
        () => {
          attempts += 1;
          throw new TypeError("network down");
        },
        () => json(200, signedOut),
      ],
    });
    localStorage.setItem("afterworlds:draft:s1", "unsent words");
    render(<App />);
    const signOut = await screen.findByRole("button", { name: "Sign out" });
    act(() => signOut.click());
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "may still be signed in",
    );
    // Still presented as signed in; nothing local was discarded.
    expect(screen.getByText("Your stories")).toBeInTheDocument();
    expect(localStorage.getItem("afterworlds:draft:s1")).toBe("unsent words");
    expect(attempts).toBe(1);
    act(() => screen.getByRole("button", { name: "Sign out" }).click());
    await screen.findByRole("heading", { name: "Sign in" });
    expect(localStorage.getItem("afterworlds:draft:s1")).toBeNull();
  });

  it("forgets the previous account's story and drafts when discovery confirms signed out", async () => {
    const otherSignedIn = {
      ...signedIn,
      account_id: "acct-b",
      contact_address: "b@example.test",
    };
    const calls = stub({
      "GET /api/auth/session": [() => json(200, signedOut)],
      "POST /api/auth/sign-in": [() => json(200, otherSignedIn)],
      "GET /api/stories": [() => json(200, { stories: [], schema_version: 1 })],
    });
    localStorage.setItem("afterworlds:last-story-id", "story-of-a");
    localStorage.setItem("afterworlds:draft:story-of-a", "a's unsent words");
    render(<App />);
    await screen.findByRole("heading", { name: "Sign in" });
    expect(localStorage.getItem("afterworlds:last-story-id")).toBeNull();
    expect(localStorage.getItem("afterworlds:draft:story-of-a")).toBeNull();
    type(/Email address/, "b@example.test");
    type(/^Password/, "correct horse battery staple");
    act(() => screen.getByRole("button", { name: "Sign in" }).click());
    // B lands on the story list, not A's remembered story.
    expect(await screen.findByText("Your stories")).toBeInTheDocument();
    expect(calls.some((c) => c.url.includes("story-of-a"))).toBe(false);
  });

  it("clears account state when a retried discovery confirms signed out", async () => {
    stub({
      "GET /api/auth/session": [
        () => {
          throw new TypeError("offline");
        },
        () => json(200, signedOut),
      ],
    });
    localStorage.setItem("afterworlds:last-story-id", "story-of-a");
    localStorage.setItem("afterworlds:draft:story-of-a", "a's unsent words");
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "could not be reached",
    );
    // Unknown sign-in state discards nothing.
    expect(localStorage.getItem("afterworlds:draft:story-of-a")).toBe(
      "a's unsent words",
    );
    act(() => screen.getByRole("button", { name: "Retry" }).click());
    await screen.findByRole("heading", { name: "Sign in" });
    expect(localStorage.getItem("afterworlds:last-story-id")).toBeNull();
    expect(localStorage.getItem("afterworlds:draft:story-of-a")).toBeNull();
  });

  it("keeps local story state on a local deployment", async () => {
    stub({
      "GET /api/auth/session": [
        () => json(200, { ...signedOut, deployment: "local" }),
      ],
      "GET /api/stories": [() => json(200, { stories: [], schema_version: 1 })],
    });
    localStorage.setItem("afterworlds:draft:s1", "local words");
    render(<App />);
    expect(await screen.findByText("Your stories")).toBeInTheDocument();
    expect(localStorage.getItem("afterworlds:draft:s1")).toBe("local words");
  });

  it("never treats an unanswered status read as a local deployment", async () => {
    stub({
      "GET /api/auth/session": [
        () => {
          throw new TypeError("offline");
        },
        () => json(200, signedIn),
      ],
      "GET /api/stories": [() => json(401, expired)],
    });
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "could not be reached",
    );
    expect(screen.queryByText("Your stories")).toBeNull();
    expect(screen.queryByRole("button", { name: "Account & BYOK" })).toBeNull();
    act(() => screen.getByRole("button", { name: "Retry" }).click());
    // Retried: remote and signed in; the next protected 401 returns to sign-in.
    expect(await screen.findByText(/Your session ended/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Sign in" }),
    ).toBeInTheDocument();
  });
});
