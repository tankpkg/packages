# Vue TypeScript Patterns

Sources: Vue 3 official documentation (vuejs.org/guide/typescript), Volar documentation, vue-tsc documentation, Vue 3.4/3.5 release notes

Covers: Type-based defineProps/Emits/Model, typed composables, InjectionKey for provide/inject, template ref typing, generic components, vue-tsc configuration, and Volar setup.

## Type-Based Props

### Runtime vs Type-Based Declaration

Vue supports two prop declaration styles. Prefer type-based for TypeScript projects -- it provides full IDE inference without runtime overhead.

```typescript
// Runtime declaration (JavaScript-compatible)
const props = defineProps({
  title: { type: String, required: true },
  count: { type: Number, default: 0 },
  items: { type: Array as PropType<Item[]>, default: () => [] }
})

// Type-based declaration (TypeScript -- preferred)
const props = defineProps<{
  title: string
  count?: number
  items?: Item[]
}>()
```

### Default Values

Use `withDefaults` (Vue 3.3) or reactive destructure (Vue 3.5+):

```typescript
// withDefaults (Vue 3.3+)
interface Props {
  title: string
  count?: number
  items?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  count: 0,
  items: () => []   // factory function for non-primitive defaults
})

// Reactive destructure (Vue 3.5+ -- preferred)
const { title, count = 0, items = [] } = defineProps<Props>()
```

### Complex Prop Types

```typescript
interface User {
  id: number
  name: string
  role: 'admin' | 'user' | 'guest'
}

interface TableProps {
  users: User[]
  sortBy?: keyof User
  onRowClick?: (user: User) => void
}

const props = defineProps<TableProps>()
```

### Props Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| Default arrays/objects shared across instances | Non-factory default | Use factory function: `() => []` |
| Cannot use imported types in runtime declaration | `PropType` requires explicit cast | Switch to type-based declaration |
| `Boolean` prop absent = `false` | Vue special Boolean casting | Document explicitly in component |
| Union types not supported in runtime | No `type: [String, Number]` equivalent | Use type-based `prop?: string \| number` |

## Type-Based Emits

```typescript
// Basic typed emits
const emit = defineEmits<{
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
  (e: 'close'): void
}>()

// Vue 3.3+ shorthand syntax
const emit = defineEmits<{
  update: [value: string]
  delete: [id: number]
  close: []
}>()

// Usage
emit('update', 'new value')  // type-checked
emit('delete', 42)            // type-checked
emit('unknown')               // compile error
```

The 3.3+ tuple syntax is more concise. Use it for new projects.

## defineModel with TypeScript

Two-way binding with full type safety (Vue 3.4+):

```typescript
// Basic model
const modelValue = defineModel<string>({ required: true })

// Named models
const title = defineModel<string>('title')
const count = defineModel<number>('count', { default: 0 })

// With validation
const rating = defineModel<number>({
  required: true,
  validator: (v: number) => v >= 1 && v <= 5
})
```

Parent usage:

```vue
<RatingInput v-model="userRating" />
<FormField v-model:title="formTitle" v-model:count="formCount" />
```

`defineModel` returns a `Ref<T>` -- read and write directly inside the child component.

## Typed Composables

### Explicit Return Types

Always type composable return values for consumer clarity:

```typescript
interface UseCounterReturn {
  count: Readonly<Ref<number>>
  doubled: ComputedRef<number>
  increment: () => void
  reset: () => void
}

export function useCounter(initial = 0): UseCounterReturn {
  const count = ref(initial)
  const doubled = computed(() => count.value * 2)

  function increment() { count.value++ }
  function reset() { count.value = initial }

  return { count: readonly(count), doubled, increment, reset }
}
```

### Generic Composables

Accept type parameters for reusable data composables:

```typescript
export function useList<T>(initialItems: T[] = []) {
  const items = ref<T[]>(initialItems) as Ref<T[]>

  function add(item: T) { items.value.push(item) }
  function remove(index: number) { items.value.splice(index, 1) }
  function clear() { items.value = [] }

  return { items: readonly(items), add, remove, clear }
}

// Usage infers T from argument
const { items, add } = useList<User>()
add({ id: 1, name: 'Alice' })  // type-checked
```

### MaybeRef and MaybeRefOrGetter

Accept flexible inputs in composables:

```typescript
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useTitle(title: MaybeRefOrGetter<string>) {
  watchEffect(() => {
    document.title = toValue(title)  // unwraps ref, calls getter, or returns raw
  })
}

// All valid:
useTitle('Static')
useTitle(ref('Reactive'))
useTitle(() => `Page ${page.value}`)
```

| Type | Accepts | Use When |
|------|---------|----------|
| `MaybeRef<T>` | `T \| Ref<T>` | Input may be reactive or static |
| `MaybeRefOrGetter<T>` | `T \| Ref<T> \| (() => T)` | Also accept computed-like getters |

## Typed Provide / Inject

### InjectionKey

Use `InjectionKey<T>` to sync types between provider and consumer:

```typescript
// keys.ts
import type { InjectionKey, Ref } from 'vue'

export interface UserContext {
  user: Ref<User | null>
  login: (credentials: Credentials) => Promise<void>
  logout: () => void
}

export const UserKey: InjectionKey<UserContext> = Symbol('user')
```

```vue
<!-- Provider -->
<script setup lang="ts">
import { provide, ref } from 'vue'
import { UserKey, type UserContext } from './keys'

const user = ref<User | null>(null)

const context: UserContext = {
  user,
  login: async (creds) => { /* ... */ },
  logout: () => { user.value = null }
}

provide(UserKey, context)
</script>
```

```vue
<!-- Consumer -->
<script setup lang="ts">
import { inject } from 'vue'
import { UserKey } from './keys'

const userCtx = inject(UserKey)
// Type: UserContext | undefined

// With required assertion
const userCtx = inject(UserKey)!
// or provide a default
const userCtx = inject(UserKey, { user: ref(null), login: async () => {}, logout: () => {} })
</script>
```

### Strict Inject Helper

Create a helper that throws if injection is missing:

```typescript
export function injectStrict<T>(key: InjectionKey<T>, fallback?: T): T {
  const resolved = inject(key, fallback)
  if (resolved === undefined) {
    throw new Error(`Could not resolve injection key: ${String(key)}`)
  }
  return resolved
}
```

## Template Ref Typing

### DOM Element Refs

```vue
<script setup lang="ts">
import { useTemplateRef, onMounted } from 'vue'

// Vue 3.5+ (preferred)
const inputEl = useTemplateRef<HTMLInputElement>('input')

// Pre-3.5 fallback
const inputEl = ref<HTMLInputElement | null>(null)

onMounted(() => {
  inputEl.value?.focus()
})
</script>

<template>
  <input ref="input" />
</template>
```

### Component Refs

Access child component's exposed API:

```vue
<script setup lang="ts">
import { useTemplateRef } from 'vue'
import MyForm from './MyForm.vue'

const formRef = useTemplateRef<InstanceType<typeof MyForm>>('form')

function submitFromParent() {
  formRef.value?.validate()
  formRef.value?.submit()
}
</script>

<template>
  <MyForm ref="form" />
</template>
```

The child must `defineExpose` the methods:

```vue
<!-- MyForm.vue -->
<script setup lang="ts">
function validate() { /* ... */ }
function submit() { /* ... */ }
defineExpose({ validate, submit })
</script>
```

## Generic Components (Vue 3.3+)

Define type parameters on components using the `generic` attribute:

```vue
<script setup lang="ts" generic="T extends { id: number }">
defineProps<{
  items: T[]
  selected?: T
}>()

defineEmits<{
  select: [item: T]
}>()
</script>

<template>
  <ul>
    <li v-for="item in items" :key="item.id" @click="$emit('select', item)">
      <slot :item="item" />
    </li>
  </ul>
</template>
```

Consumer gets full inference:

```vue
<GenericList :items="users" @select="handleUser">
  <template #default="{ item }">
    <!-- item is typed as User -->
    {{ item.name }}
  </template>
</GenericList>
```

## defineSlots (Vue 3.3+)

Type slot props for consumers:

```typescript
const slots = defineSlots<{
  default: (props: { item: User; index: number }) => any
  header: (props: { title: string }) => any
  empty: () => any
}>()
```

## vue-tsc Configuration

### Setup

```bash
npm install -D vue-tsc typescript
```

Add to `package.json`:

```json
{
  "scripts": {
    "type-check": "vue-tsc --noEmit",
    "type-check:watch": "vue-tsc --noEmit --watch"
  }
}
```

### tsconfig.json for Vue

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "skipLibCheck": true,
    "noEmit": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "exclude": ["node_modules"]
}
```

### Nuxt TypeScript

Nuxt auto-generates `.nuxt/tsconfig.json`. Extend it:

```json
{
  "extends": "./.nuxt/tsconfig.json",
  "compilerOptions": {
    "strict": true
  }
}
```

Run `nuxi typecheck` instead of `vue-tsc` directly in Nuxt projects.

## Volar Setup

Install the **Vue - Official** extension (previously Volar). Disable **Vetur** if present -- they conflict. For non-Nuxt projects, add an `env.d.ts` declaring `*.vue` modules. Nuxt generates this automatically.

Run `nuxi typecheck` in Nuxt projects instead of `vue-tsc` directly.

## Common TypeScript Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using `as any` on props | Disables type checking | Define proper interface |
| Not typing emit payloads | Emits accept any arguments | Use type-based `defineEmits` |
| String keys for provide/inject | No type connection | Use `InjectionKey<T>` |
| `ref<T>()` without initial value | `Ref<T \| undefined>` | Provide initial or accept `undefined` |
| Ignoring `vue-tsc` in CI | Template type errors ship | Add `vue-tsc --noEmit` to CI pipeline |
| Using `PropType` with type-based props | Redundant and conflicting | Pick one approach per component |
| Not exposing child methods | Parent ref has empty type | Add `defineExpose({ method })` |
