# Navigation and Routing

Sources: GoRouter official documentation (pub.dev/packages/go_router 2025-2026), Flutter navigation documentation (flutter.dev), Flutter API reference for Navigator 2.0

Covers: GoRouter setup, ShellRoute and StatefulShellRoute for tabs, redirect guards, deep linking, path/query parameters, nested navigation, and migration from imperative Navigator.

## Why GoRouter

Imperative `Navigator.push` / `Navigator.pop` does not support URL-based navigation (web, deep links), declarative route definitions, route guards, or state restoration. GoRouter wraps Navigator 2.0 with a declarative, URL-based API.

## Basic Setup

```dart
final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(
      path: '/profile/:userId',
      builder: (_, state) {
        final userId = state.pathParameters['userId']!;
        return ProfileScreen(userId: userId);
      },
    ),
    GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
  ],
);

MaterialApp.router(routerConfig: router);
```

## Path and Query Parameters

```dart
GoRoute(
  path: '/products/:category',
  builder: (_, state) {
    final category = state.pathParameters['category']!;
    final sort = state.uri.queryParameters['sort'] ?? 'name';
    return ProductListScreen(category: category, sort: sort);
  },
),

// Navigate with parameters
context.go('/products/electronics?sort=price&page=2');
context.goNamed('productList', pathParameters: {'category': 'electronics'});
```

### go vs push

| Method | Behavior | Use |
|--------|----------|-----|
| `context.go('/path')` | Replaces navigation stack to match URL | Primary navigation (tabs, sections) |
| `context.push('/path')` | Pushes onto current stack | Drill-down (detail, modals) |
| `context.pop()` | Pops top route | Back navigation |
| `context.pushReplacement('/path')` | Replaces current route | Login to Home (no back) |

Rule: use `go` for top-level navigation, `push` for detail navigation within a section.

## ShellRoute (Shared Scaffold)

Wrap routes in a shared layout:

```dart
ShellRoute(
  builder: (context, state, child) => ScaffoldWithNavBar(child: child),
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/search', builder: (_, __) => const SearchScreen()),
    GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
  ],
),
```

## StatefulShellRoute (Persistent Tabs)

Preserves each tab's navigation stack independently:

```dart
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) {
    return ScaffoldWithNavBar(navigationShell: navigationShell);
  },
  branches: [
    StatefulShellBranch(routes: [
      GoRoute(
        path: '/home',
        builder: (_, __) => const HomeScreen(),
        routes: [
          GoRoute(
            path: 'detail/:id',
            builder: (_, state) => DetailScreen(id: state.pathParameters['id']!),
          ),
        ],
      ),
    ]),
    StatefulShellBranch(routes: [
      GoRoute(path: '/search', builder: (_, __) => const SearchScreen()),
    ]),
    StatefulShellBranch(routes: [
      GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
    ]),
  ],
),
```

The scaffold uses `navigationShell.goBranch(index)` to switch tabs:

```dart
class ScaffoldWithNavBar extends StatelessWidget {
  const ScaffoldWithNavBar({super.key, required this.navigationShell});
  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: (index) {
          navigationShell.goBranch(index,
            initialLocation: index == navigationShell.currentIndex);
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
```

### ShellRoute vs StatefulShellRoute

| Feature | ShellRoute | StatefulShellRoute |
|---------|-----------|-------------------|
| Shared scaffold | Yes | Yes |
| Preserves tab state | No | Yes (separate Navigators) |
| Independent back stacks | No | Yes |
| Memory usage | Lower | Higher |
| Use case | Simple shared layout | Bottom nav with persistent tabs |

## Redirect Guards

```dart
final router = GoRouter(
  redirect: (context, state) {
    final isLoggedIn = ref.read(authProvider).isAuthenticated;
    final isLoginRoute = state.matchedLocation == '/login';
    if (!isLoggedIn && !isLoginRoute) return '/login';
    if (isLoggedIn && isLoginRoute) return '/';
    return null; // No redirect
  },
  routes: [...],
);
```

### Per-Route Redirect

```dart
GoRoute(
  path: '/admin',
  redirect: (context, state) {
    final isAdmin = ref.read(userProvider).valueOrNull?.isAdmin ?? false;
    if (!isAdmin) return '/unauthorized';
    return null;
  },
  builder: (_, __) => const AdminPanel(),
),
```

### Redirect with Riverpod

```dart
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  return GoRouter(
    refreshListenable: authState,
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isLoginRoute = state.matchedLocation == '/login';
      if (!isLoggedIn && !isLoginRoute) return '/login';
      if (isLoggedIn && isLoginRoute) return '/';
      return null;
    },
    routes: [...],
  );
});
```

## Deep Linking

GoRouter handles deep links automatically. Configure platform settings:

### Android (AndroidManifest.xml)

```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="myapp.com" />
</intent-filter>
```

### iOS (Info.plist)

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array><string>myapp</string></array>
  </dict>
</array>
```

The route configuration IS the deep link configuration — no extra Dart code needed.

## Nested Routes

```dart
GoRoute(
  path: '/orders',
  builder: (_, __) => const OrderListScreen(),
  routes: [
    GoRoute(
      path: ':orderId',
      builder: (_, state) => OrderDetailScreen(
        orderId: state.pathParameters['orderId']!,
      ),
      routes: [
        GoRoute(
          path: 'tracking',
          builder: (_, state) => TrackingScreen(
            orderId: state.pathParameters['orderId']!,
          ),
        ),
      ],
    ),
  ],
),
```

URL `/orders/abc-123/tracking` matches with `orderId = abc-123`.

## Error Handling

```dart
GoRouter(
  errorBuilder: (context, state) => ErrorScreen(error: state.error),
  routes: [...],
);
```

## Migration from Navigator.push

| Imperative | GoRouter |
|-----------|---------|
| `Navigator.push(context, MaterialPageRoute(...))` | `context.push('/detail')` |
| `Navigator.pushReplacement(...)` | `context.pushReplacement('/home')` |
| `Navigator.pushAndRemoveUntil(...)` | `context.go('/home')` |
| `Navigator.pop(context)` | `context.pop()` |
| `Navigator.pop(context, result)` | `context.pop(result)` |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using `push` for tab navigation | Stacked routes instead of switching | Use `go` for top-level |
| Redirect returns same location | Infinite loop | Return `null` when no redirect |
| Missing `parentNavigatorKey` | Modal opens inside tab | Set key on route |
| Not handling auth state changes | Protected route after logout | Use `refreshListenable` |
| Hardcoding paths everywhere | Refactoring breaks nav | Define path constants |
