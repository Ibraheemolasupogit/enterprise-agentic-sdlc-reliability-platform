import { useEffect, useState, useSyncExternalStore } from "react";
import App from "./App";
import { parseAuthConfig, type AuthConfig, type OidcConfig } from "./idToken";
import { captureCallback, discardCallback, OidcSession } from "./oidcSession";
export { parseAuthConfig } from "./idToken";
export { userStorageKey } from "./oidcSession";

function OidcApp({
  config,
  callbackUrl,
}: {
  config: OidcConfig;
  callbackUrl?: string;
}) {
  const [session] = useState(() => new OidcSession(config));
  const state = useSyncExternalStore(session.subscribe, session.getSnapshot);
  useEffect(() => {
    const detach = session.attach();
    void session.complete(callbackUrl);
    return detach;
  }, [session, callbackUrl]);
  if (state.phase === "signedIn")
    return (
      <>
        <aside aria-label="Identity">
          <span>Signed in</span>{" "}
          <button onClick={() => session.logout()}>Sign out locally</button>
        </aside>
        <App
          key={state.generation}
          client={session.client}
          storageKey={state.storageKey}
        />
      </>
    );
  return (
    <main className="intro">
      <h1>Morrow Supply</h1>
      <p>Sign in to use your own basket.</p>
      {state.error && <p role="alert">{state.error}</p>}
      {state.phase === "restore" ? (
        <>
          <button onClick={() => void session.retryRestore()}>
            Retry saved basket
          </button>
          <button onClick={() => session.logout()}>Sign out locally</button>
        </>
      ) : (
        <>
          <button
            disabled={state.phase === "busy"}
            onClick={() => void session.signin()}
          >
            Sign in
          </button>
          {state.phase === "busy" && (
            <button onClick={() => session.logout()}>Cancel sign-in</button>
          )}
        </>
      )}
    </main>
  );
}

export default function AuthApp({
  callbackUrl,
}: { callbackUrl?: string } = {}) {
  const [callback] = useState(() => callbackUrl ?? captureCallback());
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    void fetch("/auth-config.json", {
      signal: AbortSignal.timeout(5000),
      cache: "no-store",
      credentials: "omit",
      redirect: "error",
    })
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json() as Promise<unknown>;
      })
      .then((v) => {
        if (active) {
          const parsed = parseAuthConfig(v);
          if (callback && parsed.mode !== "oidc") throw new Error();
          setConfig(parsed);
        }
      })
      .catch(() => {
        if (active) {
          if (callback) discardCallback();
          setError(true);
        }
      });
    return () => {
      active = false;
    };
  }, [callback]);
  if (error)
    return (
      <p role="alert">
        Authentication configuration is unavailable. The shop is closed.
      </p>
    );
  if (!config) return <p role="status">Loading the shop…</p>;
  return config.mode === "anonymous" ? (
    <App />
  ) : (
    <OidcApp config={config} callbackUrl={callback} />
  );
}
