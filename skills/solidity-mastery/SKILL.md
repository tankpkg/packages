---
name: "@tank/solidity-mastery"
description: |
  Solidity smart contract development, security, and tooling for EVM chains.
  Covers Solidity 0.8.x language patterns (custom errors, immutable, transient
  storage), security (reentrancy, access control, flash loan attacks, audit
  checklists), gas optimization (storage packing, calldata, unchecked math),
  ERC token standards (ERC-20, ERC-721, ERC-1155, ERC-4626), upgradeable
  contracts (UUPS, transparent proxy, storage layout), Foundry toolchain
  (forge test, script, deploy, fuzz/invariant testing), Hardhat integration,
  OpenZeppelin Contracts 5.x, and multi-chain deployment with verification.

  Synthesizes Solidity 0.8.x documentation, OpenZeppelin Contracts 5.x,
  Foundry Book, EIP specifications, Trail of Bits audit guides, Consensys
  best practices, and SWC Registry.

  Trigger phrases: "solidity", "smart contract", "foundry", "forge test",
  "hardhat", "ERC-20", "ERC-721", "ERC-1155", "ERC-4626", "openzeppelin",
  "reentrancy", "gas optimization", "proxy contract", "UUPS", "upgradeable",
  "solidity security", "smart contract audit", "storage layout",
  "solidity patterns", "deploy contract", "forge script", "fuzz testing",
  "invariant testing", "flash loan", "access control solidity",
  "token standard", "ABI encoding", "contract verification"
---

# Solidity Mastery

## Core Philosophy

1. **Security before features** -- Every function is a potential attack surface. Apply checks-effects-interactions, use OpenZeppelin battle-tested contracts, and audit before mainnet.
2. **Gas is user cost** -- Every opcode costs money. Pack storage, prefer calldata over memory, use custom errors, and benchmark with `forge snapshot`.
3. **Immutability demands correctness** -- Deployed contracts cannot be patched. Test exhaustively with fuzz and invariant tests before deployment.
4. **Compose from audited primitives** -- Extend OpenZeppelin rather than reimplementing. Custom cryptography and token logic introduces unaudited risk.
5. **Upgradeability is a tradeoff** -- Proxies add complexity and trust assumptions. Use only when the protocol genuinely requires post-deployment changes.

## Quick-Start: Common Problems

### "Which token standard do I need?"

| Use Case | Standard | Key Feature |
|----------|----------|-------------|
| Fungible currency/utility token | ERC-20 | Balances, approve/transferFrom |
| Unique collectibles/NFTs | ERC-721 | Token IDs, ownerOf |
| Mixed fungible + non-fungible | ERC-1155 | Batch transfers, multi-token |
| Tokenized vault / yield | ERC-4626 | Deposit/withdraw/shares math |
-> See `references/erc-standards.md`

### "My contract is too expensive to call"

1. Run `forge snapshot` to baseline gas per test
2. Pack storage variables (smaller types in same slot)
3. Replace `require(cond, "msg")` with custom errors
4. Use `calldata` instead of `memory` for read-only external args
5. Wrap safe arithmetic in `unchecked {}` blocks
-> See `references/gas-optimization.md`

### "How do I test with Foundry?"

1. Write unit tests extending `forge-std/Test.sol`
2. Use `vm.prank`, `vm.expectRevert`, `vm.deal` cheatcodes
3. Add fuzz tests with parameterized inputs
4. Write invariant tests for protocol-wide properties
5. Run `forge test -vvv` for full trace on failure
-> See `references/foundry-toolchain.md`

### "I need my contract to be upgradeable"

1. Choose pattern: UUPS (lightweight) or Transparent Proxy (admin separation)
2. Use OpenZeppelin upgradeable variants (`@openzeppelin/contracts-upgradeable`)
3. Never define constructors -- use `initializer` functions
4. Maintain storage layout compatibility across versions
-> See `references/upgradeable-contracts.md`

### "How do I prevent reentrancy?"

1. Follow checks-effects-interactions: validate, update state, then call external
2. Use OpenZeppelin `ReentrancyGuard` for defense-in-depth
3. Consider `transient storage` locks (Solidity 0.8.28+, EIP-1153)
-> See `references/security-vulnerabilities.md`

## Decision Trees

### Development Toolchain

| Signal | Use |
|--------|-----|
| Fast compilation, Solidity-native tests | Foundry (forge) |
| JavaScript/TypeScript integration needed | Hardhat |
| Quick prototyping in browser | Remix IDE |
| Production project | Foundry + Hardhat hybrid |

### Contract Architecture

| Signal | Pattern |
|--------|---------|
| Simple standalone contract | Direct deployment |
| Need post-deployment upgrades | UUPS or Transparent Proxy |
| Deploy many identical contracts | Factory (Clone/CREATE2) |
| Complex multi-contract system | Diamond (EIP-2535) or modular |

### Access Control

| Signal | Pattern |
|--------|---------|
| Single privileged address | `Ownable` (OpenZeppelin) |
| Multiple roles with distinct permissions | `AccessControl` (role-based) |
| Time-delayed admin operations | `TimelockController` |
| Governance by token holders | Governor + Timelock |

## Reference Index

| File | Contents |
|------|----------|
| `references/security-vulnerabilities.md` | Reentrancy, access control flaws, flash loan attacks, integer issues, front-running, tx.origin, delegatecall risks, audit checklist |
| `references/gas-optimization.md` | Storage packing, calldata vs memory, custom errors, unchecked math, immutable/constant, batch operations, compiler optimizer settings |
| `references/erc-standards.md` | ERC-20, ERC-721, ERC-1155, ERC-4626 implementation patterns, extensions, common pitfalls, OpenZeppelin usage |
| `references/foundry-toolchain.md` | Forge test, script, deploy, fuzz testing, invariant testing, cheatcodes, gas snapshots, Cast CLI, Anvil forking |
| `references/upgradeable-contracts.md` | UUPS, transparent proxy, beacon proxy, storage layout, initializers, upgrade safety, OpenZeppelin Upgrades |
| `references/contract-patterns.md` | Factory, clone (EIP-1167), CREATE2, diamond (EIP-2535), access control, state machines, pull payments |
| `references/deployment-verification.md` | Multi-chain deployment, Foundry scripts, constructor args encoding, Etherscan verification, deterministic deploys |
