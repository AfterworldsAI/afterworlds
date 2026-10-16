import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AccountPanel from "./AccountPanel";
import App from "./App";
import type { AccountStatus } from "./api/client";

const SECRET = "sk-ant-SYNTHETIC-SECRET-0123456789abcdef"; // pragma: allowlist secret

type Provider = AccountStatus["byok"]["providers"][number];

function provider(
  name: Provider["provider"],
  overrides: Partial<Provider> = {},
): Provider {
  return {
    provider: name,
    credential_present: false,
    enabled: null,
    validation_status: null,
    last_validated_at: null,
    schema_version: 1,
    ...overrides,
  };
}

function account(overrides: {
  credits?: Partial<AccountStatus["credits"]>;
  byok?: Partial<AccountStatus["byok"]>;
  rest?: Partial<AccountStatus>;
}): AccountStatus {
  return {
    credits: {
      included: null,
      top_up: null,
      total: null,
      hosted_turn_available: false,
      hosted_unavailable_reason: "no_subscription",
      schema_version: 1,
      ...overrides.credits,
    },
    cloud_services: "not_activated",
    byok: {
      license_active: false,
      credential_store_writable: true,
      providers: [provider("anthropic"), provider("openrouter")],
      openrouter_model: null,
      byok_ready: false,
      schema_version: 1,
      ...overrides.byok,
    },
    selected_access_path: null,
    blocked_error_code: "entitlement_blocked",
    usage_estimate_available: false,
    purchase_available: false,
    trial_enrollment_available: false,
    refreshed_at: "2026-10-15T00:00:00Z",
    schema_version: 1,
    ...overrides.rest,
  };
}

type Call = { url: string; method: string; body: string | undefined };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Routes each request to the next queued response for its method+path. */
function stubFetch(
  routes: Record<string, (() => Response | Promise<Response>)[]>,
) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      calls.push({ url, method, body: init?.body as string | undefined });
      const queue = routes[`${method} ${url}`];
      const next = queue && (queue.length > 1 ? queue.shift() : queue[0]);
      if (!next) throw new Error(`unexpected ${method} ${url}`);
      return Promise.resolve(next());
    }),
  );
  return calls;
}

const apiError = (code: string, message: string) => ({
  error_code: code,
  message,
  detail: null,
  schema_version: 1,
});

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("AccountPanel billing", () => {
  it("distinguishes no plan from balances and shows exact strings", async () => {
    stubFetch({ "GET /api/account": [() => json(200, account({}))] });
    render(<AccountPanel refreshKey={0} />);
    expect(await screen.findByTestId("no-hosted-plan")).toBeInTheDocument();
    expect(screen.getByTestId("hosted-availability")).toHaveTextContent(
      "No hosted plan is active.",
    );
    expect(
      screen.getByText(/Usage estimates are not available yet/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/starting a trial are not available in this version/),
    ).toBeInTheDocument();
    expect(screen.getByTestId("cloud-services")).toHaveTextContent(
      "Not activated.",
    );
  });

  it("renders negative, depleted and retained balances verbatim", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(
            200,
            account({
              credits: {
                included: "-12.3456",
                top_up: "0.0001",
                total: "-12.3455",
                hosted_unavailable_reason: "credits_exhausted",
              },
              rest: { cloud_services: "lapsed" },
              byok: { license_active: true },
            }),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    const credits = await screen.findByTestId("hosted-credits");
    expect(credits).toHaveTextContent("-12.3456");
    expect(credits).toHaveTextContent("0.0001");
    expect(credits).toHaveTextContent("-12.3455");
    expect(screen.getByTestId("hosted-availability")).toHaveTextContent(
      /exhausted/,
    );
    expect(screen.getByTestId("cloud-services")).toHaveTextContent(
      /Lapsed.*BYOK license.*not affected/,
    );
    expect(screen.getByTestId("byok-license")).toHaveTextContent("active.");
  });

  it("explains inactive hosted access with retained balances", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(
            200,
            account({
              credits: {
                included: "40.5000",
                top_up: "3.2500",
                total: "43.7500",
                hosted_unavailable_reason: "subscription_inactive",
              },
            }),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    expect(await screen.findByTestId("hosted-credits")).toHaveTextContent(
      "43.7500",
    );
    expect(screen.getByTestId("hosted-availability")).toHaveTextContent(
      /balances are kept/,
    );
  });

  it("shows the server's selection and unknown readiness honestly", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(
            200,
            account({
              credits: {
                included: "5.0000",
                top_up: "0.0000",
                total: "5.0000",
                hosted_turn_available: true,
                hosted_unavailable_reason: null,
              },
              byok: {
                byok_ready: null,
                providers: [
                  provider("anthropic", { credential_present: null }),
                  provider("openrouter"),
                ],
              },
              rest: {
                selected_access_path: "hosted",
                blocked_error_code: null,
              },
            }),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    expect(await screen.findByTestId("selected-access-path")).toHaveTextContent(
      "would use hosted credits",
    );
    expect(screen.getByTestId("byok-ready")).toHaveTextContent(
      "BYOK readiness could not be verified.",
    );
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "unknown (could not be read)",
    );
  });

  it("re-reads on refreshKey change and marks failed refreshes stale", async () => {
    const calls = stubFetch({
      "GET /api/account": [
        () => json(200, account({})),
        () =>
          json(500, apiError("internal_error", "An internal error occurred.")),
      ],
    });
    const { rerender } = render(<AccountPanel refreshKey={0} />);
    await screen.findByTestId("no-hosted-plan");
    rerender(<AccountPanel refreshKey={1} />);
    expect(
      await screen.findByText(/may be out of date: An internal error occurred/),
    ).toBeInTheDocument();
    // The last authoritative values stay visible, never replaced by zeros.
    expect(screen.getByTestId("no-hosted-plan")).toBeInTheDocument();
    expect(calls.filter((c) => c.url === "/api/account")).toHaveLength(2);
  });

  it("shows a typed load failure with retry", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(503, apiError("credential_settings_unavailable", "Try again.")),
        () => json(200, account({})),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Try again.");
    act(() => screen.getByRole("button", { name: "Retry" }).click());
    expect(await screen.findByTestId("no-hosted-plan")).toBeInTheDocument();
  });
});

describe("AccountPanel credentials", () => {
  it("sends the key once in the body, then clears it; never stores it", async () => {
    let release: (r: Response) => void = () => {};
    const saved = account({
      byok: {
        providers: [
          provider("anthropic", {
            credential_present: true,
            enabled: true,
            validation_status: "untested",
          }),
          provider("openrouter"),
        ],
      },
    });
    const calls = stubFetch({
      "GET /api/account": [() => json(200, account({}))],
      "PUT /api/account/byok/anthropic/credential": [
        () => new Promise<Response>((r) => (release = r)),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    const input = (await screen.findByLabelText(
      "Anthropic API key",
    )) as HTMLInputElement;
    expect(input.type).toBe("password");
    expect(input.autocomplete).toBe("off");
    fireEvent.change(input, { target: { value: SECRET } });
    act(() =>
      screen.getByRole("button", { name: "Save Anthropic key" }).click(),
    );

    // Pending: confirmed only after backend success.
    expect(
      await screen.findByText("Saving Anthropic key…"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/key saved/)).toBeNull();
    expect(input).toBeDisabled();

    await act(async () => release(json(200, saved)));
    expect(await screen.findByText(/Anthropic key saved/)).toBeInTheDocument();
    expect(input.value).toBe("");
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "Not validated (still eligible for use)",
    );

    const put = calls.find((c) => c.method === "PUT")!;
    expect(JSON.parse(put.body!)).toEqual({ api_key: SECRET });
    for (const call of calls) expect(call.url).not.toContain(SECRET);
    expect(JSON.stringify({ ...localStorage })).not.toContain(SECRET);
    expect(JSON.stringify({ ...sessionStorage })).not.toContain(SECRET);
    expect(document.body.innerHTML).not.toContain(SECRET);
    // Saving never validates.
    expect(calls.some((c) => c.url.endsWith("/validate"))).toBe(false);
  });

  it("clears the key after a typed failure and re-reads state", async () => {
    const calls = stubFetch({
      "GET /api/account": [() => json(200, account({}))],
      "PUT /api/account/byok/anthropic/credential": [
        () =>
          json(
            503,
            apiError(
              "credential_store_unavailable",
              "The platform credential store is unavailable; the change was not completed.",
            ),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    const input = (await screen.findByLabelText(
      "Anthropic API key",
    )) as HTMLInputElement;
    fireEvent.change(input, { target: { value: SECRET } });
    act(() =>
      screen.getByRole("button", { name: "Save Anthropic key" }).click(),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /credential store is unavailable/,
    );
    await waitFor(() => expect(input.value).toBe(""));
    expect(screen.queryByText(/key saved/)).toBeNull();
    expect(calls.filter((c) => c.url === "/api/account")).toHaveLength(2);
  });

  it("validates only after explicit acknowledgement", async () => {
    const configured = account({
      byok: {
        providers: [
          provider("anthropic", {
            credential_present: true,
            enabled: true,
            validation_status: "untested",
          }),
          provider("openrouter"),
        ],
      },
    });
    const validated = account({
      byok: {
        providers: [
          provider("anthropic", {
            credential_present: true,
            enabled: true,
            validation_status: "valid",
            last_validated_at: "2026-10-15T00:00:00Z",
          }),
          provider("openrouter"),
        ],
      },
    });
    const calls = stubFetch({
      "GET /api/account": [() => json(200, configured)],
      "POST /api/account/byok/anthropic/validate": [() => json(200, validated)],
    });
    render(<AccountPanel refreshKey={0} />);
    const validate = await screen.findByRole("button", {
      name: "Validate Anthropic key",
    });
    expect(validate).toBeDisabled();
    act(() => screen.getByLabelText(/Validating contacts Anthropic/).click());
    act(() => validate.click());
    expect(
      await screen.findByText("Anthropic validation recorded."),
    ).toBeInTheDocument();
    const post = calls.find((c) => c.method === "POST")!;
    expect(JSON.parse(post.body!)).toEqual({
      acknowledge_provider_contact: true,
    });
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "Validated",
    );
    expect(
      screen.getByLabelText(/Validating contacts Anthropic/),
    ).not.toBeChecked();
  });

  it("toggles, removes and configures the OpenRouter model", async () => {
    const configured = account({
      byok: {
        providers: [
          provider("anthropic"),
          provider("openrouter", {
            credential_present: true,
            enabled: true,
            validation_status: "untested",
          }),
        ],
        openrouter_model: "mistralai/mistral-large-2411",
      },
    });
    const calls = stubFetch({
      "GET /api/account": [() => json(200, configured)],
      "PUT /api/account/byok/openrouter/enabled": [() => json(200, configured)],
      "PUT /api/account/byok/openrouter/model": [
        () => json(422, apiError("validation_failed", "Enter an exact model.")),
        () => json(200, configured),
      ],
      "DELETE /api/account/byok/openrouter/credential": [
        () => json(200, account({})),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    const model = (await screen.findByLabelText(
      "OpenRouter model",
    )) as HTMLInputElement;
    expect(model.value).toBe("mistralai/mistral-large-2411");

    act(() =>
      screen.getByRole("button", { name: "Disable OpenRouter" }).click(),
    );
    expect(await screen.findByText("OpenRouter disabled.")).toBeInTheDocument();
    expect(JSON.parse(calls.at(-1)!.body!)).toEqual({ enabled: false });

    fireEvent.change(model, { target: { value: "openrouter/auto" } });
    act(() => screen.getByRole("button", { name: "Save model" }).click());
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Enter an exact model.",
    );

    act(() => screen.getByRole("button", { name: "Clear model" }).click());
    expect(
      await screen.findByText("OpenRouter model cleared."),
    ).toBeInTheDocument();
    expect(JSON.parse(calls.at(-1)!.body!)).toEqual({ model_identifier: null });

    act(() =>
      screen.getByRole("button", { name: "Remove OpenRouter key" }).click(),
    );
    expect(
      await screen.findByText("OpenRouter key removed."),
    ).toBeInTheDocument();
  });

  it("reports a read-only credential store and disables writes", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(200, account({ byok: { credential_store_writable: false } })),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    expect(await screen.findByTestId("store-read-only")).toBeInTheDocument();
    expect(screen.getByLabelText("Anthropic API key")).toBeDisabled();
    expect(screen.queryByRole("button", { name: /Remove/ })).toBeNull();
  });
});

describe("AccountPanel unknown readiness", () => {
  it("does not claim absence or a cause when the probe failed", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(
            200,
            account({
              byok: {
                license_active: true,
                byok_ready: null,
                providers: [
                  provider("anthropic", {
                    credential_present: true,
                    enabled: true,
                    validation_status: "valid",
                  }),
                  provider("openrouter"),
                ],
              },
              rest: { blocked_error_code: "byok_credentials_required" },
            }),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    const selection = await screen.findByTestId("selected-access-path");
    expect(selection).toHaveTextContent(
      "BYOK readiness could not be verified, so BYOK is not used.",
    );
    expect(selection).not.toHaveTextContent(/no provider key/);
    expect(screen.getByTestId("byok-ready")).toHaveTextContent(
      "BYOK readiness could not be verified.",
    );
    expect(screen.getByTestId("byok-ready")).not.toHaveTextContent(
      /credential store|No provider key/,
    );
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      /Key: saved/,
    );
  });
});

function deferred() {
  let resolve: (r: Response) => void = () => {};
  const promise = new Promise<Response>((r) => (resolve = r));
  return { promise, resolve };
}

const before = account({});
const after = account({
  byok: {
    providers: [
      provider("anthropic", {
        credential_present: true,
        enabled: true,
        validation_status: "untested",
      }),
      provider("openrouter"),
    ],
  },
});

describe("AccountPanel unverified credential", () => {
  it("shows an incomplete replacement as unverified, not a verdict", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(
            200,
            account({
              byok: {
                license_active: true,
                providers: [
                  provider("anthropic", {
                    credential_present: true,
                    enabled: true,
                    validation_status: "error",
                    last_validated_at: null,
                  }),
                  provider("openrouter"),
                ],
              },
              rest: { blocked_error_code: "byok_credentials_required" },
            }),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    const anthropic = await screen.findByTestId("provider-anthropic");
    expect(anthropic).toHaveTextContent(
      "Not verified: a key change did not complete",
    );
    expect(anthropic).not.toHaveTextContent(/Validation error|Validated/);
    // Recovery stays available.
    expect(
      screen.getByRole("button", { name: "Validate Anthropic key" }),
    ).toBeInTheDocument();
  });

  it("keeps a real validation error with its time", async () => {
    stubFetch({
      "GET /api/account": [
        () =>
          json(
            200,
            account({
              byok: {
                providers: [
                  provider("anthropic", {
                    credential_present: true,
                    enabled: true,
                    validation_status: "error",
                    last_validated_at: "2026-10-15T00:00:00Z",
                  }),
                  provider("openrouter"),
                ],
              },
            }),
          ),
      ],
    });
    render(<AccountPanel refreshKey={0} />);
    expect(await screen.findByTestId("provider-anthropic")).toHaveTextContent(
      "Validation error (not used)",
    );
  });
});

describe("AccountPanel mutation/read ordering", () => {
  async function startSave(
    reads: (() => Response | Promise<Response>)[],
    put: Promise<Response>,
  ) {
    const calls = stubFetch({
      "GET /api/account": reads,
      "PUT /api/account/byok/anthropic/credential": [() => put],
    });
    const view = render(<AccountPanel refreshKey={0} />);
    fireEvent.change(await screen.findByLabelText("Anthropic API key"), {
      target: { value: SECRET },
    });
    act(() =>
      screen.getByRole("button", { name: "Save Anthropic key" }).click(),
    );
    expect(
      await screen.findByText("Saving Anthropic key…"),
    ).toBeInTheDocument();
    return { calls, view };
  }

  const gets = (calls: Call[]) =>
    calls.filter((c) => c.method === "GET").length;

  it("defers a refresh clicked while a change is pending", async () => {
    const put = deferred();
    const { calls } = await startSave(
      [() => json(200, before), () => json(200, after)],
      put.promise,
    );
    act(() => screen.getByRole("button", { name: "Refresh" }).click());
    // No read starts while the change is in flight.
    expect(gets(calls)).toBe(1);

    await act(async () => put.resolve(json(200, after)));
    await waitFor(() => expect(gets(calls)).toBe(2));
    expect(await screen.findByText(/Anthropic key saved/)).toBeInTheDocument();
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "Key: saved",
    );
    expect(screen.queryByText(/may be out of date/)).toBeNull();
  });

  it("defers a turn-triggered refresh begun during the change", async () => {
    const put = deferred();
    const { calls, view } = await startSave(
      [() => json(200, before), () => json(200, after)],
      put.promise,
    );
    view.rerender(<AccountPanel refreshKey={1} />);
    expect(gets(calls)).toBe(1);
    await act(async () => put.resolve(json(200, after)));
    await waitFor(() => expect(gets(calls)).toBe(2));
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "Key: saved",
    );
  });

  it("discards a read already in flight when the change starts", async () => {
    const put = deferred();
    const slowRead = deferred();
    const calls = stubFetch({
      "GET /api/account": [() => json(200, before), () => slowRead.promise],
      "PUT /api/account/byok/anthropic/credential": [() => put.promise],
    });
    const view = render(<AccountPanel refreshKey={0} />);
    fireEvent.change(await screen.findByLabelText("Anthropic API key"), {
      target: { value: SECRET },
    });
    view.rerender(<AccountPanel refreshKey={1} />); // read begins (pre-commit)
    await waitFor(() => expect(gets(calls)).toBe(2));
    act(() =>
      screen.getByRole("button", { name: "Save Anthropic key" }).click(),
    );
    await act(async () => put.resolve(json(200, after)));
    expect(await screen.findByText(/Anthropic key saved/)).toBeInTheDocument();
    // The pre-commit read lands last but must not overwrite the result.
    await act(async () => slowRead.resolve(json(200, before)));
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "Key: saved",
    );
    expect(screen.queryByText("Refreshing…")).toBeNull();
  });

  it("re-reads once after a failed change, marking state stale until then", async () => {
    const put = deferred();
    const reread = deferred();
    const { calls } = await startSave(
      [() => json(200, before), () => reread.promise],
      put.promise,
    );
    await act(async () =>
      put.resolve(json(503, apiError("credential_store_unavailable", "Down."))),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("Down.");
    expect(gets(calls)).toBe(2);
    expect(screen.getByText("Refreshing…")).toBeInTheDocument();
    await act(async () => reread.resolve(json(200, before)));
    expect(screen.getByTestId("provider-anthropic")).toHaveTextContent(
      "Key: not set",
    );
    expect(screen.queryByText(/key saved/)).toBeNull();
  });
});

describe("App account view", () => {
  it("re-reads the account when a turn started before opening it settles", async () => {
    const story = {
      story_id: "s1",
      title: "First",
      mode: "branching",
      status: "in_play",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      schema_version: 1,
    };
    const turn = deferred();
    const accountReads: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, init?: RequestInit) => {
        const path = url.split("?")[0]!;
        const method = init?.method ?? "GET";
        if (method === "POST" && path === "/api/stories/s1/turns")
          return turn.promise;
        if (path === "/api/account") {
          accountReads.push(url);
          return Promise.resolve(json(200, account({})));
        }
        const bodies: Record<string, unknown> = {
          "/api/stories": { stories: [story], schema_version: 1 },
          "/api/stories/s1": story,
          "/api/stories/s1/turns": { turns: [], schema_version: 1 },
          "/api/stories/s1/visible-state": { visible_state: null },
        };
        return Promise.resolve(json(200, bodies[path]));
      }),
    );
    render(<App />);
    const first = await screen.findByRole("button", { name: /^First/ });
    act(() => first.click());
    const textarea = await screen.findByPlaceholderText("What do you do?");
    fireEvent.change(textarea, { target: { value: "hello" } });
    act(() => screen.getByRole("button", { name: /submit/i }).click());

    // Open the account view while the turn is still in flight.
    act(() => screen.getByRole("button", { name: "Account & BYOK" }).click());
    await screen.findByTestId("no-hosted-plan");
    expect(accountReads).toHaveLength(1);

    await act(async () =>
      turn.resolve(
        json(200, {
          disposition: "delivered",
          turn_id: "t1",
          delivered_output: "ok",
          stable_prefix_cache_warmed: false,
          interaction_rejection_reason: null,
          interaction_rejection_message: null,
          pipeline_error_summary: null,
          provider_refusal: null,
          pending_roll_redirect_message: null,
          settlement_warning: null,
          visible_state: null,
          schema_version: 1,
        }),
      ),
    );
    await waitFor(() => expect(accountReads).toHaveLength(2));
  });

  it("opens the account view from the header", async () => {
    stubFetch({
      "GET /api/stories": [() => json(200, { stories: [], schema_version: 1 })],
      "GET /api/account": [() => json(200, account({}))],
    });
    render(<App />);
    act(() => screen.getByRole("button", { name: "Account & BYOK" }).click());
    expect(await screen.findByTestId("no-hosted-plan")).toBeInTheDocument();
    act(() => screen.getByRole("button", { name: "Close account" }).click());
    expect(await screen.findByText("Your stories")).toBeInTheDocument();
  });
});
