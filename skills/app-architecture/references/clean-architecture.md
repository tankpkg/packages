# Clean Architecture

Sources: Martin (Clean Architecture), Cockburn (Hexagonal Architecture), Palermo (Onion Architecture), Richards & Ford (Fundamentals of Software Architecture)

Covers: concentric circle model, the dependency rule, entities layer, use cases layer, interface adapters layer, frameworks and drivers layer, practical project structure, mapping between layers, common implementation decisions.

## The Concentric Circle Model

Clean architecture organizes code in concentric rings. Inner rings know nothing about outer rings. Dependencies point strictly inward.

```
+-----------------------------------------------------------+
|  Frameworks & Drivers (outermost)                         |
|  +-----------------------------------------------------+ |
|  |  Interface Adapters                                  | |
|  |  +-----------------------------------------------+  | |
|  |  |  Application / Use Cases                      |  | |
|  |  |  +-----------------------------------------+  |  | |
|  |  |  |  Entities / Domain (innermost)          |  |  | |
|  |  |  +-----------------------------------------+  |  | |
|  |  +-----------------------------------------------+  | |
|  +-----------------------------------------------------+ |
+-----------------------------------------------------------+
```

## The Dependency Rule

All dependency arrows point toward the center of the diagram. Code in any given ring may only reference code in the same ring or a ring closer to the center — never outward toward infrastructure or delivery mechanisms.

| Inner Circle | Can Reference | Cannot Reference |
|---|---|---|
| Entities | Only other entities, language primitives | Use cases, adapters, frameworks |
| Use Cases | Entities, port interfaces | Adapters, frameworks, specific DB/API |
| Interface Adapters | Use cases, entities | Specific framework internals |
| Frameworks & Drivers | Anything inward | N/A (outermost ring) |

Data crosses boundaries through simple data structures (DTOs), not by passing framework objects or ORM entities inward.

## Layer Details

### Entities (Innermost Circle)

Core domain concepts that exist independently of any particular application. These rules belong to the business itself and would remain valid even if the software were rewritten from scratch or replaced entirely.

| Component | Purpose | Example |
|---|---|---|
| Entity | Identity + behavior + business rules | `Order` with `addItem()`, `calculateTotal()` |
| Value Object | Immutable, identity-less, equality by value | `Money`, `EmailAddress`, `DateRange` |
| Domain Event | Record of something significant that happened | `OrderPlaced`, `PaymentReceived` |
| Business Rule / Policy | Encapsulated rule, often a function or strategy | `DiscountPolicy`, `ShippingCalculator` |

Entities have zero dependencies on frameworks, databases, or external libraries. They use only the programming language and standard library.

### Use Cases (Application Business Rules)

Application-specific business rules. Orchestrate the flow of data to and from entities. Each use case represents a single user intention.

| Principle | Explanation |
|---|---|
| One class per use case | `CreateOrder`, `CancelOrder`, `GetOrderDetails` — not one `OrderService` with all methods |
| Defines input/output ports | Declares what data it needs (input DTO) and what it returns (output DTO) |
| Orchestrates, does not implement | Calls entity methods and port interfaces; contains no SQL, HTTP, or framework code |
| Owns the transaction boundary | Decides when a unit of work begins and commits |

#### Use Case Structure

```
class CreateOrderUseCase {
  constructor(
    private orderRepo: OrderRepository,      // output port
    private paymentGateway: PaymentGateway,   // output port
    private eventPublisher: EventPublisher     // output port
  ) {}

  execute(input: CreateOrderInput): CreateOrderOutput {
    // 1. Validate input
    // 2. Create domain objects (entities, value objects)
    // 3. Execute business logic (entity methods)
    // 4. Persist through port (orderRepo.save)
    // 5. Publish domain events (eventPublisher.publish)
    // 6. Return output DTO
  }
}
```

### Interface Adapters

Bridge between the domain core and the outside world. Each adapter translates between the data shapes that use cases work with (DTOs, domain objects) and the shapes that a specific technology expects (HTTP payloads, SQL rows, gRPC messages).

| Adapter Type | Direction | Responsibility |
|---|---|---|
| Controller | Inward (driving) | Convert HTTP request to use case input DTO, call use case |
| Presenter | Outward (from use case) | Convert use case output DTO to view model for response |
| Gateway implementation | Outward (driven) | Implement output port using a specific technology |
| Repository implementation | Outward (driven) | Implement repository port with specific database |
| Mapper | Both | Convert between domain entities and persistence/API models |

### Frameworks and Drivers (Outermost Circle)

Specific technology choices: web framework (Express, Spring, Django), ORM (Prisma, Hibernate, SQLAlchemy), message broker client, HTTP client library.

This layer is where all the details go. Keep it thin — it should contain only glue code that wires the framework to the interface adapters.

| Principle | Implication |
|---|---|
| Frameworks are details | The application works conceptually without any specific framework |
| Keep framework code at the edge | Controller annotations, ORM decorators, route definitions — all outermost |
| Framework lock-in is acceptable here | Inner layers are protected from framework changes |

## Practical Project Structure

### Feature-First (Recommended for Most Projects)

```
src/
  features/
    orders/
      domain/
        Order.ts              # Entity
        OrderItem.ts           # Value object
        OrderRepository.ts     # Port (interface)
        OrderPlaced.ts         # Domain event
      application/
        CreateOrder.ts         # Use case
        CancelOrder.ts         # Use case
        GetOrderDetails.ts     # Query use case
        dto/
          CreateOrderInput.ts
          CreateOrderOutput.ts
      infrastructure/
        PostgresOrderRepository.ts    # Adapter
        OrderMapper.ts                # Entity <-> DB row mapping
      interface/
        OrderController.ts            # HTTP driving adapter
        OrderRoutes.ts                # Framework routing
    payments/
      domain/ ...
      application/ ...
      infrastructure/ ...
      interface/ ...
  shared/
    domain/
      Money.ts                # Shared value objects
      DomainEvent.ts          # Base event type
    infrastructure/
      EventPublisher.ts       # Shared infrastructure
  main.ts                     # Composition root
```

### Layer-First (Simpler, for Small Applications)

```
src/
  domain/
    entities/
    value-objects/
    ports/
    events/
  application/
    use-cases/
    dto/
  infrastructure/
    repositories/
    gateways/
    mappers/
  interface/
    http/
    cli/
  main.ts
```

Feature-first scales better for larger applications. Layer-first is simpler for small ones.

## Crossing Boundaries: Data Flow

### Inward (Request)

```
HTTP Request
  -> Controller (parse, validate format)
    -> Input DTO (plain data object)
      -> Use Case (orchestrate business logic)
        -> Entity methods (execute rules)
```

### Outward (Response)

```
Entity state
  -> Use Case (assemble output)
    -> Output DTO (plain data object)
      -> Presenter/Controller (format response)
        -> HTTP Response
```

### Persistence Mapping

The domain entity is NOT the ORM entity. Map between them:

```
Domain Entity  <-->  Mapper  <-->  Persistence Model (ORM entity / DB row)
```

| Rule | Why |
|---|---|
| Domain entity has no persistence annotations | ORM decorators create a dependency on the framework |
| Persistence model can differ from domain model | Schema optimizations (denormalization) should not affect domain design |
| Mapper handles conversion | Explicit, testable, keeps both models independent |

In simple cases (no schema/domain mismatch), you may use the domain entity directly for persistence as a pragmatic shortcut. Document this as a conscious trade-off, not the default.

## Common Implementation Decisions

### When to Simplify

Not every endpoint needs all four circles. Apply judgment:

| Scenario | Pragmatic Approach |
|---|---|
| Simple CRUD with no business logic | Controller -> Repository directly (skip use case layer) |
| Read-only query | Query handler that reads from DB and returns DTO — no domain entity involvement |
| Single implementation of a port | Still define the interface; cost is low, flexibility and testability benefit is high |
| Tiny application (< 5 endpoints) | Layer-first structure; avoid feature-first overhead |

### Error Handling Across Boundaries

| Layer | Error Type | Example |
|---|---|---|
| Domain | Domain exception (business rule violation) | `InsufficientFundsError`, `InvalidOrderStateError` |
| Application | Application exception (workflow failure) | `OrderNotFoundError`, `PaymentDeclinedError` |
| Interface adapter | Translate to appropriate external format | Domain error -> HTTP 422, not found -> HTTP 404 |
| Infrastructure | Wrap technical errors, do not leak upward | Database timeout -> `RepositoryUnavailableError` |

### Dependency Injection Approach

| Approach | When to Use |
|---|---|
| Constructor injection | Default. Explicit, testable, compile-time safe |
| Framework DI container | Large applications where manual wiring is tedious |
| Composition root (manual wiring) | Small-medium apps, maximum control and transparency |

## Clean Architecture Mistakes

| Mistake | Problem | Fix |
|---|---|---|
| Skipping the dependency rule "just this once" | Erosion is incremental, eventually the domain depends on everything | Enforce with linting rules or module access restrictions |
| Use case returning domain entity | Outer layers coupled to internal structure | Always return DTOs from use cases |
| Fat use cases with business logic | Use case becomes a god class | Push logic into entities and domain services |
| One-to-one entity/table mapping forced | Domain model mirrors database schema | Design domain model first, map to schema independently |
| No tests for the domain layer | Defeats the primary benefit of clean architecture | Domain tests should be the majority of your test suite |
