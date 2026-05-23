# CI Policy

Every pull request that changes pricing, contracts, or verification tooling must pass:

1. `npm run typecheck`
2. `npm run test`
3. `npm run contract:test`
4. `npm run policy:check`

For local developer and agent workflows, the canonical wrapper is:

- `company-verify`

CI treats any failure in that sequence as a release blocker.

