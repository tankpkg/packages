# Schema Design

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Blog (prisma.io/blog), 2025-2026 production schema patterns

Covers: Prisma schema fundamentals, model definition, field types, relations (1:1, 1:n, m:n implicit and explicit, self-relations), indexes, enums, naming conventions, referential actions, multi-schema support, and schema organization.

## Schema Fundamentals

The Prisma schema (`schema.prisma`) is the single source of truth for database structure, Prisma Client types, and migrations. It uses a dedicated DSL with three block types:

| Block | Purpose | Example |
|-------|---------|---------|
| `datasource` | Database connection | `provider = "postgresql"` |
| `generator` | Code generation target | `provider = "prisma-client-js"` |
| `model` | Database table/collection | Fields, relations, indexes |
| `enum` | Constrained value set | Status, Role |
| `type` | Composite type (MongoDB) | Address, Coordinates |

### Datasource Configuration

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
  output   = "./generated/prisma"
}
```

Set `output` to control where generated types land -- useful for monorepos.

## Model Definition

### Field Types

| Prisma Type | PostgreSQL | MySQL | Notes |
|-------------|-----------|-------|-------|
| `String` | `text` | `varchar(191)` | Use `@db.VarChar(n)` for specific length |
| `Int` | `integer` | `int` | 32-bit |
| `BigInt` | `bigint` | `bigint` | 64-bit, maps to JS `BigInt` |
| `Float` | `double precision` | `double` | Avoid for money |
| `Decimal` | `decimal(65,30)` | `decimal(65,30)` | Use for money and precision |
| `Boolean` | `boolean` | `tinyint(1)` | |
| `DateTime` | `timestamp(3)` | `datetime(3)` | Millisecond precision |
| `Json` | `jsonb` | `json` | PostgreSQL `jsonb` is queryable |
| `Bytes` | `bytea` | `longblob` | Binary data |

### Common Attributes

```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  role      Role     @default(USER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  posts     Post[]

  @@index([email])
  @@map("users")
}
```

| Attribute | Purpose |
|-----------|---------|
| `@id` | Primary key |
| `@default()` | Default value: `autoincrement()`, `cuid()`, `uuid()`, `now()`, `dbgenerated()` |
| `@unique` | Unique constraint |
| `@updatedAt` | Auto-update timestamp on modification |
| `@map("col")` | Map to different database column name |
| `@@map("tbl")` | Map to different database table name |
| `@@index([fields])` | Database index |
| `@@unique([fields])` | Composite unique constraint |
| `@db.VarChar(255)` | Native database type override |

### ID Strategy Selection

| Strategy | Syntax | When to Use |
|----------|--------|-------------|
| Auto-increment | `@id @default(autoincrement())` | Simple apps, sequential IDs acceptable |
| CUID | `@id @default(cuid())` | Distributed systems, URL-safe, sortable |
| UUID | `@id @default(uuid())` | Standards compliance, universally unique |
| Database-generated | `@id @default(dbgenerated("gen_random_uuid()"))` | Database-specific generation |

Prefer `cuid()` for most applications -- URL-safe, collision-resistant, sortable by creation time.

## Relations

### One-to-One

```prisma
model User {
  id      Int      @id @default(autoincrement())
  profile Profile?
}

model Profile {
  id     Int  @id @default(autoincrement())
  user   User @relation(fields: [userId], references: [id])
  userId Int  @unique  // @unique makes it 1:1
  bio    String?
}
```

The `@unique` on the foreign key field enforces the one-to-one constraint. Place the FK on the side that "belongs to" the other.

### One-to-Many

```prisma
model User {
  id    Int    @id @default(autoincrement())
  posts Post[]
}

model Post {
  id       Int  @id @default(autoincrement())
  author   User @relation(fields: [authorId], references: [id])
  authorId Int
}
```

The foreign key lives on the "many" side. The `posts Post[]` field on User is a virtual relation field -- it does not exist in the database.

### Many-to-Many (Implicit)

```prisma
model Post {
  id         Int        @id @default(autoincrement())
  categories Category[]
}

model Category {
  id    Int    @id @default(autoincrement())
  posts Post[]
}
```

Prisma auto-creates a join table (`_CategoryToPost`). Use implicit m:n when:
- No extra data on the relationship
- Both models use a single `@id` field
- Simpler Prisma Client API (one fewer nesting level)

### Many-to-Many (Explicit)

```prisma
model Post {
  id         Int            @id @default(autoincrement())
  categories CategoriesOnPosts[]
}

model Category {
  id    Int                @id @default(autoincrement())
  posts CategoriesOnPosts[]
}

model CategoriesOnPosts {
  post       Post     @relation(fields: [postId], references: [id])
  postId     Int
  category   Category @relation(fields: [categoryId], references: [id])
  categoryId Int
  assignedAt DateTime @default(now())

  @@id([postId, categoryId])
}
```

Use explicit m:n when storing extra data on the relationship (timestamps, ordering, metadata) or when using composite IDs.

### Self-Relations

```prisma
model User {
  id         Int    @id @default(autoincrement())
  followers  User[] @relation("UserFollows")
  following  User[] @relation("UserFollows")
}
```

Disambiguate with `@relation("name")` when a model relates to itself. Prisma creates a join table for implicit self-m:n relations.

### Disambiguating Multiple Relations

When two models have multiple relations, name each relation:

```prisma
model User {
  id           Int    @id @default(autoincrement())
  writtenPosts Post[] @relation("WrittenPosts")
  pinnedPost   Post?  @relation("PinnedPost")
}

model Post {
  id         Int   @id @default(autoincrement())
  author     User  @relation("WrittenPosts", fields: [authorId], references: [id])
  authorId   Int
  pinnedBy   User? @relation("PinnedPost", fields: [pinnedById], references: [id])
  pinnedById Int?  @unique
}
```

## Referential Actions

Control what happens when a referenced record is deleted or updated:

| Action | On Delete | On Update |
|--------|-----------|-----------|
| `Cascade` | Delete child records | Update child FK |
| `Restrict` | Prevent deletion if children exist | Prevent update |
| `NoAction` | Database-level restrict (deferred) | Database-level restrict |
| `SetNull` | Set FK to null (field must be optional) | Set FK to null |
| `SetDefault` | Set FK to default value | Set FK to default |

```prisma
model Post {
  author   User @relation(fields: [authorId], references: [id], onDelete: Cascade)
  authorId Int
}
```

Default is `Restrict` for required relations and `SetNull` for optional. Set `onDelete: Cascade` explicitly for parent-child hierarchies where children should be deleted with the parent.

## Enums

```prisma
enum Role {
  USER
  ADMIN
  MODERATOR
}

model User {
  role Role @default(USER)
}
```

Enums map to database-native enums on PostgreSQL. On MySQL, they map to `ENUM` type. Enums provide type safety in both schema and generated client types.

## Indexes and Performance

### Index Types

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  content   String
  authorId  Int
  createdAt DateTime @default(now())
  status    Status

  @@index([authorId])                      // Single-column index
  @@index([authorId, createdAt])           // Composite index
  @@index([title], type: BTree)            // B-tree (default)
  @@index([content], type: Gin)            // GIN for full-text (PostgreSQL)
  @@unique([authorId, title])              // Composite unique
}
```

| Index Type | Use Case |
|-----------|----------|
| `BTree` (default) | Equality, range, sorting |
| `Hash` | Equality only (PostgreSQL) |
| `Gin` | Full-text search, JSONB (PostgreSQL) |
| `Gist` | Geometry, range types (PostgreSQL) |

### Index Strategy

- Index all foreign key columns (Prisma does not auto-index FKs on all databases)
- Add composite indexes for frequent multi-column `WHERE` clauses
- Index columns used in `orderBy`
- Avoid over-indexing -- each index slows writes

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Model | PascalCase, singular | `User`, `BlogPost` |
| Field | camelCase | `firstName`, `createdAt` |
| Enum | PascalCase | `Role`, `PostStatus` |
| Enum value | SCREAMING_SNAKE | `ADMIN`, `IN_PROGRESS` |
| Relation field | camelCase, descriptive | `author`, `writtenPosts` |
| FK scalar | relation + `Id` | `authorId`, `categoryId` |
| Table mapping | snake_case plural | `@@map("blog_posts")` |

Use `@@map` and `@map` to maintain clean Prisma naming while matching existing database conventions.

## Schema Organization

For large schemas, split into multiple files using `prismaSchemaFolder` (Prisma v5.15+):

```
prisma/
  schema/
    base.prisma       // datasource + generator
    user.prisma        // User, Profile models
    post.prisma        // Post, Category models
    enums.prisma       // All enums
```

Enable in `package.json`:

```json
{
  "prisma": {
    "schema": "prisma/schema"
  }
}
```

This improves maintainability for schemas with 20+ models. Each file can contain models, enums, and types -- only `datasource` and `generator` must appear once.

## Multi-Schema Support (PostgreSQL)

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  schemas  = ["public", "auth"]
}

model User {
  id Int @id
  @@schema("auth")
}

model Post {
  id Int @id
  @@schema("public")
}
```

Multi-schema enables organizing models across PostgreSQL schemas. Useful for separating concerns (auth, billing, content) within a single database.
