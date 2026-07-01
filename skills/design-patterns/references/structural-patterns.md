# Structural Patterns

Sources: Gamma et al. (Design Patterns), Osmani (Learning JavaScript Design Patterns), Freeman (Head First Design Patterns), MDN Web Docs (Proxy, Reflect)

Covers: Adapter, Decorator, Facade, Proxy, Flyweight — adapted for JavaScript and TypeScript using closures, higher-order functions, ES Proxy, and module patterns.

## 1. Adapter

**Intent:** Convert the interface of a class or module into another interface that clients expect.

**When to Use:**
- Integrating a third-party library whose API does not match your internal interface
- Migrating from one service to another (old API to new API)
- Normalizing multiple data sources into a uniform shape

**When NOT to Use:**
- Interfaces are already compatible
- You control both sides and can change the source

**Real-world:** Payment gateway adapters (Stripe/PayPal behind one interface), ORM adapters, API versioning layers.

```ts
// External SDK with incompatible interface
interface ExternalAnalytics {
  trackEvent(name: string, meta: Record<string, string>): void;
}

// Your internal interface
interface Analytics {
  track(event: string, properties: Record<string, unknown>): void;
}

class AnalyticsAdapter implements Analytics {
  constructor(private external: ExternalAnalytics) {}

  track(event: string, properties: Record<string, unknown>): void {
    const meta: Record<string, string> = {};
    for (const [key, val] of Object.entries(properties)) {
      meta[key] = String(val);
    }
    this.external.trackEvent(event, meta);
  }
}
```

**Functional Adapter — preferred for simple cases:**

```ts
function adaptAnalytics(external: ExternalAnalytics): Analytics {
  return {
    track(event, properties) {
      const meta = Object.fromEntries(
        Object.entries(properties).map(([k, v]) => [k, String(v)])
      );
      external.trackEvent(event, meta);
    },
  };
}
```

## 2. Decorator

**Intent:** Attach additional responsibilities to an object dynamically, without modifying its source.

**When to Use:**
- Adding cross-cutting concerns (logging, caching, retry, timing) to functions or services
- Wrapping behavior around an existing interface at specific call sites
- When subclassing would create a combinatorial explosion of classes

**When NOT to Use:**
- Stacking more than 3-4 decorators (debug difficulty)
- The base object interface changes frequently (all decorators must update)

**Real-world:** Express/Koa middleware (each is a decorator), caching wrappers, auth guards, React higher-order components.

**Function Decorator — idiomatic JS/TS:**

```ts
type AsyncFn<T> = (...args: unknown[]) => Promise<T>;

function withRetry<T>(fn: AsyncFn<T>, retries = 3): AsyncFn<T> {
  return async (...args) => {
    let lastError: unknown;
    for (let i = 0; i <= retries; i++) {
      try {
        return await fn(...args);
      } catch (err) {
        lastError = err;
        if (i < retries) await new Promise((r) => setTimeout(r, 2 ** i * 100));
      }
    }
    throw lastError;
  };
}

function withLogging<T>(fn: AsyncFn<T>, label: string): AsyncFn<T> {
  return async (...args) => {
    console.log(`[${label}] start`);
    const result = await fn(...args);
    console.log(`[${label}] done`);
    return result;
  };
}

// Compose decorators
const fetchUser = withLogging(withRetry(api.getUser, 3), "fetchUser");
```

**Class Decorator — when interface compliance matters:**

```ts
interface DataSource {
  read(key: string): Promise<string | null>;
  write(key: string, value: string): Promise<void>;
}

class CachingDataSource implements DataSource {
  private cache = new Map<string, string>();

  constructor(private wrapped: DataSource) {}

  async read(key: string): Promise<string | null> {
    if (this.cache.has(key)) return this.cache.get(key)!;
    const value = await this.wrapped.read(key);
    if (value !== null) this.cache.set(key, value);
    return value;
  }

  async write(key: string, value: string): Promise<void> {
    this.cache.set(key, value);
    await this.wrapped.write(key, value);
  }
}
```

**TC39 Decorators (Stage 3) — for class methods:**

```ts
function logged(originalMethod: Function, context: ClassMethodDecoratorContext) {
  return function (this: unknown, ...args: unknown[]) {
    console.log(`Calling ${String(context.name)}`);
    return originalMethod.apply(this, args);
  };
}

class UserService {
  @logged
  async findById(id: string) { /* ... */ }
}
```

## 3. Facade

**Intent:** Provide a simplified interface to a complex subsystem.

**When to Use:**
- Subsystem has many classes/functions and callers only need common operations
- Hiding third-party library complexity behind your own API
- Creating a high-level API for a module that internally uses multiple services

**When NOT to Use:**
- Subsystem is already simple
- Callers need full access to subsystem internals (Facade becomes a bottleneck)

**Real-world:** ORM query facades, payment processing (hides tokenization, gateway, fraud check), media upload (hides resize, compress, store, CDN).

```ts
// Complex subsystem
class VideoEncoder { encode(file: string) { /* ... */ } }
class ThumbnailGenerator { generate(file: string) { /* ... */ } }
class CDNUploader { upload(file: string, bucket: string) { /* ... */ } }
class MetadataExtractor { extract(file: string) { /* ... */ } }

// Facade
class VideoService {
  private encoder = new VideoEncoder();
  private thumbs = new ThumbnailGenerator();
  private cdn = new CDNUploader();
  private meta = new MetadataExtractor();

  async publish(file: string): Promise<{ url: string; thumbnail: string }> {
    const metadata = this.meta.extract(file);
    const encoded = await this.encoder.encode(file);
    const thumbnail = await this.thumbs.generate(encoded);
    const url = await this.cdn.upload(encoded, "videos");
    const thumbUrl = await this.cdn.upload(thumbnail, "thumbnails");
    return { url, thumbnail: thumbUrl };
  }
}

// Callers only interact with the simple facade
const video = new VideoService();
const result = await video.publish("/uploads/raw-video.mp4");
```

## 4. Proxy

**Intent:** Provide a surrogate or placeholder for another object to control access to it.

**When to Use:**
- Lazy initialization of expensive resources (virtual proxy)
- Access control (protection proxy)
- Logging, metering, or caching transparent to callers
- Remote service abstraction (remote proxy)

**When NOT to Use:**
- No access control or lazy loading needed — direct reference is simpler
- Performance-critical hot paths (proxy adds indirection overhead)

**Real-world:** API rate limiters, lazy-loaded images, Vue.js reactivity system, validation proxies.

**ES Proxy — the JS-native implementation:**

```ts
function createValidatingProxy<T extends object>(target: T, rules: Record<string, (v: unknown) => boolean>): T {
  return new Proxy(target, {
    set(obj, prop, value) {
      const key = String(prop);
      if (rules[key] && !rules[key](value)) {
        throw new Error(`Invalid value for ${key}: ${value}`);
      }
      return Reflect.set(obj, prop, value);
    },
  });
}

const user = createValidatingProxy(
  { name: "", age: 0 },
  {
    age: (v) => typeof v === "number" && v >= 0 && v <= 150,
    name: (v) => typeof v === "string" && (v as string).length > 0,
  },
);

user.name = "Alice"; // OK
user.age = -5;       // throws: Invalid value for age
```

**Lazy-loading Proxy:**

```ts
function lazyInit<T extends object>(factory: () => T): T {
  let instance: T | null = null;
  return new Proxy({} as T, {
    get(_, prop, receiver) {
      if (!instance) instance = factory();
      return Reflect.get(instance, prop, receiver);
    },
  });
}

const db = lazyInit(() => connectToDatabase()); // Connection only created on first access
```

## 5. Flyweight

**Intent:** Share fine-grained objects efficiently to minimize memory usage.

**When to Use:**
- Large number of similar objects (10,000+) consuming significant memory
- Most object state can be shared (intrinsic) while a small portion varies (extrinsic)
- Object creation is a measurable memory bottleneck

**When NOT to Use:**
- Small number of objects — optimization not needed
- Objects have mostly unique state — nothing to share
- Premature optimization without profiling

**Real-world:** Text editor character rendering, game particle systems, icon/sprite caches, DOM element pooling.

```ts
class Icon {
  constructor(
    public readonly name: string,
    public readonly svgData: string, // large, shareable
  ) {}
}

class IconFactory {
  private cache = new Map<string, Icon>();

  getIcon(name: string): Icon {
    if (!this.cache.has(name)) {
      const svgData = loadSvgFromDisk(name); // expensive
      this.cache.set(name, new Icon(name, svgData));
    }
    return this.cache.get(name)!;
  }
}

// Extrinsic state (position, size) stays outside the flyweight
interface PlacedIcon {
  icon: Icon;    // shared flyweight
  x: number;     // extrinsic
  y: number;     // extrinsic
  size: number;  // extrinsic
}
```

## Structural Pattern Comparison

| Pattern | Complexity | Key Mechanism | JS/TS Idiom |
| --- | --- | --- | --- |
| Adapter | Low | Interface translation | Wrapper function or class |
| Decorator | Low-Med | Wrapping with same interface | Higher-order functions, class wrapping |
| Facade | Low | Simplified entry point | Service class or module re-export |
| Proxy | Medium | Transparent interception | ES `Proxy` object, wrapper class |
| Flyweight | Medium | Object sharing via cache | `Map` cache with factory access |

## JS/TS-Specific Guidelines

1. **Higher-order functions ARE decorators.** `withRetry(fn)` is more idiomatic than a `RetryDecorator` class.
2. **ES `Proxy` is a first-class pattern.** Use it for validation, reactivity, lazy loading. Avoid in hot loops.
3. **Module re-exports as Facade.** An `index.ts` that re-exports a curated API from internal modules is a Facade.
4. **Adapter functions over adapter classes.** When the adaptation is stateless, a function is cleaner.
5. **`Map` or `WeakMap` for Flyweight caches.** `WeakMap` prevents memory leaks when flyweight keys are objects.
