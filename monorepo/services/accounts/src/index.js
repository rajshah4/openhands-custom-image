/**
 * @typedef {"active" | "suspended"} AccountState
 */

/**
 * @typedef {Object} AccountProfile
 * @property {string} accountId
 * @property {AccountState} state
 * @property {"standard" | "premium"} customerTier
 */

/**
 * @param {AccountProfile} profile
 * @returns {boolean}
 */
export function isPremiumAccount(profile) {
  return profile.customerTier === "premium" && profile.state === "active";
}

