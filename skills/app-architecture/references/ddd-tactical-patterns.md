# DDD Tactical Patterns

Sources: Evans (Domain-Driven Design), Vernon (Implementing Domain-Driven Design), Millett & Tune (Patterns, Principles, and Practices of Domain-Driven Design), Fowler (Patterns of Enterprise Application Architecture)

Covers: entities, value objects, aggregates and aggregate roots, domain events, repositories, domain services, application services, factories, the anemic domain model problem. Focuses on tactical (in-code) patterns, not strategic (organizational) DDD.

## When to Apply DDD Tactical Patterns

| Signal | Apply DDD | Skip DDD |
|---|---|---|
| Complex, evolving business rules | Yes | |
| Domain experts available for collaboration | Yes | |
| Core domain (competitive advantage) | Yes | |
| CRUD with minimal logic | | Yes |
| Generic subdomain (solved problem) | | Yes |
| Integration-heavy, logic-light | | Yes |

DDD tactical patterns have a cost: more classes, more indirection, more modeling effort. Apply them where the domain is the primary source of complexity.

## Entities

Objects defined by their identity, not their attributes. Two entities with the same attributes but different identities are different objects.

| Property | Explanation |
|---|---|
| Has a unique identity | UUID, database ID, or natural key — persists across state changes |
| Mutable | State changes over time through defined behaviors |
| Encapsulates behavior | Business rules live as methods on the entity, not in external services |
| Enforces invariants | Constructor and methods guarantee the entity is always in a valid state |

### Entity Design Rules

| Rule | Example |
|---|---|
| No public setters | Expose methods that express intent: `order.cancel()` not `order.setStatus("cancelled")` |
| Constructor validates | `new Order(items)` throws if items list is empty |
| Methods enforce rules | `order.addItem(item)` checks max items, duplicate detection |
| State transitions are explicit | `order.ship()` validates that order is in "paid" state before transitioning |

### Entity vs Data Record

```
// Anemic (data record with no behavior):
class Order {
  id: string;
  items: OrderItem[];
  status: string;
  total: number;
}

// Rich entity (encapsulates behavior):
class Order {
  private constructor(private id: OrderId, private items: OrderItem[], private status: OrderStatus) {
    if (items.length === 0) throw new EmptyOrderError();
  }

  addItem(item: OrderItem): void { /* validates, updates total */ }
  cancel(): void { /* validates state transition */ }
  ship(): void { /* validates state transition, emits event */ }
  get total(): Money { /* calculates from items */ }
}
```

## Value Objects

Objects defined by their attributes, not identity. Two value objects with the same attributes are interchangeable.

| Property | Explanation |
|---|---|
| No identity | Compared by attribute equality, not reference |
| Immutable | Once created, cannot change. Operations return new instances |
| Self-validating | Constructor rejects invalid state |
| Replaces primitive obsession | `Money` instead of `number`, `EmailAddress` instead of `string` |

### Common Value Objects

| Value Object | Replaces | Validation |
|---|---|---|
| `Money(amount, currency)` | `number` | Non-negative, valid currency code |
| `EmailAddress(value)` | `string` | RFC-compliant format |
| `DateRange(start, end)` | Two `Date` fields | Start before end |
| `Address(street, city, zip, country)` | Multiple strings | Non-empty required fields, valid postal code |
| `Quantity(value)` | `number` | Positive integer |
| `OrderId(value)` | `string` | Valid UUID format |

### Value Object Design Rules

| Rule | Rationale |
|---|---|
| All fields set in constructor | Immutability from creation |
| No setters | Mutation returns a new instance: `money.add(other)` returns new `Money` |
| Override equality | Two `Money(100, "USD")` instances are equal |
| Make invalid states unrepresentable | `Quantity(-5)` throws at construction time |

## Aggregates

A cluster of domain objects treated as a single unit for data changes. One entity is the aggregate root — the entry point for all external access.

### Aggregate Rules

| Rule | Explanation |
|---|---|
| External access through the root only | Outside code never reaches into the aggregate to modify an inner entity |
| One transaction per aggregate | A single database transaction modifies one aggregate. Cross-aggregate consistency is eventual |
| Reference other aggregates by ID | Do not hold object references to other aggregates. Store `customerId: CustomerId`, not `customer: Customer` |
| Keep aggregates small | Large aggregates cause contention. Prefer smaller, focused aggregates |

### Identifying Aggregate Boundaries

| Question | If Yes |
|---|---|
| Must these objects change together in a single transaction? | Same aggregate |
| Can these objects change independently? | Separate aggregates |
| Does a business rule span both objects? | Consider same aggregate (but evaluate contention cost) |
| Will concurrent users modify the same data? | Smaller aggregates reduce lock contention |

### Example: Order Aggregate

```
Order (Aggregate Root)
  |-- OrderId (value object)
  |-- OrderItem[] (entity, contained within aggregate)
  |     |-- ProductId (value object, reference to Product aggregate)
  |     |-- Quantity (value object)
  |     |-- Price (value object)
  |-- ShippingAddress (value object)
  |-- OrderStatus (value object / enum)
  |-- CustomerId (value object, reference to Customer aggregate)
```

`Order` is the root. External code calls `order.addItem()`, never `orderItem.setQuantity()` directly. `ProductId` and `CustomerId` are references by ID to other aggregates, not object references.

### Aggregate Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Giant aggregate (entire order + customer + inventory) | Lock contention, slow persistence, large transaction scope | Break into smaller aggregates linked by ID |
| Object references between aggregates | Lazy loading, accidental modification of another aggregate | Store ID only, load other aggregate when needed |
| Multiple aggregates in one transaction | Violates consistency boundary, couples aggregates | Use domain events for cross-aggregate coordination |
| Aggregate without invariants | No business reason for the grouping | Reevaluate boundaries; maybe it is just an entity |

## Domain Events

A record that something significant happened in the domain. Expressed in past tense using ubiquitous language.

| Property | Explanation |
|---|---|
| Immutable | Events represent facts that happened; they cannot change |
| Named in past tense | `OrderPlaced`, `PaymentReceived`, `ItemShipped` |
| Contains relevant data | Event carries the data needed by handlers: `OrderPlaced { orderId, items, total, timestamp }` |
| Produced by aggregates | Aggregates emit events as side effects of state changes |

### Event Handling Patterns

| Pattern | Scope | Example |
|---|---|---|
| In-process handler | Same bounded context, same transaction | Update read model after order placed |
| Async handler | Same bounded context, separate transaction | Send confirmation email |
| Cross-context event | Different bounded context, async | Billing context reacts to order placed |

### Raising Events

```
class Order {
  private events: DomainEvent[] = [];

  place(): void {
    this.validateCanBePlaced();
    this.status = OrderStatus.Placed;
    this.events.push(new OrderPlaced(this.id, this.items, this.total));
  }

  pullEvents(): DomainEvent[] {
    const events = [...this.events];
    this.events = [];
    return events;
  }
}
```

The application service (use case) retrieves events after the operation and dispatches them.

## Repositories

Abstraction over data access. The calling code interacts with the repository as if it were a simple collection — `add`, `find`, `remove` — while the implementation hides the actual persistence mechanism behind that interface.

| Rule | Explanation |
|---|---|
| One repository per aggregate root | `OrderRepository`, not `OrderItemRepository` |
| Interface in domain, implementation in infrastructure | Port/adapter pattern |
| Works with domain objects, not persistence models | `save(order: Order)` not `save(row: OrderRow)` |
| Encapsulates query logic | `findByCustomer(customerId)` not raw SQL in use cases |

### Repository Interface Design

```
interface OrderRepository {
  save(order: Order): void;
  findById(id: OrderId): Order | null;
  findByCustomer(customerId: CustomerId): Order[];
  nextIdentity(): OrderId;
}
```

Keep repository interfaces narrow. Complex reporting queries belong in a separate read model or query service, not in the domain repository.

## Domain Services

Operations that do not naturally belong to any single entity or value object.

| Signal | Use a Domain Service |
|---|---|
| Logic involves multiple aggregates | `TransferFundsService(fromAccount, toAccount, amount)` |
| Business rule does not belong to one entity | `PricingService.calculatePrice(product, customer, promotions)` |
| Stateless operation on domain concepts | `PasswordPolicy.validate(password)` |

Domain services are part of the domain layer. They use domain types and express domain concepts. Do not confuse with application services.

## Application Services (Use Cases)

Orchestrate domain objects to fulfill a user intention. Application services live in the application layer, above the domain.

| Domain Service | Application Service |
|---|---|
| Contains business logic | Contains workflow orchestration |
| Uses domain types only | Uses ports to interact with infrastructure |
| Part of the domain layer | Part of the application layer |
| `PricingService.calculate()` | `PlaceOrderUseCase.execute()` |
| Stateless business computation | Manages transaction boundaries, calls repositories, publishes events |

### Application Service Responsibilities

1. Accept input DTO (not domain objects) from the driving adapter
2. Load required aggregates from repositories
3. Call domain methods (entity methods, domain services)
4. Persist changes through repositories
5. Dispatch domain events
6. Return output DTO

Application services must not contain business rules. If a conditional or calculation appears in the application service, it probably belongs in a domain entity or domain service.

## Factories

Encapsulate complex object creation logic. Use when constructing an aggregate requires more than simple parameter assignment.

| Use Factory When | Example |
|---|---|
| Creation logic is complex | Building an order from a cart involves validation, pricing, inventory checks |
| Creation spans multiple objects | Creating an account requires a user, profile, and default settings |
| Different creation paths exist | Creating an order from web vs from bulk import has different rules |

Factories can be static methods on the aggregate root (`Order.createFromCart(cart)`) or standalone factory classes for complex cases.

## The Anemic Domain Model Problem

An anemic domain model looks like DDD (entities, value objects, repositories) but all behavior lives in services. Entities are data bags with getters and setters.

| Symptom | Indicates Anemia |
|---|---|
| Entities have only getters/setters | No encapsulated behavior |
| Services contain all business logic | Logic is procedural, not object-oriented |
| Validation in services, not entities | Invalid entity states are possible |
| "Manager" or "Helper" classes | Logic that should be on the entity is displaced |

### The Fix

Move behavior into entities and value objects. Start by identifying where the domain rules are enforced (usually in service classes) and relocate them to the objects that own the data those rules operate on.
