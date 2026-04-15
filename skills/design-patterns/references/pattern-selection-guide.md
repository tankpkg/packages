# Pattern Selection Guide

Sources: Gamma et al. (Design Patterns), Osmani (Learning JavaScript Design Patterns), Fowler (Patterns of Enterprise Application Architecture), Vlissides (Pattern Hatching), 2020-2026 JS/TS community practice

Covers: Decision matrices for selecting the right pattern, pattern complexity ranking, combination recipes, migration paths between patterns, and comprehensive when-not-to-use tables.

## Pattern Selection by Problem Domain

### Object Creation Problems

| Problem | First Choice | Escalation | Avoid |
| --- | --- | --- | --- |
| Type varies at runtime | Factory Method | Abstract Factory (multiple families) | Builder (wrong domain) |
| Many optional config fields | Options Object | Builder (multi-step, validation) | Factory (wrong domain) |
| Need exact copies with tweaks | Spread/structuredClone | Prototype class (complex objects) | Factory (overhead) |
| Shared singleton resource | Module-scoped export | Class Singleton (lazy init) | Global variable |
| Test data generation | Factory function | Builder (complex test objects) | Manual construction |

### Interface and Composition Problems

| Problem | First Choice | Escalation | Avoid |
| --- | --- | --- | --- |
| Incompatible third-party API | Adapter function | Adapter class (stateful) | Modifying library source |
| Add behavior without modifying source | Higher-order function | Decorator class (interface compliance) | Subclassing |
| Complex subsystem, simple caller needs | Facade service | Facade module re-export | Exposing all internals |
| Control/intercept access | ES Proxy | Proxy class (typed interface) | Modifying target object |
| 10,000+ similar objects in memory | Flyweight + cache | Object pool | Premature optimization |

### Communication and Behavior Problems

| Problem | First Choice | Escalation | Avoid |
| --- | --- | --- | --- |
| React to state changes | Observer (EventEmitter) | Pub/Sub (cross-boundary) | Polling |
| Swap algorithm at runtime | Strategy function | Strategy class (stateful) | Switch statement |
| Undo/redo, command queuing | Command | Command + Memento (state snapshots) | Direct mutation |
| Object behavior varies by mode | State map (transitions) | State class (complex actions) | Nested if/else |
| Many-to-many communication | Mediator | Pub/Sub (decoupled, async) | Direct references |
| Sequential processing, bail-out | Chain of Responsibility | Middleware (bidirectional) | Monolithic handler |

### Architecture-Level Problems

| Problem | First Choice | Escalation | Avoid |
| --- | --- | --- | --- |
| Request pipeline (HTTP, CLI) | Middleware compose | Plugin system (lifecycle hooks) | Monolithic handler |
| Cross-cutting context (theme, auth) | Provider (Context/DI) | Module-scoped state | Prop drilling |
| Decouple data access | Repository interface | Repository + Unit of Work | Direct ORM in business logic |
| Third-party extensibility | Plugin/Hook system | Event-based plugins | Subclassing |
| Cross-service events | Pub/Sub broker | Event sourcing | Direct service calls |

## Complexity Ranking

Ranked from simplest to most complex. Start from the top; move down only when the simpler option is insufficient.

| Rank | Pattern | Lines of Code (typical) | When to Upgrade |
| --- | --- | --- | --- |
| 1 | Module (ES export) | 5-20 | Need runtime encapsulation |
| 2 | Strategy (function) | 10-30 | Need stateful strategy selection |
| 3 | Factory (function) | 15-40 | Need multiple product families |
| 4 | Observer (EventEmitter) | 20-50 | Need cross-boundary decoupling |
| 5 | Adapter (function) | 10-30 | Need stateful adaptation |
| 6 | Decorator (HOF) | 15-40 | Need interface-compliant wrapping |
| 7 | Facade (class) | 20-60 | Subsystem grows further |
| 8 | Chain of Responsibility | 20-50 | Need bidirectional flow (middleware) |
| 9 | Builder | 30-70 | Construction needs cross-field validation |
| 10 | Command | 30-80 | Need macro/composite commands |
| 11 | State | 40-100 | State count exceeds 5 (use state library) |
| 12 | Proxy (ES Proxy) | 20-60 | Interception points multiply |
| 13 | Mediator | 40-100 | Mediator grows too large (split by domain) |
| 14 | Middleware (compose) | 30-80 | Need lifecycle hooks (plugin system) |
| 15 | Repository + UoW | 60-150 | Multiple data sources, complex transactions |
| 16 | Plugin/Hook system | 50-150 | Hook surface area grows (document carefully) |
| 17 | Abstract Factory | 50-120 | Product families stabilize (rare in JS/TS) |
| 18 | Pub/Sub broker | 40-100 | Need persistence, replay (use message queue) |

## Pattern Combination Recipes

Patterns frequently work together. These combinations solve common architectural needs.

### Factory + Strategy
**Problem:** Create objects that behave differently based on type, and each type has swappable algorithms.
```
PaymentFactory.create("stripe") -> StripePayment
  uses RetryStrategy | FailFastStrategy
```

### Repository + Unit of Work
**Problem:** Multiple entities must be persisted atomically.
```
UnitOfWork tracks changes across UserRepository + OrderRepository
  -> commit() wraps all in a single transaction
```

### Observer + Command
**Problem:** React to events and support undo.
```
UI emits events (Observer)
  -> each event creates a Command
  -> CommandHistory enables undo/redo
```

### Middleware + Strategy
**Problem:** Request pipeline where individual steps are swappable.
```
Middleware pipeline: [auth, rateLimit, handler]
  auth uses Strategy: JWTAuth | APIKeyAuth | OAuth
```

### Facade + Adapter
**Problem:** Simplify a complex subsystem that includes incompatible third-party APIs.
```
PaymentFacade
  -> StripeAdapter (adapts Stripe SDK)
  -> PayPalAdapter (adapts PayPal SDK)
  -> exposes: charge(), refund(), subscribe()
```

### Factory + Decorator
**Problem:** Create objects and then wrap them with cross-cutting concerns.
```
Factory creates Logger
  -> Decorator adds timestamp prefix
  -> Decorator adds log-level filtering
```

### Provider + Repository
**Problem:** Share a repository instance across a component tree.
```
RepositoryProvider wraps components
  -> useRepository() hook accesses the shared instance
  -> swappable: InMemoryRepo (tests) vs PostgresRepo (prod)
```

## Migration Paths

When a pattern outgrows its usefulness, migrate to the next level.

| From | To | Signal |
| --- | --- | --- |
| Switch/if-else on type | Factory Method | 3+ branches, adding new types |
| Factory Method | Abstract Factory | Multiple related product families |
| Simple boolean flag | State pattern | 3+ states with different behaviors |
| Direct function calls | Observer | 3+ callers need notification |
| Observer | Pub/Sub | Cross-module or cross-service boundary |
| Observer | Mediator | Many-to-many communication causing cycles |
| Callback nesting | Middleware pipeline | 3+ sequential processing steps |
| Middleware | Plugin/Hook | Need lifecycle events, not just request flow |
| Direct DB calls | Repository | Business logic mixed with queries |
| Repository | Repository + UoW | Multi-entity transactions required |
| Inheritance hierarchy | Strategy + Composition | Subclass explosion, diamond problems |
| God class | Facade + extracted services | Class exceeds 300 lines |

## When NOT to Use: Comprehensive Table

| Pattern | Do NOT Use When | Use Instead |
| --- | --- | --- |
| Singleton | Need testability, multiple instances in tests | Dependency Injection |
| Factory Method | Only one concrete type ever | Direct `new` or function call |
| Abstract Factory | One product type, families never change | Factory Method |
| Builder | Object has 1-3 fields, no validation | Constructor or options object |
| Prototype | Objects are cheap to create | Direct construction |
| Adapter | You control both interfaces | Change the source interface |
| Decorator | Stacking 5+ layers | Compose into single function |
| Facade | Callers need full subsystem access | Export subsystem directly |
| Proxy | Hot path with nanosecond budget | Direct access |
| Flyweight | Fewer than 1,000 instances | Regular objects |
| Observer | One subscriber | Direct callback |
| Strategy | One algorithm, never changes | Inline the logic |
| Command | No undo, no queuing, no logging | Direct function call |
| State | Two states with trivial behavior | Boolean flag |
| Mediator | Two components communicating | Direct reference |
| Chain of Resp. | One handler always processes | Direct dispatch |
| Iterator | Standard array/map traversal | Built-in iterators |
| Middleware | One processing step | Single function |
| Plugin/Hook | No external consumers | Internal function calls |
| Repository | Simple CRUD, no business logic | Direct ORM usage |
| Pub/Sub | Same-module communication | Observer |

## Pattern Smell Detection

Signs that a pattern is misapplied:

| Smell | Likely Cause | Fix |
| --- | --- | --- |
| Pattern adds code but no flexibility | Premature application | Remove pattern, use direct code |
| Cannot explain why pattern is here | Cargo culting | Delete and simplify |
| Pattern name not in any class/function | Pattern is invisible to readers | Name it explicitly or remove |
| 3+ patterns interacting in one file | Over-engineering | Flatten; keep at most 2 patterns per module |
| Tests require elaborate mocking of pattern infrastructure | Pattern is too heavy | Simplify; patterns should make testing easier, not harder |
| Adding a new feature requires touching pattern boilerplate | Pattern fights the change | Wrong pattern for the problem; reassess |
| Team members cannot explain the pattern | Knowledge silo | Simplify or document; if neither helps, remove |

## The Pattern Application Checklist

Before introducing any pattern, answer:

1. **Is the problem real?** Have I seen it cause bugs, confusion, or duplication? (Not hypothetical.)
2. **Is this the simplest pattern that solves it?** Consult the complexity ranking above.
3. **Can I name it?** The class/function/module should contain the pattern name.
4. **Will it survive 3 requirement changes?** If the pattern fights likely changes, it is the wrong one.
5. **Can a junior understand it in 5 minutes?** If not, the complexity cost exceeds the benefit.
6. **Does it make testing easier?** Patterns should improve testability. If mocking becomes harder, reconsider.

All YES: apply the pattern. Any NO: defer or choose a simpler alternative.

## Pattern-to-Framework Mapping

Common frameworks already implement these patterns. Recognize them to avoid re-inventing.

| Framework / Library | Built-in Pattern | Do NOT Rebuild |
| --- | --- | --- |
| React Context | Provider | Custom prop-drilling solution |
| React `useReducer` | State + Command | Manual state machine class |
| Redux / Zustand | Mediator + Observer + Command | Custom event bus for state |
| Express / Koa / Hono | Middleware (Chain of Resp.) | Custom request pipeline |
| Prisma / TypeORM | Repository + Unit of Work | Manual SQL builder |
| Webpack / Vite | Plugin/Hook (Tapable) | Custom build extensibility |
| RxJS | Observer + Iterator + Strategy | Custom reactive streams |
| InversifyJS / tsyringe | Provider (DI Container) | Manual service locator |
| Zod / Yup | Builder (schema builder) | Custom validation chain |
| TanStack Query | Repository + Observer + Cache | Manual fetch + cache layer |

## Refactoring Toward Patterns

Patterns are not introduced upfront. They emerge through refactoring when complexity demands them.

### Step-by-Step: Switch Statement to Strategy

1. Identify the switch/if-else that branches on type or mode.
2. Extract each branch body into a standalone function with the same signature.
3. Create a `Record<string, Function>` mapping type keys to handler functions.
4. Replace the switch with a lookup: `strategies[type](args)`.
5. Name the type: `type PricingStrategy = (price: number, qty: number) => number`.

### Step-by-Step: God Function to Facade

1. Identify the 200+ line function doing multiple unrelated things.
2. Group lines by concern (validation, transformation, persistence, notification).
3. Extract each group into a separate service class or module.
4. Create a Facade function that calls the extracted services in sequence.
5. The original call site now calls the Facade — same API, decomposed internals.

### Step-by-Step: Callback Spaghetti to Observer

1. Identify functions that accept multiple callbacks or notify multiple callers.
2. Create a typed EventEmitter with named events.
3. Replace callback parameters with event subscriptions.
4. Move notification logic from the source to the emitter: `emitter.emit("change", data)`.
5. Subscribers register independently: `emitter.on("change", handler)`.

### Step-by-Step: Prop Drilling to Provider

1. Identify data passed through 3+ component levels without being used in intermediate levels.
2. Create a Context with `createContext<T>(defaultValue)`.
3. Create a Provider component that wraps the subtree needing access.
4. Create a custom hook `useX()` that calls `useContext` with a null-check.
5. Replace all intermediate prop passing with direct `useX()` calls at consumption points.

### Step-by-Step: Direct DB Calls to Repository

1. Identify business logic files that import the ORM or database client directly.
2. Define an interface with the query methods the business logic actually uses.
3. Create a class implementing that interface with the current ORM calls.
4. Replace all direct ORM imports in business logic with the interface.
5. Inject the implementation via constructor or Provider.
6. Create an `InMemoryRepository` implementing the same interface for tests.

## Patterns and Testing

Patterns should make testing easier. If they make it harder, the pattern is misapplied.

| Pattern | Testing Benefit | Testing Approach |
| --- | --- | --- |
| Factory | Swap production factory for test factory | Inject factory function |
| Strategy | Test each algorithm in isolation | Unit test each strategy function |
| Repository | Swap real DB for in-memory implementation | Interface-based injection |
| Observer | Verify events emitted with correct data | Subscribe in test, assert on callback |
| Command | Test execute and undo independently | Unit test each command |
| Middleware | Test each middleware in isolation | Call with mock context and next |
| Decorator | Test wrapped and unwrapped behavior | Test base, then test decorated version |
| State | Test each state and transition | Assert state transitions given actions |
| Adapter | Test adaptation logic without real service | Mock the external interface |
| Provider | Override context value in test tree | Wrap test component with test Provider |
| Plugin | Test plugin in isolation with mock hooks | Call plugin.setup with stub hooks |
