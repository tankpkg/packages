---
name: "@tank/app-architecture"
description: |
  Application-level architecture patterns for structuring code within a single
  service or monolith. Covers layered architecture (traditional N-tier, when
  it works, when it breaks), hexagonal architecture / ports and adapters
  (dependency inversion, port/adapter taxonomy, testing benefits), clean
  architecture (concentric circles, dependency rule, use cases, entities,
  interface adapters), DDD tactical patterns (entities, value objects,
  aggregates, domain events, repositories, domain services, application
  services), CQRS (command/query separation at application level, read models,
  eventual consistency), event sourcing (event store, projections, snapshots,
  when to use vs avoid), modular monolith (module boundaries, internal APIs,
  shared kernel), vertical slice architecture (feature-organized code,
  MediatR-style), and feature flag architectural support.

  Synthesizes Martin (Clean Architecture), Evans (Domain-Driven Design),
  Vernon (Implementing DDD), Cockburn (Hexagonal Architecture), Young
  (CQRS Journey), Ford & Richards (Fundamentals of Software Architecture,
  Software Architecture: The Hard Parts), Fowler (Patterns of Enterprise
  Application Architecture).

  Trigger phrases: "app architecture", "application architecture",
  "hexagonal architecture", "ports and adapters", "clean architecture",
  "onion architecture", "layered architecture", "n-tier", "domain-driven
  design", "DDD", "aggregate", "value object", "domain event", "DDD repository",
  "data access layer", "CQRS", "event sourcing", "modular monolith", "vertical slice",
  "how to structure my app", "project structure", "folder structure",
  "dependency rule", "dependency inversion", "use case", "application service",
  "domain service", "anemic domain model", "rich domain model",
  "feature flags architecture", "trunk-based development",
  "where does this code go", "which architecture pattern"
---

# Application Architecture

## Core Philosophy

1. **Dependencies point inward.** Business logic never depends on frameworks, databases, or HTTP. Infrastructure depends on the domain, never the reverse.
2. **Boundaries are the architecture.** The placement and enforcement of module boundaries matters more than which pattern name you pick.
3. **Match complexity to the problem.** CRUD apps do not need hexagonal architecture. Complex domains do not survive without explicit modeling. Select the lightest pattern that controls your actual complexity.
4. **Make the implicit explicit.** Use cases, domain rules, and module contracts should be readable in code, not buried in service classes or controllers.
5. **Delay distribution, enforce modularity now.** A well-bounded modular monolith can be split into services later. Poorly structured microservices cannot be easily merged back.

## Quick-Start: Common Problems

### "How should I structure this app?"

1. Is the domain complex with rich business rules? -> Clean/Hexagonal + DDD tactical patterns
2. Is it mostly CRUD with some validation? -> Layered architecture or vertical slices
3. Do reads and writes have very different shapes/loads? -> Consider CQRS
4. Will multiple teams work in this codebase? -> Modular monolith with enforced boundaries
5. Is it a greenfield with unclear requirements? -> Vertical slices, refactor toward hexagonal as patterns emerge
-> See `references/architecture-selection.md`

### "Where does this code go?"

1. Does it express a business rule independent of any use case? -> Domain layer (entity/value object)
2. Does it orchestrate a user-facing workflow? -> Application layer (use case / application service)
3. Does it translate between external format and internal model? -> Interface adapter (controller, presenter, mapper)
4. Does it interact with a database, API, or file system? -> Infrastructure layer (driven adapter / repository impl)
-> See `references/clean-architecture.md`

### "Should I use DDD here?"

1. Is the domain the primary source of complexity? -> Yes, DDD tactical patterns add value
2. Is the complexity mostly technical (integrations, performance)? -> No, DDD adds overhead without payoff
3. Can you access domain experts regularly? -> Essential for DDD to work
4. Is the team willing to invest in a ubiquitous language? -> Required precondition
-> See `references/ddd-tactical-patterns.md`

### "My codebase is a big ball of mud"

1. Identify the highest-value bounded context -> Draw a boundary around it first
2. Define an explicit interface (internal API) for that module -> No direct database access from outside
3. Move related code inside the boundary -> One module at a time
4. Enforce the boundary with build tooling or access rules -> Prevent regression
-> See `references/modular-monolith-vertical-slices.md`

## Architecture Style Selection

| Domain Complexity | Read/Write Asymmetry | Team Size | Recommendation |
|---|---|---|---|
| Low (CRUD-dominant) | Low | Any | Layered architecture or vertical slices |
| Medium (some business rules) | Low | Small | Clean architecture (simplified) |
| Medium | High | Any | Clean architecture + CQRS |
| High (complex domain logic) | Low | Any | Hexagonal/Clean + DDD tactical patterns |
| High | High | Any | Hexagonal/Clean + DDD + CQRS |
| Any | Any | Multiple teams, one codebase | Modular monolith with enforced boundaries |
| High + audit/compliance needs | High | Any | Event sourcing + CQRS (evaluate carefully) |

## Dependency Direction Quick Reference

| Layer | Depends On | Never Depends On |
|---|---|---|
| Domain (entities, value objects) | Nothing | Application, infrastructure, UI |
| Application (use cases) | Domain | Infrastructure, UI |
| Interface adapters (controllers, presenters) | Application, domain | Infrastructure details |
| Infrastructure (DB, APIs, frameworks) | Application, domain (implements interfaces) | Nothing restricts it inward |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Anemic domain model | Entities are data bags, logic scattered in services | Move behavior into entities/value objects |
| Big ball of mud | No boundaries, everything depends on everything | Identify bounded contexts, extract modules |
| Over-layering | 6 layers for a CRUD endpoint, pass-through delegation | Remove layers that add no logic; vertical slices for simple features |
| Framework coupling | Domain logic imports Spring/Express/Django | Invert dependencies; domain defines interfaces, infrastructure implements |
| Shared database across modules | Modules coupled through tables, no clear ownership | Each module owns its tables, communicate through APIs/events |
| God service | One application service with 50 methods | Split by use case; one class per use case or feature |
| Leaking domain logic | Validation and business rules in controllers | Push rules into domain objects, use application services to orchestrate |

## Reference Index

| File | Contents |
|------|----------|
| `references/layered-hexagonal.md` | Traditional layered architecture (N-tier, when it works, when it breaks), hexagonal architecture (ports, adapters, driven/driving distinction), dependency inversion mechanics |
| `references/clean-architecture.md` | Clean architecture concentric circles, dependency rule, entities, use cases, interface adapters, frameworks layer, practical project structure |
| `references/ddd-tactical-patterns.md` | Entities, value objects, aggregates, aggregate roots, domain events, repositories, domain services, application services, factories |
| `references/cqrs-event-sourcing.md` | CQRS at application level, read/write model separation, eventual consistency, event sourcing fundamentals, event store, projections, snapshots, when to use vs avoid |
| `references/modular-monolith-vertical-slices.md` | Module boundary enforcement, internal APIs, shared kernel, inter-module communication, vertical slice architecture, feature-organized code, MediatR patterns |
| `references/architecture-selection.md` | Architecture style comparison matrix, migration paths between styles, feature flags as architectural enabler, trunk-based development support, incremental adoption strategies |
