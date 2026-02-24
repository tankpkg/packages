# Layout and Responsive Patterns

Sources: Tailwind CSS docs; Every Layout (Pickering/Bell).

## Flexbox patterns
Use flex as layout primitives with predictable gap and alignment.

### Row with gap
```html
<div class="flex items-center gap-4">
  <div class="h-8 w-8 rounded bg-slate-200"></div>
  <div class="h-8 w-24 rounded bg-slate-200"></div>
  <div class="h-8 w-16 rounded bg-slate-200"></div>
</div>
```

### Column stack
```html
<div class="flex flex-col gap-3">
  <div class="h-10 rounded bg-slate-200"></div>
  <div class="h-10 rounded bg-slate-200"></div>
  <div class="h-10 rounded bg-slate-200"></div>
</div>
```

### Space-between
```html
<div class="flex items-center justify-between rounded-md border border-slate-200 px-4 py-2">
  <span class="text-sm font-medium text-slate-700">Title</span>
  <button class="rounded-md bg-slate-900 px-2 py-1 text-xs font-medium text-white">Action</button>
</div>
```

### Centering (horizontal)
```html
<div class="flex">
  <div class="mx-auto rounded bg-slate-200 px-6 py-2 text-sm text-slate-700">Centered</div>
</div>
```

### Centering (vertical)
```html
<div class="flex h-32 items-center rounded-md border border-slate-200">
  <div class="rounded bg-slate-100 px-3 py-1 text-sm text-slate-700">Vertically centered</div>
</div>
```

### Centering (both)
```html
<div class="flex h-40 items-center justify-center rounded-md border border-slate-200">
  <div class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white">Centered</div>
</div>
```

### Centering with max width
```html
<div class="flex">
  <div class="mx-auto w-full max-w-3xl rounded-md bg-slate-100 px-6 py-4 text-sm text-slate-700">
    Constrain width and center with mx-auto.
  </div>
</div>
```

## Grid patterns
Use grid to define columns, rows, and gaps.

### Two-column grid
```html
<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
  <div class="rounded-lg bg-slate-100 p-4">Col 1</div>
  <div class="rounded-lg bg-slate-100 p-4">Col 2</div>
</div>
```

### Three-column grid
```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
  <div class="rounded-lg bg-slate-100 p-4">A</div>
  <div class="rounded-lg bg-slate-100 p-4">B</div>
  <div class="rounded-lg bg-slate-100 p-4">C</div>
</div>
```

### Responsive card grid
```html
<div class="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
  <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">Card</article>
  <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">Card</article>
  <article class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">Card</article>
</div>
```

### Sidebar layout
```html
<div class="grid min-h-screen grid-cols-1 lg:grid-cols-[260px_1fr]">
  <aside class="border-r border-slate-200 bg-white p-6">Sidebar</aside>
  <main class="p-6">Main content</main>
</div>
```

## Stack pattern
Use consistent vertical rhythm for content blocks.
```html
<div class="flex flex-col gap-6">
  <div class="rounded bg-slate-100 p-4">Item</div>
  <div class="rounded bg-slate-100 p-4">Item</div>
  <div class="rounded bg-slate-100 p-4">Item</div>
</div>
```

## Cluster pattern
Wrap items and use gap for spacing.
```html
<div class="flex flex-wrap items-center gap-2">
  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">Tag</span>
  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">Tag</span>
  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">Tag</span>
</div>
```

## Switcher pattern
Switch to columns when space allows.
```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-[repeat(auto-fit,minmax(16rem,1fr))]">
  <div class="rounded bg-slate-100 p-4">Panel</div>
  <div class="rounded bg-slate-100 p-4">Panel</div>
  <div class="rounded bg-slate-100 p-4">Panel</div>
</div>
```

## Container queries
Use component-scoped responsiveness with @container.
```html
<div class="@container rounded-xl border border-slate-200 p-4">
  <div class="flex flex-col gap-4 @[32rem]:flex-row">
    <div class="flex-1 rounded-lg bg-slate-100 p-4">Primary</div>
    <div class="flex-1 rounded-lg bg-slate-100 p-4">Secondary</div>
  </div>
</div>
```

## Responsive design
Mobile-first base styles, then layer on breakpoints.
```html
<div class="rounded-lg bg-slate-900 px-4 py-6 text-sm text-white md:px-8 md:py-10 lg:text-base">
  Base styles apply on mobile. Breakpoints enhance on larger screens.
</div>
```

### Breakpoint-based layout shift
```html
<div class="flex flex-col gap-4 md:flex-row md:items-center">
  <div class="flex-1 rounded bg-slate-100 p-4">Content</div>
  <div class="rounded bg-slate-200 p-4 md:w-64">Panel</div>
</div>
```

## Aspect ratio
Use fixed ratios for media and cards.
```html
<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
  <div class="aspect-video overflow-hidden rounded-lg bg-slate-200"></div>
  <div class="aspect-square overflow-hidden rounded-lg bg-slate-200"></div>
  <div class="aspect-[4/3] overflow-hidden rounded-lg bg-slate-200"></div>
</div>
```

## Overflow handling
Manage text overflow and scroll containers.

### Truncate
```html
<p class="w-48 truncate text-sm text-slate-700">This is a very long title that should truncate.</p>
```

### Line clamp
```html
<p class="line-clamp-3 text-sm text-slate-700">
  Long description that should clamp to three lines for consistent card height.
</p>
```

### Scroll container
```html
<div class="h-40 overflow-y-auto rounded-md border border-slate-200 p-3 text-sm text-slate-700">
  Scroll this content if it exceeds the container height.
</div>
```

## Position patterns
Use sticky, fixed, and absolute with clear z-index.

### Sticky header
```html
<header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
  <div class="mx-auto max-w-6xl px-6 py-3 text-sm font-medium text-slate-900">Header</div>
</header>
```

### Fixed sidebar
```html
<aside class="fixed inset-y-0 left-0 w-64 border-r border-slate-200 bg-white">
  <div class="p-6 text-sm text-slate-700">Fixed sidebar</div>
</aside>
<main class="ml-64 p-6">Content area</main>
```

### Absolute overlay
```html
<div class="relative rounded-lg border border-slate-200 p-6">
  <div class="absolute inset-0 rounded-lg bg-slate-900/10"></div>
  <div class="relative text-sm text-slate-700">Overlay content</div>
</div>
```

## Z-index scale
Keep a small, documented scale.
```html
<div class="relative">
  <div class="absolute inset-0 z-10 bg-slate-900/10"></div>
  <div class="absolute inset-2 z-20 rounded bg-white p-3 shadow">Modal</div>
  <div class="absolute inset-6 z-30 rounded bg-slate-100 p-2">Tooltip</div>
</div>
```

## Responsive typography
Use clamp for fluid sizing.
```html
<h1 class="text-[clamp(1.75rem,2vw+1rem,3rem)] font-semibold tracking-tight text-slate-900">
  Fluid headline
</h1>
<p class="text-[clamp(1rem,1vw+0.75rem,1.25rem)] text-slate-600">
  Supporting copy scales with viewport.
</p>
```

## Anti-patterns
Avoid layout practices that break consistency.
```html
<!-- Anti-pattern: hardcoded widths without breakpoints -->
<div class="w-[812px]">Fixed width</div>
<!-- Prefer: responsive max width -->
<div class="mx-auto w-full max-w-5xl px-6">Responsive</div>
```

| Anti-pattern | Fix |
| --- | --- |
| Nesting flex and grid without need | Choose one layout primitive |
| No gaps, only margins | Use `gap-*` for consistent spacing |
| Absolute positioning for layout | Use grid or flex |
| Unscoped z-index values | Document a z-scale |
| Ignoring overflow | Add `overflow-*` for safety |
| Using breakpoints for small tweaks | Prefer base styles or container queries |
