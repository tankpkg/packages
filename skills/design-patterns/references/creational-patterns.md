# Creational Patterns

Sources: Gamma et al. (Design Patterns), Freeman (Head First Design Patterns), Osmani (Learning JavaScript Design Patterns), Vlissides (Pattern Hatching)

Covers: Factory Method, Abstract Factory, Builder, Prototype, Singleton — adapted for modern JavaScript and TypeScript with closures, modules, and generics.

## 1. Factory Method

**Intent:** Define an interface for creating objects, but let subclasses or functions decide which class to instantiate.

**When to Use:**
- Object type determined at runtime by input data (e.g., parsing config, API responses)
- You want to decouple creation from usage
- Multiple product types share a common interface

**When NOT to Use:**
- Only one concrete type exists — use `new` directly
- The creation logic is trivial (no branching)

**Real-world:** UI component factories, notification channel selection, database driver instantiation.

```ts
interface Logger {
  log(message: string): void;
}

class ConsoleLogger implements Logger {
  log(message: string) { console.log(message); }
}

class FileLogger implements Logger {
  log(message: string) { fs.appendFileSync("app.log", message + "\n"); }
}

// Factory function — preferred in JS/TS over class-based factory
function createLogger(type: "console" | "file"): Logger {
  switch (type) {
    case "console": return new ConsoleLogger();
    case "file":    return new FileLogger();
    default:        throw new Error(`Unknown logger type: ${type}`);
  }
}

const logger = createLogger(config.logTarget);
```

**JS/TS Adaptation:** Prefer factory functions over class hierarchies. Use a `Record<string, () => T>` registry for open-ended extension:

```ts
const loggerRegistry: Record<string, () => Logger> = {
  console: () => new ConsoleLogger(),
  file:    () => new FileLogger(),
};

function createLogger(type: string): Logger {
  const factory = loggerRegistry[type];
  if (!factory) throw new Error(`Unknown logger: ${type}`);
  return factory();
}

// Third-party code can register new loggers
loggerRegistry.sentry = () => new SentryLogger();
```

## 2. Abstract Factory

**Intent:** Create families of related objects without specifying their concrete classes.

**When to Use:**
- Multiple related products must be created together (e.g., themed UI: Button + Input + Modal)
- Swapping entire families at once (light theme vs dark theme, SQL vs NoSQL)

**When NOT to Use:**
- Single product type — use Factory Method
- Families never change — over-engineering

**Real-world:** Cross-platform UI toolkits, database abstraction layers, test fixture generators.

```ts
interface UIFactory {
  createButton(): Button;
  createInput(): Input;
}

class MaterialUIFactory implements UIFactory {
  createButton() { return new MaterialButton(); }
  createInput()  { return new MaterialInput(); }
}

class AntDesignFactory implements UIFactory {
  createButton() { return new AntButton(); }
  createInput()  { return new AntInput(); }
}

function buildForm(factory: UIFactory) {
  const button = factory.createButton();
  const input = factory.createInput();
  // Both are guaranteed to be from the same family
}
```

## 3. Builder

**Intent:** Construct complex objects step by step, separating construction from representation.

**When to Use:**
- Object has 4+ optional fields or complex construction sequences
- Need to build different representations of the same type
- Construction involves validation across multiple fields

**When NOT to Use:**
- Object has 1-3 fields — use constructor or object literal
- No optional fields or construction steps

**Real-world:** Query builders (Knex, Prisma), HTTP request builders, config objects, test data factories.

```ts
class QueryBuilder {
  private table = "";
  private conditions: string[] = [];
  private orderField?: string;
  private limitVal?: number;

  from(table: string): this {
    this.table = table;
    return this;
  }

  where(condition: string): this {
    this.conditions.push(condition);
    return this;
  }

  orderBy(field: string): this {
    this.orderField = field;
    return this;
  }

  limit(n: number): this {
    this.limitVal = n;
    return this;
  }

  build(): string {
    if (!this.table) throw new Error("Table required");
    let sql = `SELECT * FROM ${this.table}`;
    if (this.conditions.length) sql += ` WHERE ${this.conditions.join(" AND ")}`;
    if (this.orderField) sql += ` ORDER BY ${this.orderField}`;
    if (this.limitVal) sql += ` LIMIT ${this.limitVal}`;
    return sql;
  }
}

const query = new QueryBuilder()
  .from("users")
  .where("active = true")
  .where("age > 18")
  .orderBy("created_at")
  .limit(10)
  .build();
```

**JS/TS Adaptation:** For simple cases, prefer the options object pattern over a Builder class:

```ts
interface QueryOptions {
  table: string;
  where?: string[];
  orderBy?: string;
  limit?: number;
}

function buildQuery(opts: QueryOptions): string {
  let sql = `SELECT * FROM ${opts.table}`;
  if (opts.where?.length) sql += ` WHERE ${opts.where.join(" AND ")}`;
  if (opts.orderBy) sql += ` ORDER BY ${opts.orderBy}`;
  if (opts.limit) sql += ` LIMIT ${opts.limit}`;
  return sql;
}
```

Use a class Builder when: construction is multi-step, validation spans steps, or you need method chaining with IDE autocomplete.

## 4. Prototype

**Intent:** Create new objects by cloning an existing instance rather than constructing from scratch.

**When to Use:**
- Object creation is expensive (DB fetches, heavy computation)
- Need copies with minor variations from a template
- Configuration objects with many defaults

**When NOT to Use:**
- Objects are cheap to create
- Deep cloning is complex (circular references, non-serializable fields)

**Real-world:** Game entity spawning, document template systems, configuration presets.

```ts
interface Cloneable<T> {
  clone(): T;
}

class ServerConfig implements Cloneable<ServerConfig> {
  constructor(
    public host: string,
    public port: number,
    public ssl: boolean,
    public timeout: number,
    public retries: number,
  ) {}

  clone(): ServerConfig {
    return new ServerConfig(this.host, this.port, this.ssl, this.timeout, this.retries);
  }
}

const production = new ServerConfig("api.example.com", 443, true, 30000, 3);
const staging = production.clone();
staging.host = "staging.example.com";
staging.ssl = false;
```

**JS/TS Adaptation:** For plain objects, use structured clone or spread:

```ts
const defaults = { host: "localhost", port: 3000, ssl: false, timeout: 5000 };
const custom = { ...defaults, port: 8080, ssl: true }; // shallow clone + override

// Deep clone for nested objects
const deepCopy = structuredClone(complexObject);
```

## 5. Singleton

**Intent:** Ensure a class or module has exactly one instance and provide a global point of access.

**When to Use:**
- Resource that is expensive to create and must be shared (DB connection pool, logger)
- Configuration that must be consistent across the application

**When NOT to Use:**
- Sharing state between tests (causes coupling, flaky tests)
- Hiding dependencies (use explicit DI instead)
- Any case where you want testability — Singletons resist mocking

**Real-world:** Database connection pools, application-wide config, caches.

**The JS Module IS a Singleton.** In Node.js/ESM, each module is evaluated once and cached. Exporting an instance from a module is the idiomatic JS Singleton:

```ts
// db.ts — this IS the singleton pattern in JS
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
});

export default pool;
```

Every import of `db.ts` receives the same `pool` instance. No class ceremony needed.

**When you must use class-based Singleton** (rare — framework constraints, lazy initialization):

```ts
class AppConfig {
  private static instance: AppConfig;
  private data: Map<string, unknown> = new Map();

  private constructor() {}

  static getInstance(): AppConfig {
    if (!AppConfig.instance) {
      AppConfig.instance = new AppConfig();
    }
    return AppConfig.instance;
  }

  get<T>(key: string): T | undefined {
    return this.data.get(key) as T;
  }

  set(key: string, value: unknown): void {
    this.data.set(key, value);
  }
}
```

**Prefer DI over Singleton.** Instead of `AppConfig.getInstance()`, inject the config:

```ts
function createApp(config: AppConfig) {
  // config is injected — testable, mockable, explicit
}
```

## Creational Pattern Comparison

| Pattern | Complexity | Use When | Avoid When |
| --- | --- | --- | --- |
| Factory Method | Low | Runtime type selection | Single concrete type |
| Abstract Factory | Medium | Related product families | One product type |
| Builder | Medium | Complex multi-step construction | Simple 1-3 field objects |
| Prototype | Low | Cloning with minor variations | Cheap-to-create objects |
| Singleton | Low | Shared resource, one instance | Testability matters (use DI) |

## JS/TS-Specific Guidelines

1. **Factory functions over factory classes.** Functions are simpler, compose better, and avoid `this` confusion.
2. **Options objects over Builder classes.** When construction is a single step, `buildThing(opts)` beats `new ThingBuilder().setA().setB().build()`.
3. **Module scope over Singleton class.** ES modules already provide single-instance semantics.
4. **`structuredClone` over manual Prototype.** For plain data objects, use the platform primitive.
5. **Generics for type-safe factories.** Use `<T>` to preserve concrete return types through factory indirection.
