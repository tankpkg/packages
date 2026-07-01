# Nuxt 3 Fundamentals

Sources: Nuxt 3 official documentation (nuxt.com), Nuxt GitHub repository (nuxt/nuxt), Daniel Roe (Nuxt core team talks), Pooya Parsa (Nitro/UnJS creator)

Covers: Directory structure, auto-imports, plugins, layouts, middleware, runtime config, nuxt.config.ts, error handling, and Nuxt DevTools.

## Directory Structure

```
app/                    # Application source (Nuxt 4 default, optional in Nuxt 3)
  components/           # Auto-imported Vue components
  composables/          # Auto-imported composables (use*.ts)
  layouts/              # Layout components (default.vue, admin.vue)
  middleware/           # Route middleware
  pages/                # File-based routing
  plugins/              # App plugins (run before mount)
  utils/                # Auto-imported utility functions
  app.vue               # Root component
  error.vue             # Global error page
content/                # Nuxt Content markdown files (if module installed)
public/                 # Static assets (served as-is at /)
server/                 # Server-side code (Nitro)
  api/                  # API routes (/api/*)
  routes/               # Server routes (any path)
  middleware/            # Server middleware (runs on every request)
  plugins/              # Nitro plugins (server lifecycle)
  utils/                # Server-only utilities (auto-imported)
nuxt.config.ts          # Nuxt configuration
app.config.ts           # Runtime app configuration (client-accessible)
```

### Key Directory Rules

| Directory | Auto-Import | Available On | Notes |
|-----------|------------|--------------|-------|
| `components/` | Yes, by filename | Client + Server | Nested dirs create prefix: `base/Button.vue` = `<BaseButton>` |
| `composables/` | Yes, top-level exports | Client + Server | Only `use*` naming convention is auto-imported |
| `utils/` | Yes, top-level exports | Client + Server | Helpers, formatters, constants |
| `server/utils/` | Yes, top-level exports | Server only | Never shipped to client bundle |
| `server/api/` | By file path | Server only | `server/api/users.get.ts` = `GET /api/users` |
| `middleware/` | By filename | Client + Server | Route guards, auth checks |
| `plugins/` | Automatic | Client + Server | `.server.ts` / `.client.ts` suffixes for environment targeting |

## Auto-Imports

Nuxt auto-imports Vue APIs, Nuxt composables, components, and your own composables/utils.

### What Gets Auto-Imported

```vue
<script setup lang="ts">
// Vue APIs -- no import needed
const count = ref(0)
const doubled = computed(() => count.value * 2)

// Nuxt composables -- no import needed
const { data } = await useFetch('/api/users')
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

// Your composables from composables/ -- no import needed
const { user, login } = useAuth()

// Your utils from utils/ -- no import needed
const formatted = formatDate(new Date())
</script>
```

### When to Use Explicit Imports

| Scenario | Approach |
|----------|----------|
| Vue/Nuxt APIs | Auto-import (standard) |
| Your composables/utils | Auto-import (standard) |
| Third-party libraries | Explicit import -- keeps dependency graph visible |
| Types and interfaces | Explicit import -- auto-import does not handle types by default |
| Server-only code | Explicit import from `#imports` if needed |

### Disabling Auto-Imports

```typescript
// nuxt.config.ts -- per-project opt-out
export default defineNuxtConfig({
  imports: {
    autoImport: false  // disable for composables/utils
  },
  components: {
    dirs: []  // disable component auto-import
  }
})
```

Prefer keeping auto-imports enabled. Use explicit imports only for third-party code.

### Type Support

Nuxt generates `.nuxt/imports.d.ts` automatically. Run `nuxi prepare` to regenerate type declarations after adding new composables.

## Plugins

Plugins run before the Vue app mounts. Use them for global setup.

### Basic Plugin

```typescript
// plugins/my-plugin.ts
export default defineNuxtPlugin((nuxtApp) => {
  // Access Vue app instance
  const vueApp = nuxtApp.vueApp

  // Register global component
  vueApp.component('GlobalModal', Modal)

  // Register global directive
  vueApp.directive('focus', {
    mounted: (el) => el.focus()
  })

  // Provide helper (accessible via useNuxtApp().$myHelper)
  return {
    provide: {
      myHelper: (msg: string) => console.log(msg)
    }
  }
})
```

### Environment-Specific Plugins

```
plugins/
  analytics.client.ts    # Only runs in browser
  db.server.ts           # Only runs on server
  auth.ts                # Runs on both
```

### Plugin Ordering

```typescript
// plugins/01.auth.ts  -- number prefix controls order
export default defineNuxtPlugin({
  name: 'auth',
  enforce: 'pre',       // 'pre' | 'default' | 'post'
  async setup(nuxtApp) {
    // Runs before other plugins
  }
})
```

### Typed Plugin Provides

```typescript
// plugins/api.ts
export default defineNuxtPlugin(() => {
  const api = {
    getUsers: () => $fetch<User[]>('/api/users'),
    getUser: (id: number) => $fetch<User>(`/api/users/${id}`)
  }

  return { provide: { api } }
})

// Usage in components:
const { $api } = useNuxtApp()
const users = await $api.getUsers()
```

Extend types in `index.d.ts`:

```typescript
declare module '#app' {
  interface NuxtApp {
    $api: {
      getUsers: () => Promise<User[]>
      getUser: (id: number) => Promise<User>
    }
  }
}
```

## Layouts

### Default Layout

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <AppHeader />
    <main>
      <slot />   <!-- Page content renders here -->
    </main>
    <AppFooter />
  </div>
</template>
```

### Named Layouts

```vue
<!-- layouts/admin.vue -->
<template>
  <div class="admin-layout">
    <AdminSidebar />
    <div class="admin-content">
      <slot />
    </div>
  </div>
</template>
```

```vue
<!-- pages/admin/dashboard.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'admin'
})
</script>
```

### Dynamic Layouts

```vue
<script setup lang="ts">
const route = useRoute()
const layout = computed(() =>
  route.meta.isAdmin ? 'admin' : 'default'
)
</script>

<template>
  <NuxtLayout :name="layout">
    <NuxtPage />
  </NuxtLayout>
</template>
```

## Route Middleware

Middleware runs before navigating to a route. Three types:

### Named Middleware

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user } = useAuth()

  if (!user.value) {
    return navigateTo('/login')
  }
})
```

Apply per-page:

```vue
<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})
</script>
```

### Inline Middleware

```vue
<script setup lang="ts">
definePageMeta({
  middleware: [
    function (to, from) {
      if (to.params.id === '0') {
        return abortNavigation()
      }
    }
  ]
})
</script>
```

### Global Middleware

```typescript
// middleware/01.logger.global.ts
export default defineNuxtRouteMiddleware((to, from) => {
  console.log(`Navigating: ${from.path} -> ${to.path}`)
})
```

### Middleware Return Values

| Return | Effect |
|--------|--------|
| Nothing (`undefined`) | Continue navigation |
| `navigateTo('/path')` | Redirect to another route |
| `navigateTo('/login', { external: true })` | External redirect |
| `abortNavigation()` | Cancel navigation |
| `abortNavigation(error)` | Cancel with error (shows error page) |

## Runtime Config

### Definition

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    // Server-only (never exposed to client)
    apiSecret: '',
    dbUrl: '',

    // Client-accessible (under public key)
    public: {
      apiBase: 'https://api.example.com',
      appName: 'My App'
    }
  }
})
```

### Environment Variable Override

Nuxt maps `NUXT_` prefixed env vars automatically:

```bash
NUXT_API_SECRET=my-secret           # -> runtimeConfig.apiSecret
NUXT_DB_URL=postgres://...          # -> runtimeConfig.dbUrl
NUXT_PUBLIC_API_BASE=https://...    # -> runtimeConfig.public.apiBase
```

### Usage

```typescript
// In components/composables (client + server)
const config = useRuntimeConfig()
console.log(config.public.apiBase)

// In server routes (server-only values accessible)
export default defineEventHandler(() => {
  const config = useRuntimeConfig()
  console.log(config.apiSecret)  // only accessible server-side
})
```

### App Config vs Runtime Config

| Feature | `runtimeConfig` | `app.config.ts` |
|---------|----------------|-----------------|
| Environment variables | Yes (NUXT_ prefix) | No |
| Server secrets | Yes (top-level keys) | No |
| Reactive in client | No | Yes (`useAppConfig()`) |
| HMR support | No | Yes |
| Use case | API keys, URLs, secrets | Theme, feature flags, UI config |

## Error Handling

### Page-Level Errors

```vue
<!-- error.vue (root level) -->
<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{
  error: NuxtError
}>()

const handleClear = () => clearError({ redirect: '/' })
</script>

<template>
  <div>
    <h1>{{ error.statusCode }}</h1>
    <p>{{ error.message }}</p>
    <button @click="handleClear">Go Home</button>
  </div>
</template>
```

### Component-Level Error Boundary

```vue
<template>
  <NuxtErrorBoundary @error="logError">
    <SomeComponent />
    <template #error="{ error, clearError }">
      <p>Something went wrong: {{ error.message }}</p>
      <button @click="clearError">Retry</button>
    </template>
  </NuxtErrorBoundary>
</template>
```

### Creating Errors

```typescript
// In server routes
throw createError({
  statusCode: 404,
  statusMessage: 'User not found'
})

// In components (triggers error page)
showError({
  statusCode: 500,
  statusMessage: 'Something went wrong'
})

// Clear error state
clearError({ redirect: '/' })
```

## nuxt.config.ts Key Options

```typescript
export default defineNuxtConfig({
  ssr: true,                          // Enable SSR (default)
  devtools: { enabled: true },         // Nuxt DevTools (Shift+Alt+D)
  modules: ['@pinia/nuxt', '@vueuse/nuxt', '@nuxt/image'],
  typescript: { strict: true, typeCheck: true },
  app: { head: { title: 'My App' } },
  routeRules: { '/': { prerender: true }, '/api/**': { cors: true } },
  nitro: { preset: 'node-server' }
})
```
