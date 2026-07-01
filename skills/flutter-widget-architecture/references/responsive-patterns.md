# Responsive Layout Patterns: LayoutBuilder, MediaQuery, Breakpoints

Sources: Flutter responsive design documentation, Material design responsive guidelines, production patterns

Covers: Building layouts that adapt to different screen sizes, orientations, and device types.

## MediaQuery: Device Information

MediaQuery provides information about the device and app window.

### Common MediaQuery Properties

```dart
final mediaQuery = MediaQuery.of(context);

// Screen dimensions
mediaQuery.size.width // Device width
mediaQuery.size.height // Device height

// Safe area (notches, status bar)
mediaQuery.padding.top // Status bar height
mediaQuery.viewInsets.bottom // Keyboard height

// Device properties
mediaQuery.devicePixelRatio // Pixel density
mediaQuery.orientation // Portrait or Landscape

// Text scaling
mediaQuery.textScaleFactor // User text size preference
```

### Pattern: Responsive Text

```dart
class ResponsiveText extends StatelessWidget {
  final String text;
  final TextStyle? baseStyle;

  const ResponsiveText(
    this.text, {
    this.baseStyle,
  });

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final screenWidth = mediaQuery.size.width;

    // Scale text based on screen width
    double fontSize;
    if (screenWidth < 600) {
      fontSize = 14; // Mobile
    } else if (screenWidth < 1200) {
      fontSize = 16; // Tablet
    } else {
      fontSize = 18; // Desktop
    }

    return Text(
      text,
      style: (baseStyle ?? TextStyle()).copyWith(fontSize: fontSize),
    );
  }
}
```

### Pattern: Avoiding Keyboard Overlap

```dart
class KeyboardAwareForm extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final keyboardHeight = mediaQuery.viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.only(bottom: keyboardHeight),
      child: Column(
        children: [
          TextField(decoration: InputDecoration(labelText: 'Name')),
          TextField(decoration: InputDecoration(labelText: 'Email')),
          SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {},
            child: Text('Submit'),
          ),
        ],
      ),
    );
  }
}
```

## LayoutBuilder: Parent Constraints

LayoutBuilder gives you the parent's constraints, allowing you to build different layouts based on available space.

### Pattern: Responsive Grid

```dart
class ResponsiveGrid extends StatelessWidget {
  final List<Widget> children;

  const ResponsiveGrid({required this.children});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Determine number of columns based on width
        int columns;
        if (constraints.maxWidth < 600) {
          columns = 1; // Mobile
        } else if (constraints.maxWidth < 1200) {
          columns = 2; // Tablet
        } else {
          columns = 3; // Desktop
        }

        return GridView.count(
          crossAxisCount: columns,
          children: children,
        );
      },
    );
  }
}

// Usage
ResponsiveGrid(
  children: [
    Card(child: Text('Item 1')),
    Card(child: Text('Item 2')),
    Card(child: Text('Item 3')),
  ],
)
```

### Pattern: Responsive Sidebar

```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget sidebar;
  final Widget content;

  const ResponsiveLayout({
    required this.sidebar,
    required this.content,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 800) {
          // Mobile: Stack sidebar and content
          return Column(
            children: [
              Expanded(child: content),
              Container(
                height: 200,
                child: sidebar,
              ),
            ],
          );
        } else {
          // Desktop: Side-by-side layout
          return Row(
            children: [
              SizedBox(width: 250, child: sidebar),
              Expanded(child: content),
            ],
          );
        }
      },
    );
  }
}
```

## Breakpoints

Define breakpoints for consistent responsive behavior across your app.

### Pattern: Breakpoint System

```dart
class Breakpoints {
  static const mobile = 600.0;
  static const tablet = 1200.0;
  static const desktop = 1920.0;
}

enum DeviceType { mobile, tablet, desktop }

extension DeviceTypeExtension on BuildContext {
  DeviceType get deviceType {
    final width = MediaQuery.of(this).size.width;
    if (width < Breakpoints.mobile) return DeviceType.mobile;
    if (width < Breakpoints.tablet) return DeviceType.tablet;
    return DeviceType.desktop;
  }

  bool get isMobile => deviceType == DeviceType.mobile;
  bool get isTablet => deviceType == DeviceType.tablet;
  bool get isDesktop => deviceType == DeviceType.desktop;
}

// Usage
class MyScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    if (context.isMobile) {
      return MobileLayout();
    } else if (context.isTablet) {
      return TabletLayout();
    } else {
      return DesktopLayout();
    }
  }
}
```

## Orientation-Aware Layouts

### Pattern: Orientation-Specific Layout

```dart
class OrientationAwareWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final orientation = MediaQuery.of(context).orientation;

    if (orientation == Orientation.portrait) {
      return PortraitLayout();
    } else {
      return LandscapeLayout();
    }
  }
}

class PortraitLayout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(child: Container(color: Colors.blue)),
        Expanded(child: Container(color: Colors.red)),
      ],
    );
  }
}

class LandscapeLayout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: Container(color: Colors.blue)),
        Expanded(child: Container(color: Colors.red)),
      ],
    );
  }
}
```

## Safe Area

Use SafeArea to avoid notches, status bars, and other system UI.

### Pattern: Safe Area Layout

```dart
class SafeAreaExample extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          Text('Below status bar'),
          Expanded(child: Container(color: Colors.blue)),
          Text('Above navigation bar'),
        ],
      ),
    );
  }
}

// Customize which edges to apply SafeArea
SafeArea(
  left: false, // Don't apply to left edge
  right: false, // Don't apply to right edge
  top: true, // Apply to top (status bar)
  bottom: true, // Apply to bottom (navigation bar)
  child: MyContent(),
)
```

## Adaptive Widgets

Flutter provides adaptive widgets that automatically use the appropriate design system.

### Pattern: Adaptive Button

```dart
class AdaptiveButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const AdaptiveButton({
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    // Use Material on Android, Cupertino on iOS
    if (Theme.of(context).platform == TargetPlatform.iOS) {
      return CupertinoButton(
        onPressed: onPressed,
        child: Text(label),
      );
    } else {
      return ElevatedButton(
        onPressed: onPressed,
        child: Text(label),
      );
    }
  }
}
```

### Pattern: Adaptive Dialog

```dart
Future<void> showAdaptiveDialog(BuildContext context) {
  if (Theme.of(context).platform == TargetPlatform.iOS) {
    return showCupertinoDialog(
      context: context,
      builder: (context) => CupertinoAlertDialog(
        title: Text('Confirm'),
        content: Text('Are you sure?'),
        actions: [
          CupertinoDialogAction(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          CupertinoDialogAction(
            onPressed: () => Navigator.pop(context),
            isDefaultAction: true,
            child: Text('OK'),
          ),
        ],
      ),
    );
  } else {
    return showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Confirm'),
        content: Text('Are you sure?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
}
```

## Responsive Image Sizing

### Pattern: Responsive Image

```dart
class ResponsiveImage extends StatelessWidget {
  final String imageUrl;

  const ResponsiveImage({required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Scale image based on available width
        final imageWidth = constraints.maxWidth;
        final imageHeight = imageWidth * 0.6; // 16:10 aspect ratio

        return Image.network(
          imageUrl,
          width: imageWidth,
          height: imageHeight,
          fit: BoxFit.cover,
        );
      },
    );
  }
}
```

## Responsive Padding and Spacing

### Pattern: Adaptive Spacing

```dart
class AdaptiveSpacing extends StatelessWidget {
  final Widget child;

  const AdaptiveSpacing({required this.child});

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final screenWidth = mediaQuery.size.width;

    // Adjust padding based on screen size
    double padding;
    if (screenWidth < 600) {
      padding = 16; // Mobile
    } else if (screenWidth < 1200) {
      padding = 24; // Tablet
    } else {
      padding = 32; // Desktop
    }

    return Padding(
      padding: EdgeInsets.all(padding),
      child: child,
    );
  }
}
```

## Complete Responsive App Example

```dart
class ResponsiveApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: ResponsiveHome(),
    );
  }
}

class ResponsiveHome extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Responsive App')),
      body: LayoutBuilder(
        builder: (context, constraints) {
          if (constraints.maxWidth < 600) {
            return MobileLayout();
          } else if (constraints.maxWidth < 1200) {
            return TabletLayout();
          } else {
            return DesktopLayout();
          }
        },
      ),
    );
  }
}

class MobileLayout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        children: [
          Container(height: 200, color: Colors.blue),
          Container(height: 200, color: Colors.red),
          Container(height: 200, color: Colors.green),
        ],
      ),
    );
  }
}

class TabletLayout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          flex: 1,
          child: Container(color: Colors.blue),
        ),
        Expanded(
          flex: 2,
          child: Column(
            children: [
              Expanded(child: Container(color: Colors.red)),
              Expanded(child: Container(color: Colors.green)),
            ],
          ),
        ),
      ],
    );
  }
}

class DesktopLayout extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          flex: 1,
          child: Container(color: Colors.blue),
        ),
        Expanded(
          flex: 2,
          child: Row(
            children: [
              Expanded(child: Container(color: Colors.red)),
              Expanded(child: Container(color: Colors.green)),
            ],
          ),
        ),
      ],
    );
  }
}
```

## Responsive Design Checklist

- [ ] Use MediaQuery for device information
- [ ] Use LayoutBuilder for parent constraints
- [ ] Define breakpoints for consistent behavior
- [ ] Test on multiple device sizes
- [ ] Use SafeArea for notches and system UI
- [ ] Adapt layouts for portrait and landscape
- [ ] Use adaptive widgets for platform-specific UI
- [ ] Scale text and spacing responsively
- [ ] Test keyboard behavior
- [ ] Optimize images for different screen sizes
