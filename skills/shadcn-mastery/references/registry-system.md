# Registry System

Sources: shadcn/ui registry documentation (ui.shadcn.com 2025-2026), shadcn/ui registry schema specification, shadcn-ui/ui GitHub repository

Covers: registry architecture, registry.json schema, registry-item.json schema, building a custom registry, namespaces, authentication, distributing components, MCP server integration, registry examples.

## What Is the Registry

The shadcn registry is a code distribution system. It defines a flat-file schema for components, hooks, utilities, pages, and configuration files, plus a CLI to install them across projects.

The default shadcn/ui registry lives at `ui.shadcn.com`. Custom registries allow teams to distribute their own components, design system extensions, and application blocks via the same CLI.

### Registry Capabilities

| Feature | Description |
|---------|-------------|
| Component distribution | Share UI components across projects and teams |
| Dependency resolution | Automatically install required components and npm packages |
| Cross-framework support | Works with React, Vue, Svelte, and other frameworks |
| Private registries | Authenticated access for internal design systems |
| Namespaced installation | Install from multiple registries with `@namespace/component` syntax |
| AI integration | Schema is AI-readable for component generation and modification |

## Building a Custom Registry

### Step 1: Create registry.json

Define the registry manifest at the project root:

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry.json",
  "name": "acme-ui",
  "homepage": "https://ui.acme.com",
  "items": [
    {
      "name": "fancy-button",
      "type": "registry:ui",
      "title": "Fancy Button",
      "description": "An animated button with gradient hover effects.",
      "dependencies": ["framer-motion"],
      "registryDependencies": ["button"],
      "files": [
        {
          "path": "registry/fancy-button.tsx",
          "type": "registry:ui",
          "target": "components/ui/fancy-button.tsx"
        }
      ]
    }
  ]
}
```

### Step 2: Create Component Files

Place component source files in a `registry/` directory:

```
project/
  registry.json
  registry/
    fancy-button.tsx
    data-grid.tsx
    use-debounce.ts
```

### Step 3: Build Registry JSON

```bash
npx shadcn@latest build
```

This reads `registry.json` and generates individual JSON files in `public/r/`:

```
public/r/
  fancy-button.json
  data-grid.json
  use-debounce.json
```

Customize the output directory:

```bash
npx shadcn@latest build --output ./custom-registry
```

### Step 4: Deploy

Host the `public/r/` directory on any static file server, CDN, or behind an API. The CLI fetches `{registry-url}/{name}.json` for each component.

## registry.json Schema

Top-level manifest that declares all registry items:

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry.json",
  "name": "string",
  "homepage": "string (optional)",
  "items": [
    {
      "name": "string (required)",
      "type": "string (required)",
      "title": "string (optional)",
      "description": "string (optional)",
      "dependencies": ["string (npm packages)"],
      "devDependencies": ["string (npm dev packages)"],
      "registryDependencies": ["string (other registry items)"],
      "files": [
        {
          "path": "string (source path)",
          "type": "string (file type)",
          "target": "string (installation target, optional)"
        }
      ],
      "tailwind": {
        "config": {}
      },
      "cssVars": {
        "light": {},
        "dark": {}
      },
      "meta": {}
    }
  ]
}
```

### Item Types

| Type | Purpose | Installation Target |
|------|---------|-------------------|
| `registry:ui` | UI component | `components/ui/` |
| `registry:component` | Application component | `components/` |
| `registry:hook` | React hook | `hooks/` |
| `registry:lib` | Utility function | `lib/` |
| `registry:block` | Page-level block or template | `components/` or app directory |
| `registry:page` | Full page | App directory |
| `registry:file` | Config file (eslint, tailwind, etc.) | Project root or specified target |
| `registry:theme` | Theme configuration | CSS file |

### Dependencies vs Registry Dependencies

- `dependencies`: npm packages installed via the package manager (`framer-motion`, `date-fns`)
- `registryDependencies`: other registry items resolved first (`button`, `dialog`, `input`)

The CLI installs registry dependencies recursively before the requested item.

## registry-item.json Schema

Each built item produces a JSON file consumed by the CLI:

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry-item.json",
  "name": "fancy-button",
  "type": "registry:ui",
  "title": "Fancy Button",
  "description": "An animated button with gradient hover effects.",
  "dependencies": ["framer-motion"],
  "registryDependencies": ["button"],
  "files": [
    {
      "path": "components/ui/fancy-button.tsx",
      "type": "registry:ui",
      "content": "// Full component source code here..."
    }
  ],
  "tailwind": {},
  "cssVars": {
    "light": {},
    "dark": {}
  }
}
```

The `content` field contains the full file source. The CLI writes this content to the target path.

## Namespaces

Namespaces scope registries so components from different sources do not conflict.

### Consumer Configuration

In `components.json`:

```json
{
  "registries": {
    "acme": {
      "url": "https://ui.acme.com/r/{name}.json"
    },
    "internal": {
      "url": "https://registry.internal.company.com/r/{name}.json",
      "headers": {
        "Authorization": "Bearer ${REGISTRY_TOKEN}"
      }
    }
  }
}
```

### Installation with Namespaces

```bash
# From the default shadcn registry
npx shadcn@latest add button

# From the acme namespace
npx shadcn@latest add @acme/fancy-button

# From the internal namespace
npx shadcn@latest add @internal/data-grid
```

### Multiple Registry Setup Example

```json
{
  "registries": {
    "acme": {
      "url": "https://ui.acme.com/r/{name}.json"
    },
    "team": {
      "url": "https://team.company.com/r/v2/{name}.json",
      "headers": {
        "X-API-Key": "${TEAM_REGISTRY_KEY}"
      }
    }
  }
}
```

## Authentication

For private registries requiring authentication:

### Header-Based Authentication

```json
{
  "registries": {
    "private": {
      "url": "https://private-registry.com/r/{name}.json",
      "headers": {
        "Authorization": "Bearer ${PRIVATE_REGISTRY_TOKEN}"
      }
    }
  }
}
```

Environment variables in `${VAR_NAME}` format are expanded from the shell environment at runtime.

### Token Sources

| Method | Setup |
|--------|-------|
| Environment variable | `export PRIVATE_REGISTRY_TOKEN=xxx` in shell |
| `.env` file | Add to `.env.local` (not committed to git) |
| CI/CD secret | Configure in GitHub Actions, GitLab CI, etc. |

## Registry Item Examples

### UI Component

```json
{
  "name": "status-badge",
  "type": "registry:ui",
  "dependencies": [],
  "registryDependencies": ["badge"],
  "files": [
    {
      "path": "registry/status-badge.tsx",
      "type": "registry:ui",
      "target": "components/ui/status-badge.tsx"
    }
  ]
}
```

### Hook

```json
{
  "name": "use-debounce",
  "type": "registry:hook",
  "files": [
    {
      "path": "registry/use-debounce.ts",
      "type": "registry:hook",
      "target": "hooks/use-debounce.ts"
    }
  ]
}
```

### Block (Page Section)

```json
{
  "name": "login-form",
  "type": "registry:block",
  "registryDependencies": ["button", "input", "label", "card"],
  "files": [
    {
      "path": "registry/login-form.tsx",
      "type": "registry:component",
      "target": "components/login-form.tsx"
    }
  ]
}
```

### Theme

```json
{
  "name": "ocean-theme",
  "type": "registry:theme",
  "cssVars": {
    "light": {
      "primary": "oklch(0.55 0.15 230)",
      "primary-foreground": "oklch(0.98 0.01 230)"
    },
    "dark": {
      "primary": "oklch(0.75 0.12 230)",
      "primary-foreground": "oklch(0.15 0.02 230)"
    }
  },
  "files": []
}
```

## MCP Server

shadcn provides an MCP (Model Context Protocol) server for AI-powered registry operations:

```bash
npx shadcn@latest mcp
```

The MCP server exposes registry items to AI tools, enabling:
- AI-driven component discovery and installation
- Automated component generation following registry schema
- Design system enforcement through AI assistants

Configure the MCP server endpoint in your registry for AI integration:

```json
{
  "name": "acme-ui",
  "mcp": {
    "url": "https://ui.acme.com/mcp"
  },
  "items": [...]
}
```

## Distribution Workflow

1. Define components in `registry.json`
2. Write component source in `registry/` directory
3. Run `npx shadcn@latest build` to generate JSON
4. Deploy `public/r/` to a static host or CDN
5. Consumers add the registry namespace to their `components.json`
6. Consumers install with `npx shadcn@latest add @namespace/component`
7. The CLI resolves dependencies, downloads source, and writes files

For teams: maintain the registry in a separate repository or monorepo package. Run `shadcn build` in CI to validate the registry on every push.
