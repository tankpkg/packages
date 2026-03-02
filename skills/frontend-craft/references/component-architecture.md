# Component Architecture for Premium UI

Sources: shadcn/ui conventions, Radix UI documentation, Wathan/Schoger (Refactoring UI)

Covers: shadcn/ui patterns, Radix UI primitives, CVA variant system, design tokens with CSS custom properties, cn() utility, composition with Slot/asChild, accessible component foundations.

## 1. The Stack

Premium UI development relies on a multi-layered approach that decouples accessibility, styling logic, visual implementation, and animated effects. Each layer solves a specific problem in the component lifecycle.

| Layer | Technology | Primary Responsibility |
|-------|------------|------------------------|
| **Primitive** | Radix UI | Headless logic, ARIA attributes, keyboard navigation, focus management. |
| **Logic/Variant** | CVA (Class Variance Authority) | Mapping component props to specific Tailwind class sets in a type-safe manner. |
| **Styling** | Tailwind CSS | Utility-first styling engine using design tokens for visual consistency. |
| **Functional UI** | shadcn/ui Patterns | Buttons, dialogs, forms, tables — the architectural convention for functional components. |
| **Visual Effects** | Aceternity UI | Animated backgrounds, 3D cards, text effects, parallax — copy-paste via same shadcn CLI. |
| **Utility** | cn() (clsx + tailwind-merge) | Resolving class conflicts and conditional logic at runtime. |
| **Composition** | Radix Slot | Enabling polymorphic components via the asChild pattern. |

### shadcn/ui vs External Component Sources

shadcn/ui, Aceternity UI, and all third-party registries use the same CLI and coexist in `components/ui/`.

- **shadcn/ui**: Functional UI primitives — Button, Dialog, Table, Select, Form.
- **Aceternity UI**: Visual effects — animated backgrounds, 3D cards, text animations, parallax. Install: `npx shadcn@latest add @aceternity/<name>`
- **Shadcn Registries**: 50+ quality registries (Magic UI, React Bits, Cult UI, Kibo UI, etc.) — all installable via `npx shadcn@latest add @registry/component`.
- **Search across all**: `python scripts/search-components.py <query>` (11K+ cached components).

For full catalogs and decision trees, see `references/component-discovery-sources.md`.

## 2. Design Tokens with CSS Custom Properties

Premium systems avoid hardcoded hex values in component files. Instead, they use semantic CSS variables mapped to HSL values. This enables dynamic theme switching (light/dark mode), consistency, and programmatic color manipulation.

### HSL-Based Color System
Use HSL (Hue, Saturation, Lightness) for tokens. This allows the system to generate foreground (text) colors and opacity variants using the same base variable without redefining the color.

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  
  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;
  
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;

  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  
  --popover: 222.2 84% 4.9%;
  --popover-foreground: 210 40% 98%;
  
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
  
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 224.3 76.3% 48%;
}
```

### Tailwind Integration
Map these variables in the `tailwind.config.js` to allow utility usage like `bg-primary` or `text-muted-foreground`. This abstraction decouples the theme definition from the component styles.

```javascript
module.exports = {
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
}
```

## 3. CVA Variant System

Class Variance Authority (CVA) provides a declarative way to manage component variants. It replaces complex template literals and conditional logic with a structured, type-safe schema.

### Defining Variants
Centralize styling logic in a `cva` definition. Include `base` styles, `variants`, `compoundVariants` for intersecting props, and `defaultVariants`.

```typescript
import { cva, type VariantProps } from "class-variance-authority";

export const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}
```

### Compound Variants
Use `compoundVariants` to apply specific styles when multiple conditions are met. This is essential for managing states that depend on two different props, like a specific padding for an outline button of a certain size.

```typescript
compoundVariants: [
  {
    variant: "outline",
    size: "lg",
    class: "border-2",
  },
  {
    variant: "ghost",
    size: "icon",
    class: "rounded-full",
  }
],
```

## 4. The cn() Utility

The `cn()` utility is the standard for merging Tailwind classes in shadcn-style architectures. It combines `clsx` for conditional logic and `tailwind-merge` to handle utility overrides efficiently.

### Implementation
The `tailwind-merge` step is critical because standard string concatenation allows conflicting classes (e.g., `p-2 p-4`) where the result depends on CSS source order rather than the developer's intent. `twMerge` ensures the last class provided wins.

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### Usage Pattern
Always use `cn()` when applying classes that might be extended or overridden via props.

```tsx
<div className={cn(
  "base-style flex items-center justify-between", 
  isActive && "text-primary font-bold", 
  className
)}>
  {children}
</div>
```

## 5. Radix Primitive Patterns

Radix UI provides the unstyled foundation for complex interactive components. Premium implementation follows strict patterns for triggers, content, and portals to ensure stability and accessibility.

### Portal and Overlay Usage
Modal components (Dialog, Sheet, Select, Popover) must use `Portal` to render content at the root of the document. This prevents the modal from being clipped by containers with `overflow: hidden` and simplifies z-index management.

```tsx
const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
```

### Select and DropdownMenu Patterns
Use `asChild` on triggers to allow wrapping custom elements like icons or avatars without adding unnecessary DOM levels. Ensure `DropdownMenuItem` uses `onSelect` for actions rather than `onClick` to handle keyboard interactions correctly.

## 6. Composition with Slot (asChild)

Polymorphism allows a component to render as a different HTML element or another React component while maintaining its own logic and styles. The `@radix-ui/react-slot` package is the engine for this pattern.

### Implementation Pattern
The `Slot` component merges its props with the props of its immediate child. This is the "clean" way to implement polymorphic components without the `as` prop complexity.

```tsx
import { Slot } from "@radix-ui/react-slot";

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
```

### When to Use Slot vs Direct Render
1. **Use Slot**: When the user needs to change the element (e.g., using a Next.js `Link` as a `Button`) while preserving the Button's visual variants.
2. **Use Direct Render**: For internal components where the underlying element is fixed (e.g., a form `Input`).

## 7. Accessible Foundations

Radix handles the technical implementation of ARIA, but premium architecture requires adhering to specific patterns during implementation.

### Focus Management
Architecture should rely on Radix's automatic focus trapping.
- **Initial Focus**: Use `onOpenAutoFocus` to focus a specific input inside a dialog.
- **Return Focus**: Radix automatically returns focus to the `Trigger` when the component closes.
- **Focus Indicators**: Ensure the `ring` utilities are applied to all interactive elements in the `base` CVA style.

### Keyboard Navigation Patterns
- **Esc Key**: Global listener for closing overlays.
- **Tab Key**: Restricted to the active overlay (focus trap).
- **Arrow Keys**: Used for navigating lists, menu items, and tab headers.

### Screen Reader Considerations
- **sr-only**: Use for providing context that is only visible to screen readers (e.g., the "Close" label on an icon-only button).
- **Aria-Labels**: Prefer `aria-label` or `aria-labelledby` for complex components where the text content doesn't clearly describe the purpose.

## 8. File Organization

Maintain a clean separation between styling definitions, logic, and exports to prevent maintenance debt.

### Directory Structure
```
components/
├── ui/                 # Low-level primitives (Button, Input, Dialog)
│   ├── button.tsx      # Standardized primitive
│   ├── dialog.tsx      # Composition of Radix parts
│   └── select.tsx
├── shared/             # Reusable compositions (UserAvatar, NavItem)
│   ├── user-nav.tsx    # Higher-level UI logic
│   └── main-nav.tsx
├── layouts/            # Page-level structural components
└── forms/              # Domain-specific form components
```

### Barrel Exports
Use barrel exports (`index.ts`) sparingly. While they simplify imports, they can lead to circular dependencies and performance issues in large codebases. Prefer direct imports for `ui` components.

### UI vs Shared
- **UI Components**: Purely visual, context-agnostic, built on Radix/CVA.
- **Shared Components**: May contain application logic, use multiple UI components, and are context-aware.

## 9. Anti-Patterns

Avoid these common architectural mistakes that degrade the quality of a component system.

| Anti-Pattern | Consequence | Corrective Action |
|--------------|-------------|-------------------|
| **Wrapping Primitives** | Extra DOM nodes, broken focus. | Use `asChild` and `Slot` for composition. |
| **Leaking Styles** | Unexpected visual overrides. | Use `cn()` with `twMerge` to handle prop overrides properly. |
| **Inconsistent Tokens** | Brand dilution, maintenance hell. | Only use CSS variables from the design system. |
| **Fighting the Primitive** | Fragile logic, accessibility regressions. | Respect Radix state management; use callbacks. |
| **Prop Drilling Styles** | Hard to read components. | Use `CVA` variants instead of passing 10 styling props. |
| **Hardcoded Colors** | Broken dark mode, no flexibility. | Always use `hsl(var(--token))` syntax. |
| **Manual Portal management** | Z-index wars, stacking context issues. | Use `Radix.Portal` for all floating elements. |

### Summary of Implementation
Premium architecture is defined by its predictability and separation of concerns. By leveraging Radix for accessibility logic, CVA for styling variations, and Tailwind for implementation, developers create components that are robust, type-safe, and visually consistent. Adhering to the `asChild` pattern and the `cn()` utility ensures that the system remains flexible and interoperable with other libraries.
