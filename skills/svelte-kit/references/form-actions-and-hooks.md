# Form Actions and Hooks

Sources: SvelteKit official documentation (form actions, progressive enhancement, hooks, server endpoints), Svelte official documentation, adapter and community production guidance from 2024-2026

Covers: default and named form actions, progressive enhancement with `use:enhance`, validation patterns, file uploads, hooks (`handle`, `handleFetch`, `handleError`), request lifecycle customization, and `+server` endpoint patterns in SvelteKit.

## Form Actions Are the Default Mutation Primitive

SvelteKit form actions let you handle writes on the server while preserving normal HTML form behavior.

| Feature | Why it matters |
|--------|----------------|
| Works without JavaScript | Progressive enhancement by default |
| Server-native mutation model | Keep secrets and writes server-side |
| Validation-friendly | Return structured errors with `fail()` |
| Tight route coupling | Mutation logic stays near the page |

If a mutation is driven by a form, start with actions before inventing a fetch-heavy API workflow.

## Default Action Pattern

```ts
// +page.server.ts
import { fail } from '@sveltejs/kit'

export const actions = {
  default: async ({ request, locals }) => {
    const data = await request.formData()
    const email = String(data.get('email') ?? '')

    if (!email) {
      return fail(400, {
        errors: { email: 'Email is required' },
        values: { email }
      })
    }

    await locals.db.user.create({ data: { email } })

    return { success: true }
  }
}
```

The paired form can stay plain HTML:

```svelte
<form method="POST">
  <input name="email" value={form?.values?.email ?? ''} />
  {#if form?.errors?.email}
    <p>{form.errors.email}</p>
  {/if}
  <button type="submit">Save</button>
</form>
```

## Named Actions

Use named actions when one page hosts multiple related mutations.

```ts
export const actions = {
  saveDraft: async (event) => {
    // ...
  },
  publish: async (event) => {
    // ...
  }
}
```

### When named actions help

| Situation | Why |
|----------|-----|
| Edit page with draft and publish buttons | Multiple clear mutations |
| Settings page with separate forms | Avoid giant monolithic action |
| Admin dashboard with row-level actions | Keeps intent explicit |

### When not to use them

| Anti-pattern | Better move |
|-------------|-------------|
| 10 unrelated actions on one page | Split the page or endpoint |
| Actions chosen via hidden input switches | Prefer named actions |
| Pure JSON API called by many consumers | Use `+server` endpoint |

## Validation Patterns

Validation belongs on the server even if you add client-side hints.

### Return validation failures with `fail`

| Status | Use for |
|-------|---------|
| 400 | Invalid input or malformed request |
| 401 | User must authenticate |
| 403 | User is authenticated but forbidden |
| 404 | Target resource missing |
| 409 | Conflict / already exists |

### Recommended action response shape

```ts
return fail(400, {
  errors: {
    title: 'Title is required'
  },
  values: {
    title,
    body
  }
})
```

Keep both **errors** and **values** so the form can re-render without losing user input.

## Schema Validation Strategy

| Need | Pattern |
|-----|---------|
| Small forms | inline checks in action |
| Medium/large forms | Zod or Valibot schema in server module |
| Shared validation between API and form | central schema file |

### Example with Zod

```ts
const schema = z.object({
  title: z.string().min(1),
  email: z.string().email()
})

export const actions = {
  default: async ({ request }) => {
    const raw = Object.fromEntries(await request.formData())
    const parsed = schema.safeParse(raw)

    if (!parsed.success) {
      return fail(400, {
        errors: parsed.error.flatten().fieldErrors,
        values: raw
      })
    }

    return { success: true }
  }
}
```

## Progressive Enhancement with `use:enhance`

`use:enhance` upgrades the form to client-side submission while preserving the server action contract.

```svelte
<script>
  import { enhance } from '$app/forms'
</script>

<form method="POST" use:enhance>
  <!-- fields -->
</form>
```

### What enhancement gives you

| Capability | Benefit |
|-----------|---------|
| No full page reload | Better UX |
| Action result still wired to page form state | Keep server contract |
| Hooks into pending/success/error states | Better form feedback |

### When to add it

| Situation | Add `use:enhance`? |
|----------|--------------------|
| Simple content form | Yes |
| File upload with progress | Usually yes, with custom logic |
| Page should reload normally after submit | Optional |
| Heavily JS-driven custom interaction | Maybe use endpoint + fetch instead |

## Custom `enhance` Behavior

You can customize pending and result handling.

```svelte
<form
  method="POST"
  use:enhance={({ formData, cancel, submitter }) => {
    saving = true

    return async ({ result, update }) => {
      saving = false
      await update()
      if (result.type === 'success') toast('Saved')
    }
  }}
>
```

### Good use cases for custom enhance

| Use case | Example |
|---------|---------|
| Pending spinner | disable submit button |
| Toast notifications | show success/failure messages |
| Optimistic UI | update visible list immediately |
| Multi-submit controls | inspect `submitter` |

## Multiple Submit Buttons

Named actions pair well with multiple submit buttons.

```svelte
<form method="POST">
  <button formaction="?/saveDraft">Save draft</button>
  <button formaction="?/publish">Publish</button>
</form>
```

This is clearer than branching inside a single default action.

## Redirect Patterns

Use redirects after successful mutations that should move the user elsewhere.

```ts
import { redirect } from '@sveltejs/kit'

throw redirect(303, `/posts/${slug}`)
```

### Status code guidance

| Code | Use |
|-----|-----|
| 303 | POST/PUT action success redirect |
| 302 | temporary redirect when semantics are looser |
| 307/308 | preserve method/body exactly |

For form actions, `303` is the common post-success choice.

## File Upload Actions

Actions can receive files through `FormData`.

### Checklist

1. Validate file presence
2. Validate size and MIME type on server
3. Stream or upload promptly
4. Avoid buffering giant files unnecessarily

### Example outline

| Concern | Pattern |
|--------|---------|
| Avatar upload | use `formData.get('avatar')` |
| Type validation | check `file.type` |
| Size validation | check `file.size` |
| Storage | pipe to S3/R2/local storage service |

For heavy upload workflows with progress bars, a dedicated `+server` endpoint may be a better fit.

## When to Use `+server.ts` Instead of Actions

Actions are page-coupled. Endpoints are more general.

| Use actions when | Use `+server.ts` when |
|------------------|------------------------|
| Mutation is tied to a page form | API must serve many consumers |
| Want automatic form state wiring | Need JSON-first protocol |
| Want progressive enhancement | Need webhook or external integration |
| User interaction is HTML-form shaped | Response is binary, stream, or custom API |

## `+server.ts` Basics

```ts
export async function POST({ request, locals }) {
  const body = await request.json()
  const created = await locals.db.item.create({ data: body })
  return new Response(JSON.stringify(created), {
    headers: { 'content-type': 'application/json' }
  })
}
```

### Endpoint guidance

| Concern | Recommendation |
|--------|----------------|
| Public API | validate body and auth explicitly |
| Internal app endpoint | still validate, do not trust client |
| Webhook | verify signature before processing |
| Binary response | use `Response` with correct headers |

## `handle` Hook

`handle` runs around every request and is the right place for request-wide server concerns.

### Common `handle` responsibilities

| Responsibility | Why |
|---------------|-----|
| Populate `event.locals` | auth/session/db helpers |
| Enforce global auth gates | shared route protection |
| Add tracing/request metadata | request lifecycle control |
| Set headers | security/caching defaults |

### Example

```ts
export async function handle({ event, resolve }) {
  event.locals.user = await getUserFromCookie(event.cookies)
  return resolve(event)
}
```

Keep it thin. Do not pile every feature concern into one giant hook.

## `handleFetch`

Use `handleFetch` to intercept server-side fetches.

| Good use case | Example |
|--------------|---------|
| Inject auth headers | internal service token |
| Rewrite internal URLs | service mesh or staging routing |
| Shared tracing headers | correlation IDs |

Avoid hiding business logic in fetch interception.

## `handleError`

`handleError` is for unexpected failures.

| Use for | Example |
|--------|---------|
| Logging production exceptions | Sentry, Rollbar, console/error sink |
| Sanitizing returned messages | do not leak stack details |
| Adding correlation IDs | link UI errors to logs |

Do not use `handleError` for expected validation failures — those belong in actions or endpoints.

## Hook Design Rules

| Rule | Why |
|-----|-----|
| Keep hooks cross-cutting | Prevent feature sprawl |
| Put feature-specific auth in route/server logic when possible | Easier reasoning |
| Avoid expensive DB calls in every request if not needed | Protect latency |
| Populate `locals` with useful, minimal request context | Cleaner downstream code |

## Cookies and Sessions

Actions and hooks often work together around cookies.

### Rules

1. Set cookies server-side in actions/endpoints/hooks
2. Use secure defaults (`httpOnly`, `sameSite`, `secure` in production)
3. Derive `locals.user` from cookies in `handle`

## Common Form/Hook Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Using fetch API for every form by default | Lose native form and action benefits | Start with actions |
| Returning raw validation library objects | Hard-to-render UI | flatten to `errors` + `values` |
| Doing mutation in `load` | Wrong lifecycle | move to action or endpoint |
| Putting per-route logic in `handle` | Hook becomes god function | keep route concerns near route |
| Using actions for cross-client public API | Tight page coupling | use `+server.ts` |

## Release Readiness Checklist

- [ ] Form mutations use actions unless an endpoint is clearly better
- [ ] Validation errors return stable `fail()` payloads with values preserved
- [ ] `use:enhance` is added only where UX benefits justify it
- [ ] File uploads validate type and size on server
- [ ] `handle` populates `locals` cleanly without becoming feature soup
- [ ] `handleFetch` and `handleError` are used only for genuine cross-cutting concerns
- [ ] Endpoint vs action choice is intentional per mutation surface
