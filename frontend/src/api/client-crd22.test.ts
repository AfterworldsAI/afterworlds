import { afterEach, describe, expect, it, vi } from "vitest";

import { dataRequests, setSignedOutListener, staffApi } from "./client";

type Call = {
  url: string;
  method: string;
  body: unknown;
  header: string | null;
};

function stub(status = 200, body: unknown = {}) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      calls.push({
        url,
        method: init?.method ?? "GET",
        body: init?.body ? JSON.parse(init.body as string) : undefined,
        header: headers.get("X-Afterworlds-Request"),
      });
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  setSignedOutListener(null);
});

describe("CRD Issue 22 client contract", () => {
  it("binds requester calls to the documented paths and bodies", async () => {
    const calls = stub(200, { requests: [] });
    await dataRequests.list();
    await dataRequests.get("r1");
    await dataRequests.create("export", "account");
    await dataRequests.preview("r1");
    await dataRequests.confirm("r1", 2, "rev", null);
    await dataRequests.executeLocal("r1", 3);
    await dataRequests.receipt("r1", "code");
    expect(dataRequests.artifactUrl("r1")).toBe(
      "/api/data-requests/r1/artifact",
    );
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      "GET /api/data-requests",
      "GET /api/data-requests/r1",
      "POST /api/data-requests",
      "GET /api/data-requests/r1/deletion-preview",
      "POST /api/data-requests/r1/confirm",
      "POST /api/data-requests/r1/execute",
      "POST /api/data-requests/receipt",
    ]);
    expect(calls[2]!.body).toEqual({
      kind: "export",
      scope: "account",
      story_id: null,
    });
    expect(calls[6]!.body).toEqual({ request_id: "r1", credential: "code" });
    expect(calls.every((c) => c.header === "1")).toBe(true);
  });

  it("binds every staff call and never ends the ordinary session on a staff 401", async () => {
    const signedOut = vi.fn();
    setSignedOutListener(signedOut);
    const calls = stub(200, { requests: [] });
    await staffApi.signOut();
    await staffApi.supportActions("a1");
    await staffApi.operationStatus("o1");
    await staffApi.dataRequests();
    await staffApi.reject("r1", 2, "duplicate", "Already handled.");
    await staffApi.execute("r1", 3);
    await staffApi.finalize("r1");
    await staffApi.noteAnomaly(
      "turn_settlement:t/1",
      "closed",
      "resolved",
      null,
    );
    await staffApi.retentionSweep();
    expect(calls.map((c) => `${c.method} ${c.url}`)).toEqual([
      "DELETE /api/admin/session",
      "GET /api/admin/accounts/a1/support-actions",
      "GET /api/admin/support-operations/o1",
      "GET /api/admin/data-requests",
      "POST /api/admin/data-requests/r1/reject",
      "POST /api/admin/data-requests/r1/execute",
      "POST /api/admin/data-requests/r1/finalize",
      "POST /api/admin/anomalies/turn_settlement%3At%2F1/notes",
      "POST /api/admin/maintenance/retention-sweep",
    ]);
    expect(calls[4]!.body).toEqual({
      expected_revision: 2,
      reason_code: "duplicate",
      reason: "Already handled.",
    });

    stub(401, {
      error_code: "authentication_required",
      message: "Authentication required.",
      detail: null,
      schema_version: 1,
    });
    await expect(staffApi.anomalies()).rejects.toThrow(
      "Authentication required.",
    );
    expect(signedOut).not.toHaveBeenCalled();
    await expect(dataRequests.list()).rejects.toThrow();
    expect(signedOut).toHaveBeenCalledTimes(1);
  });
});
