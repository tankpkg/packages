---
name: "nextjs-to-tanstack"
description: |
  Migrate Next.js applications to TanStack Start — escape Vercel lock-in with
  a client-first, type-safe, deploy-anywhere React framework. Covers the full
  migration lifecycle: routing conversion (App Router and Pages Router),
  data fetching (RSC/getServerSideProps to loaders and createServerFn),
  component migration (Link, Image, Head, fonts, navigation hooks),
  auth and middleware patterns, deployment to any platform via Nitro
  (Cloudflare, AWS, Netlify, Bun, Deno, self-hosted), and migration
  strategy (brute-force, strangler fig, AI-assisted). Synthesizes TanStack
  Start official docs, Inngest migration case study (Jan 2026), BeyondIT
  benchmarks, TkDodo patterns, and production community examples.

  Trigger phrases: "next.js to tanstack", "nextjs to tanstack",
  "migrate from nextjs", "migrate from next.js", "tanstack start",
  "tanstack start migration", "escape vercel", "leave nextjs",
  "leave next.js", "nextjs alternative", "replace nextjs",
  "move off nextjs", "ditch nextjs", "nextjs lock-in",
  "vercel lock-in", "nextjs to tanstack start",
  "convert nextjs", "tanstack start conversion",
  "next.js migration", "nextjs migration"
---

# Next.js to TanStack Start Migration

## Core Philosophy

- Explicit over magic — TanStack Start has no `use client`/`use server` directives, no implicit RSC boundaries, no opaque caching layers. Server code is explicitly declared with `createServerFn()` and route `loader` functions.
- Deploy anywhere — Nitro abstracts all platform differences. Same codebase deploys to Vercel, Cloudflare Workers, AWS Lambda, Bun, Deno, or a $20/mo VPS. No vendor lock-in.
- Type safety end-to-end — Route params, loader data, search params, and server function return types are all inferred by TypeScript. Invalid routes are compile errors.
- Client-first, server-capable — All components are standard React. Server capabilities are added explicitly, not assumed by default. The mental model is a React SPA that can optionally fetch data on the server.

## Quick-Start: What Are You Migrating?

| Starting Point | Key Changes | Primary Reference |
|---------------|-------------|-------------------|
| App Router (RSC) | Remove directives, RSC → loaders + createServerFn | `references/data-and-server-functions.md` |
| App Router (routing) | `[slug]` → `$slug`, layout.tsx → __root.tsx | `references/routing-migration.md` |
| Pages Router | getServerSideProps → loader, _app → __root | `references/routing-migration.md` |
| Server Actions | `'use server'` → `createServerFn()` | `references/data-and-server-functions.md` |
| next/link, next/image | `href` → `to`, Image → @unpic/react | `references/component-migration.md` |
| middleware.ts | Edge middleware → beforeLoad + createMiddleware | `references/auth-and-middleware.md` |
| next.config.js | → vite.config.ts + Nitro presets | `references/deployment-and-config.md` |
| Auth (NextAuth, etc.) | Session/Better Auth patterns for TanStack | `references/auth-and-middleware.md` |
| Deployment | Vercel-only → deploy anywhere | `references/deployment-and-config.md` |

## Concept Mapping

| Next.js | TanStack Start | Notes |
|---------|---------------|-------|
| `app/layout.tsx` | `routes/__root.tsx` | `createRootRoute()` + `<Outlet />` |
| `app/page.tsx` | `routes/index.tsx` | `createFileRoute('/')` |
| `app/[slug]/page.tsx` | `routes/$slug.tsx` | Dynamic: `[slug]` → `$slug` |
| `app/[...slug]/page.tsx` | `routes/$.tsx` | Catch-all via `_splat` param |
| `getServerSideProps` | Route `loader` | Explicit server boundary |
| Server Actions (`'use server'`) | `createServerFn()` | Explicit, typed, validated |
| `next/link` (`href`) | `<Link to="...">` | Fully type-safe |
| `next/image` | `@unpic/react` or `<img>` | No built-in optimization server |
| `metadata` export | Route `head()` function | Merges up the route tree |
| `middleware.ts` | `beforeLoad` / `createMiddleware` | Per-route, not edge-global |
| `next.config.js` | `vite.config.ts` | Vite + Nitro plugins |
| `NEXT_PUBLIC_` env vars | `VITE_` env vars | Vite convention |
| `loading.tsx` | `pendingComponent` | Route option |
| `error.tsx` | `errorComponent` | Route option |
| `not-found.tsx` | `notFoundComponent` | Route option |
| `useRouter().push()` | `useNavigate()` | Type-safe navigation |
| `useSearchParams()` | `Route.useSearch()` | Requires `validateSearch` |
| `useParams()` | `Route.useParams()` | Fully typed |

## Migration Approach Decision Tree

| Signal | Approach | Reference |
|--------|----------|-----------|
| < 30 routes, small team | Brute-force (convert all at once) | `references/migration-strategy.md` |
| 30+ routes, mission-critical | Strangler fig (incremental via proxy) | `references/migration-strategy.md` |
| Shared component library | Monorepo migration | `references/migration-strategy.md` |
| Many similar routes | AI-assisted (establish patterns, AI converts) | `references/migration-strategy.md` |

## Common Gotchas

| Gotcha | Impact | Fix |
|--------|--------|-----|
| No RSC — everything is client-capable | RSC patterns break | Use loaders + createServerFn |
| Dev mode ≠ production | Behaviors differ | Always `vite build && vite preview` |
| CSS needs `?url` suffix in root | Broken SSR styles | `import css from './app.css?url'` |
| `routeTree.gen.ts` errors before first run | Expected | Run `vite dev` once to generate |
| ThemeProvider FOUC | Flash of unstyled content | Use `ScriptOnce` for theme script |
| Auth libs need explicit `baseURL` | Auth calls fail | Set `baseURL` in auth client |
| Huge migration PRs | Can't code review | Plan for UAT-based validation |
| No Parallel/Intercepting Routes | Layout patterns break | Conditional rendering or search params |

## Performance Expectations

| Metric | Next.js (before) | TanStack Start (after) | Source |
|--------|-----------------|----------------------|--------|
| Dev server startup | 10-12s | 2-3s | Inngest |
| Client bundle size | baseline | 30-35% smaller | BeyondIT |
| Build time (CI) | baseline | 7x faster | BeyondIT |
| Dev memory usage | 9-10 GB | Standard Node | BeyondIT |

## Features With No Direct Equivalent

| Next.js Feature | TanStack Start Status |
|-----------------|----------------------|
| `next/og` (OG image gen) | Use Satori directly or external service |
| Parallel Routes (`@slot`) | Conditional rendering |
| Intercepting Routes (`(.)`) | Not available |
| ISR (`revalidate: 60`) | Basic ISR exists, not as mature |
| Edge Runtime | Cloudflare Workers via Vite plugin |
| `use cache` directive | TanStack Query for client caching |
| Image optimization server | External CDN (Cloudinary, Imgix) |

## Workflow

1. Assess scope — count routes, identify RSC-heavy pages, check deployment needs.
2. Choose migration approach — brute-force, strangler fig, or monorepo. See `references/migration-strategy.md`.
3. Set up TanStack Start project — vite.config.ts, router.tsx, __root.tsx. See `references/deployment-and-config.md`.
4. Convert routes — file naming, loaders, components. See `references/routing-migration.md`.
5. Migrate data fetching — loaders, server functions, TanStack Query. See `references/data-and-server-functions.md`.
6. Migrate UI components — Link, Image, Head, navigation hooks. See `references/component-migration.md`.
7. Migrate auth — middleware, session, guards. See `references/auth-and-middleware.md`.
8. Configure deployment — Nitro preset, env vars. See `references/deployment-and-config.md`.
9. Learn TanStack patterns — type-safe nav, search params, preloading. See `references/tanstack-start-patterns.md`.
10. Verify — build, preview, UAT, performance comparison.

## Reference Files

| File | Contents |
|------|----------|
| `references/routing-migration.md` | File routing conversion, dynamic params, layouts, __root.tsx, route tree, API routes |
| `references/data-and-server-functions.md` | Loaders, createServerFn, mutations, TanStack Query integration, streaming/deferred |
| `references/component-migration.md` | Link, Image, Head/meta, fonts, navigation hooks, error/loading/notFound, search params |
| `references/deployment-and-config.md` | vite.config.ts, Nitro presets, env vars, platform-specific configs, static export |
| `references/auth-and-middleware.md` | beforeLoad, createMiddleware, session auth, Better Auth, context inheritance, guards |
| `references/migration-strategy.md` | Step-by-step procedures, brute-force vs strangler fig, AI-assisted migration, gotchas, rollback |
| `references/tanstack-start-patterns.md` | Type-safe navigation, search params, preloading, devtools, SSR+Query, router context |
