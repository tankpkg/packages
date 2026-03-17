# Migration Strategy and Procedures

Sources: Inngest engineering blog (Jan 2026), BeyondIT benchmark (Mar 2026), Catalin Pit migration PR, TanStack Start official migration guide

## 1. When to Migrate vs Stay on Next.js

Migration is a significant investment. Evaluate honestly before committing.

### Migrate when these signals are present

**Developer experience is degrading:**
- Local dev server takes 8 seconds or more to start — this compounds across a team and kills flow state
- You are debugging cache directives (`revalidate`, `cache: 'no-store'`, `unstable_cache`) on a weekly basis
- The RSC mental model requires constant context-switching for engineers who are not full-time frontend

**Operational concerns are real:**
- Containerized deployment with OOM issues — Next.js 16 has documented memory leaks in Kubernetes that require pod restarts and memory limits above 9GB per instance
- Infrastructure cost is a concern — a Vite-based stack runs comfortably on a $20/month VPS; equivalent Vercel usage for a mid-size app can exceed $500/month
- Vendor lock-in is a strategic risk — you want the freedom to deploy to Cloudflare Workers, AWS Lambda, Fly.io, or a bare VPS without rewriting infrastructure

**Architecture is a better fit:**
- You want explicit, predictable server/client boundaries rather than implicit RSC boundaries
- Your team is small and everyone touches the frontend occasionally — TanStack Start's mental model is closer to standard React
- You are building a highly interactive application where client-side routing performance matters

### Stay on Next.js when these conditions apply

**Features with no equivalent:**
- ISR (Incremental Static Regeneration) is mission-critical and heavily used — TanStack Start has no direct equivalent
- Edge Runtime is required for geo-routing or A/B testing at the CDN level
- Parallel Routes or Intercepting Routes are load-bearing in your current architecture
- `next/og` is used for dynamic OpenGraph image generation at scale

**Organizational factors:**
- You require Vercel SLA or enterprise support contracts
- Your team is full-time frontend and has internalized the RSC mental model — the migration cost outweighs the benefit
- You depend on a mature plugin ecosystem (next-auth v4, next-intl, next-sitemap) and the migration cost of those integrations is high

**Decision matrix:**

| Signal | Weight | Migrate | Stay |
|--------|--------|---------|------|
| Dev server > 8s | High | Yes | — |
| OOM in k8s | High | Yes | — |
| ISR heavily used | High | — | Yes |
| Edge Runtime required | High | — | Yes |
| Vercel enterprise contract | Medium | — | Yes |
| Small team, mixed frontend | Medium | Yes | — |
| Parallel/Intercepting Routes | Medium | — | Yes |
| Infrastructure cost concern | Medium | Yes | — |
| Full-time frontend team | Low | — | Yes |

---

## 2. Migration Approaches

Three approaches cover the range of app sizes and risk tolerances. Choose based on route count, team size, and tolerance for a period of dual-stack complexity.

### Approach A: Brute-Force (Recommended for apps with fewer than 30 routes)

Convert everything at once in a single branch. Inngest used this approach — one engineer with AI assistance completed their larger dashboard app in approximately two weeks.

**When to use:**
- Fewer than 30 routes
- No mission-critical pages that cannot tolerate a regression window
- Team can absorb a large PR that is validated by UAT rather than line-by-line code review

**Steps:**
1. Create a new TanStack Start project alongside the existing Next.js app
2. Establish patterns on 2-3 representative routes before converting the rest
3. Use AI assistance to convert remaining routes following the established patterns
4. Build and compile frequently — do not accumulate unbuildable code
5. Validate with UAT rather than traditional code review (PRs will exceed 4,000 lines)
6. Switch DNS or deployment target when validation passes

**Tradeoffs:**

| Aspect | Assessment |
|--------|------------|
| Complexity | Low — one codebase, one mental model |
| Risk window | High — all-or-nothing cutover |
| PR reviewability | Low — validate by running, not reading |
| Time to complete | Fast — 1-3 weeks for small apps |
| Rollback | DNS switch or keep old deployment live |

### Approach B: Strangler Fig (Recommended for apps with 30+ routes)

Deploy TanStack Start on a separate origin and use a reverse proxy to route traffic incrementally. BeyondIT used this approach — Nginx in front of both origins, migrating high-friction surfaces first.

**When to use:**
- 30 or more routes
- Mission-critical pages that require zero regression risk
- Team can manage two deployment pipelines temporarily

**Steps:**
1. Deploy TanStack Start app on a separate origin or port
2. Place a reverse proxy (Nginx, Cloudflare, Caddy) in front of both origins
3. Route specific paths to TanStack Start; route everything else to Next.js
4. Migrate routes one section at a time, starting with the highest-friction pages (slowest dev experience, most cache debugging)
5. Gradually shift more path prefixes to TanStack Start
6. When all routes are migrated, remove the proxy and decommission Next.js

**Tradeoffs:**

| Aspect | Assessment |
|--------|------------|
| Complexity | High — proxy config, two pipelines, shared auth |
| Risk window | Low — each migration is independently reversible |
| PR reviewability | High — small, focused PRs |
| Time to complete | Slow — weeks to months depending on app size |
| Rollback | Per-route, instant via proxy config |

**Proxy configuration pattern (Nginx):**

```nginx
location /dashboard {
    proxy_pass http://tanstack-origin;
}
location / {
    proxy_pass http://nextjs-origin;
}
```

Shared authentication requires a common session store (Redis, database-backed sessions) accessible from both origins. Cookie domain must cover both origins or use a shared parent domain.

### Approach C: Monorepo Component Sharing

Extract shared UI components into a package, then run both apps in a monorepo. Migrate routes by moving them to the TanStack Start app while sharing the component library.

**When to use:**
- Large design system or component library that both apps will use
- Team already operates a monorepo
- Long migration timeline where component parity matters

**Tradeoffs:**

| Aspect | Assessment |
|--------|------------|
| Complexity | Very high — monorepo tooling, package boundaries |
| Component reuse | Excellent — single source of truth |
| Time to complete | Slowest approach |
| Recommended for | Teams with existing monorepo infrastructure |

---

## 3. Step-by-Step Migration Procedure (Brute-Force)

This procedure covers the brute-force approach in detail. Adapt phases for the strangler fig approach by applying Phase 2 and Phase 3 per route batch.

### Phase 1: Project Setup

1. Create the project directory and initialize TanStack Start:
   ```
   npx @tanstack/cli create
   ```
   Or scaffold manually if you need precise control over the initial structure.

2. Install core dependencies:
   ```
   @tanstack/react-start
   @tanstack/react-router
   react@19
   react-dom@19
   vinxi
   ```

3. Copy shared packages from the Next.js app: UI component library, utility functions, TypeScript types, constants, and any framework-agnostic business logic.

4. Configure `vite.config.ts`:
   - Add Tailwind CSS plugin if used
   - Configure `resolve.alias` to match `tsconfig.json` path aliases
   - Add any Vite plugins that replace Next.js webpack plugins

5. Create `src/router.tsx` with the router factory. This is the entry point for all routing configuration.

6. Create `src/routes/__root.tsx` with the HTML shell, global providers, and root layout. This replaces `app/layout.tsx`.

7. Run `vite dev` once to generate `routeTree.gen.ts`. TypeScript errors before this file exists are expected and not actionable.

### Phase 2: Route Conversion

Apply this procedure to each Next.js page or route segment. Work through routes in dependency order — shared layouts before leaf routes.

1. Create the corresponding TanStack route file. See `routing-migration.md` for the filename mapping from Next.js conventions to TanStack file-based routing.

2. Convert data fetching:
   - `getServerSideProps` → `loader` function on the route + `createServerFn` for server-side logic
   - React Server Components with `async` data → `loader` + `createServerFn`
   - `getStaticProps` → `loader` (TanStack Start does not have a static generation equivalent; use a CDN or caching layer)

3. Replace navigation imports:
   - `next/link` → `Link` from `@tanstack/react-router` (`href` prop → `to` prop)
   - `next/image` → `@unpic/react` `Image` component or a plain `<img>` with explicit dimensions
   - `useRouter()` → `useNavigate()` for programmatic navigation, `Route.useParams()` for route parameters, `Route.useSearch()` for query parameters

4. Replace metadata:
   - `export const metadata` → `head()` function on the route object
   - Dynamic metadata from `generateMetadata` → `head()` with access to loader data via `ctx.loaderData`

5. Replace loading and error UI:
   - `loading.tsx` → `pendingComponent` on the route
   - `error.tsx` → `errorComponent` on the route

6. Convert server actions:
   - `'use server'` functions → `createServerFn` with explicit HTTP method
   - Form actions → `createServerFn` called from a client-side submit handler

7. Build after every 3-5 routes: `vite build`. Do not accumulate unbuildable code — server-side bundling errors are difficult to isolate in large changesets.

8. Test the converted route in the browser before moving to the next.

### Phase 3: Infrastructure

1. Convert `next.config.js` features to `vite.config.ts`. See `deployment-and-config.md` for the mapping of redirects, rewrites, headers, and image optimization configuration.

2. Migrate environment variables: rename all `NEXT_PUBLIC_` prefixes to `VITE_`. Update all references in source code. Server-only variables (no prefix) remain unchanged.

3. Convert `middleware.ts` logic:
   - Authentication guards → `beforeLoad` on protected routes or route groups
   - Request/response manipulation → `createMiddleware` from `@tanstack/react-start`

4. Configure the Nitro deployment preset in `app.config.ts` to match your target platform (Node.js, Cloudflare Workers, AWS Lambda, etc.).

5. Update CI/CD pipeline: replace `next build` with `vite build`, update artifact paths, update health check endpoints.

### Phase 4: Verification

Run this checklist before switching traffic:

1. `vite build && tsc --noEmit` — must pass with zero errors
2. `vite preview` — smoke test all routes locally against the production build
3. UAT all routes manually — do not rely on automated tests alone for a migration of this scope
4. Compare page load times against the Next.js baseline using browser DevTools or WebPageTest
5. Verify SEO: inspect `<head>` output for meta tags, Open Graph tags, and canonical URLs on representative pages
6. Test all auth flows end-to-end: login, signup, logout, session expiry, protected route redirect
7. Test all forms and mutations
8. Run a load test if the application has known traffic spikes

---

## 4. AI-Assisted Migration Pattern

Inngest's documented approach: establish patterns manually on a small number of representative routes, then use AI for the repetitive conversion work.

**Setup (manual, ~1 day):**

1. Manually convert three representative routes:
   - A simple static page with no data fetching
   - A page with server-side data fetching (loader + createServerFn)
   - A page with a form and a mutation (createServerFn with POST)

2. Document the patterns in a short internal migration guide. Include the before (Next.js) and after (TanStack Start) for each pattern.

**Execution (AI-assisted):**

3. For each remaining route, provide the AI with:
   - The internal migration guide
   - The Next.js source file
   - The target TanStack Start file structure
   - Any relevant shared utilities

4. Review each AI conversion for correctness. The AI will handle mechanical transformations reliably; review for logic errors and edge cases.

5. Build and compile after every batch of conversions. Inngest's key lesson: "Build and compile early and often." Server-side bundling issues are hard to isolate from large changesets.

**What AI handles well:**
- Renaming imports and props (`href` → `to`, `useRouter` → `useNavigate`)
- Restructuring data fetching from RSC patterns to loader patterns
- Converting metadata exports to `head()` functions
- Renaming route files to TanStack conventions

**What requires human review:**
- Complex authentication logic
- Error handling and edge cases
- Performance-sensitive data fetching patterns
- Any route with non-standard Next.js patterns

---

## 5. Critical Gotchas

### Build and Runtime

| Gotcha | Impact | Fix |
|--------|--------|-----|
| Dev mode behavior differs from production | Silent failures in production | Always run `vite build && vite preview` before deploying |
| Server-side bundling errors are hard to isolate | Debugging takes hours in large PRs | Build after every 3-5 route conversions |
| `routeTree.gen.ts` does not exist before first dev run | TypeScript errors on fresh clone | Run `vite dev` once; commit the generated file |
| Vite SSR module cache causes `instanceof` failures | Error type checks fail silently | Use `error.name === 'MyError'` instead of `error instanceof MyError` |
| `NEXT_PUBLIC_` variables are undefined | Runtime errors in client code | Rename all prefixes to `VITE_` and update all references |

### Code Patterns

| Gotcha | Impact | Fix |
|--------|--------|-----|
| CSS files imported without `?url` suffix break SSR | Styles missing in server-rendered HTML | Use `import css from './styles.css?url'` for SSR-compatible CSS imports |
| Theme providers cause flash of unstyled content | Poor user experience on first load | Use `ScriptOnce` from `@tanstack/react-router` to inject theme script before hydration |
| Auth libraries require explicit `baseURL` | Auth API calls fail in SSR context | Set `baseURL` explicitly in auth client configuration |
| `href` prop on `Link` is not caught at runtime | Navigation silently does nothing | TypeScript will catch this; run `tsc --noEmit` early |
| `[slug]` filename convention does not work | Routes return 404 | Rename all dynamic segments from `[param]` to `$param` |
| `searchParams` accessed without `validateSearch` | Search params are `undefined` | Declare `validateSearch` with a Zod schema or validator function on the route |
| `useRouter().push()` has no equivalent | Navigation calls throw at runtime | Replace with `useNavigate()` from `@tanstack/react-router` |
| `useSearchParams()` has no direct equivalent | Search param reads return `undefined` | Use `Route.useSearch()` after declaring `validateSearch` |

### Architecture

| Gotcha | Impact | Fix |
|--------|--------|-----|
| No React Server Components | RSC-dependent patterns break | Rethink data flow: use `loader` for server data, `createServerFn` for server logic |
| No `use client` / `use server` directives | Directive-heavy code requires rewrite | Remove all directives; use explicit file-based boundaries instead |
| No Parallel Routes | Parallel layout patterns break | Use conditional rendering or separate route trees |
| No Intercepting Routes | Modal-as-route patterns break | Implement modal state via TanStack Router search params |
| Large migration PRs cannot be code-reviewed line by line | Regressions slip through | Plan for UAT-based validation; do not block on traditional code review |
| Shared auth between Next.js and TanStack Start (strangler fig) | Session state is inconsistent | Use a shared session store (Redis or database) with a common cookie domain |

---

## 6. Performance Expectations

Real-world benchmarks from documented migration case studies. Individual results vary based on app complexity, caching strategy, and deployment target.

| Metric | Before (Next.js) | After (TanStack Start) | Source |
|--------|-----------------|----------------------|--------|
| Local dev server startup | 10-12 seconds | 2-3 seconds | Inngest (Jan 2026) |
| First meaningful paint | Baseline | 20-30% faster | BeyondIT (Mar 2026) |
| Client bundle size | Baseline | 30-35% smaller | BeyondIT (Mar 2026) |
| CI build time | Baseline | 7x faster | BeyondIT (Mar 2026) |
| Peak dev process memory | 9-10 GB | Standard Node.js | BeyondIT (Mar 2026) |

The dev server improvement is the most consistent finding across case studies. The production performance improvements depend heavily on how much of the Next.js bundle size was attributable to RSC infrastructure and the Next.js runtime.

---

## 7. Rollback Strategy

Plan for rollback before starting. The cost of a rollback is low if you prepare; it is high if you do not.

**Brute-force approach:**
- Keep the Next.js app deployed and accessible on a separate origin or subdomain throughout the migration
- Use DNS switching or a load balancer weight to cut over traffic
- Inngest documented exactly one significant rollback during their migration — an integration flow that behaved differently outside of their test environment
- Test integration flows (payment providers, OAuth callbacks, webhooks) against the production TanStack Start deployment before switching traffic

**Strangler fig approach:**
- Rollback is per-route: update the proxy configuration to route a path back to Next.js
- Maintain the Next.js deployment pipeline until the migration is complete and stable
- Document which paths are on which origin in a shared location

**General principles:**
- Do not decommission the Next.js deployment until the TanStack Start app has been stable in production for at least two weeks
- Keep environment variables synchronized between both deployments during the transition period
- Monitor error rates and performance metrics for 48 hours after each traffic shift

---

## 8. Post-Migration Checklist

Use this checklist before decommissioning the Next.js deployment.

**Routing and rendering:**
- [ ] All routes are accessible and return correct HTTP status codes
- [ ] Dynamic routes resolve correctly with all parameter combinations
- [ ] 404 handling works for unknown routes
- [ ] Redirects are in place for any changed URL structure

**Data and state:**
- [ ] Data fetching works in all routes (loaders, server functions)
- [ ] Forms and mutations complete successfully
- [ ] Optimistic updates behave correctly if used
- [ ] Error boundaries are in place for all data-fetching routes

**Authentication:**
- [ ] Login flow completes and sets session correctly
- [ ] Signup flow completes
- [ ] Logout clears session and redirects correctly
- [ ] Protected routes redirect unauthenticated users
- [ ] Session expiry is handled gracefully

**SEO and metadata:**
- [ ] `<title>` tags render correctly on all pages
- [ ] Meta description tags are present
- [ ] Open Graph tags render correctly
- [ ] Canonical URLs are correct
- [ ] Sitemaps are generating if applicable
- [ ] Robots.txt is accessible

**Infrastructure:**
- [ ] Environment variables migrated (`NEXT_PUBLIC_` → `VITE_`)
- [ ] Deployment pipeline configured and passing
- [ ] Health check endpoint accessible
- [ ] Error monitoring (Sentry, etc.) receiving events from new deployment
- [ ] Performance monitoring baseline established

**Performance:**
- [ ] Page load times meet or exceed Next.js baseline
- [ ] Core Web Vitals are within acceptable range
- [ ] No memory leaks under sustained load
