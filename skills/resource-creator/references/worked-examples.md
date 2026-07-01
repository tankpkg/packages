# Worked Resource Examples

Sources: Tank specification (AGENTS.md), quality-gate bundle reference
implementation, production bundle patterns

Covers: four complete resource atom examples with full tank.json manifests,
showing project context resources, style guide resources, config resources,
and agent+resource combos. Each example includes rationale, the resource
atom, the full manifest, and usage notes.

## Example 1: Project Context Resource

### Scenario

A monorepo has 50+ packages. Agents working in the repo need to understand
module boundaries, ownership, and data flow -- but only when navigating
across modules. Injecting this map into every prompt wastes tokens.

### The Resource File

Create `references/architecture.md` in the bundle:

```markdown
# Project Architecture

## Module Boundaries

| Module        | Owner       | Purpose                    | Dependencies         |
| ------------- | ----------- | -------------------------- | -------------------- |
| @app/api      | backend     | REST API gateway           | @app/db, @app/auth   |
| @app/web      | frontend    | Next.js web application    | @app/ui, @app/api    |
| @app/ui       | frontend    | Shared component library   | none                 |
| @app/db       | backend     | Database models and queries| none                 |
| @app/auth     | backend     | Authentication service     | @app/db              |

## Data Flow

API requests: @app/web -> @app/api -> @app/auth -> @app/db
UI components: @app/web imports from @app/ui
```

### The Resource Atom

```json
{
  "kind": "resource",
  "uri": "tank://context/architecture",
  "name": "project-architecture",
  "description": "Module boundaries, ownership, dependencies, and data flow for the monorepo"
}
```

### Full tank.json

```json
{
  "name": "@tank/monorepo-context",
  "version": "1.0.0",
  "description": "Project architecture context for monorepo navigation.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "resource",
      "uri": "tank://context/architecture",
      "name": "project-architecture",
      "description": "Module boundaries, ownership, dependencies, and data flow for the monorepo"
    }
  ]
}
```

### Why Resource, Not Instruction

The architecture map is 30+ lines and only relevant when the agent works
across module boundaries. On single-module tasks (most tasks), it adds
noise. As a resource, it costs zero tokens until the agent actually needs
cross-module context.

### Usage Pattern

An agent or instruction references the resource by name. The adapter
resolves `tank://context/architecture` to the bundled file.

---

## Example 2: Style Guide Resource

### Scenario

A frontend team enforces specific TypeScript and CSS conventions. A code
reviewer agent needs these conventions as reference material, but other
agents in the bundle (linters, formatters) do not.

### The Resource File

Create `references/style-guide.md` in the bundle:

```markdown
# Frontend Style Guide

## TypeScript

- Prefer `interface` over `type` for object shapes.
- Use `unknown` instead of `any` -- narrow with type guards.
- Name boolean variables with `is`, `has`, `should` prefixes.
- Export types separately: `export type { UserProps }`.
- Maximum function length: 30 lines.

## CSS / Tailwind

- Use semantic color tokens: `text-primary` not `text-blue-600`.
- Mobile-first: start with `sm:` breakpoints.
- No arbitrary values in Tailwind: define tokens in `tailwind.config`.
- Component styles in co-located `.module.css` files.

## Naming

- Components: PascalCase (`UserCard.tsx`).
- Hooks: camelCase with `use` prefix (`useAuth.ts`).
- Utils: camelCase (`formatDate.ts`).
- Constants: SCREAMING_SNAKE (`MAX_RETRIES`).
```

### The Resource Atom

```json
{
  "kind": "resource",
  "uri": "tank://guides/code-style",
  "name": "code-style-guide",
  "description": "TypeScript and CSS/Tailwind conventions for the frontend team"
}
```

### Full tank.json

```json
{
  "name": "@tank/frontend-standards",
  "version": "1.0.0",
  "description": "Frontend coding standards with style-aware code review.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "resource",
      "uri": "tank://guides/code-style",
      "name": "code-style-guide",
      "description": "TypeScript and CSS/Tailwind conventions for the frontend team"
    },
    {
      "kind": "agent",
      "name": "style-reviewer",
      "role": "Review modified files for style guide violations. Read the code-style-guide resource first, then check each file against the conventions. Report violations with file, line, and the specific rule broken.",
      "tools": ["read", "grep", "glob"],
      "model": "fast",
      "readonly": true
    }
  ]
}
```

### Why a Resource+Agent Combo

The style guide is only needed by the reviewer agent, not by every agent
in the system. Making it a resource means:

1. The reviewer reads it once per review session.
2. Other agents never load it.
3. The guide can be updated independently of the reviewer's role prompt.

The agent's `role` explicitly tells it to read the resource first. This
is the recommended pattern -- do not rely on the agent discovering the
resource on its own.

---

## Example 3: Config Resource

### Scenario

A deployment bundle needs environment-specific configuration. The config
varies between staging and production but the bundle logic is identical.
The config includes feature flags, API endpoints, and rate limits.

### The Resource Atom (Dynamic)

```json
{
  "kind": "resource",
  "uri": "file://./config/environment.json",
  "name": "env-config",
  "description": "Environment-specific configuration: feature flags, API endpoints, rate limits"
}
```

### The Config File

At `./config/environment.json` in the project (not the package):

```json
{
  "environment": "staging",
  "features": {
    "dark_mode": true,
    "beta_api": false,
    "new_checkout": true
  },
  "endpoints": {
    "api": "https://staging-api.example.com",
    "auth": "https://staging-auth.example.com"
  },
  "limits": {
    "requests_per_minute": 100,
    "max_upload_mb": 25
  }
}
```

### Full tank.json

```json
{
  "name": "@tank/deploy-config",
  "version": "1.0.0",
  "description": "Environment-aware deployment configuration resource.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["./config/**", "**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    },
    {
      "kind": "resource",
      "uri": "file://./config/environment.json",
      "name": "env-config",
      "description": "Environment-specific feature flags, API endpoints, and rate limits"
    }
  ]
}
```

### Why file:// Instead of tank://

The config file lives in the **project**, not the **package**. It changes
per environment without requiring a new package version. Using `file://`
means the resource resolves to whatever config is present in the current
working directory.

### Permission Note

The `filesystem.read` permission explicitly includes `./config/**` to
cover the config file location. The default `**/*` glob would also match,
but being explicit documents intent and allows tighter scoping in
security-sensitive environments.

---

## Example 4: Agent+Resource Combo (API Validator)

### Scenario

A backend team needs automated API contract validation. An agent reads the
API schema and error code catalog, then validates that new API endpoints
conform to the contract. This is the most sophisticated resource pattern:
multiple resources feeding a single specialized agent.

### The Resource Files

`references/api-schema.md`:

```markdown
# API Schema Contract

## Authentication

All endpoints require Bearer token in Authorization header.
Rate limit: 100 requests/minute per token.

## Standard Response Envelope

Every response must follow this structure:

{ "data": <payload>, "meta": { "request_id": "<uuid>", "timestamp": "<iso8601>" } }

Error responses:

{ "error": { "code": "<ERROR_CODE>", "message": "<human readable>", "details": {} } }

## Endpoint Conventions

- Resource URLs: plural nouns (`/users`, `/orders`).
- Actions: POST to `/users/{id}/actions/{action-name}`.
- Pagination: `?page=1&per_page=20`, response includes `meta.total`.
- Filtering: `?filter[status]=active&filter[role]=admin`.
- Sorting: `?sort=-created_at` (prefix `-` for descending).
```

`references/error-codes.md`:

```markdown
# Error Code Catalog

## Client Errors (4xx)

| Code              | HTTP Status | Description                    |
| ----------------- | ----------- | ------------------------------ |
| AUTH_EXPIRED      | 401         | Token has expired              |
| AUTH_INVALID      | 401         | Token is malformed or invalid  |
| FORBIDDEN         | 403         | Valid token, insufficient role  |
| NOT_FOUND         | 404         | Resource does not exist         |
| VALIDATION_FAILED | 422         | Request body failed validation  |
| RATE_LIMITED      | 429         | Too many requests              |

## Server Errors (5xx)

| Code              | HTTP Status | Description                    |
| ----------------- | ----------- | ------------------------------ |
| INTERNAL          | 500         | Unexpected server error        |
| SERVICE_UNAVAILABLE | 503       | Dependency is down             |
| TIMEOUT           | 504         | Upstream request timed out     |
```

### The Resource Atoms

```json
{
  "kind": "resource",
  "uri": "tank://schemas/api-contract",
  "name": "api-schema",
  "description": "API response envelope, endpoint conventions, pagination, filtering, and sorting standards"
},
{
  "kind": "resource",
  "uri": "tank://data/error-codes",
  "name": "error-catalog",
  "description": "Standard error codes with HTTP status mappings for client and server errors"
}
```

### Full tank.json

```json
{
  "name": "@tank/api-contract-validator",
  "version": "1.0.0",
  "description": "Validate API implementations against schema and error contracts.",
  "permissions": {
    "network": { "outbound": [] },
    "filesystem": { "read": ["**/*"], "write": [] },
    "subprocess": false
  },
  "repository": "https://github.com/tankpkg/packages",
  "atoms": [
    {
      "kind": "resource",
      "uri": "tank://schemas/api-contract",
      "name": "api-schema",
      "description": "API response envelope, endpoint conventions, pagination, filtering, sorting"
    },
    {
      "kind": "resource",
      "uri": "tank://data/error-codes",
      "name": "error-catalog",
      "description": "Standard error codes with HTTP status mappings"
    },
    {
      "kind": "agent",
      "name": "api-validator",
      "role": "Validate API route implementations against the project contract. Read the api-schema resource for endpoint conventions and the error-catalog resource for error code standards. For each route file, check: response envelope structure, error code usage, pagination implementation, and naming conventions. Report violations with file, line, severity (critical/high/medium), and the specific contract rule broken.",
      "tools": ["read", "grep", "glob"],
      "model": "balanced",
      "readonly": true
    },
    {
      "kind": "instruction",
      "content": "./SKILL.md"
    }
  ]
}
```

### Composition Anatomy

The instruction provides behavioral context (always loaded). The resources
provide reference data (loaded when the agent reads them). The agent
orchestrates the validation using both.

### Key Design Decisions

1. **Two resources, not one.** The API schema and error catalog are
   distinct concerns. Splitting them means a future "error code linter"
   agent can reuse the error-catalog resource without pulling the full
   API schema.

2. **Agent references resources by name.** The `role` field explicitly
   names both resources. This removes ambiguity about which resources
   the agent should read.

3. **readonly: true.** The validator only reads and reports -- it does
   not modify files. This permission constraint is enforced by the
   adapter.

4. **model: balanced.** Schema validation requires reasoning about
   structure, not just pattern matching. The `fast` tier would miss
   subtle contract violations.

## Pattern Summary

| Example               | Resource Scheme | Agent Combo | Key Pattern                     |
| --------------------- | --------------- | ----------- | ------------------------------- |
| Project Context       | `tank://`       | No          | Standalone reference data       |
| Style Guide           | `tank://`       | Yes         | Single resource + reviewer      |
| Config                | `file://`       | No          | Dynamic environment data        |
| API Validator         | `tank://`       | Yes         | Multiple resources + validator  |

## Checklist for New Resources

| Check                                           | Required |
| ----------------------------------------------- | -------- |
| Content fits resource (not instruction) model   | Yes      |
| URI follows naming conventions                  | Yes      |
| URI scheme matches data location                | Yes      |
| `name` set if referenced by agent/hook          | Yes      |
| `description` set if multiple resources exist   | Yes      |
| Permissions cover the URI scheme access pattern  | Yes      |
| A consuming agent or hook exists                | Yes      |
| Resource content under 500 lines                | Yes      |
