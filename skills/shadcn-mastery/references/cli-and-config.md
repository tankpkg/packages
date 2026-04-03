# CLI and Configuration

Sources: shadcn/ui official documentation (ui.shadcn.com 2025-2026), shadcn-ui/ui GitHub repository, Tailwind CSS v4 documentation

Covers: CLI commands (init, add, view, search, build, migrate), components.json schema and configuration options, path aliases, Tailwind CSS v3 vs v4 setup, monorepo configuration.

## CLI Overview

shadcn/ui ships a CLI (`shadcn`) that copies component source code into the project. Components are not installed as npm dependencies -- they become owned source files.

### init

Initialize a new project with shadcn/ui configuration:

```bash
npx shadcn@latest init
```

The init command:
1. Installs dependencies (`tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`)
2. Creates the `cn` utility function
3. Generates `components.json` with project configuration
4. Sets up CSS variables in `globals.css`

Options:

| Flag | Purpose |
|------|---------|
| `-d, --defaults` | Skip prompts, use default configuration |
| `-f, --force` | Force overwrite of existing configuration |
| `-s, --silent` | Suppress output |
| `-y, --yes` | Accept all prompts |
| `--src-dir` | Use the `src` directory |

The `create` command is an alias for `init`.

### add

Add components, hooks, and utilities to the project:

```bash
npx shadcn@latest add button dialog input
```

Multiple components can be added in a single command. The CLI resolves and installs all dependencies.

Options:

| Flag | Purpose |
|------|---------|
| `-o, --overwrite` | Overwrite existing files |
| `-a, --all` | Add all available components |
| `-p, --path <path>` | Custom path for component installation |
| `-s, --silent` | Suppress output |

### view

Preview registry items before installing:

```bash
npx shadcn@latest view button
npx shadcn@latest view button dialog
npx shadcn@latest view @acme/fancy-button
```

Use `view` to inspect component source code, dependencies, and structure before committing to installation.

### search

Search for items across registries:

```bash
npx shadcn@latest search
npx shadcn@latest search "date picker"
npx shadcn@latest search -r @acme
```

The `list` command is an alias for `search`.

### build

Generate registry JSON files from a `registry.json` manifest:

```bash
npx shadcn@latest build
npx shadcn@latest build --output ./custom-dir
```

Reads `registry.json` and outputs registry item JSON files to `public/r/` by default.

### migrate

Run automated migrations on existing components:

```bash
npx shadcn@latest migrate icons
npx shadcn@latest migrate radix
npx shadcn@latest migrate rtl
```

Available migrations:

| Migration | Effect |
|-----------|--------|
| `icons` | Switch icon library across all UI components |
| `radix` | Convert `@radix-ui/react-*` imports to unified `radix-ui` package |
| `rtl` | Convert physical CSS properties to logical equivalents (`ml-4` to `ms-4`) |

Migrate specific files with glob patterns:

```bash
npx shadcn@latest migrate rtl "src/components/**/*.tsx"
```

### docs

Fetch component documentation and API references:

```bash
npx shadcn@latest docs button
```

### info

Display project configuration and environment details:

```bash
npx shadcn@latest info
```

## components.json Schema

The `components.json` file configures how the CLI generates and places components. It is only required when using the CLI (not for manual copy-paste).

### Complete Schema

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "rsc": true,
  "tsx": true,
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "registries": {}
}
```

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `style` | `"new-york"` | Component style. The `default` style is deprecated. |
| `tailwind.config` | string | Path to `tailwind.config.js`. Leave blank for Tailwind v4. |
| `tailwind.css` | string | Path to the CSS file importing Tailwind. |
| `tailwind.baseColor` | string | Base color palette: `neutral`, `stone`, `zinc`, `mauve`, `olive`, `mist`, `taupe`. |
| `tailwind.cssVariables` | boolean | `true` for CSS variable theming (recommended), `false` for inline utilities. |
| `tailwind.prefix` | string | Prefix for Tailwind utility classes (e.g., `tw-`). |
| `rsc` | boolean | Add `"use client"` directive to client components when true. |
| `tsx` | boolean | Generate `.tsx` (true) or `.jsx` (false) files. |
| `aliases.components` | string | Import alias for components directory. |
| `aliases.utils` | string | Import alias for utility functions. |
| `aliases.ui` | string | Import alias for UI components. Controls where `ui` components install. |
| `aliases.lib` | string | Import alias for lib functions (`format-date`, `generate-id`). |
| `aliases.hooks` | string | Import alias for hooks (`use-media-query`, `use-toast`). |

Fields marked as "cannot be changed after initialization": `style`, `tailwind.baseColor`, `tailwind.cssVariables`. To switch these, delete and re-install components.

### Path Alias Setup

Aliases in `components.json` must match `tsconfig.json` paths:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

If using the `src` directory, ensure it is included under `paths`.

## Tailwind CSS v3 vs v4

### Tailwind v3 Configuration

For Tailwind v3 projects, specify the config file path:

```json
{
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "app/globals.css",
    "cssVariables": true
  }
}
```

### Tailwind v4 Configuration

For Tailwind v4 projects, leave `tailwind.config` blank:

```json
{
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "cssVariables": true
  }
}
```

Tailwind v4 uses CSS-first configuration. Theme tokens are exposed via `@theme inline` in the CSS file instead of `tailwind.config.js`:

```css
@import "tailwindcss";

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}
```

## Monorepo Setup

### Creating a Monorepo Project

```bash
npx shadcn@latest init --monorepo
```

Select a template (Turborepo-based). This creates `apps/web` and `packages/ui` workspaces.

### Adding Components in Monorepo

Run the `add` command from the app directory:

```bash
cd apps/web
npx shadcn@latest add button
```

The CLI detects the monorepo structure and installs:
- UI primitives (`button`, `input`, `card`) in `packages/ui`
- Page-level blocks (`login-form`) in `apps/web/components`
- Dependencies in the correct workspace `package.json`

### Importing in Monorepo

```typescript
import { Button } from "@workspace/ui/components/button"
import { cn } from "@workspace/ui/lib/utils"
import { useMediaQuery } from "@workspace/ui/hooks/use-media-query"
```

### Monorepo Requirements

1. Every workspace must have its own `components.json`
2. Aliases must match workspace-specific paths
3. `style`, `iconLibrary`, and `baseColor` must be identical across workspaces
4. For Tailwind v4, leave `tailwind.config` empty in all `components.json` files

Example `packages/ui/components.json`:

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "tailwind": {
    "config": "",
    "css": "src/styles/globals.css",
    "cssVariables": true
  },
  "aliases": {
    "components": "@workspace/ui/components",
    "utils": "@workspace/ui/lib/utils",
    "ui": "@workspace/ui/components/ui",
    "lib": "@workspace/ui/lib",
    "hooks": "@workspace/ui/hooks"
  }
}
```

## Namespaced Registries

Configure third-party or private registries in `components.json`:

```json
{
  "registries": {
    "acme": {
      "url": "https://acme.com/r/{name}.json"
    },
    "internal": {
      "url": "https://internal.company.com/r/{name}.json",
      "headers": {
        "Authorization": "Bearer ${INTERNAL_TOKEN}"
      }
    }
  }
}
```

Install from a namespaced registry:

```bash
npx shadcn@latest add @acme/fancy-button
npx shadcn@latest add @internal/data-grid
```

The `{name}` placeholder is replaced with the resource name. Environment variables in `${VAR_NAME}` format are expanded automatically.

-> See `references/registry-system.md` for building custom registries.
