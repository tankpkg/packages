# Pagination, Filtering, and Sorting

Sources: RFC 5988 (Web Linking / Link header), Relay GraphQL Cursor Connections Specification (Meta, open source), OpenAPI Specification 3.1, IETF HTTP semantics

Covers: offset pagination, cursor pagination, keyset pagination, GraphQL Relay connections spec, sorting, filtering operators, field selection, response envelope design.

## Pagination Strategy Selection

| Strategy | Performance | Supports Page Numbers | Safe with Real-Time Data | Best For |
|---------|-----------|----------------------|------------------------|---------|
| Offset / Limit | O(offset) — degrades at depth | Yes | No — page drift on inserts/deletes | Admin UIs, small datasets, when total count required |
| Cursor (opaque token) | O(1) consistent | No — next/prev only | Yes | Feeds, timelines, large collections |
| Keyset (last-seen value) | O(1) consistent | No | Yes | REST APIs, sequential access, high-volume data |

Choose offset only when page numbers are a hard UI requirement and the dataset is small enough that deep pagination won't occur in practice.

## Offset Pagination

### Request Parameters

```
GET /users?page=2&per_page=20
GET /users?offset=40&limit=20
```

Both `page/per_page` and `offset/limit` are common. Pick one convention and use it everywhere.

### Response Envelope

```json
{
  "data": [ { "id": 1 }, { "id": 2 } ],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total_count": 847,
    "total_pages": 43,
    "has_next": true,
    "has_prev": true
  }
}
```

Use the `Link` header (RFC 5988) alongside the body for clients that prefer headers:

```http
Link: </users?page=3&per_page=20>; rel="next",
      </users?page=1&per_page=20>; rel="prev",
      </users?page=43&per_page=20>; rel="last",
      </users?page=1&per_page=20>; rel="first"
```

### Limits

Apply a maximum `per_page` (typically 100–500). Return a `400` if the client requests more:

```json
{ "type": "...", "title": "Invalid Request", "status": 400, "detail": "per_page cannot exceed 100." }
```

### SQL Implementation

```sql
-- Page 2, 20 items per page
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 20;
```

Performance cliff: `OFFSET 10000` requires scanning and discarding 10,000 rows before returning 20. Mitigate with a deferred join for wide tables:

```sql
SELECT u.*
FROM users u
JOIN (
  SELECT id FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 10000
) AS sub ON u.id = sub.id;
```

The subquery fetches only IDs (narrow), then the outer query fetches full rows for just those IDs.

### Page Drift Problem

If a new item is inserted between page 1 and page 2 requests, all subsequent pages shift. Users see duplicate items on page 2 that appeared on page 1, or skip items entirely. For real-time data, use cursor pagination instead.

## Cursor Pagination

### Request Parameters

```
GET /users?limit=20                              # First page
GET /users?after=eyJpZCI6NDJ9&limit=20          # Next page (forward)
GET /users?before=eyJpZCI6MX0=&limit=20         # Previous page (backward)
```

### Response Envelope

```json
{
  "data": [ { "id": 22 }, { "id": 21 } ],
  "pagination": {
    "has_next": true,
    "has_prev": true,
    "next_cursor": "eyJpZCI6MjF9",
    "prev_cursor": "eyJpZCI6MjJ9"
  }
}
```

### Cursor Encoding

The cursor must be opaque to the client — it encodes implementation details that clients should never parse. Use base64 of a JSON object containing the sort column values:

```typescript
function encodeCursor(item: { id: string; createdAt: Date }): string {
  const payload = { id: item.id, created_at: item.createdAt.toISOString() };
  return Buffer.from(JSON.stringify(payload)).toString('base64url');
}

function decodeCursor(cursor: string): { id: string; created_at: string } {
  return JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8'));
}
```

### Keyset SQL Implementation

```sql
-- First page (no cursor)
SELECT * FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- Next page (cursor decoded to: created_at='2024-01-15T10:00:00Z', id=42)
SELECT * FROM posts
WHERE (created_at, id) < ('2024-01-15T10:00:00Z', 42)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

Keyset rules:
- The sort key must be unique. Add `id` as a tiebreaker when sorting by a non-unique column.
- The cursor must encode all columns in the ORDER BY clause.
- The index must cover all ORDER BY columns: `CREATE INDEX ON posts (created_at DESC, id DESC);`
- Use row value comparison `(col1, col2) < (val1, val2)` — most databases optimize this correctly.

## GraphQL Relay Cursor Connections

The Relay Cursor Connections spec defines a standard pagination shape for GraphQL. Any client that understands the Relay spec can paginate your API without custom knowledge.

### Schema

```graphql
type Query {
  users(
    first: Int      # Forward: take the first N edges after `after`
    after: String   # Forward: start after this cursor
    last: Int       # Backward: take the last N edges before `before`
    before: String  # Backward: end before this cursor
  ): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int    # Optional — requires an extra COUNT query
}

type UserEdge {
  node: User!      # The actual item
  cursor: String!  # Opaque cursor for this specific edge position
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String    # Cursor of the first edge; null if no edges
  endCursor: String      # Cursor of the last edge; null if no edges
}
```

### Usage

```graphql
# First page
query {
  users(first: 20) {
    edges {
      node { id name email }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# Next page — pass endCursor from previous response as after
query {
  users(first: 20, after: "cursor_value_here") {
    edges {
      node { id name email }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

### totalCount Trade-Off

`totalCount` requires a `COUNT(*)` query on every paginated request — often expensive on large tables. Only add it if the UI genuinely needs "Showing 20 of 847 results." For infinite scroll or next/prev navigation, `hasNextPage` alone is sufficient.

If you need `totalCount`, consider caching it separately with a short TTL rather than computing it on every request.

## Sorting

### REST Sorting Parameters

Single-field sort with explicit direction:

```
GET /orders?sort=created_at&order=desc
GET /orders?sort=total_amount&order=asc
```

Multi-field sort using comma-separated fields with prefix convention (`-` = descending):

```
GET /users?sort=-created_at,last_name
```

Validate sort fields against an allowlist — never allow arbitrary column names from query params, as this exposes internal schema and enables abuse:

```typescript
const SORTABLE_FIELDS = new Set(['created_at', 'name', 'email', 'updated_at']);

function validateSortField(field: string): string {
  if (!SORTABLE_FIELDS.has(field)) {
    throw new ValidationError(`Cannot sort by '${field}'. Allowed: ${[...SORTABLE_FIELDS].join(', ')}`);
  }
  return field;
}
```

Include active sort parameters in the pagination response so clients can construct stable next-page URLs:

```json
{
  "data": [ ... ],
  "pagination": { ... },
  "sort": [ { "field": "created_at", "direction": "desc" } ]
}
```

### GraphQL Sorting

```graphql
enum SortDirection { ASC DESC }

enum UserSortField { CREATED_AT NAME EMAIL UPDATED_AT }

input UserSort {
  field: UserSortField!
  direction: SortDirection! = DESC
}

type Query {
  users(sort: [UserSort!], first: Int, after: String): UserConnection!
}
```

## Filtering

### Simple Equality and Range Filters

```
GET /orders?status=active
GET /orders?created_after=2024-01-01&created_before=2024-12-31
GET /users?role=admin&verified=true
```

Use clear, predictable parameter names. Prefer ISO 8601 for dates in filter values.

### Array (Any-Of) Filters

```
GET /orders?status=active&status=pending        # repeated param
GET /orders?status[]=active&status[]=pending    # bracket notation
GET /orders?status=active,pending               # comma-separated
```

Pick one convention across your API. Bracket notation is explicit; comma-separated is compact. Repeated param is the most broadly supported by HTTP frameworks.

### Operator-Based Filters

For APIs that need complex filtering, use an operator suffix:

```
GET /products?price[gte]=100&price[lte]=500
GET /users?created_at[after]=2024-01-01
GET /users?name[contains]=alice
```

| Suffix | Meaning | Example |
|--------|---------|---------|
| (none) or `[eq]` | Equals | `?status=active` |
| `[ne]` | Not equals | `?status[ne]=deleted` |
| `[gt]` | Greater than | `?age[gt]=18` |
| `[gte]` | Greater than or equal | `?price[gte]=100` |
| `[lt]` | Less than | `?price[lt]=1000` |
| `[lte]` | Less than or equal | `?price[lte]=1000` |
| `[in]` | In list | `?status[in]=active,pending` |
| `[contains]` | Substring match | `?name[contains]=alice` |
| `[starts_with]` | Prefix match | `?email[starts_with]=admin` |

Only expose operators that have indexed backing. A `[contains]` filter on a non-indexed text column is a full table scan.

### GraphQL Filtering

Use a structured filter input type:

```graphql
input OrderFilter {
  status: OrderStatus
  createdAfter: DateTime
  createdBefore: DateTime
  minAmount: Int
  maxAmount: Int
  search: String
}

type Query {
  orders(filter: OrderFilter, sort: [OrderSort!], first: Int, after: String): OrderConnection!
}
```

Structured input types are more maintainable than string-based filter expressions and provide full type safety.

## Sparse Fieldsets (Field Selection)

Allow clients to request only the fields they need, reducing payload size:

```
GET /users?fields=id,name,email
```

```json
[ { "id": 1, "name": "Alice", "email": "alice@example.com" } ]
```

Rules:
- Always include `id` in the response even if not requested — clients need it for caching and follow-up requests.
- Validate requested fields against a public allowlist.
- Document the default field set vs the complete available set.
- GraphQL provides field selection natively via query syntax — no extra implementation needed.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Offset pagination on large tables | O(offset) database scan; degrades past page 50-100 | Switch to cursor or keyset pagination |
| Non-unique sort key without tiebreaker | Inconsistent page boundaries; items appear on multiple pages | Add `id` as secondary sort column |
| Exposing raw database IDs or offsets as cursors | Leaks schema; cursor breaks on schema change | Encode cursor as opaque token (base64) |
| Sorting by non-indexed column | Full table scan on every paginated request | Only allow sort on indexed columns |
| Always computing `total_count` | Expensive `COUNT(*)` on every page request | Make it opt-in (`?include_total=true`) or cache separately |
| Accepting arbitrary sort column names | Schema exposure; enables abuse | Explicit allowlist of sortable fields |
| Mixing offset and cursor on the same endpoint | Ambiguous behavior, hard to implement correctly | Pick one strategy per collection endpoint |
| Pagination parameters that reset when filters change | Users see wrong page after filtering | Reset to page 1 when filter changes |
