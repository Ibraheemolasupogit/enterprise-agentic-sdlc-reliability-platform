import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

function command(args, extra = {}) {
  return spawn(process.execPath, args, {
    stdio: "inherit",
    env: { ...process.env, DB_PATH: "data/e2e.sqlite", ...extra },
  });
}
async function once(args) {
  await new Promise((resolve, reject) => {
    const child = command(args);
    child.once("exit", (code) =>
      code === 0 ? resolve() : reject(new Error("E2E database setup failed.")),
    );
    child.once("error", reject);
  });
}
await once(["api/dist/database-cli.js", "migrate"]);
await once(["api/dist/database-cli.js", "reset", "--confirm-demo-reset"]);
const api = command(["api/dist/server.js"], {
  PORT: "4174",
  HOST: "127.0.0.1",
  ALLOWED_ORIGINS: "http://127.0.0.1:4173",
});
let ready = false;
for (let attempt = 0; attempt < 50; attempt++) {
  try {
    ready = (await fetch("http://127.0.0.1:4174/health/ready")).ok;
  } catch {
    /* Wait for child startup. */
  }
  if (ready) break;
  await delay(100);
}
if (!ready) {
  api.kill();
  throw new Error("E2E API did not become ready.");
}
const web = command(
  [
    "node_modules/vite/bin/vite.js",
    "--config",
    "frontend/vite.config.ts",
    "--port",
    "4173",
  ],
  { API_PORT: "4174" },
);
const stop = () => {
  web.kill("SIGTERM");
  api.kill("SIGTERM");
};
process.once("SIGINT", stop);
process.once("SIGTERM", stop);
web.once("exit", (code) => {
  api.kill();
  process.exitCode = code ?? 1;
});
api.once("exit", () => web.kill());
