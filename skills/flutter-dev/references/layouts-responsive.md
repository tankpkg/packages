# Layouts and Responsive Design

Sources: Flutter official documentation (layout, BoxConstraints, Flex, Stack, Slivers, Material 3, Cupertino), Dart/Flutter DevTools docs, community production patterns from 2024-2026

Covers: BoxConstraints mental model, Flex-based layouts, Stack and positioned content, slivers, responsive design, adaptive Material/Cupertino UI, breakpoints, and layout debugging patterns in Flutter.

## Layout Is Constraint Negotiation

Flutter layout is driven by constraints moving down the tree and sizes moving back up.

| Concept | Meaning |
|--------|---------|
| parent sets constraints | child must obey allowed size range |
| child picks a size | within those constraints |
| parent places child | final painting position |

Understand this and most Flutter layout issues become predictable instead of magical.

## Flex First: Row, Column, Flex

Use Flex layouts for most standard UI composition.

| Need | Widget |
|-----|--------|
| vertical arrangement | `Column` |
| horizontal arrangement | `Row` |
| dynamic axis reuse | `Flex` |

### Common companions

| Widget | Use |
|-------|-----|
| `Expanded` | consume remaining space |
| `Flexible` | flexible sizing without forcing fill |
| `Spacer` | intentional empty flex space |
| `SizedBox` | explicit fixed gaps |

### Flex pitfalls

| Mistake | Problem | Fix |
|--------|---------|-----|
| unbounded `Column` in scrollable parent | render/layout errors | wrap in constrained parent or sliver/list |
| too many nested Rows/Columns | brittle tree | extract and simplify |
| using `Expanded` everywhere | hard-to-control sizing | use `Flexible`/fixed sizing intentionally |

## BoxConstraints Mental Model

| Situation | Constraint intuition |
|----------|----------------------|
| `Scaffold` body | usually tight max width/height from screen |
| child in `Row` | width may be loose unless expanded |
| child in `ListView` | main axis often unbounded |

When you see overflow, ask: **what constraints did this widget receive?**

## Stack and Overlay Patterns

Use `Stack` when children overlap or anchor relative to the same bounds.

```dart
Stack(
  children: [
    Image.network(heroUrl),
    Positioned(
      bottom: 16,
      left: 16,
      child: Text(title),
    ),
  ],
)
```

### Good stack use cases

| Use case | Why |
|---------|-----|
| hero overlay text | same visual layer |
| badges on avatars/cards | relative positioning |
| floating controls over media/maps | layered UI |

Avoid using Stack to fake every layout problem. If children do not overlap, Flex is usually better.

## Scrollables and Slivers

Use the simplest scroll widget that fits.

| Need | Widget |
|-----|--------|
| simple vertical list | `ListView.builder` |
| simple grid | `GridView.builder` |
| mixed scrolling content | `CustomScrollView` + slivers |
| collapsible app bar + sections | `SliverAppBar` + slivers |

### Sliver strategy

| Pattern | Why |
|--------|-----|
| `SliverList` | large efficient list |
| `SliverGrid` | grid inside one scroll context |
| `SliverToBoxAdapter` | bridge normal widgets into sliver tree |
| `SliverPadding` | sliver-aware spacing |

Use slivers when multiple independently scrollable widgets start fighting each other.

## Responsive Design Rules

Responsive Flutter is not just screen width checks. It is about information density, layout structure, and input modality.

### Baseline breakpoint thinking

| Size class | Example |
|-----------|---------|
| compact | phones |
| medium | foldables / small tablets |
| expanded | tablets / desktop |

### Responsive questions

1. Should this layout reflow from column to row?
2. Should nav become rail/sidebar instead of bottom bar?
3. Should content width cap for readability?

## `LayoutBuilder` vs `MediaQuery`

| Tool | Use when |
|-----|----------|
| `MediaQuery` | you need screen-level data |
| `LayoutBuilder` | you need parent-constrained width/height |

Prefer `LayoutBuilder` for reusable components because parent constraints matter more than global screen width there.

## Adaptive Design: Material vs Cupertino

Flutter can target multiple platform conventions.

| Pattern | Example |
|--------|---------|
| Material-first app | Android/web default |
| Cupertino-specific UX | iOS-polished flows |
| adaptive widget use | `Switch.adaptive`, `CircularProgressIndicator.adaptive` |

Do not over-split every widget by platform. Adapt where users will notice meaningful interaction differences.

## Navigation Shell Responsiveness

| Width / device | Navigation pattern |
|---------------|--------------------|
| phone | bottom navigation bar |
| tablet | navigation rail |
| desktop | sidebar / split pane |

Navigation layout often drives the entire app shell structure.

## Content Width and Readability

On desktop/tablet, full-width text layouts often look amateurish.

| Pattern | Benefit |
|--------|---------|
| max content width container | better readability |
| side panels for supporting controls | better use of wide viewports |
| adaptive two-column forms | shorter scanning paths |

## Common Layout Debugging Moves

| Problem | Debug move |
|--------|------------|
| overflow stripes | inspect parent constraints and children sizes |
| widget not expanding | check `Expanded` / `Flexible` placement |
| unexpected size | wrap with `ColoredBox` or use DevTools layout explorer |
| nested scroll weirdness | move to single `CustomScrollView` |

## Material 3 Layout Considerations

Material 3 encourages more adaptive surfaces and spacing-aware layout patterns.

| Surface | Pattern |
|--------|---------|
| large-screen nav | rail/sidebar |
| cards and lists | more breathable spacing |
| dialogs/sheets | shape and width tuned per size class |

Use Material 3 as a design system, not just a color change.

## Common Layout Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| hard-coding widths everywhere | brittle across devices | use constraints and breakpoints |
| nested scroll views | jank and gesture conflicts | unify scroll context |
| ignoring text scale | clipped/overflowing text | test accessibility text sizes |
| designing only on one phone size | poor tablet/web behavior | test multiple classes |

## Release Readiness Checklist

- [ ] Core screens work on compact and expanded layouts
- [ ] Navigation adapts appropriately across device classes
- [ ] Scroll behavior is unified and intentional
- [ ] Content width is capped for readability where needed
- [ ] Material/Cupertino adaptation is applied where it improves UX
- [ ] Accessibility text scaling does not break the layout
