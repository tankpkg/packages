# Vue 3 Composition API

Sources: Vue 3 official documentation (vuejs.org), Evan You (RFC-0040 script setup), Vue 3.4/3.5 release notes, VueUse source patterns

Covers: `<script setup>` syntax, reactive primitives (ref, reactive, computed, watch), lifecycle hooks, composable design patterns, and Vue 3.4+/3.5+ features.

## Script Setup

`<script setup>` is the standard way to write Vue 3 components. It compiles to `setup()` with automatic returns -- every top-level binding is available in the template.

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

function increment() {
  count.value++
}

onMounted(() => {
  console.log('mounted with count:', count.value)
})
</script>

<template>
  <button @click="increment">{{ count }} ({{ doubled }})</button>
</template>
```

### Why Script Setup Is the Standard

| Benefit | Explanation |
|---------|-------------|
| Less boilerplate | No `export default`, no `setup() { return {} }` |
| Better TypeScript inference | Top-level types flow to template without annotation |
| Compile-time optimization | Compiler inlines bindings, avoiding runtime proxy overhead |
| Cleaner imports | Components, directives auto-registered by import |
| IDE support | Volar provides full template type-checking |

### Key Rules

- One `<script setup>` per SFC. Use a separate `<script>` block (without `setup`) only for `inheritAttrs` or named exports.
- Top-level `await` makes the component an async setup component -- wrap parent with `<Suspense>`.
- `defineProps`, `defineEmits`, `defineModel`, `defineExpose`, `defineOptions`, `defineSlots` are compiler macros -- no import needed.

## Reactive Primitives

### ref()

Wraps any value in a reactive container. Access via `.value` in script; auto-unwraps in templates.

```typescript
const name = ref('Alice')     // Ref<string>
const count = ref(0)          // Ref<number>
const user = ref({ id: 1 })   // Ref<{ id: number }>

// Script: use .value
name.value = 'Bob'

// Template: auto-unwraps
// {{ name }} outputs "Bob"
```

Use `ref()` as the default for all state. It works with primitives and objects alike.

### reactive()

Creates a deeply reactive proxy of an object. No `.value` wrapper -- access properties directly.

```typescript
const state = reactive({
  count: 0,
  user: { name: 'Alice' }
})

state.count++           // reactive
state.user.name = 'Bob' // deep reactive
```

| Consideration | ref() | reactive() |
|--------------|-------|------------|
| Primitives | Yes | No (objects only) |
| Reassignment | `count.value = newVal` | Cannot reassign root -- loses reactivity |
| Destructuring | Safe (refs keep reactivity) | Loses reactivity -- use `toRefs()` |
| Template syntax | Auto-unwraps (no `.value`) | Direct property access |
| Recommended for | Default choice, all types | Object state you never reassign |

### computed()

Cached derived state. Re-evaluates only when tracked dependencies change.

```typescript
const firstName = ref('John')
const lastName = ref('Doe')
const fullName = computed(() => `${firstName.value} ${lastName.value}`)

// Writable computed
const fullNameWritable = computed({
  get: () => `${firstName.value} ${lastName.value}`,
  set: (val: string) => {
    const [first, last] = val.split(' ')
    firstName.value = first
    lastName.value = last ?? ''
  }
})
```

Never put side effects inside `computed()`. Use `watch()` or `watchEffect()` instead.

### watch()

Explicit source watching with access to old and new values.

```typescript
const id = ref(1)

// Watch a single ref
watch(id, (newId, oldId) => {
  fetchUser(newId)
})

// Watch a getter
watch(() => route.params.id, (newId) => {
  fetchUser(newId)
})

// Watch multiple sources
watch([firstName, lastName], ([newFirst, newLast]) => {
  saveUser(newFirst, newLast)
})

// Immediate + deep
watch(user, (newUser) => {
  syncProfile(newUser)
}, { immediate: true, deep: true })
```

### watchEffect()

Auto-tracks dependencies. Runs immediately. No old/new value access.

```typescript
watchEffect(() => {
  // Automatically tracks `id.value` and `name.value`
  console.log(`User ${id.value}: ${name.value}`)
})
```

Use `watchEffect` when the callback reads the same sources it reacts to. Use `watch` when the side effect needs old values or should not run immediately.

### watchPostEffect() and watchSyncEffect()

| Timing | Function | When |
|--------|----------|------|
| Pre-render (default) | `watch` / `watchEffect` | Before DOM updates |
| Post-render | `watchPostEffect()` | After DOM updates -- safe to read DOM |
| Synchronous | `watchSyncEffect()` | Before Vue batches updates -- rarely needed |

## Lifecycle Hooks

| Options API | Composition API | When |
|------------|-----------------|------|
| `beforeCreate` / `created` | `<script setup>` body | During setup (no hook needed) |
| `beforeMount` | `onBeforeMount()` | Before initial DOM mount |
| `mounted` | `onMounted()` | After DOM mount -- safe to access `$el` |
| `beforeUpdate` | `onBeforeUpdate()` | Before reactive DOM re-render |
| `updated` | `onUpdated()` | After DOM re-render |
| `beforeUnmount` | `onBeforeUnmount()` | Before teardown -- remove listeners here |
| `unmounted` | `onUnmounted()` | After teardown |
| `activated` | `onActivated()` | `<KeepAlive>` component activated |
| `deactivated` | `onDeactivated()` | `<KeepAlive>` component deactivated |
| `errorCaptured` | `onErrorCaptured()` | Error from descendant component |

Register hooks at the top level of `<script setup>`. They bind to the current component instance automatically.

## Composable Design Patterns

### Naming Convention

Prefix with `use`: `useCounter`, `useFetch`, `useAuth`. Place in `composables/` directory.

### Return Object Pattern

Return a plain object with named refs, computed, and functions. Consumers destructure what they need.

```typescript
// composables/useCounter.ts
export function useCounter(initial = 0) {
  const count = ref(initial)
  const doubled = computed(() => count.value * 2)

  function increment() { count.value++ }
  function reset() { count.value = initial }

  return { count, doubled, increment, reset }
}
```

```vue
<script setup lang="ts">
const { count, increment } = useCounter(10)
</script>
```

### Async Composable Pattern

Return reactive state alongside loading and error refs.

```typescript
export function useUser(id: MaybeRef<number>) {
  const user = ref<User | null>(null)
  const error = ref<Error | null>(null)
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    error.value = null
    try {
      user.value = await api.getUser(toValue(id))
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  watch(() => toValue(id), fetch, { immediate: true })

  return { user, error, loading, refresh: fetch }
}
```

### Composable Rules

| Rule | Reason |
|------|--------|
| Call at top level of `<script setup>` | Hooks bind to current instance |
| Accept `MaybeRef<T>` for reactive inputs | Supports both `ref(val)` and raw `val` via `toValue()` |
| Return refs (not raw values) | Consumers retain reactivity on destructure |
| Clean up side effects | Use `onUnmounted` or `watchEffect` cleanup |
| Keep composables focused | One concern per composable -- compose them together |

### MaybeRef and toValue

Accept flexible inputs with `MaybeRef<T>` (Vue 3.3+) and normalize with `toValue()`:

```typescript
import { toValue, type MaybeRef } from 'vue'

export function useTitle(title: MaybeRef<string>) {
  watchEffect(() => {
    document.title = toValue(title)
  })
}

// Both work:
useTitle('Static Title')
useTitle(ref('Reactive Title'))
useTitle(computed(() => `Page - ${page.value}`))
```

## Vue 3.4+ Features

### defineModel (Stable in 3.4)

Two-way binding without the `modelValue` prop + `update:modelValue` emit boilerplate:

```vue
<!-- Child component -->
<script setup lang="ts">
const model = defineModel<string>({ required: true })
// model is a Ref<string> -- read and write directly
</script>

<template>
  <input v-model="model" />
</template>
```

```vue
<!-- Parent -->
<Child v-model="parentValue" />
```

Named models: `const title = defineModel<string>('title')` maps to `v-model:title`.

### v-bind Shorthand (3.4)

```vue
<!-- Before -->
<img :id="id" :src="src" :alt="alt" />

<!-- After (3.4+) -->
<img :id :src :alt />
```

Same-name shorthand -- attribute name matches variable name.

## Vue 3.5+ Features

### useTemplateRef (3.5)

Type-safe template refs without string matching:

```vue
<script setup lang="ts">
import { useTemplateRef, onMounted } from 'vue'

const inputRef = useTemplateRef<HTMLInputElement>('input')

onMounted(() => {
  inputRef.value?.focus()
})
</script>

<template>
  <input ref="input" />
</template>
```

### Reactive Props Destructure (3.5, stable)

Destructure props with defaults directly -- retains reactivity:

```vue
<script setup lang="ts">
interface Props {
  msg?: string
  count?: number
}

const { msg = 'hello', count = 0 } = defineProps<Props>()
// msg and count are reactive -- no withDefaults needed
</script>
```

### useId (3.5)

Generate unique IDs for accessibility attributes:

```vue
<script setup>
import { useId } from 'vue'
const id = useId()
</script>

<template>
  <label :for="id">Email</label>
  <input :id="id" type="email" />
</template>
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `reactive()` on primitives | TypeError -- reactive needs objects | Use `ref()` for primitives |
| Destructuring `reactive()` | Loses reactivity | Use `toRefs(state)` or stick with `ref()` |
| Reassigning `reactive()` root | `state = newObj` breaks proxy | Use `Object.assign(state, newObj)` or `ref()` |
| Side effects in `computed()` | Unpredictable re-evaluation timing | Move to `watch()` or `watchEffect()` |
| Forgetting `.value` in script | Silent bugs: comparing ref object, not value | Enable Volar for `.value` warnings |
| Composable called conditionally | Hooks may not bind correctly | Always call at top level |
| `watch` without cleanup | Timer/listener leaks | Return cleanup from `watch` callback or use `onUnmounted` |
| Options API mixins in Vue 3 | Name collisions, implicit dependencies | Rewrite as composables |

## Composition API Review Questions

1. Should this state be `ref`, `reactive`, computed, or moved into a composable?
2. Are side effects isolated in `watch`/`watchEffect` instead of leaking into computed values?
3. Does this composable expose a clear API or just move complexity around?
