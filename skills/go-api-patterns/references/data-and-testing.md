# Data and Testing

Sources: pgx documentation, sqlx documentation, sqlc documentation, ent documentation, go.dev (database/sql, testing, httptest), Alex Edwards (Let's Go Further), Testcontainers for Go documentation

Covers: database library selection, repository patterns, connection pools, transactions, migrations, query testing, httptest usage, table-driven tests, integration tests, and testcontainers for Go APIs.

## Database Library Selection

Choose the thinnest abstraction that still buys you real leverage.

| Library | Best for | Trade-off |
|--------|----------|-----------|
| `pgx` | PostgreSQL-first services, max control, pool tuning | Postgres only |
| `database/sql` | Lowest common denominator, basic drivers | More boilerplate |
| `sqlx` | SQL-first teams that want struct scanning helpers | Still manual SQL |
| `sqlc` | Large SQL codebases that want generated type-safe methods | Codegen workflow |
| `ent` | Graph-style schema, strongly typed models, code-first development | Higher abstraction and generation cost |

### Practical defaults

| Situation | Recommendation |
|----------|----------------|
| New PostgreSQL service | `pgx` or `sqlc` over `pgx` |
| Team loves writing SQL | `sqlc` |
| Existing hand-written SQL service | `sqlx` |
| Need cross-database support | `database/sql` or `sqlx` |
| Strong domain modeling and generated query builders | `ent` |

## Repository Boundaries

Repositories isolate persistence concerns, not business workflows.

### Good repository responsibilities

1. Query construction
2. Row mapping
3. Transaction participation
4. Persistence-specific error conversion

### Bad repository responsibilities

| Anti-pattern | Move to |
|-------------|---------|
| Business rule orchestration | service layer |
| HTTP payload validation | handler layer |
| Cross-repository workflow coordination | service layer |
| Request-level metrics and response shaping | HTTP boundary |

## pgx Pattern

```go
type UserRepository struct {
    db *pgxpool.Pool
}

func (r *UserRepository) GetByID(ctx context.Context, id int64) (User, error) {
    const q = `select id, email, created_at from users where id = $1`
    var u User
    err := r.db.QueryRow(ctx, q, id).Scan(&u.ID, &u.Email, &u.CreatedAt)
    if errors.Is(err, pgx.ErrNoRows) {
        return User{}, ErrNotFound
    }
    return u, err
}
```

Use `pgxpool.Pool` directly for most services. You rarely need a second abstraction over the connection pool.

## sqlx Pattern

```go
type UserRow struct {
    ID    int64  `db:"id"`
    Email string `db:"email"`
}

func (r *UserRepository) List(ctx context.Context) ([]UserRow, error) {
    var users []UserRow
    err := r.db.SelectContext(ctx, &users, `select id, email from users order by id desc limit 100`)
    return users, err
}
```

`sqlx` is best when you want helper methods, not a new mental model.

## sqlc Pattern

| Strength | Why it matters |
|---------|----------------|
| SQL remains the source of truth | Easier to reason about execution plans |
| Generated types | Eliminates stringly-typed Scan code |
| Reviewable generated methods | Good for teams with strict code review |

Use sqlc when you have many queries and want compile-time guarantees around parameter and result types.

## ent Pattern

| Good fit | Warning sign |
|---------|-------------|
| Teams that prefer schema-as-code | Teams that need hand-tuned SQL everywhere |
| Graph-like traversal patterns | Heavy use of database-specific features |
| Generated edge traversals | Need to inspect every SQL statement |

Use ent deliberately. It is powerful, but a very different workflow from SQL-first development.

## Connection Pool Rules

### Tune these settings intentionally

| Setting | Why |
|--------|-----|
| max open connections | Protect database from overload |
| min idle connections | Reduce cold starts under bursty load |
| max lifetime | Prevent stale connections and LB issues |
| health check period | Detect dead backends |

### Pool sizing guideline

| Workload | Suggested starting point |
|---------|--------------------------|
| Small API, one pod | 10-20 |
| Moderate service, CPU-bound | 20-40 |
| Many replicas against small DB | Lower per-replica count |

Do the math at cluster level. Ten pods with pool size 20 means 200 DB connections.

## Transaction Rules

Use transactions only for operations that must succeed or fail together.

```go
func (s *OrderService) CreateOrder(ctx context.Context, in CreateOrderInput) error {
    tx, err := s.db.Begin(ctx)
    if err != nil {
        return err
    }
    defer tx.Rollback(ctx)

    if err := s.orders.Insert(ctx, tx, in.Order); err != nil {
        return err
    }
    if err := s.outbox.Insert(ctx, tx, NewOrderCreatedEvent(in.Order.ID)); err != nil {
        return err
    }
    return tx.Commit(ctx)
}
```

### Transaction anti-patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| External HTTP call inside transaction | Locks held while waiting on network | Move call outside tx or use outbox pattern |
| Long-running report generation in tx | Blocks pool and rows | Snapshot data first |
| Starting tx in handler for every write | Boilerplate and misuse | Start in service when needed |

## Migration Strategy

| Strategy | Use when |
|---------|----------|
| SQL files with goose/migrate/tern | SQL-first teams |
| ent migration | ent-managed schema evolution |
| Atlas / schema tool | Larger governance around schema changes |

Keep migrations in source control. Never rely on “current schema in prod” as truth.

## Testing Pyramid for Go APIs

### Recommended balance

| Test type | Tooling | Purpose |
|----------|---------|---------|
| Unit | `testing`, table-driven tests | Pure logic, helper functions |
| Handler integration | `httptest` | Request/response behavior |
| Repository integration | real DB / testcontainers | SQL correctness |
| End-to-end | docker compose / deployed env | Critical paths only |

Do not push every behavior into slow end-to-end tests.

## Table-driven Tests

Go’s testing style rewards explicit cases.

```go
func TestParsePage(t *testing.T) {
    cases := []struct {
        name string
        in   string
        want int
        err  bool
    }{
        {name: "default", in: "", want: 1},
        {name: "valid", in: "3", want: 3},
        {name: "bad", in: "abc", err: true},
    }

    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            got, err := parsePage(tc.in)
            if tc.err && err == nil { t.Fatal("expected error") }
            if !tc.err && got != tc.want { t.Fatalf("got %d want %d", got, tc.want) }
        })
    }
}
```

Use this pattern for validators, parsers, and service logic.

## httptest Patterns

### Handler test with recorder

```go
req := httptest.NewRequest(http.MethodGet, "/users/42", nil)
rr := httptest.NewRecorder()

handler.ServeHTTP(rr, req)

if rr.Code != http.StatusOK {
    t.Fatalf("status = %d", rr.Code)
}
```

### Full router test with server

```go
srv := httptest.NewServer(routes)
defer srv.Close()

resp, err := http.Get(srv.URL + "/healthz")
```

### When to use which

| Approach | Use for |
|---------|---------|
| Recorder | Single handler behavior |
| Test server | Router, middleware, and client integration |

## Mocking Rules

| Dependency | Mock or real? |
|-----------|---------------|
| Pure service collaborator | Mock okay |
| SQL repository | Prefer real DB in integration test |
| Third-party HTTP API | Mock or fake server |
| Clock / UUID / random | Fake deterministically |

Do not mock the database driver for SQL correctness tests.

## Testcontainers Pattern

Use testcontainers when SQL correctness matters and SQLite is not equivalent.

| Good fit | Example |
|---------|---------|
| PostgreSQL-specific queries | JSONB, array ops, advisory locks |
| Migration verification | apply migrations in CI |
| Pool behavior | integration under real driver |

### Checklist

1. Start DB container once per package when possible
2. Run migrations before tests
3. Use isolated schemas or truncate data between tests
4. Keep slow integration tests in a separate package or tag if needed

## Fixtures and Builders

Prefer small helper builders over giant JSON fixtures.

```go
func NewTestUser() User {
    return User{Email: "user@example.com", Name: "Test User"}
}
```

| Pattern | Benefit |
|--------|---------|
| Builder helpers | Easy to override one field |
| Factory functions | Centralize valid defaults |
| SQL seed files | Good for complex relational fixtures |

## Common Data/Test Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Sharing a global DB across unrelated tests without cleanup | Test pollution | Reset state between tests |
| Using mocks for all persistence tests | False confidence | Add real DB integration tests |
| Ignoring context cancellation in repository methods | Hung requests and shutdown pain | Pass `ctx` everywhere |
| Writing tests that assert exact SQL strings from ORM code | Brittle | Assert observable behavior |
| Not testing migrations in CI | Broken deploys | Run migrations against disposable DB |

## Release Readiness Checklist

- [ ] Database library choice matches team workflow
- [ ] Repository boundaries stay persistence-focused
- [ ] Pool sizing is reasoned at cluster level
- [ ] Transactions wrap only truly atomic work
- [ ] Migrations are source-controlled and CI-tested
- [ ] Handler tests use `httptest`
- [ ] SQL correctness is covered by integration tests against a real DB
