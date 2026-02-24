# Server Components and Actions

Sources:
- Next.js Docs: App Router, Server Components, Server Actions
- React Server Components RFC
- Vercel Blog: Server Actions and Streaming

## Mental Model
- Run Server Components on the server only.
- Run Client Components in the browser only.
- Serialize props across the RSC boundary; only JSON-serializable values cross.
- Treat the "use client" directive as an opt-in to bundling and hydration.
- Keep secrets on the server; never pass tokens to Client Components.

## Server vs Client: Where Code Executes
- Execute Server Components in Node.js or Edge runtime.
- Execute Client Components in the browser with full access to DOM APIs.
- Treat each Client Component as a bundle entry.
- Enforce a single direction of import: Server can import Client, Client cannot import Server.

## Serialization Boundary Rules
- Pass plain objects, arrays, strings, numbers, booleans, null.
- Pass Dates only when you serialize to ISO strings.
- Avoid functions, class instances, Map, Set, or Error objects.
- Use IDs and fetch on the client if you must hydrate rich types.

## "use client" Decision Tree
| Need | Decision | Reason |
| --- | --- | --- |
| Use state, effects, refs, browser APIs | Add "use client" | Requires browser runtime |
| Attach event handlers like onClick | Add "use client" | Requires hydration |
| Render static data with no events | Avoid "use client" | Keep zero JS |
| Use a client-only library (charts, maps) | Add "use client" | Library needs window |
| Fetch data securely with secrets | Avoid "use client" | Keep secrets server-side |
| Compose a small interactive widget | Add "use client" on leaf | Minimize bundle size |

## Server Component Data Fetching
Use async Server Components and fetch in place.
Prefer colocated reads; avoid lifting to layouts when not shared.

```tsx
// app/dashboard/page.tsx
import { Suspense } from "react";
import { Stats } from "./stats";
import { RecentActivity } from "./recent-activity";

export default async function DashboardPage() {
  const user = await getUser();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Welcome, {user.name}</h1>
      <Suspense fallback={<div>Loading stats...</div>}>
        <Stats userId={user.id} />
      </Suspense>
      <RecentActivity userId={user.id} />
    </div>
  );
}

async function getUser() {
  const res = await fetch("https://api.example.com/me", {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load user");
  return res.json();
}
```

## Server Actions: Form Handling
Use Server Actions for same-origin mutations and form submissions.
Keep validation server-side and return serializable responses.

```tsx
// app/settings/actions.ts
"use server";

import { revalidatePath } from "next/cache";

export async function updateProfile(formData: FormData) {
  const name = String(formData.get("name") || "");
  const bio = String(formData.get("bio") || "");

  if (!name.trim()) {
    return { ok: false, message: "Name is required" };
  }

  await db.user.update({ data: { name, bio } });
  revalidatePath("/settings");
  return { ok: true };
}
```

```tsx
// app/settings/page.tsx
import { updateProfile } from "./actions";

export default function SettingsPage() {
  return (
    <form action={updateProfile} className="space-y-4">
      <label className="block">
        Name
        <input name="name" className="border p-2" />
      </label>
      <label className="block">
        Bio
        <textarea name="bio" className="border p-2" />
      </label>
      <button type="submit" className="rounded bg-black px-4 py-2 text-white">
        Save
      </button>
    </form>
  );
}
```

## Server Actions from Client Components
Use `startTransition` to call actions without blocking UI.

```tsx
// app/cart/add-to-cart.tsx
"use client";

import { useTransition } from "react";
import { addItem } from "./actions";

export function AddToCartButton({ sku }: { sku: string }) {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      onClick={() => startTransition(() => addItem(sku))}
      disabled={isPending}
      className="rounded bg-blue-600 px-4 py-2 text-white"
    >
      {isPending ? "Adding..." : "Add to cart"}
    </button>
  );
}
```

```tsx
// app/cart/actions.ts
"use server";

import { revalidateTag } from "next/cache";

export async function addItem(sku: string) {
  await db.cart.add({ sku, qty: 1 });
  revalidateTag("cart");
}
```

## Composition Pattern: Server Wrapper + Client Leaf
Keep the server in control of data; pass only what the client needs.

```tsx
// app/products/[id]/page.tsx
import { ProductGallery } from "./product-gallery";

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id);

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <ProductGallery images={product.images} />
      <div>
        <h1 className="text-2xl font-semibold">{product.title}</h1>
        <p className="mt-2 text-slate-600">{product.description}</p>
      </div>
    </div>
  );
}

async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error("Product not found");
  return res.json();
}
```

```tsx
// app/products/[id]/product-gallery.tsx
"use client";

export function ProductGallery({ images }: { images: string[] }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {images.map((src) => (
        <img key={src} src={src} alt="" className="rounded" />
      ))}
    </div>
  );
}
```

## Streaming with Suspense
Use `loading.tsx` for route-level fallbacks.
Use inline Suspense for partial streaming inside a route.

```tsx
// app/inventory/loading.tsx
export default function Loading() {
  return <div className="animate-pulse">Loading inventory...</div>;
}
```

```tsx
// app/inventory/page.tsx
import { Suspense } from "react";
import { InventoryTable } from "./table";
import { InventorySummary } from "./summary";

export default function InventoryPage() {
  return (
    <div className="space-y-6">
      <Suspense fallback={<div>Loading summary...</div>}>
        <InventorySummary />
      </Suspense>
      <Suspense fallback={<div>Loading table...</div>}>
        <InventoryTable />
      </Suspense>
    </div>
  );
}
```

## Server-Only Utilities
Use server-only utilities inside Server Components and Actions.
Guard with the `server-only` package when needed.

```ts
// app/lib/auth.ts
import "server-only";
import { cookies, headers } from "next/headers";

export function getSession() {
  const session = cookies().get("session")?.value;
  const userAgent = headers().get("user-agent");
  return { session, userAgent };
}
```

## Passing Data Between Layers
- Pass data via props for direct ownership.
- Use `searchParams` for URL-derived state.
- Read cookies and headers only on the server.
- Use context providers only inside Client Components.

```tsx
// app/search/page.tsx
export default async function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const q = searchParams.q || "";
  const results = await search(q);
  return (
    <div>
      <h1 className="text-xl">Results for "{q}"</h1>
      <ul>{results.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
    </div>
  );
}
```

## Route Handler vs Server Action
- Use Server Actions for same-origin UI mutations.
- Use Route Handlers for external clients, webhooks, or non-UI APIs.
- Use Route Handlers for edge runtime responses.

## Error Handling
- Throw in Server Components to trigger `error.tsx` boundaries.
- Use `notFound()` for missing resources.
- Return safe errors from Server Actions instead of throwing.

## Anti-Patterns
| Anti-Pattern | Replace With |
| --- | --- |
| Adding "use client" at top-level layouts | Push to leaf components |
| Passing full database rows to Client Components | Map to minimal props |
| Calling server-only utilities in Client Components | Move logic to Server Components |
| Using client fetch for same-origin form submits | Server Actions |
| Fetching in middleware | Move to Server Components or Route Handlers |
| Relying on global loading spinners | Use `loading.tsx` and nested Suspense |
| Returning non-serializable values from actions | Return plain objects |
| Mixing streaming boundaries with shared state | Split into isolated sections |
