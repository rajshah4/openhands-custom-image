# Architecture Overview

The fintech monorepo is organized around service ownership plus shared contracts.

Core layout:

- `services/payments`
  - fee calculation and payment orchestration
- `services/accounts`
  - customer state and tier checks
- `services/risk`
  - risk review and settlement eligibility
- `packages/contracts`
  - cross-service business contracts and release-governed pricing constants
- `packages/shared`
  - common types and helpers

The payments service must not invent pricing rules locally. Fee policy changes are owned by `packages/contracts` and documented in the docs corpus before implementation.

