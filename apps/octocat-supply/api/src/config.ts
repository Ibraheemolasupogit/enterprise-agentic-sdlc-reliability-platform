import { lstatSync, mkdirSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

export const appRoot = fileURLToPath(new URL("../../", import.meta.url));

export function demoDatabasePath(input = "data/demo.sqlite", root = appRoot) {
  if (isAbsolute(input) || input.includes(":") || input.includes(".."))
    throw new Error("DB_PATH must name a relative local demo database.");
  if (!["data/demo.sqlite", "data/e2e.sqlite"].includes(input))
    throw new Error("DB_PATH must be data/demo.sqlite or data/e2e.sqlite.");
  const file = resolve(root, input);
  const rel = relative(root, file);
  if (rel.startsWith(`..${sep}`) || isAbsolute(rel))
    throw new Error("Database path escapes application root.");
  for (const candidate of [
    root,
    dirname(file),
    file,
    `${file}-wal`,
    `${file}-shm`,
  ]) {
    try {
      const stat = lstatSync(candidate);
      if (stat.isSymbolicLink() || (stat.isFile() && stat.nlink > 1))
        throw new Error("Linked demo data paths are not allowed.");
    } catch (error) {
      if (!(
        error instanceof Error &&
        "code" in error &&
        error.code === "ENOENT"
      ))
        throw error;
    }
  }
  mkdirSync(dirname(file), { recursive: true });
  return file;
}

export function portNumber(value = "3000") {
  if (!/^\d+$/.test(value) || Number(value) < 1024 || Number(value) > 65535)
    throw new Error("PORT must be between 1024 and 65535.");
  return Number(value);
}
