# Payments Pricing Policy

The payments service uses a standard fee of `250` basis points.

Premium customers now receive the new discount approved in `FIN-4821`.

Current policy:

- standard fee: `250` basis points
- premium discount: `75` basis points
- premium effective fee: `175` basis points

Implementation notes:

- do not preserve the legacy premium discount
- the payments service should align with `packages/contracts`
- after changing the code, run `company-verify`

