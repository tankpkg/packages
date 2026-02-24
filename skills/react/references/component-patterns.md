# Component Patterns

Sources: React documentation; Kent C. Dodds Advanced React Patterns.

## Compound Components (Context-Based Accordion)
Use a shared context to coordinate child pieces without prop threading.
Expose leaf components so the API reads like HTML.
Keep state in the parent and derive child behavior from context.
Provide stable ids for items to avoid index keys.
Return null for collapsed panels to avoid extra DOM.
```tsx
type AccordionCtx = { open: string | null; setOpen: (id: string | null) => void };
const AccordionContext = React.createContext<AccordionCtx | null>(null);
export function Accordion({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState<string | null>(null);
  const value = React.useMemo(() => ({ open, setOpen }), [open]);
  return <AccordionContext.Provider value={value}>{children}</AccordionContext.Provider>;
}
export function AccordionItem({ id, children }: { id: string; children: React.ReactNode }) {
  return <div data-acc-item={id}>{children}</div>;
}
export function AccordionHeader({ id, children }: { id: string; children: React.ReactNode }) {
  const ctx = React.useContext(AccordionContext)!;
  const isOpen = ctx.open === id;
  return <button onClick={() => ctx.setOpen(isOpen ? null : id)}>{children}</button>;
}
export function AccordionPanel({ id, children }: { id: string; children: React.ReactNode }) {
  const ctx = React.useContext(AccordionContext)!;
  return ctx.open === id ? <div>{children}</div> : null;
}
```

## Render Props (Behavior Injection)
Use render props when consumers must control layout.
Pass state and actions to a function so the caller decides placement.
Keep the render prop stable by memoizing callbacks.
Prefer a single render prop over multiple prop functions.
Return minimal data so consumers avoid unnecessary work.
```tsx
type MouseState = { x: number; y: number };
export function Mouse({ children }: { children: (s: MouseState) => React.ReactNode }) {
  const [pos, setPos] = React.useState<MouseState>({ x: 0, y: 0 });
  return (
    <div
      onMouseMove={(e) => setPos({ x: e.clientX, y: e.clientY })}
      style={{ height: 200, border: "1px solid #ddd" }}
    >
      {children(pos)}
    </div>
  );
}
// Usage
<Mouse>{({ x, y }) => <span>{x},{y}</span>}</Mouse>;
```

## Slots Pattern (Named Children)
Model slots with explicit props so consumers see all extension points.
Reserve `children` for the main body and use named props for slots.
Treat slot components as optional and provide defaults.
Keep slot types narrow to prevent API drift.
Prefer slot props over `cloneElement` when possible.
```tsx
type CardProps = {
  title?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
};
export function Card({ title, actions, children }: CardProps) {
  return (
    <section className="card">
      <header className="card__header">
        <h3>{title}</h3>
        <div className="card__actions">{actions}</div>
      </header>
      <div className="card__body">{children}</div>
    </section>
  );
}
// Usage
<Card title="Invoice" actions={<button>Pay</button>}>...</Card>;
```

## Container and Presentational Split
Apply the split when data access and UI evolve at different speeds.
Keep the container focused on data and orchestration.
Make the presentational component pure and prop-driven.
Export the presentational component for reuse in tests and stories.
Use naming that makes the boundary obvious to readers.
```tsx
type User = { id: string; name: string };
function UserListView({ users, onSelect }: { users: User[]; onSelect: (u: User) => void }) {
  return (
    <ul>
      {users.map((u) => (
        <li key={u.id}>
          <button onClick={() => onSelect(u)}>{u.name}</button>
        </li>
      ))}
    </ul>
  );
}
export function UserListContainer() {
  const { data = [] } = useUsersQuery();
  const navigate = useNavigate();
  return <UserListView users={data} onSelect={(u) => navigate(`/users/${u.id}`)} />;
}
```

## Polymorphic Components with `as`
Use polymorphism for shared styling across element types.
Type the `as` prop to keep attributes safe and discoverable.
Prefer `as` only when semantics differ but UI stays consistent.
Default to a semantic element, then allow overrides.
Document which props are forwarded to the rendered element.
```tsx
type AsProp<E extends React.ElementType> = { as?: E };
type Props<E extends React.ElementType> = AsProp<E> & {
  variant?: "primary" | "ghost";
  children: React.ReactNode;
};
type PolymorphicProps<E extends React.ElementType> = Props<E> &
  Omit<React.ComponentPropsWithoutRef<E>, keyof Props<E>>;
export function Button<E extends React.ElementType = "button">(
  { as, variant = "primary", children, ...rest }: PolymorphicProps<E>
) {
  const Comp = as || "button";
  return <Comp className={`btn btn--${variant}`} {...rest}>{children}</Comp>;
}
```

## Composition Over Inheritance
Prefer composition so features remain opt-in and testable.
Wrap behavior around children instead of extending base classes.
Expose primitives and let consumers build higher-level pieces.
Use helper components to share layout, not inheritance trees.
Keep component contracts explicit through props and slots.
```tsx
function CardFrame({ children }: { children: React.ReactNode }) {
  return <div className="card-frame">{children}</div>;
}
function CardTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="card-title">{children}</h3>;
}
function CardBody({ children }: { children: React.ReactNode }) {
  return <div className="card-body">{children}</div>;
}
export function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <CardFrame>
      <CardTitle>{title}</CardTitle>
      <CardBody>{children}</CardBody>
    </CardFrame>
  );
}
```

## Controlled and Uncontrolled Modes
Support controlled mode when external state must drive UI.
Support uncontrolled mode for simpler forms and prototyping.
Keep the behavior deterministic by using a single source of truth.
Expose `onChange` regardless of the mode.
Document which props must be paired together.
```tsx
type ToggleProps = {
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (next: boolean) => void;
};
export function Toggle({ checked, defaultChecked, onChange }: ToggleProps) {
  const [internal, setInternal] = React.useState(defaultChecked ?? false);
  const isControlled = checked !== undefined;
  const value = isControlled ? checked : internal;
  const setValue = (next: boolean) => {
    if (!isControlled) setInternal(next);
    onChange?.(next);
  };
  return <button onClick={() => setValue(!value)}>{value ? "On" : "Off"}</button>;
}
```

## Colocation Principle (Feature Folder)
Keep a feature's component, hook, and tests in one folder.
Co-locate API clients and UI so changes stay near usage.
Prefer feature boundaries over type boundaries.
Keep cross-feature primitives in a shared folder.
Document module exports through a single entry file.
```tsx
// features/billing/
//   BillingPage.tsx
//   BillingForm.tsx
//   useBilling.ts
//   api.ts
//   BillingPage.test.tsx
export { BillingPage } from "./BillingPage";
export { BillingForm } from "./BillingForm";
export { useBilling } from "./useBilling";
export * as billingApi from "./api";
```

## Barrel Exports with Public Surface
Use barrels to define the supported public API of a feature.
Avoid re-exporting deep files to keep refactors safe.
Prefer explicit exports over `export *` for stable contracts.
Keep the barrel small so consumers read it at a glance.
Audit barrels during refactors to remove dead exports.
```tsx
// features/profile/index.ts
export { ProfilePage } from "./ProfilePage";
export { ProfileCard } from "./ProfileCard";
export { useProfile } from "./useProfile";
export type { Profile } from "./types";
// elsewhere
import { ProfilePage, useProfile } from "features/profile";
```

## Feature-Based Structure (Route Module)
Group route-level elements into a single module entry point.
Make data loading, actions, and components live together.
Export a small surface so routing remains clean.
Keep view-only components in a `components` subfolder.
Promote shared layout pieces to a higher-level feature.
```tsx
// routes/orders/index.ts
export { OrdersPage } from "./OrdersPage";
export { OrdersHeader } from "./components/OrdersHeader";
export { ordersLoader } from "./data/ordersLoader";
export { ordersAction } from "./data/ordersAction";
// router
{ path: "/orders", element: <OrdersPage />, loader: ordersLoader, action: ordersAction }
```

## Anti-Patterns and Corrections
Replace prop drilling with context boundaries or slots.
Avoid copying props into state unless you manage dirty state.
Do not `cloneElement` for simple extension points.
Skip monolithic components that handle data, layout, and side effects.
Prefer composable primitives to "smart" mega components.
```tsx
// Bad: prop drilling and derived state
function Page({ theme, user }: { theme: Theme; user: User }) {
  return <Layout theme={theme} userName={user.name} />;
}
// Good: context boundary + derived value inline
const ThemeContext = React.createContext<Theme | null>(null);
function Page({ theme, user }: { theme: Theme; user: User }) {
  return (
    <ThemeContext.Provider value={theme}>
      <Layout userName={user.name} />
    </ThemeContext.Provider>
  );
}
```
