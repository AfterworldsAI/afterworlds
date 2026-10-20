import { useCallback, useEffect, useState } from "react";

import {
  ApiRequestError,
  staffApi,
  type AdjustmentPreview,
  type AdminAccountView,
  type Anomaly,
  type AnomalyReport,
  type DataRequest,
  type EntitlementHistory,
  type SupportOperation,
} from "./api/client";

/**
 * CRD Issue 22: the Owner administrator's support console.
 *
 * A separate staff session (its own sign-in and cookie); every action is
 * decided and recorded by the server against that session, never by this
 * page. Balances are shown verbatim. A credit adjustment is previewed, needs
 * a reason and explicit confirmation, keeps one operation ID for the logical
 * action, and is never retried automatically: an uncertain result offers a
 * status read under the same ID. Nothing privileged is persisted here.
 */

type Outcome =
  | { kind: "confirmed"; operation: SupportOperation }
  | { kind: "rejected"; message: string }
  | { kind: "uncertain"; message: string };

function message(err: unknown): string {
  if (err instanceof ApiRequestError) return err.apiError.message;
  return "No response was received.";
}

function newOperationId(): string {
  return crypto.randomUUID();
}

function StaffSignIn({ onSignedIn }: { onSignedIn: () => void }) {
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        setError(null);
        staffApi
          .signIn(address, password)
          .then(onSignedIn)
          .catch((err) => setError(message(err)))
          .finally(() => setPassword(""));
      }}
    >
      <h2>Staff sign-in</h2>
      {error && <p role="alert">{error}</p>}
      <label>
        Staff email{" "}
        <input
          aria-label="Staff email"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
      </label>
      <label>
        Staff password{" "}
        <input
          aria-label="Staff password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <button type="submit">Sign in to staff</button>
    </form>
  );
}

function Adjustment({
  account,
  onDone,
}: {
  account: AdminAccountView;
  onDone: () => void;
}) {
  const [hosted, setHosted] = useState("");
  const [topUp, setTopUp] = useState("");
  const [reason, setReason] = useState("");
  const [preview, setPreview] = useState<AdjustmentPreview | null>(null);
  const [operationId, setOperationId] = useState(newOperationId);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setPreview(null);
    setOperationId(newOperationId());
  }

  async function submit() {
    if (!preview) return;
    setBusy(true);
    try {
      const operation = await staffApi.adjust(
        account.account_id,
        operationId,
        hosted || null,
        topUp || null,
        reason,
        preview.last_entitlement_event_id,
      );
      setOutcome({ kind: "confirmed", operation });
      onDone();
      reset();
    } catch (err) {
      if (err instanceof ApiRequestError && err.status < 500)
        setOutcome({ kind: "rejected", message: message(err) });
      else setOutcome({ kind: "uncertain", message: message(err) });
    } finally {
      setBusy(false);
    }
  }

  async function checkStatus() {
    setBusy(true);
    try {
      const operation = await staffApi.operationStatus(operationId);
      if (operation.outcome_code === "committed") {
        setOutcome({ kind: "confirmed", operation });
        onDone();
        reset();
      } else
        setOutcome({
          kind: "uncertain",
          message: `Recorded outcome: ${operation.outcome_code}.`,
        });
    } catch (err) {
      setOutcome({ kind: "uncertain", message: message(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h3>Credit adjustment</h3>
      <label>
        Included credits delta{" "}
        <input
          aria-label="Included credits delta"
          value={hosted}
          onChange={(e) => {
            setHosted(e.target.value);
            reset();
          }}
        />
      </label>
      <label>
        Top-up credits delta{" "}
        <input
          aria-label="Top-up credits delta"
          value={topUp}
          onChange={(e) => {
            setTopUp(e.target.value);
            reset();
          }}
        />
      </label>
      <label>
        Reason{" "}
        <input
          aria-label="Reason"
          value={reason}
          maxLength={280}
          onChange={(e) => {
            setReason(e.target.value);
            reset();
          }}
        />
      </label>
      {error && <p role="alert">{error}</p>}
      <button
        type="button"
        disabled={busy || (!hosted && !topUp)}
        onClick={() => {
          setError(null);
          setOutcome(null);
          staffApi
            .previewAdjustment(
              account.account_id,
              hosted || null,
              topUp || null,
            )
            .then(setPreview)
            .catch((err) => setError(message(err)));
        }}
      >
        Preview adjustment
      </button>
      {preview && (
        <div role="region" aria-label="Adjustment preview">
          <p>
            Account <code>{preview.account_id}</code>: included{" "}
            {preview.current.included ?? "none"} →{" "}
            {preview.resulting_included ?? "—"}; top-up{" "}
            {preview.current.top_up ?? "none"} →{" "}
            {preview.resulting_top_up ?? "—"} (deltas{" "}
            {preview.hosted_credit_delta} / {preview.top_up_credit_delta}).
          </p>
          {preview.refusal_code && (
            <p role="alert">
              The entitlement service would refuse this ({preview.refusal_code}
              ); nothing will change.
            </p>
          )}
          <button
            type="button"
            disabled={busy || !reason.trim()}
            onClick={() => void submit()}
          >
            Confirm adjustment
          </button>
        </div>
      )}
      {outcome?.kind === "confirmed" && (
        <p role="status">
          Applied: entitlement event{" "}
          <code>{outcome.operation.source_entitlement_event_id}</code>; included
          now {outcome.operation.account?.credits.included}.
        </p>
      )}
      {outcome?.kind === "rejected" && (
        <p role="alert">Not applied: {outcome.message}</p>
      )}
      {outcome?.kind === "uncertain" && (
        <p role="alert">
          Outcome unknown: {outcome.message} Check the status before doing
          anything else.{" "}
          <button
            type="button"
            disabled={busy}
            onClick={() => void checkStatus()}
          >
            Check status
          </button>
        </p>
      )}
    </div>
  );
}

function AccountLookup() {
  const [accountId, setAccountId] = useState("");
  const [account, setAccount] = useState<AdminAccountView | null>(null);
  const [history, setHistory] = useState<EntitlementHistory | null>(null);
  const [events, setEvents] = useState<EntitlementHistory["events"]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load(id: string) {
    setError(null);
    try {
      const view = await staffApi.account(id);
      const page = await staffApi.history(id);
      setAccount(view);
      setHistory(page);
      setEvents(page.events);
    } catch (err) {
      setAccount(null);
      setHistory(null);
      setEvents([]);
      setError(message(err));
    }
  }

  async function more() {
    if (!account || !history?.next_after_sequence) return;
    const page = await staffApi.history(
      account.account_id,
      history.next_after_sequence,
    );
    setHistory(page);
    setEvents((prev) => [...prev, ...page.events]);
  }

  return (
    <section aria-labelledby="lookup-heading">
      <h2 id="lookup-heading">Account lookup</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void load(accountId.trim());
        }}
      >
        <label>
          Account ID{" "}
          <input
            aria-label="Account ID"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
          />
        </label>
        <button type="submit">Look up</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {account && (
        <div>
          <p>
            Status {account.status}; entitlement {account.entitlement_state};
            plan {account.hosted_plan ?? "none"}; included{" "}
            {account.credits.included ?? "none"}, top-up{" "}
            {account.credits.top_up ?? "none"}, total{" "}
            {account.credits.total ?? "none"}; Cloud Services{" "}
            {account.cloud_services}
            {account.cloud_services_expires_at &&
              ` (until ${account.cloud_services_expires_at})`}
            ; BYOK licence {account.byok_license_active ? "active" : "inactive"}
            ; local key readiness: not visible to the remote service.
          </p>
          {(account.expected_conditions ?? []).length > 0 && (
            <p>
              Expected conditions:{" "}
              {(account.expected_conditions ?? []).join(", ")}
            </p>
          )}
          <p>
            Replay check: {account.replay?.status}
            {account.replay?.detail_code && ` (${account.replay.detail_code})`}
          </p>
          <Adjustment
            account={account}
            onDone={() => void load(account.account_id)}
          />
          <h3>Entitlement history (replay order)</h3>
          <p>
            Showing {events.length} of {history?.total_events} events.
          </p>
          <ol aria-label="Entitlement history">
            {events.map((e) => (
              <li key={e.event_id}>
                #{e.global_sequence} {e.event_type}
                {e.hosted_credit_delta && ` included ${e.hosted_credit_delta}`}
                {e.top_up_credit_delta && ` top-up ${e.top_up_credit_delta}`}
                {e.manual_reason && ` — ${e.manual_reason}`}
                {e.parse_error && ` (unreadable: ${e.parse_error})`}
              </li>
            ))}
          </ol>
          {history?.next_after_sequence != null && (
            <button type="button" onClick={() => void more()}>
              Load more
            </button>
          )}
        </div>
      )}
    </section>
  );
}

function RequestQueue() {
  const [requests, setRequests] = useState<DataRequest[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(() => {
    staffApi
      .dataRequests()
      .then(setRequests)
      .catch((err) => setError(message(err)));
  }, []);
  useEffect(reload, [reload]);

  function step(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    fn()
      .catch((err) => setError(message(err)))
      .finally(() => {
        setBusy(false);
        reload();
      });
  }

  return (
    <section aria-labelledby="queue-heading">
      <h2 id="queue-heading">Data requests</h2>
      {error && <p role="alert">{error}</p>}
      {requests === null ? (
        <p>Loading…</p>
      ) : (
        <ul aria-label="Data request queue">
          {requests.map((r) => (
            <li key={r.request_id}>
              {r.kind} / {r.scope} for <code>{r.subject_ref}</code>: {r.state}
              {r.progress_code && ` (${r.progress_code})`}
              {r.overdue.length > 0 && ` overdue: ${r.overdue.join(", ")}`}{" "}
              {r.state === "awaiting_authorization" && (
                <>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      step(() =>
                        staffApi.approve(r.request_id, r.revision, null),
                      )
                    }
                  >
                    Approve
                  </button>{" "}
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      step(() =>
                        staffApi.reject(
                          r.request_id,
                          r.revision,
                          "administrator",
                          "Rejected by the administrator.",
                        ),
                      )
                    }
                  >
                    Reject
                  </button>
                </>
              )}
              {(r.state === "approved" ||
                r.state === "failed" ||
                (r.state === "in_progress" && !r.progress_code)) && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    step(() => staffApi.execute(r.request_id, r.revision))
                  }
                >
                  {r.state === "approved" ? "Execute" : "Retry"}
                </button>
              )}
              {r.state === "in_progress" && r.progress_code && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => step(() => staffApi.finalize(r.request_id))}
                >
                  Re-check completion
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Anomalies() {
  const [report, setReport] = useState<AnomalyReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = useCallback(() => {
    staffApi
      .anomalies()
      .then(setReport)
      .catch((err) => setError(message(err)));
  }, []);
  useEffect(reload, [reload]);

  function note(a: Anomaly, state: "investigating" | "closed") {
    staffApi
      .noteAnomaly(
        a.anomaly_id,
        state,
        state === "closed" ? "resolved" : "investigating",
        null,
      )
      .then(reload)
      .catch((err) => setError(message(err)));
  }

  return (
    <section aria-labelledby="anomaly-heading">
      <h2 id="anomaly-heading">Anomalies</h2>
      {error && <p role="alert">{error}</p>}
      {report && (
        <>
          <p>
            Sources:{" "}
            {Object.entries(report.sources)
              .map(([k, v]) => `${k} ${v}`)
              .join(", ")}
          </p>
          {report.anomalies.length === 0 ? (
            <p>No anomalies in the available sources.</p>
          ) : (
            <ul aria-label="Anomaly list">
              {report.anomalies.map((a) => (
                <li key={a.anomaly_id}>
                  {a.signal_code} ({a.source_kind} <code>{a.source_id}</code>):{" "}
                  {a.explanation} [{a.investigation_state}]{" "}
                  <button
                    type="button"
                    onClick={() => note(a, "investigating")}
                  >
                    Investigating
                  </button>{" "}
                  <button type="button" onClick={() => note(a, "closed")}>
                    Close
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}

export default function SupportConsole() {
  const [signedIn, setSignedIn] = useState(false);
  const [sweep, setSweep] = useState<string | null>(null);
  if (!signedIn) return <StaffSignIn onSignedIn={() => setSignedIn(true)} />;
  return (
    <div>
      <button
        type="button"
        onClick={() => {
          void staffApi.signOut().finally(() => setSignedIn(false));
        }}
      >
        Sign out of staff
      </button>{" "}
      <button
        type="button"
        onClick={() => {
          staffApi
            .retentionSweep()
            .then((r) =>
              setSweep(
                Object.entries(r.counts)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(", "),
              ),
            )
            .catch((err) => setSweep(message(err)));
        }}
      >
        Run retention expiry
      </button>
      {sweep && <p role="status">{sweep}</p>}
      <AccountLookup />
      <RequestQueue />
      <Anomalies />
    </div>
  );
}
