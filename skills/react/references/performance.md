# Performance

Sources: React documentation; React Compiler RFC.

## React.memo Decision Table
Use memoization when props are stable and render is expensive.
Avoid memoization when props change every render.
Measure before adding memoization to avoid wasted work.
Use `React.memo` for leaf components in hot lists.
Pair memoization with stable callbacks and values.
```tsx
// Good: stable props + expensive rendering
const Avatar = React.memo(function Avatar({ user }: { user: User }) {
  return <img src={user.image} alt={user.name} />;
});
// Bad: unstable props recreated on every render
<Avatar user={{ name, image }} />
// Fix: hoist or memoize prop objects
const user = React.useMemo(() => ({ name, image }), [name, image]);
<Avatar user={user} />;
```

## useMemo and useCallback
Memoize computations that are heavy or used as dependencies.
Use callbacks only when passing to memoized children.
Avoid wrapping trivial calculations that are cheap.
Keep dependency arrays precise to avoid stale results.
Prefer inlining logic until profiler shows a hotspot.
```tsx
const filtered = React.useMemo(
  () => items.filter((i) => i.status === filter),
  [items, filter]
);
const onSelect = React.useCallback(
  (id: string) => setSelectedId(id),
  []
);
```

## Code Splitting with React.lazy
Split by route or heavy widgets first.
Keep Suspense fallbacks aligned with layout size.
Use named chunks to make bundles readable.
Avoid too many tiny chunks that hurt network overhead.
Combine with data prefetch for perceived performance.
```tsx
const AnalyticsPanel = React.lazy(() => import(/* webpackChunkName: "analytics" */ "./AnalyticsPanel"));
function Dashboard() {
  return (
    <React.Suspense fallback={<PanelSkeleton />}>
      <AnalyticsPanel />
    </React.Suspense>
  );
}
```

## Virtualization for Large Lists
Virtualize when list size or row complexity is high.
Keep item heights predictable for smoother scrolling.
Use windowing libraries to render only visible items.
Avoid virtualization for short lists or simple rows.
Keep item keys stable to prevent row reuse issues.
```tsx
import { FixedSizeList as List } from "react-window";
function Users({ users }: { users: User[] }) {
  return (
    <List height={400} width={600} itemCount={users.length} itemSize={48}>
      {({ index, style }) => (
        <div style={style} key={users[index].id}>{users[index].name}</div>
      )}
    </List>
  );
}
```

## React Compiler (React 19)
Rely on the compiler to memoize pure components automatically.
Avoid manual memoization unless profiling proves a need.
Mark components as pure by keeping side effects out of render.
Opt out when memoization causes stale visuals.
Use compiler output to verify skipped re-renders.
```tsx
// React Compiler can auto-memoize this pure component
function Price({ value }: { value: number }) {
  return <span>{value.toFixed(2)}</span>;
}
// Opt out by mutating or using refs in render (avoid this)
function BadPrice({ value }: { value: number }) {
  const ref = React.useRef(0);
  ref.current++;
  return <span>{value}-{ref.current}</span>;
}
```

## Profiling Workflow
Profile in React DevTools before optimizing.
Sort by self time to find real bottlenecks.
Inspect props changes to find unstable inputs.
Use why-did-you-render to spot unnecessary rerenders.
Capture interactions to see user-perceived lag.
```tsx
if (process.env.NODE_ENV === "development") {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const whyDidYouRender = require("@welldone-software/why-did-you-render");
  whyDidYouRender(React, { trackAllPureComponents: true });
}
```

## Bundle Size Optimization
Prefer dynamic imports for low-traffic screens.
Avoid pulling entire utility libraries for one function.
Use tree-shakeable ESM builds.
Split vendor bundles based on usage patterns.
Inspect bundles regularly to prevent regressions.
```tsx
// Good: per-function import
import debounce from "lodash/debounce";
// Good: dynamic import for rare feature
const PdfViewer = React.lazy(() => import("./PdfViewer"));
```

## Image Optimization
Use responsive images and lazy loading for below-the-fold media.
Serve modern formats when available.
Avoid layout shifts by reserving space.
Prefer framework helpers such as next/image.
Defer non-critical images until idle.
```tsx
import Image from "next/image";
function Hero() {
  return (
    <Image
      src="/hero.jpg"
      alt="Product overview"
      width={1200}
      height={600}
      priority
    />
  );
}
```

## Rendering Performance and Keys
Use stable domain ids for keys instead of array indexes.
Keep list item components small and memoized when needed.
Avoid inline objects and callbacks in lists.
Split list rows into memoized leaf components.
Use `key` on the outermost repeated element.
```tsx
const Row = React.memo(function Row({ item }: { item: Item }) {
  return <li>{item.label}</li>;
});
function List({ items }: { items: Item[] }) {
  return <ul>{items.map((item) => <Row key={item.id} item={item} />)}</ul>;
}
```

## Transition and Deferred Value

Use `useTransition` to mark state updates as non-urgent so the UI stays responsive during expensive renders.
Use `useDeferredValue` to defer expensive derived computations while showing stale data.
Combine with Suspense for progressive loading without blocking interaction.

```tsx
import { useTransition, useDeferredValue } from "react";

function SearchResults({ query }: { query: string }) {
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;
  const results = useSearchResults(deferredQuery);

  return (
    <div style={{ opacity: isStale ? 0.6 : 1 }}>
      {results.map((r) => <ResultItem key={r.id} item={r} />)}
    </div>
  );
}

function FilterPanel({ items, onFilter }: { items: Item[]; onFilter: (f: string) => void }) {
  const [isPending, startTransition] = useTransition();

  function handleChange(value: string) {
    startTransition(() => onFilter(value));
  }

  return (
    <>
      <input onChange={(e) => handleChange(e.target.value)} />
      {isPending && <Spinner />}
    </>
  );
}
```

## Streaming and Suspense Patterns

Use Suspense boundaries to stream partial UI from server components.
Place boundaries around slow data fetches so fast sections render immediately.
Avoid nesting too many Suspense boundaries — group related data.
Use `fallback` that matches the layout dimensions to prevent shifts.

```tsx
function Dashboard() {
  return (
    <div className="grid grid-cols-2 gap-4">
      <React.Suspense fallback={<ChartSkeleton />}>
        <RevenueChart />
      </React.Suspense>
      <React.Suspense fallback={<TableSkeleton />}>
        <RecentOrders />
      </React.Suspense>
    </div>
  );
}
```

## State Colocation

Keep state as close to where it is used as possible.
Lift state only when siblings need it — never default to global state.
Extract components to isolate rerenders to the smallest subtree.

| Symptom | Fix |
| --- | --- |
| parent rerenders when child state changes | colocate state in child |
| unrelated siblings rerender together | split into separate components |
| context causes full-tree rerenders | split context by update frequency |

```tsx
// Bad: filter state in parent rerenders entire list
function Page() {
  const [filter, setFilter] = useState("");
  return (
    <>
      <FilterInput value={filter} onChange={setFilter} />
      <ExpensiveList filter={filter} />
    </>
  );
}

// Good: isolate filter state with composition
function Page() {
  return <FilteredList />;
}

function FilteredList() {
  const [filter, setFilter] = useState("");
  return (
    <>
      <FilterInput value={filter} onChange={setFilter} />
      <ExpensiveList filter={filter} />
    </>
  );
}
```

## Anti-Patterns and Corrections
Avoid memoizing everything by default.
Do not use `useMemo` for trivial constants.
Avoid inline functions in list items when it creates rerender storms.
Do not split bundles by component without analyzing load cost.
Avoid virtualization when row height changes frequently.
Do not wrap every component in `React.memo` — profile first.
Do not hoist state to global stores when local state suffices.
Avoid excessive context splitting that makes code hard to follow.

```tsx
// Bad: memoizing trivial value
const label = React.useMemo(() => "Save", []);
// Good: inline trivial values
const labelFixed = "Save";

// Bad: global store for local UI state
const useFilterStore = create((set) => ({ filter: "", setFilter: (f: string) => set({ filter: f }) }));
// Good: local useState for component-scoped state
const [filter, setFilter] = useState("");
```
