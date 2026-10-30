import { createApp } from "./app.js";
import { demoDatabasePath, portNumber } from "./config.js";
import { Store } from "./database.js";

const store = new Store(demoDatabasePath(process.env.DB_PATH));
const host = process.env.HOST ?? "127.0.0.1";
if (!["127.0.0.1", "0.0.0.0"].includes(host))
  throw new Error(
    "HOST must be loopback, or 0.0.0.0 inside the isolated container.",
  );
const origins = process.env.ALLOWED_ORIGINS?.split(",");
const server = createApp(store, { log: true, origins }).listen(
  portNumber(process.env.PORT),
  host,
  () => console.log("Morrow Supply API started."),
);
server.requestTimeout = 5000;
server.headersTimeout = 5000;
for (const signal of ["SIGTERM", "SIGINT"] as const)
  process.once(signal, () => {
    server.close(() => {
      store.close();
      process.exit(0);
    });
    setTimeout(() => process.exit(1), 5000).unref();
  });
