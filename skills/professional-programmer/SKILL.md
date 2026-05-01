---
name: "@tank/professional-programmer"
description: |
  Professional programming judgment for coding agents. Covers production-quality
  implementation, explicit tradeoffs, testing discipline, refactoring safety,
  debugging, delivery hygiene, collaboration, and software craftsmanship.
  Synthesizes Birat Rai's 97-step Medium roadmap, the CC-licensed 97 Things
  Every Programmer Should Know GitBook/GitHub text, and existing Tank specialist
  skills for clean code, BDD, security, databases, and codemods.

  Trigger phrases: "professional programmer", "code professionally",
  "code like a senior engineer", "production-quality code",
  "engineering judgment", "how should this be coded",
  "is this code professional", "review this like a principal engineer",
  "ship-ready code", "coding discipline", "programmer wisdom",
  "97 things", "software craftsmanship", "what tradeoff should win",
  "tighten this code", "before I commit"
---

# Professional Programmer

## Core Philosophy

1. **Correctness first** -- Clever wrong code is not professional. Prove behavior before optimizing or polishing.
2. **Simplicity before abstraction** -- Abstractions must earn their keep through repeated use, clearer boundaries, or safer change.
3. **Tests are engineering evidence** -- Untested behavior is a guess. Prefer behavior-focused tests over incidental implementation checks.
4. **Code is maintained more than written** -- Optimize names, structure, errors, and logs for the next maintainer under pressure.
5. **Tradeoffs must be explicit** -- State what wins, what loses, why now, and how to verify the decision later.

## Quick-Start: Common Problems

### "I need to implement this feature professionally"

1. Clarify user behavior, domain terms, failure modes, and rollout risk.
2. Choose the smallest design that preserves correctness and future readability.
3. Add behavior tests or characterization tests before changing risky code.
4. Route specialized concerns to the relevant Tank skill.
-> See `references/professional-principles.md` and `references/testing-and-verification.md`.

### "This code feels messy"

1. Identify the dominant smell: unclear responsibility, hidden state, duplication, unsafe errors, or missing tests.
2. Prefer removal and simplification before adding new abstractions.
3. Keep refactors small and verify after each step.
-> See `references/simplicity-and-design.md` and `references/refactoring-and-removal.md`.

### "I need to decide whether to abstract"

1. Ask whether the variation exists today or is speculative.
2. Compare DRY against clarity and coupling.
3. Keep duplication when shared abstraction would hide different concepts.
-> See `references/conflict-resolution.md`.

### "I need to debug a hard issue"

1. Reproduce the behavior and trust executable evidence over assumptions.
2. Check your code first, then dependencies, configuration, and environment.
3. Add a regression test or durable guard before declaring the fix complete.
-> See `references/correctness-and-state.md` and `references/tools-and-automation.md`.

### "I need to ship safely"

1. Check tests, build health, logging, migration risk, rollback path, and user-visible failure modes.
2. Deploy incrementally when possible and keep the build clean.
3. Document known tradeoffs and follow-up debt.
-> See `references/tools-and-automation.md` and `references/collaboration-and-process.md`.

## Decision Trees

### Specialist Routing

| Signal | Use |
| ------ | --- |
| Code smells, long functions, naming, modularity | `@tank/clean-code` |
| Behavior tests, Gherkin, real-system verification | `@tank/bdd-e2e-testing` |
| Security boundary, secrets, auth, injection, threat model | `@tank/security-review` |
| Query plan, schema, indexes, database performance | `@tank/relational-db-mastery` |
| Custom lint rule, AST migration, codemod | `@tank/ast-linter-codemod` |
| TypeScript rename, move, split, organize imports | `js-tools` |

### Principle Routing

| Situation | Load |
| --------- | ---- |
| Unsure what professional behavior means | `references/professional-principles.md` |
| Principles conflict | `references/conflict-resolution.md` |
| Design is too clever or vague | `references/simplicity-and-design.md` |
| State, errors, or correctness are risky | `references/correctness-and-state.md` |
| Test strategy is weak | `references/testing-and-verification.md` |
| Refactor may break behavior | `references/refactoring-and-removal.md` |
| Build, tools, deployment, commits are weak | `references/tools-and-automation.md` |
| Performance or systems tradeoff appears | `references/performance-and-systems.md` |
| Review, customer, estimation, or teamwork issue | `references/collaboration-and-process.md` |

## Reference Index

| File | Contents |
| ---- | -------- |
| `references/source-coverage.md` | Source ingestion method, coverage counts, copyright policy, and ledger interpretation |
| `references/professional-principles.md` | Professional responsibility, maintainability, learning loops, supportability, and clarification habits |
| `references/conflict-resolution.md` | Tiebreakers for correctness, security, simplicity, performance, DRY, tests, and abstraction conflicts |
| `references/simplicity-and-design.md` | Simplicity, code as design, SRP, small functions, domain language, APIs, and behavior encapsulation |
| `references/correctness-and-state.md` | Shared state, message passing, state modeling, floating point, exceptions, errors, and visibility |
| `references/testing-and-verification.md` | Required behavior tests, concrete tests, readable tests, CI, test data, and engineering evidence |
| `references/refactoring-and-removal.md` | Safe refactoring, characterization tests, Boy Scout rule, code removal, and debt handling |
| `references/tools-and-automation.md` | Coding standards, analysis tools, command line, IDE, version control, build, deploy, and bug trackers |
| `references/performance-and-systems.md` | Algorithms, data structures, profiling, databases, IPC, logging, bottlenecks, and estimation |
| `references/collaboration-and-process.md` | Code reviews, pairing, testers, customer ambiguity, documentation, humility, and team learning |
