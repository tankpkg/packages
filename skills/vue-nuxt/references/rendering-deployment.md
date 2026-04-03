# Rendering and Deployment

Sources: Nuxt 3 official documentation (nuxt.com/docs/guide/concepts/rendering), Nitro documentation (nitro.build), Pooya Parsa (Nitro/UnJS creator), Nuxt deployment presets documentation

Covers: SSR, SSG, ISR, SWR, hybrid rendering with routeRules, SEO (useHead, useSeoMeta), Nitro deployment presets, edge rendering, Docker patterns, and performance optimization.

## Rendering Modes

### Server-Side Rendering (SSR)

Default mode. Server generates HTML for each request. Client hydrates and takes over.

```typescript
// nuxt.config.ts -- SSR is the default
export default defineNuxtConfig({
  ssr: true  // default, can omit
})
```

| Advantage | Trade-off |
|-----------|-----------|
| SEO -- crawlers get full HTML | Server required (not static hosting) |
| Fast first contentful paint | Server compute cost per request |
| Social sharing meta tags work | More complex deployment |
| Works without JavaScript | Hydration overhead on client |

### Static Site Generation (SSG)

Pre-renders all pages at build time. Deploy to any static host.

```bash
npx nuxi generate
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  // Pages discovered automatically via crawler
  // Or specify routes explicitly:
  nitro: {
    prerender: {
      routes: ['/about', '/contact'],
      crawlLinks: true   // default: true
    }
  }
})
```

| Advantage | Trade-off |
|-----------|-----------|
| No server needed | Build time scales with page count |
| CDN-cacheable everywhere | Data stale until rebuild |
| Cheapest hosting | Dynamic routes need enumeration |
| Fastest TTFB | User-specific content requires client fetch |

### Client-Side Rendering (CSR)

Disable SSR entirely. Traditional SPA behavior.

```typescript
// nuxt.config.ts -- global CSR
export default defineNuxtConfig({
  ssr: false
})
```

Use per-route with routeRules instead of disabling globally.

### Hybrid Rendering (routeRules)

Mix rendering strategies per route. The most powerful Nuxt rendering feature.

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Static at build time
    '/': { prerender: true },
    '/about': { prerender: true },

    // ISR: generate on first request, revalidate every hour
    '/blog/**': { isr: 3600 },

    // SWR: serve stale, revalidate in background
    '/products/**': { swr: 3600 },

    // SWR with immediate revalidation
    '/dashboard': { swr: true },

    // Client-side only (no SSR)
    '/admin/**': { ssr: false },

    // CORS headers for API routes
    '/api/**': { cors: true },

    // Redirect
    '/old-page': { redirect: '/new-page' },

    // Cache headers
    '/static/**': {
      headers: { 'cache-control': 'public, max-age=31536000, immutable' }
    }
  }
})
```

### Rendering Mode Decision Tree

| Route Characteristics | Mode | routeRule |
|----------------------|------|-----------|
| Content rarely changes (about, terms) | SSG | `prerender: true` |
| Content changes hourly/daily (blog, catalog) | ISR | `isr: 3600` |
| Content changes frequently, SEO matters | SWR | `swr: true` |
| Full SSR needed (personalized, real-time) | SSR | Default (no rule) |
| Admin panel, no SEO needed | CSR | `ssr: false` |
| Marketing landing pages | SSG | `prerender: true` |
| API endpoints | -- | `cors: true` if needed |

### ISR vs SWR

| Feature | ISR | SWR |
|---------|-----|-----|
| First request | Generates and caches | Generates and caches |
| Subsequent requests | Serves cache until TTL | Always serves cache |
| After TTL | Next request triggers regeneration, serves stale | Background revalidation, never blocks |
| Best for | Content with clear freshness requirements | Content where staleness is acceptable |
| CDN behavior | May purge and regenerate | Serves stale while updating |

## SEO

### useHead

Set page-level `<head>` tags:

```vue
<script setup lang="ts">
useHead({
  title: 'My Page Title',
  meta: [
    { name: 'description', content: 'Page description for SEO' },
    { property: 'og:title', content: 'My Page Title' },
    { property: 'og:description', content: 'Page description' },
    { property: 'og:image', content: 'https://example.com/og.png' }
  ],
  link: [
    { rel: 'canonical', href: 'https://example.com/page' }
  ],
  script: [
    { type: 'application/ld+json', innerHTML: JSON.stringify(structuredData) }
  ]
})
```

### useSeoMeta (Preferred)

Type-safe, flat API for SEO meta tags:

```vue
<script setup lang="ts">
useSeoMeta({
  title: 'My Page Title',
  description: 'Page description for SEO',
  ogTitle: 'My Page Title',
  ogDescription: 'Page description',
  ogImage: 'https://example.com/og.png',
  ogType: 'website',
  twitterCard: 'summary_large_image',
  twitterTitle: 'My Page Title',
  twitterDescription: 'Page description',
  twitterImage: 'https://example.com/og.png',
  robots: 'index, follow'
})
```

### Dynamic SEO

```vue
<script setup lang="ts">
const { data: post } = await useFetch(`/api/posts/${route.params.slug}`)

useSeoMeta({
  title: () => post.value?.title ?? 'Loading...',
  description: () => post.value?.excerpt,
  ogTitle: () => post.value?.title,
  ogImage: () => post.value?.coverImage
})
</script>
```

### Title Template

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  app: {
    head: {
      titleTemplate: '%s | My App'
    }
  }
})
```

Set `title: 'Home'` in a page -- renders as "Home | My App".

## Nitro Deployment Presets

Nitro is Nuxt's server engine. Presets adapt the build output for different hosting platforms.

### Preset Selection

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'node-server'  // specify target platform
  }
})
```

Or use environment variable:

```bash
NITRO_PRESET=cloudflare-pages npx nuxi build
```

### Available Presets

| Preset | Platform | SSR | Notes |
|--------|----------|-----|-------|
| `node-server` | Node.js (default) | Yes | Standard Node server, works anywhere |
| `node-cluster` | Node.js cluster | Yes | Multi-process for CPU-bound workloads |
| `static` | Static hosting | No (SSG) | `nuxi generate` output |
| `vercel` | Vercel | Yes | Auto-detected on Vercel |
| `vercel-edge` | Vercel Edge Functions | Yes | Edge runtime |
| `netlify` | Netlify | Yes | Auto-detected on Netlify |
| `netlify-edge` | Netlify Edge | Yes | Deno-based edge |
| `cloudflare-pages` | Cloudflare Pages | Yes | Workers runtime |
| `cloudflare-module` | Cloudflare Workers | Yes | Module worker format |
| `aws-lambda` | AWS Lambda | Yes | API Gateway compatible |
| `deno-server` | Deno | Yes | Deno runtime |
| `bun` | Bun | Yes | Bun runtime |
| `firebase` | Firebase Hosting | Yes | Cloud Functions backend |
| `digital-ocean` | DigitalOcean App Platform | Yes | App Platform deployment |

### Docker Deployment

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx nuxi build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.output /app/.output

ENV HOST=0.0.0.0
ENV PORT=3000
EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
```

### Environment Variables in Production

```bash
# Runtime config override (server-side)
NUXT_API_SECRET=production-secret

# Public runtime config override (client + server)
NUXT_PUBLIC_API_BASE=https://api.production.com

# Nitro config
NITRO_PORT=3000
NITRO_HOST=0.0.0.0
```

## Edge Rendering

Deploy Nuxt to edge networks for lowest latency. Rendering happens at the CDN edge closest to the user.

### Constraints

| Feature | Edge Support |
|---------|-------------|
| Node.js APIs (fs, path) | Not available |
| npm packages with native deps | Not supported |
| Long-running processes | Timeout limits (varies by platform) |
| WebSocket | Limited |
| Database connections | Use HTTP-based clients (Prisma Edge, PlanetScale) |

### Edge-Compatible Database Access

```typescript
// server/utils/db.ts
import { PrismaClient } from '@prisma/client/edge'
import { withAccelerate } from '@prisma/extension-accelerate'

export const prisma = new PrismaClient().$extends(withAccelerate())
```

## Performance Optimization

### Payload Optimization

```typescript
// Reduce SSR payload by picking only needed fields
const { data } = await useFetch('/api/large-dataset', {
  pick: ['id', 'title', 'slug']  // only these fields in payload
})

// Transform to reduce size
const { data } = await useFetch('/api/posts', {
  transform: (posts) => posts.map(({ id, title }) => ({ id, title }))
})
```

### Component Lazy Loading

```vue
<template>
  <!-- Lazy-load heavy components -->
  <LazyHeavyChart v-if="showChart" :data="chartData" />

  <!-- Auto-prefixed: components/HeavyChart.vue -->
</template>
```

Prefix any component with `Lazy` to defer loading until it renders.

### Payload Reducer (Nuxt 3.4+)

Register custom serializers for complex types:

```typescript
// plugins/payload-reducer.ts
export default definePayloadPlugin((nuxtApp) => {
  definePayloadReducer('Date', (val) =>
    val instanceof Date && val.toISOString()
  )
  definePayloadReviver('Date', (val) => new Date(val))
})
```

### Build Optimization

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  // Tree-shake unused components
  components: {
    dirs: ['~/components']  // explicit directories
  },

  // Experimental features
  experimental: {
    payloadExtraction: true,    // extract payload to separate file
    treeshakeClientOnly: true   // tree-shake server-only code from client
  },

  // Vite optimization
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'vue-router']
          }
        }
      }
    }
  }
})
```

### Image Optimization

Use `@nuxt/image` for automatic optimization:

```vue
<template>
  <NuxtImg
    src="/images/hero.jpg"
    width="800"
    height="400"
    format="webp"
    loading="lazy"
    placeholder
  />
</template>
```

## Common Deployment Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| SSG for user-specific content | Content same for all users | Use SSR or client-side fetch |
| No `NUXT_` prefix on env vars | Runtime config not overridden | Prefix with `NUXT_` or `NUXT_PUBLIC_` |
| Edge preset with Node.js deps | Build fails or runtime crash | Audit dependencies for edge compatibility |
| Missing `prerender` for static routes | Pages not generated | Add to `routeRules` or `nitro.prerender.routes` |
| Large SSR payload | Slow hydration, large HTML | Use `pick`, `transform`, payload extraction |
| No cache headers on static assets | Repeated downloads | Set `cache-control` via routeRules |
