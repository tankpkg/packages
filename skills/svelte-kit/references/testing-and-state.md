# Testing and State

Sources: Svelte official documentation, SvelteKit official documentation, Vitest documentation, Playwright documentation, Testing Library documentation, community Svelte production patterns from 2024-2026

Covers: Vitest unit testing, component testing, Playwright end-to-end testing, mocking load data, context API, shared state strategies, route-aware state patterns, and when to choose runes, context, or stores.

## Testing Strategy Pyramid

SvelteKit apps benefit from three main layers of testing.

| Layer | Tool | Best for |
|------|------|----------|
| Unit | Vitest | pure helpers, derived logic, state utilities |
| Component | Vitest + Testing Library | rendering, interaction, accessibility |
| End-to-end | Playwright | routes, forms, auth, navigation, SSR integration |

Do not push every UI check into Playwright. Use the cheapest test level that catches the risk.

## Vitest for Pure Logic

Use Vitest for utility functions, parsers, data transforms, and state modules with minimal DOM involvement.

```ts
import { describe, expect, it } from 'vitest'
import { slugify } from './slugify'

describe('slugify', () => {
  it('lowercases and joins words', () => {
    expect(slugify('Hello World')).toBe('hello-world')
  })
})
```

### Good unit-test targets

| Target | Why |
|-------|-----|
| formatting helpers | deterministic outputs |
| schema validation helpers | edge-case heavy |
| derived business rules | easy to isolate |
| URL/state conversion utilities | navigation correctness |

## Component Testing

Use Testing Library for component behavior rather than implementation details.

```ts
import { render, screen } from '@testing-library/svelte'
import userEvent from '@testing-library/user-event'
import Counter from './Counter.svelte'

it('increments count', async () => {
  const user = userEvent.setup()
  render(Counter)
  await user.click(screen.getByRole('button', { name: /increment/i }))
  expect(screen.getByText('1')).toBeInTheDocument()
})
```

### Component test rules

| Rule | Why |
|-----|-----|
| Prefer `getByRole` and accessible queries | More user-realistic and resilient |
| Assert visible behavior | Avoid coupling to internal structure |
| Avoid testing rune internals directly | Test rendered outcomes |
| Mock only true boundaries | Keep confidence real |

## What to Mock in Component Tests

| Dependency | Mock? |
|-----------|-------|
| Browser APIs not available in jsdom | Yes |
| Network requests | Usually yes at component level |
| Child components with complex unrelated logic | Sometimes |
| SvelteKit page data | Yes, inject simplified data |

Do not mock everything. If the component behavior depends on the child, render the child.

## Testing Components with Props

```ts
render(ProfileCard, {
  props: {
    user: { id: '1', name: 'Ada' }
  }
})
```

### Prop test focus

| Question | Assert |
|---------|--------|
| Does it render the right data? | visible text |
| Does callback prop fire? | event/callback invocation |
| Does fallback UI appear? | empty/loading/error state |

## Testing Forms

Forms are a high-value testing target because they combine state, validation, and server integration.

### Component-level form tests

| Check | Example |
|------|---------|
| required fields render | labels and controls exist |
| client-side hints show | validation text |
| disabled state while pending | submit button disabled |
| callback or action trigger | event observed |

### End-to-end form tests

| Check | Example |
|------|---------|
| successful submit redirects or updates UI | form action success |
| invalid data preserves values and shows errors | server-side validation |
| progressive enhancement still works | JS on/off path if critical |

## Playwright for Route-Level Behavior

Use Playwright for the seams where routing, SSR, actions, cookies, and browser behavior meet.

### Best Playwright targets

| Flow | Why |
|-----|-----|
| login/logout | session + redirect behavior |
| form actions | real request/response lifecycle |
| navigation + data reload | SvelteKit router behavior |
| protected routes | server and client auth gates |
| upload/download flow | browser integration |

### Minimal Playwright example

```ts
test('user can create a post', async ({ page }) => {
  await page.goto('/posts/new')
  await page.getByLabel('Title').fill('My Post')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('Post created')).toBeVisible()
})
```

## Route-Aware Testing

Some state behaves differently on first SSR render vs client navigation.

| Risk | Test at |
|-----|---------|
| `load` behavior and redirects | Playwright |
| page option effects (`ssr`, `csr`, `prerender`) | Playwright or route integration |
| context-only component logic | component test |
| pure state utility | Vitest |

If the bug depends on navigation boundaries, use Playwright.

## State Strategy: Local Rune, Context, or Store

Choose state mechanisms by scope.

| Scope | Best tool |
|------|-----------|
| Single component | local rune |
| Subtree or layout-owned feature | context + rune |
| App-wide, cross-tree, or external subscriber compatibility | store |

### Local rune example

Use for tabs, toggles, simple forms, and local component state.

### Context pattern

Use context when a parent owns capability/state for descendants.

```ts
setContext('wizard', wizardState)
const wizard = getContext<WizardState>('wizard')
```

### Store pattern

Use stores when you need an explicit subscribable contract.

| Good store use case | Example |
|--------------------|---------|
| auth session used in many unrelated components | top-level app state |
| websocket-driven live data feed | explicit subscription |
| legacy Svelte 4 app migrating gradually | compatibility |

## Shared State Across Routes

Route changes can tear down components. Put state at the right level.

| Need | Put state in |
|-----|--------------|
| Persist across pages in a section | layout component / layout context |
| Persist across whole app session | root layout or store |
| Reset on page navigation | page component |

### Example

If a dashboard sidebar should preserve expanded groups while navigating between child pages, the state belongs in the dashboard layout, not each page.

## Context API Guidelines

| Rule | Why |
|-----|-----|
| Use context for ownership within a tree | aligns with component hierarchy |
| Keep keys explicit and typed | avoids collisions |
| Do not hide global state in context by default | makes access paths unclear |

Context is powerful but should remain architectural, not magical.

## Mocking Load Data

When testing page components in isolation, pass representative `data` props.

```ts
render(PageComponent, {
  props: {
    data: {
      posts: [{ id: '1', title: 'Hello' }]
    }
  }
})
```

### Load-data test rules

1. Mock realistic shapes
2. Include empty/error/loading-like cases where UI varies
3. Do not over-mock framework behavior that you intend to verify in Playwright

## Testing Error and Empty States

| State | Why it matters |
|------|----------------|
| Empty list | Common production path |
| Validation error | UX correctness |
| Not found / permission denied | route behavior and messaging |
| Slow network fallback | perceived performance |

If your page only passes tests in the happy path, it is under-tested.

## Accessibility Testing Basics

Component and E2E tests should assert accessible UI when practical.

| Practice | Example |
|---------|---------|
| Query by role | buttons, headings, dialogs |
| Assert labels | form controls |
| Focus tests | keyboard flows in dialogs/forms |
| Integrate axe or similar in CI | smoke-level a11y coverage |

## Common Testing Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Snapshot-heavy component tests | brittle, low-signal | assert specific behavior |
| Testing internal rune variables | couples to implementation | assert DOM/result |
| Overusing Playwright for tiny logic checks | slow feedback | move to unit/component tests |
| Keeping global singleton state across tests | flaky bleed-through | reset state between tests |
| Assuming SSR and client navigation behave the same | misses real bugs | test both where relevant |

## Release Readiness Checklist

- [ ] Pure helpers have Vitest coverage
- [ ] Important UI components are tested by behavior, not internals
- [ ] Critical route flows have Playwright coverage
- [ ] State scope matches ownership: local, layout/context, or store
- [ ] Shared state survives or resets on navigation intentionally
- [ ] Error, empty, and validation states are tested alongside happy paths
- [ ] Accessibility-sensitive flows use semantic assertions
