# API Versioning

Sources: RFC 8594 (Sunset Header, 2019), RFC 7231 (HTTP Content Negotiation), IETF API versioning practices, Stripe Engineering Blog (public), Semantic Versioning specification (semver.org)

Covers: breaking vs non-breaking change classification, versioning strategies (URL path, header, media type), deprecation workflow, Sunset header, API lifecycle management.

## Breaking vs Non-Breaking Changes

Before choosing a versioning strategy, develop precise intuition for what constitutes a breaking change. Most changes can be made without a new version.

### Breaking Changes — Require a New Version

| Change | Example | Why It Breaks Clients |
|--------|---------|----------------------|
| Removing a field | Deleting `user.middle_name` | Clients reading that field get `undefined` |
| Renaming a field | `name` → `full_name` | Clients using the old name get no data |
| Changing a field's type | `age: number` → `age: string` | Client-side type assumptions fail |
| Narrowing enum values | Removing `"PENDING"` from `status` | Client switch/match statements miss the case |
| Removing an endpoint | Deleting `GET /profiles` | Clients receive 404 or 410 |
| Changing URL structure | `/users/{id}` → `/members/{id}` | Client URL construction breaks |
| Making an optional field required | `phone` becomes required | Old clients not sending it receive 422 |
| Changing HTTP method for existing operation | `GET /search` → `POST /search` | Clients using GET receive 405 |
| Changing error codes clients may check | `USER_NOT_FOUND` → `RESOURCE_NOT_FOUND` | Client conditional logic breaks |

### Non-Breaking Changes — Safe Without a New Version

| Change | Why It's Safe |
|--------|--------------|
| Adding a new field to a response | Clients following the Tolerant Reader pattern ignore unknown fields |
| Adding a new optional query parameter | Old clients don't send it; server uses a sensible default |
| Adding a new endpoint | Old clients don't know it exists |
| Adding a new enum value | Old clients treat it as an unknown value (handle gracefully in client code) |
| Making a required field optional | Old clients still send it; new clients can omit it |
| Reducing a rate limit (looser) | Old clients get more capacity |
| Bug fixes that don't change the contract | Behavior correction that matches the documented spec |

### Tolerant Reader Pattern

Design clients to tolerate unknown fields and new enum values. Parse only what you need; discard the rest. Clients that break on new fields force API providers into unnecessary major versions.

## Versioning Strategies

### URL Path Versioning

```
GET /v1/users/42
GET /v2/users/42
```

Embed the version in the URL path prefix. This is the most common approach for public APIs.

Advantages:
- Explicit and visible in logs, browser address bar, and API documentation
- Easy to test without special tooling
- CDN-cacheable without `Vary` headers
- Routers and load balancers can direct by prefix

Disadvantages:
- Version is coupled to the URL, which REST purists argue should be a stable resource identifier
- Every bookmark and stored link must be updated on version change

Use for: public APIs, most production APIs.

### Header Versioning

```http
GET /users/42
Accept-Version: 2
```

Or with a custom header:

```http
GET /users/42
X-API-Version: 2024-01-15
```

Version is request metadata, not part of the resource identifier.

Advantages: Clean URLs that don't change between versions.

Disadvantages:
- Harder to test (requires setting a custom header; can't just paste a URL)
- Not CDN-cacheable without `Vary: Accept-Version` header, which many CDNs handle poorly
- Less visible in error messages and logs

Use for: internal APIs where clients are controlled, APIs without CDN caching requirements.

### Media Type Versioning (Content Negotiation)

```http
GET /users/42
Accept: application/vnd.example.v2+json
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/vnd.example.v2+json
```

Advantages: Follows the HTTP specification's intent for content negotiation.

Disadvantages: Verbose, unusual outside hypermedia APIs, poor tooling support, confusing for new API consumers.

Use for: specialized hypermedia APIs where protocol purity matters.

### Strategy Comparison

| Strategy | Visibility | CDN-Cacheable | Browser-Testable | Common Usage |
|---------|-----------|--------------|-----------------|-------------|
| URL path `/v2/` | High | Yes | Yes | Most public APIs |
| Header `Accept-Version` | Low | With `Vary` | No | Internal APIs |
| Media type `vnd.+json` | Medium | With `Vary` | No | Rarely |
| Query param `?version=2` | High | Poor | Yes | Avoid |

Do not use query parameter versioning. It pollutes the resource identity and interacts poorly with caches.

## Version Numbering

### Integer Versions

Increment the version number only for breaking changes:

```
v1 → v2 → v3
```

Integer versions work well when the API surface is stable and versions represent significant, distinct generations. GitHub, Stripe legacy, and most REST APIs use this model.

### Date-Based Versions

Stripe's current model uses the API key's creation date as the version:

```
2024-01-15
2024-06-01
2024-11-01
```

Each client is pinned to a specific date snapshot. New features appear in the latest date. Old date snapshots freeze their behavior. Clients upgrade on their own schedule by updating the version date.

This model works well for APIs that evolve frequently in small increments rather than large breaking changes. The infrastructure cost is higher — the server must maintain behavior for every active version date.

### What to Version

Version the API surface, not implementation details. A new version is warranted when the contract changes — what fields exist, what operations are available, what types fields have.

## Deprecation Workflow

### Step 1: Announce

Before deprecating anything:
- Publish a changelog entry describing what's deprecated and why
- Document the migration path: what clients should use instead
- Set a concrete sunset date (minimum 6 months for external clients; 12+ months for widely-used APIs)
- Email API consumers if you have contact information

### Step 2: Add Deprecation Signals in Responses

Use RFC 8594 `Sunset` header to signal when the endpoint or version will stop responding:

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jan 2025 00:00:00 GMT
Link: <https://docs.example.com/migration/v2>; rel="successor-version"
```

For deprecated fields within a response, use a `_deprecated` metadata object:

```json
{
  "user_name": "Alice",
  "full_name": "Alice Smith",
  "_deprecated": {
    "user_name": "Deprecated. Use full_name instead. Removed: 2025-01-01."
  }
}
```

In GraphQL, use the built-in `@deprecated` directive:

```graphql
type User {
  userName: String @deprecated(reason: "Use fullName. Removed 2025-Q1.")
  fullName: String!
}
```

### Step 3: Monitor and Contact

Track requests to deprecated endpoints and fields:
- Log usage per API key / client ID
- Build a dashboard: "% of traffic still on deprecated version"
- Contact clients with high request volumes directly — don't wait for them to discover the sunset

### Step 4: Sunset

On the sunset date, return `410 Gone` (not `404`):

```http
HTTP/1.1 410 Gone
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/endpoint-removed",
  "title": "Endpoint Removed",
  "status": 410,
  "detail": "The v1 users endpoint was removed on 2025-01-01. Migrate to /v2/users. See https://docs.example.com/migration/v2."
}
```

Keep the 410 response permanently — don't recycle old version URLs for new purposes.

## API Lifecycle Stages

| Stage | Behavior | Client Expectations |
|-------|---------|-------------------|
| Preview / Beta | May change without notice | Labeled as beta; not for production |
| Stable | Breaking changes require new version + deprecation period | Safe to depend on in production |
| Deprecated | Still functional; sunset date announced and enforced | Must migrate by sunset date |
| Sunset | Returns 410 Gone | No longer functional |

Mark lifecycle stage in documentation and in the API response if useful:

```http
X-API-Stage: deprecated
Sunset: Sat, 01 Jan 2025 00:00:00 GMT
```

## Running Multiple Versions

While deprecation is in effect, run old and new versions in parallel:

```
/v1/* → v1 handler (until sunset date)
/v2/* → v2 handler (current)
```

Avoid reimplementing v1 in terms of v2 when the semantics changed significantly — divergent implementations are easier to reason about and delete.

Keep an internal changelog of what changed between each version. When you sunset v1, delete its code entirely.

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Versioning every non-breaking change | Unnecessary migration burden on clients | Only version breaking changes |
| No sunset date on deprecation | Clients delay indefinitely | Set and publicly commit to a date |
| Removing a version without a replacement | Clients are blocked with no path forward | Always document the migration path before sunsetting |
| Different versioning strategy per endpoint | Inconsistent, confusing | One strategy, applied uniformly |
| Version numbers in field names (`name_v2`) | Leaks implementation into the contract | Version the API, not individual fields |
| Treating a bug fix as non-breaking when clients depend on the buggy behavior | Breaks clients who adapted to the bug | Announce the fix, document it, give migration time |
