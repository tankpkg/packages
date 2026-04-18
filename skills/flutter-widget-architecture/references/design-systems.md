# Design Systems: Material 3 and Cupertino

Sources: Material Design 3 specification, Apple Human Interface Guidelines, Flutter design system documentation

Covers: Material 3 and Cupertino design system usage, theming, component patterns, and platform-specific design.

## Material 3 Design System

Material 3 is Google's modern design system with dynamic color, improved typography, and refined components.

### Material 3 Theme

```dart
void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Material 3 App',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.light,
        ),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          brightness: Brightness.dark,
        ),
      ),
      themeMode: ThemeMode.system, // Follow system theme
      home: Home(),
    );
  }
}
```

### Dynamic Color (Material You)

Dynamic color adapts to the user's wallpaper on Android 12+.

```dart
class DynamicColorApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return DynamicColorBuilder(
      builder: (lightDynamic, darkDynamic) {
        ColorScheme lightColorScheme;
        ColorScheme darkColorScheme;

        if (lightDynamic != null && darkDynamic != null) {
          // Use dynamic colors from wallpaper
          lightColorScheme = lightDynamic.harmonized();
          darkColorScheme = darkDynamic.harmonized();
        } else {
          // Fallback to seed color
          lightColorScheme = ColorScheme.fromSeed(seedColor: Colors.blue);
          darkColorScheme = ColorScheme.fromSeed(
            seedColor: Colors.blue,
            brightness: Brightness.dark,
          );
        }

        return MaterialApp(
          theme: ThemeData(
            useMaterial3: true,
            colorScheme: lightColorScheme,
          ),
          darkTheme: ThemeData(
            useMaterial3: true,
            colorScheme: darkColorScheme,
          ),
          home: Home(),
        );
      },
    );
  }
}
```

### Material 3 Components

```dart
// Elevated Button (primary action)
ElevatedButton(
  onPressed: () {},
  child: Text('Elevated Button'),
)

// Filled Button (secondary action)
FilledButton(
  onPressed: () {},
  child: Text('Filled Button'),
)

// Outlined Button (tertiary action)
OutlinedButton(
  onPressed: () {},
  child: Text('Outlined Button'),
)

// Text Button (lowest priority)
TextButton(
  onPressed: () {},
  child: Text('Text Button'),
)

// FAB with icon
FloatingActionButton(
  onPressed: () {},
  child: Icon(Icons.add),
)

// Extended FAB
FloatingActionButton.extended(
  onPressed: () {},
  icon: Icon(Icons.add),
  label: Text('Add'),
)

// Card (elevated surface)
Card(
  child: Padding(
    padding: EdgeInsets.all(16),
    child: Text('Card content'),
  ),
)

// Chip (compact element)
Chip(
  label: Text('Chip'),
  onDeleted: () {},
)

// Input Chip (user input)
InputChip(
  label: Text('Input'),
  onDeleted: () {},
)

// Filter Chip (filtering)
FilterChip(
  label: Text('Filter'),
  selected: true,
  onSelected: (selected) {},
)

// Choice Chip (single selection)
ChoiceChip(
  label: Text('Choice'),
  selected: true,
  onSelected: (selected) {},
)
```

### Material 3 Typography

```dart
class TypographyExample extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      children: [
        Text('Display Large', style: textTheme.displayLarge),
        Text('Display Medium', style: textTheme.displayMedium),
        Text('Display Small', style: textTheme.displaySmall),
        Text('Headline Large', style: textTheme.headlineLarge),
        Text('Headline Medium', style: textTheme.headlineMedium),
        Text('Headline Small', style: textTheme.headlineSmall),
        Text('Title Large', style: textTheme.titleLarge),
        Text('Title Medium', style: textTheme.titleMedium),
        Text('Title Small', style: textTheme.titleSmall),
        Text('Body Large', style: textTheme.bodyLarge),
        Text('Body Medium', style: textTheme.bodyMedium),
        Text('Body Small', style: textTheme.bodySmall),
        Text('Label Large', style: textTheme.labelLarge),
        Text('Label Medium', style: textTheme.labelMedium),
        Text('Label Small', style: textTheme.labelSmall),
      ],
    );
  }
}
```

### Material 3 Color System

```dart
class ColorSystemExample extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      children: [
        // Primary colors
        Container(
          color: colorScheme.primary,
          child: Text('Primary'),
        ),
        Container(
          color: colorScheme.onPrimary,
          child: Text('On Primary'),
        ),
        Container(
          color: colorScheme.primaryContainer,
          child: Text('Primary Container'),
        ),
        Container(
          color: colorScheme.onPrimaryContainer,
          child: Text('On Primary Container'),
        ),

        // Secondary colors
        Container(
          color: colorScheme.secondary,
          child: Text('Secondary'),
        ),
        Container(
          color: colorScheme.onSecondary,
          child: Text('On Secondary'),
        ),

        // Tertiary colors
        Container(
          color: colorScheme.tertiary,
          child: Text('Tertiary'),
        ),

        // Error colors
        Container(
          color: colorScheme.error,
          child: Text('Error'),
        ),

        // Surface colors
        Container(
          color: colorScheme.surface,
          child: Text('Surface'),
        ),
        Container(
          color: colorScheme.surfaceVariant,
          child: Text('Surface Variant'),
        ),
      ],
    );
  }
}
```

## Cupertino Design System

Cupertino is Apple's iOS design system with native iOS look and feel.

### Cupertino Theme

```dart
void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CupertinoApp(
      title: 'Cupertino App',
      theme: CupertinoThemeData(
        primaryColor: CupertinoColors.activeBlue,
        brightness: Brightness.light,
      ),
      home: Home(),
    );
  }
}
```

### Cupertino Components

```dart
// Navigation bar (iOS bottom tab bar)
CupertinoTabScaffold(
  tabBar: CupertinoTabBar(
    items: [
      BottomNavigationBarItem(
        icon: Icon(CupertinoIcons.home),
        label: 'Home',
      ),
      BottomNavigationBarItem(
        icon: Icon(CupertinoIcons.search),
        label: 'Search',
      ),
    ],
  ),
  tabBuilder: (context, index) {
    return CupertinoTabView(
      builder: (context) => index == 0 ? HomeScreen() : SearchScreen(),
    );
  },
)

// Button
CupertinoButton(
  onPressed: () {},
  child: Text('Button'),
)

// Filled button
CupertinoButton.filled(
  onPressed: () {},
  child: Text('Filled Button'),
)

// Dialog
showCupertinoDialog(
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
)

// Action sheet
showCupertinoModalPopup(
  context: context,
  builder: (context) => CupertinoActionSheetAction(
    actions: [
      CupertinoActionSheetAction(
        onPressed: () => Navigator.pop(context),
        child: Text('Option 1'),
      ),
      CupertinoActionSheetAction(
        onPressed: () => Navigator.pop(context),
        child: Text('Option 2'),
      ),
    ],
    cancelButton: CupertinoActionSheetAction(
      onPressed: () => Navigator.pop(context),
      isDefaultAction: true,
      child: Text('Cancel'),
    ),
  ),
)

// Picker
CupertinoDatePicker(
  onDateTimeChanged: (DateTime value) {},
)

// Segmented control
CupertinoSegmentedControl<int>(
  children: {
    0: Text('Option 1'),
    1: Text('Option 2'),
    2: Text('Option 3'),
  },
  onValueChanged: (value) {},
)

// Slider
CupertinoSlider(
  value: 50,
  min: 0,
  max: 100,
  onChanged: (value) {},
)

// Switch
CupertinoSwitch(
  value: true,
  onChanged: (value) {},
)

// Activity indicator (spinner)
CupertinoActivityIndicator()
```

## Cross-Platform Design

### Pattern: Adaptive Design System

```dart
class AdaptiveTheme {
  static ThemeData buildTheme(BuildContext context) {
    final platform = Theme.of(context).platform;

    if (platform == TargetPlatform.iOS) {
      return _buildCupertinoTheme();
    } else {
      return _buildMaterialTheme();
    }
  }

  static ThemeData _buildMaterialTheme() {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
    );
  }

  static CupertinoThemeData _buildCupertinoTheme() {
    return CupertinoThemeData(
      primaryColor: CupertinoColors.activeBlue,
    );
  }
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: AdaptiveTheme.buildTheme(context),
      home: Home(),
    );
  }
}
```

### Pattern: Platform-Specific Components

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
    final platform = Theme.of(context).platform;

    if (platform == TargetPlatform.iOS) {
      return CupertinoButton.filled(
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

class AdaptiveDialog extends StatelessWidget {
  final String title;
  final String message;
  final VoidCallback onConfirm;

  const AdaptiveDialog({
    required this.title,
    required this.message,
    required this.onConfirm,
  });

  @override
  Widget build(BuildContext context) {
    final platform = Theme.of(context).platform;

    if (platform == TargetPlatform.iOS) {
      return CupertinoAlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          CupertinoDialogAction(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          CupertinoDialogAction(
            onPressed: () {
              onConfirm();
              Navigator.pop(context);
            },
            isDefaultAction: true,
            child: Text('OK'),
          ),
        ],
      );
    } else {
      return AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              onConfirm();
              Navigator.pop(context);
            },
            child: Text('OK'),
          ),
        ],
      );
    }
  }
}
```

## Custom Theme Extension

```dart
class CustomColors extends ThemeExtension<CustomColors> {
  final Color success;
  final Color warning;
  final Color info;

  CustomColors({
    required this.success,
    required this.warning,
    required this.info,
  });

  @override
  ThemeExtension<CustomColors> copyWith({
    Color? success,
    Color? warning,
    Color? info,
  }) {
    return CustomColors(
      success: success ?? this.success,
      warning: warning ?? this.warning,
      info: info ?? this.info,
    );
  }

  @override
  ThemeExtension<CustomColors> lerp(
    ThemeExtension<CustomColors>? other,
    double t,
  ) {
    if (other is! CustomColors) return this;
    return CustomColors(
      success: Color.lerp(success, other.success, t) ?? success,
      warning: Color.lerp(warning, other.warning, t) ?? warning,
      info: Color.lerp(info, other.info, t) ?? info,
    );
  }
}

// Usage
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        extensions: [
          CustomColors(
            success: Colors.green,
            warning: Colors.orange,
            info: Colors.blue,
          ),
        ],
      ),
      home: Home(),
    );
  }
}

// Access custom colors
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final customColors = Theme.of(context).extension<CustomColors>();
    return Container(
      color: customColors?.success,
      child: Text('Success'),
    );
  }
}
```

## Design System Best Practices

1. **Consistency** — Use the design system consistently across the app
2. **Accessibility** — Ensure sufficient color contrast and touch targets
3. **Theming** — Support light and dark modes
4. **Typography** — Use the design system's type scale
5. **Spacing** — Use consistent spacing and padding
6. **Components** — Use pre-built components from the design system
7. **Customization** — Extend the design system for custom needs
8. **Testing** — Test on multiple devices and platforms
