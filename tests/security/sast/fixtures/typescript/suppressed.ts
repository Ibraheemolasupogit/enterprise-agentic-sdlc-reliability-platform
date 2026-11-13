// C5-M08 inline suppression must not hide a mandatory control (--disable-nosem).
export function suppressed(expression: string) {
  // ruleid: morrow.ts.unsafe-html-or-eval
  return eval(expression); // nosemgrep
}
