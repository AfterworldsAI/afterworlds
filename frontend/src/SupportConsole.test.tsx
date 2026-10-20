import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { setSignedOutListener, type AdminAccountView } from "./api/client";
import SupportConsole from "./SupportConsole";

type Call = { url: string; method: string; body: string | undefined };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

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

const ACCOUNT = "55555555-5555-5555-5555-555555555555";
const EVENT = "66666666-6666-6666-6666-666666666666";

function view(overrides: Partial<AdminAccountView> = {}): AdminAccountView {
  return {
    account_id: ACCOUNT,
    status: "active",
    created_at: "2026-10-19T00:00:00Z",
    closed_at: null,
    owned_story_count: 2,
    credits: {
      included: "-1.5000",
      top_up: "0.0000",
      total: "-1.5000",
      hosted_turn_available: false,
      hosted_unavailable_reason: "credits_exhausted",
      schema_version: 1,
    },
    cloud_services: "lapsed",
    byok_license_active: true,
    byok_readiness_source: "unavailable_remotely",
    entitlement_state: "present",
    hosted_access_active: true,
    hosted_plan: "subscription",
    cloud_services_expires_at: null,
    byok_license_purchased_at: null,
    last_entitlement_event_id: EVENT,
    expected_conditions: ["negative_balance", "credits_exhausted"],
    replay: {
      status: "consistent",
      detail_code: null,
      through_sequence: 3,
      mismatched_fields: [],
      schema_version: 1,
    },
    schema_version: 1,
    ...overrides,
  };
}

function page(after: number, next: number | null) {
  return {
    account_id: ACCOUNT,
    order: "global_sequence_ascending",
    after_sequence: after,
    events: [
      {
        global_sequence: after + 1,
        event_id: `00000000-0000-0000-0000-00000000000${after + 1}`,
        event_type: "manual_credit_adjustment",
        created_at: "2026-10-19T00:00:00Z",
        hosted_credit_delta: "5.0000",
        manual_reason: "<script>x</script>",
        schema_version: 1,
      },
    ],
    total_events: 2,
    next_after_sequence: next,
    replay: view().replay,
    schema_version: 1,
  };
}

const unauthenticated = () =>
  json(401, {
    error_code: "authentication_required",
    message: "Authentication required.",
    detail: null,
    schema_version: 1,
  });

// Fresh queues per test: the first admin read finds no staff session.
const empty = () => {
  const routes: Record<string, (() => Response)[]> = {
    "GET /api/admin/data-requests": [
      () => json(200, { requests: [], schema_version: 1 }),
    ],
    "GET /api/admin/anomalies": [
      () =>
        json(200, {
          anomalies: [],
          sources: {
            entitlement_replay: "unavailable",
            commercial_events: "not_integrated",
          },
          generated_at: "2026-10-19T00:00:00Z",
          schema_version: 1,
        }),
    ],
  };
  routes["GET /api/admin/data-requests"]!.unshift(unauthenticated);
  return routes;
};

async function signIn() {
  fireEvent.change(screen.getByLabelText("Staff email"), {
    target: { value: "o@e.t" },
  });
  fireEvent.change(screen.getByLabelText("Staff password"), {
    target: { value: "pw" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign in to staff" }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  setSignedOutListener(null);
});

describe("SupportConsole", () => {
  it("signs in to staff separately and shows source-bound account state", async () => {
    const signedOut = vi.fn();
    setSignedOutListener(signedOut);
    stubFetch({
      ...empty(),
      "POST /api/admin/session": [
        () =>
          json(401, {
            error_code: "authentication_required",
            message: "Authentication required.",
            detail: null,
            schema_version: 1,
          }),
        () => json(200, { signed_in: true, schema_version: 1 }),
      ],
      [`GET /api/admin/accounts/${ACCOUNT}`]: [() => json(200, view())],
      [`GET /api/admin/accounts/${ACCOUNT}/entitlement-history?after_sequence=0&limit=50`]:
        [() => json(200, page(0, 1))],
      [`GET /api/admin/accounts/${ACCOUNT}/entitlement-history?after_sequence=1&limit=50`]:
        [() => json(200, page(1, null))],
    });
    render(<SupportConsole />);
    await screen.findByRole("button", { name: "Sign in to staff" });
    await signIn();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Authentication required.",
    );
    // A staff 401 never ends the ordinary session view.
    expect(signedOut).not.toHaveBeenCalled();
    await signIn();
    fireEvent.change(await screen.findByLabelText("Account ID"), {
      target: { value: ACCOUNT },
    });
    fireEvent.click(screen.getByRole("button", { name: "Look up" }));
    expect(await screen.findByText(/included -1.5000/)).toBeInTheDocument();
    expect(
      screen.getByText(/not visible to the remote service/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Expected conditions: negative_balance/),
    ).toBeInTheDocument();
    expect(screen.getByText(/<script>x<\/script>/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Load more" }));
    await waitFor(() =>
      expect(
        screen.getByRole("list", { name: "Entitlement history" }).children,
      ).toHaveLength(2),
    );
    expect(
      screen.queryByRole("button", { name: "Load more" }),
    ).not.toBeInTheDocument();
  });

  it("previews, confirms once and reads back an uncertain adjustment by the same ID", async () => {
    const calls = stubFetch({
      ...empty(),
      "POST /api/admin/session": [
        () => json(200, { signed_in: true, schema_version: 1 }),
      ],
      [`GET /api/admin/accounts/${ACCOUNT}`]: [() => json(200, view())],
      [`GET /api/admin/accounts/${ACCOUNT}/entitlement-history?after_sequence=0&limit=50`]:
        [() => json(200, page(0, null))],
      [`POST /api/admin/accounts/${ACCOUNT}/credit-adjustments/preview`]: [
        () =>
          json(200, {
            account_id: ACCOUNT,
            current: view().credits,
            hosted_credit_delta: "5.0000",
            top_up_credit_delta: "0.0000",
            resulting_included: "3.5000",
            resulting_top_up: "0.0000",
            last_entitlement_event_id: EVENT,
            refusal_code: null,
            schema_version: 1,
          }),
      ],
      [`POST /api/admin/accounts/${ACCOUNT}/credit-adjustments`]: [
        () =>
          json(503, {
            error_code: "operation_outcome_unknown",
            message: "The adjustment's outcome is unknown.",
            detail: null,
            schema_version: 1,
          }),
      ],
    });
    render(<SupportConsole />);
    await screen.findByRole("button", { name: "Sign in to staff" });
    await signIn();
    fireEvent.change(await screen.findByLabelText("Account ID"), {
      target: { value: ACCOUNT },
    });
    fireEvent.click(screen.getByRole("button", { name: "Look up" }));
    fireEvent.change(await screen.findByLabelText("Included credits delta"), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Preview adjustment" }));
    const region = await screen.findByRole("region", {
      name: "Adjustment preview",
    });
    expect(region).toHaveTextContent("-1.5000 → 3.5000");
    const confirm = screen.getByRole("button", { name: "Confirm adjustment" });
    expect(confirm).toBeDisabled(); // a reason is required
    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "goodwill" },
    });
    // Changing the form discards the preview; preview again.
    fireEvent.click(screen.getByRole("button", { name: "Preview adjustment" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm adjustment" }),
    );
    expect(await screen.findByText(/Outcome unknown/)).toBeInTheDocument();
    const adjust = calls.find((c) => c.url.endsWith("/credit-adjustments"))!;
    const operationId = JSON.parse(adjust.body!).operation_id as string;
    expect(JSON.parse(adjust.body!).expected_last_entitlement_event_id).toBe(
      EVENT,
    );
    // No automatic retry happened.
    expect(
      calls.filter((c) => c.url.endsWith("/credit-adjustments")),
    ).toHaveLength(1);

    stubFetch({
      ...empty(),
      [`GET /api/admin/support-operations/${operationId}`]: [
        () =>
          json(200, {
            operation_id: operationId,
            outcome_code: "committed",
            source_entitlement_event_id: EVENT,
            events: [],
            account: view({
              credits: { ...view().credits, included: "3.5000" },
            }),
            schema_version: 1,
          }),
      ],
      [`GET /api/admin/accounts/${ACCOUNT}`]: [() => json(200, view())],
      [`GET /api/admin/accounts/${ACCOUNT}/entitlement-history?after_sequence=0&limit=50`]:
        [() => json(200, page(0, null))],
    });
    fireEvent.click(screen.getByRole("button", { name: "Check status" }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      `event ${EVENT}`,
    );
  });

  function previewBody(delta: string) {
    return {
      account_id: ACCOUNT,
      current: view().credits,
      hosted_credit_delta: delta,
      top_up_credit_delta: "0.0000",
      resulting_included: "x",
      resulting_top_up: "0.0000",
      last_entitlement_event_id: EVENT,
      refusal_code: null,
      schema_version: 1,
    };
  }

  function committed(operationId: string) {
    return {
      operation_id: operationId,
      outcome_code: "committed",
      source_entitlement_event_id: EVENT,
      events: [],
      account: view(),
      schema_version: 1,
    };
  }

  async function openAdjustment() {
    render(<SupportConsole />);
    await screen.findByRole("button", { name: "Sign in to staff" });
    await signIn();
    fireEvent.change(await screen.findByLabelText("Account ID"), {
      target: { value: ACCOUNT },
    });
    fireEvent.click(screen.getByRole("button", { name: "Look up" }));
    await screen.findByLabelText("Included credits delta");
  }

  const PREVIEW = `POST /api/admin/accounts/${ACCOUNT}/credit-adjustments/preview`;
  const ADJUST = `POST /api/admin/accounts/${ACCOUNT}/credit-adjustments`;
  const base = () => ({
    ...empty(),
    "POST /api/admin/session": [
      () => json(200, { signed_in: true, schema_version: 1 }),
    ],
    [`GET /api/admin/accounts/${ACCOUNT}`]: [() => json(200, view())],
    [`GET /api/admin/accounts/${ACCOUNT}/entitlement-history?after_sequence=0&limit=50`]:
      [() => json(200, page(0, null))],
  });

  it("shows only the latest preview and confirms exactly the previewed request", async () => {
    let releaseOld: (r: Response) => void = () => {};
    const calls = stubFetch({
      ...base(),
      [PREVIEW]: [
        () => new Promise<Response>((r) => (releaseOld = r)),
        () => json(200, previewBody("50.0000")),
      ],
      [ADJUST]: [() => json(200, committed("x"))],
    });
    await openAdjustment();
    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "goodwill" },
    });
    fireEvent.change(screen.getByLabelText("Included credits delta"), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Preview adjustment" }));
    fireEvent.change(screen.getByLabelText("Included credits delta"), {
      target: { value: "50" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Preview adjustment" }));
    const region = await screen.findByRole("region", {
      name: "Adjustment preview",
    });
    expect(region).toHaveTextContent("deltas 50.0000");
    releaseOld(json(200, previewBody("5.0000"))); // the older, slower answer
    await new Promise((r) => setTimeout(r, 0));
    expect(region).toHaveTextContent("deltas 50.0000");
    expect(region).not.toHaveTextContent("5.0000 /");
    fireEvent.click(screen.getByRole("button", { name: "Confirm adjustment" }));
    await screen.findByRole("status");
    const body = JSON.parse(
      calls.find((c) => c.url.endsWith("/credit-adjustments"))!.body!,
    );
    expect(body.hosted_credit_delta).toBe("50");
    expect(body.reason).toBe("goodwill");
  });

  it("locks an uncertain action to its ID and starts a new one only after a terminal rejection", async () => {
    const calls = stubFetch({
      ...base(),
      [PREVIEW]: [() => json(200, previewBody("5.0000"))],
      [ADJUST]: [
        () =>
          json(503, {
            error_code: "operation_outcome_unknown",
            message: "Unknown.",
            detail: null,
            schema_version: 1,
          }),
        () => json(200, committed("y")),
      ],
    });
    await openAdjustment();
    fireEvent.change(screen.getByLabelText("Reason"), {
      target: { value: "goodwill" },
    });
    fireEvent.change(screen.getByLabelText("Included credits delta"), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Preview adjustment" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm adjustment" }),
    );
    expect(await screen.findByText(/Outcome unknown/)).toBeInTheDocument();
    // The submitted action cannot be edited or re-sent while uncertain.
    expect(screen.getByLabelText("Included credits delta")).toBeDisabled();
    expect(screen.getByLabelText("Reason")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Confirm adjustment" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Preview adjustment" }),
    ).toBeDisabled();
    const first = JSON.parse(
      calls.filter((c) => c.url.endsWith("/credit-adjustments"))[0]!.body!,
    ).operation_id as string;

    const statusPath = `GET /api/admin/support-operations/${first}`;
    const routes: Record<string, (() => Response)[]> = {
      [statusPath]: [
        () =>
          json(200, {
            ...committed(first),
            outcome_code: "requested",
            source_entitlement_event_id: null,
          }),
        () =>
          json(200, {
            ...committed(first),
            outcome_code: "rejected_stale",
            source_entitlement_event_id: null,
          }),
      ],
    };
    const more = stubFetch({
      ...base(),
      ...routes,
      [PREVIEW]: [() => json(200, previewBody("5.0000"))],
      [ADJUST]: [() => json(200, committed("y"))],
    });
    fireEvent.click(screen.getByRole("button", { name: "Check status" }));
    expect(
      await screen.findByText(/still recorded as requested/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Included credits delta")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Check status" }));
    expect(
      await screen.findByText(/Not applied: Recorded outcome: rejected_stale/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Included credits delta")).toBeEnabled();
    expect(
      screen.queryByRole("region", { name: "Adjustment preview" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Preview adjustment" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm adjustment" }),
    );
    await screen.findByRole("status");
    const second = JSON.parse(
      more.find((c) => c.url.endsWith("/credit-adjustments"))!.body!,
    ).operation_id as string;
    // Both status reads asked about the submitted action's own ID.
    expect(
      more
        .filter((c) => c.url.includes("/support-operations/"))
        .map((c) => c.url.endsWith(first)),
    ).toEqual([true, true]);
    expect(second).not.toBe(first);
  });

  it("drives the request queue, anomaly notes and retention expiry", async () => {
    const request = {
      request_id: "77777777-7777-7777-7777-777777777777",
      kind: "deletion",
      environment: "remote",
      scope: "story",
      story_ids: [],
      state: "awaiting_authorization",
      revision: 2,
      requested_at: "2026-10-19T00:00:00Z",
      verified_at: "2026-10-19T00:00:00Z",
      confirmed_at: null,
      approved_at: null,
      closed_at: null,
      export_deadline_at: null,
      live_deadline_at: null,
      backup_deadline_at: null,
      overdue: [],
      progress_code: null,
      policy_version: "v",
      transitions: [],
      phases: [],
      receipts: [],
      artifact: null,
      subject_ref: ACCOUNT,
      schema_version: 1,
    };
    const anomaly = {
      anomaly_id: "turn_settlement:t1",
      source_kind: "turn_settlement",
      source_id: "t1",
      subject_ref: ACCOUNT,
      observed_at: "2026-10-19T00:00:00Z",
      signal_code: "settlement_failed",
      explanation: "A delivered turn's settlement failed.",
      investigation_state: "open",
      notes: [],
      schema_version: 1,
    };
    const calls = stubFetch({
      "POST /api/admin/session": [
        () => json(200, { signed_in: true, schema_version: 1 }),
      ],
      "GET /api/admin/data-requests": [
        unauthenticated,
        () => json(200, { requests: [request], schema_version: 1 }),
        () =>
          json(200, {
            requests: [
              {
                ...request,
                state: "in_progress",
                progress_code: "x_pending",
                revision: 4,
              },
            ],
            schema_version: 1,
          }),
      ],
      [`POST /api/admin/data-requests/${request.request_id}/approve`]: [
        () => json(200, request),
      ],
      [`POST /api/admin/data-requests/${request.request_id}/finalize`]: [
        () => json(200, request),
      ],
      "GET /api/admin/anomalies": [
        () =>
          json(200, {
            anomalies: [anomaly],
            sources: { settlement_failures: "available" },
            generated_at: "2026-10-19T00:00:00Z",
            schema_version: 1,
          }),
      ],
      [`POST /api/admin/anomalies/${encodeURIComponent(anomaly.anomaly_id)}/notes`]:
        [() => json(200, { ...anomaly, investigation_state: "closed" })],
      "POST /api/admin/maintenance/retention-sweep": [
        () =>
          json(200, {
            counts: { artifacts_expired: 1 },
            swept_at: "2026-10-19T00:00:00Z",
            schema_version: 1,
          }),
      ],
      "DELETE /api/admin/session": [
        () => json(200, { signed_in: false, schema_version: 1 }),
      ],
    });
    render(<SupportConsole />);
    await screen.findByRole("button", { name: "Sign in to staff" });
    await signIn();
    const approve = await screen.findByRole("button", { name: "Approve" });
    expect(approve).toBeDisabled(); // a review reason is required
    fireEvent.change(screen.getByLabelText("Review reason"), {
      target: { value: "verified owner" },
    });
    fireEvent.click(approve);
    await waitFor(() => {
      const call = calls.find((c) => c.url.endsWith("/approve"));
      expect(JSON.parse(call!.body!).reason).toBe("verified owner");
    });
    fireEvent.click(
      await screen.findByRole("button", { name: "Re-check completion" }),
    );
    await waitFor(() =>
      expect(calls.some((c) => c.url.endsWith("/finalize"))).toBe(true),
    );
    expect(await screen.findByText(/settlement_failed/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    await waitFor(() =>
      expect(calls.some((c) => c.url.includes("/notes"))).toBe(true),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Run retention expiry" }),
    );
    expect(await screen.findByText("artifacts_expired: 1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sign out of staff" }));
    expect(
      await screen.findByRole("button", { name: "Sign in to staff" }),
    ).toBeInTheDocument();
  });
});
