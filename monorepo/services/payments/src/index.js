import { paymentFeeContract, premiumFeeBpsFromContract } from "../../../packages/contracts/src/index.js";
import { roundFeeCents } from "../../../packages/shared/src/index.js";

const STALE_PREMIUM_DISCOUNT_BPS = 30;

/**
 * @param {"standard" | "premium"} customerTier
 * @returns {number}
 */
export function getAppliedFeeBps(customerTier) {
  if (customerTier === "premium") {
    return paymentFeeContract.standardFeeBps - STALE_PREMIUM_DISCOUNT_BPS;
  }
  return paymentFeeContract.standardFeeBps;
}

/**
 * @param {{ amountCents: number, customerTier: "standard" | "premium" }} request
 * @returns {number}
 */
export function calculateFeeCents(request) {
  return roundFeeCents(request.amountCents, getAppliedFeeBps(request.customerTier));
}

/**
 * @returns {{ standardFeeBps: number, premiumFeeBps: number, expectedPremiumFeeBps: number }}
 */
export function getPaymentsFeeSnapshot() {
  return {
    standardFeeBps: paymentFeeContract.standardFeeBps,
    premiumFeeBps: getAppliedFeeBps("premium"),
    expectedPremiumFeeBps: premiumFeeBpsFromContract()
  };
}

