# Expo Router

Sources: Expo Documentation (2025-2026), React Navigation v7 docs, Expo blog (app folder structure best practices)

Covers: file-based routing conventions, layout patterns (Stack, Tabs, Drawer, Slot), typed routes, deep linking, authentication flows, API routes, and platform-specific modules.

## File-Based Routing Fundamentals

Expo Router maps file system structure to navigation hierarchy. Every file in the `app/` directory becomes a route. The framework uses the same conventions as Next.js for React Native.

### Route Conventions

| File | Route | Purpose |
|------|-------|---------|
| `app/index.tsx` | `/` | Home screen |
| `app/about.tsx` | `/about` | Static route |
| `app/users/[id].tsx` | `/users/123` | Dynamic segment |
| `app/[...rest].tsx` | `/any/deep/path` | Catch-all route |
| `app/+not-found.tsx` | Any unmatched | 404 screen |
| `app/_layout.tsx` | N/A | Layout wrapper (not a route) |

### Dynamic Routes

Use square brackets for dynamic segments:

```typescript
// app/users/[id].tsx
import { useLocalSearchParams } from 'expo-router';

export default function UserProfile() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Text>User {id}</Text>;
}
```

Multiple dynamic segments combine naturally:

```typescript
// app/posts/[postId]/comments/[commentId].tsx
const { postId, commentId } = useLocalSearchParams<{
  postId: string;
  commentId: string;
}>();
```

### Typed Routes

Enable typed routes in the Expo config for compile-time route safety:

```json
{
  "expo": {
    "experiments": {
      "typedRoutes": true
    }
  }
}
```

After enabling, `router.push()` and `<Link>` accept only valid routes:

```typescript
import { router } from 'expo-router';

// Type-safe navigation
router.push('/users/123');          // valid
router.push({ pathname: '/users/[id]', params: { id: '123' } });

// TypeScript error at compile time:
router.push('/nonexistent');        // error
```

## Layout Patterns

Layout files (`_layout.tsx`) define how child routes are arranged. Every directory can have one layout file.

### Root Layout

The root layout (`app/_layout.tsx`) is the app entry point. Initialize fonts, splash screen, and providers here:

```typescript
// app/_layout.tsx
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({
    Inter: require('@/assets/fonts/Inter.ttf'),
  });

  useEffect(() => {
    if (loaded) SplashScreen.hide();
  }, [loaded]);

  if (!loaded) return null;

  return (
    <Providers>
      <Stack />
    </Providers>
  );
}
```

### Stack Navigator

Return `<Stack />` from a layout to get push/pop navigation:

```typescript
// app/products/_layout.tsx
import { Stack } from 'expo-router';

export default function ProductsLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Products' }} />
      <Stack.Screen name="[productId]" options={{ headerShown: false }} />
    </Stack>
  );
}
```

Stack implements React Navigation's native stack. Screen options match the React Navigation API. Define `Stack.Screen` components to customize headers without defining component props.

### Tab Navigator

Wrap routes in a directory with parentheses for route groups:

```typescript
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import MaterialIcons from '@expo/vector-icons/MaterialIcons';

export default function TabLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => (
            <MaterialIcons name="home" size={28} color={color} />
          ),
        }}
      />
      <Tabs.Screen name="feed" options={{ title: 'Feed' }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} />
    </Tabs>
  );
}
```

### Native Tabs (SDK 55+)

Use platform-native tab bars on Android and iOS for expected platform behaviors:

```typescript
// app/(tabs)/_layout.tsx
import { NativeTabs } from 'expo-router/native-tabs';

export default function TabLayout() {
  return (
    <NativeTabs>
      <NativeTabs.Trigger name="index">
        <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          src={require('@/assets/images/tabIcons/home.png')}
        />
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="explore">
        <NativeTabs.Trigger.Label>Explore</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Icon
          src={require('@/assets/images/tabIcons/explore.png')}
        />
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
```

### Drawer Navigator

Install `expo-router`'s drawer support:

```typescript
// app/_layout.tsx
import { Drawer } from 'expo-router/drawer';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

export default function Layout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Drawer>
        <Drawer.Screen name="index" options={{ drawerLabel: 'Home' }} />
        <Drawer.Screen name="settings" options={{ drawerLabel: 'Settings' }} />
      </Drawer>
    </GestureHandlerRootView>
  );
}
```

### Slot (No Navigator)

Use `Slot` for layouts without navigation behavior (headers, footers, shared UI):

```typescript
// app/social/_layout.tsx
import { Slot } from 'expo-router';

export default function Layout() {
  return (
    <>
      <Header />
      <Slot />
      <Footer />
    </>
  );
}
```

## Route Groups

Parenthesized directories create logical groups without affecting the URL:

```
app/
  (auth)/
    _layout.tsx     # Auth-specific layout (no tabs)
    login.tsx       # /login
    register.tsx    # /register
  (tabs)/
    _layout.tsx     # Tab navigator
    index.tsx       # /
    profile.tsx     # /profile
```

Route groups enable different layouts for different sections without nesting URL paths.

## Modals

Define modal routes using the `presentation` screen option:

```typescript
// app/_layout.tsx
<Stack>
  <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
  <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
</Stack>
```

The parent navigator remains visible underneath the modal. Navigate with `router.push('/modal')` and dismiss with `router.back()`.

## Deep Linking

Expo Router handles deep linking automatically. Every route has a corresponding URL.

### Configuration

```json
{
  "expo": {
    "scheme": "myapp",
    "web": {
      "bundler": "metro"
    }
  }
}
```

### Universal Links (iOS) and App Links (Android)

Configure in `app.json` for production deep linking:

```json
{
  "expo": {
    "ios": {
      "associatedDomains": ["applinks:example.com"]
    },
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [{ "scheme": "https", "host": "example.com", "pathPrefix": "/" }],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

URLs map directly to file routes: `https://example.com/users/123` opens `app/users/[id].tsx`.

## Authentication Pattern

Redirect unauthenticated users from the root layout:

```typescript
// app/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/hooks/useAuth';

export default function RootLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingScreen />;

  return (
    <Stack>
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(app)" options={{ headerShown: false }} />
    </Stack>
  );
}

// app/(app)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/hooks/useAuth';

export default function AppLayout() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Redirect href="/login" />;
  return <Stack />;
}
```

## API Routes (Web Only)

Expo Router supports server-side API routes for web deployments:

```typescript
// app/api/users+api.ts
export function GET(request: Request) {
  return Response.json({ users: [] });
}

export function POST(request: Request) {
  const body = await request.json();
  return Response.json({ created: true }, { status: 201 });
}
```

API routes run server-side only and follow the `+api.ts` naming convention.

## Platform-Specific Modules

Use file extensions for per-platform implementations:

```
components/
  app-tabs.tsx          # Web fallback
  app-tabs.native.tsx   # iOS and Android
  app-tabs.ios.tsx      # iOS only (highest priority on iOS)
```

Resolution order: `.ios.tsx` > `.native.tsx` > `.tsx` on iOS. The same pattern works for Android.

## Navigation Hooks

| Hook | Purpose |
|------|---------|
| `useRouter()` | Programmatic navigation (push, replace, back) |
| `useLocalSearchParams()` | Current route params (re-renders on change) |
| `useGlobalSearchParams()` | Global params (all active routes) |
| `useSegments()` | Current URL segments array |
| `usePathname()` | Current URL pathname string |
| `useNavigationContainerRef()` | React Navigation ref for advanced control |

### Programmatic Navigation

```typescript
import { router } from 'expo-router';

router.push('/users/123');              // Push onto stack
router.replace('/home');                // Replace current screen
router.back();                         // Go back
router.canGoBack();                    // Check if back is possible
router.dismiss();                      // Dismiss modal
router.dismissAll();                   // Dismiss all modals
router.navigate('/users/123');         // Navigate (deduplicates)
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Nesting navigators unnecessarily | Double headers, confusing back behavior | Use single navigator per layout level |
| Missing `_layout.tsx` | Routes render without navigation chrome | Add layout file in every directory that needs navigation |
| Hardcoding paths | Broken when file structure changes | Use typed routes and `href` objects |
| No loading state in auth redirect | Flash of wrong screen | Show loading screen while checking auth |
| Forgetting `GestureHandlerRootView` | Drawer and gesture-based navigation fails | Wrap root layout with gesture handler root |
