# Modular Monolith and Vertical Slice Architecture

Sources: Ford et al. (Software Architecture: The Hard Parts), Richards & Ford (Fundamentals of Software Architecture), Palermo (Vertical Slice Architecture), Bogard (MediatR and vertical slices), Evans (Domain-Driven Design)

Covers: modular monolith structure, module boundary enforcement, internal APIs, shared kernel, inter-module communication, vertical slice architecture, feature-organized code, MediatR/Mediator patterns, comparing modular monolith with microservices, migration paths.

## Modular Monolith

### Core Concept

A single deployable unit with strict internal module boundaries. Each module encapsulates a bounded context or business capability. Modules communicate through well-defined internal APIs, not by reaching into each other's internals.

The modular monolith captures the organizational benefits of microservices (clear ownership, encapsulation, independent development) without the operational complexity of distribution (network failures, service discovery, distributed transactions).

### Module Structure

| Component | Purpose | Example |
|---|---|---|
| Public API | The only way other modules interact with this module | `OrderModule.placeOrder(command)`, `OrderModule.getOrderStatus(id)` |
| Internal domain | Entities, value objects, business rules — not accessible from outside | `Order`, `OrderItem`, `OrderStatus` |
| Internal persistence | Module's database tables or schema — not queried by other modules | `orders` table, `order_items` table |
| Internal infrastructure | Module-specific adapters, integrations | Module's email sender, payment adapter |

### Module Boundary Enforcement

| Mechanism | How | Strength |
|---|---|---|
| Package/namespace visibility | Use language access modifiers (`internal` in C#, package-private in Java) | Medium — enforced by compiler |
| Build module boundaries | Separate build modules/projects per domain module | Strong — compile-time enforcement |
| ArchUnit / dependency-cruiser | Automated tests that verify dependency rules | Strong — CI-enforced |
| Linting rules | Custom ESLint/TSLint rules that block cross-module imports | Medium — enforceable in CI |
| Code review conventions | Team agreement on import rules | Weak — relies on human discipline |

Prefer compiler-enforced or CI-enforced boundaries. Convention-only enforcement degrades under deadline pressure.

### Practical Project Structure

```
src/
  modules/
    orders/
      public/                     # Module's public API
        OrderModule.ts             # Facade: the ONLY entry point for other modules
        OrderDTO.ts                # Data types exposed to other modules
      internal/                    # Hidden from other modules
        domain/
          Order.ts
          OrderItem.ts
          OrderRepository.ts
        application/
          PlaceOrder.ts
          CancelOrder.ts
        infrastructure/
          PostgresOrderRepository.ts
    payments/
      public/
        PaymentModule.ts
        PaymentDTO.ts
      internal/
        domain/ ...
        application/ ...
        infrastructure/ ...
    shipping/
      public/ ...
      internal/ ...
  shared/                          # Shared kernel
    types/
      Money.ts
      Address.ts
    events/
      DomainEvent.ts
      EventBus.ts
  main.ts                          # Composition root, wires modules together
```

### Inter-Module Communication

| Pattern | Mechanism | Coupling | When to Use |
|---|---|---|---|
| Direct method call via public API | Module A calls `OrderModule.getOrderStatus(id)` | Synchronous, tightest | Query another module's data, low latency needed |
| In-process events (event bus) | Module A publishes `OrderPlaced`, Module B subscribes | Async, loose | Side effects: send email, update read model, trigger next step |
| Shared database view (read only) | Module B reads a view/table that Module A maintains | Data coupling | Reporting, dashboards (pragmatic but watch for schema coupling) |

#### Event Bus for Module Communication

```
// orders module publishes:
eventBus.publish(new OrderPlaced({ orderId, customerId, total }));

// payments module subscribes:
eventBus.subscribe(OrderPlaced, (event) => {
  paymentModule.initiatePayment(event.orderId, event.total);
});
```

Events decouple modules. The orders module does not know or care that the payments module exists. Adding new consumers requires no changes to the publisher.

### Shared Kernel

A small set of types, interfaces, or utilities shared across all modules.

| Include in Shared Kernel | Exclude from Shared Kernel |
|---|---|
| Fundamental value objects (`Money`, `Address`, `DateRange`) | Domain-specific entities |
| Base domain event type | Module-specific events (those belong in the publishing module) |
| Common error types | Business logic of any kind |
| Event bus interface | Module-specific persistence |

Keep the shared kernel minimal. It is a coupling point — changes to it affect all modules.

### Database Strategy

| Strategy | Description | Trade-Off |
|---|---|---|
| Shared database, separate schemas | Each module owns a schema; no cross-schema queries | Moderate isolation; same DB instance |
| Shared database, separate tables | Each module owns tables, enforced by convention or tooling | Weakest isolation; easy to violate |
| Separate databases per module | Each module gets its own database | Strongest isolation; operational overhead |

For most modular monoliths, shared database with separate schemas provides a good balance. Enforce that modules only access their own schema.

## Vertical Slice Architecture

### Core Concept

Organize code by feature (vertical slice), not by technical layer (horizontal). Each slice contains everything needed for one feature: handler, validation, data access, response shaping.

```
Traditional (horizontal layers):
  Controllers/     -> OrderController, ProductController, UserController
  Services/        -> OrderService, ProductService, UserService
  Repositories/    -> OrderRepository, ProductRepository, UserRepository

Vertical slices:
  Features/
    PlaceOrder/    -> PlaceOrderHandler, PlaceOrderValidator, PlaceOrderQuery
    CancelOrder/   -> CancelOrderHandler, CancelOrderValidator
    GetOrderList/  -> GetOrderListHandler, GetOrderListQuery
```

### Why Vertical Slices

| Problem with Horizontal Layers | Vertical Slice Solution |
|---|---|
| One feature change touches 4+ files across layers | All code for a feature is co-located in one folder |
| Service classes grow into god classes | Each feature has its own handler — small, focused, testable |
| Hard to understand a feature (code scattered everywhere) | Open one folder, see the entire feature |
| Difficulty deleting features | Delete one folder; no orphaned code in other layers |
| All features share the same abstraction level | Each slice can use the right level of abstraction for its complexity |

### Slice Structure

```
Features/
  PlaceOrder/
    PlaceOrderCommand.ts       # Input data structure
    PlaceOrderHandler.ts       # Business logic + data access
    PlaceOrderValidator.ts     # Input validation
    PlaceOrderResponse.ts      # Output data structure
    PlaceOrder.test.ts         # Tests for this feature
  GetOrderDetails/
    GetOrderDetailsQuery.ts
    GetOrderDetailsHandler.ts
    GetOrderDetailsResponse.ts
    GetOrderDetails.test.ts
```

### The Mediator Pattern (MediatR-Style)

Vertical slices often use a mediator to decouple the entry point (controller) from the handler.

```
// Controller:
router.post('/orders', async (req, res) => {
  const result = await mediator.send(new PlaceOrderCommand(req.body));
  res.status(201).json(result);
});

// Handler (registered with mediator):
class PlaceOrderHandler implements Handler<PlaceOrderCommand, PlaceOrderResponse> {
  async handle(command: PlaceOrderCommand): Promise<PlaceOrderResponse> {
    // validate, create domain objects, persist, return response
  }
}
```

The controller does not know which handler serves the command. The mediator resolves it. This enables cross-cutting concerns (logging, validation, authorization) as pipeline behaviors.

### Pipeline Behaviors (Cross-Cutting Concerns)

| Behavior | Responsibility | Position in Pipeline |
|---|---|---|
| Logging | Log command name, execution time, success/failure | First (wraps everything) |
| Validation | Validate command input | Before handler |
| Authorization | Check user permissions for this command | Before handler |
| Transaction | Wrap handler in a database transaction | Around handler |
| Caching | Cache query results | Around handler (queries only) |

### When Vertical Slices Work Best

| Signal | Good Fit |
|---|---|
| Features are independent with little shared logic | Each slice is self-contained |
| Team works on features, not layers | Feature ownership maps to slice ownership |
| Fast iteration, frequent feature additions | Adding a feature is adding a folder |
| Mixed complexity across features | Complex features get more structure, simple ones stay minimal |

### When Vertical Slices Are Not Enough

| Signal | Augment With |
|---|---|
| Shared business rules across features | Extract domain layer with entities/value objects |
| Cross-feature transactions | Application service or saga coordination |
| Complex invariants | Aggregate pattern from DDD |
| Growing codebase, multiple teams | Modular monolith boundaries around groups of slices |

## Combining Approaches

### Modular Monolith + Vertical Slices

Use modular monolith boundaries at the macro level (module per bounded context) and vertical slices within each module.

```
modules/
  orders/
    features/
      PlaceOrder/
      CancelOrder/
      GetOrderList/
    domain/             # Shared domain objects within the module
      Order.ts
      OrderItem.ts
    public/
      OrderModule.ts    # Module facade
  payments/
    features/
      ProcessPayment/
      RefundPayment/
    domain/
      Payment.ts
    public/
      PaymentModule.ts
```

### Modular Monolith + Clean Architecture

Use module boundaries at the macro level, clean architecture within each module.

```
modules/
  orders/
    domain/             # Entities, value objects, ports
    application/        # Use cases
    infrastructure/     # Adapters
    interface/          # Controllers
    public/             # Module facade
```

### Migration Path: Monolith to Microservices

1. Structure the monolith as modules with enforced boundaries
2. Ensure modules communicate only through public APIs or events
3. Ensure each module owns its data (no cross-module database access)
4. When deployment independence is needed, extract a module into a service
5. Replace in-process calls with network calls, in-process events with message broker

If steps 1-3 are done well, step 4-5 is mechanical. The hard work is getting the boundaries right.

## Feature Flags as Architectural Support

Feature flags enable trunk-based development and incremental rollout within any architecture style.

| Use Case | How |
|---|---|
| Incomplete feature behind a flag | Merge to main, flag is off in production |
| Gradual rollout | Enable for 5% of users, monitor, increase |
| A/B testing | Flag controls which variant a user sees |
| Kill switch | Disable a problematic feature without deployment |
| Module extraction | Flag routes traffic between old and new module during migration |

### Architectural Placement

Place flag evaluation at the entry point (controller or use case), not deep in domain logic. Feature flags are infrastructure concerns — keep them out of the domain model.

```
// In controller or use case (acceptable):
if (featureFlags.isEnabled('newPricing', user)) {
  return newPricingUseCase.execute(input);
} else {
  return legacyPricingUseCase.execute(input);
}

// In domain entity (avoid):
class Order {
  calculateTotal() {
    if (featureFlags.isEnabled('newPricing')) { ... }  // domain depends on infrastructure
  }
}
```
