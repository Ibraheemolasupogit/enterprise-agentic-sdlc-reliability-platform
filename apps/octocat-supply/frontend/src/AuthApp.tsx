import { useEffect, useState } from "react";
import {
  InMemoryWebStorage,
  UserManager,
  WebStorageStateStore,
  type User,
} from "oidc-client-ts";
import App from "./App";
import { createClient, ApiError } from "./api";

export type AuthConfig =
  | { mode: "anonymous" }
  | {
      mode: "oidc";
      authority: string;
      clientId: string;
      scope: string;
      publicOrigin: string;
    };
export function parseAuthConfig(value: unknown): AuthConfig {
  if (!value || typeof value !== "object" || !("mode" in value))
    throw new Error("Invalid authentication configuration.");
  if (value.mode === "anonymous") return { mode: "anonymous" };
  const v = value as Record<string, unknown>;
  if (
    v.mode !== "oidc" ||
    ["authority", "clientId", "scope", "publicOrigin"].some(
      (k) => typeof v[k] !== "string" || !v[k],
    )
  )
    throw new Error("Incomplete OIDC configuration.");
  const authority = new URL(v.authority as string),
    origin = new URL(v.publicOrigin as string);
  if (
    authority.protocol !== "https:" ||
    authority.username ||
    authority.password ||
    authority.search ||
    authority.hash ||
    origin.origin !== v.publicOrigin ||
    origin.protocol !== "https:" ||
    !String(v.scope).split(" ").includes("openid")
  )
    throw new Error("OIDC requires trusted HTTPS origins and openid scope.");
  return v as AuthConfig;
}

export function userStorageKey(user: Pick<User, "profile">) {
  return (
    "morrow-oidc-cart:" +
    encodeURIComponent(JSON.stringify([user.profile.iss, user.profile.sub]))
  );
}

function SignedIn({ user, manager }: { user: User; manager: UserManager }) {
  const [client] = useState(() =>
    createClient(async () => {
      if (user.expired || !user.access_token)
        throw new ApiError("Your session expired. Sign in again.", 401);
      return user.access_token;
    }),
  );
  return (
    <>
      <aside aria-label="Identity">
        <span>Signed in</span>{" "}
        <button onClick={() => void manager.removeUser()}>
          Sign out locally
        </button>
      </aside>
      <App client={client} storageKey={userStorageKey(user)} />
    </>
  );
}

function OidcApp({
  config,
}: {
  config: Extract<AuthConfig, { mode: "oidc" }>;
}) {
  const [manager] = useState(
    () =>
      new UserManager({
        authority: config.authority,
        client_id: config.clientId,
        scope: config.scope,
        redirect_uri: config.publicOrigin + "/auth/callback",
        response_type: "code",
        disablePKCE: false,
        automaticSilentRenew: false,
        monitorSession: false,
        loadUserInfo: false,
        userStore: new WebStorageStateStore({
          store: new InMemoryWebStorage(),
        }),
        stateStore: new WebStorageStateStore({ store: sessionStorage }),
      }),
  );
  const [user, setUser] = useState<User | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const loaded = (value: User) => setUser(value),
      unloaded = () => setUser(null);
    manager.events.addUserLoaded(loaded);
    manager.events.addUserUnloaded(unloaded);
    const expired = () => {
      void manager.removeUser();
    };
    manager.events.addAccessTokenExpired(expired);
    if (location.pathname === "/auth/callback") {
      void manager
        .signinRedirectCallback()
        .then((value) => {
          setUser(value);
          history.replaceState({}, "", "/");
        })
        .catch(() => {
          history.replaceState({}, "", "/");
          setError("Sign-in could not be verified. Start a new sign-in.");
        });
    }
    return () => {
      manager.events.removeUserLoaded(loaded);
      manager.events.removeUserUnloaded(unloaded);
      manager.events.removeAccessTokenExpired(expired);
    };
  }, [manager]);
  if (user && !user.expired)
    return (
      <SignedIn key={userStorageKey(user)} user={user} manager={manager} />
    );
  return (
    <main className="intro">
      <h1>Morrow Supply</h1>
      <p>Sign in to use your own basket.</p>
      {error && <p role="alert">{error}</p>}
      <button
        onClick={() => {
          void manager
            .signinRedirect()
            .catch(() => setError("Sign-in is unavailable. Please try again."));
        }}
      >
        Sign in
      </button>
    </main>
  );
}

export default function AuthApp() {
  const [config, setConfig] = useState<AuthConfig | null>(null),
    [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    void fetch("/auth-config.json", {
      signal: AbortSignal.timeout(5000),
      cache: "no-store",
    })
      .then((r) => {
        if (!r.ok) throw new Error();
        return r.json() as Promise<unknown>;
      })
      .then((v) => {
        if (active) setConfig(parseAuthConfig(v));
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, []);
  if (error)
    return (
      <p role="alert">
        Authentication configuration is unavailable. The shop is closed.
      </p>
    );
  if (!config) return <p role="status">Loading the shop…</p>;
  return config.mode === "anonymous" ? <App /> : <OidcApp config={config} />;
}
