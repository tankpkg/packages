# Component Recipes

Sources: Tailwind CSS docs; Refactoring UI (Wathan/Schoger); shadcn/ui patterns.

## Buttons
Use consistent radius, focus ring, and disabled styles across variants.
```html
<button class="inline-flex items-center justify-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/50 disabled:pointer-events-none disabled:opacity-50">
  Primary
</button>
<button class="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 shadow-sm transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/50 disabled:pointer-events-none disabled:opacity-50">
  Secondary
</button>
<button class="inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/50 disabled:pointer-events-none disabled:opacity-50">
  Ghost
</button>
<button class="inline-flex items-center justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-red-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-600/40 disabled:pointer-events-none disabled:opacity-50">
  Destructive
</button>
<button class="inline-flex items-center justify-center rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/50">
  Small
</button>
<button class="inline-flex items-center justify-center rounded-md bg-slate-900 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/50">
  Large
</button>
```

## Card
Use a header, body, and footer to keep spacing predictable.
```html
<article class="rounded-xl border border-slate-200 bg-white shadow-sm">
  <div class="border-b border-slate-200 px-6 py-4">
    <h3 class="text-base font-semibold text-slate-900">Card title</h3>
    <p class="mt-1 text-sm text-slate-600">Short supporting text goes here.</p>
  </div>
  <div class="px-6 py-4 text-sm text-slate-700">
    This is the body content. Use text-sm for long-form readability.
  </div>
  <div class="flex items-center justify-end gap-2 border-t border-slate-200 px-6 py-4">
    <button class="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100">Cancel</button>
    <button class="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800">Save</button>
  </div>
</article>
```

## Form Inputs
Provide consistent height, padding, and focus state across inputs.

### Text input
```html
<label class="block text-sm font-medium text-slate-700" for="email">Email</label>
<input id="email" type="email" class="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/30" placeholder="you@example.com">
```

### Select
```html
<label class="block text-sm font-medium text-slate-700" for="plan">Plan</label>
<select id="plan" class="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/30">
  <option>Starter</option>
  <option>Pro</option>
  <option>Enterprise</option>
</select>
```

### Checkbox
```html
<label class="flex items-start gap-2 text-sm text-slate-700">
  <input type="checkbox" class="mt-0.5 h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900/30">
  <span>Send me product updates</span>
</label>
```

### Radio group
```html
<fieldset class="space-y-2">
  <legend class="text-sm font-medium text-slate-700">Billing</legend>
  <label class="flex items-center gap-2 text-sm text-slate-700">
    <input type="radio" name="billing" class="h-4 w-4 border-slate-300 text-slate-900 focus:ring-slate-900/30" checked>
    <span>Monthly</span>
  </label>
  <label class="flex items-center gap-2 text-sm text-slate-700">
    <input type="radio" name="billing" class="h-4 w-4 border-slate-300 text-slate-900 focus:ring-slate-900/30">
    <span>Annual</span>
  </label>
</fieldset>
```

### Textarea
```html
<label class="block text-sm font-medium text-slate-700" for="message">Message</label>
<textarea id="message" rows="4" class="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/30"></textarea>
```

### Error state
```html
<label class="block text-sm font-medium text-slate-700" for="username">Username</label>
<input id="username" class="mt-1 w-full rounded-md border border-red-500 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-red-600 focus:outline-none focus:ring-2 focus:ring-red-500/30" value="taken-name">
<p class="mt-1 text-xs text-red-600">That name is already taken.</p>
```

## Input with icon
Use relative wrapper and left padding.
```html
<div class="relative">
  <span class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
    <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M8 2a6 6 0 100 12A6 6 0 008 2zm8 16-4.35-4.35a8 8 0 111.41-1.41L16 16z"/>
    </svg>
  </span>
  <input class="w-full rounded-md border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/30" placeholder="Search">
</div>
```

## Navigation
Keep nav items aligned and ensure visible focus styles.

### Horizontal navbar
```html
<nav class="border-b border-slate-200 bg-white">
  <div class="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
    <a class="text-base font-semibold text-slate-900" href="#">Acme</a>
    <div class="hidden items-center gap-6 text-sm font-medium text-slate-600 md:flex">
      <a class="hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/40" href="#">Features</a>
      <a class="hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/40" href="#">Pricing</a>
      <a class="hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/40" href="#">Docs</a>
    </div>
    <button class="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white">Sign in</button>
  </div>
</nav>
```

### Sidebar
```html
<aside class="w-64 border-r border-slate-200 bg-white">
  <div class="px-4 py-6">
    <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">Workspace</div>
    <nav class="mt-4 space-y-1 text-sm">
      <a class="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-2 text-slate-900" href="#">Overview</a>
      <a class="flex items-center gap-2 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900" href="#">Projects</a>
      <a class="flex items-center gap-2 rounded-md px-3 py-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900" href="#">Settings</a>
    </nav>
  </div>
</aside>
```

### Breadcrumbs
```html
<nav class="text-sm text-slate-600" aria-label="Breadcrumb">
  <ol class="flex items-center gap-2">
    <li><a class="hover:text-slate-900" href="#">Home</a></li>
    <li class="text-slate-400">/</li>
    <li><a class="hover:text-slate-900" href="#">Projects</a></li>
    <li class="text-slate-400">/</li>
    <li class="font-medium text-slate-900" aria-current="page">Alpha</li>
  </ol>
</nav>
```

## Modal / Dialog
Use a scrim, a centered panel, and focusable actions.
```html
<div class="fixed inset-0 z-50 flex items-center justify-center">
  <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"></div>
  <div class="relative w-full max-w-lg rounded-xl bg-white p-6 shadow-lg">
    <h3 class="text-base font-semibold text-slate-900">Delete project?</h3>
    <p class="mt-2 text-sm text-slate-600">This action cannot be undone.</p>
    <div class="mt-6 flex justify-end gap-2">
      <button class="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100">Cancel</button>
      <button class="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-500">Delete</button>
    </div>
  </div>
</div>
```

## Alert / Toast
Use left border or icon color to indicate intent.
```html
<div class="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
  <svg class="mt-0.5 h-4 w-4 text-amber-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 9H9V5h2v6zm0 4H9v-2h2v2z"/>
  </svg>
  <div>
    <p class="font-medium">Heads up</p>
    <p class="text-amber-800">Your plan renews in 3 days.</p>
  </div>
</div>
```

## Badge / Tag
Combine border and subtle bg for readability.
```html
<span class="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs font-medium text-slate-700">Beta</span>
<span class="inline-flex items-center rounded-full bg-emerald-600/10 px-2.5 py-0.5 text-xs font-medium text-emerald-700">Active</span>
```

## Avatar with fallback
Use gradient or initials fallback if image fails.
```html
<div class="flex items-center gap-3">
  <img class="h-10 w-10 rounded-full object-cover" src="https://placehold.co/80x80" alt="Alex Kim">
  <div class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">AK</div>
</div>
```

## Table
Use zebra rows and hover for scanability.
```html
<div class="overflow-x-auto rounded-lg border border-slate-200">
  <table class="min-w-full text-left text-sm">
    <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
      <tr>
        <th class="px-4 py-3">Name</th>
        <th class="px-4 py-3">Role</th>
        <th class="px-4 py-3">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-slate-200">
      <tr class="odd:bg-white even:bg-slate-50 hover:bg-slate-100">
        <td class="px-4 py-3 font-medium text-slate-900">Alex Kim</td>
        <td class="px-4 py-3 text-slate-600">Design</td>
        <td class="px-4 py-3"><span class="rounded-full bg-emerald-600/10 px-2 py-0.5 text-xs text-emerald-700">Active</span></td>
      </tr>
      <tr class="odd:bg-white even:bg-slate-50 hover:bg-slate-100">
        <td class="px-4 py-3 font-medium text-slate-900">Jordan Lee</td>
        <td class="px-4 py-3 text-slate-600">Engineering</td>
        <td class="px-4 py-3"><span class="rounded-full bg-amber-600/10 px-2 py-0.5 text-xs text-amber-700">On leave</span></td>
      </tr>
    </tbody>
  </table>
</div>
```

## Pagination
Simple pagination with active state.
```html
<nav class="flex items-center gap-1 text-sm">
  <a class="rounded-md px-2 py-1 text-slate-600 hover:bg-slate-100" href="#">Prev</a>
  <a class="rounded-md bg-slate-900 px-2 py-1 font-medium text-white" href="#">1</a>
  <a class="rounded-md px-2 py-1 text-slate-600 hover:bg-slate-100" href="#">2</a>
  <span class="px-2 py-1 text-slate-400">...</span>
  <a class="rounded-md px-2 py-1 text-slate-600 hover:bg-slate-100" href="#">8</a>
  <a class="rounded-md px-2 py-1 text-slate-600 hover:bg-slate-100" href="#">Next</a>
</nav>
```

## Anti-Patterns
Avoid patterns that break design consistency.
```html
<!-- Anti-pattern: inline styles and ad-hoc colors -->
<button style="background:#1f2937;color:white;padding:10px 14px;border-radius:6px">Save</button>
<!-- Prefer Tailwind tokens for scale + theming -->
<button class="rounded-md bg-slate-900 px-3.5 py-2 text-sm font-medium text-white">Save</button>
```

| Anti-pattern | Fix |
| --- | --- |
| Arbitrary values everywhere | Use theme scale, document exceptions |
| Missing focus-visible | Add `focus-visible:ring` utilities |
| Inconsistent button padding | Use size variants |
| One-off shadows | Use `shadow-sm`, `shadow-md`, `shadow-lg` |
| Too many font sizes | Restrict to 3-4 sizes |
| Mixed radius | Use one radius per size tier |
