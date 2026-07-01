# Accessibility and Radix Primitives

Sources: Radix UI documentation (radix-ui.com 2025-2026), WAI-ARIA Authoring Practices 1.2, shadcn/ui component source (GitHub shadcn-ui/ui), WCAG 2.2 Guidelines

Covers: Radix primitive architecture, ARIA roles and attributes, keyboard navigation patterns, focus management, screen reader support, accessible component patterns for dialogs, menus, forms, and custom components.

## Radix Primitive Architecture

shadcn/ui builds on Radix UI primitives -- unstyled, accessible components that handle ARIA attributes, keyboard interactions, and focus management. shadcn adds visual styling via Tailwind CSS on top.

### What Radix Handles

| Concern | Radix Responsibility | Developer Responsibility |
|---------|---------------------|--------------------------|
| ARIA roles | Automatic (`role="dialog"`, `role="menu"`, etc.) | None -- do not override |
| ARIA attributes | Automatic (`aria-expanded`, `aria-selected`, etc.) | Add `aria-label` when visible text is absent |
| Keyboard navigation | Built-in (Enter, Space, Escape, Arrow keys) | None for standard patterns |
| Focus trapping | Automatic in overlays (Dialog, Sheet, AlertDialog) | None |
| Focus restoration | Returns focus to trigger on close | None |
| Screen reader announcements | Live regions for dynamic content | Add descriptive text when needed |
| Visual styling | None | Full developer responsibility via Tailwind |

### Data Attributes

Radix exposes component state via `data-*` attributes for CSS styling:

| Attribute | Values | Used For |
|-----------|--------|----------|
| `data-state` | `"open"` / `"closed"` | Dialog, Popover, Collapsible, Accordion |
| `data-state` | `"checked"` / `"unchecked"` | Checkbox, Switch, RadioGroup |
| `data-state` | `"active"` / `"inactive"` | Tabs, Toggle |
| `data-disabled` | `""` (present when disabled) | All interactive components |
| `data-highlighted` | `""` (present on highlight) | Menu items, Select items |
| `data-orientation` | `"horizontal"` / `"vertical"` | Separator, Tabs, Slider |
| `data-side` | `"top"` / `"right"` / `"bottom"` / `"left"` | Popover, Tooltip, DropdownMenu |

Style with Tailwind data attribute selectors:

```tsx
<SwitchPrimitive.Thumb
  className="data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0"
/>
```

## Keyboard Navigation Patterns

### Dialog / AlertDialog

| Key | Action |
|-----|--------|
| `Escape` | Close dialog |
| `Tab` | Move focus to next focusable element (trapped inside) |
| `Shift + Tab` | Move focus to previous focusable element |

Focus is trapped inside the dialog. On close, focus returns to the trigger element.

### DropdownMenu / ContextMenu

| Key | Action |
|-----|--------|
| `Enter` / `Space` | Open menu (on trigger), select item |
| `ArrowDown` | Move to next item |
| `ArrowUp` | Move to previous item |
| `ArrowRight` | Open submenu |
| `ArrowLeft` | Close submenu |
| `Escape` | Close menu |
| `Home` | Move to first item |
| `End` | Move to last item |
| Type-ahead | Focus item starting with typed characters |

### Select

| Key | Action |
|-----|--------|
| `Enter` / `Space` | Open select, confirm selection |
| `ArrowDown` / `ArrowUp` | Navigate options |
| `Escape` | Close without selecting |
| Type-ahead | Jump to matching option |

### Tabs

| Key | Action |
|-----|--------|
| `ArrowRight` / `ArrowLeft` | Switch tabs (horizontal) |
| `ArrowDown` / `ArrowUp` | Switch tabs (vertical) |
| `Home` | First tab |
| `End` | Last tab |

### Accordion

| Key | Action |
|-----|--------|
| `Enter` / `Space` | Toggle section |
| `ArrowDown` | Next trigger |
| `ArrowUp` | Previous trigger |
| `Home` | First trigger |
| `End` | Last trigger |

## Focus Management

### Focus Trapping

Radix automatically traps focus inside modal overlays:
- `Dialog` -- focus trapped, Escape closes
- `AlertDialog` -- focus trapped, outside click blocked
- `Sheet` -- focus trapped

Non-modal components (Popover, Tooltip, DropdownMenu) do not trap focus but manage focus within the floating content.

### Focus on Open

Radix auto-focuses the first focusable element when a dialog opens. Override with `autoFocus={false}` on the dialog or by placing `autoFocus` on the desired element:

```tsx
<DialogContent>
  <DialogTitle>Edit Profile</DialogTitle>
  <Input autoFocus placeholder="Name" />
</DialogContent>
```

### Focus Restoration

When a modal closes, focus returns to the element that triggered it. This behavior is automatic and critical for keyboard users.

### Focus Visible

shadcn components use `focus-visible:` instead of `focus:` for outlines. This shows focus rings only for keyboard navigation, not mouse clicks:

```tsx
className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
```

## Screen Reader Patterns

### Labels

Provide accessible names for all interactive elements:

```tsx
// Visible label (preferred)
<Label htmlFor="email">Email</Label>
<Input id="email" />

// Hidden label for icon-only buttons
<Button variant="ghost" size="icon" aria-label="Close menu">
  <X className="h-4 w-4" />
</Button>

// Using sr-only for screen-reader-only text
<span className="sr-only">Open notifications</span>
```

### Descriptions

Connect descriptions to form controls:

```tsx
<Field>
  <FieldLabel>Password</FieldLabel>
  <Input type="password" aria-describedby="password-desc" />
  <FieldDescription id="password-desc">
    Minimum 8 characters with one uppercase letter.
  </FieldDescription>
</Field>
```

### Error Announcements

Mark invalid fields for screen readers:

```tsx
<Input
  aria-invalid={!!error}
  aria-describedby={error ? "email-error" : undefined}
/>
{error && (
  <FieldError id="email-error" role="alert">
    {error.message}
  </FieldError>
)}
```

Use `role="alert"` or `aria-live="polite"` on error messages so screen readers announce them when they appear.

### Accessible Dialogs

Radix Dialog automatically sets:
- `role="dialog"` on the content
- `aria-modal="true"` for modal dialogs
- `aria-labelledby` pointing to `DialogTitle`
- `aria-describedby` pointing to `DialogDescription` (if present)

Always include a `DialogTitle`. If the title should be visually hidden:

```tsx
import { VisuallyHidden } from "radix-ui"

<DialogContent>
  <VisuallyHidden>
    <DialogTitle>Confirm Action</DialogTitle>
  </VisuallyHidden>
  {/* Visual content without a heading */}
</DialogContent>
```

## Accessible Form Patterns

### Required Fields

Mark required fields with `aria-required`:

```tsx
<Input aria-required="true" />
```

Or in the Zod schema, all non-optional fields are implicitly required. Display a visual indicator:

```tsx
<FieldLabel>
  Email <span className="text-destructive" aria-hidden="true">*</span>
</FieldLabel>
```

Use `aria-hidden="true"` on the asterisk since `aria-required` already conveys the information.

### Form Error Summary

For long forms, provide an error summary at the top:

```tsx
{Object.keys(form.formState.errors).length > 0 && (
  <div role="alert" className="rounded-md border border-destructive p-4">
    <p className="font-medium text-destructive">Please fix the following errors:</p>
    <ul className="list-disc pl-4 text-sm text-destructive">
      {Object.entries(form.formState.errors).map(([field, error]) => (
        <li key={field}>{error?.message}</li>
      ))}
    </ul>
  </div>
)}
```

### Fieldset and Legend

Group related fields with `FieldSet` and `FieldLegend`:

```tsx
<FieldSet>
  <FieldLegend>Notification Preferences</FieldLegend>
  <FieldDescription>Choose how you want to be notified.</FieldDescription>
  <FieldGroup data-slot="checkbox-group">
    {/* Checkbox items */}
  </FieldGroup>
</FieldSet>
```

## Building Accessible Custom Components

When creating custom components from Radix primitives, follow this checklist:

| Check | Implementation |
|-------|---------------|
| Visible label or `aria-label` | Every interactive element has an accessible name |
| Keyboard operable | All actions reachable without mouse |
| Focus visible | `focus-visible:ring-2` on focusable elements |
| State communicated | Use Radix data attributes or `aria-expanded`, `aria-selected` |
| Error announced | `aria-invalid` + `role="alert"` on error messages |
| Color not sole indicator | Use icons or text in addition to color for status |
| Contrast ratio | Text meets 4.5:1 (normal) or 3:1 (large) against background |
| Motion respect | Use `prefers-reduced-motion` media query for animations |

### Reduced Motion

Respect user preferences for reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

In components using Framer Motion / Motion:

```tsx
import { useReducedMotion } from "framer-motion"

function AnimatedCard({ children }) {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
    >
      {children}
    </motion.div>
  )
}
```

## Testing Accessibility

| Tool | Purpose |
|------|---------|
| Keyboard navigation | Tab through the entire page, verify all interactive elements reachable |
| Screen reader (VoiceOver/NVDA) | Verify announcements, labels, and landmark navigation |
| axe-core / Lighthouse | Automated WCAG violation detection |
| Color contrast checker | Verify token pairs meet WCAG AA (4.5:1 text, 3:1 large text) |
| `prefers-reduced-motion` | Toggle in browser DevTools, verify animations respect preference |

Run automated checks in CI with `@axe-core/playwright` or `jest-axe` for component tests.
