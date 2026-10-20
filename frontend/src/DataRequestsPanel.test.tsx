import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DataRequest, DeletionPreview } from "./api/client";
import DataRequestsPanel, { ReceiptLookup } from "./DataRequestsPanel";

type Call = { url: string; method: string; body: string | undefined };

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubFetch(routes: Record<string, (() => Response)[]>) {
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

const STORY = "11111111-1111-1111-1111-111111111111";

function request(overrides: Partial<DataRequest> = {}): DataRequest {
  return {
    request_id: "22222222-2222-2222-2222-222222222222",
    kind: "export",
    environment: "remote",
    scope: "story",
    story_ids: [STORY],
    state: "awaiting_authorization",
    revision: 1,
    requested_at: "2026-10-19T00:00:00Z",
    verified_at: "2026-10-19T00:00:00Z",
    confirmed_at: null,
    approved_at: null,
    closed_at: null,
    export_deadline_at: "2026-10-26T00:00:00Z",
    live_deadline_at: null,
    backup_deadline_at: null,
    overdue: [],
    progress_code: null,
    policy_version: "crd22-matrix-r1",
    transitions: [],
    phases: [],
    receipts: [],
    artifact: null,
    subject_ref: null,
    schema_version: 1,
    ...overrides,
  };
}

const preview: DeletionPreview = {
  scope: "account",
  story_ids: [STORY],
  counts: { stories: 1, turns: 3 },
  removed_classes: ["turns", "story_bible"],
  retained_categories: [
    {
      code: "entitlement_history",
      purpose: "Reconstruct credit effects.",
      end_condition: "24 months after closure.",
      schema_version: 1,
    },
  ],
  scope_revision: "rev-1",
  live_deletion_limit_days: 7,
  final_deletion_limit_days: 30,
  commercial_dependency: "dependency_unavailable",
  notices: ["Files on your own device are not touched."],
  schema_version: 1,
};

const stories = {
  stories: [
    {
      story_id: STORY,
      title: "The Gate",
      mode: "branching",
      status: "in_play",
      updated_at: "2026-10-19T00:00:00Z",
      schema_version: 1,
    },
  ],
  schema_version: 1,
};

afterEach(() => vi.unstubAllGlobals());

describe("DataRequestsPanel", () => {
  it("shows authoritative states, deadlines, phases and a download", async () => {
    stubFetch({
      "GET /api/data-requests": [
        () =>
          json(200, {
            requests: [
              request({
                state: "completed",
                missed_deadlines: ["export_production"],
                artifact: {
                  status: "available",
                  available_at: "2026-10-19T00:00:00Z",
                  expires_at: "2026-10-26T00:00:00Z",
                  removed_at: null,
                  size_bytes: 10,
                  schema_version: 1,
                },
              }),
              request({
                request_id: "33333333-3333-3333-3333-333333333333",
                kind: "deletion",
                state: "in_progress",
                progress_code: "active_data_removed_backups_pending",
                overdue: ["final_deletion"],
                phases: [
                  {
                    phase_code: "backups",
                    outcome_code: "pending",
                    attempt_id: "44444444-4444-4444-4444-444444444444",
                    counts: {},
                    detail_code: null,
                    observed_at: "2026-10-19T00:00:00Z",
                    deadline_at: null,
                    schema_version: 1,
                  },
                ],
              }),
            ],
            schema_version: 1,
          }),
      ],
      "GET /api/stories": [() => json(200, stories)],
    });
    render(<DataRequestsPanel local={false} />);
    expect(await screen.findByText(/Export of “The Gate”/)).toBeInTheDocument();
    expect(screen.getByText(/: Completed/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Download export/ }),
    ).toHaveAttribute(
      "href",
      "/api/data-requests/22222222-2222-2222-2222-222222222222/artifact",
    );
    expect(
      screen.getByText(/active data removed backups pending/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Overdue: final_deletion/)).toBeInTheDocument();
    expect(screen.getByText(/backups: pending/)).toBeInTheDocument();
    expect(
      screen.getByText(/Completed late: export_production/),
    ).toBeInTheDocument();
  });

  it("previews, confirms account deletion with the password and shows the receipt code once", async () => {
    const created = request({
      kind: "deletion",
      scope: "account",
      state: "requested",
      story_ids: [],
    });
    const calls = stubFetch({
      "GET /api/data-requests": [
        () => json(200, { requests: [], schema_version: 1 }),
      ],
      "GET /api/stories": [() => json(200, stories)],
      "POST /api/data-requests": [() => json(201, created)],
      [`GET /api/data-requests/${created.request_id}/deletion-preview`]: [
        () => json(200, preview),
      ],
      [`POST /api/data-requests/${created.request_id}/confirm`]: [
        () =>
          json(200, {
            request: {
              ...created,
              state: "awaiting_authorization",
              revision: 2,
            },
            receipt_credential: "receipt-secret-code",
            schema_version: 1,
          }),
      ],
    });
    render(<DataRequestsPanel local={false} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Delete my account…" }),
    );
    expect(await screen.findByRole("dialog")).toHaveTextContent(
      /There is no undo/,
    );
    expect(screen.getByText(/Export first/)).toBeInTheDocument();
    expect(screen.getByText(/stay incomplete/)).toBeInTheDocument();
    expect(
      screen.getByRole("list", { name: "Kept records" }),
    ).toHaveTextContent("entitlement_history");
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "pw-123456789012" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirm deletion" }));
    expect(await screen.findByText("receipt-secret-code")).toBeInTheDocument();
    const confirm = calls.find((c) => c.url.endsWith("/confirm"))!;
    expect(JSON.parse(confirm.body!)).toEqual({
      expected_revision: 1,
      scope_revision: "rev-1",
      password: "pw-123456789012",
    });
    fireEvent.click(screen.getByRole("button", { name: "I have saved it" }));
    expect(screen.queryByText("receipt-secret-code")).not.toBeInTheDocument();
    expect(localStorage.length).toBe(0);
  });

  it("lets the local owner run and retry, and reports errors without guessing", async () => {
    const failed = request({
      environment: "local",
      state: "failed",
      revision: 4,
    });
    const calls = stubFetch({
      "GET /api/data-requests": [
        () => json(200, { requests: [failed], schema_version: 1 }),
      ],
      "GET /api/stories": [() => json(200, stories)],
      [`POST /api/data-requests/${failed.request_id}/execute`]: [
        () =>
          json(409, {
            error_code: "operation_stale",
            message: "The request is at revision 5, not 4.",
            detail: null,
            schema_version: 1,
          }),
      ],
    });
    render(<DataRequestsPanel local />);
    expect(
      await screen.findByText(/all data on this device/),
    ).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Retry now" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("revision 5");
    expect(calls.filter((c) => c.method === "POST")).toHaveLength(1);
  });

  it("creates a Story export only for a chosen Story", async () => {
    const calls = stubFetch({
      "GET /api/data-requests": [
        () => json(200, { requests: [], schema_version: 1 }),
      ],
      "GET /api/stories": [() => json(200, stories)],
      "POST /api/data-requests": [() => json(201, request())],
    });
    render(<DataRequestsPanel local={false} />);
    const exportButton = await screen.findByRole("button", {
      name: "Export Story",
    });
    expect(exportButton).toBeDisabled();
    await screen.findByRole("option", { name: "The Gate" });
    fireEvent.change(screen.getByLabelText("Story"), {
      target: { value: STORY },
    });
    fireEvent.click(exportButton);
    await waitFor(() =>
      expect(calls.some((c) => c.method === "POST")).toBe(true),
    );
    const body = JSON.parse(calls.find((c) => c.method === "POST")!.body!);
    expect(body).toEqual({ kind: "export", scope: "story", story_id: STORY });
  });

  it("reissues a lost receipt code with the password and shows it once", async () => {
    const confirmed = request({
      kind: "deletion",
      scope: "account",
      state: "awaiting_authorization",
      story_ids: [],
      confirmed_at: "2026-10-19T00:00:00Z",
      revision: 2,
    });
    const calls = stubFetch({
      "GET /api/data-requests": [
        () => json(200, { requests: [confirmed], schema_version: 1 }),
      ],
      "GET /api/stories": [() => json(200, stories)],
      [`POST /api/data-requests/${confirmed.request_id}/receipt-credential`]: [
        () =>
          json(200, {
            request: confirmed,
            receipt_credential: "fresh-receipt-code",
            schema_version: 1,
          }),
      ],
    });
    render(<DataRequestsPanel local={false} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Lost your receipt code?" }),
    );
    fireEvent.change(screen.getByLabelText("Password for a new receipt code"), {
      target: { value: "pw-123456789012" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Issue new code" }));
    expect(await screen.findByText("fresh-receipt-code")).toBeInTheDocument();
    const call = calls.find((c) => c.url.endsWith("/receipt-credential"))!;
    expect(JSON.parse(call.body!)).toEqual({ password: "pw-123456789012" });
    expect(localStorage.length).toBe(0);
  });
});

describe("ReceiptLookup", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("reads a closed account's request and receipt by its code, then forgets the code", async () => {
    const done = request({
      kind: "deletion",
      scope: "account",
      story_ids: [],
      state: "completed",
      phases: [
        {
          phase_code: "identity",
          outcome_code: "succeeded",
        } as DataRequest["phases"][number],
      ],
      receipts: [
        {
          receipt_id: "33333333-3333-3333-3333-333333333333",
          receipt_kind: "deletion",
          attempt_id: "44444444-4444-4444-4444-444444444444",
          created_at: "2026-10-19T00:00:00Z",
          body: { stories_deleted: 2, classes: ["turns", "story_bible"] },
          schema_version: 1,
        },
      ],
    });
    const calls = stubFetch({
      "POST /api/data-requests/receipt": [
        () =>
          json(403, {
            error_code: "forbidden",
            message: "That receipt code does not match.",
            detail: null,
            schema_version: 1,
          }),
        () => json(200, done),
      ],
    });
    render(<ReceiptLookup />);
    const check = screen.getByRole("button", { name: "Check request" });
    expect(check).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Request ID"), {
      target: { value: done.request_id },
    });
    fireEvent.change(screen.getByLabelText("Receipt code"), {
      target: { value: "wrong" },
    });
    fireEvent.click(check);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "does not match",
    );
    expect(screen.getByLabelText("Receipt code")).toHaveValue("");
    fireEvent.change(screen.getByLabelText("Receipt code"), {
      target: { value: "right-code" },
    });
    fireEvent.click(check);
    const region = await screen.findByRole("region", {
      name: "Request status",
    });
    expect(region).toHaveTextContent(
      "Deletion of the whole account: Completed",
    );
    expect(region).toHaveTextContent("identity: done");
    expect(region).toHaveTextContent('"stories_deleted": 2');
    expect(JSON.parse(calls[1]!.body!)).toEqual({
      request_id: done.request_id,
      credential: "right-code",
    });
    await waitFor(() =>
      expect(screen.getByLabelText("Receipt code")).toHaveValue(""),
    );
  });
});
