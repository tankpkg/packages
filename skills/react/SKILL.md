---
name: "@tank/react"
description: "Expert React patterns for production apps. Covers linting with React Doctor. Triggers: react, component, hook, useState, useEffect, useReducer, useMemo, useCallback, context, render, JSX, props, state, state management, server state, TanStack Query, suspense, memo, performance, testing, React 19, server component, react-doctor, linter, health score, dead code."
---
# React

## Core Philosophy
- Composition over configuration: shape APIs with children, slots, and small props.
- Colocation principle: keep state, view, and data fetching near the consumer.
- Derive, don't sync: compute from source of truth, avoid mirror state.
- Make invalid states unrepresentable: model state transitions explicitly.
- Optimize for change: prefer patterns that localize edits.
- Keep effects reactive: side effects follow data, not events.
- Name state by intent, not by UI widget.

## Component Decision Tree
| When you need | Use | Why | Notes |
| --- | --- | --- | --- |
| Static UI with simple props | Simple component | Lowest overhead | Keep props shallow |
| Shared state across related pieces | Compound component | Implicit coordination | Use context + slots |
| Behavior injection into layout | Render prop | Flexible control | Prefer stable function identity |
| Wrap a 3rd-party API | HOC | Encapsulate wiring | Avoid for new component APIs |
| Reuse logic without UI | Custom hook | Share behavior | Return data + actions |

## State Management Decision Tree
| Situation | Use | Rationale | Tradeoffs |
| --- | --- | --- | --- |
| Single field or UI toggle | useState | Direct, local | Avoid derived duplicates |
| Multi-step workflow | useReducer | Explicit transitions | Slightly more boilerplate |
| Shared local UI state | Context | Avoid prop drilling | Split by concern |
| Cross-route app state | External store | Centralized access | Use selectors |
| Server data cache | TanStack Query | Cache + sync | Learn invalidation |

## Hooks Rules of Thumb
- Start with state local; lift only when 2+ siblings depend on it.
- Prefer `useReducer` when updates depend on the previous state in many places.
- Put async data in a server-state tool; don't mirror it in `useState`.
- Make effects about synchronization, not computation.
- Stabilize callbacks only when you pass them to memoized children.
- Store derived values with `useMemo` only when recomputation is expensive.
- Avoid `useEffect` for DOM reads; reach for refs and layout effects intentionally.
- If a hook returns both data and actions, keep the action names stable.
- Minimize hook parameters; prefer passing config objects.

## React 19 Features Quick Reference
| Feature | What it enables | When to use | Pitfall |
| --- | --- | --- | --- |
| `use()` | Read promises/context in render | Server and client data boundaries | Requires Suspense |
| Actions | Async mutations with form integration | Form submissions | Avoid manual loading flags |
| `useOptimistic` | Instant UI while awaiting server | Mutations with predictable rollback | Ensure reconciliation |
| Server Components | Zero-bundle UI on server | Read-only, data-heavy views | Requires boundary discipline |

## Anti-Patterns
| Don't | Do Instead | Why |
| --- | --- | --- |
| Prop drill through 4+ layers | Introduce Context boundary | Reduce wiring churn |
| Copy props into state | Derive in render | Avoid divergence |
| `useEffect` to compute derived values | `useMemo` or inline | Keep data flow explicit |
| Store server data in `useState` | Use query cache | Built-in invalidation |
| Overuse `React.memo` | Memoize only hotspots | Extra work otherwise |
| Inline object props every render | Memoize or hoist | Stabilize referential equality |
| One global Context for everything | Split by domain | Reduce rerenders |
| Event handlers that depend on stale state | Use functional updates | Avoid stale closure bugs |
| Keys from array index | Stable domain IDs | Preserve item identity |

## Component API Checklist
- Expose the minimum props needed to express intent.
- Prefer boolean props for mode switches; prefer enums for variants.
- Use `children` for structure and provide slots for customization.
- Keep side-effecting props explicit (`onOpen`, `onClose`, `onSubmit`).
- Return primitive data from hooks, not JSX.
- If a prop can be derived, remove it from the public API.
- Keep controlled and uncontrolled modes separate and obvious.
- Document default behavior with tests.

## Effect Design Checklist
- Identify the external system being synchronized.
- Keep the dependency list aligned with the system inputs.
- Use `AbortController` for fetch cancellation.
- Prefer `useLayoutEffect` only for layout reads or measurement.
- Cleanup always mirrors setup; avoid conditional cleanup.
- Avoid `setState` in effects when value can be derived.
- Never wire effects to user events; use event handlers.
- Promote repeated effect patterns into a custom hook.

## Suspense and Data Boundaries
- Add Suspense at product-level latency points, not every component.
- Keep fallback UI representative of the final layout.
- Isolate error boundaries per feature area.
- Avoid shared mutable state across server and client components.
- Use data loaders at route boundaries to avoid waterfalls.
- Prefer streaming for long-tail data, keep critical path small.
- Avoid hiding errors by catching promises without rendering.

## Testing Heuristics
- Test the user-visible output, not internal state.
- Prefer React Testing Library queries that match user intent.
- Avoid snapshot tests for dynamic content; assert specific UI.
- Use MSW or a query cache to model server responses.
- Separate unit tests for hooks from integration tests for screens.
- Assert optimistic updates and rollback behavior explicitly.
- Keep test data realistic to catch rendering edge cases.
- When in doubt, test the boundary between components.

## TypeScript Integration
- Model props with discriminated unions for variant-driven UIs.
- Type `children` explicitly when slots are required.
- Use `ComponentPropsWithoutRef<"button">` for pass-through props.
- Prefer `satisfies` to keep config objects narrow.
- Keep hooks generic only when the type pays for itself.
- Treat `as` polymorphism as part of the public API contract.

## Operational Workflow
- Start by modeling state transitions in a reducer or state chart.
- Build the smallest component tree that expresses the intent.
- Add composition points only after usage shows friction.
- Introduce Suspense and streaming after data paths are stable.
- Profile before memoization to avoid premature tuning.
- Document invariants with tests instead of comments.

## Performance Posture
- Prefer fewer renders over cheaper renders when possible.
- Avoid re-render cascades by splitting context providers.
- Use virtualization when list size > 200 or rendering cost is high.
- Treat `memo` and `useCallback` as opt-in tools, not defaults.
- Split bundles by route first, then by heavy widget.
- Inspect bundle output to validate tree-shaking.
- Defer non-critical work with `useTransition` or Actions.
- Use stable keys and stable item identity for lists.

## Migration Notes
- Prefer incremental refactors; wrap new components under old API.
- Introduce adapters for legacy props; deprecate in types.
- Use codemods for prop renames and hook replacements.
- Keep fallback UI identical during data-layer changes.
- Add feature flags for high-risk UI rewrites.
- Gate server component adoption per route.
- Keep a clear rollback path for Actions adoption.
- Remove dead code after two releases.

## Refactor Triggers
- Prop lists exceed 8-10 items or include derived values.
- Effects contain more than one external resource.
- A component has more than 2 responsibilities.
- A hook has side effects and state but no cleanup.
- Re-render time dominates in the profiler.
- Teams repeatedly add exceptions to the API.

## Linting with React Doctor
React Doctor is a CLI linter that scans React codebases for anti-patterns and outputs a 0–100 health score with actionable diagnostics. It auto-detects your framework (Next.js, Vite, Remix, React Native) and React version.

### Quick Start
```bash
npx -y react-doctor@latest .
```

### Key CLI Flags
| Flag | Purpose |
| --- | --- |
| `--verbose` | Show file paths and line numbers per rule |
| `--diff main` | Scan only files changed vs base branch |
| `--score` | Output only the numeric score (CI-friendly) |
| `--no-lint` | Skip lint checks, run dead code only |
| `--no-dead-code` | Skip dead code detection, run lint only |
| `--fix` | Open Ami to auto-fix issues |
| `-y` | Skip prompts, scan all workspace projects |

### Configuration
Create `react-doctor.config.json` at project root:
```json
{
  "ignore": {
    "rules": ["react/no-danger", "knip/exports"],
    "files": ["src/generated/**"]
  },
  "lint": true,
  "deadCode": true,
  "verbose": false,
  "diff": "main"
}
```
Or use the `reactDoctor` key in `package.json`.

### Rule Categories Overview
| Category | Focus | Example Rules |
| --- | --- | --- |
| State & Effects | Derived state, fetch in effect, cascading setState | `no-derived-state-effect`, `no-fetch-in-effect` |
| Architecture | Giant components, render-in-render | `no-giant-component`, `no-nested-component-definition` |
| Performance | Memoization misuse, layout animations, hydration | `no-usememo-simple-expression`, `no-layout-property-animation` |
| Security | eval usage, hardcoded secrets | `no-eval`, `no-secrets-in-client-code` |
| Bundle Size | Barrel imports, full lodash, moment.js | `no-barrel-import`, `no-full-lodash-import`, `no-moment` |
| Correctness | Array index keys, conditional rendering | `no-array-index-as-key`, `rendering-conditional-render` |
| Next.js | Image, link, metadata, server data | `nextjs-no-img-element`, `nextjs-missing-metadata` |
| React Native | Raw text, deprecated modules, Reanimated | `rn-no-raw-text`, `rn-prefer-reanimated` |

### Score Interpretation
| Range | Label | Action |
| --- | --- | --- |
| 75–100 | Great | Maintain current quality |
| 50–74 | Needs work | Address errors first, then warnings |
| 0–49 | Critical | Prioritize security and correctness rules |

### CI/CD Integration (GitHub Actions)
```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
- uses: millionco/react-doctor@main
  with:
    diff: main
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Programmatic API
```ts
import { diagnose } from "react-doctor/api";

const result = await diagnose("./path/to/project", {
  lint: true,
  deadCode: true,
});

console.log(result.score);       // { score: 82, label: "Good" }
console.log(result.diagnostics); // Array of Diagnostic objects
console.log(result.project);     // Detected framework, React version
```

### When to Suppress Rules
- `react/no-danger`: When rendering trusted sanitized HTML.
- `knip/exports`: For public library entry points consumed externally.
- `no-barrel-import`: For small internal barrels with few re-exports.
- Add suppressions to `ignore.rules` in config, not inline comments.

See `skills/react/references/react-doctor.md` for the full rule reference.

## Reference Index
- `skills/react/references/component-patterns.md`
- `skills/react/references/hooks-and-state.md`
- `skills/react/references/performance.md`
- `skills/react/references/react-doctor.md`
