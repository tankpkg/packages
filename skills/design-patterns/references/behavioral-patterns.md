# Behavioral Patterns

Sources: Gamma et al. (Design Patterns), Osmani (Learning JavaScript Design Patterns), Freeman (Head First Design Patterns), Fowler (Patterns of Enterprise Application Architecture)

Covers: Observer, Strategy, Command, State, Mediator, Chain of Responsibility, Iterator — adapted for JavaScript and TypeScript using closures, generics, and native language features.

## 1. Observer

**Intent:** Define a one-to-many dependency so that when one object changes state, all dependents are notified automatically.

**When to Use:**
- UI components reacting to data changes
- Event-driven architectures (domain events, webhooks)
- Decoupling producers from consumers

**When NOT to Use:**
- Only one subscriber — direct callback is simpler
- Order of notification matters (Observer does not guarantee order)
- Too many observers (>10) make debugging difficult — consider Mediator

**Real-world:** EventEmitter, React state updates, RxJS Observables, DOM events.

```ts
type Listener<T> = (data: T) => void;

class EventEmitter<Events extends Record<string, unknown>> {
  private listeners = new Map<keyof Events, Set<Listener<any>>>();

  on<K extends keyof Events>(event: K, listener: Listener<Events[K]>): () => void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener); // unsubscribe
  }

  emit<K extends keyof Events>(event: K, data: Events[K]): void {
    this.listeners.get(event)?.forEach((fn) => fn(data));
  }
}

// Type-safe usage
interface AppEvents {
  "user:created": { id: string; email: string };
  "order:placed": { orderId: string; total: number };
}

const bus = new EventEmitter<AppEvents>();
const unsub = bus.on("user:created", (user) => console.log(user.email));
bus.emit("user:created", { id: "1", email: "a@b.com" });
unsub(); // cleanup
```

## 2. Strategy

**Intent:** Define a family of algorithms, encapsulate each one, and make them interchangeable at runtime.

**When to Use:**
- Multiple algorithms for the same task (sorting, pricing, validation, compression)
- Algorithm selection based on runtime conditions (user tier, locale, config)
- Eliminating large switch/if-else blocks on algorithm type

**When NOT to Use:**
- Only one algorithm exists — a plain function is enough
- Algorithms never change at runtime — compile-time selection suffices

**Real-world:** Payment processing strategies, compression algorithms, pricing tiers, authentication providers.

```ts
// Strategy as a function type — idiomatic JS/TS
type PricingStrategy = (basePrice: number, quantity: number) => number;

const regularPricing: PricingStrategy = (price, qty) => price * qty;
const premiumPricing: PricingStrategy = (price, qty) => price * qty * 0.8;
const wholesalePricing: PricingStrategy = (price, qty) =>
  qty >= 100 ? price * qty * 0.6 : price * qty * 0.75;

// Context holds a strategy reference
class ShoppingCart {
  constructor(private pricing: PricingStrategy) {}

  setPricing(strategy: PricingStrategy) { this.pricing = strategy; }

  calculateTotal(items: { price: number; quantity: number }[]): number {
    return items.reduce((sum, item) => sum + this.pricing(item.price, item.quantity), 0);
  }
}

const cart = new ShoppingCart(regularPricing);
cart.setPricing(premiumPricing); // swap at runtime
```

**Strategy Map pattern — clean runtime selection:**

```ts
const strategies: Record<string, PricingStrategy> = {
  regular: regularPricing,
  premium: premiumPricing,
  wholesale: wholesalePricing,
};

function getPricing(tier: string): PricingStrategy {
  const strategy = strategies[tier];
  if (!strategy) throw new Error(`Unknown pricing tier: ${tier}`);
  return strategy;
}
```

## 3. Command

**Intent:** Encapsulate a request as an object, allowing parameterization, queuing, logging, and undo/redo.

**When to Use:**
- Undo/redo functionality
- Task queues and job scheduling
- Macro recording (sequence of operations replayed later)
- Decoupling the invoker from the operation

**When NOT to Use:**
- Simple one-shot operations with no need for undo, queuing, or logging

**Real-world:** Text editor undo/redo, CLI command history, transaction logs, CQRS command side.

```ts
interface Command {
  execute(): void;
  undo(): void;
}

class InsertTextCommand implements Command {
  constructor(
    private document: { content: string },
    private position: number,
    private text: string,
  ) {}

  execute() {
    const { content } = this.document;
    this.document.content = content.slice(0, this.position) + this.text + content.slice(this.position);
  }

  undo() {
    const { content } = this.document;
    this.document.content = content.slice(0, this.position) + content.slice(this.position + this.text.length);
  }
}

class CommandHistory {
  private history: Command[] = [];
  private pointer = -1;

  execute(cmd: Command) {
    this.history.length = this.pointer + 1; // discard redo stack
    cmd.execute();
    this.history.push(cmd);
    this.pointer++;
  }

  undo() {
    if (this.pointer < 0) return;
    this.history[this.pointer].undo();
    this.pointer--;
  }

  redo() {
    if (this.pointer >= this.history.length - 1) return;
    this.pointer++;
    this.history[this.pointer].execute();
  }
}
```

## 4. State

**Intent:** Allow an object to alter its behavior when its internal state changes, appearing to change its class.

**When to Use:**
- Object behavior varies by mode (draft/published/archived, idle/loading/error)
- Complex conditional logic based on current state
- State transitions follow explicit rules (finite state machine)

**When NOT to Use:**
- Only 2 simple states — a boolean flag suffices
- No behavioral difference between states — just data

**Real-world:** UI component states (form submission flow), order processing, media players, TCP connections.

```ts
interface ConnectionState {
  open(ctx: Connection): void;
  close(ctx: Connection): void;
  send(ctx: Connection, data: string): void;
}

class DisconnectedState implements ConnectionState {
  open(ctx: Connection) {
    console.log("Opening connection...");
    ctx.setState(new ConnectedState());
  }
  close() { console.log("Already disconnected"); }
  send() { throw new Error("Cannot send: not connected"); }
}

class ConnectedState implements ConnectionState {
  open() { console.log("Already connected"); }
  close(ctx: Connection) {
    console.log("Closing connection...");
    ctx.setState(new DisconnectedState());
  }
  send(_ctx: Connection, data: string) {
    console.log(`Sending: ${data}`);
  }
}

class Connection {
  private state: ConnectionState = new DisconnectedState();

  setState(state: ConnectionState) { this.state = state; }
  open()             { this.state.open(this); }
  close()            { this.state.close(this); }
  send(data: string) { this.state.send(this, data); }
}
```

**Lightweight alternative — state map:**

```ts
type State = "idle" | "loading" | "success" | "error";
type Action = "fetch" | "resolve" | "reject" | "reset";

const transitions: Record<State, Partial<Record<Action, State>>> = {
  idle:    { fetch: "loading" },
  loading: { resolve: "success", reject: "error" },
  success: { reset: "idle", fetch: "loading" },
  error:   { reset: "idle", fetch: "loading" },
};

function transition(current: State, action: Action): State {
  return transitions[current]?.[action] ?? current;
}
```

## 5. Mediator

**Intent:** Define an object that encapsulates how a set of objects interact, promoting loose coupling.

**When to Use:**
- Many objects communicate in complex, many-to-many patterns
- Changes to one component cascade unpredictably to others
- Centralizing communication logic (chat rooms, form field dependencies, UI panels)

**When NOT to Use:**
- Simple one-to-one communication — direct reference is clearer
- The mediator becomes a god object (split into multiple mediators by domain)

**Real-world:** Chat servers, form validation coordinators, air traffic control, Redux store.

```ts
interface FormField {
  name: string;
  value: unknown;
  setDisabled(disabled: boolean): void;
}

class FormMediator {
  private fields = new Map<string, FormField>();

  register(field: FormField) {
    this.fields.set(field.name, field);
  }

  notify(sender: string, event: string) {
    if (sender === "country" && event === "change") {
      const country = this.fields.get("country");
      const state = this.fields.get("state");
      const zip = this.fields.get("zip");
      // Enable/disable fields based on country selection
      if (country?.value === "US") {
        state?.setDisabled(false);
        zip?.setDisabled(false);
      } else {
        state?.setDisabled(true);
        zip?.setDisabled(true);
      }
    }
  }
}
```

## 6. Chain of Responsibility

**Intent:** Pass a request along a chain of handlers. Each handler decides either to process or forward.

**When to Use:**
- Multiple handlers that can process a request, but the handler is unknown at compile time
- Processing pipeline where handlers can short-circuit
- Decoupling sender from receiver

**When NOT to Use:**
- Guaranteed single handler — use direct dispatch
- Order does not matter — use Observer

**Real-world:** Express middleware, DOM event bubbling, logging level filters, approval workflows.

```ts
type Handler<T> = (request: T, next: () => void) => void;

function createChain<T>(...handlers: Handler<T>[]): (request: T) => void {
  return (request: T) => {
    let index = 0;
    function next() {
      if (index < handlers.length) {
        const handler = handlers[index++];
        handler(request, next);
      }
    }
    next();
  };
}

// Usage: approval chain
interface Expense { amount: number; approved: boolean }

const managerApproval: Handler<Expense> = (req, next) => {
  if (req.amount <= 1000) { req.approved = true; return; }
  next();
};

const directorApproval: Handler<Expense> = (req, next) => {
  if (req.amount <= 10000) { req.approved = true; return; }
  next();
};

const cfoApproval: Handler<Expense> = (req, _next) => {
  req.approved = req.amount <= 100000;
};

const approve = createChain(managerApproval, directorApproval, cfoApproval);
```

## 7. Iterator

**Intent:** Provide a way to access elements of a collection sequentially without exposing the underlying representation.

**When to Use:**
- Custom data structures that need `for...of` support
- Lazy evaluation of sequences (pagination, infinite streams)
- Uniform traversal across different collection types

**When NOT to Use:**
- Standard arrays/maps — built-in iterators already exist

**Real-world:** Database cursor pagination, file line readers, tree traversal, range generators.

```ts
async function* paginate<T>(fetchPage: (cursor: string) => Promise<{ data: T[]; next?: string }>) {
  let cursor = "";
  while (true) {
    const page = await fetchPage(cursor);
    yield* page.data;
    if (!page.next) break;
    cursor = page.next;
  }
}
```

## Behavioral Pattern Comparison

| Pattern | Complexity | Key Mechanism | JS/TS Idiom |
| --- | --- | --- | --- |
| Observer | Low | Callback registry | EventEmitter, custom typed emitter |
| Strategy | Low | Swappable function | Function types, strategy map |
| Command | Medium | Request as object | Command interface with execute/undo |
| State | Medium | Delegated behavior | State interface or transition map |
| Mediator | Medium | Centralized coordination | Mediator class or event bus |
| Chain of Resp. | Low-Med | Handler chain with next() | Composed handler functions |
| Iterator | Low | Sequential access protocol | Generators, Symbol.iterator |
