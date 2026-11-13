// Parser-recovery gap: invalid TS that Semgrep CE 1.185.0 accepts without error.
export const a = { b: 1,, c: 2 };
