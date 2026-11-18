// C5-G4 TypeScript syntax gate (invoked only by scripts/sast/feasibility.py; never by hand).
//
// Usage: node ts_syntax_gate.mjs REQUEST.json
// REQUEST: {"root": abs, "compiler": abs path to lib/typescript.js, "compiler_sha256": hex,
//           "version": "x.y.z", "files": [repo-relative .ts/.tsx paths]}
// Loads the compiler from the exact bytes it hashes (no re-read between check and use), parses
// each file from the exact bytes it hashes, and prints one JSON object:
//   {"schema", "typescript_version", "compiler_sha256", "files": {rel: {"sha256", "diagnostics": [[code, line, col], ...]}}}
// Syntax only: no type checking, no module resolution, no default library, no emit, no network.
// Diagnostic message text is never printed (only TS codes and positions). Any internal problem
// exits non-zero; the Python caller treats every non-zero exit or malformed output as a failure.
import { createHash } from "node:crypto";
import fs from "node:fs";
import Module from "node:module";
import path from "node:path";

function fail(message) {
  process.stdout.write(JSON.stringify({ schema: "c5-ts-syntax-gate-result/1", error: message }) + "\n");
  process.exit(2);
}

const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");
const request = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const root = path.resolve(request.root);
const compilerPath = path.resolve(request.compiler);
if (!Array.isArray(request.files) || request.files.length === 0) fail("empty file list");
const lst = fs.lstatSync(compilerPath);
if (!lst.isFile() || lst.isSymbolicLink()) fail("compiler is not a regular file");
const compilerBytes = fs.readFileSync(compilerPath);
if (sha256(compilerBytes) !== request.compiler_sha256) fail("compiler hash mismatch");
const mod = new Module(compilerPath, null);
mod.filename = compilerPath;
mod.paths = Module._nodeModulePaths(path.dirname(compilerPath));
mod._compile(compilerBytes.toString("utf8"), compilerPath);
const ts = mod.exports;
if (ts.version !== request.version) fail("compiler version mismatch");

const decoder = new TextDecoder("utf-8", { fatal: true });
const sources = new Map();
const hashes = {};
for (const rel of request.files) {
  if (typeof rel !== "string" || path.isAbsolute(rel) || rel.split("/").includes("..")) fail("unsafe path");
  const ext = path.extname(rel).toLowerCase();
  if (ext !== ".ts" && ext !== ".tsx") fail("non-TypeScript target");
  const abs = path.join(root, rel);
  if (!abs.startsWith(root + path.sep)) fail("path escape");
  const st = fs.lstatSync(abs, { throwIfNoEntry: false });
  if (!st || !st.isFile() || st.isSymbolicLink()) fail("target missing or not a regular file");
  const bytes = fs.readFileSync(abs);
  hashes[rel] = sha256(bytes);
  let text;
  try {
    text = decoder.decode(bytes);
  } catch {
    fail("target is not valid UTF-8");
  }
  const kind = ext === ".tsx" ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  sources.set("/" + rel, ts.createSourceFile("/" + rel, text, ts.ScriptTarget.Latest, true, kind));
}

const options = {
  noResolve: true, noLib: true, noEmit: true, types: [], jsx: ts.JsxEmit.Preserve,
  target: ts.ScriptTarget.Latest, module: ts.ModuleKind.ESNext,
};
const host = {
  getSourceFile: (name) => sources.get(name), getDefaultLibFileName: () => "/lib.d.ts",
  writeFile: () => {}, getCurrentDirectory: () => "/", getCanonicalFileName: (f) => f,
  useCaseSensitiveFileNames: () => true, getNewLine: () => "\n", fileExists: (f) => sources.has(f),
  readFile: () => undefined, getDirectories: () => [],
};
const program = ts.createProgram({ rootNames: [...sources.keys()], options, host });
const files = {};
for (const [name, sf] of sources) {
  const diags = program.getSyntacticDiagnostics(sf).map((d) => {
    const pos = d.file && d.start !== undefined ? d.file.getLineAndCharacterOfPosition(d.start) : { line: -1, character: -1 };
    return [d.code, pos.line + 1, pos.character + 1];
  });
  files[name.slice(1)] = { sha256: hashes[name.slice(1)], diagnostics: diags.slice(0, 5), diagnostic_count: diags.length };
}
process.stdout.write(JSON.stringify({ schema: "c5-ts-syntax-gate-result/1", typescript_version: ts.version,
  compiler_sha256: sha256(compilerBytes), files }) + "\n");
