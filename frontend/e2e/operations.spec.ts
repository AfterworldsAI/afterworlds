import { readFileSync } from "node:fs";

import {
  expect,
  test,
  type APIRequestContext,
  type Browser,
  type Page,
} from "@playwright/test";

/**
 * CRD Issue 22: the BUILT app as a remote deployment
 * (scripts/e2e_remote_server.py, its own disposable stores, fake provider).
 * Two ordinary accounts and the Owner administrator, each in its own browser
 * context. The Owner is provisioned only by the real bootstrap command and
 * works in the separate staff console (#staff). Exercises staff lookup and
 * ordered history, a previewed and confirmed credit adjustment, Story export
 * and download, confirmed Story deletion, account-wide export and deletion
 * with the minimized-retention receipt, closed-account receipt access and
 * status recovery after reload.
 */

const PASSWORD = "correct horse battery staple"; // pragma: allowlist secret
const OWNER = "owner@ops.example.test";
const A = "a@ops.example.test";
const B = "b@ops.example.test";

test.describe.configure({ mode: "serial" });

async function code(request: APIRequestContext, address: string, kind: string) {
  const resp = await request.get(
    `/__e2e__/outbox?address=${encodeURIComponent(address)}&kind=${kind}`,
  );
  return ((await resp.json()) as { code: string }).code;
}

async function enroll(page: Page, address: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("Email address").fill(address);
  await page.getByRole("button", { name: "Send code" }).click();
  await expect(page.getByText(/If this address can receive one/)).toBeVisible();
  await page
    .getByLabel("Code")
    .fill(await code(page.request, address, "enrollment"));
  await page.getByLabel("New password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText(/Account created/)).toBeVisible();
  await page.getByLabel("Email address").fill(address);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Your stories")).toBeVisible();
}

type Reply = { status: number; body: Record<string, unknown> };

async function call(
  page: Page,
  method: string,
  path: string,
  data?: unknown,
): Promise<Reply> {
  return page.evaluate(
    async ({ method, path, data }) => {
      const res = await fetch(path, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-Afterworlds-Request": "1",
        },
        body: data === undefined ? undefined : JSON.stringify(data),
      });
      return { status: res.status, body: await res.json() };
    },
    { method, path, data },
  );
}

async function playStory(page: Page, title: string): Promise<string> {
  const created = await call(page, "POST", "/api/stories", {
    title,
    mode: "branching",
  });
  const sid = String(created.body.story_id);
  await call(page, "POST", `/api/stories/${sid}/setup`, {
    mode: "branching",
    interaction_style: "freeform_only",
    branching_cadence: "balanced",
  });
  expect((await call(page, "POST", `/api/stories/${sid}/begin`)).status).toBe(
    200,
  );
  const turn = await call(page, "POST", `/api/stories/${sid}/turns`, {
    user_input: `I explore ${title}.`,
  });
  expect(turn.status).toBe(200);
  return sid;
}

async function fresh(browser: Browser): Promise<Page> {
  return (await browser.newContext({ acceptDownloads: true })).newPage();
}

async function openData(page: Page) {
  await page.getByRole("button", { name: "Your data" }).click();
  await expect(page.getByRole("heading", { name: "Your data" })).toBeVisible();
}

async function staffQueueStep(staff: Page, label: string, button: string) {
  await staff.reload();
  const row = staff
    .getByRole("list", { name: "Data request queue" })
    .getByRole("listitem")
    .filter({ hasText: label });
  // Wait for the server's recorded outcome, not just the click.
  const [response] = await Promise.all([
    staff.waitForResponse(
      (r) =>
        r.request().method() === "POST" &&
        new URL(r.url()).pathname.startsWith("/api/admin/data-requests/"),
      { timeout: 60_000 },
    ),
    row.first().getByRole("button", { name: button }).click(),
  ]);
  expect(response.status()).toBe(200);
  return (await response.json()) as Record<string, unknown>;
}

let ownerStaff: Page;
let a: Page;
let b: Page;
let aId: string;
let aStory: string;

test("the Owner administrator works in a separate staff session", async ({
  browser,
}) => {
  const owner = await fresh(browser);
  a = await fresh(browser);
  b = await fresh(browser);
  await enroll(owner, OWNER);
  await enroll(a, A);
  await enroll(b, B);
  aId = String((await call(a, "GET", "/api/auth/session")).body.account_id);
  expect((await a.request.post(`/__e2e__/entitlement/${aId}`)).ok()).toBe(true);
  aStory = await playStory(a, "Garden");
  await playStory(a, "Harbor");

  // The ordinary sessions, the Owner's included, have no staff authority.
  expect((await call(owner, "GET", `/api/admin/accounts/${aId}`)).status).toBe(
    403,
  );
  expect((await call(a, "GET", "/api/admin/data-requests")).status).toBe(403);
  const boot = await owner.request.post("/__e2e__/bootstrap", {
    data: { contact_address: OWNER, password: PASSWORD },
  });
  expect(((await boot.json()) as { exit_code: number }).exit_code).toBe(0);

  ownerStaff = await fresh(browser);
  await ownerStaff.goto("/#staff");
  await ownerStaff.getByLabel("Staff email").fill(OWNER);
  await ownerStaff.getByLabel("Staff password").fill(PASSWORD);
  await ownerStaff.getByRole("button", { name: "Sign in to staff" }).click();
  await ownerStaff.getByLabel("Account ID").fill(aId);
  await ownerStaff.getByRole("button", { name: "Look up" }).click();
  await expect(ownerStaff.getByText(/plan subscription/)).toBeVisible();
  await expect(
    ownerStaff.getByText(/not visible to the remote service/),
  ).toBeVisible();
  await expect(ownerStaff.getByText(/Replay check: consistent/)).toBeVisible();
  await expect(
    ownerStaff.getByRole("list", { name: "Entitlement history" }),
  ).toContainText("subscription_credit_grant");
  // The staff session is not an ordinary session.
  expect((await call(ownerStaff, "GET", "/api/stories")).status).toBe(401);
});

test("a previewed, reasoned credit adjustment is applied once and confirmed", async () => {
  await ownerStaff.getByLabel("Included credits delta").fill("2.5");
  await ownerStaff.getByLabel("Reason").fill("Goodwill after an outage");
  await ownerStaff.getByRole("button", { name: "Preview adjustment" }).click();
  const preview = ownerStaff.getByRole("region", {
    name: "Adjustment preview",
  });
  await expect(preview).toContainText("deltas 2.5000");
  await ownerStaff.getByRole("button", { name: "Confirm adjustment" }).click();
  await expect(ownerStaff.getByRole("status")).toContainText(
    "Applied: entitlement event",
  );
  await expect(
    ownerStaff.getByRole("list", { name: "Entitlement history" }),
  ).toContainText("Goodwill after an outage");
});

test("Story export: requested, approved, executed and downloaded by its owner", async () => {
  await a.reload();
  await openData(a);
  await a.getByLabel("Story").selectOption(aStory);
  await a.getByRole("button", { name: "Export Story" }).click();
  await expect(
    a.getByText(/Export of “Garden”: Waiting for review/),
  ).toBeVisible();

  await staffQueueStep(ownerStaff, "export / story", "Approve");
  await staffQueueStep(ownerStaff, "export / story", "Execute");

  await a.reload();
  await openData(a);
  await expect(a.getByText(/Export of “Garden”: Completed/)).toBeVisible();
  const [download] = await Promise.all([
    a.waitForEvent("download"),
    a.getByRole("link", { name: /Download export/ }).click(),
  ]);
  const zip = readFileSync((await download.path())!);
  expect(zip.subarray(0, 2).toString()).toBe("PK");
  expect(zip.includes("manifest.json")).toBe(true);
  // Another account cannot fetch it.
  const listed = await call(a, "GET", "/api/data-requests");
  const id = (listed.body.requests as { request_id: string }[])[0]!.request_id;
  expect(
    (await call(b, "GET", `/api/data-requests/${id}/artifact`)).status,
  ).toBe(404);
});

test("confirmed Story deletion removes it and reports pending physical cleanup", async () => {
  await a.getByLabel("Story").selectOption(aStory);
  await a.getByRole("button", { name: "Delete Story…" }).click();
  const dialog = a.getByRole("dialog");
  await expect(dialog).toContainText("There is no undo");
  await expect(
    dialog.getByRole("list", { name: "Kept records" }),
  ).toContainText("deletion_suppression");
  await dialog.getByRole("button", { name: "Confirm deletion" }).click();
  await expect(
    a.getByText(/Deletion of “Garden”: Waiting for review/),
  ).toBeVisible();

  await staffQueueStep(ownerStaff, "deletion / story", "Approve");
  await staffQueueStep(ownerStaff, "deletion / story", "Execute");

  await a.reload();
  await openData(a);
  await expect(a.getByText(/physical compaction pending/)).toBeVisible();
  expect((await call(a, "GET", `/api/stories/${aStory}`)).status).toBe(404);
  const left = await call(a, "GET", "/api/stories");
  expect(
    (left.body.stories as { title: string }[]).map((s) => s.title),
  ).toEqual(["Harbor"]);
});

test("account-wide export then deletion, with a receipt after closure", async () => {
  const bId = String(
    (await call(b, "GET", "/api/auth/session")).body.account_id,
  );
  expect((await b.request.post(`/__e2e__/entitlement/${bId}`)).ok()).toBe(true);
  await playStory(b, "Lonely");
  await b.reload();
  await openData(b);
  await b.getByRole("button", { name: "Export my account" }).click();
  await staffQueueStep(ownerStaff, "export / account", "Approve");
  await staffQueueStep(ownerStaff, "export / account", "Execute");
  await b.reload();
  await openData(b);
  await expect(b.getByRole("link", { name: /Download export/ })).toBeVisible();

  await b.getByRole("button", { name: "Delete my account…" }).click();
  const dialog = b.getByRole("dialog");
  await expect(dialog).toContainText("Export first");
  // B's live hosted subscription needs CRD Issue 23's closure contract.
  await expect(dialog).toContainText("stay incomplete");
  await dialog.getByLabel("Password").fill(PASSWORD);
  await dialog.getByRole("button", { name: "Confirm deletion" }).click();
  const receipt = b.getByRole("status");
  await expect(receipt).toContainText("receipt code");
  const codes = await receipt.locator("code").allTextContents();
  const [requestId, credential] = [codes[0]!, codes[1]!];

  await staffQueueStep(ownerStaff, "deletion / account", "Approve");
  await staffQueueStep(ownerStaff, "deletion / account", "Execute");

  // B's sessions were revoked: the app returns to sign-in.
  await b.reload();
  await expect(b.getByRole("heading", { name: "Sign in" })).toBeVisible();
  const status = await call(b, "POST", "/api/data-requests/receipt", {
    request_id: requestId,
    credential,
  });
  expect(status.status).toBe(200);
  expect(status.body.state).toBe("in_progress");
  const phases = status.body.phases as {
    phase_code: string;
    outcome_code: string;
  }[];
  const outcome = Object.fromEntries(
    phases.map((p) => [p.phase_code, p.outcome_code]),
  );
  expect(outcome.identity).toBe("succeeded");
  expect(outcome.sql_content).toBe("succeeded");
  expect(outcome.physical_compaction).toBe("pending");
  expect(outcome.commercial).toBe("dependency_unavailable");
  expect(
    (
      await call(b, "POST", "/api/data-requests/receipt", {
        request_id: requestId,
        credential: "not-the-code",
      })
    ).status,
  ).toBe(404);
  // A's account and remaining Story are unaffected.
  expect((await call(a, "GET", "/api/stories")).status).toBe(200);
});

test("anomaly view reports its sources and the blocked dependency honestly", async () => {
  await ownerStaff.reload();
  await expect(
    ownerStaff.getByText(/commercial_events not_integrated/),
  ).toBeVisible();
});
