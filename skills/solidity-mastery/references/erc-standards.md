# ERC Standards

Sources: EIP specifications (ERC-20, ERC-721, ERC-1155, ERC-4626), OpenZeppelin Contracts documentation, Solidity docs, community implementation guidance

Covers: core token standards, implementation patterns, common extensions, pitfalls, and practical selection guidance.

## Standard Selection Is a Product Decision

| Need | Standard |
|-----|----------|
| fungible token | ERC-20 |
| unique NFT | ERC-721 |
| mixed token types / batch transfers | ERC-1155 |
| tokenized vault shares | ERC-4626 |

Do not force one standard into a use case it was not designed for.

## ERC-20

Use ERC-20 for fungible balances and allowance-driven transfer flows.

### Watch out for

| Concern | Note |
|--------|------|
| allowance race UX | approval patterns matter |
| decimals assumptions | UI and protocol consistency |
| non-standard token interactions | wrappers are often needed |

## ERC-721

ERC-721 is for individually unique assets.

| Good fit | Example |
|---------|---------|
| collectibles | NFT collections |
| unique positions | identity or certificate-like assets |

## ERC-1155

Use ERC-1155 when batch operations or mixed token types matter.

| Benefit | Why |
|--------|-----|
| batch transfers | cheaper multi-item movement |
| one contract for many token IDs | simpler game/inventory patterns |

## ERC-4626

ERC-4626 standardizes tokenized vault behavior.

| Core concern | Why |
|------------|-----|
| share math correctness | user fairness and solvency |
| rounding rules | value leakage risk |
| preview functions | integrator expectations |

## OpenZeppelin Guidance

Prefer audited standard implementations and extensions rather than building standards from scratch.

## ERC-20 Implementation Notes

| Concern | Recommendation |
|--------|----------------|
| mint authority | explicit role or immutable issuance rules |
| burn behavior | define who can burn and why |
| pausing | only if operational model justifies it |
| permit support | use ERC-2612 when UX needs off-chain approvals |

### Common ERC-20 pitfalls

| Pitfall | Why it matters |
|--------|----------------|
| non-standard return behavior assumptions | integrations may break |
| fee-on-transfer surprise | downstream accounting complexity |
| rebasing without explicit integrator guidance | ecosystem incompatibility |

## ERC-721 Implementation Notes

| Concern | Recommendation |
|--------|----------------|
| metadata URIs | define stable strategy early |
| enumerable extensions | add only when product truly needs them |
| mint controls | separate sale logic from token core |

### NFT review questions

1. Is metadata mutable or immutable?
2. Who controls minting and reveal timing?
3. Do marketplaces and wallets need standard extensions?

## ERC-1155 Design Notes

ERC-1155 is ideal when multiple token classes share transfer logic.

| Strength | Why |
|---------|-----|
| batch transfer efficiency | lower gas for multi-item movement |
| single contract for many item IDs | cleaner inventory-style systems |
| shared approval model | simplified UX |

### ERC-1155 caution

| Concern | Note |
|--------|------|
| token ID semantics | document clearly for integrators |
| metadata handling | standard URI substitution pattern still needs discipline |

## ERC-4626 Design Notes

| Concern | Why |
|--------|-----|
| share/asset conversion | core economic correctness |
| preview methods | integrator expectations and UX |
| rounding direction | value leakage / unfairness |
| fee integration | must stay mathematically explicit |

Vault math deserves as much review as access control.

## Standard Extension Strategy

| Need | Extension direction |
|-----|---------------------|
| voting/governance | voting extensions |
| permit signatures | ERC-2612-style support |
| royalties | ecosystem-specific NFT royalty extensions |
| pausability | only when operationally justified |

Add extensions intentionally. Every extra surface area increases audit scope.

## Integrator Compatibility Questions

1. Will wallets and indexers understand the standard/extension set?
2. Are events emitted in expected ways?
3. Are non-standard economics documented clearly?

## Standard Selection Anti-Patterns

| Anti-pattern | Better move |
|-------------|-------------|
| using ERC-721 for semi-fungible inventory | consider ERC-1155 |
| inventing custom vault math without ERC-4626 unless necessary | prefer standard |
| extending token behavior before core behavior is correct | stabilize the standard base first |

## Event and Indexer Expectations

| Concern | Why |
|--------|-----|
| standard events emitted correctly | wallets/indexers rely on them |
| metadata conventions clear | marketplace compatibility |
| extension support documented | integrator predictability |

## Review Questions

1. What wallets, explorers, or protocols must integrate with this token?
2. Are there any non-standard semantics that need explicit documentation?
3. Does the chosen standard minimize custom glue code?

## ERC-20 Review Checklist

1. Are mint and burn permissions explicit?
2. Are decimals assumptions documented for integrators?
3. Are allowance-related UX/security trade-offs understood?

## ERC-721 Review Checklist

1. How is metadata hosted and updated?
2. Are minting and reveal flows clearly separated?
3. Are royalty or extension expectations documented?

## ERC-1155 Review Checklist

1. Are token ID semantics obvious?
2. Does batching materially improve user cost?
3. Is metadata strategy consistent across IDs?

## ERC-4626 Review Checklist

1. Are preview functions tested against real math paths?
2. Is share rounding documented and tested?
3. Are fees represented consistently in deposit/withdraw semantics?

## Integrator Surface Area

| Concern | Why |
|--------|-----|
| event correctness | indexers and wallets depend on it |
| metadata semantics | marketplaces and UIs expect clarity |
| extension set | protocol compatibility |

## Standard Extension Trade-offs

| Extension type | Benefit | Cost |
|---------------|---------|------|
| permit | smoother approvals | more signature logic to audit |
| pausability | ops safety | governance trust overhead |
| snapshots | governance/accounting history | more storage/complexity |

## Common ERC Mistakes

| Mistake | Problem |
|--------|---------|
| choosing a standard for branding, not behavior | awkward implementation |
| adding too many extensions by default | larger audit surface |
| weak documentation around custom semantics | integration failures |

## Final Standards Checklist

- [ ] chosen standard matches economic and functional behavior
- [ ] extension set is justified explicitly
- [ ] events and metadata are integration-friendly
- [ ] non-standard semantics are documented aggressively

## Compatibility Smells

| Smell | Why it matters |
|------|----------------|
| unclear metadata semantics | wallet/indexer confusion |
| too many custom behaviors layered onto one standard | integration risk |
| event shape surprises | broken downstream tooling |

## ERC-20 Extension Considerations

| Extension | Use when |
|----------|----------|
| permit / ERC-2612 | signature approvals improve UX |
| snapshots | governance/accounting needs historical reads |
| pausable | governance and ops justify intervention |

## NFT Metadata Questions

1. Is metadata reveal delayed or immediate?
2. Can metadata change after mint?
3. Are marketplaces expected to reflect royalty or custom metadata semantics?

## Vault Standard Review

| Concern | Why |
|--------|-----|
| preview function correctness | integrator trust |
| fee handling clarity | predictable share math |
| deposit/withdraw rounding | user fairness |

## Standard Choice Mistakes

| Mistake | Problem |
|--------|---------|
| adding extensions without clear product need | audit surface bloat |
| mixing custom token economics with weak docs | integration failure |
| choosing a standard for marketing, not behavior | awkward implementation |

## Release Readiness Checklist

- [ ] Chosen ERC standard matches actual asset behavior
- [ ] Standard-specific math and edge cases are tested
- [ ] OpenZeppelin or equivalent audited base contracts are used where sensible
