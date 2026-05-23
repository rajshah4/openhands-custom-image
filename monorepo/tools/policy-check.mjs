import { readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const repoRoot = process.cwd();

function assertIncludes(filePath, needle, description) {
  const contents = readFileSync(filePath, "utf8");
  if (!contents.includes(needle)) {
    console.error(`policy-check failed: missing ${description} in ${filePath}`);
    process.exit(1);
  }
}

assertIncludes(join(repoRoot, "AGENTS.md"), "company-verify", "company-verify instruction");
assertIncludes(join(repoRoot, "docs", "payments-pricing.md"), "175", "documented premium effective fee");
assertIncludes(join(repoRoot, "docs", "release-guidance.md"), "FIN-4821", "release change ticket");

const indexStat = statSync(join(repoRoot, "tools", "doc-search-index.json"));
if (indexStat.size <= 0) {
  console.error("policy-check failed: doc-search-index.json is empty");
  process.exit(1);
}

console.log("policy-check passed");
