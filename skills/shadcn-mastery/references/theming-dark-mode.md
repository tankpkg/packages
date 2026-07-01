# Theming and Dark Mode

Sources: shadcn/ui theming documentation (ui.shadcn.com 2025-2026), Tailwind CSS v4 documentation, next-themes documentation

Covers: CSS variable token system, semantic background/foreground pairs, dark mode configuration, radius scale, adding custom tokens, base color palettes, theme provider setup.

## Token Architecture

shadcn/ui uses semantic CSS variables for theming. Components reference tokens like `bg-primary` and `text-primary-foreground` instead of raw color values. Override the tokens in CSS to change the entire look without modifying component code.

### Convention: Background/Foreground Pairs

Every surface token pairs with a `-foreground` token. The surface token (without suffix) controls the background, and the `-foreground` token controls the text/icon color on that surface.

```css
:root {
  --primary: oklch(0.21 0.006 285.88);
  --primary-foreground: oklch(0.98 0.002 285.88);
}
```

Usage in components:

```tsx
<div className="bg-primary text-primary-foreground">
  Primary surface with matching text color
</div>
```

## Token Reference

| Token | Controls | Used By |
|-------|----------|---------|
| `background` / `foreground` | Default app background and text | Page shell, sections, default text |
| `card` / `card-foreground` | Elevated surfaces | Card, dashboard panels, settings |
| `popover` / `popover-foreground` | Floating surfaces | Popover, DropdownMenu, ContextMenu |
| `primary` / `primary-foreground` | High-emphasis actions, brand | Default Button, selected states, badges |
| `secondary` / `secondary-foreground` | Lower-emphasis filled actions | Secondary buttons, supporting UI |
| `muted` / `muted-foreground` | Subtle surfaces, low emphasis | Descriptions, placeholders, helper text |
| `accent` / `accent-foreground` | Interactive hover/focus states | Ghost buttons, menu highlights, hovered rows |
| `destructive` | Destructive actions, errors | Destructive buttons, invalid states |
| `border` | Default borders, separators | Cards, menus, tables, dividers |
| `input` | Form control borders | Input, Textarea, Select outlines |
| `ring` | Focus rings, outlines | Buttons, inputs, focusable controls |
| `chart-1` ... `chart-5` | Chart color palette | Chart components |
| `sidebar` / `sidebar-foreground` | Sidebar surface and text | Sidebar container and content |
| `sidebar-primary` / `sidebar-primary-foreground` | Sidebar high-emphasis actions | Active items, badges, sidebar CTAs |
| `sidebar-accent` / `sidebar-accent-foreground` | Sidebar hover/selected states | Sidebar hover, open items |
| `sidebar-border` | Sidebar-specific borders | Sidebar headers, groups, dividers |
| `sidebar-ring` | Sidebar-specific focus rings | Focused controls in sidebar |
| `radius` | Base corner radius scale | Cards, inputs, buttons, popovers |

## Radius Scale

The `--radius` variable is the base token. All component radius values derive from it:

```css
:root {
  --radius: 0.625rem;
}

@theme inline {
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}
```

Changing `--radius` updates the entire radius scale. Components use `rounded-lg`, `rounded-md`, etc., which map to these derived values.

## Dark Mode Setup

Dark mode works by overriding the same tokens inside a `.dark` selector. The token names stay the same -- only values change.

### Token Override Structure

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.141 0.005 285.82);
  --primary: oklch(0.21 0.006 285.88);
  --primary-foreground: oklch(0.98 0.002 285.88);
}

.dark {
  --background: oklch(0.141 0.005 285.82);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.92 0.004 285.88);
  --primary-foreground: oklch(0.21 0.006 285.88);
}
```

### Next.js Dark Mode (next-themes)

1. Install `next-themes`:

```bash
npm i next-themes
```

2. Create a theme provider:

```tsx
"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
```

3. Wrap the root layout:

```tsx
import { ThemeProvider } from "@/components/theme-provider"

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

4. Add a theme toggle:

```tsx
"use client"

import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Moon, Sun } from "lucide-react"

export function ModeToggle() {
  const { setTheme, theme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  )
}
```

### Vite Dark Mode

For Vite/React projects without Next.js, use the same `next-themes` package or implement class toggling manually:

```tsx
import { useEffect, useState } from "react"

function useTheme() {
  const [theme, setTheme] = useState(() =>
    typeof window !== "undefined"
      ? localStorage.getItem("theme") || "system"
      : "system"
  )

  useEffect(() => {
    const root = document.documentElement
    const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches
    const isDark = theme === "dark" || (theme === "system" && systemDark)

    root.classList.toggle("dark", isDark)
    localStorage.setItem("theme", theme)
  }, [theme])

  return { theme, setTheme }
}
```

## Adding Custom Tokens

Define new tokens under `:root` and `.dark`, then expose them to Tailwind with `@theme inline`:

```css
:root {
  --warning: oklch(0.84 0.16 84);
  --warning-foreground: oklch(0.28 0.07 56);
}

.dark {
  --warning: oklch(0.68 0.16 55);
  --warning-foreground: oklch(0.98 0.02 56);
}

@theme inline {
  --color-warning: var(--warning);
  --color-warning-foreground: var(--warning-foreground);
}
```

Use in components:

```tsx
<div className="bg-warning text-warning-foreground rounded-md p-4">
  Warning message content
</div>
```

## Base Color Palettes

The `tailwind.baseColor` in `components.json` controls the default token values generated during `init`. This cannot be changed after initialization.

| Base Color | Character |
|------------|-----------|
| `neutral` | Clean, true gray |
| `stone` | Warm gray with slight brown |
| `zinc` | Cool gray with blue undertone |
| `mauve` | Purple-tinted gray |
| `olive` | Green-tinted gray |
| `mist` | Light blue-gray |
| `taupe` | Warm brown-gray |

Use `shadcn/create` at ui.shadcn.com/create to visually preview colors, radius, fonts, and icons, then generate a preset.

## Without CSS Variables

For projects preferring inline Tailwind utilities over CSS variables:

```bash
npx shadcn@latest init --css-variables false
```

This sets `tailwind.cssVariables` to `false`. Components use direct color classes like `bg-zinc-950` instead of `bg-background`. To switch an existing project, delete and re-install components.

## Color Format

shadcn/ui uses OKLCH color values in CSS variables. OKLCH provides perceptually uniform color manipulation:

```css
--primary: oklch(0.21 0.006 285.88);
```

The three values are: lightness (0-1), chroma (saturation), hue (0-360 degrees). Adjust lightness to create consistent tints and shades.

## Theme Customization Workflow

1. Start with `shadcn/create` to pick a base theme visually
2. Copy the generated CSS variables into `globals.css`
3. Adjust specific tokens for brand colors
4. Add custom tokens for project-specific surfaces (e.g., `--success`, `--warning`)
5. Verify dark mode by toggling `.dark` class and checking contrast ratios
