import { useState } from "react";

import { api, ApiRequestError, type SessionStatus } from "./api/client";

/**
 * Prerequisite #205: remote sign-in, enrollment and recovery. Codes arrive
 * by notice to the contact address; every enrollment and recovery request
 * reads the same whether or not an account exists. Nothing here is stored in
 * the browser -- the session is an HttpOnly cookie the client never reads.
 */
type Mode = "sign-in" | "register" | "recover";
type Step = "address" | "code";

function errorText(err: unknown): string {
  if (err instanceof ApiRequestError) {
    if (err.apiError.error_code === "authentication_failed") {
      return "That did not work. Check the details and try again.";
    }
    if (err.apiError.error_code === "identity_unavailable") {
      return "Sign-in is temporarily unavailable. Try again shortly.";
    }
    return err.apiError.message;
  }
  return "The request failed. Try again.";
}

export default function SignIn({
  onSignedIn,
  notice,
}: {
  onSignedIn: (status: SessionStatus) => void;
  notice?: string | null;
}) {
  const [mode, setMode] = useState<Mode>("sign-in");
  const [step, setStep] = useState<Step>("address");
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  function switchTo(next: Mode) {
    setMode(next);
    setStep("address");
    setPassword("");
    setCode("");
    setError(null);
    setInfo(null);
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      if (mode === "sign-in") {
        onSignedIn(await api.signIn(address, password));
        return;
      }
      if (step === "address") {
        await (mode === "register"
          ? api.register(address)
          : api.beginRecovery(address));
        setStep("code");
        setInfo(
          "If this address can receive one, a code has been sent to it. Enter it below.",
        );
        return;
      }
      await (mode === "register"
        ? api.completeRegistration(address, code, password)
        : api.completeRecovery(address, code, password));
      switchTo("sign-in");
      setInfo(
        mode === "register"
          ? "Account created. Sign in to continue."
          : "Password changed and every session signed out. Sign in again.",
      );
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
      setPassword("");
    }
  }

  const needsPassword = mode === "sign-in" || step === "code";
  const title =
    mode === "sign-in"
      ? "Sign in"
      : mode === "register"
        ? "Create an account"
        : "Recover your account";

  return (
    <section className="sign-in" aria-label="Sign in">
      <h2>{title}</h2>
      {notice && <p role="status">{notice}</p>}
      {info && <p role="status">{info}</p>}
      {error && <p role="alert">{error}</p>}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <label>
          Email address
          <input
            type="email"
            autoComplete="username"
            value={address}
            disabled={busy || step === "code"}
            onChange={(e) => setAddress(e.target.value)}
          />
        </label>
        {step === "code" && (
          <label>
            Code
            <input
              type="text"
              autoComplete="one-time-code"
              value={code}
              disabled={busy}
              onChange={(e) => setCode(e.target.value)}
            />
          </label>
        )}
        {needsPassword && (
          <label>
            {mode === "sign-in" ? "Password" : "New password"}
            <input
              type="password"
              autoComplete={
                mode === "sign-in" ? "current-password" : "new-password"
              }
              value={password}
              disabled={busy}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
        )}
        <button type="submit" disabled={busy || !address.trim()}>
          {mode === "sign-in"
            ? "Sign in"
            : step === "address"
              ? "Send code"
              : mode === "register"
                ? "Create account"
                : "Set new password"}
        </button>
      </form>
      <p>
        {mode !== "sign-in" && (
          <button type="button" onClick={() => switchTo("sign-in")}>
            Back to sign in
          </button>
        )}
        {mode !== "register" && (
          <button type="button" onClick={() => switchTo("register")}>
            Create an account
          </button>
        )}
        {mode !== "recover" && (
          <button type="button" onClick={() => switchTo("recover")}>
            Forgot password
          </button>
        )}
      </p>
    </section>
  );
}
