---
name: "@tank/nextjs-caching-guide"
description: |
  Deep guide to Next.js App Router caching — the four cache layers (Request
  Memoization, Data Cache, Full Route Cache, Router Cache), revalidation
  strategies (time-based, on-demand via revalidatePath/revalidateTag),
  static vs dynamic rendering decisions, ISR patterns, the use cache
  directive (Next.js 16 Cache Components replacing unstable_cache),
  cacheLife/cacheTag APIs, fetch cache options, Next.js 15 caching
  behavior changes (no-store default), CDN/edge caching for self-hosting,
  cache debugging techniques, and common pitfalls that cause stale data.

  Synthesizes Next.js official documentation (v14-16), Vercel engineering
  blog, Next.js GitHub discussions, and production caching patterns.

  Trigger phrases: "next.js caching", "next.js cache", "revalidatePath",
  "revalidateTag", "next.js ISR", "next.js stale data", "use cache",
  "next.js data cache", "next.js router cache", "next.js full route cache",
  "unstable_cache", "next.js cache busting", "next.js revalidation",
  "next.js caching explained", "cache not updating", "force-dynamic",
  "next.js static vs dynamic", "cacheLife", "cacheTag", "stale page",
  "next.js 15 caching changes", "ISR on-demand", "fetch cache options"
---

# Next.js Caching Guide

## Core Philosophy

1. **Understand the stack, not just the API** — Next.js has four distinct cache layers that interact. Fixing stale data requires knowing which layer is stale, not blindly adding force-dynamic everywhere.
2. **Static by default, dynamic by intent** — Start with static rendering and opt into dynamic behavior only for request-specific data. Every dynamic opt-in has a performance cost.
3. **Invalidation is the hard problem** — Caching data is easy. Knowing when to invalidate is where bugs live. Prefer tag-based invalidation over path-based — tags follow data, paths follow UI.
4. **Version-aware decisions matter** — Next.js 14, 15, and 16 each changed caching defaults significantly. Know which version runs in production before debugging.
5. **Cache debugging is a first-class skill** — Use response headers, verbose logging, and the static route indicator to verify cache behavior rather than guessing.

## Quick-Start: Common Problems

### "I updated data but the page still shows old content"

1. Identify which cache layer is stale — check the decision tree below
2. After mutations in Server Actions, call `revalidateTag('tag')` or `revalidatePath('/path')`
3. On the client after a Server Action, call `router.refresh()` to clear Router Cache
4. Verify with `NEXT_PRIVATE_DEBUG_CACHE=1` that revalidation fires
-> See `references/four-cache-layers.md` and `references/revalidation-strategies.md`

### "Everything is dynamic and slow"

1. Check if `force-dynamic` or `cache: 'no-store'` is set at a layout level — it cascades to all children
2. Move dynamic data reads to leaf components, keep parent routes static
3. Use `revalidate` with a time interval instead of disabling caching entirely
4. For user-specific data alongside cached content, use Partial Prerendering or composition patterns
-> See `references/static-dynamic-rendering.md`

### "Which caching model — fetch options or use cache?"

| Next.js Version | Model | Key API |
|-----------------|-------|---------|
| 14.x | fetch cache defaults to cached | `fetch({ next: { revalidate, tags } })` |
| 15.x | fetch cache defaults to uncached | `fetch({ cache: 'force-cache' })`, `unstable_cache` |
| 16.x+ | Cache Components | `'use cache'` directive, `cacheLife`, `cacheTag` |

-> See `references/use-cache-directive.md` and `references/fetch-cache-options.md`

### "How do I cache database queries (not fetch)?"

1. **Next.js 16+**: Add `'use cache'` to the async function wrapping the query
2. **Next.js 15**: Wrap with `unstable_cache(fn, keys, { tags, revalidate })`
3. **Deduplication only**: Wrap with `React.cache(fn)` for same-render dedup without persistence
-> See `references/use-cache-directive.md`

## Decision Trees

### "My page is stale" — Which Cache Layer?

| Symptom | Likely Layer | Fix |
|---------|-------------|-----|
| Stale after deploy | Full Route Cache (build-time HTML) | `revalidatePath` or redeploy |
| Stale after mutation (server) | Data Cache | `revalidateTag` in Server Action |
| Stale on client navigation | Router Cache | `router.refresh()` after mutation |
| Duplicate fetches in same render | Request Memoization | Working as intended (dedup) |
| Stale on hard refresh but fresh on soft nav | CDN/edge cache | Check Cache-Control headers |

### revalidatePath vs revalidateTag

| Signal | Use |
|--------|-----|
| Data is shared across routes (products, posts) | `revalidateTag` — follows the data |
| Single specific page needs refreshing | `revalidatePath` — targets one route |
| CMS publishes content used in many pages | `revalidateTag` — one call, all routes |
| User profile page after profile edit | `revalidatePath('/profile')` |
| Unclear which routes use this data | `revalidateTag` — decoupled from routing |

### Static vs Dynamic Rendering

| Signal | Rendering | Config |
|--------|-----------|--------|
| Content same for all users | Static | Default (no config needed) |
| Reads cookies, headers, searchParams | Dynamic | Automatic (detected) |
| Personalized but cacheable per-user | Dynamic + short revalidate | `revalidate: 60` |
| Real-time data, never cache | Dynamic | `cache: 'no-store'` or `force-dynamic` |
| Mostly static with one dynamic section | Partial Prerendering | Suspense boundary around dynamic part |

## Reference Index

| File | Contents |
|------|----------|
| `references/four-cache-layers.md` | Request Memoization, Data Cache, Full Route Cache, Router Cache — how each works, duration, interaction |
| `references/revalidation-strategies.md` | Time-based revalidation, on-demand with revalidateTag/revalidatePath, ISR patterns, webhook-triggered invalidation |
| `references/use-cache-directive.md` | Cache Components (Next.js 16+), use cache syntax, cacheLife profiles, cacheTag, updateTag, serialization, interleaving patterns |
| `references/fetch-cache-options.md` | fetch() cache option, next.revalidate, next.tags, unstable_cache, route segment config (dynamic, fetchCache, revalidate) |
| `references/static-dynamic-rendering.md` | Static vs dynamic rendering triggers, Partial Prerendering, generateStaticParams, streaming + caching interaction |
| `references/cache-debugging.md` | NEXT_PRIVATE_DEBUG_CACHE, response headers, static route indicator, build output analysis, production verification |
| `references/version-migration.md` | Next.js 14 vs 15 vs 16 caching defaults, migration paths, staleTimes config, breaking changes |
| `references/self-hosting-cdn.md` | Cache-Control headers, CDN integration, expireTime config, custom cache handlers, edge caching patterns |
