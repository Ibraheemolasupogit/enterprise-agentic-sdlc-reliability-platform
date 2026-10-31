import {
  DriverExecutor,
  migrateSql,
  seedSql,
  sqlConfiguration,
} from "./sql.js";

async function main() {
  const command = process.argv[2];
  if (
    !["migrate", "seed"].includes(command) ||
    !process.argv.includes("--confirm-sql-change")
  )
    throw new Error(
      "Only migrate/seed --confirm-sql-change are supported. No SQL reset.",
    );
  const executor = new DriverExecutor(sqlConfiguration(process.env, true));
  try {
    if (command === "migrate") await migrateSql(executor);
    else await seedSql(executor);
    console.log(`${command}: complete`);
  } finally {
    await executor.close();
  }
}
main().catch(() => {
  console.error(
    "SQL operation failed. Review configuration/schema/permissions through the approved operator; no credential fallback.",
  );
  process.exitCode = 1;
});
