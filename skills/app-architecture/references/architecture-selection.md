# Architecture Selection and Migration

Sources: Richards & Ford (Fundamentals of Software Architecture), Ford et al. (Software Architecture: The Hard Parts), Martin (Clean Architecture), Evans (Domain-Driven Design)

Covers: architecture style comparison, selection criteria, trade-off analysis, migration paths between styles, incremental adoption strategies, combining patterns, common mistakes in architecture selection.

## Architecture Style Comparison

### Overview Matrix

| Style | Domain Complexity Support | Testability | Simplicity | Team Scalability | Infrastructure Independence |
|---|---|---|---|---|---|
| Layered (N-tier) | Low | Low-Medium | High | Low | Low |
| Hexagonal (Ports/Adapters) | Medium-High | High | Medium | Medium | High |
| Clean Architecture | High | High | Medium | Medium-High | High |
| DDD Tactical | High | High | Low | High | High |
| Vertical Slices | Low-Medium | Medium-High | High | Medium | Medium |
| Modular Monolith | Medium-High | Medium-High | Medium | High | Medium |
| CQRS | Medium-High | Medium-High | Low-Medium | Medium | Medium |
| Event Sourcing | High | Medium | Low | Medium | Medium |

### Cost-Benefit Summary

| Style | Upfront Cost | Ongoing Maintenance Cost | Best Payoff Period |
|---|---|---|---|
| Layered | Very Low | Increases over time as complexity grows | Short-lived or simple apps |
| Hexagonal | Medium | Stable (boundaries prevent degradation) | Medium to long-lived apps |
| Clean Architecture | Medium-High | Stable to decreasing (easy to change internals) | Long-lived apps with evolving requirements |
| DDD Tactical | High | Decreasing (domain model captures complexity explicitly) | Complex domains, long-lived systems |
| Vertical Slices | Low | Low (features are independent) | Feature-heavy applications, rapid iteration |
| Modular Monolith | Medium | Stable (boundaries scale with team) | Multi-team codebases |
| CQRS | Medium-High | Medium (two models to maintain) | Read/write asymmetry |
| Event Sourcing | High | High (event evolution, projection maintenance) | Audit-critical, temporal query needs |

## Selection Decision Framework

### Step 1: Assess Domain Complexity

| Question | If Yes | If No |
|---|---|---|
| Are there complex business rules beyond validation? | Consider hexagonal, clean, or DDD | Layered or vertical slices |
| Do business rules change frequently? | Isolate domain (hexagonal/clean) | Layered acceptable |
| Is the domain the primary source of risk? | Invest in DDD tactical patterns | Focus architecture effort elsewhere |
| Are there multiple bounded contexts? | Modular monolith | Single-module approaches |

### Step 2: Assess Read/Write Patterns

| Question | If Yes | If No |
|---|---|---|
| Do reads and writes have very different shapes? | Consider CQRS | Unified model |
| Is read load much higher than write load (10:1+)? | CQRS with separate read store | Unified model |
| Do you need multiple read model shapes for different consumers? | CQRS with projections | Single model |

### Step 3: Assess Audit and Temporal Needs

| Question | If Yes | If No |
|---|---|---|
| Is a complete audit trail a legal/business requirement? | Evaluate event sourcing | Skip event sourcing |
| Do you need to reconstruct past states ("what was X at time T")? | Event sourcing adds value | Standard persistence |
| Can you accept eventual consistency on reads? | Event sourcing feasible | Event sourcing may cause friction |

### Step 4: Assess Team and Organizational Factors

| Question | If Yes | If No |
|---|---|---|
| Will multiple teams work in this codebase? | Modular monolith with enforced boundaries | Single-team approaches |
| Is the team experienced with DDD and event sourcing? | Advanced patterns feasible | Start simpler, evolve |
| Does the team value rapid feature delivery? | Vertical slices as default | Layered or clean by preference |

## Common Pattern Combinations

| Combination | When to Use | How They Compose |
|---|---|---|
| Clean + DDD | Complex domain with infrastructure independence | DDD entities/aggregates in clean architecture's domain circle |
| Modular Monolith + Vertical Slices | Multi-team, feature-heavy | Module boundaries at macro level, slices within each module |
| Modular Monolith + Clean | Multi-team, complex domains | Module per bounded context, clean architecture within each |
| CQRS + DDD | Complex domain + read/write asymmetry | DDD on command side, denormalized read models on query side |
| CQRS + Event Sourcing | Audit + temporal queries + read flexibility | Events as write model, projections as read models |
| Vertical Slices + Hexagonal | Feature-organized with infrastructure independence | Each slice uses ports/adapters for external dependencies |

## Migration Paths

### Layered to Hexagonal

1. Identify the most complex service class
2. Extract an interface for its data access dependency (create a port)
3. Move the existing data access code into an adapter that implements the port
4. Update the service to depend on the port interface, not the concrete implementation
5. Write a test using an in-memory adapter to verify the refactoring
6. Repeat for other services, one at a time

Cost: Low per step. No big-bang rewrite.

### Layered to Clean Architecture

1. Start with the hexagonal migration above (dependency inversion)
2. Identify domain logic in service classes
3. Extract domain logic into entity methods and value objects
4. Rename orchestration code as use cases (one per user intention)
5. Establish the layer structure and dependency rule
6. Add linting or build rules to enforce the dependency direction

### Monolith to Modular Monolith

1. Map the domain to bounded contexts (even informally)
2. Pick the most independent area of code (fewest dependencies on the rest)
3. Create a module with a public API facade
4. Move related code into the module's internal structure
5. Replace all external access to that code with calls through the public API
6. Add build-time or CI enforcement of the boundary
7. Repeat for the next most independent area

### Unified Model to CQRS

1. Identify a feature where read and write shapes diverge significantly
2. Create a separate read model (DTO or view) for that feature's queries
3. Create a query handler that reads from the database and returns the read model
4. Keep the write side unchanged
5. If reads need different optimization, introduce a denormalized read table updated by domain events
6. Extend to other features as needed

### Introducing Event Sourcing

1. Pick a single aggregate where audit trail provides clear business value
2. Implement an event store (use a library, not custom-built)
3. Modify the aggregate to emit events on state changes
4. Store events instead of (or in addition to) current state
5. Build at least one projection to prove the pattern works
6. Add snapshot support when event count per aggregate warrants it
7. Do NOT migrate the entire application; event sourcing is per-aggregate

## Architecture Selection Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Resume-driven architecture | Choosing patterns for learning, not for the problem | Evaluate trade-offs against actual requirements |
| Copy the big company | "Netflix uses event sourcing, so we should too" | Your scale, team, and constraints differ |
| Architecture astronaut | Abstracting everything before understanding the domain | Start concrete, abstract when patterns emerge |
| All-or-nothing adoption | "We must be fully DDD or not at all" | Apply patterns selectively where they add value |
| Ignoring team capability | Choosing event sourcing with a team that has never done it | Invest in training or choose a pattern the team can execute |
| Premature CQRS | Separating read/write models when they are nearly identical | Wait until read/write shapes actually diverge |
| Event sourcing everywhere | Applying event sourcing to CRUD-dominant areas | Reserve for aggregates with genuine audit or temporal needs |

## Incremental Adoption Strategy

The safest approach is incremental adoption — start simple, add structure as complexity demands it.

### Recommended Evolution Path

```
Phase 1: Layered or Vertical Slices
  Simple, fast to build, minimal ceremony.
  Appropriate for: new projects, unclear requirements, prototypes.

Phase 2: Extract Domain Model (Hexagonal/Clean)
  When business logic tangles with infrastructure.
  Trigger: difficulty testing without databases, logic in controllers.

Phase 3: Modular Boundaries
  When multiple teams or distinct business areas emerge.
  Trigger: merge conflicts across unrelated features, unclear ownership.

Phase 4: CQRS (if needed)
  When read and write patterns diverge significantly.
  Trigger: complex queries distort domain model, scaling asymmetry.

Phase 5: Event Sourcing (if needed)
  When audit trail or temporal queries become requirements.
  Trigger: regulatory compliance, "how did we get here" questions.
```

Each phase is entered only when the preceding level shows strain. Not every application reaches Phase 5 — most stabilize at Phase 2 or 3.

### Governance: Architecture Decision Records

Document each architecture decision as an ADR (Architecture Decision Record):

| Section | Content |
|---|---|
| Title | Short description of the decision |
| Status | Proposed, accepted, deprecated, superseded |
| Context | What forces are at play, what problem we face |
| Decision | What we decided and why |
| Consequences | What becomes easier, what becomes harder |

ADRs prevent re-litigating settled decisions and help new team members understand why the architecture is shaped the way it is.

### Fitness Functions

Automated tests that verify architectural constraints hold over time.

| Fitness Function | Verifies |
|---|---|
| No domain imports from infrastructure | Dependency rule is maintained |
| No cross-module direct database access | Module boundaries are respected |
| Cyclic dependency detection | No circular dependencies between modules |
| Layer access rules | Controllers do not bypass services to access repositories |
| Component coupling metrics | Coupling between modules stays below threshold |

Implement fitness functions as part of CI. They catch architectural drift before it becomes technical debt.

## Architecture Review Checklist

Use this checklist when evaluating or proposing an application architecture.

### Boundary Assessment

| Question | Red Flag If |
|---|---|
| Can you test business logic without a database? | No — domain depends on infrastructure |
| Can you replace the database without changing business logic? | No — persistence is coupled to domain |
| Can you explain what each module does in one sentence? | No — unclear boundaries, mixed responsibilities |
| Does each module have a single owner (person or team)? | No — shared ownership leads to diffuse responsibility |
| Are there circular dependencies between modules? | Yes — indicates unclear boundary placement |

### Complexity Assessment

| Question | Implication |
|---|---|
| How many files must change for a typical feature? | High number (5+) suggests wrong layer/module decomposition |
| How long does a new developer take to add a simple feature? | Long onboarding suggests over-engineering or poor documentation |
| Are there areas of code that no one wants to touch? | Indicates accumulated technical debt or unclear architecture |
| How often do changes in one area break another? | Frequently suggests insufficient boundary enforcement |

### Trade-Off Documentation

For each architectural decision, document:

| Element | Content |
|---|---|
| Decision | What pattern or approach was chosen |
| Context | What constraints, requirements, or forces led to this decision |
| Alternatives considered | What other approaches were evaluated |
| Consequences | What is now easier, what is now harder |
| Review date | When to revisit this decision |

### Technology-Specific Fitness Function Tools

| Language/Framework | Tool | Enforces |
|---|---|---|
| Java | ArchUnit | Layer dependencies, naming conventions, annotation placement |
| .NET | NetArchTest | Layer access rules, namespace dependency constraints |
| TypeScript | dependency-cruiser | Module import rules, circular dependency detection |
| TypeScript | eslint-plugin-import | Import ordering, no-restricted-paths |
| Python | import-linter | Layer contracts, forbidden import paths |
| Go | depguard | Package dependency rules |

### Signs You Need to Evolve Your Architecture

| Observation | Current Style | Consider Moving To |
|---|---|---|
| Business logic scattered across controllers and services | Layered | Hexagonal / Clean |
| Cannot test without database | Layered | Hexagonal (dependency inversion) |
| Service classes growing beyond 500 lines | Any | Vertical slices or use-case-per-class |
| Merge conflicts between unrelated features | Any single-module | Modular monolith |
| Reads and writes require very different data shapes | Unified model | CQRS |
| Audit requirements appear ("who changed what, when?") | State-based | Event sourcing (for affected aggregates) |
| Multiple teams stepping on each other | Monolith | Modular monolith with enforced boundaries |
| Need independent deployment per team | Modular monolith | Selective service extraction |
