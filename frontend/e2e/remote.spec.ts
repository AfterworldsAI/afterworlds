import {
  expect,
  test,
  type APIRequestContext,
  type Browser,
  type Page,
} from "@playwright/test";

/**
 * Prerequisite #205: the BUILT app as a remote deployment, served by
 * scripts/e2e_remote_server.py on disposable stores with the fake provider.
 * Two ordinary accounts and the Owner each use their own browser context
 * (own cookie jar). Codes come from the server's notice outbox, standing in
 * for the user's mailbox; the Owner administrator is provisioned only by the
 * real server-side bootstrap command.
 */

const PASSWORD = "correct horse battery staple"; // pragma: allowlist secret
const NEW_PASSWORD = "a recovered replacement phrase"; // pragma: allowlist secret
const OWNER = "owner@example.test";
const B = "b@example.test";

test.describe.configure({ mode: "serial" });

async function code(
  request: APIRequestContext,
  address: string,
  kind: string,
): Promise<string> {
  const resp = await request.get(
    `/__e2e__/outbox?address=${encodeURIComponent(address)}&kind=${kind}`,
  );
  const body = (await resp.json()) as { code: string };
  expect(body.code).not.toBe("");
  return body.code;
}

async function enrollAndSignIn(page: Page, address: string, password: string) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("Email address").fill(address);
  await page.getByRole("button", { name: "Send code" }).click();
  await expect(page.getByText(/If this address can receive one/)).toBeVisible();
  await page
    .getByLabel("Code")
    .fill(await code(page.request, address, "enrollment"));
  await page.getByLabel("New password").fill(password);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText(/Account created/)).toBeVisible();
  await signIn(page, address, password);
}

async function signIn(page: Page, address: string, password: string) {
  await page.getByLabel("Email address").fill(address);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Your stories")).toBeVisible();
}

async function accountId(page: Page): Promise<string> {
  const status = await call(page, "GET", "/api/auth/session");
  return String(status.body.account_id);
}

async function freshPage(browser: Browser): Promise<Page> {
  return (await browser.newContext()).newPage();
}

type Reply = { status: number; body: Record<string, unknown> };

/** An API call from inside the page, with the browser's own cookies. */
async function call(
  page: Page,
  method: string,
  path: string,
  data?: unknown,
  clientHeader = true,
): Promise<Reply> {
  return page.evaluate(
    async ({ method, path, data, clientHeader }) => {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (clientHeader) headers["X-Afterworlds-Request"] = "1";
      const res = await fetch(path, {
        method,
        headers,
        body: data === undefined ? undefined : JSON.stringify(data),
      });
      return { status: res.status, body: await res.json() };
    },
    { method, path, data, clientHeader },
  );
}

let ownerPage: Page;
let bPage: Page;
let ownerStory: string;

test("unauthenticated visitors see only sign-in; the API denies them", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  const resp = await call(page, "GET", "/api/stories");
  expect(resp.status).toBe(401);
  expect(resp.body.error_code).toBe("authentication_required");
});

test("two accounts enroll, sign in and stay isolated", async ({ browser }) => {
  ownerPage = await freshPage(browser);
  bPage = await freshPage(browser);
  await enrollAndSignIn(ownerPage, OWNER, PASSWORD);
  await enrollAndSignIn(bPage, B, PASSWORD);

  // The Owner creates a story in the UI and plays a fake-provider turn.
  const seeded = await ownerPage.request.post(
    `/__e2e__/entitlement/${await accountId(ownerPage)}`,
  );
  expect(seeded.ok()).toBe(true);
  await ownerPage.getByPlaceholder("Title").fill("Owner's tale");
  await ownerPage.getByRole("button", { name: "Create" }).click();
  const list = await call(ownerPage, "GET", "/api/stories");
  const stories = list.body.stories as { story_id: string }[];
  expect(stories).toHaveLength(1);
  ownerStory = stories[0]!.story_id;
  const setup = await call(
    ownerPage,
    "POST",
    `/api/stories/${ownerStory}/setup`,
    {
      mode: "branching",
      interaction_style: "freeform_only",
      branching_cadence: "balanced",
    },
  );
  expect(setup.status).toBe(200);
  const begin = await call(
    ownerPage,
    "POST",
    `/api/stories/${ownerStory}/begin`,
  );
  expect(begin.status).toBe(200);
  const turn = await call(
    ownerPage,
    "POST",
    `/api/stories/${ownerStory}/turns`,
    {
      user_input: "I open the door.",
    },
  );
  expect(turn.status).toBe(200);

  // B sees nothing of it, by list or by known ID, and cannot change it.
  await bPage.reload();
  await expect(bPage.getByText("Your stories")).toBeVisible();
  await expect(bPage.getByText("Owner's tale")).toHaveCount(0);
  for (const path of [
    `/api/stories/${ownerStory}`,
    `/api/stories/${ownerStory}/turns`,
    `/api/stories/${ownerStory}/visible-state`,
    `/api/stories/${ownerStory}/setup`,
  ]) {
    expect((await call(bPage, "GET", path)).status).toBe(404);
  }
  const steal = await call(bPage, "POST", `/api/stories/${ownerStory}/turns`, {
    user_input: "I take over.",
  });
  expect(steal.status).toBe(404);
  // Without the client header a state-changing request is refused outright.
  const forged = await call(
    bPage,
    "POST",
    "/api/stories",
    { title: "forged", mode: "branching" },
    false,
  );
  expect(forged.status).toBe(403);
  const own = await call(ownerPage, "GET", `/api/stories/${ownerStory}/turns`);
  expect((own.body.turns as unknown[]).length).toBeGreaterThan(0);
});

test("staff authority needs the bootstrap and a separate staff session", async ({
  browser,
}) => {
  const bId = await accountId(bPage);
  // The Owner's ordinary session never carries staff authority.
  const ordinary = await call(ownerPage, "GET", `/api/admin/accounts/${bId}`);
  expect(ordinary.status).toBe(403);
  expect(ordinary.body.error_code).toBe("staff_authority_required");

  const boot = await ownerPage.request.post("/__e2e__/bootstrap", {
    data: { contact_address: OWNER, password: PASSWORD },
  });
  expect(await boot.json()).toMatchObject({ exit_code: 0 });
  const second = await ownerPage.request.post("/__e2e__/bootstrap", {
    data: { contact_address: B, password: PASSWORD },
  });
  expect(await second.json()).toMatchObject({ exit_code: 1 });
  // Still no staff authority on the ordinary session after provisioning.
  expect(
    (await call(ownerPage, "GET", `/api/admin/accounts/${bId}`)).status,
  ).toBe(403);

  const staff = await freshPage(browser);
  await staff.goto("/");
  const signInStaff = await call(staff, "POST", "/api/admin/session", {
    contact_address: OWNER,
    password: PASSWORD,
  });
  expect(signInStaff.status).toBe(200);
  const view = await call(staff, "GET", `/api/admin/accounts/${bId}`);
  expect(view.status).toBe(200);
  expect(view.body).toMatchObject({
    account_id: bId,
    status: "active",
    owned_story_count: 0,
    byok_readiness_source: "unavailable_remotely",
  });
  // A staff session is not an ordinary session.
  expect((await call(staff, "GET", "/api/stories")).status).toBe(401);

  const revoke = await call(
    staff,
    "POST",
    `/api/admin/accounts/${bId}/sessions/revoke`,
    {
      reason: "e2e targeted revocation",
    },
  );
  expect(revoke.body).toMatchObject({ revoked_sessions: 1 });
  await bPage.reload();
  await expect(bPage.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("recovery restores access without staff authority", async () => {
  await bPage.getByRole("button", { name: "Forgot password" }).click();
  await bPage.getByLabel("Email address").fill(B);
  await bPage.getByRole("button", { name: "Send code" }).click();
  await expect(
    bPage.getByText(/If this address can receive one/),
  ).toBeVisible();
  await bPage.getByLabel("Code").fill(await code(bPage.request, B, "recovery"));
  await bPage.getByLabel("New password").fill(NEW_PASSWORD);
  await bPage.getByRole("button", { name: "Set new password" }).click();
  await expect(bPage.getByText(/every session signed out/)).toBeVisible();
  await signIn(bPage, B, NEW_PASSWORD);
  expect((await call(bPage, "GET", `/api/stories/${ownerStory}`)).status).toBe(
    404,
  );
  const staff = await call(bPage, "POST", "/api/admin/session", {
    contact_address: B,
    password: NEW_PASSWORD,
  });
  expect(staff.status).toBe(403);
});

test("sign-out revokes the session and forgets local story state", async () => {
  // Creating the story opened it, so the browser remembers it.
  await ownerPage.reload();
  expect(
    await ownerPage.evaluate(() =>
      localStorage.getItem("afterworlds:last-story-id"),
    ),
  ).toBe(ownerStory);
  await ownerPage.getByRole("button", { name: "Sign out" }).click();
  await expect(
    ownerPage.getByRole("heading", { name: "Sign in" }),
  ).toBeVisible();
  expect(
    await ownerPage.evaluate(() =>
      localStorage.getItem("afterworlds:last-story-id"),
    ),
  ).toBeNull();
  expect((await call(ownerPage, "GET", "/api/stories")).status).toBe(401);
});
