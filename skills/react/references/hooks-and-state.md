# Hooks and State

Sources: React documentation; Dan Abramov blog posts; TanStack Query documentation.

## Custom Hook: useAsync
Wrap async logic so components only coordinate inputs and outputs.
Return a stable API with `status`, `data`, and `error`.
Expose a `run` function to control when the async work begins.
Cancel stale requests by tracking the last promise.
Keep the hook generic so it can wrap any async function.
```tsx
type AsyncState<T> = { status: "idle" | "pending" | "success" | "error"; data?: T; error?: Error };
export function useAsync<T>() {
  const [state, setState] = React.useState<AsyncState<T>>({ status: "idle" });
  const last = React.useRef<Promise<T> | null>(null);
  const run = React.useCallback((promise: Promise<T>) => {
    last.current = promise;
    setState({ status: "pending" });
    promise.then(
      (data) => last.current === promise && setState({ status: "success", data }),
      (error) => last.current === promise && setState({ status: "error", error })
    );
  }, []);
  return { ...state, run };
}
```

## Custom Hook: useDebounce
Debounce user input to prevent spamming expensive work.
Keep the original value and expose the debounced output.
Use `setTimeout` cleanup to prevent stale updates.
Make the delay configurable per use case.
Use it to control search or filter queries.
```tsx
export function useDebounce<T>(value: T, delay = 250) {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
// Usage
const debouncedQuery = useDebounce(query, 300);
```

## Custom Hook: useLocalStorage
Persist small UI preferences across reloads.
Use lazy initialization to avoid blocking render.
Guard JSON parsing to keep the hook resilient.
Write changes on state updates only.
Provide a `reset` to clear stale storage values.
```tsx
export function useLocalStorage<T>(key: string, initial: T) {
  const [value, setValue] = React.useState<T>(() => {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : initial;
  });
  React.useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);
  const reset = React.useCallback(() => setValue(initial), [initial]);
  return [value, setValue, reset] as const;
}
```

## useReducer vs useState Decision Tree
Use `useState` for isolated fields and direct UI toggles.
Use `useReducer` when transitions depend on prior state and events.
Prefer reducers for multi-step workflows and undo logic.
Model transitions as actions with explicit types.
Keep reducer state normalized to avoid duplicates.
```tsx
// useState for simple toggles
function Toast() {
  const [open, setOpen] = React.useState(false);
  return <button onClick={() => setOpen((v) => !v)}>{open ? "Hide" : "Show"}</button>;
}
// useReducer for multi-step
type State = { step: number; accepted: boolean };
type Action = { type: "next" } | { type: "back" } | { type: "accept" };
function reducer(state: State, action: Action): State {
  if (action.type === "next") return { ...state, step: state.step + 1 };
  if (action.type === "back") return { ...state, step: Math.max(0, state.step - 1) };
  return { ...state, accepted: true };
}
```

## useEffect Cleanup Patterns
Treat effects as synchronization with an external system.
Always return a cleanup to avoid leaks.
Use subscriptions for event sources.
Clean up intervals and timeouts deterministically.
Cancel fetches with `AbortController`.
```tsx
React.useEffect(() => {
  const onResize = () => setSize({ w: window.innerWidth, h: window.innerHeight });
  window.addEventListener("resize", onResize);
  return () => window.removeEventListener("resize", onResize);
}, []);
React.useEffect(() => {
  const id = window.setInterval(() => setTick((t) => t + 1), 1000);
  return () => window.clearInterval(id);
}, []);
React.useEffect(() => {
  const controller = new AbortController();
  fetch(`/api/users`, { signal: controller.signal }).then(/* ... */);
  return () => controller.abort();
}, []);
```

## Derive, Don't Sync
Avoid `useEffect` + `setState` for derived values.
Compute values during render or memoize for heavy calculations.
Keep a single source of truth for each piece of data.
Prefer `useMemo` when the derivation is expensive.
Eliminate state that only mirrors props.
```tsx
function PriceSummary({ items }: { items: { price: number; qty: number }[] }) {
  const total = React.useMemo(
    () => items.reduce((sum, i) => sum + i.price * i.qty, 0),
    [items]
  );
  return <div>Total: {total}</div>;
}
```

## Server State vs Client State
Store remote data in a cache designed for server state.
Avoid duplicating server responses in local component state.
Use query invalidation instead of manual refetch flags.
Separate client-only state (drafts, open panels) from server state.
Model mutations through the server-state tool API.
```tsx
const queryClient = new QueryClient();
function Users() {
  const users = useQuery({ queryKey: ["users"], queryFn: fetchUsers });
  const createUser = useMutation({
    mutationFn: postUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });
  if (users.isLoading) return <Spinner />;
  return <UserList users={users.data ?? []} onCreate={createUser.mutate} />;
}
```

## Context Performance Boundaries
Split contexts by domain to avoid broad rerenders.
Use selectors or external stores for high-frequency updates.
Keep provider values stable with `useMemo`.
Use `useSyncExternalStore` for subscription-based state.
Avoid passing inline objects to providers.
```tsx
const ThemeContext = React.createContext<Theme | null>(null);
const AuthContext = React.createContext<Auth | null>(null);
function Providers({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  const auth = useAuth();
  return (
    <ThemeContext.Provider value={theme}>
      <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
    </ThemeContext.Provider>
  );
}
```

## React 19: use()
Use `use()` to read promises in render and let Suspense handle loading.
Keep the promise creation outside render when possible.
Prefer `use()` for server data in Server Components.
Keep error boundaries near the call site.
Avoid mixing imperative fetch calls with `use()` in the same component.
```tsx
async function getUser(id: string) {
  const res = await fetch(`/api/users/${id}`);
  if (!res.ok) throw new Error("failed");
  return res.json();
}
export function UserCard({ userPromise }: { userPromise: Promise<User> }) {
  const user = React.use(userPromise);
  return <div>{user.name}</div>;
}
```

## React 19: useOptimistic
Use optimistic state when the final server shape is predictable.
Keep the optimistic reducer pure and reversible.
Reconcile with actual server response on success.
Reset on error using the base state.
Avoid optimistic updates for non-idempotent mutations.
```tsx
type Todo = { id: string; text: string };
export function Todos({ initial }: { initial: Todo[] }) {
  const [todos, setTodos] = React.useState(initial);
  const [optimistic, addOptimistic] = React.useOptimistic(todos, (state, next: Todo) => [next, ...state]);
  const onCreate = async (text: string) => {
    const optimisticTodo = { id: "temp", text };
    addOptimistic(optimisticTodo);
    const saved = await createTodo({ text });
    setTodos((prev) => [saved, ...prev.filter((t) => t.id !== "temp")]);
  };
  return <TodoList items={optimistic} onCreate={onCreate} />;
}
```

## React 19: useFormStatus
Use form status to disable buttons and show progress.
Keep the UI consistent with server action state.
Avoid separate loading flags for form submissions.
Let the form own its submission state.
Use `pending` for optimistic UI states.
```tsx
function SubmitButton() {
  const { pending } = React.useFormStatus();
  return <button type="submit" disabled={pending}>{pending ? "Saving" : "Save"}</button>;
}
function ProfileForm() {
  return (
    <form action={saveProfile}>
      <input name="name" />
      <SubmitButton />
    </form>
  );
}
```

## Anti-Patterns and Fixes
Avoid stale closures by using functional updates.
Do not omit dependencies to silence the linter.
Avoid `useEffect` for derived state or data mapping.
Do not store server data in component state.
Avoid a single giant context for everything.
```tsx
// Bad: stale closure
function Counter() {
  const [count, setCount] = React.useState(0);
  React.useEffect(() => {
    const id = setInterval(() => setCount(count + 1), 1000);
    return () => clearInterval(id);
  }, []);
  return <div>{count}</div>;
}
// Good: functional update
function CounterFixed() {
  const [count, setCount] = React.useState(0);
  React.useEffect(() => {
    const id = setInterval(() => setCount((c) => c + 1), 1000);
    return () => clearInterval(id);
  }, []);
  return <div>{count}</div>;
}
```
