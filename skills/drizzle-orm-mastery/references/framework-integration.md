# Framework Integration

Sources: Drizzle ORM v1.x documentation (orm.drizzle.team), Supabase Drizzle guide (supabase.com), Neon serverless driver docs, Turso/libSQL documentation, Cloudflare D1 documentation, 2025-2026 community integration patterns

Covers: connecting Drizzle to various database providers and frameworks including Next.js App Router, Supabase, Neon serverless, Cloudflare D1, Turso/libSQL, TanStack Start, and environment-specific connection patterns.

## Connection Pattern Overview

| Provider | Driver Package | Drizzle Package | Connection Type |
|----------|---------------|-----------------|-----------------|
| PostgreSQL (self-hosted) | `pg` | `drizzle-orm/node-postgres` | TCP pool |
| PostgreSQL (Supabase) | `postgres` | `drizzle-orm/postgres-js` | TCP or HTTP pooler |
| PostgreSQL (Neon) | `@neondatabase/serverless` | `drizzle-orm/neon-http` or `neon-serverless` | HTTP or WebSocket |
| MySQL | `mysql2` | `drizzle-orm/mysql2` | TCP pool |
| SQLite (local) | `better-sqlite3` | `drizzle-orm/better-sqlite3` | File |
| SQLite (Turso) | `@libsql/client` | `drizzle-orm/libsql` | HTTP or embedded |
| SQLite (Cloudflare D1) | D1 binding | `drizzle-orm/d1` | Worker binding |

## PostgreSQL with node-postgres

Standard setup for self-hosted PostgreSQL, AWS RDS, or any TCP-accessible instance.

```typescript
// src/db/index.ts
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "./schema";

export const db = drizzle({
  connection: process.env.DATABASE_URL!,
  schema,
  casing: "snake_case",
});
```

For explicit pool control:

```typescript
import { Pool } from "pg";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "./schema";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
});

export const db = drizzle({ client: pool, schema });
```

## Supabase

Supabase provides PostgreSQL with a built-in connection pooler (Supavisor). Use the pooler URL for serverless environments.

### Direct Connection (Long-Lived Servers)

```typescript
import postgres from "postgres";
import { drizzle } from "drizzle-orm/postgres-js";
import * as schema from "./schema";

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle({ client, schema });
```

### Pooled Connection (Serverless / Edge)

Use the Supavisor pooler URL (port 6543) with `?pgbouncer=true`:

```typescript
import postgres from "postgres";
import { drizzle } from "drizzle-orm/postgres-js";
import * as schema from "./schema";

const client = postgres(process.env.DATABASE_URL!, {
  prepare: false,  // required for transaction pooling mode
});
export const db = drizzle({ client, schema });
```

Set `prepare: false` when using Supavisor in transaction pooling mode because prepared statements are not supported across pooled connections.

### drizzle.config.ts for Supabase

```typescript
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema",
  out: "./drizzle",
  dbCredentials: {
    url: process.env.DATABASE_URL!,  // use direct URL, not pooler
  },
});
```

Use the direct connection URL (port 5432) for drizzle-kit operations (generate, push, migrate). The pooler URL is for application runtime only.

## Neon Serverless

Neon provides serverless PostgreSQL with HTTP and WebSocket drivers optimized for edge runtimes.

### HTTP Driver (Recommended for Serverless)

```typescript
import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "./schema";

const sql = neon(process.env.DATABASE_URL!);
export const db = drizzle({ client: sql, schema });
```

The HTTP driver sends each query as an individual HTTP request. No persistent connection. Ideal for Vercel Edge Functions and Cloudflare Workers.

### WebSocket Driver (For Transactions)

The HTTP driver does not support transactions because each query is a separate HTTP request. Use the WebSocket driver when transactions are needed:

```typescript
import { Pool, neonConfig } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-serverless";
import * as schema from "./schema";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export const db = drizzle({ client: pool, schema });
```

### Decision: HTTP vs WebSocket

| Factor | HTTP (`neon-http`) | WebSocket (`neon-serverless`) |
|--------|-------------------|------------------------------|
| Latency | Higher per-query (HTTP overhead) | Lower (persistent connection) |
| Transactions | Not supported | Supported |
| Edge runtime compatible | Yes | Yes (with WebSocket polyfill) |
| Connection management | None (stateless) | Pool required |
| Best for | Simple CRUD, read-heavy | Write-heavy, transactions |

## Cloudflare D1

D1 is Cloudflare's edge SQLite database. Access it through Worker bindings.

### Worker Setup

```typescript
// src/index.ts (Cloudflare Worker)
import { drizzle } from "drizzle-orm/d1";
import * as schema from "./schema";

export interface Env {
  DB: D1Database;
}

export default {
  async fetch(request: Request, env: Env) {
    const db = drizzle({ client: env.DB, schema });

    const users = await db.select().from(schema.users);
    return Response.json(users);
  },
};
```

### D1 Schema (SQLite Dialect)

```typescript
import { sqliteTable, integer, text } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: integer().primaryKey({ autoIncrement: true }),
  name: text().notNull(),
  email: text().notNull().unique(),
});
```

### drizzle.config.ts for D1

```typescript
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  dialect: "sqlite",
  schema: "./src/db/schema.ts",
  out: "./drizzle",
  dbCredentials: {
    // For local development
    url: ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/<db-id>/db.sqlite",
  },
});
```

For remote D1:

```bash
# Apply migrations to remote D1
wrangler d1 migrations apply <database-name> --remote
```

### Next.js with D1 (Edge Runtime)

```typescript
// app/api/users/route.ts
import { drizzle } from "drizzle-orm/d1";
import { getRequestContext } from "@cloudflare/next-on-pages";

export const runtime = "edge";

export async function GET() {
  const { env } = getRequestContext();
  const db = drizzle({ client: env.DB });
  const users = await db.select().from(schema.users);
  return Response.json(users);
}
```

## Turso / libSQL

Turso provides edge-distributed SQLite using libSQL.

```typescript
import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
import * as schema from "./schema";

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

export const db = drizzle({ client, schema });
```

### Embedded Replicas (Turso)

For low-latency reads with local SQLite replica:

```typescript
import { createClient } from "@libsql/client";

const client = createClient({
  url: "file:local.db",
  syncUrl: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
  syncInterval: 60,  // sync every 60 seconds
});
```

## Next.js App Router

### Singleton Pattern

Prevent creating multiple database connections in development (hot reload creates new instances):

```typescript
// src/db/index.ts
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "./schema";

const globalForDb = globalThis as unknown as {
  db: ReturnType<typeof drizzle> | undefined;
};

export const db = globalForDb.db ?? drizzle({
  connection: process.env.DATABASE_URL!,
  schema,
});

if (process.env.NODE_ENV !== "production") {
  globalForDb.db = db;
}
```

### Server Components

```typescript
// app/users/page.tsx
import { db } from "@/db";
import { users } from "@/db/schema";

export default async function UsersPage() {
  const allUsers = await db.select().from(users);
  return (
    <ul>
      {allUsers.map((user) => <li key={user.id}>{user.name}</li>)}
    </ul>
  );
}
```

### Server Actions

```typescript
// app/actions.ts
"use server";

import { db } from "@/db";
import { users } from "@/db/schema";
import { revalidatePath } from "next/cache";

export async function createUser(formData: FormData) {
  await db.insert(users).values({
    name: formData.get("name") as string,
    email: formData.get("email") as string,
  });
  revalidatePath("/users");
}
```

### Route Handlers

```typescript
// app/api/users/route.ts
import { db } from "@/db";
import { users } from "@/db/schema";
import { NextResponse } from "next/server";

export async function GET() {
  const allUsers = await db.select().from(users);
  return NextResponse.json(allUsers);
}
```

## TanStack Start

TanStack Start uses server functions. Connect Drizzle in server-side code:

```typescript
// src/db/index.ts
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "./schema";

export const db = drizzle({
  connection: process.env.DATABASE_URL!,
  schema,
});
```

```typescript
// src/routes/users.tsx
import { createServerFn } from "@tanstack/react-start";
import { db } from "../db";
import { users } from "../db/schema";

const getUsers = createServerFn("GET", async () => {
  return db.select().from(users);
});
```

## Environment-Specific Connection Patterns

| Environment | Pattern | Key Consideration |
|-------------|---------|-------------------|
| Local development | Direct TCP, single connection | Use `push` for fast iteration |
| Node.js server (long-lived) | TCP pool (pg Pool / postgres.js) | Size pool to CPU cores |
| Vercel Serverless Functions | postgres.js or Neon HTTP | New connection per invocation |
| Vercel Edge Functions | Neon HTTP or D1 binding | No TCP; HTTP-only drivers |
| Cloudflare Workers | D1 binding or Turso HTTP | SQLite dialect only for D1 |
| AWS Lambda | RDS Proxy + node-postgres | Use RDS Proxy to manage connections |
| Docker/Kubernetes | TCP pool with health checks | Set idle timeout < server timeout |

## Common Integration Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| No singleton in Next.js dev | Connection leak on hot reload | Use `globalThis` singleton pattern |
| Pooler URL for drizzle-kit | Push/generate fails with pooler | Use direct DB URL for kit, pooler for runtime |
| Missing `prepare: false` with Supavisor | Prepared statement errors | Set `prepare: false` for transaction pooling |
| HTTP driver for transactions | Transactions silently fail | Use WebSocket or TCP driver for transactions |
| Edge runtime with node-postgres | Runtime error (no TCP in edge) | Use HTTP-based driver (Neon HTTP, D1) |
| Importing `db` in client components | Database URL exposed to browser | Only import `db` in server components/actions |
