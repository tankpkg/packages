# Runtime Performance

Sources: Grigorik (High Performance Browser Networking), Google Chromium rendering documentation, web.dev runtime performance guides, MDN Web Docs (Performance API, Web Workers), Wagner (Web Performance in Action)

Covers: DOM batch reads/writes, requestAnimationFrame, forced reflow avoidance, Web Workers, virtual lists, event delegation, debounce/throttle, long task management, and memory optimization.

## The Rendering Pipeline

Every frame the browser executes:

```
JavaScript -> Style -> Layout -> Paint -> Composite
```

| Phase | Cost | Triggered By |
| --- | --- | --- |
| JavaScript | Variable | Event handlers, timers, rAF callbacks |
| Style | Moderate | Class changes, inline style changes |
| Layout (reflow) | Expensive | Width/height/position changes, DOM mutations |
| Paint | Expensive | Color/background changes, text changes |
| Composite | Cheap | Transform/opacity changes only |

**Target: 16.6ms per frame** for 60fps. If any phase exceeds this, frames drop.

### Composite-Only Animations

The cheapest visual changes only trigger compositing:

```css
/* GOOD: Only triggers composite */
.animate {
  transform: translateX(100px);
  opacity: 0.5;
  will-change: transform;
}

/* BAD: Triggers layout + paint + composite */
.animate-bad {
  left: 100px;     /* Layout */
  width: 200px;    /* Layout */
  background: red; /* Paint */
}
```

Always animate `transform` and `opacity`. Never animate `top`, `left`, `width`, `height`, `margin`, or `padding`.

## DOM Batching: Reads and Writes

Interleaving DOM reads and writes causes forced synchronous layout (layout thrashing).

### The Problem

```javascript
// BAD: Read-write-read-write forces layout recalculation each cycle
for (const el of elements) {
  const height = el.offsetHeight;    // READ -> forces layout
  el.style.height = height * 2 + 'px'; // WRITE -> invalidates layout
}
// Each READ after a WRITE forces the browser to recalculate layout
```

### The Fix: Batch Reads, Then Batch Writes

```javascript
// GOOD: All reads first, then all writes
const heights = [];
for (const el of elements) {
  heights.push(el.offsetHeight); // READ (only one layout calculation)
}
for (let i = 0; i < elements.length; i++) {
  elements[i].style.height = heights[i] * 2 + 'px'; // WRITE
}
```

### Properties That Trigger Layout

Reading any of these forces a synchronous layout if the DOM is dirty:

| Category | Properties |
| --- | --- |
| Box dimensions | `offsetWidth`, `offsetHeight`, `offsetTop`, `offsetLeft` |
| Scroll | `scrollTop`, `scrollLeft`, `scrollWidth`, `scrollHeight` |
| Client | `clientWidth`, `clientHeight`, `clientTop`, `clientLeft` |
| Window | `innerWidth`, `innerHeight`, `getComputedStyle()` |
| Element | `getBoundingClientRect()`, `focus()` |

### Using requestAnimationFrame for Writes

```javascript
function updateLayout(elements, newPositions) {
  // Schedule writes for the next frame
  requestAnimationFrame(() => {
    for (let i = 0; i < elements.length; i++) {
      elements[i].style.transform = `translateY(${newPositions[i]}px)`;
    }
  });
}
```

### fastdom Pattern

For complex interleaved operations, use the read/write scheduling pattern:

```javascript
// Read phase
const measurements = [];
requestAnimationFrame(() => {
  // Batch all reads
  for (const el of elements) {
    measurements.push(el.getBoundingClientRect());
  }

  // Then schedule writes in the next microtask
  requestAnimationFrame(() => {
    for (let i = 0; i < elements.length; i++) {
      elements[i].style.transform =
        `translate(${measurements[i].left}px, ${measurements[i].top}px)`;
    }
  });
});
```

## Long Tasks and Main Thread Management

A long task is any JavaScript execution that takes > 50ms, blocking user input.

### Yielding to the Main Thread

```javascript
// Modern: scheduler.yield() (Chrome 129+)
async function processItems(items) {
  for (const item of items) {
    processItem(item);
    await scheduler.yield(); // Yield after each item
  }
}

// Fallback: setTimeout yielding
function yieldToMain() {
  return new Promise(resolve => setTimeout(resolve, 0));
}

async function processItemsCompat(items) {
  for (let i = 0; i < items.length; i++) {
    processItem(items[i]);
    if (i % 50 === 0) await yieldToMain();
  }
}
```

### Time-Slicing Pattern

Process work in fixed time slices, yielding between slices:

```javascript
async function timeSlice(tasks, sliceMs = 5) {
  let deadline = performance.now() + sliceMs;
  let i = 0;

  while (i < tasks.length) {
    tasks[i]();
    i++;

    if (performance.now() >= deadline) {
      await yieldToMain();
      // Reset deadline for next slice
      deadline = performance.now() + sliceMs;
    }
  }
}
```

## Web Workers

Move CPU-intensive work off the main thread entirely.

### When to Use Workers

| Use Case | Main Thread? | Worker? |
| --- | --- | --- |
| DOM manipulation | Yes | No (no DOM access) |
| Event handling | Yes | No |
| Data parsing (large JSON) | No | Yes |
| Sorting/filtering large datasets | No | Yes |
| Image processing | No | Yes |
| Cryptographic operations | No | Yes |
| Text search/regex on large text | No | Yes |
| WebSocket message processing | Either | Recommended |

### Basic Worker Pattern

```javascript
// main.js
const worker = new Worker('/worker.js');

worker.postMessage({ type: 'sort', data: largeArray });

worker.addEventListener('message', (event) => {
  const { sorted } = event.data;
  renderList(sorted);
});
```

```javascript
// worker.js
self.addEventListener('message', (event) => {
  const { type, data } = event.data;

  if (type === 'sort') {
    const sorted = data.sort((a, b) => a.value - b.value);
    self.postMessage({ sorted });
  }
});
```

### Transferable Objects

For large ArrayBuffers, use transfer instead of copy:

```javascript
// Main thread: transfer the buffer (zero-copy)
const buffer = new ArrayBuffer(1024 * 1024); // 1 MB
worker.postMessage({ buffer }, [buffer]);
// buffer is now unusable in main thread (transferred)

// Worker: receive and process
self.addEventListener('message', (event) => {
  const { buffer } = event.data;
  const view = new Float32Array(buffer);
  // Process the data...
  self.postMessage({ buffer }, [buffer]); // Transfer back
});
```

### Comlink (Simplified Worker API)

```javascript
// worker.js
import { expose } from 'comlink';

const api = {
  async processData(data) {
    return heavyComputation(data);
  },
};

expose(api);

// main.js
import { wrap } from 'comlink';

const worker = new Worker('/worker.js');
const api = wrap(worker);

const result = await api.processData(largeDataset);
```

## Virtual Lists (Windowed Rendering)

Render only visible items. Critical for lists with 1,000+ items.

### Core Concept

Instead of rendering 10,000 DOM nodes, render only the 20-30 visible in the viewport. As the user scrolls, recycle DOM nodes with new data.

### Minimal Implementation

```javascript
class VirtualList {
  constructor(container, items, itemHeight) {
    this.container = container;
    this.items = items;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight) + 2;

    this.container.style.overflow = 'auto';
    this.container.style.position = 'relative';

    // Spacer for total scroll height
    this.spacer = document.createElement('div');
    this.spacer.style.height = `${items.length * itemHeight}px`;
    this.container.appendChild(this.spacer);

    this.container.addEventListener('scroll', () => this.render());
    this.render();
  }

  render() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = Math.min(startIndex + this.visibleCount, this.items.length);

    // Clear and re-render visible items
    const fragment = document.createDocumentFragment();
    for (let i = startIndex; i < endIndex; i++) {
      const el = document.createElement('div');
      el.style.position = 'absolute';
      el.style.top = `${i * this.itemHeight}px`;
      el.style.height = `${this.itemHeight}px`;
      el.textContent = this.items[i];
      fragment.appendChild(el);
    }

    // Remove old rendered items, add new
    this.spacer.innerHTML = '';
    this.spacer.style.height = `${this.items.length * this.itemHeight}px`;
    this.spacer.appendChild(fragment);
  }
}
```

For production, use established libraries: `@tanstack/virtual`, `react-window`, `react-virtuoso`.

## Event Delegation

Attach one handler to a parent instead of N handlers to N children.

```javascript
// BAD: 1000 event listeners
document.querySelectorAll('.item').forEach(item => {
  item.addEventListener('click', handleClick);
});

// GOOD: 1 event listener
document.getElementById('list').addEventListener('click', (event) => {
  const item = event.target.closest('.item');
  if (item) handleClick(item);
});
```

Benefits:
- Lower memory usage (1 listener vs N)
- Works with dynamically added elements
- Faster setup (no loop over elements)

## Debounce and Throttle

### Debounce

Execute after the user stops firing events. Use for search input, resize, form validation.

```javascript
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

searchInput.addEventListener('input', debounce((e) => {
  fetchResults(e.target.value);
}, 300));
```

### Throttle

Execute at most once per interval. Use for scroll handlers, mousemove, game loops.

```javascript
function throttle(fn, ms) {
  let last = 0;
  return (...args) => {
    const now = Date.now();
    if (now - last >= ms) {
      last = now;
      fn(...args);
    }
  };
}

window.addEventListener('scroll', throttle(updateScrollIndicator, 100));
```

## content-visibility

Skip rendering of off-screen content entirely:

```css
.section {
  content-visibility: auto;
  contain-intrinsic-size: auto 500px; /* Estimated height */
}
```

The browser skips layout and paint for off-screen sections, dramatically reducing initial rendering cost for long pages. The `contain-intrinsic-size` prevents scrollbar jumping by providing an estimated height.

## Memory Optimization

| Pattern | Problem | Fix |
| --- | --- | --- |
| Event listeners not removed | Memory leak on SPA navigation | Remove in cleanup/destroy lifecycle |
| Closures holding large objects | Prevents garbage collection | Nullify references when done |
| Unbounded caches/arrays | Memory grows indefinitely | Use LRU cache, set max size |
| Detached DOM nodes | Elements removed but still referenced | Clear references after removal |
| Large object creation in loops | GC pressure, jank | Reuse objects, use object pools |

### Detecting Memory Leaks

1. DevTools > Memory > Heap Snapshot.
2. Take snapshot before action, perform action, take snapshot after.
3. Compare snapshots. Look for unexpected retained objects.
4. Use "Allocation timeline" to see where objects are allocated.
