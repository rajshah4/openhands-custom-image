/**
 * @typedef {"standard" | "premium"} CustomerTier
 */

/**
 * @typedef {Object} FeeQuoteRequest
 * @property {number} amountCents
 * @property {CustomerTier} customerTier
 */

/**
 * @param {number} amountCents
 * @param {number} bps
 * @returns {number}
 */
export function roundFeeCents(amountCents, bps) {
  return Math.ceil((amountCents * bps) / 10_000);
}

/**
 * @param {number} bps
 * @returns {string}
 */
export function formatPercentFromBps(bps) {
  return `${(bps / 100).toFixed(2)}%`;
}

