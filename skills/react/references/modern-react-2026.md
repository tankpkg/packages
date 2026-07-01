# Modern React Stack (2026)

Sources: React documentation (react.dev); React Compiler RFC; TanStack Query v5 documentation; Vite documentation.

Covers: Vite setup, React Compiler adoption, TanStack Query patterns, and React 19 full API reference.

## Vite + React Setup

### Scaffold a new project

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app && npm install
```

### Plugin selection

| Plugin | When to use | HMR speed | JSX transform |
| --- | --- | --- | --- |
| `@vitejs/plugin-react` | Need Babel plugins (e.g., styled-components) | Fast | Babel |
| `@vitejs/plugin-react-swc` | Default choice for new projects | Fastest | SWC |

```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: { port: 3000 },
  build: { sourcemap: true },
});
```

### Environment variables
Vite exposes env vars prefixed with `VITE_` to client code via `import.meta.env`.
Never put secrets in `VITE_` variables -- they are bundled into client output.

```ts
// .env
VITE_API_URL=https://api.example.com

// src/config.ts
export const API_URL = import.meta.env.VITE_API_URL;
```

### Path aliases

```ts
// vite.config.ts
import path from "node:path";
export default defineConfig({
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
```

```json
// tsconfig.json (for IDE support)
{ "compilerOptions": { "paths": { "@/*": ["./src/*"] } } }
```

### Production build checklist
- Enable `build.sourcemap` for error monitoring.
- Set `build.target` to match your browser support.
- Use `build.rollupOptions.output.manualChunks` for vendor splitting.
- Run `npx vite-bundle-visualizer` to inspect output.

## React Compiler

### What it does
React Compiler auto-memoizes component renders and hook return values at build time.
It analyzes data flow to insert memoization equivalent to `React.memo`, `useMemo`, and `useCallback` automatically.
Manual memoization becomes unnecessary for pure components.

### What it auto-memoizes

| Pattern | Before compiler | After compiler |
| --- | --- | --- |
| Pure component render | Needs `React.memo` wrapper | Auto-skipped when props unchanged |
| Derived value in render | Needs `useMemo` | Auto-memoized |
| Callback passed to child | Needs `useCallback` | Auto-stabilized |
| JSX expression tree | Re-created every render | Cached when inputs stable |

### When manual memo is still needed
- Components with side effects in render (non-pure).
- Components using refs that change between renders.
- Third-party components that mutate props internally.
- Performance-critical paths where compiler heuristics are insufficient (rare).

### Adoption guide

1. Install the compiler plugin:
```bash
npm install -D babel-plugin-react-compiler
```

2. Configure with Vite (requires Babel plugin, so use `@vitejs/plugin-react`):
```ts
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [["babel-plugin-react-compiler", {}]],
      },
    }),
  ],
});
```

3. Validate with eslint plugin:
```bash
npm install -D eslint-plugin-react-compiler
```

```js
// eslint.config.js
import reactCompiler from "eslint-plugin-react-compiler";
export default [
  { plugins: { "react-compiler": reactCompiler }, rules: { "react-compiler/react-compiler": "error" } },
];
```

4. Incremental adoption -- opt in per file or directory:
```ts
// vite.config.ts
react({
  babel: {
    plugins: [
      ["babel-plugin-react-compiler", {
        sources: (filename) => filename.includes("src/components"),
      }],
    ],
  },
})
```

### Migration checklist
- Remove `React.memo` wrappers from pure components.
- Remove `useMemo` for inline derivations.
- Remove `useCallback` where the only consumer is a child component.
- Keep `useMemo` for genuinely expensive computations (>1ms).
- Keep `useCallback` for callbacks passed to non-React code (event listeners, third-party libs).
- Run profiler before and after to verify equivalent performance.

## TanStack Query (React Query v5)

### Setup

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Basic query

```tsx
import { useQuery } from "@tanstack/react-query";

function Users() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["users"],
    queryFn: () => fetch("/api/users").then((r) => r.json()),
  });

  if (isLoading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <UserList users={data} />;
}
```

### Mutations with optimistic updates

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useCreateTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (newTodo: { text: string }) =>
      fetch("/api/todos", { method: "POST", body: JSON.stringify(newTodo) }).then((r) => r.json()),
    onMutate: async (newTodo) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previous = queryClient.getQueryData(["todos"]);
      queryClient.setQueryData(["todos"], (old: Todo[]) => [
        ...old,
        { id: "temp", text: newTodo.text },
      ]);
      return { previous };
    },
    onError: (_err, _vars, context) => {
      queryClient.setQueryData(["todos"], context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}
```

### Prefetching

```tsx
function UserLink({ userId }: { userId: string }) {
  const queryClient = useQueryClient();

  return (
    <a
      href={`/users/${userId}`}
      onMouseEnter={() => {
        queryClient.prefetchQuery({
          queryKey: ["user", userId],
          queryFn: () => fetchUser(userId),
          staleTime: 30_000,
        });
      }}
    >
      View User
    </a>
  );
}
```

### Suspense integration

```tsx
import { useSuspenseQuery } from "@tanstack/react-query";

function UserProfile({ userId }: { userId: string }) {
  const { data } = useSuspenseQuery({
    queryKey: ["user", userId],
    queryFn: () => fetchUser(userId),
  });
  return <div>{data.name}</div>;
}

// Wrap in Suspense at route or feature level
function UserPage({ userId }: { userId: string }) {
  return (
    <React.Suspense fallback={<ProfileSkeleton />}>
      <UserProfile userId={userId} />
    </React.Suspense>
  );
}
```

### Cache invalidation patterns

| Pattern | When to use | Example |
| --- | --- | --- |
| `invalidateQueries` | After mutation success | `queryClient.invalidateQueries({ queryKey: ["todos"] })` |
| `setQueryData` | Optimistic update before server responds | `queryClient.setQueryData(["todo", id], updatedTodo)` |
| `prefetchQuery` | Preload on hover or route transition | `queryClient.prefetchQuery({ queryKey: [...] })` |
| `removeQueries` | Clear stale data on logout | `queryClient.removeQueries({ queryKey: ["user"] })` |
| `resetQueries` | Reset to initial state | `queryClient.resetQueries({ queryKey: ["filters"] })` |

## Server State vs Client State

### Clear separation

| Category | Examples | Tool | Storage |
| --- | --- | --- | --- |
| Server state | User profile, todos, orders | TanStack Query | Query cache |
| Client UI state | Open panels, selected tab, draft text | useState / useReducer | Component tree |
| Client app state | Theme, auth token, locale | Context or external store | Memory / localStorage |
| URL state | Search filters, pagination, sort | URL search params | Browser URL |

### Rules
- Never copy server data into `useState`. Use the query cache as the single source.
- Mutations go through `useMutation`, not manual fetch + setState.
- Client state that does not need persistence stays in components.
- URL state is the source of truth for anything linkable or shareable.

```tsx
// Server state: TanStack Query owns it
const { data: todos } = useQuery({ queryKey: ["todos"], queryFn: fetchTodos });

// Client UI state: local to component
const [selectedId, setSelectedId] = useState<string | null>(null);

// URL state: search params own it
const [searchParams, setSearchParams] = useSearchParams();
const filter = searchParams.get("status") ?? "all";
```

## React 19 Full API Reference

### use()
Read a promise or context value during render. Suspends the component until the promise resolves.
```tsx
// Read a promise (must be wrapped in Suspense)
function UserCard({ userPromise }: { userPromise: Promise<User> }) {
  const user = React.use(userPromise);
  return <div>{user.name}</div>;
}

// Read context (replaces useContext)
function ThemedButton() {
  const theme = React.use(ThemeContext);
  return <button style={{ color: theme.primary }}>Click</button>;
}
```

### Actions and useActionState
Actions are async functions passed to `<form action={...}>` or `startTransition`.
`useActionState` provides the action result and pending state.
```tsx
async function createTodo(prevState: State, formData: FormData) {
  "use server";
  const text = formData.get("text") as string;
  await db.todos.create({ text });
  return { message: "Created" };
}

function TodoForm() {
  const [state, formAction, isPending] = React.useActionState(createTodo, { message: "" });
  return (
    <form action={formAction}>
      <input name="text" />
      <button disabled={isPending}>{isPending ? "Adding..." : "Add"}</button>
      {state.message && <p>{state.message}</p>}
    </form>
  );
}
```

### useFormStatus
Read the pending state of the nearest parent `<form>`. Must be a child component of the form.
```tsx
function SubmitButton() {
  const { pending, data, method, action } = React.useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? "Submitting..." : "Submit"}
    </button>
  );
}
```

### useOptimistic
Show optimistic state while an async action is in flight.
```tsx
function Messages({ messages }: { messages: Message[] }) {
  const [optimistic, addOptimistic] = React.useOptimistic(
    messages,
    (state, newMsg: string) => [...state, { id: "temp", text: newMsg, sending: true }],
  );

  async function send(formData: FormData) {
    const text = formData.get("text") as string;
    addOptimistic(text);
    await postMessage(text);
  }

  return (
    <div>
      {optimistic.map((m) => (
        <div key={m.id} style={{ opacity: m.sending ? 0.6 : 1 }}>{m.text}</div>
      ))}
      <form action={send}>
        <input name="text" />
      </form>
    </div>
  );
}
```

### ref as prop
In React 19, `ref` is a regular prop. No `forwardRef` wrapper needed.
```tsx
function Input({ ref, ...props }: { ref?: React.Ref<HTMLInputElement> } & React.InputHTMLAttributes<HTMLInputElement>) {
  return <input ref={ref} {...props} />;
}
// Usage: <Input ref={inputRef} placeholder="Name" />
```

### Context as provider
`<Context>` can be used directly as a provider. No `.Provider` suffix needed.
```tsx
const ThemeContext = React.createContext("light");
// React 19: <ThemeContext value="dark"><Page /></ThemeContext>
```

### Document metadata
React 19 hoists `<title>`, `<meta>`, and `<link>` to `<head>` automatically.
```tsx
function BlogPost({ post }: { post: Post }) {
  return (
    <article>
      <title>{post.title}</title>
      <meta name="description" content={post.excerpt} />
      <h1>{post.title}</h1>
    </article>
  );
}
```

## Decision Tree: Choosing the Right Data Pattern

| Question | Answer | Pattern |
| --- | --- | --- |
| Does the data come from a server? | Yes | TanStack Query |
| Is it a form submission? | Yes | Actions + useActionState |
| Do you need instant feedback? | Yes | useOptimistic |
| Is it local UI state? | Yes | useState / useReducer |
| Does it need to survive navigation? | Yes | URL search params or external store |
| Is it shared across many components? | Yes | Context or external store |
| Is it derived from other state? | Yes | Compute inline or useMemo |
