# Layouts and Responsive Design

Sources: Flutter layout documentation (flutter.dev 2025-2026), Flutter API reference (api.flutter.dev), Material Design 3 specification (m3.material.io), Apple Human Interface Guidelines (Cupertino)

Covers: constraint system, Flex layout, Stack, Slivers, LayoutBuilder, MediaQuery, responsive breakpoints, Material 3 theming, Cupertino widgets, and adaptive design.

## Constraint System

Flutter layout uses a single-pass model: constraints go down, sizes go up, parent sets position.

### BoxConstraints

| Situation | Constraint |
|----------|-----------|
| `Scaffold` body | Tight max width/height from screen |
| Child in `Row` | Width may be loose unless Expanded |
| Child in `ListView` | Main axis often unbounded |

### Common Constraint Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `RenderBox was not laid out` | No constraints (Column in Column) | Wrap in `Expanded` or `SizedBox` |
| `A RenderFlex overflowed` | Children exceed space | `SingleChildScrollView`, `Flexible`, or constrain children |
| `Unbounded height` in ListView | `ListView` inside `Column` | Wrap `ListView` in `Expanded` or `SizedBox(height:)` |

When overflow occurs, ask: what constraints did this widget receive?

## Flex Layout (Row and Column)

### Alignment

```dart
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  crossAxisAlignment: CrossAxisAlignment.center,
  children: [Text('Left'), Text('Right')],
)
```

### Expanded and Flexible

```dart
Row(children: [
  Expanded(flex: 2, child: Container(color: Colors.red)),   // 2/3 width
  Expanded(flex: 1, child: Container(color: Colors.blue)),  // 1/3 width
])
// Flexible: child can be SMALLER than allocated space
// Expanded: child MUST fill allocated space
```

### Spacing

```dart
// Preferred (Flutter 3.10+)
Column(spacing: 16, children: [Widget1(), Widget2(), Widget3()])

// Alternative
Column(children: [Widget1(), const SizedBox(height: 16), Widget2()])
```

## Stack

Overlay widgets. First child at bottom, last on top.

```dart
Stack(
  clipBehavior: Clip.none,
  children: [
    Positioned.fill(child: Image.network(url, fit: BoxFit.cover)),
    Positioned(
      bottom: 16, left: 16, right: 16,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.black54, borderRadius: BorderRadius.circular(8)),
        child: Text('Overlay', style: TextStyle(color: Colors.white)),
      ),
    ),
  ],
)
```

Use Stack when children overlap. If no overlap, Flex is better.

## Slivers

Scrollable layout primitives. Use `CustomScrollView` for mixed-content scrollable pages.

| Sliver | Purpose |
|--------|---------|
| `SliverAppBar` | Collapsible/pinned app bar |
| `SliverList` | Variable-height scrollable list |
| `SliverGrid` | Scrollable grid |
| `SliverToBoxAdapter` | Non-sliver widget in sliver context |
| `SliverPersistentHeader` | Sticky/shrinking header |
| `SliverFillRemaining` | Fill remaining viewport |
| `SliverPadding` | Padding around a sliver |

### Mixed Content Scroll

```dart
CustomScrollView(
  slivers: [
    SliverAppBar(
      expandedHeight: 200, pinned: true,
      flexibleSpace: FlexibleSpaceBar(
        title: const Text('Profile'),
        background: Image.network(coverUrl, fit: BoxFit.cover),
      ),
    ),
    SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: UserInfoCard(user: user),
      ),
    ),
    SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      sliver: SliverGrid.builder(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2, mainAxisSpacing: 12, crossAxisSpacing: 12),
        itemCount: photos.length,
        itemBuilder: (_, i) => PhotoTile(photo: photos[i]),
      ),
    ),
  ],
)
```

## LayoutBuilder

Inspect parent constraints to make layout decisions:

```dart
LayoutBuilder(builder: (context, constraints) {
  if (constraints.maxWidth > 900) return WideLayout(child: content);
  if (constraints.maxWidth > 600) return MediumLayout(child: content);
  return NarrowLayout(child: content);
})
```

### LayoutBuilder vs MediaQuery

| Tool | Responds To | Use |
|------|------------|-----|
| `LayoutBuilder` | Parent constraints | Responsive components |
| `MediaQuery.sizeOf(context)` | Full screen | App-level layout |
| `MediaQuery.orientationOf(context)` | Orientation | Orientation layouts |

Prefer `LayoutBuilder` for reusable components — adapts to wherever placed.

## Responsive Breakpoints

```dart
abstract class Breakpoints {
  static const double compact = 600;
  static const double medium = 840;
  static const double expanded = 1200;
}

class ResponsiveLayout extends StatelessWidget {
  final Widget compact, medium, expanded;
  const ResponsiveLayout({super.key, required this.compact,
    required this.medium, required this.expanded});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth >= Breakpoints.expanded) return expanded;
      if (constraints.maxWidth >= Breakpoints.medium) return medium;
      return compact;
    });
  }
}
```

## Material 3 Theming

### ColorScheme from Seed

```dart
MaterialApp(
  theme: ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF6750A4), brightness: Brightness.light),
    useMaterial3: true,
  ),
  darkTheme: ThemeData(
    colorScheme: ColorScheme.fromSeed(
      seedColor: const Color(0xFF6750A4), brightness: Brightness.dark),
    useMaterial3: true,
  ),
);
```

### Typography

```dart
Text('Headline', style: Theme.of(context).textTheme.headlineMedium);
Text('Body', style: Theme.of(context).textTheme.bodyLarge);
```

### Material 3 Widgets

| M3 Widget | Replaces |
|-----------|---------|
| `NavigationBar` | `BottomNavigationBar` |
| `NavigationRail` | Side nav for medium screens |
| `NavigationDrawer` | `Drawer` |
| `SearchBar` / `SearchAnchor` | Custom search |
| `FilledButton` | `ElevatedButton` (primary) |
| `SegmentedButton` | `ToggleButtons` |

## Cupertino (iOS) Widgets

```dart
// Adaptive widgets - platform-appropriate automatically
Switch.adaptive(value: val, onChanged: onChanged);
Slider.adaptive(value: val, onChanged: onChanged);
CircularProgressIndicator.adaptive();
```

### Platform-Specific

```dart
import 'dart:io' show Platform;

Widget buildButton() {
  if (Platform.isIOS) {
    return CupertinoButton.filled(child: Text('Save'), onPressed: _save);
  }
  return FilledButton(onPressed: _save, child: Text('Save'));
}
```

For web, use `kIsWeb` from `package:flutter/foundation.dart`.

## Navigation Shell Responsiveness

| Width | Navigation |
|-------|-----------|
| Phone | Bottom navigation bar |
| Tablet | Navigation rail |
| Desktop | Sidebar / split pane |

## Safe Areas and Insets

| Concern | Tool |
|--------|------|
| System notches / cutouts | `SafeArea` |
| Keyboard overlap | `MediaQuery.viewInsets` |
| Immersive content | Opt out, handle padding manually |

## Common Layout Patterns

| Pattern | Implementation |
|---------|---------------|
| Scrollable form | `SingleChildScrollView` + `Column` |
| Pull-to-refresh list | `RefreshIndicator` + `ListView.builder` |
| Grid gallery | `GridView.builder` + `SliverGridDelegateWithMaxCrossAxisExtent` |
| Sticky header list | `CustomScrollView` + `SliverPersistentHeader(pinned: true)` |
| Bottom sheet | `showModalBottomSheet` or `DraggableScrollableSheet` |
| Side-by-side on tablet | `LayoutBuilder` with breakpoint |

## Common Mistakes

| Mistake | Problem | Fix |
|--------|---------|-----|
| Hard-coding widths | Brittle across devices | Use constraints and breakpoints |
| Nested scroll views | Jank and gesture conflicts | Unify scroll context with slivers |
| Ignoring text scale | Clipped text | Test accessibility text sizes |
| Designing only for one phone | Poor tablet/web | Test multiple classes |
| Ignoring SafeArea | Bugs on real devices | Wrap layouts in SafeArea |
| Full-width text on desktop | Poor readability | Cap content width |
