#!/usr/bin/env bash
set -euo pipefail

repo_root="${FINTECH_MONOREPO_ROOT:-/workspace/fintech-monorepo}"

prepare-fintech-monorepo >/dev/null

echo "Prewarmed sandbox comparison:"
echo
echo "Repo hydrated from prebaked seed into: $repo_root"
echo
echo "Top docs for premium discount:"
company-doc-search "premium discount payments"
echo
echo "Verification command already installed:"
echo "  company-verify"
