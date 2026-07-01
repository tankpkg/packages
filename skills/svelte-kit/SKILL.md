---
name: "@tank/svelte-kit"
description: |
  Expert Svelte 5 and SvelteKit patterns for building production web applications.
  Covers Svelte 5 runes ($state, $derived, $effect, $props, $bindable),
  component patterns (snippets, event handling, lifecycle), SvelteKit routing
  (filesystem-based, layouts, groups, params), load functions (+page.js,
  +page.server.js, universal vs server), form actions (progressive enhancement,
  validation, multiple actions), hooks (handle, handleFetch, handleError),
  server-only modules (+server.ts, $env), SSR/SSG/SPA rendering modes,
  error handling (expected vs unexpected, error boundaries), state management
  (runes vs stores, shared state, context), testing (Vitest unit, Playwright
  E2E, component testing), deployment adapters (Vercel, Cloudflare, Node,
  static), and migration from Svelte 4 to Svelte 5. Synthesizes official
  Svelte 5 documentation (svelte.dev 2024-2026), SvelteKit documentation,
  Rich Harris talks, and community production patterns.

  Trigger phrases: "svelte", "sveltekit", "svelte 5", "svelte runes",
  "$state", "$derived", "$effect", "$props", "svelte component",
  "sveltekit routing", "sveltekit load function", "sveltekit form actions",
  "svelte store", "svelte tutorial", "sveltekit deployment",
  "sveltekit adapter", "svelte hooks", "svelte server",
  "svelte migration", "svelte testing", "sveltekit SSR",
  "svelte state management", "svelte snippet", "+page.server",
  "sveltekit error handling", "svelte 4 to 5", "svelte typescript"
---

# SvelteKit

## Core Philosophy

1. **Runes replace stores for component state** -- Svelte 5 runes ($state, $derived, $effect) provide fine-grained reactivity without the subscription boilerplate of stores. Use runes as the default; reach for stores only for cross-component shared state or legacy compatibility.
2. **Server-first by default** -- SvelteKit renders on the server first (SSR), then hydrates. Place data fetching in load functions, secrets in +page.server.ts, and leverage form actions for mutations -- progressive enhancement comes free.
3. **Filesystem is the API** -- Routes, layouts, error boundaries, and API endpoints are defined by directory structure and file naming conventions (+page, +layout, +server, +error). Master the naming and nesting rules.
4. **Lean on the platform** -- SvelteKit uses native web APIs (fetch, Request, Response, FormData, URL). Adapters map this to any deployment target. Write platform-standard code.
5. **Type safety without ceremony** -- SvelteKit generates $types automatically. Use PageProps, LayoutProps, PageServerLoad -- the framework infers types from your file structure.

## Quick-Start: Common Problems

### "How do I manage reactive state in Svelte 5?"

1. Use `let count = $state(0)` for mutable state in components
2. Use `let doubled = $derived(count * 2)` for computed values
3. Use `$effect(() => { ... })` for side effects when reactive values change
4. Use `let { data, children } = $props()` to receive component props
5. For deep objects, use `$state({ nested: { value: 1 } })` -- Svelte proxies deeply
-> See `references/svelte5-runes.md`

### "Where should I put my data fetching logic?"

| Data Source | File | Runs On |
|-------------|------|---------|
| Public API, no secrets | +page.js | Server + Client |
| Database, API keys, secrets | +page.server.js | Server only |
| Shared across child routes | +layout.js / +layout.server.js | Server (+ Client for .js) |
| REST/JSON endpoint | +server.js | Server only |

-> See `references/routing-and-load.md`

### "How do I handle form submissions?"

1. Export `actions` from `+page.server.js` with `default` or named actions
2. Use `<form method="POST">` -- works without JavaScript
3. Call `use:enhance` from `$app/forms` for progressive enhancement
4. Return validation errors via `fail(400, { errors })` from the action
-> See `references/form-actions-and-hooks.md`

### "How do I deploy my SvelteKit app?"

1. Pick adapter matching your target (adapter-auto detects Vercel/Cloudflare/Netlify)
2. Install adapter, configure in `svelte.config.js`
3. Set page options (prerender, ssr, csr) per route as needed
4. Build with `vite build`, deploy with platform CLI
-> See `references/deployment-and-migration.md`

### "I need to migrate from Svelte 4 to Svelte 5"

1. Run `npx sv migrate svelte-5` for automated codemod
2. Replace `export let` with `$props()`, reactive `$:` with `$derived`/`$effect`
3. Replace `<slot>` with `{@render children()}` snippets
4. Replace `createEventDispatcher` with callback props
-> See `references/deployment-and-migration.md`

## Decision Trees

### State Management Approach

| Signal | Use |
|--------|-----|
| Component-local reactive value | `$state()` rune |
| Computed from other state | `$derived()` rune |
| Side effect on state change | `$effect()` rune |
| Shared across unrelated components | Runes in .svelte.js module or store |
| Global app state (auth, theme) | Context API + runes or writable store |
| Server-loaded data | Load function, access via `$props().data` |

### Rendering Mode

| Signal | Mode |
|--------|------|
| Content changes per request, needs SEO | SSR (default) |
| Content same for all users, rebuild on deploy | SSG (`prerender = true`) |
| Dashboard, no SEO needed | SPA (`ssr = false`) |
| Marketing pages with dynamic sections | SSR + selective prerender |

### Load Function Placement

| Signal | File |
|--------|------|
| Needs secrets, DB, private env vars | `+page.server.js` |
| Runs on client navigation too, no secrets | `+page.js` |
| Data shared across child pages | `+layout(.server).js` |
| Standalone API (JSON, webhooks) | `+server.js` |

## Reference Index

| File | Contents |
|------|----------|
| `references/svelte5-runes.md` | $state, $derived, $effect, $props, $bindable, snippets, event handling, bindings, component composition, and stores-vs-runes guidance |
| `references/routing-and-load.md` | Filesystem routing, params, layout groups, universal vs server load, invalidation, streaming, and server-only modules |
| `references/form-actions-and-hooks.md` | Default and named form actions, progressive enhancement, validation, file uploads, hooks (`handle`, `handleFetch`, `handleError`), and `+server` endpoints |
| `references/testing-and-state.md` | Vitest, Playwright E2E, component testing, mocking load data, context API, shared state, and route-aware state patterns |
| `references/deployment-and-migration.md` | Adapter selection, Vercel/Cloudflare/Node/static deployment, page options, SSR/SSG/SPA trade-offs, and Svelte 4→5 migration patterns |
