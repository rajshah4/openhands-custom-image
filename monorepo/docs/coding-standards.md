# Coding Standards

Pricing logic should be:

- explicit
- deterministic
- easy to compare against documented contracts

Do not hardcode stale discounts in service code once a pricing contract exists.

Preferred pattern:

- read shared contract values
- keep service implementation aligned with the contract
- verify with `company-verify`

