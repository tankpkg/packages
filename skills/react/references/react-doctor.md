# React Doctor Rule Reference

Sources: React Doctor documentation; github.com/millionco/react-doctor.

React Doctor provides 60+ rules across 11 categories. Rules are automatically toggled based on detected framework (Next.js, Vite, Remix, React Native), React version, and compiler setup.

## State & Effects

Prevent misuse of hooks that leads to unnecessary renders, stale data, or infinite loops.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-derived-state-effect` | error | Computing derived state inside useEffect instead of useMemo or inline |
| `no-fetch-in-effect` | error | Fetching data in useEffect instead of a data library (TanStack Query, SWR) |
| `no-cascading-set-state` | warning | Multiple setState calls in sequence causing extra renders |
| `no-effect-event-handler` | warning | Using useEffect to respond to events instead of event handlers |
| `no-derived-useState` | warning | Storing derived values in useState instead of computing inline |
| `prefer-useReducer` | warning | Complex state logic better suited to useReducer |
| `rerender-lazy-state-init` | warning | Expensive computation in useState initializer without lazy init |
| `rerender-functional-setstate` | warning | setState with stale value instead of functional update |
| `rerender-dependencies` | error | Missing or incorrect dependency arrays in hooks |

```tsx
// Bad: derived state in effect
const [fullName, setFullName] = useState("");
useEffect(() => {
  setFullName(`${first} ${last}`);
}, [first, last]);

// Good: derive inline
const fullName = `${first} ${last}`;
```

## Architecture

Keep components focused and avoid patterns that break React's rendering model.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-giant-component` | warning | Components exceeding 300 lines |
| `no-render-in-render` | error | Defining components inside another component's render |
| `no-nested-component-definition` | error | Nested component definitions that remount on every render |

```tsx
// Bad: component defined inside render
function Parent() {
  function Child() { return <div>hi</div>; }
  return <Child />;
}

// Good: define outside
function Child() { return <div>hi</div>; }
function Parent() { return <Child />; }
```

## Performance

Catch CSS animation pitfalls, memoization misuse, and hydration issues.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-usememo-simple-expression` | warning | Memoizing trivial expressions (strings, booleans) |
| `no-layout-property-animation` | warning | Animating width, height, top, left (use transform instead) |
| `rerender-memo-with-default-value` | warning | Memoized components with default prop values causing re-renders |
| `no-inline-prop-on-memo-component` | warning | Passing inline objects/arrays to React.memo components |
| `rendering-hydration-no-flicker` | error | Patterns that cause visible flicker during hydration |
| `no-transition-all` | warning | Using `transition: all` instead of specific properties |
| `no-global-css-variable-animation` | warning | Animating CSS custom properties globally |
| `no-large-animated-blur` | warning | Blur animations over 10px (GPU-expensive) |
| `no-scale-from-zero` | warning | Scaling from 0 causes layout shift |
| `no-permanent-will-change` | warning | Permanent `will-change` wastes GPU memory |
| `rendering-animate-svg-wrapper` | warning | Animated SVGs not wrapped for performance |

```tsx
// Bad: animating layout property
.modal { transition: height 0.3s; }

// Good: animate transform
.modal { transition: transform 0.3s; }
```

## Security

Detect code execution risks and leaked secrets in client bundles.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-eval` | error | Usage of eval() or Function() constructor |
| `no-secrets-in-client-code` | error | Hardcoded API keys, tokens, or secrets in client-side code |

## Bundle Size

Prevent bloated bundles from common import mistakes.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-barrel-import` | warning | Importing from barrel index files that prevent tree-shaking |
| `no-full-lodash-import` | warning | `import _ from "lodash"` instead of `import debounce from "lodash/debounce"` |
| `no-moment` | warning | Using moment.js (deprecated, use date-fns or dayjs) |
| `prefer-dynamic-import` | warning | Heavy libraries loaded synchronously instead of dynamically |
| `use-lazy-motion` | warning | Full Framer Motion bundle instead of LazyMotion |
| `no-undeferred-third-party` | warning | Third-party scripts not deferred |

```tsx
// Bad: full lodash import
import _ from "lodash";
_.debounce(fn, 300);

// Good: per-function import
import debounce from "lodash/debounce";
debounce(fn, 300);
```

## Correctness

Catch bugs that produce wrong output or break React's reconciliation.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `no-array-index-as-key` | error | Using array index as key in lists |
| `rendering-conditional-render` | warning | Incorrect conditional rendering patterns (e.g., `count && <Comp />` rendering "0") |
| `no-prevent-default` | warning | Unnecessary preventDefault on non-native events |

```tsx
// Bad: falsy number renders "0"
{count && <Badge count={count} />}

// Good: explicit boolean check
{count > 0 && <Badge count={count} />}
```

## Next.js Rules

Enabled automatically when Next.js is detected. Covers framework-specific patterns.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `nextjs-no-img-element` | warning | Using `<img>` instead of `next/image` |
| `nextjs-async-client-component` | error | Async client components (not supported) |
| `nextjs-no-a-element` | warning | Using `<a>` instead of `next/link` |
| `nextjs-no-use-search-params-without-suspense` | error | `useSearchParams` without Suspense boundary |
| `nextjs-no-client-fetch-for-server-data` | warning | Client-side fetch for data available in Server Components |
| `nextjs-missing-metadata` | warning | Page routes missing metadata exports |
| `nextjs-no-client-side-redirect` | warning | Client-side redirects instead of server-side |
| `nextjs-no-redirect-in-try-catch` | error | Wrapping redirect() in try-catch (redirect throws) |
| `nextjs-image-missing-sizes` | warning | `next/image` without sizes prop |
| `nextjs-no-native-script` | warning | Using `<script>` instead of `next/script` |
| `nextjs-inline-script-missing-id` | warning | Inline `next/script` without id prop |
| `nextjs-no-font-link` | warning | Font `<link>` instead of `next/font` |
| `nextjs-no-css-link` | warning | CSS `<link>` instead of component import |
| `nextjs-no-polyfill-script` | warning | Manual polyfill scripts (Next.js includes them) |
| `nextjs-no-head-import` | warning | Importing `next/head` instead of using Metadata API |
| `nextjs-no-side-effect-in-get-handler` | error | Side effects in GET route handlers |

## React Native Rules

Enabled automatically when React Native is detected.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `rn-no-raw-text` | error | Text outside `<Text>` component |
| `rn-no-deprecated-modules` | warning | Using deprecated RN modules instead of community packages |
| `rn-no-legacy-expo-packages` | warning | Outdated Expo package imports |
| `rn-no-dimensions-get` | warning | `Dimensions.get()` instead of `useWindowDimensions` hook |
| `rn-no-inline-flatlist-renderitem` | warning | Inline renderItem causing FlatList re-renders |
| `rn-no-legacy-shadow-styles` | warning | Legacy shadow styles instead of modern API |
| `rn-prefer-reanimated` | warning | Using Animated API instead of Reanimated |
| `rn-no-single-element-style-array` | warning | Array syntax for a single style object |

## Server Rules

| Rule | Severity | What it catches |
| --- | --- | --- |
| `server-auth-actions` | error | Server Actions without auth validation |
| `server-after-nonblocking` | warning | Not using `after()` for non-blocking operations |

## Client Rules

| Rule | Severity | What it catches |
| --- | --- | --- |
| `client-passive-event-listeners` | warning | Non-passive scroll/touch listeners hurting scroll performance |

## JavaScript Performance

General JS patterns that affect React app performance.

| Rule | Severity | What it catches |
| --- | --- | --- |
| `js-combine-iterations` | warning | Multiple array iterations that could be combined |
| `js-tosorted-immutable` | warning | Mutating sort instead of `toSorted()` |
| `js-hoist-regexp` | warning | RegExp created inside loops |
| `js-min-max-loop` | warning | Manual loops for min/max instead of `Math.min`/`Math.max` |
| `js-set-map-lookups` | warning | Array includes/find for lookups instead of Set/Map |
| `js-batch-dom-css` | warning | Unbatched DOM/CSS reads and writes |
| `js-index-maps` | warning | Array find for indexed lookups instead of Map |
| `js-cache-storage` | warning | Repeated localStorage/sessionStorage reads without caching |
| `js-early-exit` | warning | Deep nesting instead of early returns |
| `async-parallel` | warning | Sequential async operations that could run in parallel |

## Built-in React and Accessibility Rules

React Doctor also enforces standard rules via oxlint:

| Rule | Severity |
| --- | --- |
| `react/rules-of-hooks` | error |
| `react/no-direct-mutation-state` | error |
| `react/jsx-no-duplicate-props` | error |
| `react/jsx-key` | error |
| `react/no-danger` | warning |
| `jsx-a11y/alt-text` | error |
| `jsx-a11y/anchor-is-valid` | warning |
| `jsx-a11y/click-events-have-key-events` | warning |

## Configuration Reference

### Config File Options
| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `ignore.rules` | `string[]` | `[]` | Rules to suppress |
| `ignore.files` | `string[]` | `[]` | File globs to exclude |
| `lint` | `boolean` | `true` | Enable lint checks |
| `deadCode` | `boolean` | `true` | Enable dead code detection via knip |
| `verbose` | `boolean` | `false` | Show file details per rule |
| `diff` | `boolean \| string` | — | Diff mode or base branch name |

### GitHub Actions Inputs
| Input | Default | Description |
| --- | --- | --- |
| `directory` | `.` | Project directory to scan |
| `verbose` | `true` | Show file details per rule |
| `project` | — | Workspace project(s) to scan |
| `diff` | — | Base branch for diff mode |
| `github-token` | — | Posts findings as PR comment |
| `node-version` | `20` | Node.js version |

### Programmatic API Types
```ts
interface Diagnostic {
  filePath: string;
  plugin: string;
  rule: string;
  severity: "error" | "warning";
  message: string;
  help: string;
  line: number;
  column: number;
  category: string;
}

interface DiagnoseResult {
  score: { score: number; label: string } | null;
  diagnostics: Diagnostic[];
  project: { framework: string; reactVersion: string };
}
```
