# Deployment and Verification

Sources: Foundry Book, Hardhat verification guides, Etherscan verification docs, OpenZeppelin deployment practices, multi-chain operations guidance

Covers: deployment scripts, constructor args, deterministic deploys, verification, multi-chain release concerns, and operational checks after deployment.

## Deployment Is an Operational Workflow, Not Just a Script

| Concern | Why |
|--------|-----|
| correct config per chain | avoid wrong addresses and permissions |
| verification | trust and integrator usability |
| post-deploy checks | catch bad releases quickly |

## Script Design Rules

1. keep deployment scripts explicit
2. separate config by chain/environment
3. log deployed addresses clearly
4. verify ownership/admin assumptions immediately after deploy

## Constructor and Initializer Inputs

| Concern | Recommendation |
|--------|----------------|
| constructor args | record and verify exactly |
| initializer params | stage and test before prod |
| chain-specific addresses | isolate in config, not magic constants |

## Verification

| Why verify | Benefit |
|-----------|---------|
| source transparency | user/integrator trust |
| easier debugging | explorers show source |
| auditability | external review becomes simpler |

## Deterministic Deploys

Use deterministic deployment only when address predictability materially helps system design or UX.

## Post-Deploy Checklist

1. confirm owner/admin roles
2. confirm expected constructor/initializer state
3. verify source on explorer
4. run one smoke interaction on deployed contract

## Multi-Chain Notes

| Concern | Why |
|--------|-----|
| config drift across chains | easy operational bug |
| explorer differences | verification workflow changes |
| gas economics | deployment assumptions vary |

## Common Deployment Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| wrong admin/owner set at deploy | control loss or takeover risk | verify immediately |
| no recorded deployment metadata | hard ops/debugging | log and store artifacts |
| assuming one chain config fits all | broken releases | separate chain config |

## Release Readiness Checklist

- [ ] Deployment scripts are explicit and environment-aware
- [ ] Constructor or initializer inputs are reviewed and recorded
- [ ] Source verification is part of the release workflow
- [ ] Post-deploy smoke checks confirm roles and critical behavior
- [ ] Multi-chain configuration is separated and documented

## Verification Checklist

| Check | Why |
|------|-----|
| compiler version and settings match | explorer verification correctness |
| constructor args encoded correctly | source match |
| library links resolved | deployment transparency |

## Deployment Metadata to Keep

1. chain ID and network name
2. deployed address
3. implementation/proxy/beacon address where relevant
4. admin/owner addresses
5. verification links

Good deployment metadata turns future incidents into debugging tasks rather than archaeology.

## Rollout Questions

1. Is this a first deployment or an upgrade?
2. Are there chain-specific dependencies or external addresses involved?
3. Has a fork or staging rehearsal happened for risky changes?

## Verification Failure Modes

| Failure | Common cause |
|--------|--------------|
| source mismatch | wrong compiler or optimizer settings |
| constructor mismatch | wrong encoded args |
| library mismatch | unresolved links or wrong addresses |

## Post-Deploy Validation Questions

1. Does the contract report the expected owner/admin?
2. Do key read methods return sane initialized values?
3. Has explorer verification succeeded and been recorded?

## Chain Configuration Review

| Concern | Why |
|--------|-----|
| explorer endpoints vary | verification workflow changes |
| gas and nonce behavior differ | script assumptions may break |
| dependent contract addresses differ | integration risk |

## Deployment Runbook Questions

1. What exactly gets deployed on each chain?
2. Which addresses must be substituted per environment?
3. What is the first post-deploy read/write smoke test?

## Upgrade Deployment Notes

| Concern | Recommendation |
|--------|----------------|
| implementation change | verify storage compatibility first |
| admin operation | confirm multisig/timelock path |
| user-visible impact | document rollout clearly |

## Verification Discipline

Source verification should be treated as part of release completeness, not a nice-to-have afterthought.

| Why verify fast | Benefit |
|---------------|---------|
| public trust | users and integrators can inspect code |
| incident response | easier debugging |
| auditability | clearer release record |

## Final Deployment Checklist

- [ ] chain-specific config is isolated and reviewed
- [ ] deployment metadata is recorded immediately
- [ ] explorer verification succeeded on target chains
- [ ] post-deploy smoke checks cover roles and one critical flow
- [ ] upgrade-specific rollout checks are done where relevant

## Operational Smells

| Smell | Why it matters |
|------|----------------|
| no verification link recorded | weak audit trail |
| no distinction between first deploy and upgrade runbook | missed checks |
| chain config mixed into source or scripts ad hoc | release risk |

## Environment Separation

| Concern | Recommendation |
|--------|----------------|
| testnet vs mainnet addresses | separate config clearly |
| multisig/admin wallets | do not reuse casually across environments |
| deploy credentials | scope and document them |

## Release Operator Questions

1. What exact artifact or commit is being deployed?
2. Which chain-specific addresses are inputs to this run?
3. What is the first transaction or read that proves success?

## Post-Verification Actions

| Action | Why |
|------|-----|
| record explorer links | future debugging and trust |
| share deployed addresses with integrators/internal teams | reduce config drift |
| archive tx hashes and metadata | auditability |

## Rollback / Mitigation Notes

If a bad deployment cannot be rolled back directly, know in advance whether the response is pause, upgrade, migration, or communication-only. Operational ambiguity is itself a release risk.

## Multi-Sig / Governance Handoff Checks

| Check | Why |
|------|-----|
| correct owner/admin assigned | control safety |
| timelock or multisig address verified | governance correctness |
| deployer no longer has unintended privilege | least privilege |

## Release Communications Checklist

1. share final addresses and explorer links internally
2. update docs or integration config consumers depend on
3. note any chain-specific caveats for downstream teams or users

## Practical Verification Questions

1. Can a new engineer reproduce this deployment from the recorded metadata?
2. Would an auditor be able to map addresses to source and release intent quickly?
3. Is there any hidden manual step not captured in the runbook?

If the answer to the third question is yes, the deployment process is not finished.

## Chain Launch Order Considerations

| Concern | Why |
|--------|-----|
| smaller test or lower-risk chain first | safer rehearsal |
| mainnet last | highest blast radius |
| address dependency sequencing | reduce integration mistakes |

## Documentation Handoff

After deployment, publish the final addresses, admin ownership, and explorer links where downstream teams can reliably find them. Hidden release metadata becomes future operational debt.

Clear release records shorten audits, incident response, and future migrations.

They also reduce hidden operational dependency on the original deployer.

Good records are part of secure delivery.

Releases should be repeatable by process, not memory.

That standard should hold on every chain.

## Deployment Metadata Checklist

| Item | Why |
|-----|-----|
| network/chain ID | avoid chain confusion |
| deployer address | auditability |
| contract/proxy/implementation addresses | operational clarity |
| verification URLs | future debugging |

## Release Rehearsal Questions

1. Has the deployment or upgrade path been tested on fork/staging?
2. Are chain-specific addresses isolated from production code?
3. Is there a documented rollback or pause response if something goes wrong?

## Deployment Anti-Patterns

| Anti-pattern | Problem |
|-------------|---------|
| hand-running undocumented release steps | fragile operations |
| verifying source only after users discover issues | slower trust recovery |
| no post-deploy ownership/admin checks | latent control bugs |
