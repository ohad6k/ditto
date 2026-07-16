# Emulo Pro Product Naming Design

## Decision

The paid Emulo product is named **Emulo Pro**. Polar production contains two
private recurring products:

- `Emulo Pro Monthly` at `$9 USD` per month
- `Emulo Pro Annual` at `$79 USD` per year

`Founding Beta` is not part of either permanent product name. It may appear as
limited cohort or pricing language, such as `Founding member pricing`, without
making the customer-facing product sound temporary.

## Customer-facing description

> Personalized workflow intelligence and managed continuity across your AI
> agents and devices. Includes early access to premium Emulo capabilities and
> direct founding-member support. AI model usage is not included.

## Product boundary

The open-source local product remains **Emulo**. **Emulo Pro** is the paid
managed layer for continuity, orchestration, premium capabilities, and direct
support. The name must not imply that model tokens, guaranteed productivity
results, or ownership of a user's local Emulo data are included.

## Consistency rules

- Use `Emulo Pro` in Polar product names, checkout copy, account UI, and future
  paid-plan documentation.
- Use `Monthly` and `Annual` only to distinguish billing cadence.
- Keep cohort language in descriptions or campaign copy, not product identity.
- Keep both Polar products private until production billing is independently
  verified and checkout is explicitly enabled.

## Acceptance criteria

- Polar production shows exactly the two private recurring products above.
- Prices and billing intervals match the decision exactly, with no trial.
- The repository stores only nonsecret product IDs after provider verification.
- Production checkout remains disabled throughout product setup.
