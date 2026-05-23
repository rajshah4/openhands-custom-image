import { describe, expect, it } from "vitest";

import { calculateFeeCents, getPaymentsFeeSnapshot } from "../src/index.js";

describe("payments fee policy", () => {
  it("keeps the standard fee unchanged", () => {
    expect(calculateFeeCents({ amountCents: 10_000, customerTier: "standard" })).toBe(250);
  });

  it("applies the new premium discount from company policy", () => {
    expect(calculateFeeCents({ amountCents: 10_000, customerTier: "premium" })).toBe(175);
  });

  it("matches the contract fee snapshot", () => {
    expect(getPaymentsFeeSnapshot()).toEqual({
      standardFeeBps: 250,
      premiumFeeBps: 175,
      expectedPremiumFeeBps: 175
    });
  });
});
