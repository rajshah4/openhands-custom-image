import { paymentFeeContract, premiumFeeBpsFromContract } from "../packages/contracts/src/index.js";
import { calculateFeeCents, getPaymentsFeeSnapshot } from "../services/payments/src/index.js";

function fail(message) {
  console.error(`contract-check failed: ${message}`);
  process.exit(1);
}

const snapshot = getPaymentsFeeSnapshot();
const expectedPremiumFeeBps = premiumFeeBpsFromContract();

if (snapshot.premiumFeeBps !== expectedPremiumFeeBps) {
  fail(
    `premium fee mismatch: expected ${expectedPremiumFeeBps} bps from contract, got ${snapshot.premiumFeeBps} bps`
  );
}

const sampleFee = calculateFeeCents({
  amountCents: 10_000,
  customerTier: "premium"
});

if (sampleFee !== 175) {
  fail(`premium fee sample mismatch: expected 175 cents, got ${sampleFee} cents`);
}

if (paymentFeeContract.approvedChangeTicket !== "FIN-4821") {
  fail(`unexpected change ticket ${paymentFeeContract.approvedChangeTicket}`);
}

console.log("contract-check passed");
