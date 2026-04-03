# Nuxt Data Fetching

Sources: Nuxt 3 official documentation (nuxt.com/docs/getting-started/data-fetching), Nuxt GitHub discussions, Daniel Roe (Nuxt core team), ofetch/unjs documentation

Covers: useFetch, useAsyncData, $fetch, server routes and API patterns, caching keys, error handling, request deduplication, serialization, and lazy loading.

## The Three Fetching Primitives

Nuxt provides three ways to fetch data. Each serves a different purpose.

| Primitive | SSR-Safe | Deduplication | Reactive | Use Case |
|-----------|----------|---------------|----------|----------|
| `useFetch` | Yes | Yes (by URL) | Yes | Component data with SSR hydration |
| `useAsyncData` | Yes | Yes (by key) | Yes | Complex fetch logic with SSR hydration |
| `$fetch` | No* | No | No | Client-only mutations, server routes, non-component code |

*`$fetch` inside `useAsyncData` becomes SSR-safe.

### Why Not Plain fetch()?

Using `fetch()` or `$fetch()` directly in `<script setup>` causes double data fetching -- once on the server during SSR, then again on the client during hydration. `useFetch` and `useAsyncData` solve this by transferring server-fetched data to the client via payload.

## useFetch

Shorthand for `useAsyncData` + `$fetch`. Use for straightforward API calls.

```vue
<script setup lang="ts">
interface User {
  id: number
  name: string
  email: string
}

const { data, status, error, refresh, clear } = await useFetch<User[]>('/api/users')
</script>

<template>
  <div v-if="status === 'pending'">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <ul v-else>
    <li v-for="user in data" :key="user.id">{{ user.name }}</li>
  </ul>
</template>
```

### Return Values

| Property | Type | Description |
|----------|------|-------------|
| `data` | `Ref<T \| null>` | Fetched data (null until resolved) |
| `status` | `Ref<'idle' \| 'pending' \| 'success' \| 'error'>` | Current fetch state |
| `error` | `Ref<Error \| null>` | Error object if request failed |
| `refresh()` | `() => Promise<void>` | Re-execute the fetch |
| `execute()` | `() => Promise<void>` | Same as refresh (alias) |
| `clear()` | `() => void` | Clear data, reset status to idle |

### Common Options

```typescript
const { data } = await useFetch('/api/users', {
  // Request options (passed to $fetch / ofetch)
  method: 'GET',
  headers: { 'Authorization': `Bearer ${token}` },
  query: { page: 1, limit: 20 },
  body: { name: 'Alice' },          // for POST/PUT/PATCH

  // Nuxt options
  key: 'users-list',                // custom deduplication key
  server: true,                      // fetch on server (default: true)
  lazy: false,                       // false = block navigation until resolved
  immediate: true,                   // fetch immediately (default: true)
  default: () => [],                 // default value before fetch resolves
  transform: (data) => data.items,   // transform response
  pick: ['id', 'name'],             // pick specific fields (reduces payload)
  watch: [page],                     // re-fetch when these refs change
  deep: true,                        // deep reactive data (default: true)
  dedupe: 'cancel',                  // 'cancel' | 'defer' for concurrent requests
  getCachedData: (key, nuxtApp) => { // custom cache strategy
    return nuxtApp.payload.data[key] || nuxtApp.static.data[key]
  }
})
```

### Reactive Query Parameters

Pass refs as query parameters -- `useFetch` re-fetches automatically when they change:

```vue
<script setup lang="ts">
const page = ref(1)
const search = ref('')

const { data: users } = await useFetch('/api/users', {
  query: { page, search, limit: 20 }
})
// Changing page.value or search.value triggers a refetch
</script>
```

## useAsyncData

Use when fetch logic is more complex than a single URL, or when combining multiple sources.

```typescript
// Single complex fetch
const { data: user } = await useAsyncData('user', () =>
  $fetch(`/api/users/${route.params.id}`)
)

// Multiple parallel fetches
const { data } = await useAsyncData('dashboard', async () => {
  const [users, stats, notifications] = await Promise.all([
    $fetch('/api/users'),
    $fetch('/api/stats'),
    $fetch('/api/notifications')
  ])
  return { users, stats, notifications }
})

// With external SDK
const { data } = await useAsyncData('posts', () =>
  supabase.from('posts').select('*').order('created_at', { ascending: false })
)
```

### Key Requirements

The first argument is a unique cache key. Rules:

| Key Rule | Reason |
|----------|--------|
| Must be unique across the app | Prevents data collision |
| Must be a static string (not dynamic expression) | Enables payload deduplication |
| Use route params for dynamic keys | `\`user-${route.params.id}\`` for per-item caching |
| Omit key = auto-generated from file + line | Works but harder to debug |

## $fetch

Nuxt's universal HTTP client (built on `ofetch`). Use for non-component contexts and client-only actions.

### When to Use $fetch Directly

```typescript
// Client-only form submission
async function handleSubmit() {
  await $fetch('/api/users', {
    method: 'POST',
    body: { name: formData.name, email: formData.email }
  })
}

// Inside server routes (server-to-server)
export default defineEventHandler(async () => {
  const data = await $fetch('https://external-api.com/data')
  return data
})

// Inside useAsyncData (makes it SSR-safe)
const { data } = await useAsyncData('key', () => $fetch('/api/endpoint'))
```

### $fetch vs useFetch Decision

| Context | Use | Reason |
|---------|-----|--------|
| `<script setup>` data loading | `useFetch` | SSR hydration, deduplication |
| `<script setup>` complex logic | `useAsyncData` + `$fetch` | Multiple sources, transforms |
| Event handler (button click) | `$fetch` | Client-only, no SSR needed |
| Server route | `$fetch` | Server-side, no hydration |
| Pinia store action | `$fetch` | Non-component context |
| Middleware | `$fetch` | Non-component context |

## Server Routes

### Basic API Routes

```typescript
// server/api/users.get.ts -- GET /api/users
export default defineEventHandler(async (event) => {
  const query = getQuery(event)    // { page: '1', limit: '20' }
  const users = await db.users.findMany({
    skip: (Number(query.page) - 1) * Number(query.limit),
    take: Number(query.limit)
  })
  return users
})

// server/api/users.post.ts -- POST /api/users
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const user = await db.users.create({ data: body })
  return user
})

// server/api/users/[id].get.ts -- GET /api/users/:id
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const user = await db.users.findUnique({ where: { id: Number(id) } })
  if (!user) {
    throw createError({ statusCode: 404, statusMessage: 'User not found' })
  }
  return user
})
```

### HTTP Method Suffixes

| File | Method | Route |
|------|--------|-------|
| `server/api/users.get.ts` | GET | `/api/users` |
| `server/api/users.post.ts` | POST | `/api/users` |
| `server/api/users/[id].put.ts` | PUT | `/api/users/:id` |
| `server/api/users/[id].delete.ts` | DELETE | `/api/users/:id` |
| `server/api/users/[id].patch.ts` | PATCH | `/api/users/:id` |
| `server/api/users.ts` (no suffix) | All methods | `/api/users` |

### Server Route Utilities

```typescript
export default defineEventHandler(async (event) => {
  // Read request data
  const body = await readBody(event)         // POST/PUT body
  const query = getQuery(event)              // URL query params
  const params = getRouterParam(event, 'id') // Route params
  const headers = getHeaders(event)          // Request headers
  const cookies = parseCookies(event)        // Cookies

  // Set response
  setResponseStatus(event, 201)
  setResponseHeader(event, 'X-Custom', 'value')
  setCookie(event, 'session', 'abc123', { httpOnly: true })

  return { success: true }
})
```

### Input Validation

Use `zod` or `h3-zod` for runtime validation in server routes:

```typescript
import { z } from 'zod'

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'user']).default('user')
})

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const parsed = CreateUserSchema.safeParse(body)

  if (!parsed.success) {
    throw createError({
      statusCode: 400,
      data: parsed.error.issues
    })
  }

  return await db.users.create({ data: parsed.data })
})
```

### Server Middleware

Runs on every server request (before route handlers):

```typescript
// server/middleware/auth.ts
export default defineEventHandler((event) => {
  const token = getHeader(event, 'authorization')?.replace('Bearer ', '')

  if (event.path.startsWith('/api/admin') && !token) {
    throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  }

  // Attach user to event context for downstream handlers
  if (token) {
    event.context.user = verifyToken(token)
  }
})
```

## Lazy Fetching

Defer fetching until after navigation completes (non-blocking):

```typescript
// Lazy -- does not block navigation
const { data, status } = useLazyFetch('/api/heavy-data')

// Equivalent
const { data, status } = useFetch('/api/heavy-data', { lazy: true })

// Show loading while data arrives
// status.value === 'pending' until resolved
```

Use `lazy: true` for below-the-fold content or secondary data that should not delay page rendering.

## Error Handling

```vue
<script setup lang="ts">
const { data, error } = await useFetch('/api/users')

// Watch for errors
watch(error, (err) => {
  if (err) {
    console.error('Fetch failed:', err.message)
  }
})
</script>

<template>
  <div v-if="error">
    <p>Failed to load: {{ error.statusCode }} {{ error.message }}</p>
    <button @click="refresh()">Retry</button>
  </div>
</template>
```

For server routes, throw `createError()` -- Nuxt serializes it to the client:

```typescript
throw createError({
  statusCode: 403,
  statusMessage: 'Forbidden',
  data: { reason: 'Insufficient permissions' }  // accessible via error.data
})
```

## Serialization Awareness

Data transferred from server to client via JSON serialization. Non-serializable types are lost:

| Type | Serializes | Workaround |
|------|-----------|------------|
| Date | Converts to string | Parse with `new Date()` in `transform` |
| Map/Set | Lost | Convert to array/object |
| Functions | Lost | Cannot transfer |
| undefined | Lost (becomes null) | Use null explicitly |
| BigInt | Error | Convert to string |

```typescript
const { data } = await useFetch('/api/posts', {
  transform: (posts) => posts.map(p => ({
    ...p,
    createdAt: new Date(p.createdAt)  // restore Date objects
  }))
})
```

## Refreshing Data

```typescript
const { data, refresh } = await useFetch('/api/users')

// Manual refresh
async function handleRefresh() {
  await refresh()
}

// Refresh all data on the page
await refreshNuxtData()

// Refresh specific keys
await refreshNuxtData('users')
await refreshNuxtData(['users', 'stats'])
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `$fetch` in `<script setup>` without wrapper | Double fetch (server + client) | Wrap in `useFetch` or `useAsyncData` |
| Duplicate keys in `useAsyncData` | Data collision, stale responses | Use unique keys per data source |
| Mutating `data.value` directly | Bypasses reactivity tracking | Use `refresh()` or replace entire value |
| Not handling `null` data | Template errors before fetch resolves | Use `v-if="data"` or `default` option |
| Forgetting `await` on `useFetch` | Data undefined during SSR | Always `await` in `<script setup>` |
| Large payloads without `pick` | Bloated HTML payload, slow hydration | Use `pick` to select needed fields |
| Using `watch` + manual `$fetch` | Reinventing `useFetch` reactivity | Use `watch` option in `useFetch` instead |
