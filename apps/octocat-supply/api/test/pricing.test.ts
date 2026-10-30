import { describe, expect, it } from "vitest";
import { calculateTotals, validateQuantity } from "../src/pricing.js";

describe("authoritative integer pricing", () => {
  it("handles an empty basket and the specified multi-line example", () => {
    expect(calculateTotals([])).toMatchObject({
      subtotalMinor: 0,
      discountMinor: 0,
      totalMinor: 0,
    });
    expect(
      calculateTotals([
        { unitPriceMinor: 12999, quantity: 2 },
        { unitPriceMinor: 1999, quantity: 3 },
      ]),
    ).toMatchObject({
      subtotalMinor: 31995,
      discountMinor: 3199,
      totalMinor: 28796,
      currency: "GBP",
    });
  });
  it.each([
    [29999, 0],
    [30000, 3000],
    [30001, 3000],
    [30009, 3000],
    [30010, 3001],
  ])("applies the threshold/floor rule at %i pence", (subtotal, discount) => {
    expect(
      calculateTotals([{ unitPriceMinor: subtotal, quantity: 1 }])
        .discountMinor,
    ).toBe(discount);
  });
  it.each([0, -1, 1.5, 100, NaN, Infinity, "2", null])(
    "rejects an invalid quantity %s",
    (quantity) => {
      expect(() => validateQuantity(quantity)).toThrow();
    },
  );
  it("accepts quantity boundaries, and rejects fractional/unsafe prices or oversized carts", () => {
    expect(validateQuantity(1)).toBe(1);
    expect(validateQuantity(99)).toBe(99);
    expect(() =>
      calculateTotals([{ unitPriceMinor: 1.5, quantity: 1 }]),
    ).toThrow();
    expect(() =>
      calculateTotals([
        { unitPriceMinor: Number.MAX_SAFE_INTEGER, quantity: 99 },
      ]),
    ).toThrow();
    expect(() =>
      calculateTotals(
        Array.from({ length: 101 }, () => ({ unitPriceMinor: 1, quantity: 1 })),
      ),
    ).toThrow();
  });
});
