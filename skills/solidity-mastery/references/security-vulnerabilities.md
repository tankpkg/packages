# Security Vulnerabilities

Sources: Solidity official documentation, OpenZeppelin Contracts, Trail of Bits smart contract security guidance, Consensys smart contract best practices, SWC Registry, Foundry Book

Covers: reentrancy, access control flaws, flash loan assumptions, `tx.origin`, delegatecall risks, denial of service, oracle manipulation, integer edge cases, and practical audit checklists for Solidity contracts.

## Security Is the Product

In Solidity, security is not a non-functional afterthought. It is a core property of the protocol or application itself.

| Web bug | Smart contract equivalent |
|--------|---------------------------|
| recover with patch later | funds may be gone forever |
| roll back bad deployment | impossible or socially expensive |
| hide behind support workflow | chain execution is final |

Assume every public function will be attacked by automation, MEV bots, and highly motivated adversaries.

## Reentrancy

Reentrancy happens when external control flow returns to your contract before you finish updating internal state.

### Classic bad pattern

```solidity
function withdraw() external {
    uint256 amount = balances[msg.sender];
    require(amount > 0, "none");
    (bool ok,) = msg.sender.call{value: amount}("");
    require(ok, "send failed");
    balances[msg.sender] = 0;
}
```

This sends value before state update.

### Correct baseline

1. Check preconditions
2. Update state
3. Perform external interaction

```solidity
function withdraw() external nonReentrant {
    uint256 amount = balances[msg.sender];
    require(amount > 0, "none");
    balances[msg.sender] = 0;
    (bool ok,) = msg.sender.call{value: amount}("");
    require(ok, "send failed");
}
```

### Reentrancy checklist

| Check | Why |
|------|-----|
| state updated before call | shrink attack window |
| pull-payment model where possible | safer than push |
| `ReentrancyGuard` on sensitive external entrypoints | defense in depth |
| cross-function state coupling reviewed | reentrancy is not always single-function |

## Access Control Failures

Many exploits are simple privilege mistakes, not deep math bugs.

| Mistake | Problem | Fix |
|--------|---------|-----|
| missing `onlyOwner` / role check | anyone can mutate privileged state | explicit role gate |
| owner initialized incorrectly | permanent loss of control | test constructor/initializer |
| upgrade auth too broad | arbitrary implementation takeover | restricted upgrade authority |
| admin key hot wallet | operational compromise risk | multisig/timelock |

Use OpenZeppelin `Ownable`, `AccessControl`, and `TimelockController` rather than inventing your own admin logic.

## `tx.origin` Abuse

Never use `tx.origin` for authorization.

| Why | Explanation |
|----|-------------|
| phishing path | attacker contract can trick user-origin call chain |
| not future-safe | breaks composability and smart account compatibility |

Always authorize with `msg.sender` and explicit trusted roles/contracts.

## Delegatecall Risks

`delegatecall` executes foreign code in your contract’s storage context.

| Risk | Result |
|-----|--------|
| malicious implementation | storage corruption or takeover |
| storage layout mismatch | silent state corruption |
| untrusted plugin module | arbitrary behavior |

Use `delegatecall` only in well-audited proxy/module patterns with strict upgrade/auth controls.

## Flash Loan Assumption Failures

Flash loans are not a bug by themselves. They amplify weak assumptions.

| Weak assumption | Exploit path |
|---------------|-------------|
| spot price equals fair price | price manipulation within one block |
| no one can temporarily dominate liquidity | flash-funded control |
| governance only needs token snapshot at execution | borrowed voting power |

### Defenses

1. Use TWAP/oracle windows instead of instantaneous AMM price
2. Add delay or snapshot mechanisms to governance
3. Model attacker access to huge temporary capital

## Oracle Manipulation

| Bad oracle pattern | Safer alternative |
|-------------------|-------------------|
| single AMM spot read | TWAP or external oracle |
| unbounded trusted updater | signed/quorum-fed updates |
| no staleness checks | timestamp heartbeat validation |

Any protocol depending on price, collateral, or liquidation logic must treat oracle design as security-critical.

## Denial of Service Patterns

| Pattern | Failure |
|--------|---------|
| unbounded loop over user-controlled array | function becomes uncallable |
| push payments to many recipients | one failing recipient blocks progress |
| dependence on strict ordering with no skip path | one bad element bricks workflow |

### Mitigation patterns

| Problem | Fix |
|--------|-----|
| many recipients | pull claims |
| large batch work | chunked processing |
| one bad record blocks all | explicit retry/skip path |

## Integer and Arithmetic Concerns

Solidity 0.8+ checks overflow by default, but arithmetic safety still matters.

| Concern | Why |
|--------|-----|
| division truncation | can break accounting assumptions |
| rounding direction | value leakage or unfairness |
| unchecked blocks | safe only with proven bounds |

Write tests around rounding and boundary conditions, not just overflow behavior.

## Signature and Authorization Pitfalls

| Mistake | Consequence |
|--------|-------------|
| no chain ID/domain separation | replay across chains/contracts |
| missing nonce | replay on same chain |
| invalid signer recovery assumptions | forged or mis-validated approvals |

Use EIP-712 carefully and test replay resistance explicitly.

## External Call Rules

| Rule | Reason |
|-----|--------|
| minimize external calls in stateful flows | reduce attack surface |
| check return values | many tokens/contracts fail silently otherwise |
| assume called contracts can reenter or revert unexpectedly | safe-by-default mindset |

## Upgradeability Security Checks

| Check | Why |
|------|-----|
| initializer can only run once | prevent takeover |
| implementation cannot be directly initialized dangerously | proxy safety |
| storage gap/layout maintained | prevent corruption |
| upgrade auth is strongly restricted | prevent arbitrary implementation changes |

## Audit Checklist

1. Enumerate privileged roles and their powers
2. Review every external call path
3. Review every state transition around value movement
4. Check invariants under reentrancy and flash-capital assumptions
5. Check array/list growth and loop bounds
6. Check signature replay protection
7. Check upgrade and initialization flows

## Common Security Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| assuming OpenZeppelin use alone makes code safe | custom glue code still exploitable | audit integrations |
| relying on tests without adversarial scenarios | false confidence | fuzz + invariant + review |
| no threat model for economic attacks | protocol can fail without code bug | model incentives and game theory |
| missing emergency pause or circuit breaker where warranted | no blast-radius control | add controlled pause when justified |

## Review Questions for Every External Function

1. What state can this function mutate?
2. What external calls can it trigger?
3. What privileged assumptions does it rely on?
4. What happens if the caller has flash-loan-sized capital or adversarial timing?

These questions catch many issues before formal audit review.

## Low-Level Call Safety Notes

| Concern | Why |
|--------|-----|
| arbitrary `call` data | increases attack surface |
| unchecked low-level call result | silent failure / inconsistent state |
| assuming ERC-20 compliance | many tokens are non-standard |

Use battle-tested wrappers and explicit return-value handling.

## Emergency Controls Trade-off

| Control | Benefit | Cost |
|--------|---------|------|
| pause mechanism | blast radius control | governance/trust complexity |
| timelock | slows admin abuse | slower emergency response |
| multisig admin | key risk reduction | operational overhead |

Security controls should reflect protocol threat model, not cargo-cult patterns.

## Front-Running and Ordering Risk

| Pattern | Risk |
|--------|------|
| public mempool-sensitive action | copied/reordered by MEV bots |
| first-come reward or mint | sandwich or sniping risk |
| revealed parameters with economic value | manipulation before settlement |

Mitigations may include commit-reveal, off-chain matching, slippage checks, or time-bounded parameters.

## Approval and Allowance Risks

| Concern | Why |
|--------|-----|
| infinite approvals | larger blast radius on compromise |
| stale approvals | lingering permission risk |
| permit/signature misuse | replay or signer confusion |

Allowance UX and safety are part of protocol security, not just wallet ergonomics.

## Economic Security Review

1. What assumptions depend on liquidity or oracle honesty?
2. Can temporary capital break invariants?
3. Does timing/order matter to fairness or solvency?

Economic exploits often pass unit tests while still destroying the protocol.

## Release Readiness Checklist

- [ ] Reentrancy-sensitive flows follow CEI and/or guards
- [ ] Privileged actions are protected by explicit, reviewed access control
- [ ] `tx.origin` is never used for authorization
- [ ] Price/oracle assumptions are resilient to manipulation
- [ ] Loops and payout paths cannot be DOSed cheaply
- [ ] Signature flows include nonce and domain separation
- [ ] Upgrade and initialization paths are locked down if proxies are used
