# Testing and Seeding

Sources: Prisma ORM Documentation (prisma.io/docs), Prisma Blog testing series, jest-mock-extended documentation, 2025-2026 production testing patterns

Covers: Unit testing with mocked Prisma Client (singleton and dependency injection patterns), integration testing with real databases (Docker, migrate reset), database seeding (prisma db seed, faker, idempotent seeds), and test environment configuration.

## Testing Strategy

| Test Type | Database | Speed | Catches |
|-----------|----------|-------|---------|
| Unit tests | Mocked Prisma Client | Fast (~ms) | Logic errors, edge cases, input validation |
| Integration tests | Real database (Docker) | Slower (~s) | Schema issues, constraint violations, query correctness |
| E2E tests | Real database + API | Slowest | Full-stack issues, API contracts |

Combine unit tests (mocked) for fast feedback on business logic with integration tests (real DB) for query correctness and schema validation.

## Unit Testing with Mocked Client

### Prerequisites

```bash
npm install -D jest ts-jest jest-mock-extended @types/jest
```

### Approach 1: Singleton Mock

Create a singleton Prisma Client that Jest mocks automatically:

```typescript
// lib/prisma.ts
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()
export default prisma
```

```typescript
// test/singleton.ts
import { PrismaClient } from '@prisma/client'
import { mockDeep, mockReset, DeepMockProxy } from 'jest-mock-extended'
import prisma from '../lib/prisma'

jest.mock('../lib/prisma', () => ({
  __esModule: true,
  default: mockDeep<PrismaClient>(),
}))

beforeEach(() => {
  mockReset(prismaMock)
})

export const prismaMock = prisma as unknown as DeepMockProxy<PrismaClient>
```

```typescript
// jest.config.js
module.exports = {
  clearMocks: true,
  preset: 'ts-jest',
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/test/singleton.ts'],
}
```

### Using the Singleton Mock in Tests

```typescript
// __tests__/user.test.ts
import { prismaMock } from '../test/singleton'
import { createUser } from '../services/user'

test('creates a new user', async () => {
  const mockUser = {
    id: 1,
    email: 'alice@example.com',
    name: 'Alice',
    role: 'USER',
    createdAt: new Date(),
    updatedAt: new Date(),
  }

  prismaMock.user.create.mockResolvedValue(mockUser)

  const result = await createUser('alice@example.com', 'Alice')

  expect(result).toEqual(mockUser)
  expect(prismaMock.user.create).toHaveBeenCalledWith({
    data: { email: 'alice@example.com', name: 'Alice' },
  })
})

test('throws on duplicate email', async () => {
  prismaMock.user.create.mockRejectedValue(
    new Prisma.PrismaClientKnownRequestError('Unique constraint failed', {
      code: 'P2002',
      meta: { target: ['email'] },
      clientVersion: '5.0.0',
    })
  )

  await expect(createUser('alice@example.com', 'Alice'))
    .rejects.toThrow('Email already registered')
})
```

### Approach 2: Dependency Injection

Pass Prisma Client as a parameter to enable testing without module mocking:

```typescript
// context.ts
import { PrismaClient } from '@prisma/client'
import { mockDeep, DeepMockProxy } from 'jest-mock-extended'

export type Context = { prisma: PrismaClient }
export type MockContext = { prisma: DeepMockProxy<PrismaClient> }

export const createMockContext = (): MockContext => ({
  prisma: mockDeep<PrismaClient>(),
})
```

```typescript
// services/user.ts
import { Context } from '../context'

export async function createUser(email: string, name: string, ctx: Context) {
  return ctx.prisma.user.create({
    data: { email, name },
  })
}
```

```typescript
// __tests__/user.test.ts
import { MockContext, Context, createMockContext } from '../context'
import { createUser } from '../services/user'

let mockCtx: MockContext
let ctx: Context

beforeEach(() => {
  mockCtx = createMockContext()
  ctx = mockCtx as unknown as Context
})

test('creates a new user', async () => {
  const mockUser = { id: 1, email: 'alice@example.com', name: 'Alice' }
  mockCtx.prisma.user.create.mockResolvedValue(mockUser as any)

  const result = await createUser('alice@example.com', 'Alice', ctx)
  expect(result.email).toBe('alice@example.com')
})
```

### Singleton vs DI

| Aspect | Singleton | Dependency Injection |
|--------|-----------|---------------------|
| Setup complexity | Simpler (jest.config + singleton file) | More boilerplate (context types) |
| Test isolation | Reset mock before each test | New context per test |
| Refactoring cost | Low (import mock globally) | Higher (pass context everywhere) |
| Framework compatibility | Jest-specific | Framework-agnostic |
| Best for | Most projects | Large apps with many services |

## Integration Testing

### Docker-Based Test Database

```yaml
# docker-compose.test.yml
services:
  test-db:
    image: postgres:16
    environment:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # RAM disk for speed
```

### Test Setup and Teardown

```typescript
// test/setup.ts
import { PrismaClient } from '@prisma/client'
import { execSync } from 'child_process'

const prisma = new PrismaClient()

beforeAll(async () => {
  // Apply migrations to test database
  execSync('npx prisma migrate deploy', {
    env: {
      ...process.env,
      DATABASE_URL: 'postgresql://test:test@localhost:5433/test',
    },
  })
})

afterAll(async () => {
  await prisma.$disconnect()
})

// Clean database between tests
async function cleanDatabase() {
  const tableNames = await prisma.$queryRaw<{ tablename: string }[]>`
    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  `
  const tables = tableNames
    .map(t => t.tablename)
    .filter(name => name !== '_prisma_migrations')
    .map(name => `"public"."${name}"`)
    .join(', ')

  if (tables.length > 0) {
    await prisma.$executeRawUnsafe(`TRUNCATE TABLE ${tables} CASCADE`)
  }
}

beforeEach(async () => {
  await cleanDatabase()
})

export { prisma }
```

### Integration Test Example

```typescript
// __tests__/integration/user.test.ts
import { prisma } from '../setup'

test('creates and retrieves user with posts', async () => {
  const user = await prisma.user.create({
    data: {
      email: 'alice@example.com',
      name: 'Alice',
      posts: {
        create: [
          { title: 'Post 1', published: true },
          { title: 'Post 2', published: false },
        ],
      },
    },
    include: { posts: true },
  })

  expect(user.posts).toHaveLength(2)
  expect(user.email).toBe('alice@example.com')

  // Verify published filter works
  const publishedPosts = await prisma.post.findMany({
    where: { authorId: user.id, published: true },
  })
  expect(publishedPosts).toHaveLength(1)
})

test('enforces unique email constraint', async () => {
  await prisma.user.create({
    data: { email: 'alice@example.com', name: 'Alice' },
  })

  await expect(
    prisma.user.create({
      data: { email: 'alice@example.com', name: 'Alice 2' },
    })
  ).rejects.toThrow()
})
```

### Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    setupFiles: ['./test/setup.ts'],
    testTimeout: 10000,
    pool: 'forks',  // Use forks for DB isolation
    poolOptions: {
      forks: { singleFork: true },  // Serialize DB tests
    },
  },
})
```

## Database Seeding

### Seed Script

```typescript
// prisma/seed.ts
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  // Upsert for idempotent seeding
  const admin = await prisma.user.upsert({
    where: { email: 'admin@example.com' },
    update: {},
    create: {
      email: 'admin@example.com',
      name: 'Admin',
      role: 'ADMIN',
    },
  })

  const categories = ['Technology', 'Science', 'Design']
  for (const name of categories) {
    await prisma.category.upsert({
      where: { name },
      update: {},
      create: { name },
    })
  }

  console.log('Seeded:', { admin })
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(() => prisma.$disconnect())
```

### Configure in package.json

```json
{
  "prisma": {
    "seed": "tsx prisma/seed.ts"
  }
}
```

Run seed manually or automatically after `migrate reset`:

```bash
npx prisma db seed          # Manual seed
npx prisma migrate reset    # Drops DB, applies migrations, runs seed
```

### Faker for Realistic Test Data

```typescript
import { faker } from '@faker-js/faker'

async function seedTestData(count: number) {
  const users = Array.from({ length: count }, () => ({
    email: faker.internet.email(),
    name: faker.person.fullName(),
    role: faker.helpers.arrayElement(['USER', 'ADMIN'] as const),
  }))

  await prisma.user.createMany({ data: users, skipDuplicates: true })
}
```

### Idempotent Seeding

Use `upsert` instead of `create` to make seeds re-runnable:

```typescript
// BAD: Fails on second run (duplicate key)
await prisma.user.create({
  data: { email: 'admin@example.com', name: 'Admin' },
})

// GOOD: Idempotent -- safe to run multiple times
await prisma.user.upsert({
  where: { email: 'admin@example.com' },
  update: {},  // No changes if exists
  create: { email: 'admin@example.com', name: 'Admin' },
})
```

## Test Environment Tips

| Tip | Implementation |
|-----|---------------|
| Use separate `.env.test` | `dotenv -e .env.test -- npx jest` |
| Parallelize safely | Separate database per test suite or TRUNCATE between tests |
| Speed up Docker DB | Use `tmpfs` mount for PostgreSQL data directory |
| Avoid test pollution | TRUNCATE tables in `beforeEach`, not `afterEach` |
| Skip seed in CI tests | Use explicit test fixtures instead of shared seeds |
| Type-safe test factories | Create factory functions returning Prisma input types |
