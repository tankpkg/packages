# Validation and OpenAPI

Sources: Hono official documentation (hono.dev, 2024-2026), @hono/zod-validator docs, @hono/zod-openapi docs, Zod documentation (zod.dev), Standard Schema specification (standardschema.dev)

Covers: manual validator, Zod integration, Valibot and ArkType via Standard Schema, @hono/zod-openapi for OpenAPI spec generation, validation targets, error customization, and Swagger UI setup.

## Validation Targets

Hono validates six request targets:

| Target | Source | Access |
|--------|--------|--------|
| `json` | Request body (application/json) | `c.req.valid('json')` |
| `form` | Request body (multipart/form-data, x-www-form-urlencoded) | `c.req.valid('form')` |
| `query` | URL query parameters | `c.req.valid('query')` |
| `param` | URL path parameters | `c.req.valid('param')` |
| `header` | HTTP headers | `c.req.valid('header')` |
| `cookie` | Cookies | `c.req.valid('cookie')` |

## Manual Validator

Use `validator()` from `hono/validator` without external dependencies:

```typescript
import { validator } from 'hono/validator'

app.post(
  '/posts',
  validator('json', (value, c) => {
    const { title, body } = value
    if (!title || typeof title !== 'string') {
      return c.json({ error: 'title is required' }, 400)
    }
    if (!body || typeof body !== 'string') {
      return c.json({ error: 'body is required' }, 400)
    }
    return { title, body } // Return validated data
  }),
  (c) => {
    const { title, body } = c.req.valid('json')
    return c.json({ title, body }, 201)
  }
)
```

Returning a `Response` from the validator short-circuits the request. Returning data makes it available via `c.req.valid()`.

## Multiple Validators

Chain validators for different targets on the same route:

```typescript
app.post(
  '/posts/:id',
  validator('param', (value, c) => {
    const id = Number(value.id)
    if (isNaN(id)) return c.json({ error: 'Invalid ID' }, 400)
    return { id }
  }),
  validator('query', (value, c) => {
    return { page: Number(value.page) || 1 }
  }),
  validator('json', (value, c) => {
    if (!value.title) return c.json({ error: 'title required' }, 400)
    return { title: value.title as string }
  }),
  (c) => {
    const { id } = c.req.valid('param')
    const { page } = c.req.valid('query')
    const { title } = c.req.valid('json')
    return c.json({ id, page, title })
  }
)
```

## Zod Validator Middleware

Install `@hono/zod-validator` for seamless Zod integration:

```bash
npm i zod @hono/zod-validator
```

```typescript
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
  tags: z.array(z.string()).optional(),
})

app.post(
  '/posts',
  zValidator('json', createPostSchema),
  (c) => {
    const data = c.req.valid('json')
    // data is typed: { title: string; body: string; tags?: string[] }
    return c.json({ message: 'Created', data }, 201)
  }
)
```

### Custom Error Handler

Override the default 400 response on validation failure:

```typescript
app.post(
  '/posts',
  zValidator('json', createPostSchema, (result, c) => {
    if (!result.success) {
      return c.json(
        {
          error: 'Validation failed',
          issues: result.error.issues.map((i) => ({
            path: i.path.join('.'),
            message: i.message,
          })),
        },
        422
      )
    }
  }),
  (c) => {
    const data = c.req.valid('json')
    return c.json(data, 201)
  }
)
```

### Validating Query Parameters

Query params arrive as strings. Use `z.coerce` for numeric fields:

```typescript
const paginationSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.enum(['asc', 'desc']).optional(),
})

app.get('/posts', zValidator('query', paginationSchema), (c) => {
  const { page, limit, sort } = c.req.valid('query')
  return c.json({ page, limit, sort })
})
```

### Validating Headers

Header names must be lowercase in the validator:

```typescript
const headerSchema = z.object({
  'x-api-key': z.string().min(1),
  'x-request-id': z.string().uuid().optional(),
})

app.use('/api/*', zValidator('header', headerSchema))
```

### Validating Form Data with Files

```typescript
const uploadSchema = z.object({
  file: z.instanceof(File),
  description: z.string().optional(),
})

app.post('/upload', zValidator('form', uploadSchema), async (c) => {
  const { file, description } = c.req.valid('form')
  // file is typed as File
  return c.json({ name: file.name, size: file.size })
})
```

## Standard Schema Validator

Use any Standard Schema-compatible library (Zod, Valibot, ArkType) with a single adapter:

```bash
npm i @hono/standard-validator
```

### With Valibot

```typescript
import * as v from 'valibot'
import { sValidator } from '@hono/standard-validator'

const schema = v.object({
  name: v.string(),
  age: v.number(),
})

app.post('/users', sValidator('json', schema), (c) => {
  const data = c.req.valid('json')
  return c.json(data, 201)
})
```

### With ArkType

```typescript
import { type } from 'arktype'
import { sValidator } from '@hono/standard-validator'

const schema = type({
  name: 'string',
  age: 'number',
})

app.post('/users', sValidator('json', schema), (c) => {
  const data = c.req.valid('json')
  return c.json(data, 201)
})
```

## OpenAPI Integration with @hono/zod-openapi

Generate OpenAPI specifications from Zod schemas:

```bash
npm i @hono/zod-openapi
```

### Define Routes with OpenAPI Metadata

```typescript
import { OpenAPIHono, createRoute, z } from '@hono/zod-openapi'

const app = new OpenAPIHono()

const PostSchema = z.object({
  id: z.string().openapi({ example: 'abc123' }),
  title: z.string().openapi({ example: 'My Post' }),
  body: z.string(),
})

const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
})

const ErrorSchema = z.object({
  error: z.string(),
})

const createPostRoute = createRoute({
  method: 'post',
  path: '/posts',
  tags: ['Posts'],
  summary: 'Create a new post',
  request: {
    body: {
      content: {
        'application/json': { schema: CreatePostSchema },
      },
    },
  },
  responses: {
    201: {
      description: 'Post created',
      content: { 'application/json': { schema: PostSchema } },
    },
    400: {
      description: 'Validation error',
      content: { 'application/json': { schema: ErrorSchema } },
    },
  },
})

app.openapi(createPostRoute, (c) => {
  const data = c.req.valid('json')
  const post = { id: crypto.randomUUID(), ...data }
  return c.json(post, 201)
})
```

### Serve OpenAPI Spec and Swagger UI

```typescript
import { swaggerUI } from '@hono/swagger-ui'

// Serve the OpenAPI JSON spec
app.doc('/doc', {
  openapi: '3.0.0',
  info: { title: 'My API', version: '1.0.0' },
})

// Serve Swagger UI
app.get('/swagger', swaggerUI({ url: '/doc' }))
```

### OpenAPI with Route Groups

```typescript
const postsApp = new OpenAPIHono()
  .openapi(listPostsRoute, listPostsHandler)
  .openapi(createPostRoute, createPostHandler)
  .openapi(getPostRoute, getPostHandler)

const usersApp = new OpenAPIHono()
  .openapi(listUsersRoute, listUsersHandler)

const app = new OpenAPIHono()
  .route('/posts', postsApp)
  .route('/users', usersApp)

app.doc('/doc', {
  openapi: '3.0.0',
  info: { title: 'API', version: '1.0.0' },
})
```

## Validation + RPC Type Flow

When using `zValidator` with RPC, the client automatically infers input types:

```typescript
// Server
const route = app.post(
  '/posts',
  zValidator('json', z.object({ title: z.string() })),
  (c) => {
    const { title } = c.req.valid('json')
    return c.json({ id: '1', title }, 201)
  }
)
export type AppType = typeof route

// Client
const client = hc<AppType>('http://localhost:8787/')
const res = await client.posts.$post({
  json: { title: 'Hello' }, // Type-checked against Zod schema
})
```

The Zod schema becomes the single source of truth for request shape, validation rules, and client types.

## Content-Type Requirement

Validation for `json` and `form` targets requires matching Content-Type headers. Without the header, the validator receives an empty object:

```typescript
// Testing: must set Content-Type
const res = await app.request('/posts', {
  method: 'POST',
  body: JSON.stringify({ title: 'Test' }),
  headers: { 'Content-Type': 'application/json' }, // Required
})
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Uppercase header names in validator | Headers always lowercase in Hono | Use `'x-api-key'` not `'X-Api-Key'` |
| Missing Content-Type in tests | Validator receives empty object `{}` | Set `Content-Type: application/json` |
| Not using `z.coerce` for query params | Validation fails (string vs number) | `z.coerce.number()` for numeric query params |
| Mixing zValidator and manual validator | Inconsistent type inference | Pick one approach per route |
| Not handling Zod errors | Default 400 response with raw Zod errors | Pass custom error handler as third argument |
