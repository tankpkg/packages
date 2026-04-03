# Deployment and Serverless

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Accelerate documentation, Prisma Blog deployment guides, Vercel/AWS Lambda deployment patterns, 2025-2026 production deployment patterns

Covers: Docker builds with Prisma, CI/CD pipelines, serverless connection management, Prisma Accelerate, PgBouncer configuration, edge deployment, error handling and retry patterns, and Prisma Client generation strategies.

## Docker Deployment

### Multi-Stage Dockerfile

```dockerfile
# Stage 1: Build
FROM node:20-slim AS builder
WORKDIR /app

COPY package*.json ./
COPY prisma ./prisma/
RUN npm ci

# Generate Prisma Client
RUN npx prisma generate

COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-slim AS runner
WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/package*.json ./

# Run migrations and start
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
```

### Key Docker Considerations

| Concern | Solution |
|---------|----------|
| Binary target mismatch | Prisma generates platform-specific engine binaries. Generate inside the Docker build |
| Image size | Use `node:20-slim` or `node:20-alpine`. Prisma engine adds ~15MB |
| Migration timing | Run `migrate deploy` at container startup, not build time |
| Secret management | Pass `DATABASE_URL` as environment variable, not baked into image |
| Health checks | Add a `/health` endpoint that calls `prisma.$queryRaw\`SELECT 1\`` |

### Binary Targets

When building on a different OS than the deployment target, specify binary targets:

```prisma
generator client {
  provider      = "prisma-client-js"
  binaryTargets = ["native", "linux-musl-openssl-3.0.x"]
}
```

Common targets:

| Platform | Binary Target |
|----------|--------------|
| Debian/Ubuntu (Docker) | `debian-openssl-3.0.x` |
| Alpine (Docker) | `linux-musl-openssl-3.0.x` |
| AWS Lambda | `rhel-openssl-3.0.x` |
| macOS (dev) | `darwin` (covered by `native`) |

## CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci

      # Generate Prisma Client for type checking and build
      - run: npx prisma generate

      # Type check and build
      - run: npm run build

      # Apply migrations to production database
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

      # Deploy application
      - run: npm run deploy
```

### Pipeline Order

1. `npm ci` -- install dependencies
2. `prisma generate` -- generate types and client
3. Build and test (types available from step 2)
4. `prisma migrate deploy` -- apply schema changes
5. Deploy application code

Run migrations BEFORE deploying new code. If migrations fail, the old code continues running against the old schema.

## Serverless Deployment

### The Serverless Connection Problem

Each serverless function invocation creates a Prisma Client instance with its own connection pool. With 100 concurrent invocations, each opening 5 connections, the database handles 500 connections -- likely exceeding its limit.

| Platform | Default Concurrency | Connection Risk |
|----------|-------------------|-----------------|
| AWS Lambda | 1000 | High |
| Vercel Functions | 100-1000 | High |
| Cloudflare Workers | 1000+ | Critical (no TCP) |
| Railway / Fly.io | Instance-based | Moderate |

### Solutions

| Solution | Mechanism | Latency | Cost |
|----------|-----------|---------|------|
| Prisma Accelerate | Managed connection proxy + caching | +5-20ms | Paid after free tier |
| PgBouncer (self-hosted) | External connection pooler | +1-5ms | Infrastructure cost |
| Managed pooler (Supabase, Neon) | Built-in connection pooling | +1-5ms | Included in DB plan |
| Reduce pool size | `max: 1` per function | None | Free |

### Prisma Accelerate

Prisma Accelerate is a managed global edge cache and connection pooler:

```typescript
import { PrismaClient } from '@prisma/client'
import { withAccelerate } from '@prisma/extension-accelerate'

const prisma = new PrismaClient().$extends(withAccelerate())
```

```
# Use Accelerate connection string
DATABASE_URL="prisma://accelerate.prisma-data.net/?api_key=YOUR_KEY"
```

#### Caching with Accelerate

```typescript
// Cache for 60 seconds
const users = await prisma.user.findMany({
  cacheStrategy: {
    ttl: 60,      // Time to live in seconds
    sttl: 120,    // Stale-while-revalidate window
  },
})
```

| Strategy | Behavior |
|----------|----------|
| `ttl` only | Cache for N seconds, then fetch fresh |
| `sttl` only | Always serve from cache, revalidate in background |
| `ttl` + `sttl` | Serve fresh for `ttl`, then stale for `sttl` while revalidating |

### Serverless Pool Configuration

For serverless without Accelerate or PgBouncer:

```typescript
import { PrismaPg } from '@prisma/adapter-pg'

const adapter = new PrismaPg({
  connectionString: process.env.DATABASE_URL,
  max: 1,  // Minimal pool for serverless
})

const prisma = new PrismaClient({ adapter })
```

Set `max: 1` to minimize connections per function instance.

## Edge Deployment

### Cloudflare Workers / Vercel Edge

Edge runtimes cannot open TCP connections directly. Use Prisma Accelerate as the bridge:

```typescript
// Works on edge runtimes (no direct DB connection needed)
import { PrismaClient } from '@prisma/client/edge'
import { withAccelerate } from '@prisma/extension-accelerate'

const prisma = new PrismaClient().$extends(withAccelerate())
```

The edge client communicates with Prisma Accelerate over HTTPS, which proxies to the database.

### Edge vs Serverless Decision

| Factor | Edge (Workers/Edge Functions) | Serverless (Lambda/Functions) |
|--------|-------------------------------|-------------------------------|
| Cold start | ~0ms | 100-500ms |
| TCP connections | Not available | Available |
| Direct DB access | No (needs proxy) | Yes |
| Runtime | V8 isolate | Node.js |
| Best for | Read-heavy, cached data | Write-heavy, complex queries |

## Error Handling

### Common Prisma Error Codes

| Code | Name | Cause | Handling |
|------|------|-------|----------|
| `P2002` | Unique constraint violation | Duplicate value on unique field | Return 409 Conflict or retry with different data |
| `P2025` | Record not found | `update`/`delete` target does not exist | Return 404 Not Found |
| `P2003` | Foreign key constraint failure | Referenced record does not exist | Validate input, return 400 |
| `P2024` | Connection pool timeout | Pool exhausted, too many connections | Increase pool size or add pooler |
| `P2034` | Transaction write conflict | Serializable isolation conflict | Retry the transaction |
| `P1001` | Cannot reach database | Network issue, database down | Retry with backoff, alert |
| `P1008` | Query timeout | Query took too long | Optimize query, increase timeout |

### Error Handling Pattern

```typescript
import { Prisma } from '@prisma/client'

async function createUser(email: string, name: string) {
  try {
    return await prisma.user.create({ data: { email, name } })
  } catch (error) {
    if (error instanceof Prisma.PrismaClientKnownRequestError) {
      switch (error.code) {
        case 'P2002':
          const target = (error.meta?.target as string[])?.join(', ')
          throw new ConflictError(`Duplicate value on: ${target}`)
        case 'P2025':
          throw new NotFoundError('Record not found')
        case 'P2003':
          throw new BadRequestError('Referenced record does not exist')
        default:
          throw new InternalError(`Database error: ${error.code}`)
      }
    }
    if (error instanceof Prisma.PrismaClientValidationError) {
      throw new BadRequestError('Invalid query parameters')
    }
    throw error
  }
}
```

### Retry with Exponential Backoff

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  options: { maxRetries?: number; baseDelay?: number; retryOn?: string[] } = {}
): Promise<T> {
  const { maxRetries = 3, baseDelay = 100, retryOn = ['P2034', 'P1001', 'P1008'] } = options
  let lastError: Error

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      if (
        error instanceof Prisma.PrismaClientKnownRequestError &&
        retryOn.includes(error.code) &&
        attempt < maxRetries
      ) {
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 100
        await new Promise(resolve => setTimeout(resolve, delay))
        continue
      }
      throw error
    }
  }
  throw lastError!
}

// Usage
const user = await withRetry(() =>
  prisma.user.create({ data: { email: 'alice@example.com' } })
)
```

## Prisma Client Generation

### When to Generate

| Event | Command |
|-------|---------|
| After `npm install` (fresh clone) | `prisma generate` (add to `postinstall` script) |
| After schema changes | `prisma generate` (automatic with `migrate dev`) |
| In Docker build | `RUN npx prisma generate` |
| In CI pipeline | `npx prisma generate` before build step |

### Postinstall Hook

```json
{
  "scripts": {
    "postinstall": "prisma generate"
  }
}
```

This ensures Prisma Client is generated after every `npm install`, including in CI and Docker builds.

### Output Location

```prisma
generator client {
  provider = "prisma-client-js"
  output   = "./generated/prisma"
}
```

Custom output paths are useful in monorepos to place generated types near the consuming package. Import from the custom path:

```typescript
import { PrismaClient } from './generated/prisma'
```

## Deployment Checklist

| Step | Command/Action | Environment |
|------|---------------|-------------|
| Generate client | `npx prisma generate` | CI/Build |
| Run migrations | `npx prisma migrate deploy` | CI/Deploy |
| Set DATABASE_URL | Environment variable / secrets | Production |
| Configure pool size | Driver adapter options | Production |
| Add health check | `SELECT 1` endpoint | Production |
| Set up monitoring | Query logging, error tracking | Production |
| Graceful shutdown | `$disconnect()` on SIGTERM | Production |
| Backup strategy | pg_dump / managed backups | Production |
