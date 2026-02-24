---
name: "@tank/nextjs"
description: "Expert Next.js App Router execution guide for server-first rendering, caching, routing, and deployment. Triggers: nextjs, next.js, app router, server component, client component, server action, route handler, middleware, SSR, SSG, ISR, caching, revalidation, streaming, suspense, parallel routes, intercepting routes, next/image, metadata, layout."
triggers:
- nextjs
- next.js
- app router
- server component
- client component
- server action
- route handler
- middleware
- ssr
- ssg
- isr
- caching
- revalidation
- streaming
- suspense
- parallel routes
- intercepting routes
- route groups
- next/image
- metadata
- layout
- route segment config
- use client
- rsc
- loading.tsx
- error.tsx
- not-found.tsx
---

# Core Philosophy
- Server-first rendering: prefer Server Components and server actions, push interactivity to leaves.
- Cache everything by default: assume cached, then opt out with intent and explicit scope.
- Colocation over convention: keep data, UI, and constraints next to the segment that owns them.

# Operating Model
- Start with the route segment: choose static or dynamic behavior before writing code.
- Draw the data flow: read in Server Components, mutate in Server Actions or Route Handlers.
- Place streaming boundaries where partial UI is acceptable.
- Treat middleware as routing, not business logic.

# Server vs Client Component Decision Tree
| Need | Use | Why |
| --- | --- | --- |
| Access to browser APIs, stateful UI, event handlers | Client Component | Runs in browser, can use hooks and effects |
| Fetch data, read cookies/headers, call server actions | Server Component | Runs on server, no bundle cost |
| Render large content tree with minimal JS | Server Component | Streams HTML with zero client JS |
| Interactive widget inside mostly static page | Server Component wrapping Client Component | Keep JS at the leaf |
| Use third-party client-only library | Client Component | Requires window/document |
| Share data across multiple client widgets | Server Component + context boundary | Fetch once on server |
| Need to keep secrets or tokens off the client | Server Component | Never serialize secrets |

# Data Fetching Decision Tree
| Goal | Use | Placement |
| --- | --- | --- |
| Read data for UI, can be cached | RSC async fetch | Server Component |
| Mutate data from a form or button | Server Action | Server Component or Client Component form |
| Expose API for external clients or webhooks | Route Handler | app/api/.../route.ts |
| Client needs incremental updates or polling | Client fetch | Client Component |
| Reuse data across pages | Shared RSC fetch + cache tags | Server Component |
| Need edge runtime | Route Handler or Middleware | app/api or middleware.ts |

# Caching Quick Reference
| Layer | Cached By Default | Revalidate | Opt Out |
| --- | --- | --- | --- |
| Request memoization | Yes (per request) | N/A | `cache: "no-store"` |
| Data Cache | Yes | `next.revalidate`, `revalidateTag` | `cache: "no-store"` |
| Full Route Cache | Yes (static) | `revalidatePath`, segment `revalidate` | `export const dynamic = "force-dynamic"` |
| Router Cache | Yes (client) | `router.refresh()` | `router.refresh()` after mutations |

# Route Conventions
| File | Purpose | Notes |
| --- | --- | --- |
| `page.tsx` | Route entry | Renders UI for a segment |
| `layout.tsx` | Shared UI | Persists across segments |
| `template.tsx` | Per-navigation layout | Remounts on navigation |
| `loading.tsx` | Suspense fallback | Shows while streaming |
| `error.tsx` | Segment error boundary | Client Component with `use client` |
| `not-found.tsx` | 404 UI | Called via `notFound()` |
| `route.ts` | Route Handler | HTTP methods for APIs |
| `middleware.ts` | Edge routing | Runs before route |

# Segment Configuration Defaults
| Option | Default | Use Case |
| --- | --- | --- |
| `dynamic` | `"auto"` | Let Next decide static vs dynamic |
| `revalidate` | `false` | Opt into ISR per segment |
| `fetchCache` | `"auto"` | Control caching for fetch in segment |
| `runtime` | `"nodejs"` | Use edge only when needed |

# Server Action Rules
- Declare `"use server"` at the function or file scope.
- Return serializable values only.
- Validate input on the server, never trust client state.
- Use `revalidatePath` or `revalidateTag` after mutations.
- Prefer form actions for simple submits, `startTransition` for client triggers.

# Middleware Rules
- Keep middleware fast and deterministic.
- Avoid data fetching; redirect or rewrite instead.
- Use matcher config to limit execution scope.
- Put auth gating in middleware, not data enrichment.

# Rendering Defaults
- RSC fetch is cached by default; opt out with `cache: "no-store"`.
- Static rendering is default when no dynamic APIs are used.
- Dynamic rendering triggers on cookies, headers, or `no-store` fetch.
- Streaming is automatic with Suspense boundaries.

# Anti-Patterns
| Anti-Pattern | Replace With |
| --- | --- |
| Marking everything `use client` | Server Components + leaf clients |
| Fetching in Client Components without need | RSC async fetch |
| Mutations via client fetch to app APIs | Server Actions for same-origin UI |
| Using middleware for data fetching | Route Handlers or Server Actions |
| Forcing dynamic on static pages | `revalidate` or tag-based ISR |
| Coupling layouts to data fetching | Move reads to page or nested components |
| Serializing secrets to props | Read secrets in Server Components |
| One global loading state | Segment `loading.tsx` + nested Suspense |
| Overusing route handlers for UI | Prefer RSC for UI data |

# Workflow
1. Pick static or dynamic per segment using `dynamic` and `revalidate`.
2. Fetch in Server Components; memoize with tags and revalidate on writes.
3. Add Server Actions for mutations; invalidate with `revalidatePath` or `revalidateTag`.
4. Insert `loading.tsx` and inline Suspense for gradual streaming.
5. Add `error.tsx` and `not-found.tsx` for resilience.
6. Validate middleware for routing-only responsibilities.
7. Optimize bundles: keep Client Components small and isolated.

# Quality Checklist
- Every client component has a server parent.
- Every mutation has a cache invalidation step.
- Every slow segment has a loading boundary.
- Every external API has a route handler.
- Every metadata dependency is explicit.

# Output Expectations
- Provide concrete code with file paths.
- Explain cache effects explicitly.
- Show where each component runs.
- Keep client JS minimal.

# Reference Files
- `references/server-components.md`
- `references/caching-and-data.md`
- `references/routing-patterns.md`
