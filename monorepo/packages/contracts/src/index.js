/**
 * @typedef {Object} PaymentFeeContract
 * @property {number} standardFeeBps
 * @property {number} premiumDiscountBps
 * @property {string} approvedChangeTicket
 * @property {string} effectiveDate
 */

/** @type {PaymentFeeContract} */
export const paymentFeeContract = {
  standardFeeBps: 250,
  premiumDiscountBps: 75,
  approvedChangeTicket: "FIN-4821",
  effectiveDate: "2026-05-15"
};

/**
 * @returns {number}
 */
export function premiumFeeBpsFromContract() {
  return paymentFeeContract.standardFeeBps - paymentFeeContract.premiumDiscountBps;
}

