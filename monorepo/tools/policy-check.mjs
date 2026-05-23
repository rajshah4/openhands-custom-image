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

const indexDir = join(repoRoot, "tools", "doc-search-index");
const metadataPath = join(indexDir, "metadata.json");

const indexStat = statSync(indexDir);
if (!indexStat.isDirectory()) {
  console.error("policy-check failed: tools/doc-search-index is not a directory");
  process.exit(1);
}

const metadataStat = statSync(metadataPath);
if (metadataStat.size <= 0) {
  console.error("policy-check failed: tools/doc-search-index/metadata.json is empty");
  process.exit(1);
}

console.log("policy-check passed");
