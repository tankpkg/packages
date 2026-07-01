# Self-Hosting and CDN Caching

Sources: Next.js official documentation (v15-16), Vercel engineering blog (self-hosting improvements), Next.js GitHub discussions, Cloudflare Workers documentation, AWS CloudFront documentation

Covers: Cache-Control header management, CDN integration patterns, expireTime configuration, custom cache handlers, ISR with self-hosting, edge caching patterns, and troubleshooting CDN + Next.js interactions.

## Cache-Control Headers

### Default Headers for ISR Pages

Next.js sets `Cache-Control` headers automatically for ISR pages:

```
Cache-Control: s-maxage=<revalidate>, stale-while-revalidate=<expireTime>
```

| Component | Meaning | Default |
|-----------|---------|---------|
| `s-maxage` | How long CDN/shared caches consider the response fresh | Value from `revalidate` config |
| `stale-while-revalidate` | How long CDN can serve stale while revalidating in background | 1 year (Next.js 15+) |

### expireTime Configuration

Control the `stale-while-revalidate` window (previously `experimental.swrDelta`):

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  expireTime: 3600, // 1 hour stale-while-revalidate window
}
```

| Value | Effect |
|-------|--------|
| Default (1 year) | CDN can serve stale content for up to a year while revalidating |
| `3600` | CDN serves stale for max 1 hour, then must wait for fresh |
| `0` | CDN never serves stale; waits for revalidation to complete |

Longer `expireTime` values maximize cache hit rates but increase how long stale content can be served during revalidation.

### Custom Cache-Control Headers

Next.js 15+ no longer overrides custom `Cache-Control` headers. Set them in Route Handlers or middleware:

```typescript
// app/api/data/route.ts
export async function GET() {
  const data = await fetchData()

  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, s-maxage=600, stale-while-revalidate=3600',
    },
  })
}
```

### Header Precedence

| Source | Priority | Notes |
|--------|----------|-------|
| Custom `Cache-Control` in response | Highest | Not overridden in Next.js 15+ |
| Route segment `revalidate` | Medium | Sets `s-maxage` automatically |
| CDN configuration | Varies | CDN may override or respect origin headers |

## Custom Cache Handlers

Replace the default filesystem cache with a custom backend (Redis, S3, DynamoDB, etc.):

### Configuration

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  cacheHandler: require.resolve('./cache-handler.mjs'),
  cacheMaxMemorySize: 0, // Disable in-memory cache, use handler only
}
```

Or via environment variable:

```bash
NEXT_CACHE_HANDLER_PATH=./cache-handler.mjs
```

### Cache Handler Interface

```typescript
// cache-handler.mjs
export default class CacheHandler {
  constructor(options) {
    // options.serverDistDir — path to .next/server
    // options.dev — true in development
  }

  async get(key) {
    // Return { value, lastModified } or null
    const entry = await redis.get(`cache:${key}`)
    if (!entry) return null
    return JSON.parse(entry)
  }

  async set(key, data, ctx) {
    // ctx.revalidate — revalidation interval
    // ctx.tags — cache tags
    const ttl = ctx.revalidate || 3600
    await redis.set(`cache:${key}`, JSON.stringify({
      value: data,
      lastModified: Date.now(),
      tags: ctx.tags,
    }), 'EX', ttl)
  }

  async revalidateTag(tags) {
    // Invalidate all entries matching any of the provided tags
    for (const tag of tags) {
      const keys = await redis.smembers(`tag:${tag}`)
      if (keys.length > 0) {
        await redis.del(...keys)
        await redis.del(`tag:${tag}`)
      }
    }
  }
}
```

### Cache Handler for use cache (Next.js 16+)

```typescript
// next.config.ts
const nextConfig: NextConfig = {
  cacheComponents: true,
  cacheHandlers: {
    default: require.resolve('./cache-handler-default.mjs'),
    remote: require.resolve('./cache-handler-remote.mjs'),
  },
}
```

The `default` handler serves `'use cache'` entries. The `remote` handler serves `'use cache: remote'` entries.

## CDN Integration Patterns

### Pattern 1: CDN Respects Origin Headers

Configure the CDN to respect `Cache-Control` headers from Next.js:

```
Browser → CDN → Next.js Server
         ↑
    Caches based on
    Cache-Control from origin
```

**Cloudflare**: Default behavior respects origin `Cache-Control`. Add a Page Rule or Cache Rule to override if needed.

**AWS CloudFront**: Set Cache Policy to "Use origin cache control headers".

**Nginx**:

```nginx
location / {
  proxy_pass http://nextjs:3000;
  proxy_cache_valid 200 60s;
  proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
  add_header X-Cache-Status $upstream_cache_status;
}
```

### Pattern 2: CDN as Primary Cache, Next.js Dynamic

For CDN-first caching where Next.js always renders fresh:

```
Browser → CDN (caches) → Next.js Server (always dynamic)
```

```typescript
// next.config.ts — all routes dynamic
const nextConfig: NextConfig = {
  // Let CDN handle caching
}

// Pages set Cache-Control for CDN
export default async function Page() {
  const data = await fetchFreshData()
  // Headers set via middleware or route handler
  return <div>{data}</div>
}
```

### Pattern 3: ISR Behind CDN

ISR works naturally with CDN caching:

```
Browser → CDN → Next.js ISR
    ↑              ↑
    CDN cache    Full Route Cache
    (respects     (ISR revalidation)
     s-maxage)
```

**Consideration**: Both CDN and Next.js cache the page. Revalidation happens at the Next.js layer. The CDN may still serve stale content if its TTL has not expired.

**Solution**: Set CDN TTL equal to or less than ISR `revalidate`:

```typescript
export const revalidate = 300 // Next.js revalidates every 5 min

// Middleware to set CDN-friendly headers
export function middleware(request: NextRequest) {
  const response = NextResponse.next()
  // CDN caches for 4 min (less than ISR interval)
  response.headers.set('CDN-Cache-Control', 'max-age=240')
  return response
}
```

### Pattern 4: Edge Caching with Purge API

Use on-demand revalidation with CDN purge for immediate freshness:

```typescript
// app/actions.ts
'use server'
import { revalidateTag } from 'next/cache'

export async function updateProduct(id: string) {
  await db.product.update({ where: { id } })

  // Step 1: Invalidate Next.js cache
  revalidateTag(`product-${id}`)

  // Step 2: Purge CDN cache
  await fetch('https://api.cloudflare.com/client/v4/zones/ZONE/purge_cache', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.CF_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      files: [`https://your-app.com/products/${id}`]
    }),
  })
}
```

## ISR with Self-Hosting

### Filesystem Cache

By default, self-hosted Next.js uses the filesystem for ISR cache (`.next/cache/`). This works for single-server deployments.

### Multi-Server Deployments

Multiple server instances do not share the filesystem cache. Use a shared cache handler:

| Approach | Complexity | Performance |
|----------|-----------|-------------|
| Shared NFS/EFS volume | Low | Moderate (network filesystem) |
| Redis cache handler | Medium | Fast (in-memory) |
| S3/GCS cache handler | Medium | Moderate (object storage) |
| Custom database handler | High | Varies |

### Docker Deployments

```dockerfile
FROM node:20-alpine AS runner
WORKDIR /app

# Copy build output
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Ensure cache directory is writable
RUN mkdir -p .next/cache && chown -R node:node .next/cache

USER node
EXPOSE 3000
CMD ["node_modules/.bin/next", "start"]
```

### Persistent Cache Across Deployments

Mount a persistent volume for the cache directory:

```yaml
# docker-compose.yml
services:
  nextjs:
    image: your-app
    volumes:
      - next-cache:/app/.next/cache
    environment:
      - NEXT_PRIVATE_DEBUG_CACHE=1

volumes:
  next-cache:
```

Without persistent cache, every deployment starts with an empty cache. All ISR pages regenerate on first request.

## Troubleshooting CDN + Next.js

| Problem | Cause | Fix |
|---------|-------|-----|
| CDN serves stale after revalidation | CDN TTL longer than ISR interval | Reduce CDN TTL or add purge |
| Double caching (CDN + Next.js) | Both layers cache independently | Align TTLs, or make Next.js dynamic and let CDN cache |
| `revalidateTag` has no effect | CDN cache not purged | Add CDN purge API call after revalidation |
| ISR not working in Docker | Cache directory not writable or not persisted | Mount persistent volume, fix permissions |
| Different content across CDN nodes | CDN not propagating purge globally | Use purge-all or wait for propagation |
| Cache-Control headers missing | Middleware or CDN overriding | Check middleware, CDN rules, and Next.js config |
| Self-hosted ISR slower than Vercel | Filesystem cache vs Vercel edge cache | Use Redis/shared cache handler |

## Platform-Specific Notes

### Vercel

- ISR cache is distributed globally at the edge automatically
- No custom cache handler needed
- `revalidateTag` propagates to all edge regions
- `x-vercel-cache` header shows CDN status

### Cloudflare

- Use Cloudflare Workers or Pages for Next.js hosting
- Configure `Cache-Control` and `CDN-Cache-Control` separately
- Use `cf-cache-status` header to debug
- Purge API available for on-demand invalidation

### AWS (CloudFront + ECS/Lambda)

- CloudFront respects `s-maxage` by default
- Use Lambda@Edge or CloudFront Functions for header manipulation
- Invalidation API for purging specific paths
- Consider DynamoDB or ElastiCache Redis for shared cache handler

For cache debugging tools, see `references/cache-debugging.md`.
For version-specific defaults, see `references/version-migration.md`.
