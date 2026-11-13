// Parser-recovery gap: invalid TS that Semgrep CE 1.185.0 accepts without error.
export function g(a: boolean) {
  if (a {
    return 1;
  }
  return 0;
}
