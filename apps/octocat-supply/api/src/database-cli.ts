import { demoDatabasePath } from "./config.js";
import { Store } from "./database.js";

const command = process.argv[2];
if (
  !["migrate", "seed", "reset"].includes(command) ||
  (command === "reset" && !process.argv.includes("--confirm-demo-reset"))
) {
  console.error(
    "Use migrate, seed, or reset --confirm-demo-reset. Reset affects only the named local demo database.",
  );
  process.exitCode = 1;
} else {
  let store: Store | undefined;
  try {
    store = new Store(demoDatabasePath(process.env.DB_PATH));
    if (command === "migrate") store.migrate();
    else store.seed(command === "reset");
    console.log(`${command}: complete`);
  } catch (error) {
    console.error(
      error instanceof Error ? error.message : "Database operation failed.",
    );
    process.exitCode = 1;
  } finally {
    store?.close();
  }
}
