---
name: "@tank/zod-patterns"
description: |
  Zod schema validation patterns for TypeScript applications. Covers schema
  primitives and composition (string, number, object, array, enum, union,
  discriminatedUnion, record, tuple), transforms and pipes, refinements,
  error handling (safeParse, custom errors, error formatting, i18n), type
  inference (z.infer, z.input, z.output), branded types, recursive schemas,
  coercion, and Zod 4 features (Zod Mini, metadata registries, JSON Schema
  conversion, file schemas, stringbool, template literals). Includes integration
  patterns for React Hook Form, tRPC, Next.js, Express/Hono API validation,
  and environment variable parsing. Covers Zod vs Valibot vs ArkType vs Yup.

  Synthesizes Zod v4 official documentation (zod.dev), colinhacks/zod GitHub,
  @hookform/resolvers, tRPC documentation, and TypeScript handbook.

  Trigger phrases: "zod", "zod schema", "zod validation", "zod tutorial",
  "zod cheat sheet", "zod typescript", "zod infer", "zod transform",
  "zod refine", "zod union", "zod discriminated union", "zod react hook form",
  "zod trpc", "zod error", "zod custom error", "zod enum", "zod optional",
  "zod default", "zod pipe", "zod branded", "zod coerce", "zod safeParse",
  "zod object", "zod array", "zod record", "schema validation typescript",
  "runtime type checking", "zod mini", "zod 4", "zod environment variables"
---

# Zod Patterns

## Core Philosophy

1. **Parse, don't validate** — Use `safeParse` to convert unknown data into typed values at system boundaries. Parsing returns typed data; validation just says yes/no.
2. **Schema is the source of truth** — Define the Zod schema first, infer TypeScript types from it with `z.infer<>`. Never duplicate types manually.
3. **Fail at the boundary, trust the interior** — Validate untrusted data (API inputs, form data, env vars, config files) at entry points. Once parsed, the interior code operates on trusted types without re-validation.
4. **Compose, don't repeat** — Build complex schemas by composing primitives: `.extend()`, `.pick()`, `.omit()`, `.partial()`, `.merge()`, spread syntax. Reuse base schemas across endpoints.
5. **Errors are data, not exceptions** — Prefer `safeParse` over `parse` in application code. Reserve throwing `parse` for scripts and CLIs where crash-on-invalid is acceptable.

## Quick-Start: Common Problems

### "How do I validate an API request body?"

1. Define a Zod schema for the expected shape
2. Call `schema.safeParse(req.body)` in the handler
3. Return 400 with formatted errors if `!result.success`
4. Use `result.data` (fully typed) for business logic
-> See `references/api-validation.md`

### "How do I connect Zod with React Hook Form?"

1. Install `@hookform/resolvers`
2. Pass `zodResolver(schema)` to `useForm({ resolver: ... })`
3. Infer form types from the schema with `z.infer<typeof schema>`
-> See `references/form-integration.md`

### "How do I validate environment variables?"

```typescript
const envSchema = z.object({
  DATABASE_URL: z.url(),
  PORT: z.coerce.number().default(3000),
  NODE_ENV: z.enum(["development", "staging", "production"]),
  DEBUG: z.stringbool().default("false"),
});
export const env = envSchema.parse(process.env);
```
-> See `references/practical-recipes.md`

### "How do I transform data during parsing?"

1. Use `.transform()` to change the output type
2. Use `.pipe()` to chain schema-to-schema transformations
3. Use `.overwrite()` (Zod 4) for same-type mutations that preserve introspection
-> See `references/transforms-pipes.md`

### "Which validation library should I use?"

| Need | Library |
|------|---------|
| TypeScript-first, largest ecosystem | Zod |
| Smallest bundle size (<1kb) | Valibot |
| Fastest runtime validation | ArkType |
| Legacy projects, Formik | Yup |
-> See `references/ecosystem-comparison.md`

## Decision Trees

### Schema Composition

| Goal | Method |
|------|--------|
| Add fields to object | `.extend()` or spread `{ ...A.shape, ...B.shape }` |
| Remove fields | `.omit({ key: true })` |
| Keep only specific fields | `.pick({ key: true })` |
| Make all fields optional | `.partial()` |
| Make all fields required | `.required()` |
| Combine two object schemas | `z.intersection(A, B)` or spread |

### Error Handling

| Context | Approach |
|---------|----------|
| API handlers, middleware | `safeParse` + return formatted errors |
| CLI scripts, build tools | `parse` (throw on failure) |
| Forms (React Hook Form) | `zodResolver` handles errors automatically |
| Global error messages | `z.config({ customError: ... })` |
| Per-field custom messages | `z.string({ error: "..." })` |

### Parse vs SafeParse

| Signal | Use |
|--------|-----|
| Untrusted external input (API, form, file) | `safeParse` — handle errors gracefully |
| Startup config, env vars (must succeed) | `parse` — crash fast if invalid |
| Internal data you trust | Skip validation entirely |

## Reference Index

| File | Contents |
|------|----------|
| `references/schema-primitives.md` | All schema types: strings, numbers, objects, arrays, enums, unions, discriminatedUnion, records, tuples, literals, dates, nullish, recursive schemas |
| `references/transforms-pipes.md` | Transforms, pipes, coercion, preprocess, overwrite, refinements, superRefine, custom validators, async validation |
| `references/error-handling.md` | safeParse, ZodError structure, error customization (schema-level, per-parse, global), error formatting, prettifyError, i18n locales |
| `references/type-inference.md` | z.infer, z.input, z.output, branded types, readonly schemas, JSON Schema conversion, metadata registries, Zod Mini |
| `references/form-integration.md` | React Hook Form + zodResolver, server actions, progressive enhancement, conditional validation, field arrays, multi-step forms |
| `references/api-validation.md` | Express/Hono/Next.js middleware, tRPC integration, request/response validation, OpenAPI generation |
| `references/practical-recipes.md` | Environment variables, config parsing, API response validation, date handling, file uploads, discriminated union patterns |
| `references/ecosystem-comparison.md` | Zod vs Valibot vs ArkType vs Yup vs TypeBox, bundle size, performance benchmarks, migration paths, Zod 3 to 4 migration |
