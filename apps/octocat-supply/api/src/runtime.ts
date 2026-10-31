import { Store } from "./database.js";
import { demoDatabasePath } from "./config.js";
import {
  anonymousAuthenticator,
  oidcAuthenticator,
  oidcSettings,
} from "./auth.js";
import { DriverExecutor, SqlStore, sqlConfiguration } from "./sql.js";

export function runtimeSettings(env: NodeJS.ProcessEnv) {
  const auth = env.AUTH_MODE ?? "anonymous";
  const database = env.DATABASE_BACKEND ?? "sqlite";
  const environment = env.APP_ENV ?? "local";
  if (
    !["local", "cloud"].includes(environment) ||
    !["anonymous", "oidc"].includes(auth) ||
    !["sqlite", "sql"].includes(database)
  )
    throw new Error("Unknown application/authentication/database mode.");
  if ((database === "sql" || environment === "cloud") && auth !== "oidc")
    throw new Error("SQL/cloud operation requires OIDC.");
  if (environment === "cloud" && database !== "sql")
    throw new Error("Cloud SQLite fallback is forbidden.");
  const oidc = auth === "oidc" ? oidcSettings(env) : undefined;
  const sql = database === "sql" ? sqlConfiguration(env) : undefined;
  const origins = env.ALLOWED_ORIGINS?.split(",");
  if (
    auth === "oidc" &&
    (!origins?.length ||
      origins.some((v) => {
        try {
          const u = new URL(v);
          return u.origin !== v || u.protocol !== "https:";
        } catch {
          return true;
        }
      }))
  )
    throw new Error("OIDC requires explicit HTTPS origins.");
  return { auth, database, environment, oidc, sql, origins };
}

export function createRuntime(env: NodeJS.ProcessEnv) {
  const config = runtimeSettings(env);
  return {
    store: config.sql
      ? new SqlStore(new DriverExecutor(config.sql))
      : new Store(demoDatabasePath(env.DB_PATH)),
    authenticate: config.oidc
      ? oidcAuthenticator(config.oidc)
      : anonymousAuthenticator,
    origins: config.origins,
  };
}
