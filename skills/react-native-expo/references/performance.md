# Performance Optimization

Sources: React Native performance documentation (2025-2026), Shopify FlashList documentation, Hermes engine documentation, Expo documentation, React Native New Architecture performance analysis

Covers: list rendering with FlashList, Hermes engine optimization, bundle splitting, image caching with expo-image, memory management, startup time optimization, New Architecture performance gains, and profiling tools.

## List Rendering

Lists are the most common performance bottleneck in React Native. The wrong approach causes dropped frames, high memory usage, and slow scrolling.

### FlashList vs FlatList

| Dimension | FlatList | FlashList |
|-----------|---------|-----------|
| Cell recycling | No (creates/destroys views) | Yes (reuses views like native UITableView) |
| Blank areas on fast scroll | Common | Rare (10x fewer blanks) |
| Memory usage | Proportional to rendered items | Constant (recycles) |
| Setup complexity | Built-in, no install | Requires `@shopify/flash-list` |
| `estimatedItemSize` | Not needed | Required (critical for performance) |

### FlashList Setup

```bash
npx expo install @shopify/flash-list
```

```typescript
import { FlashList } from '@shopify/flash-list';

function Feed({ posts }: { posts: Post[] }) {
  return (
    <FlashList
      data={posts}
      renderItem={({ item }) => <PostCard post={item} />}
      estimatedItemSize={200}  // Average item height in pixels
      keyExtractor={(item) => item.id}
      onEndReached={loadMore}
      onEndReachedThreshold={0.5}
    />
  );
}
```

### estimatedItemSize

The most important FlashList prop. Incorrect values cause blank areas:

| Value | Effect |
|-------|--------|
| Too small | Overestimates visible items, more blanks on scroll |
| Too large | Underestimates, fewer items pre-rendered |
| Accurate | Optimal recycling, minimal blanks |

Measure actual item height in development, then set `estimatedItemSize` to the average.

### List Performance Rules

| Rule | Rationale |
|------|-----------|
| Use `keyExtractor` with stable IDs | Prevents unnecessary re-renders on data change |
| Memoize `renderItem` component | `React.memo()` prevents re-render when props unchanged |
| Avoid inline functions in `renderItem` | Creates new closure each render |
| Use `getItemType` for heterogeneous lists | FlashList recycles by type, avoids layout shifts |
| Set `removeClippedSubviews={true}` on FlatList | Detaches offscreen views (Android optimization) |
| Avoid nesting scrollable views | "VirtualizedLists should never be nested" |

### Heterogeneous Lists

```typescript
<FlashList
  data={items}
  renderItem={({ item }) => {
    switch (item.type) {
      case 'header': return <SectionHeader item={item} />;
      case 'post': return <PostCard post={item} />;
      case 'ad': return <AdBanner ad={item} />;
    }
  }}
  getItemType={(item) => item.type}
  estimatedItemSize={150}
/>
```

`getItemType` tells FlashList to only recycle cells of the same type, preventing layout recalculation.

## Hermes Engine

Hermes is React Native's default JavaScript engine, optimized for mobile:

| Feature | V8/JSC | Hermes |
|---------|--------|--------|
| Compilation | JIT (Just-In-Time) | AOT (Ahead-Of-Time) bytecode |
| Startup time | Slower (parse + compile at launch) | Faster (pre-compiled bytecode) |
| Memory usage | Higher | Lower (optimized GC) |
| Bundle format | Plain JavaScript | Hermes bytecode (.hbc) |
| Debugging | Chrome DevTools | Chrome DevTools via Hermes |

### Hermes Optimization Tips

| Tip | Impact |
|-----|--------|
| Avoid large JSON at import time | Blocks startup; load async or lazy |
| Minimize `require()` calls at top level | Each require blocks startup thread |
| Use Hermes bytecode in production | Enabled by default with Expo |
| Profile with Hermes sampling profiler | Identifies hot functions |
| Avoid `eval()` and `new Function()` | Hermes does not support dynamic code evaluation |

### Profiling with Hermes

```bash
# Start profiling
npx react-native profile-hermes

# Or via Dev Menu:
# Dev Menu > Start/Stop Sampling Profiler
# Downloads .cpuprofile file
```

Open the `.cpuprofile` in Chrome DevTools > Performance tab for flame chart analysis.

## Bundle Optimization

### Analyzing Bundle Size

```bash
# Generate source maps
npx expo export --source-maps

# Analyze with source-map-explorer
npx source-map-explorer dist/_expo/static/js/*.js
```

### Reducing Bundle Size

| Technique | Savings | Implementation |
|-----------|---------|---------------|
| Tree shaking | 10-30% | Ensure `sideEffects: false` in package.json |
| Lazy imports | Startup time | `const Heavy = React.lazy(() => import('./Heavy'))` |
| Replace heavy libraries | Variable | dayjs instead of moment, lodash-es with tree shaking |
| Remove unused imports | 5-15% | TypeScript strict mode + ESLint |
| Platform-specific bundles | ~10% | Metro bundles per-platform automatically |

### Lazy Loading Screens

```typescript
import { lazy, Suspense } from 'react';

const SettingsScreen = lazy(() => import('./screens/SettingsScreen'));

function App() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <SettingsScreen />
    </Suspense>
  );
}
```

With Expo Router, lazy loading happens automatically per-route. Each route file is only loaded when navigated to.

## Image Optimization

### expo-image Caching

```typescript
import { Image } from 'expo-image';

<Image
  source={{ uri: imageUrl }}
  cachePolicy="memory-disk"   // Cache in memory and disk
  recyclingKey={item.id}       // Reuse in lists for smooth scrolling
  placeholder={{ blurhash }}   // Show placeholder while loading
  transition={200}             // Smooth fade-in
  contentFit="cover"
/>
```

### Image Caching Policies

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `memory-disk` | Cache in RAM + disk | Default for most images |
| `memory` | Cache in RAM only | Frequently changing images |
| `disk` | Cache on disk only | Large images, low memory devices |
| `none` | No caching | Real-time content (live feeds) |

### Image Size Guidelines

| Context | Max Resolution | Format |
|---------|---------------|--------|
| Thumbnails (lists) | 200x200 | WebP or JPEG (quality 80) |
| Full-screen photos | Device width x 2 | WebP or JPEG (quality 85) |
| Icons/illustrations | 100x100 | PNG or SVG |
| Backgrounds | 1080px wide max | WebP (quality 75) |

Resize images server-side. Never load 4000x3000 originals for a 100px thumbnail.

## Startup Time Optimization

### Measuring Startup

```typescript
import * as Sentry from '@sentry/react-native';

// Measure time to interactive
const startTime = Date.now();

export default function App() {
  useEffect(() => {
    const tti = Date.now() - startTime;
    Sentry.addBreadcrumb({ message: `TTI: ${tti}ms` });
  }, []);
}
```

### Startup Optimization Checklist

| Optimization | Impact | Implementation |
|-------------|--------|---------------|
| Defer non-critical initialization | High | Move analytics, crash reporting to after first render |
| Minimize root component tree | High | Lazy load tabs not shown on startup |
| Reduce font loading | Medium | Load only used weights; use system fonts where possible |
| Optimize splash-to-content transition | Perceived | Keep splash visible until first meaningful paint |
| Reduce AsyncStorage reads at startup | Medium | Migrate to MMKV (synchronous) |
| Avoid large JSON imports | Medium | Load config async, not at module scope |

### Splash Screen Timing

```typescript
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    async function prepare() {
      // Load minimum required data
      await Promise.all([
        loadFonts(),
        loadAuthState(),
        // Do NOT wait for: analytics, non-critical API calls
      ]);
      setAppReady(true);
    }
    prepare();
  }, []);

  useEffect(() => {
    if (appReady) SplashScreen.hideAsync();
  }, [appReady]);

  if (!appReady) return null;
  return <Stack />;
}
```

## Memory Management

### Common Memory Leaks

| Leak Source | Detection | Fix |
|-------------|-----------|-----|
| Uncleared listeners | Growing memory over time | Return cleanup from useEffect |
| Retained navigation state | Memory grows with navigation depth | Use `detachInactiveScreens` |
| Uncancelled async operations | setState after unmount | AbortController or cleanup flag |
| Large image cache | High memory warnings | Set cache limits, use `recyclingKey` |
| Global state accumulation | State grows indefinitely | Clear stale entries, use TTL |

### Preventing Leaks

```typescript
useEffect(() => {
  const controller = new AbortController();

  async function fetchData() {
    try {
      const response = await fetch(url, { signal: controller.signal });
      const data = await response.json();
      setData(data);
    } catch (e) {
      if (e.name !== 'AbortError') throw e;
    }
  }

  fetchData();
  return () => controller.abort();
}, [url]);
```

## Memoization Patterns

### When to Memoize

| Signal | Action |
|--------|--------|
| Expensive computation in render | `useMemo` |
| Callback passed to memoized child | `useCallback` |
| Component receives same props, renders expensive UI | `React.memo` |
| List item component | Always `React.memo` |
| Simple component, cheap render | Do NOT memoize (overhead not worth it) |

### List Item Memoization

```typescript
const PostCard = React.memo(function PostCard({ post }: { post: Post }) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{post.title}</Text>
      <Text style={styles.body}>{post.body}</Text>
    </View>
  );
});
```

### Re-render Debugging

```typescript
// Detect unnecessary re-renders in development
if (__DEV__) {
  const whyDidYouRender = require('@welldone-software/why-did-you-render');
  whyDidYouRender(React, { trackAllPureComponents: true });
}
```

## New Architecture Performance Gains

| Metric | Improvement | Mechanism |
|--------|------------|-----------|
| Startup time | 10-30% faster | Lazy TurboModule loading eliminates bridge init |
| Touch responsiveness | Synchronous | JSI eliminates async bridge latency |
| Layout calculation | Faster | C++ Yoga engine in Fabric, no bridge round-trips |
| Concurrent rendering | Enabled | Urgent updates (input) prioritized over background |
| Memory | Reduced | Immutable shadow tree with structural sharing |

For detailed New Architecture information, see `references/new-architecture.md`.

## Performance Profiling Workflow

1. **Identify**: Use Perf Monitor (Dev Menu) to spot frame drops
2. **Profile**: React DevTools Profiler for render timing
3. **Measure**: Hermes profiler for JS execution hotspots
4. **Fix**: Apply optimization (memo, FlashList, lazy load)
5. **Verify**: Re-profile to confirm improvement
6. **Monitor**: Sentry or Datadog for production performance tracking
