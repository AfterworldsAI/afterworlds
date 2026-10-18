import { useCallback, useEffect, useRef, useState } from "react";

import {
  api,
  ApiRequestError,
  type AccountStatus,
  type ByokProviderName,
} from "./api/client";

/**
 * CRD Issue 20: billing, Cloud Services and BYOK settings.
 *
 * Presents and collects; the backend owns entitlements, credentials,
 * readiness and selection. Every value shown is the last authoritative
 * read -- a settings change is confirmed only by the server's refreshed
 * view, and a failure re-reads instead of guessing. Balances are rendered
 * verbatim (exact decimal strings), never parsed into numbers.
 *
 * Raw keys live only in a transient password input: sent once in the request
 * body, cleared when the request settles, never stored or read back.
 */

const PROVIDER_LABEL: Record<ByokProviderName, string> = {
  anthropic: "Anthropic",
  openrouter: "OpenRouter",
};

const PROVIDER_ROLE: Record<ByokProviderName, string> = {
  anthropic: "Primary provider.",
  openrouter:
    "Fallback when Anthropic is also ready; used alone otherwise. Requires an exact model.",
};

const UNAVAILABLE_REASON: Record<string, string> = {
  no_subscription: "No hosted plan is active.",
  subscription_inactive:
    "Hosted access is inactive. Recorded balances are kept but cannot be used for turns.",
  credits_exhausted:
    "Hosted credits are exhausted (the total is zero or below). Hosted turns stop; they never continue at reduced quality.",
};

const CLOUD_TEXT: Record<AccountStatus["cloud_services"], string> = {
  active: "Active.",
  lapsed:
    "Lapsed. Hosted storage, sync, backup, remote access and hosted ingestion are unavailable. Your BYOK license and reading, exporting and downloading your own work are not affected.",
  not_activated: "Not activated.",
};

const VALIDATION_TEXT: Record<string, string> = {
  untested: "Not validated (still eligible for use)",
  valid: "Validated",
  invalid: "Rejected by the provider (not used)",
  error: "Validation error (not used)",
};

function selectionText(account: AccountStatus): string {
  if (account.selected_access_path === "byok")
    return "A turn started now would use your own provider keys (BYOK).";
  if (account.selected_access_path === "hosted")
    return "A turn started now would use hosted credits.";
  if (account.blocked_error_code === "byok_credentials_required")
    return account.byok.byok_ready === null
      ? "Turns are unavailable: BYOK readiness could not be verified, so BYOK is not used."
      : "Turns are unavailable: your BYOK license is active, but no provider key and configuration is ready.";
  return "Turns are unavailable: no access path is active.";
}

function errorText(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) return err.apiError.message;
  return err instanceof Error ? err.message : fallback;
}

export default function AccountPanel({ refreshKey }: { refreshKey: number }) {
  const [account, setAccount] = useState<AccountStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [stale, setStale] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [opError, setOpError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [keyInputs, setKeyInputs] = useState<Record<ByokProviderName, string>>({
    anthropic: "",
    openrouter: "",
  });
  const [acknowledged, setAcknowledged] = useState<ByokProviderName | null>(
    null,
  );
  const [modelInput, setModelInput] = useState("");
  // Only the latest read may populate the view.
  const readEpoch = useRef(0);
  // While a change is in flight no read starts: one begun now could see
  // pre-commit state and land after the change's own authoritative result.
  // Requested reads run once the change settles.
  const mutating = useRef(false);
  const rereadRequested = useRef(false);

  const load = useCallback(async () => {
    if (mutating.current) {
      rereadRequested.current = true;
      return;
    }
    const epoch = ++readEpoch.current;
    setLoading(true);
    setStale(true);
    try {
      const result = await api.getAccount();
      if (epoch !== readEpoch.current) return;
      setAccount(result);
      setModelInput(result.byok.openrouter_model ?? "");
      setLoadError(null);
      setStale(false);
    } catch (err) {
      if (epoch !== readEpoch.current) return;
      setLoadError(errorText(err, "Account status could not be loaded."));
    } finally {
      if (epoch === readEpoch.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  async function run(
    label: string,
    operation: () => Promise<AccountStatus>,
    done: string,
    cleanup?: () => void,
  ) {
    if (mutating.current) return;
    mutating.current = true;
    setPending(label);
    setOpError(null);
    setNotice(null);
    readEpoch.current++; // a read already in flight must not overwrite this
    setLoading(false);
    try {
      const result = await operation();
      setAccount(result);
      setModelInput(result.byok.openrouter_model ?? "");
      setStale(false);
      setLoadError(null);
      setNotice(done);
    } catch (err) {
      setOpError(errorText(err, "The change could not be completed."));
      setStale(true);
      // Nothing is assumed: re-read what the backend actually holds.
      rereadRequested.current = true;
    } finally {
      cleanup?.();
      setPending(null);
      mutating.current = false;
    }
    if (rereadRequested.current) {
      rereadRequested.current = false;
      await load();
    }
  }

  if (account === null) {
    return (
      <section className="account-panel" aria-label="Account">
        <h2>Account &amp; BYOK</h2>
        {loadError ? (
          <p role="alert">
            {loadError}{" "}
            <button type="button" onClick={() => void load()}>
              Retry
            </button>
          </p>
        ) : (
          <p>Loading account status…</p>
        )}
      </section>
    );
  }

  const { credits, byok } = account;
  const writable = byok.credential_store_writable;
  const busy = pending !== null;

  return (
    <section className="account-panel" aria-label="Account">
      <h2>Account &amp; BYOK</h2>
      <p className="account-freshness">
        {loading
          ? "Refreshing…"
          : `Updated ${new Date(account.refreshed_at).toLocaleString()}.`}{" "}
        <button type="button" onClick={() => void load()} disabled={loading}>
          Refresh
        </button>
      </p>
      {stale && !loading && (
        <p role="status">
          The state shown may be out of date
          {loadError ? `: ${loadError}` : "."}
        </p>
      )}
      {pending && <p role="status">{pending}…</p>}
      {opError && <p role="alert">{opError}</p>}
      {notice && !opError && <p role="status">{notice}</p>}

      <h3>Access</h3>
      <p data-testid="selected-access-path">{selectionText(account)}</p>
      <p>Readiness does not guarantee that a provider accepts a turn.</p>

      <h3>Hosted credits</h3>
      {credits.included === null ? (
        <p data-testid="no-hosted-plan">No hosted plan.</p>
      ) : (
        <dl data-testid="hosted-credits">
          <dt>Included</dt>
          <dd>{credits.included}</dd>
          <dt>Top-up</dt>
          <dd>{credits.top_up}</dd>
          <dt>Total</dt>
          <dd>{credits.total}</dd>
        </dl>
      )}
      <p data-testid="hosted-availability">
        {credits.hosted_turn_available
          ? "Hosted turns are available."
          : (UNAVAILABLE_REASON[credits.hosted_unavailable_reason ?? ""] ??
            "Hosted turns are unavailable.")}
      </p>
      <p>
        Usage estimates are not available yet: they await calibration against
        measured usage. Credits are accounting units, not prices.
      </p>
      <p>
        Buying credits or a subscription and starting a trial are not available
        in this version.
      </p>

      <h3>Cloud Services</h3>
      <p data-testid="cloud-services">{CLOUD_TEXT[account.cloud_services]}</p>

      <h3>Bring your own key</h3>
      <p data-testid="byok-license">
        BYOK license: {byok.license_active ? "active" : "not active"}.
      </p>
      {byok.readiness_source === "unavailable_remotely" ? (
        // Prerequisite #205: the remote service never sees device keys.
        <p data-testid="byok-remote">
          Provider keys stay in your local Afterworlds installation. This remote
          account cannot see, store or use them, so local BYOK readiness is not
          available here.
        </p>
      ) : (
        <p data-testid="byok-ready">
          {byok.byok_ready === null
            ? "BYOK readiness could not be verified."
            : byok.byok_ready
              ? "Provider keys and configuration are ready."
              : "No provider key and configuration is ready."}
        </p>
      )}
      {!writable && byok.readiness_source !== "unavailable_remotely" && (
        <p data-testid="store-read-only">
          This installation&apos;s credential store is read-only; keys cannot be
          added or removed here.
        </p>
      )}

      {byok.providers.map((p) => {
        const name = PROVIDER_LABEL[p.provider];
        const configured = p.validation_status !== null;
        return (
          <div
            key={p.provider}
            className="byok-provider"
            data-testid={`provider-${p.provider}`}
          >
            <h4>{name}</h4>
            <p>{PROVIDER_ROLE[p.provider]}</p>
            <p>
              Key:{" "}
              {p.credential_present === null
                ? "unknown (could not be read)"
                : p.credential_present
                  ? "saved"
                  : "not set"}
              {configured && (
                <>
                  {" · "}
                  {p.enabled ? "enabled" : "disabled"}
                  {" · "}
                  {p.validation_status === "error" && !p.last_validated_at
                    ? // A replacement that did not complete: whichever key is
                      // stored has no verdict until validated or replaced.
                      "Not verified: a key change did not complete (not used until validated or replaced)"
                    : VALIDATION_TEXT[p.validation_status ?? ""]}
                  {p.last_validated_at &&
                    ` (${new Date(p.last_validated_at).toLocaleString()})`}
                </>
              )}
            </p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const key = keyInputs[p.provider];
                void run(
                  `Saving ${name} key`,
                  () => api.saveCredential(p.provider, key),
                  `${name} key saved. It is not validated until you validate it.`,
                  () => setKeyInputs((k) => ({ ...k, [p.provider]: "" })),
                );
              }}
            >
              <label>
                {name} API key
                <input
                  type="password"
                  autoComplete="off"
                  spellCheck={false}
                  value={keyInputs[p.provider]}
                  disabled={!writable || busy}
                  onChange={(e) =>
                    setKeyInputs((k) => ({
                      ...k,
                      [p.provider]: e.target.value,
                    }))
                  }
                />
              </label>
              <button
                type="submit"
                disabled={!writable || busy || !keyInputs[p.provider]}
              >
                {p.credential_present
                  ? `Replace ${name} key`
                  : `Save ${name} key`}
              </button>
            </form>
            {writable && p.credential_present !== false && (
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void run(
                    `Removing ${name} key`,
                    () => api.removeCredential(p.provider),
                    `${name} key removed.`,
                  )
                }
              >
                Remove {name} key
              </button>
            )}
            {configured && (
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void run(
                    `${p.enabled ? "Disabling" : "Enabling"} ${name}`,
                    () => api.setProviderEnabled(p.provider, !p.enabled),
                    `${name} ${p.enabled ? "disabled" : "enabled"}.`,
                  )
                }
              >
                {p.enabled ? `Disable ${name}` : `Enable ${name}`}
              </button>
            )}
            {configured && p.credential_present && (
              <div className="byok-validate">
                <label>
                  <input
                    type="checkbox"
                    checked={acknowledged === p.provider}
                    disabled={busy}
                    onChange={(e) =>
                      setAcknowledged(e.target.checked ? p.provider : null)
                    }
                  />
                  Validating contacts {name} with this key and may use a small
                  amount of your provider usage.
                </label>
                <button
                  type="button"
                  disabled={busy || acknowledged !== p.provider}
                  onClick={() =>
                    void run(
                      `Validating ${name} key`,
                      () => api.validateCredential(p.provider),
                      `${name} validation recorded.`,
                      () => setAcknowledged(null),
                    )
                  }
                >
                  Validate {name} key
                </button>
              </div>
            )}
            {p.provider === "openrouter" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void run(
                    "Saving OpenRouter model",
                    () => api.setOpenRouterModel(modelInput),
                    "OpenRouter model saved.",
                  );
                }}
              >
                <label>
                  OpenRouter model
                  <input
                    type="text"
                    value={modelInput}
                    placeholder="vendor/model"
                    disabled={busy}
                    onChange={(e) => setModelInput(e.target.value)}
                  />
                </label>
                <button type="submit" disabled={busy || !modelInput.trim()}>
                  Save model
                </button>
                {byok.openrouter_model !== null && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void run(
                        "Clearing OpenRouter model",
                        () => api.setOpenRouterModel(null),
                        "OpenRouter model cleared.",
                      )
                    }
                  >
                    Clear model
                  </button>
                )}
                <p>
                  An exact model identifier; dynamic aliases such as
                  openrouter/auto are rejected.
                </p>
              </form>
            )}
          </div>
        );
      })}
    </section>
  );
}
