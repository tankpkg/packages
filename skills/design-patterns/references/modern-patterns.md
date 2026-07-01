# Modern JavaScript/TypeScript Patterns

Sources: Osmani (Learning JavaScript Design Patterns), Fowler (Patterns of Enterprise Application Architecture), Express.js/Koa documentation, React documentation, Webpack/Rollup plugin APIs, community patterns (2020-2026)

Covers: Module, Provider, Middleware/Pipeline, Repository, Unit of Work, Pub/Sub, Plugin/Hook — patterns native to the JavaScript and TypeScript ecosystem that extend or replace classical GoF patterns.

## 1. Module Pattern

**Intent:** Encapsulate private state and expose a public API using language-level module boundaries.

**When to Use:**
- Encapsulating internal implementation details
- Providing a clean public API from a package or feature
- Replacing classical Singleton and Namespace patterns

**When NOT to Use:**
- Everything is public — no encapsulation benefit
- Module is a single exported function — no pattern needed

**Real-world:** Every ES module, Node.js packages, library entry points.

**ES Module — the native Module pattern:**

```ts
// counter.ts — private state, public API
let count = 0;

export function increment(): number { return ++count; }
export function decrement(): number { return --count; }
export function getCount(): number { return count; }
// `count` is inaccessible from outside — true encapsulation
```

**Revealing Module with closure — pre-ESM or runtime modules:**

```ts
function createCounter(initial = 0) {
  let count = initial;

  return {
    increment: () => ++count,
    decrement: () => --count,
    getCount: () => count,
  };
}

const counter = createCounter(10);
counter.increment(); // 11
// counter.count — undefined, private
```

**Barrel re-export as Facade + Module:**

```ts
// features/auth/index.ts — curated public API
export { login, logout } from "./auth-service";
export { AuthProvider } from "./auth-provider";
export type { AuthState, User } from "./types";
// Internal implementation files are NOT exported
```

## 2. Provider Pattern

**Intent:** Share cross-cutting data or services through a component tree or dependency graph without explicit prop passing.

**When to Use:**
- Theme, locale, auth state shared across many components
- Dependency injection in component-based frameworks
- Avoiding prop drilling in deep component hierarchies

**When NOT to Use:**
- Data used by only 1-2 components — pass directly
- Frequently changing data causing unnecessary re-renders (use targeted state)

**Real-world:** React Context, Vue provide/inject, Angular dependency injection, InversifyJS.

```tsx
// React Provider pattern
interface ThemeContext {
  colors: { primary: string; background: string };
  spacing: { sm: number; md: number; lg: number };
}

const ThemeCtx = React.createContext<ThemeContext | null>(null);

function useTheme(): ThemeContext {
  const ctx = React.useContext(ThemeCtx);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

function ThemeProvider({ theme, children }: { theme: ThemeContext; children: React.ReactNode }) {
  return <ThemeCtx.Provider value={theme}>{children}</ThemeCtx.Provider>;
}
```

**DI Container — framework-agnostic Provider:**

```ts
class Container {
  private registry = new Map<string, () => unknown>();

  register<T>(token: string, factory: () => T): void {
    this.registry.set(token, factory);
  }

  resolve<T>(token: string): T {
    const factory = this.registry.get(token);
    if (!factory) throw new Error(`No provider for: ${token}`);
    return factory() as T;
  }
}

const container = new Container();
container.register("logger", () => new ConsoleLogger());
container.register("userService", () => new UserService(container.resolve("logger")));
```

## 3. Middleware / Pipeline Pattern

**Intent:** Process requests through a linear sequence of composable handlers, where each can transform, short-circuit, or pass to the next.

**When to Use:**
- HTTP request processing (auth, validation, logging, parsing, handling)
- Data transformation pipelines (ETL, build tool plugins)
- Any sequential processing where steps are composable and reorderable

**When NOT to Use:**
- Single-step processing — a function call suffices
- Steps have complex interdependencies (use a directed graph, not a pipeline)

**Real-world:** Express/Koa/Hono middleware, Webpack loaders, Redux middleware, Fastify hooks.

```ts
type Context = { req: Request; res: Response; user?: User; startTime?: number };
type Next = () => Promise<void>;
type Middleware = (ctx: Context, next: Next) => Promise<void>;

function compose(middlewares: Middleware[]): Middleware {
  return async (ctx, next) => {
    let index = -1;
    async function dispatch(i: number): Promise<void> {
      if (i <= index) throw new Error("next() called multiple times");
      index = i;
      const fn = i === middlewares.length ? next : middlewares[i];
      if (fn) await fn(ctx, () => dispatch(i + 1));
    }
    await dispatch(0);
  };
}

// Usage
const timing: Middleware = async (ctx, next) => {
  ctx.startTime = Date.now();
  await next();
  console.log(`${Date.now() - ctx.startTime!}ms`);
};

const auth: Middleware = async (ctx, next) => {
  const token = ctx.req.headers.get("authorization");
  if (!token) { ctx.res = new Response("Unauthorized", { status: 401 }); return; }
  ctx.user = await verifyToken(token);
  await next();
};

const pipeline = compose([timing, auth]);
```

**Type-safe Pipeline for data transforms:**

```ts
type Transform<TIn, TOut> = (input: TIn) => TOut;

function pipe<A, B>(fn1: Transform<A, B>): Transform<A, B>;
function pipe<A, B, C>(fn1: Transform<A, B>, fn2: Transform<B, C>): Transform<A, C>;
function pipe<A, B, C, D>(fn1: Transform<A, B>, fn2: Transform<B, C>, fn3: Transform<C, D>): Transform<A, D>;
function pipe(...fns: Transform<any, any>[]): Transform<any, any> {
  return (input) => fns.reduce((acc, fn) => fn(acc), input);
}

const processUser = pipe(
  (raw: RawUser) => validateUser(raw),
  (valid) => normalizeEmail(valid),
  (normalized) => enrichWithDefaults(normalized),
);
```

## 4. Repository Pattern

**Intent:** Mediate between the domain and data mapping layers using a collection-like interface for accessing domain objects.

**When to Use:**
- Decoupling business logic from data access (ORM, API, file system)
- Swapping storage implementations (in-memory for tests, DB for production)
- Centralizing query logic and caching

**When NOT to Use:**
- Simple CRUD with no business logic — direct ORM usage is fine
- Only one data source that will never change

**Real-world:** Data access layers in backend services, offline-first apps, multi-tenant systems.

```ts
interface UserRepository {
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  save(user: User): Promise<void>;
  delete(id: string): Promise<void>;
}

class PostgresUserRepository implements UserRepository {
  constructor(private db: Pool) {}

  async findById(id: string): Promise<User | null> {
    const { rows } = await this.db.query("SELECT * FROM users WHERE id = $1", [id]);
    return rows[0] ? this.toDomain(rows[0]) : null;
  }

  async findByEmail(email: string): Promise<User | null> {
    const { rows } = await this.db.query("SELECT * FROM users WHERE email = $1", [email]);
    return rows[0] ? this.toDomain(rows[0]) : null;
  }

  async save(user: User): Promise<void> {
    await this.db.query(
      "INSERT INTO users (id, email, name) VALUES ($1, $2, $3) ON CONFLICT (id) DO UPDATE SET email = $2, name = $3",
      [user.id, user.email, user.name],
    );
  }

  async delete(id: string): Promise<void> {
    await this.db.query("DELETE FROM users WHERE id = $1", [id]);
  }

  private toDomain(row: any): User {
    return { id: row.id, email: row.email, name: row.name };
  }
}

// Test implementation
class InMemoryUserRepository implements UserRepository {
  private users = new Map<string, User>();

  async findById(id: string) { return this.users.get(id) ?? null; }
  async findByEmail(email: string) {
    return [...this.users.values()].find((u) => u.email === email) ?? null;
  }
  async save(user: User) { this.users.set(user.id, user); }
  async delete(id: string) { this.users.delete(id); }
}
```

## 5. Unit of Work

**Intent:** Maintain a list of objects affected by a business transaction and coordinate writing out changes as a single atomic operation.

**When to Use:**
- Multiple entities must be saved or rolled back together
- Batch database operations for performance
- Tracking which objects are dirty, new, or deleted

**When NOT to Use:**
- Single entity operations — direct save is simpler
- Your ORM already provides Unit of Work (e.g., TypeORM, Prisma transactions)

```ts
class UnitOfWork {
  private operations: Array<() => Promise<void>> = [];

  registerNew<T>(repo: { save: (entity: T) => Promise<void> }, entity: T) {
    this.operations.push(() => repo.save(entity));
  }

  registerDeleted<T>(repo: { delete: (id: string) => Promise<void> }, id: string) {
    this.operations.push(() => repo.delete(id));
  }

  async commit(db: { transaction: (fn: () => Promise<void>) => Promise<void> }) {
    await db.transaction(async () => {
      for (const op of this.operations) await op();
    });
    this.operations = [];
  }
}
```

## 6. Pub/Sub (Publish-Subscribe)

**Intent:** Decouple publishers from subscribers through a message broker, allowing many-to-many communication without direct references.

**When to Use:**
- Microservice event communication
- Cross-module communication where Observer creates tight coupling
- Event sourcing and CQRS read-model updates

**When NOT to Use:**
- Same-module communication — Observer is simpler and more traceable
- Synchronous, ordered processing required

Difference from Observer: Pub/Sub has a broker (topic-based routing, possible persistence). Observer has direct subscription.

```ts
class MessageBroker {
  private topics = new Map<string, Set<(msg: unknown) => void>>();

  subscribe<T>(topic: string, handler: (msg: T) => void): () => void {
    if (!this.topics.has(topic)) this.topics.set(topic, new Set());
    this.topics.get(topic)!.add(handler as any);
    return () => this.topics.get(topic)?.delete(handler as any);
  }

  publish<T>(topic: string, message: T): void {
    this.topics.get(topic)?.forEach((handler) => handler(message));
  }
}
```

## 7. Plugin / Hook Pattern

**Intent:** Allow third-party code to extend or modify application behavior at predefined extension points without changing core code.

**When to Use:**
- Build tools, editors, frameworks that need extensibility
- Applications with user-customizable behavior
- Open-closed principle at the architecture level

**When NOT to Use:**
- Internal code with no external consumers
- Extension points are speculative (add when requested)

**Real-world:** Webpack plugins, Babel plugins, ESLint rules, Vite plugins, VS Code extensions.

```ts
interface Plugin {
  name: string;
  setup(hooks: PluginHooks): void;
}

interface PluginHooks {
  beforeBuild: Hook<{ config: BuildConfig }>;
  afterBuild: Hook<{ output: BuildOutput }>;
  onError: Hook<{ error: Error }>;
}

class Hook<T> {
  private taps: Array<(arg: T) => void | Promise<void>> = [];

  tap(fn: (arg: T) => void | Promise<void>) { this.taps.push(fn); }

  async call(arg: T) {
    for (const fn of this.taps) await fn(arg);
  }
}

// Plugin registration
class BuildSystem {
  private hooks: PluginHooks = {
    beforeBuild: new Hook(),
    afterBuild: new Hook(),
    onError: new Hook(),
  };

  use(plugin: Plugin) { plugin.setup(this.hooks); }

  async build(config: BuildConfig) {
    await this.hooks.beforeBuild.call({ config });
    const output = await this.runBuild(config);
    await this.hooks.afterBuild.call({ output });
    return output;
  }
}

// Third-party plugin
const timingPlugin: Plugin = {
  name: "timing",
  setup(hooks) {
    let start: number;
    hooks.beforeBuild.tap(() => { start = Date.now(); });
    hooks.afterBuild.tap(() => { console.log(`Build: ${Date.now() - start}ms`); });
  },
};
```

## Modern Pattern Comparison

| Pattern | Replaces | Key Benefit | JS/TS Mechanism |
| --- | --- | --- | --- |
| Module | Namespace, Revealing Module | Native encapsulation | ES modules, closures |
| Provider | Service Locator | Scoped dependency sharing | Context, DI container |
| Middleware | Chain of Responsibility | Composable request pipeline | async/await, compose() |
| Repository | Direct data access | Testable, swappable storage | Interface + implementations |
| Unit of Work | Ad-hoc transactions | Atomic multi-entity commits | Transaction wrapper |
| Pub/Sub | Tightly-coupled Observer | Decoupled cross-boundary events | Topic-based broker |
| Plugin/Hook | Subclassing for extension | Open-closed architecture | Tapable hooks, lifecycle callbacks |
