# State Management

Sources: Zustand documentation (v5, 2025), TanStack Query v5 documentation, MMKV documentation, React Hook Form docs, React Native community patterns

Covers: client state with Zustand, server state with TanStack Query, persistent storage with MMKV, form management with React Hook Form, secure storage, offline-first patterns, and Context API usage.

## State Categories

Separate state by source and lifecycle. Each category has an optimal tool:

| Category | Examples | Tool | Persistence |
|----------|----------|------|-------------|
| Server state | API data, user profile, feed | TanStack Query | Cache + refetch |
| Client state | UI toggles, filters, theme | Zustand | Optional (MMKV) |
| Form state | Input values, validation errors | React Hook Form | Transient |
| Navigation state | Current route, params | Expo Router | Automatic |
| Secure state | Auth tokens, credentials | expo-secure-store | Encrypted keychain |

### Anti-Pattern: Single Store for Everything

Do not put server data in Zustand or Redux. TanStack Query handles caching, deduplication, background refetch, and optimistic updates. Mixing server state into client stores creates stale data and synchronization bugs.

## Zustand (Client State)

Minimal, hook-based state manager. No providers, no boilerplate.

### Basic Store

```typescript
// stores/useAppStore.ts
import { create } from 'zustand';

interface AppState {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: AppState['theme']) => void;
  isOnboarded: boolean;
  completeOnboarding: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'system',
  setTheme: (theme) => set({ theme }),
  isOnboarded: false,
  completeOnboarding: () => set({ isOnboarded: true }),
}));
```

### Usage in Components

```typescript
function SettingsScreen() {
  // Subscribe to specific slice (minimizes re-renders)
  const theme = useAppStore((s) => s.theme);
  const setTheme = useAppStore((s) => s.setTheme);

  return (
    <SegmentedControl
      values={['light', 'dark', 'system']}
      selectedIndex={['light', 'dark', 'system'].indexOf(theme)}
      onChange={(e) => setTheme(e.nativeEvent.value as AppState['theme'])}
    />
  );
}
```

### Zustand with MMKV Persistence

```typescript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

const mmkvStorage = {
  getItem: (name: string) => {
    const value = storage.getString(name);
    return value ?? null;
  },
  setItem: (name: string, value: string) => {
    storage.set(name, value);
  },
  removeItem: (name: string) => {
    storage.delete(name);
  },
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: 'system',
      setTheme: (theme) => set({ theme }),
      isOnboarded: false,
      completeOnboarding: () => set({ isOnboarded: true }),
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => mmkvStorage),
    }
  )
);
```

### Zustand Slices Pattern

For larger apps, split the store into slices:

```typescript
// stores/slices/authSlice.ts
export interface AuthSlice {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const createAuthSlice = (set): AuthSlice => ({
  user: null,
  setUser: (user) => set({ user }),
});

// stores/slices/settingsSlice.ts
export interface SettingsSlice {
  notifications: boolean;
  toggleNotifications: () => void;
}

export const createSettingsSlice = (set, get): SettingsSlice => ({
  notifications: true,
  toggleNotifications: () => set((s) => ({ notifications: !s.notifications })),
});

// stores/useStore.ts
import { create } from 'zustand';

export const useStore = create<AuthSlice & SettingsSlice>()((...args) => ({
  ...createAuthSlice(...args),
  ...createSettingsSlice(...args),
}));
```

## TanStack Query (Server State)

Manages API data with caching, background refetch, pagination, and optimistic updates.

### Setup

```typescript
// app/_layout.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,       // 5 minutes
      gcTime: 1000 * 60 * 30,          // 30 minutes garbage collection
      retry: 2,
      refetchOnWindowFocus: false,      // RN doesn't have window focus
      refetchOnReconnect: true,
    },
  },
});

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <Stack />
    </QueryClientProvider>
  );
}
```

### Basic Query

```typescript
// hooks/useUser.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useUser(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => api.get(`/users/${userId}`),
    enabled: !!userId,
  });
}

// In component
function ProfileScreen() {
  const { data: user, isLoading, error, refetch } = useUser('123');

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorView error={error} onRetry={refetch} />;
  return <UserProfile user={user} />;
}
```

### Mutation with Optimistic Update

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useToggleLike(postId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.post(`/posts/${postId}/like`),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['post', postId] });
      const previous = queryClient.getQueryData(['post', postId]);

      queryClient.setQueryData(['post', postId], (old: Post) => ({
        ...old,
        isLiked: !old.isLiked,
        likeCount: old.isLiked ? old.likeCount - 1 : old.likeCount + 1,
      }));

      return { previous };
    },
    onError: (_err, _vars, context) => {
      queryClient.setQueryData(['post', postId], context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['post', postId] });
    },
  });
}
```

### Infinite Scroll

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';

export function useFeed() {
  return useInfiniteQuery({
    queryKey: ['feed'],
    queryFn: ({ pageParam }) => api.get(`/feed?cursor=${pageParam}`),
    initialPageParam: '',
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
  });
}

function FeedScreen() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useFeed();
  const posts = data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <FlashList
      data={posts}
      renderItem={({ item }) => <PostCard post={item} />}
      estimatedItemSize={200}
      onEndReached={() => hasNextPage && fetchNextPage()}
      onEndReachedThreshold={0.5}
      ListFooterComponent={isFetchingNextPage ? <ActivityIndicator /> : null}
    />
  );
}
```

## MMKV (Persistent Storage)

Synchronous key-value storage. 30x faster than AsyncStorage.

### Setup

```bash
npx expo install react-native-mmkv
```

### Basic Usage

```typescript
import { MMKV } from 'react-native-mmkv';

export const storage = new MMKV();

// Synchronous operations
storage.set('user.name', 'Alice');
storage.set('user.age', 25);
storage.set('user.isPro', true);

const name = storage.getString('user.name');    // 'Alice'
const age = storage.getNumber('user.age');       // 25
const isPro = storage.getBoolean('user.isPro');  // true

storage.delete('user.name');
storage.clearAll();
```

### MMKV vs AsyncStorage

| Feature | MMKV | AsyncStorage |
|---------|------|-------------|
| API | Synchronous | Async (Promise) |
| Speed | ~30x faster | Baseline |
| Encryption | Built-in support | None |
| Multi-process | Supported | Not supported |
| Types | String, number, boolean, Buffer | String only |
| Max size | Limited by disk | 6MB default on Android |

## React Hook Form (Forms)

### Setup

```bash
npx expo install react-hook-form @hookform/resolvers zod
```

### Form with Validation

```typescript
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'At least 8 characters'),
});

type FormData = z.infer<typeof schema>;

function LoginForm() {
  const { control, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: FormData) => loginMutation.mutate(data);

  return (
    <View>
      <Controller
        control={control}
        name="email"
        render={({ field: { onChange, onBlur, value } }) => (
          <TextInput
            placeholder="Email"
            onBlur={onBlur}
            onChangeText={onChange}
            value={value}
            keyboardType="email-address"
            autoCapitalize="none"
          />
        )}
      />
      {errors.email && <Text style={styles.error}>{errors.email.message}</Text>}

      <Controller
        control={control}
        name="password"
        render={({ field: { onChange, onBlur, value } }) => (
          <TextInput
            placeholder="Password"
            onBlur={onBlur}
            onChangeText={onChange}
            value={value}
            secureTextEntry
          />
        )}
      />
      {errors.password && <Text style={styles.error}>{errors.password.message}</Text>}

      <Button title="Login" onPress={handleSubmit(onSubmit)} />
    </View>
  );
}
```

## Secure Storage

Store sensitive data in the device keychain/keystore:

```typescript
import * as SecureStore from 'expo-secure-store';

// Store token
await SecureStore.setItemAsync('auth_token', token);

// Retrieve token
const token = await SecureStore.getItemAsync('auth_token');

// Delete token
await SecureStore.deleteItemAsync('auth_token');
```

| Storage | Use For | Encrypted | Sync |
|---------|---------|-----------|------|
| MMKV | Preferences, cache, non-sensitive data | Optional | Yes |
| SecureStore | Auth tokens, API keys, credentials | Yes (keychain) | No (async) |
| AsyncStorage | Legacy only (migrate to MMKV) | No | No |

## Context API: When to Use

Use React Context for dependency injection, not state management:

```typescript
// Appropriate: providing configured instances
const ApiContext = createContext<ApiClient>(null!);
const ThemeContext = createContext<Theme>(lightTheme);

// Inappropriate: frequently changing state
// Context re-renders ALL consumers on any change
// Use Zustand instead for shared mutable state
```

| Signal | Use Context | Use Zustand |
|--------|-------------|-------------|
| Value rarely changes (theme, locale, API client) | Yes | Overkill |
| Multiple components read/write frequently | No (perf) | Yes |
| Need selector to minimize re-renders | No (Context lacks selectors) | Yes |
| Dependency injection pattern | Yes | Not needed |
