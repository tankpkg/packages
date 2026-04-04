# Foundry Toolchain

Sources: Foundry Book, Solidity documentation, OpenZeppelin tooling guidance, community Foundry practices

Covers: forge test, scripts, deploy flows, fuzz and invariant testing, cheatcodes, gas snapshots, Cast, and Anvil-based local development.

## Foundry as the Default Solidity Workflow

Foundry gives fast compile/test loops, Solidity-native tests, and strong fuzz/invariant tooling.

| Tool | Use |
|-----|-----|
| `forge` | build, test, script |
| `cast` | chain interaction and debugging |
| `anvil` | local node / forked testing |

## Testing Layers

| Layer | Use |
|------|-----|
| unit tests | isolated contract behavior |
| fuzz tests | broad input exploration |
| invariant tests | system property validation |
| fork tests | real protocol integration assumptions |

## Cheatcode Basics

| Cheatcode | Example use |
|----------|-------------|
| `vm.prank` | impersonate caller |
| `vm.expectRevert` | assert failure path |
| `vm.warp` | advance time |
| `vm.roll` | move block number |
| `vm.deal` | fund account |

## Gas Snapshots

Use `forge snapshot` to track hot path gas changes across commits.

## Script and Deploy Flows

Keep deployment scripts deterministic, explicit, and environment-aware.

### Typical Foundry workflow

| Step | Command |
|-----|---------|
| compile | `forge build` |
| run tests | `forge test` |
| gas snapshot | `forge snapshot` |
| local fork/dev chain | `anvil` |
| deploy script | `forge script ... --broadcast` |

## Fuzz Testing

Fuzzing explores many inputs automatically and is one of Foundry’s biggest strengths.

| Good fuzz target | Why |
|-----------------|-----|
| arithmetic and accounting | catches edge values |
| permission boundaries | explores unauthorized callers |
| state transitions | exposes unexpected combinations |

### Fuzz review rules

1. Bound values where domain constraints matter
2. Add meaningful assumptions sparingly
3. Keep failing cases reproducible and understandable

## Invariant Testing

Use invariants for properties that must always hold no matter what sequence of valid actions occurs.

| Example invariant | Why |
|------------------|-----|
| total assets >= total liabilities | solvency |
| no unauthorized balance mint | permission safety |
| vault share math stays bounded | economic correctness |

Invariant tests are especially valuable for protocols with multiple interacting functions.

## Fork Testing

| Use case | Why |
|---------|-----|
| interacting with live protocols | realistic integration assumptions |
| debugging price/oracle behavior | real chain state |
| migration and upgrade rehearsal | live-like conditions |

Fork tests are not a replacement for unit/invariant tests, but they expose ecosystem assumptions early.

## Cast Usage Patterns

| Command family | Use |
|---------------|-----|
| call/read methods | inspect on-chain state |
| send tx | quick operations |
| abi/decode tools | debugging and scripting |

`cast` is the operational knife; use it to inspect and validate assumptions quickly.

## Common Foundry Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| relying only on unit tests | misses adversarial state exploration | add fuzz/invariant |
| giant opaque scripts | deploy risk | keep scripts explicit and reviewed |
| no gas snapshots on hot paths | regressions go unnoticed | snapshot regularly |
| weak fork-test hygiene | flaky assumptions | pin blocks when needed |

## Unit Test Review Questions

1. Are permission failures tested?
2. Are boundary values and zero values tested?
3. Are expected events asserted where integrations depend on them?

## Script Safety Notes

| Concern | Why |
|--------|-----|
| hidden env assumptions | brittle deploys |
| broad side effects in one script | operational risk |
| no post-deploy checks | silent bad release |

## Anvil Usage Patterns

| Use case | Why |
|---------|-----|
| local protocol rehearsal | fast feedback |
| fork-based debugging | realistic external state |
| deploy dry runs | safer release prep |

## Foundry Workflow Discipline

1. compile cleanly
2. run unit tests
3. run fuzz and invariant suites where protocol risk demands them
4. snapshot gas for hot paths
5. rehearse deployment scripts before broadcast

## Suite Composition Guide

| Suite | Purpose |
|------|---------|
| unit | correctness of individual behaviors |
| fuzz | broad edge-case exploration |
| invariant | system-wide safety properties |
| fork | integration realism |

## CI Workflow Notes

| Step | Why |
|-----|-----|
| `forge fmt` / linting equivalent | consistency |
| `forge test` | baseline correctness |
| selected invariant/fuzz suites | risk-focused confidence |
| gas snapshots on hot paths | regression detection |

## Deployment Script Questions

1. Does the script read env/config explicitly?
2. Does it log deployed addresses and roles?
3. Can it assert post-deploy invariants immediately?

## Fork Test Review Questions

1. What real protocol or external state assumption is this test validating?
2. Is the fork pinned if reproducibility matters?
3. Could this be a unit/invariant test instead?

## Operational Checklist for Foundry Users

- [ ] tests are stratified by purpose, not all mixed together
- [ ] fork tests are used intentionally, not as a crutch for weak local design
- [ ] scripts expose config and outputs clearly
- [ ] gas and invariants are part of review for hot or risky paths

## Practical Foundry Review Questions

1. Which suite proves correctness?
2. Which suite proves safety under adversarial input?
3. Which suite proves deployment assumptions?

Those three answers should be obvious before you trust a release candidate.

Clarity in suite purpose makes Foundry workflows easier to scale across a team.

It also makes failures easier to route to the right fix path.

That is a real operational advantage, not just style.

## Reproducibility Rules

| Rule | Why |
|-----|-----|
| pin remappings and dependencies | stable builds |
| keep test fixtures deterministic | easier debugging |
| isolate fork tests by block when needed | avoid drift |

## Fuzz Review Questions

1. Are value domains bounded realistically?
2. Are assumptions hiding real attack scenarios?
3. Do failures reproduce consistently after shrink?

## Invariant Design Heuristics

| Invariant type | Example |
|---------------|---------|
| accounting | total supply/assets balance correctly |
| authorization | unauthorized actor cannot mutate protected state |
| state machine | illegal transitions never succeed |

## Fork Test Cautions

| Concern | Why |
|--------|-----|
| stale assumptions about live protocol state | flaky or misleading tests |
| implicit dependence on latest head | non-reproducible failures |

Fork tests are most valuable when pinned and scoped to clear integration questions.

## Operational Use of `cast`

| Use | Example |
|----|---------|
| inspect ownership/admin values | post-deploy sanity |
| query balances or storage-derived state | incident triage |
| decode calldata/logs | debugging external interactions |

## Script Review Checklist

1. Are addresses and env vars explicit?
2. Does the script assert important post-deploy conditions?
3. Can the script be safely rerun or is it intentionally one-shot?

## Foundry Anti-Patterns

| Anti-pattern | Better move |
|-------------|-------------|
| using scripts as undocumented release process | add explicit runbook around them |
| giant monolithic test contracts | split by concern |
| no invariant suite for protocol-like systems | add at least key safety properties |

## Release Readiness Checklist

- [ ] Unit, fuzz, and invariant coverage match protocol risk
- [ ] Cheatcodes are used intentionally, not as a crutch for weak design
- [ ] Gas snapshots exist for hot paths
- [ ] Deployment scripts are explicit and reproducible
