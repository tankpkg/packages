---
name: @tank/tailwind
description: "Production Tailwind CSS patterns and component recipes for responsive, accessible UI."
triggers:
  - tailwind
  - tailwindcss
  - utility class
  - css utility
  - responsive
  - breakpoint
  - container query
  - dark mode
  - theme
  - design tokens
  - shadcn
  - component styling
  - layout
  - grid
  - flex
  - spacing scale
  - animation
  - gradient
  - shadow
  - hover
  - focus
  - aria
  - @apply
---

# Tailwind CSS Skill

## Core Philosophy
- Utility-first, not utility-only: compose primitives into systems.
- Design with constraints: pick a scale and stay on it.
- Compose, don't @apply: prefer classes in markup for clarity.

## Workflow
1. Determine component intent and state matrix (default, hover, focus, active, disabled, error).
2. Pick layout primitives (flex, grid, container, stack) before styling.
3. Use scale-first tokens (spacing, radius, type) before arbitrary values.
4. Add states with variant prefixes; keep base classes clean.
5. Validate accessibility: focus ring, contrast, motion, reduced motion.

## Responsive Design Quick Reference
| Concept | Syntax | Example |
| --- | --- | --- |
| Mobile-first | base then breakpoints | `text-sm md:text-base lg:text-lg` |
| sm | `sm:` (640px) | `sm:grid-cols-2` |
| md | `md:` (768px) | `md:px-8` |
| lg | `lg:` (1024px) | `lg:max-w-5xl` |
| xl | `xl:` (1280px) | `xl:gap-8` |
| 2xl | `2xl:` (1536px) | `2xl:py-24` |
| Container query | `@container` + `@[size]:` | `@container md:@[32rem]:grid-cols-2` |

## Spacing Scale (p-1 to p-16)
| Class | rem | px |
| --- | --- | --- |
| p-1 | 0.25rem | 4px |
| p-2 | 0.5rem | 8px |
| p-3 | 0.75rem | 12px |
| p-4 | 1rem | 16px |
| p-5 | 1.25rem | 20px |
| p-6 | 1.5rem | 24px |
| p-7 | 1.75rem | 28px |
| p-8 | 2rem | 32px |
| p-9 | 2.25rem | 36px |
| p-10 | 2.5rem | 40px |
| p-11 | 2.75rem | 44px |
| p-12 | 3rem | 48px |
| p-13 | 3.25rem | 52px |
| p-14 | 3.5rem | 56px |
| p-15 | 3.75rem | 60px |
| p-16 | 4rem | 64px |

## Common Class Combinations
| Goal | Classes |
| --- | --- |
| Center block | `mx-auto max-w-5xl px-6` |
| Center content | `flex items-center justify-center` |
| Balanced stack | `flex flex-col gap-4` |
| Truncation | `truncate` or `line-clamp-2` |
| Aspect video | `aspect-video overflow-hidden` |
| Floating action | `fixed bottom-6 right-6 z-50` |
| Focus ring | `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/50` |
| Soft card | `rounded-xl border border-slate-200 bg-white shadow-sm` |
| Overlay | `fixed inset-0 bg-slate-900/50 backdrop-blur-sm` |

## State and Accessibility
| State | Classes | Note |
| --- | --- | --- |
| Hover | `hover:bg-slate-100` | Add only where interactive |
| Focus | `focus-visible:ring-2 focus-visible:ring-slate-900/40` | Keyboard visibility |
| Active | `active:scale-[0.99]` | Subtle feedback |
| Disabled | `disabled:opacity-50 disabled:pointer-events-none` | Prevent interaction |
| Aria | `aria-[current=page]:text-slate-900` | Semantic states |

## Variant Ordering
- Order: base → size → color → state → responsive.
- Keep `dark:` variants next to base styles.
- Group focus-visible utilities together.
- Avoid mixing `group-hover` and `hover` without intent.
- Prefer `aria-*` variants over JS toggles when possible.

## Arbitrary Values Guardrails
- Use only when the scale cannot express the value.
- Document the reason in nearby code or README.
- Keep to one or two per component.
- Prefer `theme()` tokens in plugins over arbitrary values.

## When to Use @apply Decision Tree
- Do you need to style a third-party class you cannot edit?
  - Yes → Use `@apply` in a single-purpose component class.
  - No → Continue.
- Is there a strict design system class used across many repos?
  - Yes → Use `@apply` to publish stable design tokens.
  - No → Continue.
- Is this for complex pseudo-elements or media queries only in CSS?
  - Yes → Use `@apply` for base utilities, add CSS for the rest.
  - No → Do not use `@apply`; keep utilities in markup.

## Dark Mode Strategy
| Strategy | Tailwind Setting | Example |
| --- | --- | --- |
| Class toggle | `darkMode: "class"` | `html class="dark"` |
| Media query | `darkMode: "media"` | `dark:bg-slate-900` |
| Data attribute | `darkMode: ["class", "[data-theme='dark']"]` | `data-theme="dark"` |

## Anti-Patterns (Avoid)
| Anti-pattern | Why it hurts |
| --- | --- |
| Overusing `@apply` | Hides intent, reduces discoverability |
| Inline style fallbacks | Breaks design scale and theming |
| Mixing arbitrary values everywhere | Blocks consistency and reuse |
| Ignoring focus styles | Accessibility regressions |
| One-off color hexes | Breaks dark mode and tokenization |
| Deeply nested selectors | Fights utility-first model |
| Hardcoded breakpoints | Diverges from responsive system |
| Shipping unscoped `*` styles | Global side effects |
| Animations without reduced motion | Accessibility issues |

## Output Expectations
- Prefer small, composable class lists over mega strings.
- Use semantic HTML, then Tailwind for appearance.
- Provide full recipes with states and aria attributes.
- Document any arbitrary value with rationale.

## Reference Index
- `skills/tailwind/references/component-recipes.md`
- `skills/tailwind/references/layout-and-responsive.md`
- `skills/tailwind/references/customization.md`

## Communication Style
- Provide exact Tailwind classes and real HTML.
- Be explicit about responsive variants and states.
- Avoid vague advice; show working patterns.

## Quality Checklist
- Uses Tailwind scale for spacing, radius, type
- Includes hover, focus-visible, and disabled states
- Responsive behavior is mobile-first
- Dark mode strategy is consistent
- No unnecessary `@apply`
