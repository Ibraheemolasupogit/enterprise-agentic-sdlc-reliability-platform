// C5-M04 process execution controls. Synthetic; never executed.
import { exec, execFile, spawn } from "node:child_process";

export function unsafeExec(branch: string) {
  // ruleid: morrow.ts.child-process-shell
  exec(`git log ${branch}`);
}

export function unsafeShellSpawn(name: string) {
  // ruleid: morrow.ts.child-process-shell
  spawn("ls", [name], { shell: true });
}

export function safeArgv(branch: string) {
  // ok: morrow.ts.child-process-shell
  execFile("git", ["log", "--", branch]);
}

export function safeSpawn(file: string) {
  // ok: morrow.ts.child-process-shell
  spawn(process.execPath, [file], { stdio: "inherit" });
}

const run = exec;
export function missedAlias(branch: string) {
  // todoruleid: morrow.ts.child-process-shell
  run(`git log ${branch}`);
}
