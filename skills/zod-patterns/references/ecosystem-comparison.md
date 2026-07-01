# Ecosystem Comparison and Migration

Sources: Zod v4 official documentation (zod.dev), Valibot documentation (valibot.dev), ArkType documentation (arktype.io), TypeBox documentation, runtime-type-benchmarks (moltar)

Covers: Zod vs Valibot vs ArkType vs Yup vs TypeBox, bundle size comparison, performance benchmarks, API style differences, migration paths, and Zod 3 to Zod 4 migration.

## Library Comparison

### Overview

| Library | TypeScript-First | Bundle (min+gzip) | API Style | Ecosystem |
|---------|-----------------|-------------------|-----------|-----------|
| Zod 4 | Yes | ~5.4kb (2kb Mini) | Method chain | Largest (tRPC, RHF, etc.) |
| Valibot | Yes | ~0.5-1kb | Functional (pipe) | Growing |
| ArkType | Yes | ~4kb | String-based DSL | Small |
| Yup | No (added later) | ~12kb | Method chain | Large (Formik) |
| TypeBox | Yes | ~4kb | JSON Schema builder | Fastify, Elysia |

### Bundle Size

| Library | Core Schema | Object + String + Number |
|---------|-------------|-------------------------|
| Zod 4 (full) | 5.36kb | ~6kb |
| Zod 4 Mini | 1.88kb | ~2.5kb |
| Valibot | 0.5kb | ~1.2kb |
| ArkType | 4kb | ~5kb |
| Yup | 12.4kb | ~13kb |
| TypeBox | 4kb | ~5kb |

Valibot and Zod Mini win on bundle size. Full Zod wins on DX and ecosystem.

### Performance (Object Parsing)

Based on Moltar runtime-type-benchmarks and Zod repo benchmarks:

| Library | Relative Speed | Notes |
|---------|---------------|-------|
| ArkType | Fastest | Compiles to optimized validators |
| TypeBox | Very fast | JSON Schema-based, compiled |
| Zod 4 | Fast (6.5x vs Zod 3) | Major improvement over v3 |
| Valibot | Comparable to Zod 4 | Similar architecture |
| Zod 3 | Baseline | Legacy |
| Yup | Slowest | Reflection-heavy |

### TypeScript Compiler Performance

| Library | tsc Instantiations (object+extend) |
|---------|-----------------------------------|
| Zod 4 | ~175 |
| Zod 3 | ~25,000 |
| ArkType | Low (string-based) |
| Valibot | Low (functional) |

Zod 4 reduced tsc instantiations by 100x compared to Zod 3.

## API Style Comparison

### Object Schema

```typescript
// Zod
const User = z.object({
  name: z.string().min(1),
  age: z.number().positive(),
});

// Valibot
import * as v from "valibot";
const User = v.object({
  name: v.pipe(v.string(), v.minLength(1)),
  age: v.pipe(v.number(), v.minValue(1)),
});

// ArkType
import { type } from "arktype";
const User = type({
  name: "string > 0",
  "age?": "number > 0",
});

// Yup
import * as y from "yup";
const User = y.object({
  name: y.string().required().min(1),
  age: y.number().required().positive(),
});

// TypeBox
import { Type } from "@sinclair/typebox";
const User = Type.Object({
  name: Type.String({ minLength: 1 }),
  age: Type.Number({ minimum: 1 }),
});
```

### Transform

```typescript
// Zod
z.string().transform((s) => s.length);

// Valibot
v.pipe(v.string(), v.transform((s) => s.length));

// ArkType — no built-in transforms
// TypeBox — no built-in transforms (compile-time only)
```

### Error Handling

```typescript
// Zod
const result = schema.safeParse(data);
if (!result.success) result.error.issues;

// Valibot
const result = v.safeParse(schema, data);
if (!result.success) result.issues;

// ArkType
const result = schema(data);
if (result instanceof type.errors) result.summary;
```

## Selection Guide

| Priority | Best Choice | Reason |
|----------|------------|--------|
| Ecosystem (tRPC, RHF, etc.) | Zod | Widest integration support |
| Bundle size critical | Valibot or Zod Mini | Sub-2kb bundles |
| Maximum runtime speed | ArkType | Compiled validators |
| JSON Schema interop | TypeBox or Zod 4 | Native JSON Schema support |
| Existing Formik project | Yup | Built-in Formik resolver |
| New TypeScript project | Zod 4 | Best balance of DX, speed, ecosystem |
| Library/SDK authoring | Zod Mini or Valibot | Tree-shakable, minimal footprint |

### Decision Flow

```
Need tRPC or massive ecosystem? → Zod 4
Need < 2kb bundle? → Valibot (or Zod Mini)
Need fastest possible parsing? → ArkType
Need JSON Schema as source of truth? → TypeBox
Already using Formik? → Yup (or migrate to RHF + Zod)
```

## Migrating from Yup to Zod

### Key Differences

| Yup | Zod |
|-----|-----|
| `.required()` needed for non-optional | All fields required by default |
| `.nullable()` distinct from `.optional()` | Same distinction |
| `.cast()` for coercion | `z.coerce.*()` |
| `.when()` for conditional | `.refine()` or discriminatedUnion |
| Lazy evaluation by default | Eager evaluation (fail fast) |
| `.isValid()` returns boolean | `.safeParse()` returns result object |

### Common Conversions

| Yup | Zod |
|-----|-----|
| `yup.string().required()` | `z.string()` (required by default) |
| `yup.string()` (optional) | `z.string().optional()` |
| `yup.number().positive()` | `z.number().positive()` |
| `yup.mixed().oneOf(["a","b"])` | `z.enum(["a","b"])` |
| `yup.array().of(yup.string())` | `z.array(z.string())` |
| `yup.object().shape({...})` | `z.object({...})` |
| `schema.isValid(data)` | `schema.safeParse(data).success` |
| `schema.cast(data)` | `z.coerce.*().parse(data)` |
| `schema.validate(data)` | `schema.parse(data)` |

## Migrating from Zod 3 to Zod 4

### Installation

```bash
npm install zod@^4.0.0
```

### Breaking Changes

| Zod 3 | Zod 4 | Action |
|-------|-------|--------|
| `z.string().email()` | `z.email()` (top-level) | Update calls (old still works, deprecated) |
| `z.string().uuid()` | `z.uuid()` | Update calls |
| `z.nativeEnum(E)` | `z.enum(E)` | Rename |
| `z.lazy(() => Schema)` | Getter syntax | Replace with `get prop() { return Schema }` |
| `{ message: "..." }` | `{ error: "..." }` | Rename param (old still works) |
| `{ required_error, invalid_type_error }` | `{ error: fn }` | Unify into function |
| `z.setErrorMap(fn)` | `z.config({ customError: fn })` | Update |
| `z.ZodError.format()` | Still available | No change |
| `.describe("...")` | `.meta({ description: "..." })` | Prefer .meta() |
| Refinements wrap in ZodEffects | Refinements live inside schema | No code change needed |
| `z.record(valSchema)` (one arg) | `z.record(z.string(), valSchema)` | Add key schema |
| Enum keys non-exhaustive | Enum keys exhaustive | Use `z.partialRecord()` for old behavior |

### New Features Available After Migration

| Feature | API |
|---------|-----|
| Recursive objects | Getter syntax (no `z.lazy`) |
| JSON Schema | `z.toJSONSchema(schema)` |
| Metadata | `.meta({...})`, `z.registry()` |
| File validation | `z.file()` |
| String booleans | `z.stringbool()` |
| Template literals | `z.templateLiteral([...])` |
| Pretty errors | `z.prettifyError(error)` |
| i18n | `z.config(z.locales.fr())` |
| Number formats | `z.int32()`, `z.float64()`, etc. |
| Zod Mini | `import * as z from "zod/mini"` |
| Overwrite | `.overwrite(fn)` |
| XOR union | `z.xor([...])` |
| Nested discriminated unions | Compose `z.discriminatedUnion` inside another |

### Migration Strategy

1. Install Zod 4: `npm install zod@^4.0.0`
2. Fix compilation errors (mostly `z.nativeEnum` → `z.enum`)
3. Run test suite — most code works unchanged
4. Update deprecated patterns at your own pace
5. Adopt new features (metadata, JSON Schema, etc.) as needed

## Ecosystem Integrations

Libraries with first-class Zod support:

| Library | Integration |
|---------|------------|
| tRPC | `.input(zodSchema)` / `.output(zodSchema)` |
| React Hook Form | `zodResolver(schema)` |
| Conform | `parseWithZod(formData, { schema })` |
| Drizzle ORM | `createInsertSchema(table)` / `createSelectSchema(table)` |
| ts-rest | Contract-first API definitions |
| Hono | `@hono/zod-validator` middleware |
| Elysia | Built-in Zod support |
| Fastify | `fastify-type-provider-zod` |
| OpenAI SDK | Function calling parameter schemas |
| LangChain | Structured output schemas |
| Prisma | `zod-prisma-types` generator |
| tRPC Panel | Auto-generated admin UI from schemas |
| Stainless | SDK generation from Zod schemas |

## When NOT to Use Zod

| Scenario | Alternative |
|----------|------------|
| JSON Schema is the canonical source | TypeBox (schema → types) |
| Need sub-500b bundle | Valibot |
| Pure compile-time validation | TypeScript itself (no runtime cost) |
| Schema-less dynamic validation | `joi` with runtime config |
| Binary protocol validation | Protocol Buffers, MessagePack |
