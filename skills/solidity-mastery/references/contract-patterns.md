# Contract Patterns

Sources: Solidity documentation, OpenZeppelin Contracts, EIP references (EIP-1167, CREATE2, EIP-2535), community smart contract architecture guides

Covers: factory patterns, minimal proxies/clones, CREATE2 deployment, access-control composition, pull payments, state machines, modular system design, and common contract architecture trade-offs.

## Prefer Simple Architecture Until Complexity Forces More

| Need | Pattern |
|-----|---------|
| single isolated contract | direct deployment |
| many similar instances | factory + clones |
| deterministic address requirements | CREATE2 |
| highly modular giant system | carefully reviewed modular or diamond approach |

## Factory Pattern

Factories centralize instance deployment and registry logic.

| Good fit | Example |
|---------|---------|
| vault-per-user systems | new vault instances |
| per-market or per-pool deployments | clone per market |
| controlled deployment workflow | registry + emitted events |

## Clones / EIP-1167

Minimal proxies are useful when many instances share logic and differ mainly by initialization state.

| Benefit | Why |
|--------|-----|
| lower deployment cost | tiny proxy bytecode |
| shared implementation | one logic source |

### Watch out for

| Concern | Note |
|--------|------|
| initialization correctness | every clone still needs safe setup |
| implementation trust | one bug affects all clones |

## CREATE2

Use CREATE2 when deterministic addresses matter.

| Use case | Why |
|---------|-----|
| precomputed contract addresses | UX/integration predictability |
| factory patterns with known endpoints | composability |

### Risks

| Risk | Note |
|-----|------|
| salt misuse | address collisions or confusion |
| assumptions about address uniqueness | deployment orchestration complexity |

## Pull Payment Pattern

Pull payments reduce payout-side reentrancy and DOS risk.

| Push payout | Pull payout |
|-----------|-------------|
| contract sends value immediately | recipient claims value later |
| more convenience | more resilience |

Use pull payments when many recipients or untrusted recipients are involved.

## State Machine Pattern

State machines help constrain legal transitions.

| Example states | Use |
|---------------|-----|
| Created, Active, Settled | auction/order lifecycle |
| Pending, Executed, Cancelled | operational workflow |

Explicit state transitions make audits and tests clearer.

## Access Control Composition

| Need | Pattern |
|-----|---------|
| simple owner control | `Ownable` |
| multiple permissions | `AccessControl` |
| delayed privileged execution | `TimelockController` |

## Diamond and Heavy Modularity Warning

Diamond-style systems can be powerful, but they massively expand complexity and audit surface.

Use them only when simpler modularization truly cannot support the system.

## Common Pattern Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| over-engineering with complex modularity early | audit and maintenance burden | start simpler |
| clone factory without safe initialization | takeover or broken instances | initialize carefully |
| state machine undocumented | transition bugs | explicit state table/tests |

## Release Readiness Checklist

- [ ] Architecture pattern matches actual product/system need
- [ ] Factories and clones initialize safely
- [ ] CREATE2 is used only when deterministic addresses are truly needed
- [ ] Pull-payment and state-machine patterns are considered where they reduce risk
- [ ] Modular complexity is justified, not decorative

## Factory Review Questions

1. Who is allowed to create instances?
2. Does every instance need registration or discoverability?
3. Can initialization race or fail dangerously?

## Pull vs Push Payment Review

| Pattern | Use |
|--------|-----|
| push | few trusted recipients, simple flow |
| pull | many/untrusted recipients, safer resilience |

## State Machine Review

| Question | Why |
|---------|-----|
| are all legal transitions explicit? | easier auditing |
| are impossible transitions blocked? | safety and predictability |
| are terminal states truly terminal? | lifecycle correctness |

## Diamond Pattern Warning

Use diamond-style modularity only when simpler module/proxy/factory structures cannot meet product requirements.

Audit cost rises sharply once selector routing and storage composition become complex.

## Pattern Selection Heuristic

| If you need... | Start with... |
|---------------|---------------|
| one contract | direct deployment |
| many similar instances | factory or clone |
| deterministic addresses | CREATE2 |
| delayed privileged actions | timelock + role model |

## Composition Questions

1. Which contract owns which state?
2. Which contract can call which privileged function?
3. What happens if one module fails or upgrades?

## Factory Operational Questions

| Question | Why |
|---------|-----|
| is deployed instance discoverability required? | registry design |
| who pays deployment gas? | user vs protocol economics |
| must deployments be deterministic? | CREATE2 decision |

## Clone Pattern Notes

Minimal proxies are strongest when implementation logic is stable and instance-specific state is small and well-initialized.

| Concern | Note |
|--------|------|
| initializer safety | critical for clones |
| implementation bug blast radius | all clones can share it |

## Access Composition Review

1. Are privileged paths centralized or scattered?
2. Do factory-created instances inherit the right admin model?
3. Is there any hidden dependency between modules that weakens isolation?

## Pattern Anti-Patterns

| Anti-pattern | Problem |
|-------------|---------|
| choosing diamonds for novelty | unnecessary complexity |
| mixing many patterns without a clear ownership model | audit confusion |
| factory without event/log discoverability | hard operations |

## Direct Deployment Pattern

Use direct deployment when one contract or a small fixed set of contracts fully expresses the system.

| Good fit | Why |
|---------|-----|
| simple token or vault | least moving parts |
| limited governance surface | easiest audit model |

Direct deployment is underrated because it minimizes hidden coordination costs.

## Registry Pattern

Factories often benefit from an explicit registry or emitted events for discoverability.

| Need | Pattern |
|-----|---------|
| on-chain instance lookup | mapping/registry |
| off-chain discovery | emitted events with indexed fields |

## Clone Fleet Questions

1. Are clones homogeneous enough to share one implementation safely?
2. Is each clone initialized with all required immutable-like state?
3. What happens when the shared implementation has a bug?

## CREATE2 Operational Notes

| Concern | Why |
|--------|-----|
| salt derivation | address determinism and collision avoidance |
| user expectations around known addresses | UX/security significance |
| replay across environments | config hygiene |

CREATE2 is powerful, but deterministic addresses add operational expectations.

## Pull Payment Details

Pull payments shift complexity toward claim logic, but often reduce recipient-side risk.

| Benefit | Cost |
|--------|------|
| safer against malicious recipients | extra claim transaction |
| easier failure isolation | more state bookkeeping |

## State Machine Documentation Pattern

Document legal transitions explicitly.

| From | To | Condition |
|------|----|-----------|
| Created | Active | initialization complete |
| Active | Settled | success condition met |
| Active | Cancelled | explicit cancellation path |

State tables are better than prose for auditability.

## Role Composition Notes

| Concern | Recommendation |
|--------|----------------|
| one global owner for everything | avoid if duties differ materially |
| many tiny bespoke roles | can become hard to reason about |
| timelocked sensitive ops | useful for governance-heavy systems |

## Architectural Review Questions

1. Which modules or contracts may fail independently?
2. Which dependencies are optional versus correctness-critical?
3. Could a simpler architecture remove an entire attack surface?

## Pattern Trade-off Table

| Pattern | Strength | Trade-off |
|--------|----------|-----------|
| direct deployment | simplest audit model | less flexibility |
| factory + clone | cheaper instance creation | shared implementation risk |
| CREATE2 | deterministic addresses | more deployment ceremony |
| diamond | extreme modularity | major complexity/audit burden |

## Final Pattern Checklist

- [ ] architecture is simpler than or equal to the product need
- [ ] ownership and discoverability are explicit
- [ ] clone/factory initialization is safe and test-covered
- [ ] state machines and role models are documented clearly
- [ ] no pattern was chosen just because it is fashionable
