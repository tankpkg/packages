---
name: "@tank/react"
description: "Expert React patterns for production apps. Covers component composition (compound, polymorphic, slots), hooks, state architecture, performance, React 19 (use, Actions, useActionState, useFormStatus, ref as prop), React Compiler, Vite-era tooling, TanStack Query, and linting with React Doctor. Triggers: react, component, hook, useState, useEffect, useReducer, useMemo, useCallback, context, render, JSX, props, state, state management, server state, TanStack Query, suspense, memo, React performance, component performance, testing, React 19, React Compiler, server component, React Server Components, RSC, Vite, compound component, polymorphic, useActionState, react-doctor, linter, health score, dead code."
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
| Element-agnostic styling | Polymorphic (`as` prop) | Unified API across elements | Type `as` for safety |
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
| `useActionState` | Form action result + pending flag | Server/client form actions | Replaces deprecated useFormState |
| `useFormStatus` | Read parent form pending state | Submit buttons, progress indicators | Must be child of `<form>` |
| `ref` as prop | Pass refs without forwardRef | Any component exposing DOM | Drop forwardRef boilerplate |
| Server Components | Zero-bundle UI on server | Read-only, data-heavy views | Requires boundary discipline |
| Context as provider | `<Ctx>` replaces `<Ctx.Provider>` | All context usage | Drop `.Provider` suffix |

## Modern React Stack (2026)
| Layer | Tool | Why | Note |
| --- | --- | --- | --- |
| Bundler | Vite | Fast HMR, ESM-native | `plugin-react-swc` for speed |
| Memoization | React Compiler | Auto-memoizes pure renders | Remove manual memo when adopted |
| Server state | TanStack Query | Cache, invalidation, optimistic UI | Replaces useEffect fetch patterns |
| Data loading | Suspense + `use()` | Declarative async boundaries | Boundaries at latency points |
| Client state | useState / useReducer | Local-first, lift only when needed | External stores for cross-route |
| Routing | TanStack Router / React Router | Type-safe, loaders prevent waterfalls | File-based or config-based |

-> See `references/modern-react-2026.md` for setup guides and detailed patterns.

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
| Event handlers with stale state | Use functional updates | Avoid stale closure bugs |
| Keys from array index | Stable domain IDs | Preserve item identity |
| Wrap in `forwardRef` (React 19+) | Pass `ref` as regular prop | Less boilerplate |

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
- When React Compiler is active, remove redundant manual memoization.
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
React Doctor scans for anti-patterns and outputs a 0-100 health score. Run `npx -y react-doctor@latest .` to scan. Use `--diff main` for CI, `--fix` to auto-fix, `--score` for CI-friendly numeric output.
-> See `references/react-doctor.md` for the full rule reference, CI integration, and configuration.

## Reference Index
| File | Contents |
| --- | --- |
| `references/component-patterns.md` | Compound, polymorphic, slots, render props, controlled/uncontrolled |
| `references/hooks-and-state.md` | Custom hooks, useReducer patterns, effects, React 19 hooks |
| `references/performance.md` | Memo, code splitting, virtualization, React Compiler, profiling |
| `references/modern-react-2026.md` | Vite setup, React Compiler adoption, TanStack Query, React 19 API |
| `references/react-doctor.md` | Full rule reference, CI setup, configuration, programmatic API |
