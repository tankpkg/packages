# Svelte 5 Runes

Sources: Svelte official documentation (Svelte 5 runes, components, snippets), SvelteKit documentation, Rich Harris talks and migration notes, community production patterns from 2024-2026

Covers: Svelte 5 runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`, `$inspect`), snippets, event and binding patterns, component composition, shared-state patterns, and when to use runes instead of stores.

## The Mental Model Shift

Svelte 5 moves from the older “special top-level syntax” style to explicit reactive primitives called **runes**. Runes make reactivity visible and portable.

| Svelte 4 style | Svelte 5 style |
|---------------|----------------|
| `let count = 0` with `$:` labels | `let count = $state(0)` |
| `$: doubled = count * 2` | `let doubled = $derived(count * 2)` |
| `export let value` | `let { value } = $props()` |
| `<slot />` | snippets + `{@render ...}` |

The key idea: **state, derivation, effects, and props are now explicit tools instead of implicit syntax tricks**.

## `$state` for Mutable Local State

Use `$state` for local mutable state inside components.

```svelte
<script lang="ts">
  let count = $state(0)

  function increment() {
    count += 1
  }
</script>

<button onclick={increment}>{count}</button>
```

### What `$state` gives you

| Capability | Why it matters |
|-----------|----------------|
| Mutable values | Natural local component state |
| Deep proxying | Nested objects update reactively |
| Explicit intent | Easier to reason about than magic top-level `let` |
| Reuse in `.svelte.ts` / `.svelte.js` modules | Share rune-based logic across components |

### Deep object example

```svelte
<script lang="ts">
  let form = $state({
    email: '',
    profile: {
      displayName: ''
    }
  })
</script>

<input bind:value={form.email} />
<input bind:value={form.profile.displayName} />
```

You do not need immutable spread updates for every nested field.

## When `$state` is the wrong tool

| Situation | Better choice |
|----------|---------------|
| Purely computed value | `$derived` |
| Side effect / sync with browser API | `$effect` |
| Shared cross-route state with explicit subscription semantics | store or context + rune module |
| Server-loaded data | `load` + `$props().data` |

Do not turn everything into `$state` just because it is available.

## `$derived` for Computed Values

Use `$derived` for values that depend on other reactive inputs.

```svelte
<script lang="ts">
  let items = $state([1, 2, 3])
  let total = $derived(items.reduce((sum, n) => sum + n, 0))
</script>
```

### Rules for `$derived`

1. Keep it pure
2. Do not cause side effects inside the derivation
3. Prefer it over repeated inline calculations when the expression carries meaning

### Good `$derived` cases

| Case | Example |
|-----|---------|
| Totals | cart total from line items |
| Booleans | `isValid`, `isDirty`, `canSubmit` |
| Presentation | formatted display values |
| Filtering | visible items from raw state |

### Avoid using `$derived` for

| Anti-pattern | Why |
|-------------|-----|
| Fetching data | Side effect, belongs in load/effect |
| Writing to localStorage | Side effect |
| Triggering analytics | Side effect |

## `$effect` for Side Effects

Use `$effect` to react to state changes with imperative work.

```svelte
<script lang="ts">
  let query = $state('')

  $effect(() => {
    console.log('query changed', query)
  })
</script>
```

### Good `$effect` use cases

| Use case | Example |
|---------|---------|
| Local storage sync | save theme or draft state |
| DOM or browser API integration | resize observers, media queries |
| Third-party library setup | charts, maps, widgets |
| Cleanup-aware subscriptions | event listeners, timers |

### Cleanup pattern

```svelte
<script lang="ts">
  let enabled = $state(false)

  $effect(() => {
    if (!enabled) return

    const onResize = () => console.log(window.innerWidth)
    window.addEventListener('resize', onResize)

    return () => {
      window.removeEventListener('resize', onResize)
    }
  })
</script>
```

### `$effect` anti-patterns

| Anti-pattern | Better move |
|-------------|-------------|
| Deriving state from state | Use `$derived` |
| Fetching page data on navigation | Use `load` |
| Running on every keystroke without debounce | Add debounce or move to form submit |
| Writing business logic | Keep in plain functions/services |

## `$props` for Component Inputs

Props are now explicitly declared via `$props()`.

```svelte
<script lang="ts">
  type Props = {
    title: string
    count?: number
  }

  let { title, count = 0 }: Props = $props()
</script>
```

### Why this is better than `export let`

| Benefit | Meaning |
|--------|---------|
| Explicit destructuring | Default values live in one place |
| Better TS ergonomics | Strong prop typing |
| Clear mental model | Props are inputs, not magic declarations |

### Prop design rules

1. Keep prop APIs narrow
2. Prefer callback props over dispatcher complexity
3. Use defaults sparingly and intentionally
4. Move large object construction out of the child component

## `$bindable` for Two-Way Binding

Use `$bindable` only when the child intentionally exposes writable state.

```svelte
<script lang="ts">
  let { value = $bindable('') } = $props()
</script>

<input bind:value />
```

### When binding is appropriate

| Good fit | Why |
|---------|-----|
| Form controls | Mirrors native input behavior |
| Small controlled primitives | Simple parent-child sync |
| Custom input wrappers | Preserves ergonomic `bind:value` API |

### When not to use it

| Anti-pattern | Better move |
|-------------|-------------|
| Complex domain objects | Use explicit callbacks |
| Multi-step workflows | Lift state up clearly |
| Hidden side effects on write | Expose event/callback instead |

## `$inspect` for Debugging

`$inspect` is for debugging reactive flows during development.

```svelte
<script>
  let count = $state(0)
  $inspect(count)
</script>
```

Use it to understand reactive values, not as a permanent logging strategy.

## Snippets Replace Slot Mental Overload

Snippets make render-passed content and reusable markup more explicit.

### Basic snippet

```svelte
{#snippet itemRow(item)}
  <li>{item.name}</li>
{/snippet}

<ul>
  {#each items as item}
    {@render itemRow(item)}
  {/each}
</ul>
```

### Snippet vs slot intuition

| Need | Use |
|-----|-----|
| Reusable markup in same component | snippet |
| Render-prop style customization | snippet passed as prop / child pattern |
| Simple component composition in legacy code | slot-compatible migration path |

Snippets make local render reuse cleaner than many duplicated fragments.

## Event Handling in Svelte 5

Svelte 5 leans harder toward callback props and native DOM handlers.

### Preferred component communication

| Pattern | Use when |
|--------|----------|
| Callback prop | Parent must react to child action |
| Context API | Shared tree-level capabilities |
| Store / shared rune module | Cross-tree or app-level state |

### Callback prop example

```svelte
<script lang="ts">
  let { onSelect }: { onSelect: (id: string) => void } = $props()
</script>

<button onclick={() => onSelect('123')}>Select</button>
```

This is usually easier to type and reason about than a custom dispatcher.

## Bindings and Form Patterns

Native bindings remain valuable. Use them directly for plain forms.

| Input type | Pattern |
|-----------|---------|
| Text input | `bind:value` |
| Checkbox | `bind:checked` |
| Select | `bind:value` |
| Group inputs | `bind:group` |
| File input | handle from event / FormData |

Do not over-abstract forms until validation and submission patterns demand it.

## Runes vs Stores

Runes are the default. Stores still matter.

### Choose runes when

| Signal | Why |
|-------|-----|
| State is local to one component | simplest option |
| Shared logic can live in `.svelte.ts` module | reuse without store ceremony |
| You want fine-grained reactive primitives | direct and explicit |

### Choose stores when

| Signal | Why |
|-------|-----|
| Existing codebase already uses stores heavily | consistency |
| You need explicit subscription contract with non-Svelte consumers | interoperable API |
| External libraries expect store interface | compatibility |

### Migration rule

Do not rewrite every store just because runes exist. Replace stores opportunistically where runes clearly simplify code.

## Shared State Patterns

### Pattern 1: `.svelte.ts` module with runes

```ts
// state.svelte.ts
export function createCounter() {
  let count = $state(0)
  let doubled = $derived(count * 2)

  return {
    get count() { return count },
    get doubled() { return doubled },
    increment() { count += 1 }
  }
}
```

### Pattern 2: Context API for subtree state

Use context when state belongs to a subtree such as a form wizard, tabs system, or layout-level state.

### Pattern 3: Store for long-lived app state

Use stores when you need explicit global subscription or library compatibility.

## Common Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Using `$effect` for computed values | Hard-to-debug reactive loops | Use `$derived` |
| Turning every shared state problem into a global store | Unnecessary coupling | Start local, then lift only as needed |
| Rewriting stable stores during migration | Churn without value | Migrate where runes simplify code |
| Hiding callbacks inside giant prop objects | Weak component API | Pass explicit callback props |
| Treating snippets like magic slots | Confusing render flow | Keep snippet names concrete |

## Release Readiness Checklist

- [ ] `$state` is used for mutable local state, not everything
- [ ] `$derived` computations are pure
- [ ] `$effect` blocks are side-effect oriented and cleanup-aware
- [ ] `$props()` defines a clear, typed component API
- [ ] `$bindable` is used only for intentional writable child state
- [ ] Shared state pattern is chosen intentionally: local rune, context, or store
- [ ] Migration choices optimize maintainability, not novelty
