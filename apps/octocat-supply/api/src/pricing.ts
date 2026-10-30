import { badInput } from "./errors.js";

export function validateQuantity(value: unknown): number {
  if (
    typeof value !== "number" ||
    !Number.isInteger(value) ||
    value < 1 ||
    value > 99
  ) {
    badInput("Quantity must be a whole number from 1 to 99.");
  }
  return value;
}

export function calculateTotals(
  lines: { unitPriceMinor: number; quantity: number }[],
) {
  if (lines.length > 100)
    badInput("A cart may contain at most 100 different products.");
  const subtotalMinor = lines.reduce((total, line) => {
    validateQuantity(line.quantity);
    if (!Number.isSafeInteger(line.unitPriceMinor) || line.unitPriceMinor < 0)
      badInput();
    const next = total + line.unitPriceMinor * line.quantity;
    if (!Number.isSafeInteger(next)) badInput();
    return next;
  }, 0);
  // One automatic offer; all arithmetic is in integer pence, rounding down.
  const discountMinor =
    subtotalMinor >= 30_000 ? Math.floor(subtotalMinor / 10) : 0;
  return {
    subtotalMinor,
    discountMinor,
    totalMinor: subtotalMinor - discountMinor,
    currency: "GBP" as const,
    discountLabel: discountMinor ? "10% basket offer" : null,
  };
}
