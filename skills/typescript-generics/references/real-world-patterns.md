# Real-World Generic Patterns

Sources: Vanderkam (Effective TypeScript, 2nd ed., 2024), Cherny (Programming TypeScript, 2019), production library source (Zod, tRPC, Drizzle ORM, TanStack Router)

Covers: type-safe builder pattern, generic factory, type-safe event emitter, registry pattern, state machine typing, and patterns from popular TypeScript libraries.

## Type-Safe Builder Pattern

Accumulate type information through chained method calls:

```typescript
class QueryBuilder<T extends Record<string, unknown>, Selected extends keyof T = never> {
  private table: string;
  private columns: string[] = [];
  private conditions: string[] = [];

  constructor(table: string) {
    this.table = table;
  }

  select<K extends keyof T>(...cols: K[]): QueryBuilder<T, Selected | K> {
    this.columns.push(...(cols as string[]));
    return this as any;
  }

  where(condition: string): this {
    this.conditions.push(condition);
    return this;
  }

  build(): { table: string; columns: (Selected & string)[]; conditions: string[] } {
    return {
      table: this.table,
      columns: this.columns as (Selected & string)[],
      conditions: this.conditions,
    };
  }
}

interface User {
  id: string;
  name: string;
  email: string;
  age: number;
}

const query = new QueryBuilder<User>("users")
  .select("name", "email")
  .where("age > 18")
  .build();
// query.columns: ("name" | "email")[]
```

### Builder Pattern Key Technique

Each method returns a new generic instantiation with accumulated type state. The final `build()` method returns the accumulated result type.

## Generic Factory Pattern

Create instances with type safety from a registry:

```typescript
interface ComponentMap {
  button: { label: string; onClick: () => void };
  input: { value: string; onChange: (v: string) => void };
  select: { options: string[]; selected: string };
}

function createComponent<K extends keyof ComponentMap>(
  kind: K,
  props: ComponentMap[K]
): ComponentMap[K] {
  // Factory implementation
  return props;
}

// Type-safe: props must match the component kind
const btn = createComponent("button", { label: "Click", onClick: () => {} });
const inp = createComponent("input", { value: "", onChange: (v) => {} });

// Error: wrong props for kind
createComponent("button", { value: "" }); // Error
```

### Abstract Factory with Generics

```typescript
interface Serializer<T> {
  serialize(value: T): string;
  deserialize(raw: string): T;
}

class JsonSerializer<T> implements Serializer<T> {
  serialize(value: T): string {
    return JSON.stringify(value);
  }
  deserialize(raw: string): T {
    return JSON.parse(raw) as T;
  }
}

function createSerializer<T>(): Serializer<T> {
  return new JsonSerializer<T>();
}

const userSerializer = createSerializer<User>();
const json = userSerializer.serialize({ id: "1", name: "Alice" });
```

## Type-Safe Event Emitter

Full implementation using mapped types and generics:

```typescript
type EventMap = Record<string, unknown[]>;

class TypedEmitter<Events extends EventMap> {
  private listeners = new Map<string, Function[]>();

  on<K extends keyof Events & string>(
    event: K,
    listener: (...args: Events[K]) => void
  ): this {
    const existing = this.listeners.get(event) ?? [];
    existing.push(listener);
    this.listeners.set(event, existing);
    return this;
  }

  off<K extends keyof Events & string>(
    event: K,
    listener: (...args: Events[K]) => void
  ): this {
    const existing = this.listeners.get(event) ?? [];
    this.listeners.set(event, existing.filter(l => l !== listener));
    return this;
  }

  emit<K extends keyof Events & string>(
    event: K,
    ...args: Events[K]
  ): void {
    const listeners = this.listeners.get(event) ?? [];
    listeners.forEach(l => l(...args));
  }
}

// Usage
interface AppEvents extends EventMap {
  userLogin: [userId: string, timestamp: Date];
  error: [error: Error];
  dataLoaded: [data: unknown[], source: string];
}

const emitter = new TypedEmitter<AppEvents>();

emitter.on("userLogin", (userId, timestamp) => {
  // userId: string, timestamp: Date -- fully typed
  console.log(`${userId} logged in at ${timestamp}`);
});

emitter.emit("userLogin", "user-1", new Date()); // OK
emitter.emit("userLogin", 42); // Error: number not assignable to string
emitter.emit("unknown"); // Error: "unknown" not in AppEvents
```

## Registry Pattern

Map string keys to typed handlers:

```typescript
type HandlerMap = Record<string, (...args: any[]) => any>;

class Registry<Handlers extends HandlerMap = {}> {
  private handlers = new Map<string, Function>();

  register<K extends string, H extends (...args: any[]) => any>(
    key: K,
    handler: H
  ): Registry<Handlers & Record<K, H>> {
    this.handlers.set(key, handler);
    return this as any;
  }

  call<K extends keyof Handlers & string>(
    key: K,
    ...args: Parameters<Handlers[K]>
  ): ReturnType<Handlers[K]> {
    const handler = this.handlers.get(key);
    if (!handler) throw new Error(`No handler for ${key}`);
    return handler(...args);
  }
}

const registry = new Registry()
  .register("greet", (name: string) => `Hello, ${name}!`)
  .register("add", (a: number, b: number) => a + b);

registry.call("greet", "Alice"); // OK: returns string
registry.call("add", 1, 2);     // OK: returns number
registry.call("greet", 42);     // Error: number not assignable to string
```

## Type-Safe State Machine

Model states and transitions at the type level:

```typescript
interface StateConfig {
  [state: string]: {
    on: {
      [event: string]: string;
    };
  };
}

type StateMachine<Config extends StateConfig> = {
  [S in keyof Config]: {
    state: S;
    send<E extends keyof Config[S]["on"]>(
      event: E
    ): StateMachine<Config>[Config[S]["on"][E] & keyof Config];
  };
}[keyof Config];

// Define a traffic light
interface TrafficLight extends StateConfig {
  green: { on: { TIMER: "yellow" } };
  yellow: { on: { TIMER: "red" } };
  red: { on: { TIMER: "green" } };
}

// Type-safe: only valid transitions allowed
declare function createMachine<C extends StateConfig>(
  config: C,
  initial: keyof C
): StateMachine<C>;
```

## Patterns from Popular Libraries

### Zod-Style Schema Builder

```typescript
interface ZodType<T> {
  _output: T;
  parse(input: unknown): T;
  optional(): ZodType<T | undefined>;
}

interface ZodObject<T extends Record<string, ZodType<any>>> extends ZodType<{
  [K in keyof T]: T[K]["_output"];
}> {
  shape: T;
  pick<K extends keyof T>(...keys: K[]): ZodObject<Pick<T, K>>;
  omit<K extends keyof T>(...keys: K[]): ZodObject<Omit<T, K>>;
}

// The key insight: schema.parse() returns the inferred type
// z.object({ name: z.string(), age: z.number() }).parse(data)
// returns { name: string; age: number }
```

### tRPC-Style Procedure Chain

```typescript
interface ProcedureBuilder<TInput, TOutput> {
  input<T>(schema: ZodType<T>): ProcedureBuilder<T, TOutput>;
  output<T>(schema: ZodType<T>): ProcedureBuilder<TInput, T>;
  query(fn: (opts: { input: TInput }) => TOutput | Promise<TOutput>): Procedure<TInput, TOutput>;
  mutation(fn: (opts: { input: TInput }) => TOutput | Promise<TOutput>): Procedure<TInput, TOutput>;
}

// Each chain method narrows the type until query/mutation finalizes it
```

### Drizzle-Style Type-Safe SQL

```typescript
// Table definition carries column types
interface Column<T, TName extends string> {
  _type: T;
  _name: TName;
}

interface Table<TName extends string, TColumns extends Record<string, Column<any, any>>> {
  _name: TName;
  _columns: TColumns;
}

// Select infers result type from selected columns
type InferSelect<T extends Table<any, any>> = {
  [K in keyof T["_columns"]]: T["_columns"][K]["_type"];
};
```

## Middleware Pattern

Type-safe middleware chain that accumulates context:

```typescript
type Middleware<TInput, TOutput> = (
  input: TInput,
  next: (input: TInput) => TOutput
) => TOutput;

class Pipeline<TContext> {
  private middlewares: Middleware<any, any>[] = [];

  use<TNewContext extends TContext>(
    middleware: Middleware<TContext, TContext & TNewContext>
  ): Pipeline<TContext & TNewContext> {
    this.middlewares.push(middleware);
    return this as any;
  }

  run(initial: TContext): TContext {
    return this.middlewares.reduceRight(
      (next, mw) => (input) => mw(input, next),
      (input: TContext) => input
    )(initial);
  }
}
```

## Generic Configuration Pattern

Type-safe configuration with defaults:

```typescript
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

function defineConfig<T extends Record<string, unknown>>(
  defaults: T
): (overrides?: DeepPartial<T>) => T {
  return (overrides = {} as DeepPartial<T>) => {
    return deepMerge(defaults, overrides) as T;
  };
}

interface AppConfig {
  port: number;
  database: { host: string; port: number; name: string };
  logging: { level: "debug" | "info" | "error"; pretty: boolean };
}

const getConfig = defineConfig<AppConfig>({
  port: 3000,
  database: { host: "localhost", port: 5432, name: "app" },
  logging: { level: "info", pretty: false },
});

const config = getConfig({ database: { host: "prod-db" } });
// Full AppConfig with overridden database.host
```

## Pattern Selection Guide

| Need | Pattern | Key Generic Technique |
|------|---------|----------------------|
| Accumulate type through method chain | Builder | Return widened generic at each step |
| Map string keys to typed values | Registry / Factory | Indexed access: `Map[K]` |
| Type-safe events | Event emitter | Mapped event map with tuple args |
| Validate and infer | Schema (Zod) | `_output` phantom type |
| Chain transformations | Middleware / Pipeline | Intersection accumulation |
| Model valid transitions | State machine | Conditional mapped transitions |
| Config with defaults | Deep merge | `DeepPartial<T>` + merge |
