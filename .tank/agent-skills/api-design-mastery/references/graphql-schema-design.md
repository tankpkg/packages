# GraphQL Schema Design

Sources: GraphQL specification (graphql.org, open source), Relay Cursor Connections Specification (Meta, open source), graphql-js reference implementation, Apollo Server documentation (open source)

Covers: schema-first design, type system, queries/mutations/subscriptions, the N+1 problem, DataLoader batching, Relay connections spec, query complexity limits, error handling.

## Schema-First Design

Define the schema in SDL (Schema Definition Language) before writing any resolver code. The schema is the contract between client and server. Clients should participate in schema design — they know what data they need and in what shape.

```graphql
# Define this first. Write resolvers second.
type User {
  id: ID!
  email: String!
  fullName: String!
  createdAt: DateTime!
  posts: [Post!]!
}
```

Schema-first advantages:
- Frontend and backend teams can work in parallel once the schema is agreed
- The schema documents the API without extra tooling
- Breaking changes are visible as schema diffs

## Type System

### Built-In Scalars

| Scalar | Represents |
|--------|-----------|
| `String` | UTF-8 string |
| `Int` | 32-bit signed integer |
| `Float` | Double-precision float |
| `Boolean` | true / false |
| `ID` | Opaque identifier (serialized as String) |

### Custom Scalars

Define custom scalars for domain types that built-ins can't express:

```graphql
scalar DateTime   # ISO 8601 string, e.g. "2024-03-15T10:30:00Z"
scalar URL        # Valid URL string
scalar Email      # Valid email address string
scalar JSON       # Arbitrary JSON — use sparingly (loses type safety)
```

Implement custom scalars with serialization, parsing, and literal parsing on the server.

### Type Kinds

| Kind | Purpose | Example |
|------|---------|---------|
| Object Type | Shaped data | `type User { id: ID! name: String! }` |
| Interface | Common contract | `interface Node { id: ID! }` |
| Union | One of multiple types | `union SearchResult = User \| Post \| Comment` |
| Enum | Fixed set of values | `enum Status { ACTIVE INACTIVE }` |
| Input Type | Mutation / query arguments | `input CreateUserInput { name: String! }` |
| Scalar | Leaf value | `scalar DateTime` |

### Nullable vs Non-Null

Use `!` (non-null) only when the field is guaranteed to be present whenever the object exists. Defaulting to nullable gives you more flexibility to return partial data on errors.

```graphql
type User {
  id: ID!          # Always present if user exists
  email: String!   # Always present
  deletedAt: DateTime  # Nullable — may not be set
  bio: String          # Nullable — user may not have set this
}
```

Do not over-non-null fields that might fail independently. If `user.posts` could fail (resolver error) but `user.name` is fine, a non-null `posts: [Post!]!` will null out the entire `user` in the response. Nullable `posts: [Post]` allows partial success.

### Interface and Union Usage

Use **interfaces** when types share common fields and logic:

```graphql
interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

type User implements Timestamped {
  id: ID!
  email: String!
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

Use **unions** when types have no shared fields but can appear in the same position:

```graphql
union SearchResult = User | Post | Product

type Query {
  search(query: String!): [SearchResult!]!
}
```

Implement Node interface for all entity types — required for Relay cursor pagination:

```graphql
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  # ...
}
```

### Input Types

Always use dedicated input types for mutations. Output types and input types have different requirements (inputs have no resolvers; required fields differ for create vs update):

```graphql
# Separate input per operation — required fields differ
input CreateUserInput {
  email: String!
  password: String!
  fullName: String!
}

input UpdateUserInput {
  fullName: String
  bio: String
}
```

Nest input types for complex operations:

```graphql
input CreateOrderInput {
  customerId: ID!
  items: [OrderItemInput!]!
  shippingAddress: AddressInput!
}

input OrderItemInput {
  productId: ID!
  quantity: Int!
}
```

## Queries, Mutations, and Subscriptions

### Root Operations

| Operation | Purpose | Idempotent |
|-----------|---------|-----------|
| `Query` | Read data — never has side effects | Yes |
| `Mutation` | Write data (create, update, delete) | No |
| `Subscription` | Real-time data stream | N/A |

### Mutation Design

Name mutations as `verb + Noun`:

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
  publishPost(id: ID!): PublishPostPayload!
}
```

Return a **payload type**, not the entity directly. Payload types allow returning both the mutated object and any errors:

```graphql
type CreateUserPayload {
  user: User          # null if creation failed
  errors: [UserError!]!
}

type UserError {
  field: String       # null for non-field errors
  code: String!
  message: String!
}
```

Always return the mutated object in the payload so clients can update their local cache without a follow-up query.

### Subscription Design

```graphql
type Subscription {
  orderStatusChanged(orderId: ID!): OrderStatusEvent!
  newMessage(channelId: ID!): Message!
}

type OrderStatusEvent {
  orderId: ID!
  newStatus: OrderStatus!
  timestamp: DateTime!
}
```

Subscriptions require a WebSocket transport. Use `graphql-ws` (the current standard) or Server-Sent Events for simpler use cases. Deliver the minimum event payload — let clients refetch full data if needed.

## The N+1 Problem

The N+1 problem is GraphQL's most common performance failure. It occurs when a list resolver fires once, then each item's sub-resolver fires N individual times — resulting in N+1 database queries instead of 2.

### How It Happens

```graphql
query {
  users(first: 10) {
    edges { node { id name posts { title } } }
  }
}
```

Naive resolver for `posts`:

```typescript
const resolvers = {
  User: {
    posts: (user) => db.posts.findMany({ where: { authorId: user.id } }),
    // This fires once per user — 10 users = 10 extra queries + 1 initial = 11 total
  }
};
```

### DataLoader: The Solution

DataLoader batches all loads within a single event loop tick, then deduplicates them:

```typescript
import DataLoader from 'dataloader';

// Batch function: receives an array of keys, must return array in same order
async function batchLoadPosts(userIds: readonly string[]): Promise<Post[][]> {
  const posts = await db.posts.findMany({
    where: { authorId: { in: [...userIds] } },
  });
  
  // Group by userId — must return results in same order as input userIds
  const postsByUserId = new Map<string, Post[]>();
  for (const post of posts) {
    const existing = postsByUserId.get(post.authorId) ?? [];
    postsByUserId.set(post.authorId, [...existing, post]);
  }
  
  return userIds.map(id => postsByUserId.get(id) ?? []);
}

// Create loaders — must be created per request, NOT as singletons
function createLoaders() {
  return {
    postsByUserId: new DataLoader(batchLoadPosts),
    userById: new DataLoader(batchLoadUsers),
  };
}
```

Attach loaders to the request context:

```typescript
// context.ts
export async function createContext({ req }: { req: Request }) {
  return {
    db,
    loaders: createLoaders(),  // Fresh loaders per request
    currentUser: await getUserFromToken(req.headers.authorization),
  };
}
```

Use in resolver:

```typescript
const resolvers = {
  User: {
    posts: (user, _args, ctx) => ctx.loaders.postsByUserId.load(user.id),
    // DataLoader batches all these loads — 10 users = 2 total queries
  }
};
```

DataLoader rules:
- Create a new DataLoader instance **per request**, never as a module-level singleton (caching must be request-scoped).
- The batch function must return results in the **same order** as the input keys array.
- DataLoader automatically deduplicates duplicate key requests within one batch.
- Use `.loadMany(ids)` when you need to load multiple keys at once from a parent.

## Pagination (Relay Cursor Connections Spec)

The Relay Connections spec defines a standard pagination shape that any Relay-compatible client understands without custom configuration. Implement it for all collection fields in your schema.

### Schema

```graphql
type Query {
  users(
    first: Int      # Forward: take N edges after `after`
    after: String   # Forward: cursor to start after
    last: Int       # Backward: take N edges before `before`
    before: String  # Backward: cursor to end before
  ): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int    # Optional — only add if UI requires it
}

type UserEdge {
  node: User!
  cursor: String!  # Opaque, base64-encoded position token
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

### Cursor Encoding

```typescript
function encodeCursor(item: { id: string; createdAt: Date }): string {
  return Buffer.from(
    JSON.stringify({ id: item.id, createdAt: item.createdAt.toISOString() })
  ).toString('base64url');
}

function decodeCursor(cursor: string): { id: string; createdAt: string } {
  return JSON.parse(Buffer.from(cursor, 'base64url').toString('utf8'));
}
```

Never expose raw database IDs or offsets as cursors — encode them opaquely.

### totalCount Trade-Off

`totalCount` requires a separate `COUNT(*)` query. Only add it when the UI genuinely needs "Showing 20 of 847 results." For infinite scroll or next/previous navigation, `hasNextPage` is sufficient.

## Query Complexity and Depth Limits

Without limits, a malicious client can craft deeply nested queries that exhaust server resources:

```graphql
# This can trigger millions of resolvers
{ users { friends { friends { friends { friends { posts { comments { author { friends { ... } } } } } } } } } }
```

### Depth Limiting

```typescript
import depthLimit from 'graphql-depth-limit';

const server = new ApolloServer({
  validationRules: [depthLimit(7)],  // Reject queries more than 7 levels deep
});
```

### Cost Analysis

Assign a cost to each field; reject queries whose total cost exceeds a budget:

```typescript
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  validationRules: [
    createComplexityLimitRule(1000, {
      scalarCost: 0,
      objectCost: 1,
      listFactor: 10,   // Lists multiply child costs
    }),
  ],
});
```

### Disable Introspection in Production

Schema introspection lets anyone map your entire API surface. Disable it in production:

```typescript
const server = new ApolloServer({
  introspection: process.env.NODE_ENV !== 'production',
});
```

## Error Handling

GraphQL responses can contain both `data` and `errors` simultaneously — this is partial success:

```json
{
  "data": {
    "user": { "id": "1", "name": "Alice" },
    "posts": null
  },
  "errors": [
    {
      "message": "Failed to load posts",
      "path": ["posts"],
      "extensions": {
        "code": "INTERNAL_SERVER_ERROR",
        "http": { "status": 500 }
      }
    }
  ]
}
```

Always include a machine-readable `code` in `extensions`. Never return raw exception messages — mask them in production:

```typescript
import { GraphQLError } from 'graphql';

// In resolver
throw new GraphQLError('User not found', {
  extensions: {
    code: 'NOT_FOUND',
    http: { status: 404 },
  },
});
```

Mask unexpected server errors using `formatError` in your GraphQL server setup — catch `INTERNAL_SERVER_ERROR` codes and replace the message with a safe generic string before it reaches the client.

## Schema Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `data: JSON` scalar for arbitrary objects | No type safety; no IDE support | Define specific object types |
| Output type used as input type | Fields don't match (no `id` on create) | Separate `CreateXInput` and `UpdateXInput` types |
| `Boolean` flags like `isAdmin`, `isVerified` | Doesn't scale beyond two states | `enum Role { USER ADMIN }`, `enum VerificationStatus { PENDING VERIFIED }` |
| Non-null list with potentially-failing items | Single item failure nulls entire parent | `[Post]` instead of `[Post!]!` on unreliable lists |
| Mutation returns `Boolean` | Client cannot update cache | Return payload type with mutated object |
| Fetching all fields in resolver when client requests few | Wasteful DB query | Check `info.fieldNodes` or use field-aware ORM |
| N+1 resolvers without DataLoader | 1 query → N+1 queries at scale | Always use DataLoader for sub-entity loading |
| Module-level DataLoader singleton | Shares cache across requests; stale data | Create fresh DataLoader instances per request |
