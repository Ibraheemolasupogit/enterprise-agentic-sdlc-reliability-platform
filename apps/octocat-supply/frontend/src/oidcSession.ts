import {
  InMemoryWebStorage,
  Log,
  UserManager,
  WebStorageStateStore,
  type INavigator,
  type User,
} from "oidc-client-ts";
import { ApiError, createClient, type SessionRequest } from "./api";
import {
  idTokenVerifier,
  parseAuthConfig,
  trustedMetadata,
  type OidcConfig,
} from "./idToken";

const failure = "Sign-in could not be verified. Start a new sign-in.";
const expired = "Your session expired. Sign in again.";
const hash = async (value: string) =>
  Array.from(
    new Uint8Array(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)),
    ),
    (b) => b.toString(16).padStart(2, "0"),
  ).join("");

// Retained solely to migrate an already-authorized legacy OIDC cart reference.
export function userStorageKey(user: Pick<User, "profile">) {
  return (
    "morrow-oidc-cart:" +
    encodeURIComponent(JSON.stringify([user.profile.iss, user.profile.sub]))
  );
}
export type SessionState = {
  phase: "signedOut" | "busy" | "signedIn" | "restore";
  error: string;
  generation: number;
  storageKey?: string;
};

export function captureCallback() {
  if (location.pathname !== "/auth/callback") return undefined;
  const url = location.href;
  history.replaceState({}, "", "/auth/callback");
  return url;
}

export class OidcSession {
  private state: SessionState = {
    phase: "signedOut",
    error: "",
    generation: 0,
  };
  private listeners = new Set<() => void>();
  private token?: string;
  private expiresAt = 0;
  private abort = new AbortController();
  private timer?: ReturnType<typeof setTimeout>;
  private prefix = "";
  private manager?: UserManager;
  private callback?: Promise<void>;
  private attachments = 0;
  private mounted = false;
  private restore?: { legacy: string; target: string; generation: number };
  private config: OidcConfig;
  readonly client = createClient(undefined, () => this.request());

  constructor(
    config: OidcConfig,
    private storage: Storage = sessionStorage,
    private navigator?: INavigator,
  ) {
    this.config = parseAuthConfig(config) as OidcConfig;
    // Only public deployment configuration enters this transient namespace.
    // Compute it synchronously so even an immediate cancellation can clean it.
    this.prefix =
      "morrow-oidc-state:v1:" +
      encodeURIComponent(JSON.stringify(this.config)) +
      ":";
    // Protocol errors can contain callback/code/token material. Never attach a logger.
    Log.setLevel(Log.NONE);
  }
  getSnapshot = () => this.state;
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  private publish(patch: Partial<SessionState>) {
    this.state = { ...this.state, ...patch };
    for (const listener of this.listeners) listener();
  }
  private clearPending() {
    if (!this.prefix) return;
    try {
      for (let i = this.storage.length - 1; i >= 0; i--) {
        const key = this.storage.key(i);
        if (key?.startsWith(this.prefix)) this.storage.removeItem(key);
      }
    } catch {
      /* Storage failure still closes the session; no fallback store. */
    }
  }
  private reset(message = "", clear = true) {
    this.abort.abort();
    this.abort = new AbortController();
    this.token = undefined;
    this.expiresAt = 0;
    clearTimeout(this.timer);
    this.restore = undefined;
    if (clear) this.clearPending();
    void this.manager?.removeUser();
    this.publish({
      phase: "signedOut",
      error: message,
      storageKey: undefined,
      generation: this.state.generation + 1,
    });
  }
  logout = (message = "") => this.reset(message);
  private check(generation: number) {
    if (
      generation !== this.state.generation ||
      (this.mounted && !this.attachments)
    )
      throw new ApiError(expired, 401);
  }
  private checkExpiry = () => {
    if (this.token) {
      if (Date.now() / 1000 >= this.expiresAt) this.logout(expired);
      else this.scheduleExpiry();
    }
  };
  private scheduleExpiry() {
    clearTimeout(this.timer);
    this.timer = setTimeout(
      this.checkExpiry,
      Math.min(
        2147483647,
        Math.max(1, Math.ceil((this.expiresAt - Date.now() / 1000) * 1000)),
      ),
    );
  }
  attach() {
    this.mounted = true;
    this.attachments++;
    document.addEventListener("visibilitychange", this.checkExpiry);
    return () => {
      this.attachments--;
      // StrictMode's immediate effect reattachment must not replay or cancel a callback.
      void Promise.resolve().then(() => {
        if (!this.attachments) {
          document.removeEventListener("visibilitychange", this.checkExpiry);
          this.logout();
        }
      });
    };
  }
  request(): SessionRequest {
    this.checkExpiry();
    if (!this.token) throw new ApiError(expired, 401);
    const generation = this.state.generation;
    return {
      token: this.token,
      signal: this.abort.signal,
      check: () => {
        this.checkExpiry();
        this.check(generation);
      },
      unauthorized: () => {
        if (this.state.generation === generation) this.logout(expired);
      },
    };
  }
  private async initialize(generation: number) {
    const response = await fetch(
      this.config.authority.replace(/\/$/, "") +
        "/.well-known/openid-configuration",
      {
        signal: AbortSignal.any([this.abort.signal, AbortSignal.timeout(5000)]),
        credentials: "omit",
        redirect: "error",
        cache: "no-store",
      },
    );
    if (!response.ok) throw new Error(failure);
    const metadata = trustedMetadata(await response.json(), this.config);
    this.check(generation);
    const manager = new UserManager(
      {
        authority: this.config.authority,
        client_id: this.config.clientId,
        scope: this.config.scope,
        redirect_uri: this.config.publicOrigin + "/auth/callback",
        response_type: "code",
        response_mode: "query",
        metadata,
        disablePKCE: false,
        automaticSilentRenew: false,
        monitorSession: false,
        loadUserInfo: false,
        requestTimeoutInSeconds: 5,
        staleStateAgeInSeconds: 300,
        fetchRequestCredentials: "omit",
        userStore: new WebStorageStateStore({
          store: new InMemoryWebStorage(),
        }),
        stateStore: new WebStorageStateStore({
          store: this.storage,
          prefix: this.prefix + "state:",
        }),
      },
      this.navigator,
    );
    this.manager = manager;
    return { manager, verify: idTokenVerifier(this.config, metadata) };
  }
  async signin() {
    if (this.state.phase === "busy") return;
    this.logout();
    const generation = this.state.generation;
    this.publish({ phase: "busy" });
    try {
      this.check(generation);
      this.clearPending();
      const { manager } = await this.initialize(generation);
      const nonce = crypto.randomUUID();
      this.storage.setItem(
        this.prefix + "pending",
        JSON.stringify({ nonce, created: Date.now(), config: this.config }),
      );
      await manager.signinRedirect({ nonce });
      this.check(generation);
    } catch {
      if (this.state.generation === generation) this.logout(failure);
    }
  }
  complete(url?: string) {
    if (!url) return Promise.resolve();
    this.callback ??= this.consume(url);
    return this.callback;
  }
  private async consume(raw: string) {
    this.reset("", false);
    const generation = this.state.generation;
    this.publish({ phase: "busy" });
    let manager: UserManager | undefined;
    const deadline = setTimeout(() => {
      if (this.state.generation === generation) this.logout(failure);
    }, 15000);
    try {
      this.check(generation);
      const url = new URL(raw);
      const parameters = url.searchParams;
      if (
        url.origin !== this.config.publicOrigin ||
        url.pathname !== "/auth/callback" ||
        url.username ||
        url.password ||
        url.hash ||
        [...parameters.keys()].some((k) => parameters.getAll(k).length !== 1) ||
        !parameters.get("state") ||
        parameters.has("code") === parameters.has("error") ||
        (parameters.has("code") && !parameters.get("code")) ||
        (parameters.has("error") && !parameters.get("error")) ||
        ["access_token", "id_token", "code_verifier"].some((k) =>
          parameters.has(k),
        )
      )
        throw new Error(failure);
      const pending = JSON.parse(
        this.storage.getItem(this.prefix + "pending") ?? "null",
      );
      if (
        !pending ||
        typeof pending.nonce !== "string" ||
        !pending.nonce ||
        !Number.isFinite(pending.created) ||
        Date.now() - pending.created >= 300000 ||
        pending.created > Date.now() + 5000 ||
        JSON.stringify(pending.config) !== JSON.stringify(this.config)
      )
        throw new Error(failure);
      const initialized = await this.initialize(generation);
      manager = initialized.manager;
      const user = await manager.signinRedirectCallback(raw);
      this.check(generation);
      const verified = await initialized.verify(user, pending.nonce);
      this.check(generation);
      const storageKey =
        "morrow-oidc-cart:v2:" +
        (await hash(
          JSON.stringify([
            verified.issuer,
            this.config.clientId,
            verified.subject,
          ]),
        ));
      this.check(generation);
      await manager.removeUser();
      this.check(generation);
      this.token = user.access_token;
      this.expiresAt = verified.expiresAt;
      this.scheduleExpiry();
      // A legacy reference is never authority. Only the actual API may approve it.
      this.restore = {
        legacy: userStorageKey(user),
        target: storageKey,
        generation,
      };
      await this.retryRestore();
    } catch {
      await manager?.removeUser();
      if (this.state.generation === generation) this.logout(failure);
    } finally {
      clearTimeout(deadline);
      // Never erase a newer sign-in's state after an old callback finishes late.
      if (this.state.generation === generation) this.clearPending();
      history.replaceState({}, "", "/");
    }
  }
  async retryRestore() {
    const reference = this.restore;
    if (!reference) return;
    try {
      this.request().check();
      await this.migrateReference(
        reference.legacy,
        reference.target,
        reference.generation,
      );
      this.check(reference.generation);
      this.restore = undefined;
      this.publish({
        phase: "signedIn",
        storageKey: reference.target,
        error: "",
      });
    } catch (error) {
      if (reference.generation !== this.state.generation) return;
      if (error instanceof ApiError && [403, 503, 0].includes(error.status))
        this.publish({
          phase: "restore",
          error: "The saved basket could not be verified. Please retry.",
        });
      else this.logout(failure);
    }
  }
  private async migrateReference(
    legacy: string,
    target: string,
    generation: number,
  ) {
    let id: string | null;
    try {
      id = localStorage.getItem(target) ? null : localStorage.getItem(legacy);
    } catch {
      return;
    }
    if (!id) return;
    if (!/^[a-f0-9-]{36}$/i.test(id)) throw new Error(failure);
    try {
      await this.client.cart(id);
      this.check(generation);
      try {
        localStorage.setItem(target, id);
        localStorage.removeItem(legacy);
      } catch {
        /* Cart storage is optional. */
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        try {
          localStorage.removeItem(legacy);
        } catch {
          /* Optional references only. */
        }
      } else throw error;
    }
  }
}

export function discardCallback() {
  try {
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
      const key = sessionStorage.key(i);
      if (key?.startsWith("morrow-oidc-state:v1:"))
        sessionStorage.removeItem(key);
    }
  } catch {
    /* A storage failure never permits an authenticated session. */
  }
  history.replaceState({}, "", "/");
}
