---
name: "@tank/shadcn-mastery"
description: |
  Build, customize, and scale design systems with shadcn/ui. Covers the
  CLI and components.json configuration, CSS variable theming (semantic tokens,
  dark mode, custom palettes), component customization (cva variants, extending
  primitives, compound components), data tables (TanStack Table integration with
  sorting, filtering, pagination, row selection), forms (react-hook-form + zod +
  Field component, validation modes, array fields), charts (Recharts + CSS
  variable theming), the registry system (building and distributing custom
  registries, namespaces, authentication), Radix UI primitives and accessibility,
  component composition patterns (Dialog + Form, Command palette, Combobox),
  monorepo setup, and Tailwind CSS v4 integration.

  Synthesizes shadcn/ui official documentation (ui.shadcn.com 2025-2026),
  Radix UI primitives documentation, TanStack Table v8 docs, react-hook-form
  docs, class-variance-authority (cva) patterns, and Tailwind CSS v4 docs.

  Trigger phrases: "shadcn", "shadcn ui", "shadcn/ui", "shadcn components",
  "shadcn theming", "shadcn dark mode", "shadcn data table", "shadcn form",
  "shadcn dialog", "shadcn select", "shadcn custom component",
  "shadcn tailwind", "shadcn registry", "shadcn CLI", "shadcn add",
  "npx shadcn", "components.json", "shadcn button variant", "shadcn chart",
  "shadcn combobox", "shadcn command palette", "shadcn monorepo",
  "shadcn sidebar", "cva variants", "shadcn customize", "shadcn sheet",
  "shadcn accordion", "shadcn best practices", "shadcn design system"
---

# Shadcn Mastery

## Core Philosophy

1. **Open code, not a dependency** — shadcn/ui copies component source into the project. Edit files directly instead of wrapping or overriding an npm package. This is the component library you own.
2. **Semantic tokens drive consistency** — Theme with CSS variables (`--primary`, `--background`) rather than raw color values. Every component reads from the same token set, so a single variable change propagates everywhere.
3. **Composition over configuration** — Build complex UI by composing small Radix primitives (Dialog + Form, Command + Popover). Avoid prop-drilling feature flags into monolithic components.
4. **Use the CLI, not copy-paste** — `npx shadcn@latest add` resolves dependencies, respects `components.json` aliases, and handles monorepo paths. Manual copy-paste breaks this chain.
5. **Radix handles accessibility** — Radix primitives ship with ARIA roles, keyboard navigation, and focus management. Customize visuals freely but preserve the primitive structure to keep accessibility intact.

## Quick-Start: Common Problems

### "How do I set up shadcn/ui?"
1. Run `npx shadcn@latest init` — select framework, base color, CSS variables
2. Inspect the generated `components.json` — verify aliases match `tsconfig.json` paths
3. Add components: `npx shadcn@latest add button dialog input`
4. Components land in `components/ui/` — edit them directly
-> See `references/cli-and-config.md`

### "My theme colors look wrong"
1. Check `globals.css` — tokens must be defined under `:root` and `.dark`
2. Verify background/foreground pairs: `--primary` pairs with `--primary-foreground`
3. Confirm `tailwind.cssVariables` is `true` in `components.json`
4. Use `shadcn/create` to preview and generate theme presets
-> See `references/theming-dark-mode.md`

### "I need a data table with sorting and filtering"
1. Add `Table` component: `npx shadcn@latest add table`
2. Install TanStack Table: `npm i @tanstack/react-table`
3. Define column definitions in a separate `columns.tsx` file
4. Wire `useReactTable` with sorting/filtering/pagination state
-> See `references/data-tables.md`

### "How do I build a validated form?"
1. Add `Field` + `Input` + `Label` components
2. Install `react-hook-form` + `@hookform/resolvers` + `zod`
3. Define Zod schema, pass to `useForm` via `zodResolver`
4. Use `Controller` + `Field` for each form control
-> See `references/forms-validation.md`

### "I want to add a custom variant to Button"
1. Open `components/ui/button.tsx`
2. Add the variant to the `cva` call in `buttonVariants`
3. Update the `ButtonProps` type to include the new variant
-> See `references/component-customization.md`

## Decision Trees

### Component Selection

| Need | Component |
|------|-----------|
| Modal with blocking action | `AlertDialog` (prevents outside dismiss) |
| Modal with form/content | `Dialog` (standard dismissible) |
| Side panel | `Sheet` (slides from edge) |
| Mobile-friendly bottom panel | `Drawer` (swipe-to-dismiss) |
| Search/command launcher | `Command` (cmdk-powered) |
| Searchable dropdown | `Combobox` (Command + Popover) |
| Simple dropdown | `Select` (native-like) |
| Menu with actions | `DropdownMenu` (right-click or button trigger) |

### Overlay Stacking

| Signal | Approach |
|--------|----------|
| Dialog inside Dialog | Nest `Dialog` components — Radix manages stacking |
| Form inside Dialog | Compose `Dialog` + `form` + `Field` components |
| Confirmation after action | Use `AlertDialog` triggered from parent `Dialog` |
| Sheet with sub-navigation | Use `Tabs` inside `Sheet` |

## Reference Index

| File | Contents |
|------|----------|
| `references/cli-and-config.md` | CLI commands (init, add, build, migrate), components.json schema, path aliases, Tailwind v3/v4 config |
| `references/theming-dark-mode.md` | CSS variable tokens, semantic pairs, dark mode setup, radius scale, custom tokens, base colors |
| `references/component-customization.md` | cva variant patterns, extending components, compound components, cn() utility, adding new primitives |
| `references/data-tables.md` | TanStack Table integration, column definitions, sorting, filtering, pagination, row selection, reusable components |
| `references/forms-validation.md` | react-hook-form + zod + Field component, validation modes, error display, field types, array fields |
| `references/composition-patterns.md` | Dialog + Form, Command palette, Combobox, Sheet vs Dialog, sidebar patterns, toast/sonner |
| `references/registry-system.md` | Registry schema, building custom registries, namespaces, authentication, distribution, MCP server |
| `references/accessibility-radix.md` | Radix primitives, ARIA patterns, keyboard navigation, focus management, screen reader support |
