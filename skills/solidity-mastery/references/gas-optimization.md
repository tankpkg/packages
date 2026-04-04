# Gas Optimization

Sources: Solidity official documentation, Foundry Book, OpenZeppelin Contracts, community gas optimization guides, EVM opcode and storage cost references

Covers: storage packing, calldata vs memory, custom errors, unchecked math, immutable and constant values, loop and batch patterns, compiler optimization, and practical gas review heuristics.

## Gas Is User Cost and Protocol Friction

Every inefficient opcode path increases transaction cost, limits composability, and can make otherwise-correct flows unattractive or unusable.

| Concern | Why it matters |
|--------|----------------|
| expensive writes | users pay more |
| bloated loops | transactions can become unusable |
| redundant storage reads | recurring runtime waste |

Optimize where it materially affects hot paths, not by making code unreadable everywhere.

## Storage Packing

Pack smaller fields into the same storage slot when semantics allow it.

| Good candidate | Example |
|---------------|---------|
| multiple small ints/bools | `uint64`, `uint32`, `bool` together |
| compact enums + flags | status fields |

### Caution

Packing saves space but can increase complexity. Do not micro-pack fields that destroy readability without meaningful gain.

## `calldata` vs `memory`

| Type | Use |
|-----|-----|
| `calldata` | external read-only inputs |
| `memory` | internal mutable temporary values |

Prefer `calldata` for external function parameters when values do not need mutation.

## Custom Errors

Custom errors are cheaper than revert strings and clearer for downstream decoding.

```solidity
error Unauthorized(address caller);

if (msg.sender != owner) revert Unauthorized(msg.sender);
```

Use them for repeated, semantically important failure modes.

## `immutable` and `constant`

| Keyword | Use |
|--------|-----|
| `constant` | compile-time constant |
| `immutable` | constructor-set value that never changes |

Both reduce storage reads compared with mutable state.

## `unchecked` Arithmetic

Unchecked math can reduce gas, but only when bounds are already proven.

| Safe-ish use case | Example |
|------------------|---------|
| loop increments with bounded length | `unchecked { ++i; }` |
| known non-overflow domain math | carefully proven cases |

Never use `unchecked` as a blanket gas trick.

## Batch and Loop Review

| Pattern | Risk |
|--------|------|
| unbounded user-controlled loops | gas blowup / DOS |
| repeated storage writes in loop | high cost |
| per-item external calls | huge risk and cost |

Chunk large work or redesign as pull-based claims when loops threaten block gas limits.

## Compiler Optimization

| Concern | Recommendation |
|--------|----------------|
| optimizer settings | measure with realistic runs |
| via-IR | benchmark, do not assume |
| readability vs hand-tuned assembly | prefer readability unless benefit is proven |

## Gas Review Checklist

1. Identify hot functions users call frequently
2. Check storage reads/writes first
3. Replace common revert strings with custom errors where justified
4. Review loops and batch operations
5. Benchmark with Foundry snapshots

## Common Gas Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| optimizing cold admin paths only | low value | focus on user hot paths |
| unreadable micro-optimizations | maintenance risk | keep clear unless gain is meaningful |
| ignoring storage layout cost | biggest waste untouched | review state first |

## Hot Path Review Questions

1. Is this function called frequently by end users or bots?
2. Does it write storage more than necessary?
3. Can repeated reads be cached in stack/memory locally?

These questions prevent wasted effort on low-value optimization work.

## Event Emission Trade-offs

| Concern | Note |
|--------|------|
| rich events help indexers and UX | useful, but not free |
| over-emitting in tight loops | gas cost rises |

Emit the events integrations need, not every imaginable debug artifact.

## Data Structure Choices

| Pattern | Gas implication |
|--------|-----------------|
| arrays with frequent removal | can be expensive or awkward |
| mappings for keyed lookup | usually cheaper for direct access |
| nested mappings | efficient lookups, less iterable |

Use structures that match access patterns, not just conceptual domain elegance.

## Practical Optimization Order

1. Fix algorithmic/storage issues
2. Review writes and loops
3. Use custom errors and calldata improvements
4. Only then consider lower-level micro-optimizations

Good optimization order keeps readability high while still delivering real gas wins.

## Benchmarking Discipline

| Rule | Why |
|-----|-----|
| benchmark before and after a change | prove value |
| compare hot paths, not everything | focus effort |
| keep gas snapshots in review | catch regressions |

## Storage Review Questions

1. Is this value written frequently?
2. Can related fields pack safely?
3. Can repeated storage reads be cached in local variables?

Storage usually dominates micro-opcode tweaks.

## Readability Guardrail

An optimization that saves tiny gas but obscures correctness may cost more in audit and maintenance risk than it saves in production.

## Memory vs Storage Heuristics

| Concern | Recommendation |
|--------|----------------|
| repeated state reads | cache in local variable when safe |
| temporary transformed data | prefer memory/calldata appropriately |
| unnecessary writes | remove or defer |

## Loop Cost Questions

1. Can the loop length grow with user-controlled state?
2. Does each iteration touch storage or external calls?
3. Would chunking or claims make the path safer and cheaper?

## Contract-Level Optimization Smells

| Smell | Why it matters |
|------|----------------|
| gas focus with no benchmark data | guesswork |
| custom low-level tricks everywhere | audit burden |
| expensive paths accepted because “users will pay” | poor UX and protocol friction |

## Benchmark Review Questions

1. Which functions dominate aggregate user cost?
2. Which functions threaten liveness if gas rises?
3. Are snapshots compared in code review, not just locally?

## Practical Cost Drivers

| Driver | Why |
|-------|-----|
| storage writes | major recurring cost |
| event emission | integration value but not free |
| loops and batching | can dominate transaction viability |
| repeated external interactions | cost and risk compound |

## Final Gas Checklist

- [ ] benchmark data justifies optimization work
- [ ] storage and loops were reviewed before micro-tuning
- [ ] event and data-structure choices reflect actual access patterns
- [ ] readability remains acceptable for future audits and maintenance

## Hot Path Categories

| Hot path | Why it deserves attention |
|---------|---------------------------|
| user deposits/withdrawals | frequent and value-bearing |
| transfers / claims / swaps | high-volume user actions |
| keeper or liquidation flows | gas can block protocol safety |

## Memory and Copying Notes

| Concern | Recommendation |
|--------|----------------|
| repeated array copies | avoid unless necessary |
| large memory structs | review data movement carefully |
| redundant conversions | remove unnecessary transformations |

## Event Cost Discipline

Events are valuable for integrations, but every indexed field and emission has cost.

| Question | Why |
|---------|-----|
| is this event needed by off-chain consumers? | justify cost |
| is every indexed field necessary? | avoid excess indexing |

## Loop Safety Review

1. Can this loop grow with user data?
2. Will this path stay callable under realistic scale?
3. Can this be chunked or converted to pull-based settlement?

## Optimization Anti-Patterns

| Anti-pattern | Problem |
|-------------|---------|
| optimizing before profiling | wasted complexity |
| hand-rolled assembly for trivial gains | audit burden |
| shrinking readability of economic math | correctness risk |

## Release Readiness Checklist

- [ ] Hot paths are benchmarked with realistic tests
- [ ] Storage writes and reads were reviewed first
- [ ] Custom errors replace repeated costly revert strings where appropriate
- [ ] Loops cannot make functions unusable at realistic scale
- [ ] Optimization choices remain understandable to future maintainers
