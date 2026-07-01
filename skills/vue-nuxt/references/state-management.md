# State Management

Sources: Pinia official documentation (pinia.vuejs.org), VueUse documentation (vueuse.org), Eduardo San Martin Morote (Pinia creator), Anthony Fu (VueUse creator)

Covers: Pinia setup stores and option stores, store composition, persistence plugins, VueUse composables, SSR state hydration, and anti-patterns.

## Pinia Overview

Pinia is the official state management library for Vue 3. It replaces Vuex with a simpler API, full TypeScript support, and Composition API integration.

### Installation (Nuxt)

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@pinia/nuxt']
})
```

Pinia is auto-configured in Nuxt -- no `createPinia()` or `app.use()` needed.

## Store Definitions

### Option Store

Familiar pattern for developers coming from Vuex. Uses `state`, `getters`, and `actions`.

```typescript
// stores/counter.ts
export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
    name: 'Counter'
  }),

  getters: {
    doubleCount: (state) => state.count * 2,
    // Getter using another getter
    doubleCountPlusOne(): number {
      return this.doubleCount + 1
    }
  },

  actions: {
    increment() {
      this.count++
    },
    async fetchCount() {
      const { count } = await $fetch('/api/count')
      this.count = count
    }
  }
})
```

### Setup Store

Uses Composition API syntax. More flexible -- composes naturally with other composables.

```typescript
// stores/counter.ts
export const useCounterStore = defineStore('counter', () => {
  // State (ref = state)
  const count = ref(0)
  const name = ref('Counter')

  // Getters (computed = getters)
  const doubleCount = computed(() => count.value * 2)

  // Actions (functions = actions)
  function increment() {
    count.value++
  }

  async function fetchCount() {
    const { count: serverCount } = await $fetch('/api/count')
    count.value = serverCount
  }

  return { count, name, doubleCount, increment, fetchCount }
})
```

### Which Store Style to Choose

| Signal | Style | Reason |
|--------|-------|--------|
| Simple CRUD state | Option store | Less boilerplate for basic state |
| Complex logic with composables | Setup store | Composes with VueUse, watchers, lifecycle |
| Team from Vuex background | Option store | Familiar state/getters/actions structure |
| New project, TypeScript | Setup store | Better type inference, more flexible |
| Need watchers inside store | Setup store | Option stores cannot use `watch()` directly |
| Use VueUse composables in store | Setup store | Composables require setup context |

Default recommendation: setup stores for new projects.

## Using Stores

```vue
<script setup lang="ts">
const counterStore = useCounterStore()

// Access state
console.log(counterStore.count)

// Call actions
counterStore.increment()

// Destructure with storeToRefs (preserves reactivity)
const { count, doubleCount } = storeToRefs(counterStore)
const { increment } = counterStore  // actions can destructure directly
</script>

<template>
  <p>Count: {{ count }}</p>
  <p>Double: {{ doubleCount }}</p>
  <button @click="increment">+1</button>
</template>
```

### Destructuring Rules

| What | Method | Reason |
|------|--------|--------|
| State and getters | `storeToRefs(store)` | Preserves reactivity |
| Actions | Direct destructure | Functions do not need reactivity wrappers |
| Everything | `store.property` | Always works, no destructuring needed |

Never destructure state/getters without `storeToRefs` -- reactivity is lost.

## Store Composition

Stores can use other stores. Import and call inside actions or setup.

```typescript
// stores/cart.ts
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const authStore = useAuthStore()

  const total = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.qty, 0)
  )

  async function checkout() {
    if (!authStore.isAuthenticated) {
      throw new Error('Must be logged in to checkout')
    }
    await $fetch('/api/orders', {
      method: 'POST',
      body: { items: items.value, userId: authStore.user!.id }
    })
    items.value = []
  }

  return { items, total, checkout }
})
```

Avoid circular dependencies between stores. If store A needs store B and vice versa, extract shared logic into a composable.

## State Reset

```typescript
const store = useCounterStore()

// Reset to initial state
store.$reset()  // Option stores only

// For setup stores, implement manually:
export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)

  function $reset() {
    count.value = 0
  }

  return { count, $reset }
})
```

## Batch State Updates

```typescript
// Patch multiple state properties at once
store.$patch({
  count: store.count + 1,
  name: 'Updated Counter'
})

// Patch with function (for complex mutations)
store.$patch((state) => {
  state.items.push({ id: 1, name: 'New Item' })
  state.total = state.items.length
})
```

## Pinia Plugins

### Persistence Plugin

```bash
npm install pinia-plugin-persistedstate
```

```typescript
// Nuxt: plugins/pinia-persist.ts
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.$pinia.use(piniaPluginPersistedstate)
})
```

```typescript
// stores/settings.ts
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark'>('light')
  const locale = ref('en')

  return { theme, locale }
}, {
  persist: true  // persists entire store to localStorage
})

// Selective persistence
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const tempData = ref('')  // do not persist

  return { token, user, tempData }
}, {
  persist: {
    pick: ['token'],  // only persist token
    storage: persistedState.cookiesWithOptions({
      sameSite: 'strict'
    })
  }
})
```

### Custom Plugin

```typescript
// plugins/pinia-logger.ts
export default defineNuxtPlugin(({ $pinia }) => {
  $pinia.use(({ store }) => {
    store.$subscribe((mutation, state) => {
      console.log(`[${store.$id}] ${mutation.type}`, mutation.events)
    })
  })
})
```

## SSR State Hydration

Pinia handles SSR hydration automatically in Nuxt. State set during server-side rendering transfers to the client via `__NUXT__` payload.

```typescript
// This works seamlessly in Nuxt -- no manual hydration code needed
export const useDataStore = defineStore('data', () => {
  const users = ref<User[]>([])

  async function fetchUsers() {
    users.value = await $fetch('/api/users')
  }

  return { users, fetchUsers }
})
```

Call `fetchUsers()` in a page's `<script setup>` with `await` -- the data fetches on the server and hydrates on the client.

### SSR Caveat: Non-Serializable State

Pinia serializes state for hydration. Non-serializable values (Maps, Sets, classes with methods) cause hydration mismatches.

| Type | SSR-Safe | Workaround |
|------|----------|------------|
| Primitives, arrays, plain objects | Yes | None needed |
| Date | Partial (becomes string) | Reconstruct in hydration plugin |
| Map/Set | No | Use plain objects/arrays |
| Class instances | No | Use plain objects + factory functions |
| Functions in state | No | Keep functions as actions, not state |

## VueUse Integration

VueUse provides 200+ composables. Install via `@vueuse/nuxt` for Nuxt auto-import support.

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@vueuse/nuxt']
})
```

### Most Useful VueUse Composables

| Composable | Purpose | Example |
|-----------|---------|---------|
| `useStorage` | Reactive localStorage/sessionStorage | `const theme = useStorage('theme', 'light')` |
| `useDark` | Dark mode with auto-detection | `const isDark = useDark()` |
| `useDebounce` | Debounced ref | `const debouncedSearch = useDebounce(search, 300)` |
| `useIntersectionObserver` | Lazy load / infinite scroll | Trigger callback when element enters viewport |
| `useBreakpoints` | Responsive breakpoints | `const { isGreater } = useBreakpoints(breakpointsTailwind)` |
| `useClipboard` | Copy to clipboard | `const { copy, copied } = useClipboard()` |
| `useEventListener` | Auto-cleanup event listener | `useEventListener('resize', handler)` |
| `useLocalStorage` | Typed localStorage wrapper | `const count = useLocalStorage('count', 0)` |
| `useMouse` | Reactive mouse position | `const { x, y } = useMouse()` |
| `useMediaQuery` | Reactive media query | `const isLarge = useMediaQuery('(min-width: 1024px)')` |
| `onClickOutside` | Detect outside clicks | `onClickOutside(modalRef, close)` |
| `useColorMode` | Color mode management | `const mode = useColorMode()` |

### VueUse in Pinia Setup Stores

```typescript
export const useSettingsStore = defineStore('settings', () => {
  const theme = useLocalStorage('app-theme', 'light')
  const isDark = useDark()
  const breakpoints = useBreakpoints(breakpointsTailwind)
  const isMobile = breakpoints.smaller('sm')

  return { theme, isDark, isMobile }
})
```

### When to Use VueUse vs Custom Composable

| Scenario | Choice |
|----------|--------|
| Standard browser API wrapper | VueUse (likely exists) |
| Business logic specific to your app | Custom composable |
| Common reactive pattern (debounce, throttle) | VueUse |
| Domain-specific data fetching | Custom composable |
| Intersection/resize/mutation observer | VueUse |
| App-specific form validation | Custom composable |

Check https://vueuse.org/functions before writing a custom composable -- VueUse likely has it.

## State Management Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Store for everything | Over-engineering, unnecessary indirection | Use local `ref()` for component-only state |
| Direct state mutation from components | Bypasses action tracking, harder to debug | Mutate through actions |
| Destructuring without `storeToRefs` | Loses reactivity | `const { x } = storeToRefs(store)` |
| Circular store dependencies | Infinite loops, hard to debug | Extract shared logic to composable |
| Non-serializable state with SSR | Hydration mismatch | Use plain objects and arrays |
| Giant monolithic store | Hard to maintain, unnecessary loading | Split into domain-specific stores |
| Watchers in option stores | Not supported directly | Use setup stores or watch in components |
| Storing derived data | Stale data risk | Use getters/computed instead |

## When to Use Each State Tool

| State Type | Tool | Reason |
|-----------|------|--------|
| Component-local UI state | `ref()` / `reactive()` | No global access needed |
| Shared across sibling components | Pinia store | Clean shared state |
| Deep component tree (ancestor to descendant) | `provide()` / `inject()` | Avoids prop drilling |
| Server-fetched page data | `useFetch` / `useAsyncData` | Built-in SSR, caching, deduplication |
| Persistent user preferences | Pinia + persistence plugin | Survives page reload |
| URL-driven state | `useRoute().query` | Shareable, bookmarkable |
| Form state | `ref()` or VeeValidate | Local to form lifecycle |
