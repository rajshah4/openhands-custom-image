# Agent Instructions

Always treat this repository as a self-verifying enterprise codebase.

Required behavior:

- Read the docs before changing payments pricing behavior.
- Use `company-doc-search "<query>"` whenever pricing, contracts, release policy, or ownership is unclear.
- Before finishing any task, run:
  - `company-verify`
- Do not claim the task is complete until `company-verify` passes.
- If `company-verify` fails, fix the code or tests before returning control.

Task framing for this demo:

- The key task is to update the payments fee calculation so premium customers receive the new discount described in the docs.
- The current code intentionally reflects stale business logic and should fail verification until fixed.

