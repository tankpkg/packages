# Styling Patterns

Sources: React Native documentation (2025-2026), NativeWind v4 docs, Unistyles 2 docs, Tamagui docs, State of React Native 2025 survey

Covers: StyleSheet API, NativeWind v4 (Tailwind for RN), Unistyles 2, Tamagui, responsive design, dark mode, platform-specific styling, safe areas, and styling library selection.

## Styling Library Selection

| Library | Approach | Performance | Learning Curve | Best For |
|---------|----------|-------------|----------------|----------|
| StyleSheet | Plain objects | Baseline | Minimal | Simple apps, small teams |
| NativeWind v4 | Tailwind classes | Near-native | Low (if Tailwind known) | Web devs, rapid prototyping |
| Unistyles 2 | StyleSheet superset | Best-in-class | Low | Performance-critical, type-safe |
| Tamagui | Component library + compiler | Compiled output | Moderate | Design systems, cross-platform |

### Decision Matrix

| Signal | Recommendation |
|--------|---------------|
| Team knows Tailwind, web-first mindset | NativeWind v4 |
| Maximum runtime performance priority | Unistyles 2 |
| Building a component library / design system | Tamagui |
| Small project, no extra dependencies | StyleSheet.create |
| Need responsive breakpoints natively | Unistyles 2 or NativeWind |
| Want dark mode with zero config | NativeWind or Unistyles |

## StyleSheet API

The built-in styling system. Zero dependencies, maximum control.

```typescript
import { StyleSheet, View, Text } from 'react-native';

function Card({ title, children }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,       // Android shadow
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 8,
  },
});
```

### StyleSheet Best Practices

| Practice | Rationale |
|----------|-----------|
| Define styles outside component | Avoids recreation on re-render |
| Use `StyleSheet.create` | Enables validation and potential optimization |
| Compose with arrays | `style={[styles.base, styles.active]}` for conditional |
| Avoid inline objects | `style={{ flex: 1 }}` creates new object each render |
| Use `StyleSheet.flatten` | Merge computed styles when needed |

### Conditional Styles

```typescript
<View style={[
  styles.button,
  isActive && styles.buttonActive,
  isDisabled && styles.buttonDisabled,
]} />

// Or with dynamic values
const dynamicStyle = useMemo(() => ({
  opacity: isLoading ? 0.5 : 1,
  transform: [{ scale: isPressed ? 0.95 : 1 }],
}), [isLoading, isPressed]);
```

### Platform-Specific Styles

```typescript
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  shadow: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
});
```

## NativeWind v4

Tailwind CSS for React Native. Write `className` props, compiled to optimized StyleSheet at build time.

### Setup

```bash
npx expo install nativewind tailwindcss react-native-css-interop
```

```javascript
// tailwind.config.js
module.exports = {
  content: ['./app/**/*.{js,jsx,ts,tsx}', './components/**/*.{js,jsx,ts,tsx}'],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
      },
    },
  },
};
```

```javascript
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxImportSource: 'nativewind' }],
      'nativewind/babel',
    ],
  };
};
```

### Usage

```typescript
import { View, Text, Pressable } from 'react-native';

function Card() {
  return (
    <View className="bg-white rounded-xl p-4 shadow-md dark:bg-gray-800">
      <Text className="text-lg font-semibold text-gray-900 dark:text-white">
        Card Title
      </Text>
      <Pressable className="mt-4 bg-brand-500 rounded-lg py-3 px-6 active:bg-brand-600">
        <Text className="text-white text-center font-medium">Action</Text>
      </Pressable>
    </View>
  );
}
```

### NativeWind Features

| Feature | Syntax | Notes |
|---------|--------|-------|
| Dark mode | `dark:bg-gray-800` | Automatic via `useColorScheme` |
| Responsive | `md:flex-row` | Based on window width |
| Platform | `ios:pt-12 android:pt-8` | Platform-specific classes |
| Hover/Press | `active:scale-95` | Touch feedback states |
| CSS variables | `var(--color-brand)` | Theme tokens via CSS vars |
| Animations | `animate-pulse` | Basic keyframe animations |

### NativeWind Limitations

| Limitation | Workaround |
|-----------|-----------|
| No arbitrary animations | Use Reanimated for complex animations |
| Limited gradient support | Use `expo-linear-gradient` |
| Web-specific classes ignored | Check RN compatibility of Tailwind classes |
| Build step required | Metro plugin handles compilation |

## Unistyles 2

Type-safe, high-performance styling with breakpoints, themes, and runtime adaptivity. StyleSheet API superset.

### Setup

```bash
npx expo install react-native-unistyles
```

### Theme and Breakpoint Configuration

```typescript
// styles/unistyles.ts
import { UnistylesRegistry } from 'react-native-unistyles';

const lightTheme = {
  colors: {
    background: '#ffffff',
    text: '#1a1a1a',
    primary: '#3b82f6',
    surface: '#f8fafc',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
};

const darkTheme = {
  colors: {
    background: '#0f172a',
    text: '#f1f5f9',
    primary: '#60a5fa',
    surface: '#1e293b',
  },
  spacing: lightTheme.spacing,
};

const breakpoints = {
  xs: 0,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
};

type AppThemes = { light: typeof lightTheme; dark: typeof darkTheme };

declare module 'react-native-unistyles' {
  export interface UnistylesThemes extends AppThemes {}
  export interface UnistylesBreakpoints extends typeof breakpoints {}
}

UnistylesRegistry
  .addBreakpoints(breakpoints)
  .addThemes({ light: lightTheme, dark: darkTheme })
  .addConfig({ adaptiveThemes: true }); // Auto dark mode
```

### Usage

```typescript
import { createStyleSheet, useStyles } from 'react-native-unistyles';

function Card() {
  const { styles, theme } = useStyles(stylesheet);
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Card Title</Text>
    </View>
  );
}

const stylesheet = createStyleSheet((theme) => ({
  container: {
    backgroundColor: theme.colors.surface,
    borderRadius: 12,
    padding: theme.spacing.md,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.colors.text,
  },
}));
```

### Responsive Breakpoints

```typescript
const stylesheet = createStyleSheet((theme, runtime) => ({
  container: {
    flexDirection: {
      xs: 'column',
      md: 'row',
    },
    padding: {
      xs: theme.spacing.sm,
      md: theme.spacing.lg,
    },
  },
}));
```

## Tamagui

Component library with an optimizing compiler. Extracts styles to atomic CSS at build time.

### When to Use Tamagui

| Signal | Recommendation |
|--------|---------------|
| Building a design system | Strong fit |
| Cross-platform (web + native) | Strong fit |
| Need pre-built components | Use Tamagui component library |
| Simple app, no design system | Overkill, use StyleSheet or NativeWind |
| Maximum bundle size sensitivity | Consider alternatives (compiler adds weight) |

## Dark Mode

### React Native Built-in

```typescript
import { useColorScheme } from 'react-native';

function App() {
  const colorScheme = useColorScheme(); // 'light' | 'dark'
  const isDark = colorScheme === 'dark';

  return (
    <View style={{ backgroundColor: isDark ? '#0f172a' : '#ffffff' }}>
      <Text style={{ color: isDark ? '#f1f5f9' : '#1a1a1a' }}>Hello</Text>
    </View>
  );
}
```

### With NativeWind

```typescript
// Automatic dark mode support
<View className="bg-white dark:bg-slate-900">
  <Text className="text-gray-900 dark:text-gray-100">Hello</Text>
</View>
```

### With Unistyles

Configure `adaptiveThemes: true` and define `light`/`dark` themes. Unistyles auto-switches based on system preference.

## Safe Areas

Handle device notches, status bars, and home indicators:

```typescript
import { SafeAreaView } from 'react-native-safe-area-context';

function Screen() {
  return (
    <SafeAreaView style={{ flex: 1 }} edges={['top', 'bottom']}>
      <Content />
    </SafeAreaView>
  );
}
```

Use `useSafeAreaInsets()` for granular control:

```typescript
import { useSafeAreaInsets } from 'react-native-safe-area-context';

function Header() {
  const insets = useSafeAreaInsets();
  return (
    <View style={{ paddingTop: insets.top + 8 }}>
      <Text>Header</Text>
    </View>
  );
}
```

### Safe Area with NativeWind

```typescript
// Uses CSS env() under the hood
<View className="pt-safe">
  <Text>Below status bar</Text>
</View>
```

## Responsive Design Patterns

### Dimensions API

```typescript
import { useWindowDimensions } from 'react-native';

function ResponsiveGrid() {
  const { width } = useWindowDimensions();
  const columns = width > 768 ? 3 : width > 480 ? 2 : 1;
  const itemWidth = width / columns - 16;

  return (
    <FlatList
      data={items}
      numColumns={columns}
      key={columns} // Force re-render on column change
      renderItem={({ item }) => (
        <View style={{ width: itemWidth, margin: 8 }} />
      )}
    />
  );
}
```

### Flexbox Patterns

| Pattern | Usage | Code |
|---------|-------|------|
| Center content | Login screens, empty states | `justifyContent: 'center', alignItems: 'center'` |
| Space between | Navigation bars, toolbars | `flexDirection: 'row', justifyContent: 'space-between'` |
| Grow to fill | Main content area | `flex: 1` |
| Fixed + flexible | Sidebar + content | `width: 250` + `flex: 1` |
| Wrap items | Tag lists, chips | `flexWrap: 'wrap'` |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Inline style objects | New object every render, breaks memoization | Use `StyleSheet.create` outside component |
| Missing `flex: 1` on containers | Content collapses to 0 height | Add `flex: 1` up the view hierarchy |
| Using `padding` for safe area | Hardcoded values wrong on different devices | Use `react-native-safe-area-context` |
| Web CSS properties in RN | `margin: '0 auto'` invalid, no CSS cascade | Use RN flexbox: `alignSelf: 'center'` |
| Text outside `<Text>` | Crash on native | All text must be inside `<Text>` components |
| Percentage dimensions without parent | Layout breaks | Parent must have defined dimensions for `%` to work |
