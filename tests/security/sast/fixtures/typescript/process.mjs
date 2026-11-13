// C5-M04 MJS variant. Synthetic; never executed.
import * as cp from "node:child_process";

export function unsafeNamespace(target) {
  // ruleid: morrow.ts.child-process-shell
  cp.execSync("rm -rf " + target);
}

export function safeNamespace(target) {
  // ok: morrow.ts.child-process-shell
  cp.execFileSync("ls", ["--", target]);
}
