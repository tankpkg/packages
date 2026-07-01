# Component Customization

Sources: shadcn/ui official documentation (ui.shadcn.com 2025-2026), class-variance-authority (cva) documentation, Tailwind CSS documentation, Radix UI composition patterns

Covers: cva variant system, extending existing components with new variants, the cn() utility, compound component patterns, creating new components from Radix primitives, wrapping third-party components.

## The Open Code Model

shadcn/ui components are source files in the project, not locked npm packages. Customization means editing the file directly. No wrapper components, no style overrides, no `!important` hacks.

When `npx shadcn@latest add button` runs, it places `button.tsx` in `components/ui/`. That file is now yours. Edit it freely.

## The cn() Utility

Every shadcn component uses `cn()` to merge class names. It combines `clsx` (conditional classes) and `tailwind-merge` (deduplicates conflicting Tailwind classes):

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

Usage in components:

```tsx
<div className={cn("px-4 py-2", isActive && "bg-primary", className)}>
```

`tailwind-merge` resolves conflicts intelligently: `cn("px-4", "px-6")` yields `"px-6"`, not `"px-4 px-6"`.

## cva (Class Variance Authority)

cva is the variant system behind every shadcn component. It maps variant props to Tailwind class sets.

### Basic cva Pattern

```typescript
import { cva, type VariantProps } from "class-variance-authority"

const buttonVariants = cva(
  // Base classes applied to all variants
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### Component with cva Variants

```typescript
import * as React from "react"
import { Slot } from "radix-ui"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

### Adding a New Variant

Edit the component file directly. Add the new variant to the `variants` object:

```typescript
const buttonVariants = cva(
  "inline-flex items-center ...",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground ...",
        destructive: "bg-destructive ...",
        // Add new variant:
        success: "bg-green-600 text-white shadow-sm hover:bg-green-700",
        warning: "bg-warning text-warning-foreground shadow-sm hover:bg-warning/90",
      },
      size: { /* ... */ },
    },
  }
)
```

TypeScript picks up the new variant automatically via `VariantProps<typeof buttonVariants>`.

### Compound Variants

Apply classes only when specific variant combinations are active:

```typescript
const alertVariants = cva("rounded-lg border p-4", {
  variants: {
    variant: {
      default: "bg-background text-foreground",
      destructive: "border-destructive/50 text-destructive",
    },
    size: {
      default: "text-sm",
      lg: "text-base p-6",
    },
  },
  compoundVariants: [
    {
      variant: "destructive",
      size: "lg",
      className: "border-2 font-semibold",
    },
  ],
  defaultVariants: {
    variant: "default",
    size: "default",
  },
})
```

## Extending Existing Components

### Adding Props

Add custom props alongside the existing interface:

```typescript
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean  // Custom prop
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, loading, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={loading || props.disabled}
        {...props}
      >
        {loading && <Spinner className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </Comp>
    )
  }
)
```

### Wrapping with Defaults

Create application-specific wrappers that set sensible defaults:

```typescript
// components/app-button.tsx
import { Button, type ButtonProps } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function AppButton({ className, ...props }: ButtonProps) {
  return (
    <Button
      className={cn("rounded-full font-semibold", className)}
      {...props}
    />
  )
}
```

## Compound Components

Build complex UI from composable sub-components following the shadcn pattern:

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("rounded-xl border bg-card text-card-foreground shadow", className)}
      {...props}
    />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("font-semibold leading-none tracking-tight", className)} {...props} />
  )
)
CardTitle.displayName = "CardTitle"

export { Card, CardHeader, CardTitle }
```

Usage:

```tsx
<Card>
  <CardHeader>
    <CardTitle>Dashboard</CardTitle>
  </CardHeader>
</Card>
```

## The asChild Pattern

Radix's `Slot` component enables polymorphic rendering. When `asChild` is true, the component merges its props onto the child element:

```tsx
// Renders as <button>
<Button>Click me</Button>

// Renders as <a> with button styles
<Button asChild>
  <a href="/dashboard">Go to Dashboard</a>
</Button>

// Renders as Next.js Link with button styles
<Button asChild>
  <Link href="/dashboard">Go to Dashboard</Link>
</Button>
```

Use `asChild` whenever the component needs to render as a different element while preserving styles and behavior.

## Creating New Components from Radix Primitives

Wrap Radix primitives with shadcn styling conventions:

```typescript
import * as SwitchPrimitive from "radix-ui"
import { cn } from "@/lib/utils"

const Switch = React.forwardRef<
  React.ComponentRef<typeof SwitchPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitive.Root
    className={cn(
      "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-sm transition-colors",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      "disabled:cursor-not-allowed disabled:opacity-50",
      "data-[state=checked]:bg-primary data-[state=unchecked]:bg-input",
      className
    )}
    ref={ref}
    {...props}
  >
    <SwitchPrimitive.Thumb
      className={cn(
        "pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform",
        "data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0"
      )}
    />
  </SwitchPrimitive.Root>
))
Switch.displayName = SwitchPrimitive.Root.displayName
```

The pattern: import the Radix primitive, wrap with `forwardRef`, apply theme tokens via `cn()`, expose `className` for consumer overrides.

## Handling Upstream Updates

Since components are owned source, there is no automatic `npm update`. To pull upstream changes:

1. Check the shadcn/ui changelog for the component
2. Run `npx shadcn@latest add <component> --overwrite` to get the latest version
3. Re-apply custom modifications manually
4. Use version control to diff changes

For components with heavy customization, maintain a comment block at the top noting what was changed and why. This makes future merges manageable.
