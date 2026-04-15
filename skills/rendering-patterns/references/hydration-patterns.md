# Hydration Patterns

Sources: Osmani (Learning JavaScript Design Patterns), Miller & Patterson (Islands Architecture), Qwik documentation (Hevery), React documentation (Server Components), Astro documentation, Google Chrome team (web.dev), Archibald (hydration analysis)

Covers: full hydration cost model, progressive hydration, selective hydration, islands architecture, React Server Components, resumability, and hydration optimization techniques.

## The Hydration Problem

Hydration is the process of attaching JavaScript event listeners and restoring component state to server-rendered HTML. It is the primary bottleneck between First Contentful Paint (FCP) and Time to Interactive (TTI).

### Full Hydration Cost

When a page is fully hydrated, the browser must:

1. Download the entire JavaScript bundle for the page
2. Parse and compile the JavaScript
3. Execute the component tree top-down to rebuild the virtual DOM
4. Diff the virtual DOM against the server-rendered HTML
5. Attach event listeners to every interactive element

This replays the entire rendering logic client-side, even for components that will never change or respond to user interaction.

### Cost Factors

| Factor | Impact |
|---|---|
| Total JS bundle size | Download time, parse time, memory |
| Number of components | Virtual DOM reconstruction time |
| Component complexity | Execution time per component |
| Third-party scripts | Compete for main thread |
| Device capability | Low-end mobile devices are 5-10x slower than desktop |

### The TTI Gap

The time between FCP (user sees content) and TTI (user can interact) is the hydration gap. During this window:

- Buttons appear but do not respond to clicks
- Forms render but do not submit
- Links look clickable but navigation does not work
- Users perceive the page as broken or laggy

## Progressive Hydration

Progressive hydration defers the hydration of non-critical components, reducing the initial JS execution and closing the TTI gap for above-fold content.

### Hydration Triggers

| Trigger | When Component Hydrates | Use Case |
|---|---|---|
| Idle | When the main thread is idle (requestIdleCallback) | Below-fold content, non-urgent UI |
| Visible | When the component enters the viewport (IntersectionObserver) | Long pages, lazy sections |
| Interaction | When the user hovers, clicks, or focuses | Heavy widgets the user may never reach |
| Media query | When a viewport condition is met | Mobile-only or desktop-only components |
| Never | Component is never hydrated (static HTML only) | Purely presentational content |

### Implementation Pattern

```
Server renders full HTML
  -> Browser paints immediately (FCP)
  -> Critical above-fold components hydrate first
  -> Below-fold components register IntersectionObserver
  -> When scrolled into view, lazy-load JS chunk and hydrate
  -> Components the user never scrolls to are never hydrated
```

### Progressive Hydration Tradeoffs

| Advantage | Cost |
|---|---|
| Faster TTI for above-fold content | Complexity in defining hydration boundaries |
| Less initial JS execution | Brief non-interactive window for deferred components |
| Reduced main thread blocking | Must handle interaction before hydration (queue or ignore) |
| Works with existing component models | Framework support varies |

## Selective Hydration

Selective hydration, introduced with React 18's concurrent features, prioritizes hydrating components that the user is actively interacting with.

### How It Works

1. React streams server-rendered HTML with Suspense boundaries
2. JavaScript chunks load asynchronously per Suspense boundary
3. React begins hydrating components in tree order
4. If the user clicks a component that is not yet hydrated:
   - React interrupts current hydration
   - Prioritizes hydrating the clicked component
   - Resumes other hydration after the priority component is interactive

### Selective Hydration vs Progressive Hydration

| Aspect | Progressive | Selective |
|---|---|---|
| Trigger | Developer-defined (visible, idle, interaction) | User interaction (automatic) |
| Priority | Static priority order | Dynamic, responds to user intent |
| Framework coupling | Can be framework-agnostic | React 18+ specific (concurrent mode) |
| Granularity | Per component/section | Per Suspense boundary |
| Developer effort | Must configure triggers | Automatic with Suspense boundaries |

## Islands Architecture

Islands architecture renders a static HTML page with isolated interactive "islands." Each island is an independent component that hydrates separately. The rest of the page is pure HTML with zero JavaScript.

### Core Model

```
Static HTML Page (no JS)
  |-- [Static Header]        <- pure HTML, no hydration
  |-- [Static Hero]           <- pure HTML, no hydration
  |-- [Interactive Carousel]  <- island, independent JS bundle, hydrates
  |-- [Static Content]        <- pure HTML, no hydration
  |-- [Interactive Comments]  <- island, independent JS bundle, hydrates
  |-- [Static Footer]         <- pure HTML, no hydration
```

### Islands Characteristics

| Aspect | Detail |
|---|---|
| JS payload | Only for interactive islands (often 10-30% of full hydration) |
| Hydration scope | Each island hydrates independently, no shared state |
| Static content | Zero JS cost, rendered once at build time or server time |
| Component framework | Islands can use different frameworks on the same page |
| State sharing | Not built-in; requires explicit mechanisms (events, stores) |
| SEO | Full HTML available to crawlers |

### Islands Tradeoffs

| Advantage | Cost |
|---|---|
| Minimal JS shipped to client | No automatic state sharing between islands |
| Each island is independently cacheable | Requires rethinking component architecture |
| Static content has zero JS overhead | Complex interactions spanning multiple islands are harder |
| Progressive enhancement by default | Framework ecosystem is smaller (Astro, Fresh, Marko) |
| Fast TTI for mostly-static pages | Not suitable for highly interactive applications |

### When to Use Islands

- Content-heavy sites with isolated interactive widgets
- Marketing pages with a few dynamic elements (forms, carousels)
- Documentation sites with interactive code playgrounds
- Blogs with comment sections or search

### When Islands Are Not Appropriate

- Highly interactive dashboards where most components have state
- Applications with extensive cross-component state (use progressive hydration or RSC)
- Real-time collaborative tools

## React Server Components (RSC)

RSC introduces a new component type that renders exclusively on the server and sends rendered output (not JS) to the client. Server Components have zero hydration cost.

### Server vs Client Components

| Aspect | Server Component | Client Component |
|---|---|---|
| Renders on | Server only | Server (SSR) + Client (hydration) |
| JavaScript sent | None (rendered to RSC payload) | Full component JS bundle |
| Can use hooks (useState, useEffect) | No | Yes |
| Can access server resources (DB, filesystem) | Yes | No |
| Can handle user interaction | No | Yes |
| Hydration cost | Zero | Normal |
| Re-renders on | Server action or navigation | State/prop changes |

### RSC Architecture

```
Component Tree:
  ServerLayout (server) -> no JS, renders to HTML
    ServerNav (server) -> no JS, can query DB directly
    ClientSearchBar (client) -> JS shipped, hydrates, handles input
    ServerContent (server) -> no JS, renders markdown from filesystem
    ClientComments (client) -> JS shipped, hydrates, handles posting
    ServerFooter (server) -> no JS, renders links
```

Only `ClientSearchBar` and `ClientComments` contribute to the JS bundle.

### RSC Tradeoffs

| Advantage | Cost |
|---|---|
| Zero JS for server components | New mental model (server/client boundary) |
| Direct server resource access (DB, APIs) | Cannot use browser APIs in server components |
| Reduced bundle size | Framework-specific (React ecosystem only) |
| Composable with client components | Serialization constraints at the boundary |
| Server components can pass data to client components as props | Client components cannot import server components |

### RSC vs Islands

| Aspect | RSC | Islands |
|---|---|---|
| Granularity | Component-level server/client split | Page-level static/interactive split |
| State sharing | Props flow from server to client components | Explicit (events, stores) |
| Framework | React only | Framework-agnostic (Astro, Fresh, Marko) |
| Nesting | Client inside server, server inside client (via children) | Islands are top-level, not nested |
| Data fetching | Server components fetch directly | Islands fetch client-side or via page props |

## Resumability

Resumability, pioneered by Qwik, eliminates hydration entirely. Instead of replaying the application on the client, the server serializes the application state and event listener locations into the HTML. The client resumes from that state without re-executing component code.

### How Resumability Works

1. Server renders HTML and serializes component state, event handlers, and closures into HTML attributes
2. HTML is sent to the client with a tiny (~1KB) runtime loader
3. No JavaScript executes on page load (TTI equals FCP)
4. When the user interacts with an element, the runtime:
   - Reads the serialized handler reference from the HTML
   - Lazy-loads only the specific handler code
   - Executes the handler
5. Only the code needed for the interaction is ever downloaded

### Resumability vs Hydration

| Aspect | Hydration (React, Vue, etc.) | Resumability (Qwik) |
|---|---|---|
| Startup JS execution | Replay entire component tree | Zero (state serialized in HTML) |
| TTI | Delayed by hydration time | Instant (equals FCP) |
| First interaction cost | Near-zero (already hydrated) | Small (lazy-load handler) |
| JS download | Eager (full bundle or chunks) | Lazy (per-interaction) |
| Serialization overhead | None (state in JS memory) | HTML is larger (serialized state) |
| Framework maturity | Mature, large ecosystem | Newer, growing ecosystem |

### When to Consider Resumability

- Performance-critical pages where TTI must equal FCP
- Mobile-first applications targeting low-end devices
- Pages with many interactive elements but low interaction probability
- Applications where hydration cost exceeds acceptable thresholds

## Hydration Optimization Techniques

### Reducing Hydration Cost (Framework-Agnostic)

| Technique | Effect |
|---|---|
| Mark non-interactive components as static | Exclude from hydration tree |
| Code split by route | Only load JS for current page |
| Lazy load below-fold components | Defer hydration until needed |
| Minimize third-party scripts | Reduce main thread contention |
| Use CSS instead of JS for animations | Remove components from hydration scope |
| Audit `useEffect` usage | Remove unnecessary client-side effects |
| Avoid hydration mismatches | Ensure server and client render identical output |

### Measuring Hydration Performance

| Metric | Tool | Target |
|---|---|---|
| Total Blocking Time (TBT) | Lighthouse | < 200ms |
| Time to Interactive (TTI) | Lighthouse | < 3.8s on mobile |
| Interaction to Next Paint (INP) | CrUX, web-vitals | < 200ms |
| JS execution time | DevTools Performance panel | Minimize long tasks > 50ms |
| Hydration time | Custom performance marks | As close to zero as achievable |
