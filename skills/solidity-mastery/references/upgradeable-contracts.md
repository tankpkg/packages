# Upgradeable Contracts

Sources: OpenZeppelin Upgrades documentation, Solidity documentation, EIP-1967, UUPS and transparent proxy references, audit guidance from Trail of Bits and community upgradeability best practices

Covers: UUPS, transparent proxy, beacon proxy basics, storage layout safety, initializers, upgrade governance, implementation locking, and operational review patterns for upgradeable contracts.

## Upgradeability Is a Governance Choice First

Upgradeable contracts are not just a technical pattern. They change the trust model.

| Benefit | Cost |
|--------|------|
| post-deploy bug fixes | admin trust and governance complexity |
| feature iteration | larger audit surface |
| migration flexibility | storage layout and tooling discipline |

If a system does not genuinely need upgrades, non-upgradeable contracts remain simpler and safer.

## Main Proxy Patterns

| Pattern | Best for |
|--------|----------|
| UUPS | lean upgradeable applications |
| Transparent Proxy | clearer admin/user separation |
| Beacon Proxy | many instances sharing implementation |

Use the simplest proxy model that matches the upgrade and fleet shape you actually need.

## Initializer Rules

| Rule | Why |
|-----|-----|
| replace constructors with initializers | proxy-safe setup |
| guard initializer to run once | prevent takeover |
| initialize inherited modules correctly | avoid partial setup |

## Storage Layout Safety

Storage layout compatibility is the central correctness constraint in upgrades.

| Risk | Result |
|-----|--------|
| inserting fields in wrong order | state corruption |
| changing variable types | unreadable/wrong storage |
| inheritance layout drift | silent breakage |

### Storage review checklist

1. append new variables instead of reordering old ones
2. preserve inherited layout assumptions
3. review storage gaps if used
4. compare layouts before upgrade execution

## Implementation Locking

Implementations should not remain dangerously initializable in ways that allow misuse.

| Concern | Recommendation |
|--------|----------------|
| direct implementation takeover | lock or initialize appropriately |
| accidental use of implementation contract | document and guard against misuse |

## Upgrade Authorization

| Pattern | Use |
|--------|-----|
| multisig admin | baseline safer control |
| timelock + multisig | stronger governance and review |
| on-chain governance | protocol-level decentralized control |

Upgrade auth should be at least as carefully reviewed as token transfer logic.

## Common Upgrade Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| using constructors in upgradeable code | init never runs for proxy state | use initializer |
| storage reordering | permanent corruption | append only and review layouts |
| weak upgrade auth | arbitrary malicious implementation | multisig/timelock/governance |
| upgrading without test rehearsal | unsafe production mutation | stage and simulate |

## Operational Upgrade Workflow

1. review storage layout diff
2. test upgrade path on fork or staging
3. verify admin/authorization controls
4. execute upgrade through trusted governance path
5. run post-upgrade smoke checks

## Release Readiness Checklist

- [ ] Upgradeability is justified by product/governance needs
- [ ] Proxy pattern choice is explicit
- [ ] Initializers are one-time and complete
- [ ] Storage layout compatibility is reviewed before upgrades
- [ ] Upgrade authorization is strongly controlled

## Transparent Proxy Notes

| Concern | Note |
|--------|------|
| admin separation | admin calls management path, users hit implementation |
| operational clarity | easier mental model for some teams |

Transparent proxies trade some elegance for clearer control separation.

## UUPS Notes

| Concern | Note |
|--------|------|
| lighter proxy structure | useful for lean deployments |
| upgrade function in implementation | auth review becomes critical |

## Beacon Proxy Notes

Beacon proxies are useful when many proxies should share one upgradeable implementation source.

| Good fit | Example |
|---------|---------|
| many similar deployed instances | vault or account fleets |

### Beacon caution

One bad implementation update affects the whole fleet.

## Upgrade Test Checklist

1. deploy v1
2. initialize and populate representative state
3. upgrade to v2 in test/fork environment
4. verify reads and writes still behave correctly
5. verify old storage values remain coherent

## Governance Questions

1. Who can trigger an upgrade?
2. Is there a delay or review window?
3. How are emergency fixes handled?

Upgradeability without governance clarity is operational ambiguity with extra attack surface.

## Initialization Pitfalls

| Pitfall | Problem |
|--------|---------|
| forgotten parent initializer | partial state setup |
| initializer callable twice | takeover or corruption |
| unsafe implementation initialization | direct misuse risk |

## Upgrade Review Checklist

1. compare old and new storage layout
2. test the upgrade path on fork or staging
3. verify authorization for upgrade execution
4. confirm post-upgrade smoke checks

## Storage Gaps and Reserved Space

| Pattern | Why |
|--------|-----|
| reserved storage gaps | future layout flexibility |
| append-only state changes | lower corruption risk |

Use storage gaps intentionally, not as a substitute for layout review discipline.

## Proxy Admin Review

| Concern | Recommendation |
|--------|----------------|
| single hot wallet admin | avoid in production |
| multisig-controlled admin | safer baseline |
| timelocked upgrades | stronger review path |

## Upgrade Testing Matrix

| Test | Why |
|-----|-----|
| read old state after upgrade | layout safety |
| write new state after upgrade | new logic correctness |
| auth path on upgrade function | governance safety |
| event/admin outputs | operational sanity |

## Beacon Fleet Review Questions

1. How many proxies depend on this beacon?
2. What is the blast radius of one bad implementation upgrade?
3. Is there a staged rollout path or only all-at-once change?

## Governance Trade-off Table

| Governance model | Benefit | Cost |
|-----------------|---------|------|
| multisig only | simpler ops | less review delay |
| timelock + multisig | stronger review | slower emergency fixes |
| token governance | decentralization path | more system complexity |

## Common Upgrade Smells

| Smell | Why it matters |
|------|----------------|
| no written upgrade procedure | operational fragility |
| layout diff not reviewed | corruption risk |
| implementation left loosely controlled | hidden takeover vector |

## Final Upgradeability Checklist

- [ ] proxy pattern is justified and documented
- [ ] storage layout changes are reviewed before every upgrade
- [ ] implementation/init paths cannot be abused trivially
- [ ] upgrade authority is strong and operationally clear
- [ ] post-upgrade validation is part of the runbook

## Review Smells

| Smell | Why it matters |
|------|----------------|
| “we can upgrade later” with no governance plan | hidden trust risk |
| no storage diff discipline | corruption risk |
| proxy admin path not exercised in tests | operational fragility |

## Upgrade Runbook Questions

1. What exact contract(s) change in this upgrade?
2. What storage assumptions are new or modified?
3. What post-upgrade smoke checks prove the system still behaves correctly?

One explicit runbook question can prevent many dangerous “simple” upgrades.

## Proxy Pattern Comparison

| Pattern | Strength | Trade-off |
|--------|----------|-----------|
| UUPS | lean and common | upgrade auth lives in implementation path |
| Transparent | clear admin separation | slightly more operational ceremony |
| Beacon | efficient fleet upgrades | one implementation mistake can affect many proxies |

## Storage Layout Review Questions

1. Were any existing variables reordered?
2. Were any types changed incompatibly?
3. Does inheritance order affect layout unexpectedly?

## Post-Upgrade Validation

| Check | Why |
|------|-----|
| owner/admin values intact | governance continuity |
| critical read methods sane | layout correctness |
| key write path still works | upgrade safety |

## Upgradeability Anti-Patterns

| Anti-pattern | Problem |
|-------------|---------|
| adding proxies before governance is defined | hidden trust risk |
| skipping storage diff review | silent corruption risk |
| emergency upgrade path with weak auth | system takeover risk |
