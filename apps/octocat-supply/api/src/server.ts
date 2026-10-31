import { createApp } from "./app.js";
import { portNumber } from "./config.js";
import { createRuntime } from "./runtime.js";

const { store, authenticate, origins } = createRuntime(process.env);
const host = process.env.HOST ?? "127.0.0.1";
if (!["127.0.0.1", "0.0.0.0"].includes(host))
  throw new Error(
    "HOST must be loopback, or 0.0.0.0 inside the isolated container.",
  );
const server = createApp(store, { log: true, origins, authenticate }).listen(
  portNumber(process.env.PORT),
  host,
  () => console.log("Morrow Supply API started."),
);
server.requestTimeout = 5000;
server.headersTimeout = 5000;
for (const signal of ["SIGTERM", "SIGINT"] as const)
  process.once(signal, () => {
    server.close(async () => {
      await store.close();
      process.exit(0);
    });
    setTimeout(() => process.exit(1), 5000).unref();
  });
