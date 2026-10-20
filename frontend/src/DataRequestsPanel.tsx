import { useCallback, useEffect, useState } from "react";

import {
  api,
  ApiRequestError,
  dataRequests,
  type DataRequest,
  type DeletionPreview,
  type StoryListItem,
} from "./api/client";

/**
 * CRD Issue 22: your Story and account-wide export/deletion requests.
 *
 * Presentation only -- the server decides who owns what, records every
 * step and reports the authoritative state. Nothing here marks a request
 * done: it shows the last state read and re-reads after every action and on
 * reload. The account-deletion password lives only in a transient input; the
 * one-time receipt credential is shown once and never stored by the app.
 */

const STATE_TEXT: Record<DataRequest["state"], string> = {
  requested: "Waiting for your confirmation",
  awaiting_authorization: "Waiting for review",
  approved: "Approved, not started",
  in_progress: "In progress",
  completed: "Completed",
  failed: "Failed (it can be retried)",
  rejected: "Rejected",
};

const PHASE_TEXT: Record<string, string> = {
  succeeded: "done",
  pending: "pending",
  failed: "failed",
  unverified: "not verified",
  not_applicable: "not applicable",
  dependency_unavailable: "blocked: a required service is not available yet",
  owner_controlled: "on your own device",
};

function when(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString() : "—";
}

function describe(request: DataRequest, stories: StoryListItem[]): string {
  const what = request.kind === "export" ? "Export" : "Deletion";
  if (request.scope === "account")
    return `${what} of ${request.environment === "local" ? "all local data" : "your whole account"}`;
  const title =
    stories.find((s) => s.story_id === request.story_ids[0])?.title ??
    "a Story";
  return `${what} of “${title}”`;
}

function errorText(err: unknown): string {
  if (err instanceof ApiRequestError) return err.apiError.message;
  return "The request could not be completed. Reload to see its current state.";
}

export default function DataRequestsPanel({ local }: { local: boolean }) {
  const [requests, setRequests] = useState<DataRequest[] | null>(null);
  const [stories, setStories] = useState<StoryListItem[]>([]);
  const [storyId, setStoryId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{
    request: DataRequest;
    preview: DeletionPreview;
  } | null>(null);
  const [password, setPassword] = useState("");
  const [credential, setCredential] = useState<{
    requestId: string;
    value: string;
  } | null>(null);

  const reload = useCallback(() => {
    dataRequests
      .list()
      .then(setRequests)
      .catch((err) => setError(errorText(err)));
    api
      .listStories()
      .then(setStories)
      .catch(() => setStories([]));
  }, []);

  useEffect(reload, [reload]);

  async function act(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
      reload();
    }
  }

  function create(
    kind: DataRequest["kind"],
    scope: DataRequest["scope"],
    story: string | null,
  ) {
    void act(async () => {
      const created = await dataRequests.create(kind, scope, story);
      if (kind === "deletion") await openPreview(created);
    });
  }

  async function openPreview(request: DataRequest) {
    setPreview({
      request,
      preview: await dataRequests.preview(request.request_id),
    });
  }

  function confirm() {
    if (!preview) return;
    const needsPassword =
      preview.request.scope === "account" &&
      preview.request.environment === "remote";
    void act(async () => {
      try {
        const result = await dataRequests.confirm(
          preview.request.request_id,
          preview.request.revision,
          preview.preview.scope_revision,
          needsPassword ? password : null,
        );
        if (result.receipt_credential)
          setCredential({
            requestId: result.request.request_id,
            value: result.receipt_credential,
          });
        setPreview(null);
      } finally {
        setPassword("");
      }
    });
  }

  return (
    <section aria-labelledby="your-data-heading">
      <h2 id="your-data-heading">Your data</h2>
      <p>
        Export or delete one Story or{" "}
        {local ? "all data on this device" : "your whole account"}. Owned
        content can always be exported, whatever your credits or Cloud Services
        status.
        {local
          ? " Local requests need no account and never leave this device."
          : " Requests are reviewed and run by the Afterworlds administrator."}
      </p>
      {error && <p role="alert">{error}</p>}
      {credential && (
        <div role="status">
          <p>
            Keep this receipt code. After your account is closed, it is the only
            way to read this request&apos;s status and final receipt. It is
            shown once.
          </p>
          <p>
            Request <code>{credential.requestId}</code>, receipt code{" "}
            <code>{credential.value}</code>
          </p>
          <button type="button" onClick={() => setCredential(null)}>
            I have saved it
          </button>
        </div>
      )}
      <div>
        <label>
          Story{" "}
          <select
            aria-label="Story"
            value={storyId}
            onChange={(e) => setStoryId(e.target.value)}
          >
            <option value="">Choose a Story</option>
            {stories.map((s) => (
              <option key={s.story_id} value={s.story_id}>
                {s.title}
              </option>
            ))}
          </select>
        </label>{" "}
        <button
          type="button"
          disabled={busy || !storyId}
          onClick={() => create("export", "story", storyId)}
        >
          Export Story
        </button>{" "}
        <button
          type="button"
          disabled={busy || !storyId}
          onClick={() => create("deletion", "story", storyId)}
        >
          Delete Story…
        </button>
      </div>
      <div>
        <button
          type="button"
          disabled={busy}
          onClick={() => create("export", "account", null)}
        >
          {local ? "Export all local data" : "Export my account"}
        </button>{" "}
        <button
          type="button"
          disabled={busy}
          onClick={() => create("deletion", "account", null)}
        >
          {local ? "Delete all local data…" : "Delete my account…"}
        </button>
      </div>

      {preview && (
        <div role="dialog" aria-labelledby="deletion-preview-heading">
          <h3 id="deletion-preview-heading">Confirm deletion</h3>
          <p>
            {preview.preview.counts.stories} Story(ies),{" "}
            {preview.preview.counts.turns} turn(s). Live data is removed within{" "}
            {preview.preview.live_deletion_limit_days} days of confirmation
            {preview.preview.final_deletion_limit_days
              ? `; backups containing it are gone within ${preview.preview.final_deletion_limit_days} days`
              : ""}
            . There is no undo.
          </p>
          {preview.request.scope === "account" && !local && (
            <p>
              Export first if you want a copy: once your account is closed you
              can no longer sign in.
            </p>
          )}
          {preview.preview.commercial_dependency ===
            "dependency_unavailable" && (
            <p>
              Your hosted subscription must be closed by a service that is not
              available yet, so this request will stay incomplete until it is.
            </p>
          )}
          <p>Removed: {preview.preview.removed_classes.join(", ")}</p>
          <ul aria-label="Kept records">
            {preview.preview.retained_categories.map((c) => (
              <li key={c.code}>
                <strong>{c.code}</strong>: {c.purpose} Kept: {c.end_condition}
              </li>
            ))}
          </ul>
          <ul>
            {preview.preview.notices.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
          {preview.request.scope === "account" && !local && (
            <label>
              Password{" "}
              <input
                type="password"
                aria-label="Password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          )}
          <button type="button" disabled={busy} onClick={confirm}>
            Confirm deletion
          </button>{" "}
          <button type="button" onClick={() => setPreview(null)}>
            Not now
          </button>
        </div>
      )}

      {requests === null ? (
        <p>Loading requests…</p>
      ) : requests.length === 0 ? (
        <p>No requests yet.</p>
      ) : (
        <ul aria-label="Your requests">
          {requests.map((r) => (
            <li key={r.request_id}>
              <strong>{describe(r, stories)}</strong>: {STATE_TEXT[r.state]}
              {r.progress_code && (
                <> ({r.progress_code.replaceAll("_", " ")})</>
              )}
              {r.overdue.length > 0 && (
                <span role="alert"> Overdue: {r.overdue.join(", ")}</span>
              )}
              <div>
                Requested {when(r.requested_at)}
                {r.confirmed_at && <> · confirmed {when(r.confirmed_at)}</>}
                {r.export_deadline_at && (
                  <> · due {when(r.export_deadline_at)}</>
                )}
                {r.live_deadline_at && (
                  <> · live data by {when(r.live_deadline_at)}</>
                )}
                {r.backup_deadline_at && (
                  <> · backups by {when(r.backup_deadline_at)}</>
                )}
              </div>
              {r.phases.length > 0 && (
                <ul aria-label="Progress">
                  {r.phases.map((p) => (
                    <li key={p.phase_code}>
                      {p.phase_code.replaceAll("_", " ")}:{" "}
                      {PHASE_TEXT[p.outcome_code] ?? p.outcome_code}
                    </li>
                  ))}
                </ul>
              )}
              {r.state === "requested" && r.kind === "deletion" && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void act(() => openPreview(r))}
                >
                  Review and confirm
                </button>
              )}
              {local &&
                ["awaiting_authorization", "approved", "failed"].includes(
                  r.state,
                ) && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void act(() =>
                        dataRequests.executeLocal(r.request_id, r.revision),
                      )
                    }
                  >
                    {r.state === "failed" ? "Retry now" : "Run now"}
                  </button>
                )}
              {r.artifact?.status === "available" && (
                <a href={dataRequests.artifactUrl(r.request_id)} download>
                  Download export (available until {when(r.artifact.expires_at)}
                  )
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
