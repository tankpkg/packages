# Syntax

Sources: Drizzle ORM official documentation, drizzle-kit docs, Drizzle query builder reference, TypeScript/SQL workflow practices

Covers: schema definition syntax, columns and relations, query builder basics, drizzle-kit commands, type inference, and common Drizzle ORM snippets.

## Table Definition

```ts
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: text('email').notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
})
```

## Common Column Helpers

| Need | Helper |
|-----|--------|
| integer PK | `serial(...)` |
| text | `text(...)` |
| boolean | `boolean(...)` |
| timestamp | `timestamp(...)` |
| JSON | `json(...)` / db-specific helper |

### Column review questions

1. Is this field nullable, or should it be required?
2. Should this field be unique or indexed?
3. Is there a db-specific type helper that better matches the actual data?

## Relations

| Need | Pattern |
|-----|---------|
| one-to-many | foreign key + relation helper |
| many-to-many | join table |
| indexes | define in table extras |

### Join table reminder

Many-to-many in Drizzle still means an explicit join table — cheat sheets should make that obvious because it is a common source of confusion for ORM users coming from more magical systems.

## Query Builder Basics

| Task | Syntax |
|-----|--------|
| select | `db.select().from(users)` |
| insert | `db.insert(users).values(...)` |
| update | `db.update(users).set(...).where(...)` |
| delete | `db.delete(users).where(...)` |
| join | `.leftJoin(...)`, `.innerJoin(...)` |

### Common select patterns

| Need | Example |
|-----|---------|
| filtered rows | `where(eq(users.id, id))` |
| ordered rows | `orderBy(desc(users.createdAt))` |
| limited rows | `limit(10)` |
| paginated rows | `limit(...)` + `offset(...)` |

### Insert/update reminders

| Concern | Pattern |
|--------|---------|
| insert one row | `.values({ ... })` |
| insert many | `.values([{ ... }, { ... }])` |
| update filtered row | `.set({ ... }).where(...)` |

## Query Filter Helpers

| Need | Helper |
|-----|--------|
| equality | `eq(...)` |
| inequality | `ne(...)` |
| greater/less than | `gt(...)`, `lt(...)` |
| boolean combinations | `and(...)`, `or(...)` |
| inclusion | `inArray(...)` |

## Join Patterns

| Join type | Use |
|----------|-----|
| `innerJoin` | require matching rows |
| `leftJoin` | include unmatched left rows |

Drizzle joins stay explicit, which is a major part of its appeal for SQL-minded teams.

## drizzle-kit Commands

| Need | Command |
|-----|---------|
| generate migration | `drizzle-kit generate` |
| push schema | `drizzle-kit push` |
| migrate | `drizzle-kit migrate` |
| studio | `drizzle-kit studio` |

### Workflow review questions

1. Is this project using generated migrations or direct push workflow?
2. Is the chosen workflow consistent across the team and CI?
3. Are schema changes reviewed before being applied to shared environments?

## Type Inference

| Need | Pattern |
|-----|---------|
| select type | `typeof users.$inferSelect` |
| insert type | `typeof users.$inferInsert` |

Type inference is one of the fastest wins in Drizzle because it keeps schema and TypeScript aligned without separate model declarations.

## Index and Constraint Notes

| Concern | Pattern |
|--------|---------|
| unique field | `.unique()` or unique index |
| query speed | index common filters/order fields |
| relation integrity | explicit foreign keys |

## Common Schema Patterns

| Need | Pattern |
|-----|---------|
| created timestamps | `timestamp(...).defaultNow().notNull()` |
| soft-delete-ish marker | nullable deleted timestamp or status field |
| ownership relation | `userId` foreign key |

## Relation Design Questions

1. Which side owns the foreign key?
2. Is a join table required?
3. Should frequently filtered relation columns be indexed?

## Query Composition Heuristics

| Heuristic | Why |
|----------|-----|
| keep query builder chains short and readable | maintainability |
| group filters clearly | easier review |
| keep selected fields intentional when needed | payload and clarity |

## drizzle-kit Workflow Notes

| Step | Why |
|-----|-----|
| update schema file | source of truth |
| generate or push | apply chosen workflow |
| review migration output | catch unsafe schema drift |
| run studio when needed | inspect interactively |

## Schema Review Checklist

| Check | Why |
|------|-----|
| required vs nullable correct | data integrity |
| indexes align with query patterns | performance |
| relation keys explicit | join clarity |

## Join Review Questions

1. Should this be an inner or left join?
2. Are you joining only what the query needs?
3. Is the query still readable to a SQL-minded reviewer?

## Command Flow Questions

| Question | Why |
|---------|-----|
| is this local iteration or shared-env schema change? | choose push/generate flow carefully |
| are migrations part of the team workflow? | avoid drift |
| is studio useful here or just curiosity? | keep workflow sharp |

## Common Drizzle Smells

| Smell | Why it matters |
|------|----------------|
| schema types and TS usage drift apart | weak type leverage |
| team mixes multiple schema migration habits | inconsistent releases |
| joins become hard to read | query intent getting lost |

## Final Drizzle Review Questions

1. Can you define a table and relation quickly from this page?
2. Can you find the right query/filter helper without scanning full docs?
3. Is the drizzle-kit workflow clear enough to avoid team drift?

## Cheat-Sheet Review Questions

1. Can you define a table quickly from this page?
2. Can you find the basic query shape without opening full docs?
3. Can you remember the key drizzle-kit commands under pressure?

## Common Drizzle Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| forgetting relations/join table structure | awkward queries | design schema clearly |
| mixing migration workflows casually | drift | choose one clear drizzle-kit path |
| underusing inferred types | weaker TS value | use `$inferSelect` / `$inferInsert` |

## Common Drizzle Review Heuristics

| Heuristic | Why |
|----------|-----|
| keep schema explicit | type and SQL clarity |
| avoid mixing styles across team | migration/tooling consistency |
| shape joins and filters intentionally | preserve readability |

## Quick Copy Snippets

### Basic filtered select

```ts
const user = await db
  .select()
  .from(users)
  .where(eq(users.id, userId))
```

### Basic insert

```ts
await db.insert(users).values({ email })
```

### Basic update

```ts
await db.update(users).set({ email }).where(eq(users.id, userId))
```

### Basic delete

```ts
await db.delete(users).where(eq(users.id, userId))
```

## Final Usage Notes

The cheat sheet is successful if an engineer can move from “I forgot the exact Drizzle syntax” to a working schema, query, or drizzle-kit command in seconds.

## Final Drizzle Checklist

- [ ] schema syntax examples are easy to copy
- [ ] query builder basics are grouped clearly
- [ ] drizzle-kit commands are included
- [ ] inferred type patterns are easy to find
