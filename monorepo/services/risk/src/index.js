/**
 * @typedef {Object} RiskDecision
 * @property {boolean} allowInstantSettlement
 * @property {string | undefined} reviewReason
 */

/**
 * @param {number} monthlyVolumeCents
 * @returns {RiskDecision}
 */
export function evaluateRiskForPremiumCustomer(monthlyVolumeCents) {
  if (monthlyVolumeCents > 5_000_000) {
    return {
      allowInstantSettlement: false,
      reviewReason: "high monthly volume requires manual review"
    };
  }

  return {
    allowInstantSettlement: true,
    reviewReason: undefined
  };
}
