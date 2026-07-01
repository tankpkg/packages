# View Transitions API

Sources: Google Chrome team (web.dev/view-transitions), MDN Web Docs, Archibald (View Transitions explainer), Astro documentation, CSS Working Group specification, Chrome Platform Status

Covers: same-document transitions, cross-document transitions, animation control, fallback strategies, MPA vs SPA transitions, framework integration, accessibility, and performance considerations.

## Overview

The View Transitions API provides a native browser mechanism for animating between visual states during navigation or DOM updates. It captures a screenshot of the old state, applies the DOM update, and crossfades to the new state with customizable CSS animations.

### Core Mechanism

1. Browser captures a screenshot of the old state (creates "old" pseudo-elements)
2. DOM update is applied (navigation or state change)
3. Browser captures the new state (creates "new" pseudo-elements)
4. A crossfade animation runs between old and new states
5. On completion, pseudo-elements are removed and the real DOM is shown

### Browser Support

| Browser | Same-Document | Cross-Document |
|---|---|---|
| Chrome 111+ | Yes | Yes (Chrome 126+) |
| Edge 111+ | Yes | Yes (Edge 126+) |
| Safari 18+ | Yes | Yes |
| Firefox 135+ | Yes | Partial |

## Same-Document View Transitions (SPA)

Same-document transitions animate between states within a single page. This is the foundation for SPA route transitions.

### Basic API

```javascript
// Trigger a view transition
document.startViewTransition(() => {
  // Update the DOM
  updateContent(newContent);
});

// With async updates
document.startViewTransition(async () => {
  const data = await fetchPageData(url);
  renderPage(data);
});
```

### Transition Lifecycle

| Phase | What Happens | Controllable |
|---|---|---|
| Capture old state | Browser screenshots current rendered content | No (automatic) |
| DOM update | Callback function runs, modifies the DOM | Yes (your code) |
| Capture new state | Browser screenshots the updated DOM | No (automatic) |
| Animation | Crossfade between old and new screenshots | Yes (CSS) |
| Cleanup | Pseudo-elements removed, real DOM exposed | No (automatic) |

### ViewTransition Object

```javascript
const transition = document.startViewTransition(updateDOM);

// Promises for lifecycle control
transition.ready       // Resolves when animation pseudo-elements are created
transition.updateCallbackDone  // Resolves when DOM update callback completes
transition.finished    // Resolves when animation completes and cleanup is done

// Skip the animation
transition.skipTransition();
```

## Cross-Document View Transitions (MPA)

Cross-document transitions animate between full page navigations. This brings SPA-like visual continuity to multi-page applications without JavaScript routers.

### Enabling Cross-Document Transitions

```css
/* Opt in via CSS on both the old and new pages */
@view-transition {
  navigation: auto;
}
```

Both pages must opt in. The browser automatically creates a view transition on same-origin navigations.

### Cross-Document Transition Flow

1. User clicks a link (same-origin navigation)
2. Browser captures old page screenshot
3. Navigation occurs (new page loads)
4. New page's first render is captured
5. Crossfade animation runs
6. New page is shown

### Cross-Document Considerations

| Aspect | Detail |
|---|---|
| Opt-in required | Both old and new pages must include `@view-transition { navigation: auto; }` |
| Same-origin only | Cross-origin navigations cannot use view transitions |
| Navigation types | Works with link clicks, form submissions, back/forward |
| Render blocking | New page rendering may be slightly delayed to coordinate transition |
| Fallback | Non-supporting browsers perform standard navigation (no breakage) |

## Naming and Targeting Elements

### `view-transition-name`

Assign names to elements that should animate individually rather than as part of the page-wide crossfade:

```css
.hero-image {
  view-transition-name: hero;
}

.page-title {
  view-transition-name: title;
}
```

Named elements animate independently: the browser tracks the old and new positions of elements with the same `view-transition-name` and creates a smooth morph animation between them.

### Rules for `view-transition-name`

| Rule | Detail |
|---|---|
| Must be unique per page | Two elements cannot share the same name in the same document |
| Applied to the element, not a class | Each named element is tracked independently |
| `none` is the default | Elements without a name participate in the root transition |
| Dynamic assignment | Assign names via JS/CSS before starting the transition |
| The name `auto` | Generates a unique name automatically (useful for list items) |

### The Pseudo-Element Tree

During a transition, the browser creates a pseudo-element tree:

```
::view-transition
  ::view-transition-group(name)
    ::view-transition-image-pair(name)
      ::view-transition-old(name)     <- screenshot of old state
      ::view-transition-new(name)     <- screenshot of new state
```

The `root` group captures everything not explicitly named.

## Custom Animations

### Overriding the Default Crossfade

```css
/* Custom fade duration */
::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 0.3s;
}

/* Slide animation for a named element */
@keyframes slide-from-right {
  from { transform: translateX(100%); }
}

@keyframes slide-to-left {
  to { transform: translateX(-100%); }
}

::view-transition-old(content) {
  animation: slide-to-left 0.3s ease-out both;
}

::view-transition-new(content) {
  animation: slide-from-right 0.3s ease-out both;
}
```

### Common Animation Patterns

| Pattern | Old State Animation | New State Animation |
|---|---|---|
| Crossfade (default) | Fade out | Fade in |
| Slide left | Slide out to left | Slide in from right |
| Slide up | Slide out upward | Slide in from bottom |
| Scale | Scale down + fade out | Scale up + fade in |
| Morph (named) | Automatic position/size interpolation | Automatic |
| None (instant) | `animation: none` | `animation: none` |

### Directional Transitions

Apply different animations based on navigation direction:

```css
/* Forward navigation */
.transition-forward::view-transition-old(content) {
  animation: slide-to-left 0.25s ease-out;
}
.transition-forward::view-transition-new(content) {
  animation: slide-from-right 0.25s ease-out;
}

/* Back navigation */
.transition-back::view-transition-old(content) {
  animation: slide-to-right 0.25s ease-out;
}
.transition-back::view-transition-new(content) {
  animation: slide-from-left 0.25s ease-out;
}
```

In JavaScript, set the class on `<html>` before starting the transition based on navigation type or history state comparison.

### Shared Element Transitions

Named elements on both the old and new pages automatically receive a morph animation:

```css
/* Old page: product card image */
.product-card img { view-transition-name: product-image; }

/* New page: product detail hero image */
.product-detail .hero { view-transition-name: product-image; }
```

The browser interpolates position, size, and aspect ratio between the two states.

## Framework Integration

### SPA Frameworks

| Framework | Integration Approach |
|---|---|
| React (React Router) | Wrap `navigate()` in `document.startViewTransition()` |
| Vue (Vue Router) | Use `router.beforeResolve` hook with `startViewTransition` |
| Svelte (SvelteKit) | Built-in `onNavigate` lifecycle hook supports view transitions |
| Angular | `withViewTransitions()` in router configuration |
| Astro | Built-in `<ViewTransitions />` component for MPA transitions |

### Astro Integration

Astro provides first-class cross-document view transition support:

```astro
---
import { ViewTransitions } from 'astro:transitions';
---
<head>
  <ViewTransitions />
</head>
```

Astro handles the opt-in CSS, transition name management, and client-side script persistence across navigations.

### Integration Pattern for SPAs

```javascript
// Generic SPA integration
function navigateWithTransition(url, updateFn) {
  if (!document.startViewTransition) {
    updateFn();  // Fallback: instant update
    return;
  }
  document.startViewTransition(() => updateFn());
}
```

## Accessibility

### Reduced Motion

Respect the user's motion preference:

```css
@media (prefers-reduced-motion: reduce) {
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation-duration: 0.01s !important;
  }
}
```

This effectively makes the transition instant without disabling the API.

### Screen Readers

| Concern | Mitigation |
|---|---|
| Transition animations are visual only | Screen readers are not affected |
| Focus management | Ensure focus moves to appropriate element after transition |
| Content announcement | Use `aria-live` regions for dynamic content updates |
| Navigation feedback | Ensure route changes update the document title |

## Performance Considerations

### Transition Performance

| Factor | Impact | Mitigation |
|---|---|---|
| Large page screenshots | Memory for capturing old/new states | Limit transition scope with named elements |
| Complex CSS animations | GPU compositing, paint cost | Use `transform` and `opacity` only |
| DOM update during transition | Long task blocks transition start | Keep DOM updates fast, defer heavy work |
| Concurrent transitions | Multiple transitions queue or conflict | Skip previous transition before starting new one |

### Performance Best Practices

1. Keep animation duration short (200-400ms recommended)
2. Use `transform` and `opacity` for GPU-accelerated animations
3. Name only elements that need individual animation (not every element)
4. Skip transitions on slow connections or low-end devices
5. Avoid layout-triggering properties in transition animations
6. Test on mobile devices where GPU memory is limited

## Fallback Strategies

### Progressive Enhancement

```javascript
function navigate(url) {
  if (document.startViewTransition) {
    document.startViewTransition(() => loadPage(url));
  } else {
    loadPage(url);  // Works without transitions
  }
}
```

The View Transitions API is designed for progressive enhancement. Non-supporting browsers receive standard navigation or instant DOM updates with no degradation.

### Polyfill Considerations

There is no full polyfill for View Transitions. The API requires browser-level screenshot capabilities. For older browsers, use CSS animations triggered on route change as a visual approximation.
