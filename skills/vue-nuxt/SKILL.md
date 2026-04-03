---
name: "@tank/vue-nuxt"
description: |
  Vue 3 Composition API and Nuxt 3 patterns for production applications.
  Covers `<script setup>` and composable design, reactive primitives
  (ref, reactive, computed, watch), TypeScript integration (defineProps,
  defineEmits, defineModel, typed composables, InjectionKey), Pinia state
  management (setup stores, store composition, persistence), Nuxt 3 data
  fetching (useFetch, useAsyncData, $fetch, server routes), middleware and
  plugins, rendering modes (SSR, SSG, ISR, hybrid routeRules), SEO
  (useHead, useSeoMeta), Nitro deployment presets, VueUse integration,
  and testing (Vitest, @vue/test-utils, @nuxt/test-utils).

  Synthesizes Vue 3 official documentation, Nuxt 3 official documentation,
  Pinia documentation, VueUse documentation, and community production patterns.

  Trigger phrases: "vue 3", "vue component", "vue composition api",
  "script setup", "nuxt 3", "nuxt app", "composable", "vue composable",
  "pinia", "pinia store", "vue typescript", "nuxt server route",
  "useFetch", "useAsyncData", "nuxt middleware", "nuxt plugin",
  "vue testing", "vitest vue", "nuxt deployment", "nuxt SSR",
  "nuxt SSG", "vue ref", "vue reactive", "defineProps", "defineEmits",
  "defineModel", "vue provide inject", "nuxt config", "VueUse",
  "nuxt rendering", "vue best practices", "nuxt best practices"
---

# Vue & Nuxt

## Core Philosophy

1. **Composition over options** -- `<script setup>` with Composition API is the standard for Vue 3. Prefer composables for reusable logic extraction over mixins, renderless components, or Options API.
2. **Server-first in Nuxt** -- Nuxt renders on the server by default. Use `useFetch`/`useAsyncData` for data that needs SSR hydration. Reserve `$fetch` for client-only actions (form submissions, mutations).
3. **Type everything** -- Use type-based `defineProps<T>()` and `defineEmits<T>()`. Type composable return values explicitly. Use `InjectionKey<T>` for provide/inject.
4. **Auto-import with intention** -- Nuxt auto-imports composables, utils, and Vue APIs. Rely on it for framework APIs but use explicit imports for third-party code to keep dependency graphs visible.
5. **Reactivity is the API** -- `ref()` for primitives, `reactive()` for objects you never reassign, `computed()` for derived state, `watch()` for side effects. Match the primitive to the use case.

## Quick-Start: Common Problems

### "How do I structure a Vue 3 component?"

1. Use `<script setup lang="ts">` -- no `export default`, no `setup()` return
2. Define props with `defineProps<{ title: string }>()` (type-based)
3. Define emits with `defineEmits<{ (e: 'update', value: string): void }>()`
4. Extract reusable logic into `composables/use*.ts` files
-> See `references/composition-api.md`

### "useFetch vs useAsyncData vs $fetch?"

| Situation | Use |
|-----------|-----|
| Page/component data with SSR | `useFetch('/api/data')` |
| Complex fetch logic with SSR | `useAsyncData('key', () => $fetch(...))` |
| Client-only mutations | `$fetch('/api/submit', { method: 'POST' })` |
| Non-component context | `$fetch()` directly |

-> See `references/data-fetching.md`

### "Setup store or option store in Pinia?"

1. Default to setup stores -- they compose with other composables naturally
2. Use option stores only for simple CRUD state or when migrating from Vuex
3. Never access stores outside `<script setup>` or composables without `useNuxtApp()`
-> See `references/state-management.md`

### "Which rendering mode for each route?"

Use `routeRules` in `nuxt.config.ts` for per-route rendering:

| Route Pattern | Rule | Effect |
|--------------|------|--------|
| `/` | `prerender: true` | Static at build time |
| `/blog/**` | `isr: 3600` | Regenerate every hour |
| `/products/**` | `swr: true` | Stale-while-revalidate |
| `/admin/**` | `ssr: false` | Client-side only |
| `/api/**` | `cors: true` | CORS headers |

-> See `references/rendering-deployment.md`

### "How do I test Vue/Nuxt components?"

1. Use Vitest + `@vue/test-utils` for unit/component tests
2. Use `@nuxt/test-utils` for Nuxt-aware integration tests
3. Test composables by calling them inside a wrapper component or `withSetup`
-> See `references/testing.md`

## Decision Trees

### Reactive Primitive Selection

| Data Shape | Primitive | Reason |
|-----------|-----------|--------|
| String, number, boolean | `ref()` | Simple `.value` access, template auto-unwraps |
| Object you never reassign | `reactive()` | No `.value`, direct property access |
| Derived from other state | `computed()` | Cached, auto-tracks dependencies |
| Side effect on change | `watch()` | Explicit source, access old/new values |
| Side effect, auto-track deps | `watchEffect()` | No explicit source, runs immediately |

### Component Communication

| Scenario | Pattern |
|----------|---------|
| Parent to child data | Props (`defineProps`) |
| Child to parent events | Emits (`defineEmits`) |
| Two-way binding | `defineModel()` (Vue 3.4+) |
| Deep ancestor to descendant | `provide()` / `inject()` with `InjectionKey` |
| Cross-component shared state | Pinia store |
| Cross-composable coordination | Composable importing composable |

## Reference Index

| File | Contents |
|------|----------|
| `references/composition-api.md` | `<script setup>`, ref/reactive/computed/watch, lifecycle hooks, composable design patterns, Vue 3.4+ and 3.5+ features |
| `references/typescript-patterns.md` | Type-based defineProps/Emits/Model, typed composables, InjectionKey, template ref typing, vue-tsc, generic components |
| `references/nuxt-fundamentals.md` | Directory structure, auto-imports, plugins, layouts, middleware, runtime config, nuxt.config.ts, error handling |
| `references/data-fetching.md` | useFetch, useAsyncData, $fetch, server routes, API patterns, caching, error handling, serialization |
| `references/state-management.md` | Pinia setup/option stores, store composition, persistence plugins, VueUse composables, SSR state hydration |
| `references/rendering-deployment.md` | SSR/SSG/ISR/SWR, routeRules, Nitro presets, edge rendering, SEO (useHead, useSeoMeta), performance optimization |
| `references/testing.md` | Vitest setup, @vue/test-utils patterns, @nuxt/test-utils, testing composables, testing Pinia stores, MSW mocking |
