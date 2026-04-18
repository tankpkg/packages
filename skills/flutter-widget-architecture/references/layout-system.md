# Layout System: Constraints, RenderBox, Flex, Stack, Sliver, CustomMultiChildLayout

Sources: Flutter rendering pipeline documentation, layout system deep dives, production layout patterns

Covers: How constraints flow through the widget tree, RenderBox sizing, flex layouts, stacking, slivers, and custom layouts.

## Constraint System: The Foundation

Flutter's layout system is based on constraints flowing down and sizes flowing up.

### The Rule

1. **Parent passes constraints to child** — "You can be at most 300 wide and 200 tall"
2. **Child respects constraints and reports size** — "I'm 250 wide and 150 tall"
3. **Parent positions child** — "I'll put you at (10, 20)"

### BoxConstraints

```dart
// BoxConstraints defines min/max width and height
BoxConstraints(
  minWidth: 0,
  maxWidth: 300,
  minHeight: 0,
  maxHeight: 200,
)

// Common constructors
BoxConstraints.tight(Size(100, 100)) // Exact size
BoxConstraints.expand() // Fill parent
BoxConstraints.loose(Size(300, 200)) // Max size, min is 0
```

### Pattern: Understanding Constraints

```dart
class ConstraintDebugger extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 300,
      height: 200,
      color: Colors.blue,
      child: Builder(
        builder: (context) {
          final constraints = context.constraints;
          return Center(
            child: Text(
              'Max: ${constraints.maxWidth}x${constraints.maxHeight}\n'
              'Min: ${constraints.minWidth}x${constraints.minHeight}',
            ),
          );
        },
      ),
    );
  }
}
```

## ConstrainedBox and SizedBox

Use these to impose constraints on children.

### ConstrainedBox

Imposes additional constraints on a child. Child must respect both parent and ConstrainedBox constraints.

```dart
// Child can be at most 200 wide
ConstrainedBox(
  constraints: BoxConstraints(maxWidth: 200),
  child: Container(
    width: 300, // Ignored! Constrained to 200
    height: 100,
    color: Colors.blue,
  ),
)

// Minimum size
ConstrainedBox(
  constraints: BoxConstraints(minWidth: 100, minHeight: 100),
  child: Container(
    width: 50, // Expanded to 100
    height: 50, // Expanded to 100
    color: Colors.blue,
  ),
)
```

### SizedBox

Gives a child a specific size. Simpler than ConstrainedBox for fixed sizes.

```dart
// Fixed size
SizedBox(
  width: 100,
  height: 100,
  child: Container(color: Colors.blue),
)

// Spacer
SizedBox(height: 16) // Vertical space
SizedBox(width: 16) // Horizontal space

// Expand to fill
SizedBox.expand(child: Container(color: Colors.blue))

// Shrink to nothing
SizedBox.shrink() // Used for invisible widgets
```

## Flex: Row and Column

Flex widgets distribute space among children along an axis.

### Row and Column Basics

```dart
// Row: horizontal layout
Row(
  children: [
    Container(width: 100, height: 100, color: Colors.red),
    Container(width: 100, height: 100, color: Colors.blue),
  ],
)

// Column: vertical layout
Column(
  children: [
    Container(width: 100, height: 100, color: Colors.red),
    Container(width: 100, height: 100, color: Colors.blue),
  ],
)
```

### Expanded and Flexible

Expanded and Flexible make children take up available space.

```dart
// Expanded: takes all available space
Row(
  children: [
    Container(width: 100, color: Colors.red),
    Expanded(
      child: Container(color: Colors.blue), // Takes remaining space
    ),
  ],
)

// Flexible: takes available space with flex factor
Row(
  children: [
    Flexible(
      flex: 1,
      child: Container(color: Colors.red),
    ),
    Flexible(
      flex: 2,
      child: Container(color: Colors.blue), // Takes 2x space
    ),
  ],
)

// Flexible with fit
Flexible(
  fit: FlexFit.loose, // Child can be smaller than available space
  child: Container(color: Colors.red),
)

Flexible(
  fit: FlexFit.tight, // Child must fill available space
  child: Container(color: Colors.red),
)
```

### MainAxisAlignment and CrossAxisAlignment

```dart
Row(
  mainAxisAlignment: MainAxisAlignment.start, // Left
  mainAxisAlignment: MainAxisAlignment.center, // Center
  mainAxisAlignment: MainAxisAlignment.end, // Right
  mainAxisAlignment: MainAxisAlignment.spaceBetween, // Space between
  mainAxisAlignment: MainAxisAlignment.spaceAround, // Space around
  mainAxisAlignment: MainAxisAlignment.spaceEvenly, // Equal space
  crossAxisAlignment: CrossAxisAlignment.start, // Top
  crossAxisAlignment: CrossAxisAlignment.center, // Middle
  crossAxisAlignment: CrossAxisAlignment.end, // Bottom
  crossAxisAlignment: CrossAxisAlignment.stretch, // Fill height
  children: [...],
)
```

### Pattern: Responsive Flex Layout

```dart
class ResponsiveLayout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header
        Container(
          height: 60,
          color: Colors.blue,
          child: Center(child: Text('Header')),
        ),
        // Content
        Expanded(
          child: Row(
            children: [
              // Sidebar
              Container(
                width: 200,
                color: Colors.grey[300],
                child: Center(child: Text('Sidebar')),
              ),
              // Main content
              Expanded(
                child: Container(
                  color: Colors.white,
                  child: Center(child: Text('Main Content')),
                ),
              ),
            ],
          ),
        ),
        // Footer
        Container(
          height: 60,
          color: Colors.blue,
          child: Center(child: Text('Footer')),
        ),
      ],
    );
  }
}
```

## Stack and Positioned

Stack layers widgets on top of each other. Positioned places children at absolute positions.

### Stack Basics

```dart
Stack(
  children: [
    // Background
    Container(
      width: 200,
      height: 200,
      color: Colors.blue,
    ),
    // Overlay
    Container(
      width: 100,
      height: 100,
      color: Colors.red,
    ),
  ],
)
```

### Positioned

Positioned places children at specific offsets within a Stack.

```dart
Stack(
  children: [
    Container(
      width: 200,
      height: 200,
      color: Colors.blue,
    ),
    Positioned(
      top: 10,
      left: 10,
      child: Container(
        width: 50,
        height: 50,
        color: Colors.red,
      ),
    ),
    Positioned(
      bottom: 10,
      right: 10,
      child: Container(
        width: 50,
        height: 50,
        color: Colors.green,
      ),
    ),
  ],
)
```

### Positioned.fill

Positioned.fill makes a child fill the entire Stack.

```dart
Stack(
  children: [
    Container(color: Colors.blue),
    Positioned.fill(
      child: Container(
        color: Colors.red.withOpacity(0.5),
      ),
    ),
  ],
)
```

### Pattern: Floating Action Button

```dart
class FloatingActionButtonExample extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Main content
        ListView(
          children: List.generate(
            20,
            (i) => ListTile(title: Text('Item $i')),
          ),
        ),
        // Floating button
        Positioned(
          bottom: 16,
          right: 16,
          child: FloatingActionButton(
            onPressed: () {},
            child: Icon(Icons.add),
          ),
        ),
      ],
    );
  }
}
```

## Sliver Widgets

Slivers are efficient for scrollable content. They integrate with the scroll physics and only build visible items.

### CustomScrollView and Slivers

```dart
CustomScrollView(
  slivers: [
    // Sliver app bar
    SliverAppBar(
      title: Text('Title'),
      floating: true,
      snap: true,
    ),
    // Sliver list
    SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) => ListTile(title: Text('Item $i')),
        childCount: 100,
      ),
    ),
  ],
)
```

### Common Slivers

```dart
// SliverAppBar: App bar that scrolls
SliverAppBar(
  title: Text('Title'),
  expandedHeight: 200,
  flexibleSpace: FlexibleSpaceBar(
    background: Image.network('...', fit: BoxFit.cover),
  ),
)

// SliverList: Scrollable list
SliverList(
  delegate: SliverChildBuilderDelegate(
    (context, index) => ListTile(title: Text('Item $index')),
    childCount: 100,
  ),
)

// SliverGrid: Scrollable grid
SliverGrid(
  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
    crossAxisCount: 2,
  ),
  delegate: SliverChildBuilderDelegate(
    (context, index) => Container(color: Colors.blue),
    childCount: 100,
  ),
)

// SliverToBoxAdapter: Non-sliver widget in CustomScrollView
SliverToBoxAdapter(
  child: Container(height: 100, color: Colors.red),
)

// SliverPersistentHeader: Header that sticks while scrolling
SliverPersistentHeader(
  delegate: MySliverPersistentHeaderDelegate(),
  pinned: true,
)
```

### Pattern: Collapsing App Bar

```dart
class CollapsingAppBarExample extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 200,
          floating: false,
          pinned: true,
          flexibleSpace: FlexibleSpaceBar(
            title: Text('Collapsing Header'),
            background: Container(
              color: Colors.blue,
              child: Center(child: Text('Background')),
            ),
          ),
        ),
        SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) => ListTile(
              title: Text('Item $index'),
            ),
            childCount: 50,
          ),
        ),
      ],
    );
  }
}
```

## CustomMultiChildLayout

CustomMultiChildLayout gives full control over child positioning and sizing.

### Pattern: Custom Layout

```dart
class CustomLayoutDelegate extends MultiChildLayoutDelegate {
  @override
  void performLayout(Size size) {
    // Layout child 0 at top-left
    layoutChild(0, BoxConstraints.tight(Size(100, 100)));
    positionChild(0, Offset(0, 0));

    // Layout child 1 at bottom-right
    layoutChild(1, BoxConstraints.tight(Size(100, 100)));
    positionChild(1, Offset(size.width - 100, size.height - 100));

    // Layout child 2 to fill remaining space
    layoutChild(
      2,
      BoxConstraints(
        maxWidth: size.width - 200,
        maxHeight: size.height - 100,
      ),
    );
    positionChild(2, Offset(100, 0));
  }

  @override
  bool shouldRelayout(CustomLayoutDelegate oldDelegate) => false;
}

class CustomLayoutExample extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CustomMultiChildLayout(
      delegate: CustomLayoutDelegate(),
      children: [
        LayoutId(
          id: 0,
          child: Container(color: Colors.red),
        ),
        LayoutId(
          id: 1,
          child: Container(color: Colors.blue),
        ),
        LayoutId(
          id: 2,
          child: Container(color: Colors.green),
        ),
      ],
    );
  }
}
```

## RenderObject and Custom Rendering

For advanced layouts, create custom RenderObjects.

### Pattern: Custom RenderObject

```dart
class CustomRenderWidget extends RenderObjectWidget {
  @override
  RenderObject createRenderObject(BuildContext context) {
    return RenderCustom();
  }
}

class RenderCustom extends RenderBox {
  @override
  void performLayout() {
    // Calculate size based on constraints
    size = constraints.biggest;
  }

  @override
  void paint(PaintingContext context, Offset offset) {
    // Draw on canvas
    context.canvas.drawRect(
      Rect.fromLTWH(offset.dx, offset.dy, size.width, size.height),
      Paint()..color = Colors.blue,
    );
  }
}
```

## Layout Debugging

### LayoutBuilder

Use LayoutBuilder to inspect parent constraints.

```dart
LayoutBuilder(
  builder: (context, constraints) {
    return Text(
      'Max width: ${constraints.maxWidth}',
    );
  },
)
```

### Debug Paint

Enable debug paint to visualize layout:

```dart
void main() {
  debugPaintSizeEnabled = true; // Show layout bounds
  runApp(MyApp());
}
```

### Performance Tips

1. Use `const` widgets to avoid rebuilds
2. Use `RepaintBoundary` for expensive paint operations
3. Use Slivers for large scrollable lists
4. Avoid deep widget nesting
5. Use `SingleChildRenderObjectWidget` for custom layouts
