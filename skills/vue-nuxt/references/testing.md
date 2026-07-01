# Vue and Nuxt Testing

Sources: Vitest documentation (vitest.dev), @vue/test-utils documentation (test-utils.vuejs.org), @nuxt/test-utils documentation (nuxt.com/docs/getting-started/testing), Vue Testing Handbook, Markus Oberlehner (testing Vue composables)

Covers: Vitest setup, @vue/test-utils patterns, @nuxt/test-utils for integration testing, testing composables, testing Pinia stores, MSW mocking, and testing best practices.

## Vitest Setup

### Vue Project

```bash
npm install -D vitest @vue/test-utils happy-dom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',  // or 'jsdom'
    globals: true,
    include: ['**/*.{test,spec}.{ts,tsx}']
  }
})
```

### Nuxt Project

```bash
npm install -D @nuxt/test-utils vitest
```

```typescript
// vitest.config.ts
import { defineVitestConfig } from '@nuxt/test-utils/config'

export default defineVitestConfig({
  test: {
    environment: 'nuxt',
    environmentOptions: {
      nuxt: {
        domEnvironment: 'happy-dom'
      }
    }
  }
})
```

## @vue/test-utils Basics

### Mounting Components

```typescript
import { mount, shallowMount } from '@vue/test-utils'
import UserCard from './UserCard.vue'

// Full mount -- renders child components
const wrapper = mount(UserCard, {
  props: {
    user: { id: 1, name: 'Alice', role: 'admin' }
  }
})

// Shallow mount -- stubs child components
const wrapper = shallowMount(UserCard, {
  props: {
    user: { id: 1, name: 'Alice', role: 'admin' }
  }
})
```

### Mount vs ShallowMount

| Method | Child Components | Use When |
|--------|-----------------|----------|
| `mount` | Fully rendered | Testing integration between parent and children |
| `shallowMount` | Stubbed to `<component-stub>` | Testing component in isolation |

Default to `mount`. Use `shallowMount` when child components have complex setup (API calls, heavy rendering) that is not relevant to the test.

### Common Assertions

```typescript
// Text content
expect(wrapper.text()).toContain('Alice')
expect(wrapper.find('h1').text()).toBe('User Profile')

// HTML
expect(wrapper.html()).toContain('<span class="badge">')

// Element existence
expect(wrapper.find('.error-message').exists()).toBe(false)
expect(wrapper.findComponent(ChildComponent).exists()).toBe(true)

// Attributes and classes
expect(wrapper.find('button').attributes('disabled')).toBeDefined()
expect(wrapper.find('div').classes()).toContain('active')

// Emitted events
expect(wrapper.emitted('update')).toBeTruthy()
expect(wrapper.emitted('update')![0]).toEqual(['new value'])

// Props (on child components)
expect(wrapper.findComponent(Badge).props('type')).toBe('success')
```

### User Interactions

```typescript
// Click
await wrapper.find('button').trigger('click')

// Input
await wrapper.find('input').setValue('new text')

// Form submit
await wrapper.find('form').trigger('submit.prevent')

// Keyboard
await wrapper.find('input').trigger('keyup.enter')

// Custom event
await wrapper.findComponent(Modal).vm.$emit('close')
```

Always `await` trigger calls -- Vue batches DOM updates asynchronously.

### Providing Dependencies

```typescript
const wrapper = mount(UserDashboard, {
  global: {
    plugins: [createTestingPinia()],  // Pinia
    stubs: {
      NuxtLink: true,                  // Stub Nuxt components
      teleport: true                    // Stub teleport
    },
    provide: {
      [ThemeKey as symbol]: { isDark: ref(false) }
    },
    mocks: {
      $route: { params: { id: '1' } },
      $router: { push: vi.fn() }
    }
  }
})
```

## Testing Composables

### Direct Testing (No Component)

For composables that do not require a component instance:

```typescript
import { useCounter } from '~/composables/useCounter'

describe('useCounter', () => {
  it('increments count', () => {
    const { count, increment } = useCounter(0)

    expect(count.value).toBe(0)
    increment()
    expect(count.value).toBe(1)
  })

  it('computes doubled value', () => {
    const { count, doubled, increment } = useCounter(5)

    expect(doubled.value).toBe(10)
    increment()
    expect(doubled.value).toBe(12)
  })
})
```

### withSetup Helper (Component-Bound Composables)

For composables that use lifecycle hooks, inject, or other component-bound APIs:

```typescript
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'

function withSetup<T>(composable: () => T) {
  let result: T
  const TestComponent = defineComponent({
    setup() {
      result = composable()
      return () => null  // render nothing
    }
  })
  const wrapper = mount(TestComponent)
  return { result: result!, wrapper }
}

// Usage
describe('useAuth', () => {
  it('provides authentication state', () => {
    const { result } = withSetup(() => useAuth())

    expect(result.isAuthenticated.value).toBe(false)
    expect(result.user.value).toBeNull()
  })
})
```

### Testing Async Composables

```typescript
import { flushPromises } from '@vue/test-utils'

describe('useUser', () => {
  it('fetches user data', async () => {
    // Mock the API
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      json: () => Promise.resolve({ id: 1, name: 'Alice' })
    } as Response)

    const { result } = withSetup(() => useUser(ref(1)))

    expect(result.loading.value).toBe(true)

    await flushPromises()

    expect(result.loading.value).toBe(false)
    expect(result.user.value).toEqual({ id: 1, name: 'Alice' })
    expect(result.error.value).toBeNull()
  })
})
```

## Testing Pinia Stores

### Setup with createTestingPinia

```bash
npm install -D @pinia/testing
```

```typescript
import { setActivePinia, createPinia } from 'pinia'
import { createTestingPinia } from '@pinia/testing'
import { useCounterStore } from '~/stores/counter'

describe('Counter Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('increments count', () => {
    const store = useCounterStore()

    expect(store.count).toBe(0)
    store.increment()
    expect(store.count).toBe(1)
  })

  it('computes doubleCount', () => {
    const store = useCounterStore()
    store.count = 5

    expect(store.doubleCount).toBe(10)
  })
})
```

### Testing with Mocked Actions

```typescript
const wrapper = mount(CounterComponent, {
  global: {
    plugins: [
      createTestingPinia({
        initialState: {
          counter: { count: 10 }
        },
        stubActions: false  // false = real actions; true = vi.fn() stubs
      })
    ]
  }
})

const store = useCounterStore()

// With stubActions: true (default)
expect(store.increment).toHaveBeenCalledTimes(0)
await wrapper.find('button').trigger('click')
expect(store.increment).toHaveBeenCalledTimes(1)

// State still tracks if stubActions: false
expect(store.count).toBe(11)
```

### Testing Store Actions with API Calls

```typescript
describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('logs in successfully', async () => {
    vi.spyOn(global, '$fetch' as any).mockResolvedValueOnce({
      token: 'abc123',
      user: { id: 1, name: 'Alice' }
    })

    const store = useAuthStore()
    await store.login({ email: 'alice@test.com', password: 'secret' })

    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.name).toBe('Alice')
  })
})
```

## @nuxt/test-utils

For Nuxt-aware integration tests that need auto-imports, Nuxt plugins, and server routes.

### Setup

```typescript
// tests/app.nuxt.spec.ts
import { describe, it, expect } from 'vitest'
import { setup, $fetch, createPage } from '@nuxt/test-utils/e2e'

describe('App Integration', async () => {
  await setup({
    // Spins up a Nuxt dev server for tests
  })

  it('renders homepage', async () => {
    const html = await $fetch('/')
    expect(html).toContain('Welcome')
  })
})
```

### Testing Nuxt Components with Nuxt Context

```typescript
import { mountSuspended, renderSuspended } from '@nuxt/test-utils/runtime'
import UserPage from '~/pages/users/[id].vue'

describe('UserPage', () => {
  it('renders user name', async () => {
    const component = await mountSuspended(UserPage, {
      route: '/users/1'
    })

    expect(component.text()).toContain('User Profile')
  })
})
```

`mountSuspended` handles `<Suspense>` boundaries and async setup automatically.

### Testing Server Routes

```typescript
import { setup, $fetch } from '@nuxt/test-utils/e2e'

describe('API Routes', async () => {
  await setup({})

  it('GET /api/users returns users', async () => {
    const users = await $fetch('/api/users')
    expect(users).toBeInstanceOf(Array)
    expect(users[0]).toHaveProperty('id')
  })

  it('POST /api/users creates user', async () => {
    const user = await $fetch('/api/users', {
      method: 'POST',
      body: { name: 'Alice', email: 'alice@test.com' }
    })
    expect(user.name).toBe('Alice')
  })

  it('GET /api/users/999 returns 404', async () => {
    const res = await $fetch.raw('/api/users/999').catch(e => e.response)
    expect(res.status).toBe(404)
  })
})
```

## MSW (Mock Service Worker)

Mock external APIs without changing application code (`npm install -D msw`):

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('https://api.example.com/users', () => {
    return HttpResponse.json([{ id: 1, name: 'Alice' }])
  }),
  http.post('https://api.example.com/users', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: 3, ...body }, { status: 201 })
  })
]

// tests/setup.ts
import { setupServer } from 'msw/node'
import { handlers } from './mocks/handlers'

export const server = setupServer(...handlers)
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

Override per test with `server.use(http.get(..., () => new HttpResponse(null, { status: 500 })))`.

## Testing Patterns

### What to Test

| Test Target | Approach | Priority |
|------------|----------|----------|
| Composables | Direct call or `withSetup` | High -- core logic |
| Pinia stores | `createTestingPinia` + real actions | High -- state |
| Components (props/emits) | `mount` + assertions | Medium -- contracts |
| Server routes | `@nuxt/test-utils` `$fetch` | Medium -- API |
| Pages with SSR data | `mountSuspended` | Low -- integration |

Co-locate test files with source: `UserCard.vue` + `UserCard.test.ts`. Place E2E tests in `tests/e2e/`.

## Common Testing Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Not awaiting `trigger()` | Assertions run before DOM update | Always `await trigger()` |
| Testing implementation, not behavior | Brittle tests break on refactor | Test what user sees and does |
| Mocking too much | Test passes but feature broken | Mock only external boundaries |
| No `flushPromises` after async | Async state not settled | `await flushPromises()` after async composable calls |
| Missing `setActivePinia` in store tests | "getActivePinia was called with no active Pinia" | Add `beforeEach(() => setActivePinia(createPinia()))` |
| Testing `shallowMount` snapshots | Stubs change across versions | Use `mount` or assert specific elements |
| Forgetting to reset MSW handlers | Handler leak between tests | `afterEach(() => server.resetHandlers())` |
| Not testing error states | Errors crash in production | Test loading, error, and empty states |
