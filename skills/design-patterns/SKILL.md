---
name: "@tank/design-patterns"
description: |
  JavaScript and TypeScript design patterns catalog for production applications.
  Covers GoF patterns adapted for modern JS/TS (Singleton, Observer, Factory,
  Strategy, Command, Mediator, Proxy, Decorator, Adapter, Iterator, State,
  Builder, Facade, Flyweight, Prototype, Chain of Responsibility), plus
  modern JS-native patterns (Module, Provider, Middleware/Pipeline, Repository,
  Unit of Work, Pub/Sub, Plugin/Hook). Each pattern includes intent, when to
  use, when NOT to use, TypeScript implementation, and real-world examples.
  Synthesizes Gamma et al. (Design Patterns), Freeman (Head First Design
  Patterns), Osmani (Learning JavaScript Design Patterns), Fowler (Patterns
  of Enterprise Application Architecture), Vlissides (Pattern Hatching), and
  modern JS/TS community patterns.

  Trigger phrases: "design pattern", "which pattern", "factory pattern",
  "singleton", "observer pattern", "strategy pattern", "decorator pattern",
  "adapter pattern", "proxy pattern", "command pattern", "state machine",
  "builder pattern", "mediator", "middleware pattern", "plugin system",
  "pub/sub", "event emitter", "chain of responsibility", "repository pattern",
  "data access pattern",
  "facade pattern", "flyweight", "prototype pattern", "provider pattern",
  "how to structure this", "pattern for this problem", "GoF in TypeScript",
  "creational pattern", "structural pattern", "behavioral pattern"
---

# Design Patterns

Structural solutions for recurring problems in JavaScript and TypeScript applications.

## Core Philosophy

1. **Patterns are tools, not goals.** Apply a pattern to solve a specific problem. If the problem does not exist, the pattern is overhead.
2. **Favor composition over inheritance.** JS/TS excels at object composition, closures, and higher-order functions. Most GoF inheritance hierarchies collapse into simpler functional forms.
3. **Match the pattern to the language.** A Java-style Singleton is an anti-pattern in JS modules. Adapt patterns to closures, first-class functions, Proxies, and ES module scope.
4. **Prefer the simplest pattern that solves the problem.** If a function suffices, do not introduce a class hierarchy. Escalate complexity only when requirements demand it.
5. **Name the pattern in your code.** When you use a pattern, name it explicitly (e.g., `UserFactory`, `RetryStrategy`). This communicates intent to future readers.

## Pattern Selection Decision Tree

| Problem Signal | Recommended Pattern | Category |
| --- | --- | --- |
| Need to create objects without specifying exact class | Factory / Abstract Factory | Creational |
| Complex object with many optional fields | Builder | Creational |
| Need exactly one shared instance | Module Scope / Singleton | Creational |
| Need to clone expensive-to-create objects | Prototype | Creational |
| Incompatible interface between two systems | Adapter | Structural |
| Need to add behavior without modifying source | Decorator | Structural |
| Simplify a complex subsystem API | Facade | Structural |
| Intercept or control access to an object | Proxy | Structural |
| Many similar objects consuming too much memory | Flyweight | Structural |
| One-to-many notifications on state change | Observer / Pub-Sub | Behavioral |
| Swap algorithms at runtime | Strategy | Behavioral |
| Encapsulate actions as objects (undo/redo, queues) | Command | Behavioral |
| Object behavior changes based on internal state | State | Behavioral |
| Decouple many-to-many communication | Mediator | Behavioral |
| Sequential processing with bail-out | Chain of Responsibility | Behavioral |
| Request/response pipeline with transforms | Middleware / Pipeline | Modern |
| Extensible system with third-party hooks | Plugin / Hook | Modern |
| Decouple data access from business logic | Repository | Modern |
| Cross-cutting shared context (React, DI) | Provider | Modern |

## Quick-Start: Common Problems

### "I need to create objects but the type varies at runtime"

1. Start with Factory Method for a single product family.
2. Escalate to Abstract Factory when multiple related families exist.
   -> See `references/creational-patterns.md`

### "I need to add logging/caching/retry without changing existing code"

1. Use Decorator for wrapping individual instances.
2. Use Proxy for transparent interception (access control, lazy loading).
   -> See `references/structural-patterns.md`

### "I have complex conditional logic that changes based on state"

1. Use Strategy if the algorithm is selected once per operation.
2. Use State if the object transitions between modes over its lifetime.
   -> See `references/behavioral-patterns.md`

### "I need a request pipeline (auth, validation, logging, handler)"

1. Use Middleware/Pipeline for linear request processing.
2. Use Chain of Responsibility if handlers can stop propagation.
   -> See `references/modern-patterns.md`

### "I am not sure which pattern fits my problem"

1. Consult the decision tree above.
2. Read the anti-patterns section below to rule out misapplications.
   -> See `references/pattern-selection-guide.md`

## Anti-Patterns: Pattern Misuse

| Misuse | Symptom | Remedy |
| --- | --- | --- |
| Singleton for dependency sharing | Hidden global state, untestable | Use Dependency Injection |
| Factory for one concrete type | Unnecessary indirection | Use `new` directly |
| Observer with 20+ listeners | Spaghetti event flow, debug hell | Use Mediator or explicit wiring |
| Decorator stacking 5+ layers | Unreadable, hard to debug | Flatten into a single composed function |
| Strategy with one strategy | Over-engineering | Use a plain function |
| Abstract Factory for 1 product | Premature abstraction | Use simple Factory Method |
| Builder for 2-field objects | Ceremony without benefit | Use plain constructor or object literal |

## Pattern Categories At a Glance

| Category | Patterns | Focus |
| --- | --- | --- |
| Creational | Factory, Abstract Factory, Builder, Prototype, Singleton | Object creation mechanisms |
| Structural | Adapter, Decorator, Facade, Proxy, Flyweight | Object composition and interface design |
| Behavioral | Observer, Strategy, Command, State, Mediator, Chain of Responsibility, Iterator | Communication and responsibility distribution |
| Modern JS/TS | Module, Provider, Middleware, Pipeline, Repository, Unit of Work, Pub/Sub, Plugin/Hook | Patterns native to JS/TS ecosystems |

## Reference Index

| File | Contents |
| --- | --- |
| `references/creational-patterns.md` | Factory, Abstract Factory, Builder, Prototype, Singleton — intent, JS/TS implementation, when to use, when not to use |
| `references/structural-patterns.md` | Adapter, Decorator, Facade, Proxy, Flyweight — intent, JS/TS implementation, real-world examples |
| `references/behavioral-patterns.md` | Observer, Strategy, Command, State, Mediator, Chain of Responsibility, Iterator — intent, JS/TS implementation |
| `references/modern-patterns.md` | Module, Provider, Middleware/Pipeline, Repository, Unit of Work, Pub/Sub, Plugin/Hook — JS/TS-native patterns |
| `references/pattern-selection-guide.md` | Decision matrices, pattern combination recipes, migration paths, complexity comparison, when-not-to-use tables |
