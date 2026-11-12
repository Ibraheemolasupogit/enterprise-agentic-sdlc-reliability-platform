import type { PlaywrightTestConfig } from "@playwright/test";
export function assertCaptureOff(
  config: PlaywrightTestConfig,
  env?: Record<string, string | undefined>,
  args?: string[],
): void;
export function assertSanitized(text: string, canaries: string[]): void;
