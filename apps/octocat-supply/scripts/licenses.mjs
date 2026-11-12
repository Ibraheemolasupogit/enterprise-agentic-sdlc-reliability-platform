import { readFileSync, readdirSync, existsSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const lock = JSON.parse(readFileSync("package-lock.json", "utf8"));
const entries = Object.entries(lock.packages).filter(([path]) => path);
const inventory = entries.map(([path, info]) => ({
  name: info.name ?? path.split("node_modules/").at(-1),
  version: info.version,
  license: info.license ?? "REVIEW_REQUIRED",
  development: Boolean(info.dev),
  optional: Boolean(info.optional),
  resolved: info.resolved,
  integrity: info.integrity,
}));
if (inventory.some((item) => item.license === "REVIEW_REQUIRED"))
  throw new Error("A locked package is missing license metadata.");
writeFileSync("dependencies.json", JSON.stringify(inventory, null, 2) + "\n");
let notices =
  "Morrow Supply — browser runtime third-party notices\n\nOriginal application code is MIT; see LICENSE.\n\n";
for (const name of [
  "react",
  "react-dom",
  "scheduler",
  "oidc-client-ts",
  "jwt-decode",
  "jose",
]) {
  const folder = join("node_modules", name);
  const pkg = JSON.parse(readFileSync(join(folder, "package.json"), "utf8"));
  const license = readdirSync(folder).find((file) =>
    /^licen[cs]e(?:\..*)?$/i.test(file),
  );
  if (!license || !existsSync(join(folder, license)))
    throw new Error(`License text missing for ${name}`);
  notices += `=== ${name}@${pkg.version} (${pkg.license}) ===\n${readFileSync(join(folder, license), "utf8")}\n\n`;
  for (const notice of readdirSync(folder).filter((file) =>
    /^notice(?:\..*)?$/i.test(file),
  ))
    notices += readFileSync(join(folder, notice), "utf8") + "\n";
}
writeFileSync(
  "frontend/public/third-party-notices.txt",
  notices.replace(/[\t ]+$/gm, "").trimEnd() + "\n",
);
console.log(
  `Recorded ${inventory.length} exact locked packages and browser runtime license texts.`,
);
