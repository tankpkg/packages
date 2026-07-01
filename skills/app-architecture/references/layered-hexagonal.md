# Layered and Hexagonal Architecture

Sources: Fowler (Patterns of Enterprise Application Architecture), Cockburn (Hexagonal Architecture), Richards & Ford (Fundamentals of Software Architecture), Martin (Clean Architecture)

Covers: traditional layered architecture, N-tier variants, when layers work and when they break, hexagonal architecture (ports and adapters), driving vs driven adapters, dependency inversion mechanics, testing advantages.

## Traditional Layered Architecture

### The Classic N-Tier Stack

| Layer | Responsibility | Typical Contents |
|---|---|---|
| Presentation | Accept user input, render output | Controllers, views, serializers, API endpoints |
| Business Logic | Domain rules, validation, orchestration | Services, domain objects, validators |
| Data Access | Persistence, external data retrieval | Repositories, ORM mappings, query objects |
| Database | Storage | Tables, indexes, stored procedures |

Request flow is strictly top-to-bottom: Presentation -> Business -> Data Access -> Database.

### When Layered Architecture Works

| Signal | Why Layers Fit |
|---|---|
| CRUD-dominant application | Layers map cleanly to read/validate/persist flow |
| Small team, low complexity | Easy to understand, minimal ceremony |
| Well-understood domain | Business logic is thin, no need for complex modeling |
| Rapid prototyping | Fastest path to working software |
| Framework provides layers naturally | Rails, Django, Spring MVC already impose this structure |

### When Layered Architecture Breaks

| Signal | Why Layers Fail |
|---|---|
| Business logic leaks into controllers | Layer discipline erodes under deadline pressure |
| Data access layer drives design | Database schema dictates domain model (tail wags dog) |
| Cross-cutting concerns span all layers | Logging, auth, caching bypass layer boundaries |
| Testing requires the database | Business logic cannot be tested without infrastructure |
| Changes cascade through all layers | Adding a field requires changes in 4+ files across layers |

### The Layer Leakage Problem

In practice, traditional layers create a gravitational pull toward the database. The ORM entity becomes the domain model. Business rules end up in SQL queries. The presentation layer formats data shaped by the database schema, not by user needs.

This happens because the dependency direction points downward — business logic depends on the data access layer, which depends on the database. The database becomes the center of the architecture.

## Hexagonal Architecture (Ports and Adapters)

### Core Concept

The application has an inside (business logic) and an outside (everything else). The inside defines ports — interfaces that describe what it needs. The outside provides adapters — implementations that satisfy those ports.

The critical inversion: the domain does not depend on infrastructure. Infrastructure depends on the domain by implementing its interfaces.

### Terminology

| Term | Definition | Example |
|---|---|---|
| Domain / Core | Business logic, entities, rules | `Order`, `calculateShipping()`, `applyDiscount()` |
| Port | Interface defined by the domain | `OrderRepository`, `PaymentGateway`, `NotificationSender` |
| Adapter | Implementation of a port | `PostgresOrderRepository`, `StripePaymentGateway` |
| Driving adapter | Initiates interaction with the domain (input) | HTTP controller, CLI handler, message consumer, test harness |
| Driven adapter | Called by the domain through a port (output) | Database adapter, email sender, external API client |

### Driving vs Driven Distinction

```
[Driving Adapter]  -->  [Port (Input)]  -->  [Domain Core]  -->  [Port (Output)]  -->  [Driven Adapter]
   HTTP Controller       OrderService          Order logic        OrderRepository        PostgreSQL
   CLI Command           interface             pure logic         interface              adapter
   Test Harness                                                   PaymentGateway         Stripe adapter
   Message Consumer                                               interface
```

Driving adapters call INTO the application. They know about the application's input ports.

Driven adapters are called BY the application. They implement the application's output ports. The domain defines what it needs; the adapter provides the how.

### Port Design Guidelines

| Guideline | Rationale |
|---|---|
| Name ports by domain intent, not technology | `OrderRepository` not `PostgresOrderStore` |
| Keep port interfaces small and focused | Follow Interface Segregation — split read and write ports if consumers differ |
| Ports belong to the domain, not infrastructure | The interface file lives in the domain module |
| Ports use domain types, not infrastructure types | Parameters and return types are domain objects, not ORM entities or DTOs |
| One port per external concern | Separate `PaymentGateway` from `NotificationSender` even if both are HTTP calls |

### Adapter Implementation Rules

| Rule | Explanation |
|---|---|
| Adapters import domain types | The adapter converts between external format and domain objects |
| Domain never imports adapters | Dependency points inward always |
| Adapters are replaceable | Swapping PostgreSQL for MongoDB means writing a new adapter, not changing domain code |
| Adapters handle translation | Convert HTTP requests to domain commands, ORM rows to domain entities |
| Test adapters are first-class | In-memory repository implementations enable fast, isolated domain testing |

### Dependency Inversion in Practice

Without inversion (traditional layered):
```
Controller --> Service --> Repository --> Database
  (each layer depends on the layer below)
```

With inversion (hexagonal):
```
Controller --> [Port: OrderService] <-- OrderServiceImpl
                                          |
                                          v
                                   [Port: OrderRepository] <-- PostgresOrderRepository
```

The `OrderServiceImpl` depends on the `OrderRepository` interface (defined in the domain). The `PostgresOrderRepository` implements that interface. The dependency arrow from `PostgresOrderRepository` points toward the domain, not away from it.

### Testing Advantages

| Scenario | Traditional Layered | Hexagonal |
|---|---|---|
| Test business logic | Requires database (or mock ORM) | Inject in-memory adapter, test pure logic |
| Test controller | Requires running service + database | Inject mock service (implements port) |
| Test integration | Full stack, slow, brittle | Replace one adapter at a time, test contract |
| Add new database | Rewrite service layer | Write new adapter, existing tests still pass |

The hexagonal approach makes the "test pyramid" achievable: many fast unit tests (domain + in-memory adapters), fewer integration tests (real adapters), minimal end-to-end tests.

### Common Implementation Patterns

#### Project Structure (TypeScript Example)

```
src/
  domain/
    model/           # Entities, value objects
    ports/            # Input and output port interfaces
    services/         # Domain services (pure business logic)
  application/
    use-cases/        # Application services / use case orchestrators
    dto/              # Input/output data structures for use cases
  infrastructure/
    persistence/      # Database adapters (implements repository ports)
    messaging/        # Message broker adapters
    external-apis/    # Third-party API adapters
  interface/
    http/             # Controllers, routes, middleware (driving adapter)
    cli/              # CLI commands (driving adapter)
    consumers/        # Message consumers (driving adapter)
```

#### Dependency Registration

Use dependency injection (constructor injection preferred) to wire adapters to ports at the composition root — the single place where the application is assembled.

```
// Composition root (application startup)
const orderRepo = new PostgresOrderRepository(dbConnection);
const paymentGateway = new StripePaymentGateway(stripeConfig);
const createOrder = new CreateOrderUseCase(orderRepo, paymentGateway);
const orderController = new OrderController(createOrder);
```

The composition root is the only place that knows about concrete implementations. Every other module works with interfaces.

### Hexagonal Architecture Mistakes

| Mistake | Problem | Fix |
|---|---|---|
| Defining ports in the infrastructure layer | Dependency direction violated | Ports live in the domain module |
| Using ORM entities as domain model | Domain coupled to persistence | Separate domain model, map in adapter |
| Skipping the port for "simple" cases | Incremental erosion of boundaries | Always define the interface, even if only one implementation exists |
| Too many ports for trivial operations | Over-engineering for CRUD | Use hexagonal for complex domains; layered is fine for simple cases |
| Adapter doing business logic | Logic bleeds into infrastructure | Adapters translate only; business rules stay in domain |

## Layered vs Hexagonal Decision

| Signal | Use Layered | Use Hexagonal |
|---|---|---|
| Domain complexity | Low (CRUD) | Medium to High |
| Need to swap infrastructure | Unlikely | Likely or testability demands it |
| Testing strategy | Integration tests are acceptable | Unit testing domain in isolation is critical |
| Team size | Small, same mental model | Growing, need enforced boundaries |
| Expected lifespan | Short/medium | Long-lived, will evolve |

Start with layered if the application is simple. Migrate toward hexagonal when you observe: business logic tangled with infrastructure, difficulty testing without databases, or the need to support multiple adapters for the same port.

## Hexagonal Architecture by Language

### Java / Kotlin (Spring)

```
src/main/java/com/example/orders/
  domain/
    model/        # Entities, value objects (plain POJOs, no Spring annotations)
    ports/
      inbound/    # Input port interfaces (OrderService)
      outbound/   # Output port interfaces (OrderRepository, PaymentGateway)
  application/
    services/     # Implements inbound ports, orchestrates domain
  infrastructure/
    adapters/
      inbound/
        rest/     # @RestController classes (driving adapter)
        messaging/ # @KafkaListener classes (driving adapter)
      outbound/
        persistence/ # @Repository JPA implementations (driven adapter)
        http/     # External API client implementations (driven adapter)
    config/       # Spring @Configuration, bean wiring (composition root)
```

Spring's `@Configuration` classes serve as the composition root. Define beans that wire adapters to ports.

### TypeScript (NestJS)

```
src/orders/
  domain/
    Order.ts                    # Entity (plain class, no decorators)
    OrderRepository.ts          # Port interface
  application/
    PlaceOrder.usecase.ts       # Use case implementation
  infrastructure/
    TypeOrmOrderRepository.ts   # Adapter (uses @InjectRepository)
  interface/
    OrderController.ts          # NestJS @Controller (driving adapter)
  orders.module.ts              # NestJS module (composition root)
```

NestJS modules act as the composition root. Use `providers` to bind port interfaces to adapter implementations.

### Python (FastAPI / Django)

```
src/orders/
  domain/
    models.py           # Entities, value objects (plain dataclasses)
    ports.py            # Port interfaces (Protocol classes or ABCs)
  application/
    use_cases.py        # Use case functions or classes
  infrastructure/
    sqlalchemy_repo.py  # SQLAlchemy adapter (implements repository port)
    stripe_gateway.py   # Stripe API adapter
  interface/
    routes.py           # FastAPI route handlers (driving adapter)
  container.py          # Dependency injection wiring
```

Use `dependency-injector` or manual constructor injection. Python's duck typing and Protocol classes provide port interfaces without framework coupling.

## Adapter Composition Patterns

### Multi-Adapter Selection at Runtime

A single port can have multiple adapters. Select the appropriate one based on configuration or context.

| Scenario | Adapters | Selection Mechanism |
|---|---|---|
| Environment-based | `PostgresRepo` (prod), `InMemoryRepo` (test) | Dependency injection profile |
| Feature flag | `OldPaymentGateway`, `NewPaymentGateway` | Feature flag evaluation at composition root |
| Regional | `UsEmailAdapter`, `EuEmailAdapter` | Configuration by deployment region |

### Decorator Pattern for Cross-Cutting Concerns

Wrap adapters with decorators that add behavior without modifying the adapter or the port interface.

```
interface OrderRepository {
  save(order: Order): void;
  findById(id: OrderId): Order | null;
}

class CachingOrderRepository implements OrderRepository {
  constructor(private inner: OrderRepository, private cache: Cache) {}

  findById(id: OrderId): Order | null {
    const cached = this.cache.get(id);
    if (cached) return cached;
    const order = this.inner.findById(id);
    if (order) this.cache.set(id, order);
    return order;
  }

  save(order: Order): void {
    this.inner.save(order);
    this.cache.invalidate(order.id);
  }
}
```

The caching concern is separate from both the domain and the persistence adapter. Stack multiple decorators: logging, caching, metrics — all transparent to the use case.
