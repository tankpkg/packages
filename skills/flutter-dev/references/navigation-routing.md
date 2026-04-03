# Navigation and Routing

Sources: GoRouter official documentation (pub.dev/packages/go_router 2025-2026), Flutter navigation documentation (flutter.dev), Flutter API reference for Navigator 2.0

Covers: GoRouter setup and configuration, ShellRoute and StatefulShellRoute for tabs, redirect guards, deep linking, path and query parameters, nested navigation, and migration from imperative Navigator.push.

## Why GoRouter

Flutter's imperative `Navigator.push` / `Navigator.pop` does not support:
- URL-based navigation (web, deep links)
- Declarative route definitions
- Route guards without middleware hacks
- State restoration on app kill
- Predictable back button behavior across platforms

GoRouter wraps Navigator 2.0 with a declarative, URL-based API. It is the Flutter team's recommended routing package.

## Basic Setup

```dart
final router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/profile/:userId',
      builder: (context, state) {
        final userId = state.pathParameters['userId']!;
        return ProfileScreen(userId: userId);
      },
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
  ],
);

// In MaterialApp
MaterialApp.router(
  routerConfig: router,
);
```

## Path and Query Parameters

```dart
GoRoute(
  path: '/products/:category',
  builder: (context, state) {
    final category = state.pathParameters['category']!;
    final sort = state.uri.queryParameters['sort'] ?? 'name';
    final page = int.tryParse(state.uri.queryParameters['page'] ?? '1') ?? 1;
    return ProductListScreen(category: category, sort: sort, page: page);
  },
),
```

Navigate with parameters:

```dart
context.go('/products/electronics?sort=price&page=2');
context.goNamed('productList', pathParameters: {'category': 'electronics'});
```

### go vs push

| Method | Behavior | Use |
|--------|----------|-----|
| `context.go('/path')` | Replaces the entire navigation stack to match the URL | Primary navigation (tabs, sections) |
| `context.push('/path')` | Pushes onto the current stack | Drill-down (detail screens, modals) |
| `context.pop()` | Pops the top route | Back navigation |
| `context.pushReplacement('/path')` | Replaces current route | Login -> Home (no back to login) |

Rule: use `go` for top-level navigation, `push` for detail/modal navigation within a section.

## ShellRoute (Shared Scaffold)

Wrap routes in a shared layout (AppBar, Drawer, BottomNavigationBar):

```dart
ShellRoute(
  builder: (context, state, child) {
    return ScaffoldWithNavBar(child: child);
  },
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/search', builder: (_, __) => const SearchScreen()),
    GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
  ],
),
```

The `child` parameter is the matched route's widget. The shell persists while navigating between its child routes.

## StatefulShellRoute (Persistent Tabs)

`ShellRoute` destroys tab state on navigation. `StatefulShellRoute` preserves each tab's navigation stack independently using separate Navigators:

```dart
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) {
    return ScaffoldWithNavBar(navigationShell: navigationShell);
  },
  branches: [
    StatefulShellBranch(
      routes: [
        GoRoute(
          path: '/home',
          builder: (_, __) => const HomeScreen(),
          routes: [
            GoRoute(
              path: 'detail/:id',
              builder: (_, state) => DetailScreen(
                id: state.pathParameters['id']!,
              ),
            ),
          ],
        ),
      ],
    ),
    StatefulShellBranch(
      routes: [
        GoRoute(
          path: '/search',
          builder: (_, __) => const SearchScreen(),
        ),
      ],
    ),
    StatefulShellBranch(
      routes: [
        GoRoute(
          path: '/profile',
          builder: (_, __) => const ProfileScreen(),
        ),
      ],
    ),
  ],
),
```

The scaffold widget uses `navigationShell.goBranch(index)` to switch tabs:

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
          navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
          );
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
| Preserves tab state | No (rebuilds on switch) | Yes (separate Navigators per branch) |
| Independent back stacks per tab | No | Yes |
| Memory usage | Lower | Higher (keeps all tabs alive) |
| Use case | Simple shared layout | Bottom nav with persistent tabs |

## Redirect Guards

Protect routes based on authentication or other conditions:

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

Use `ref.listen` to react to auth changes and force redirect:

```dart
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  return GoRouter(
    refreshListenable: authState, // Triggers redirect re-evaluation
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

GoRouter handles deep links automatically. Configure platform-specific settings:

### Android (AndroidManifest.xml)

```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="myapp.com" />
</intent-filter>
```

### iOS (Info.plist + apple-app-site-association)

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array><string>myapp</string></array>
  </dict>
</array>
```

GoRouter parses the incoming URL and navigates to the matching route. No additional Dart code needed for link handling — the route configuration IS the deep link configuration.

## Nested Routes

Define child routes inside parent routes:

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

URL `/orders/abc-123/tracking` matches the tracking route with `orderId = abc-123`.

## Error Handling

```dart
GoRouter(
  errorBuilder: (context, state) => ErrorScreen(
    error: state.error,
    location: state.matchedLocation,
  ),
  routes: [...],
);
```

## Migration from Navigator.push

| Imperative | GoRouter Equivalent |
|-----------|-------------------|
| `Navigator.push(context, MaterialPageRoute(...))` | `context.push('/detail')` |
| `Navigator.pushReplacement(...)` | `context.pushReplacement('/home')` |
| `Navigator.pushAndRemoveUntil(...)` | `context.go('/home')` |
| `Navigator.pop(context)` | `context.pop()` |
| `Navigator.pop(context, result)` | `context.pop(result)` |
| Named routes (`pushNamed`) | `context.goNamed('routeName')` |

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Using `push` for tab navigation | Creates stacked routes instead of switching | Use `go` for top-level, `push` for detail |
| Redirect returns same location | Infinite redirect loop | Return `null` when no redirect needed |
| Missing `parentNavigatorKey` | Modal opens inside tab instead of full-screen | Set `parentNavigatorKey` on the route |
| Not handling auth state changes | User stays on protected route after logout | Use `refreshListenable` to re-evaluate redirects |
| Hardcoding paths as strings everywhere | Refactoring breaks navigation | Define path constants or use named routes |
