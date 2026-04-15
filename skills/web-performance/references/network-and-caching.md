# Network and Caching Optimization

Sources: Grigorik (High Performance Browser Networking), MDN Web Docs (HTTP caching, Service Worker API), Google web.dev caching guides, Chromium network stack documentation

Covers: HTTP caching headers, compression (gzip, Brotli), HTTP/2 and HTTP/3, CDN strategy, service worker caching patterns, and third-party script management.

## HTTP Caching

### Cache-Control Header

The primary mechanism for controlling browser and CDN caching.

| Directive | Meaning | Use When |
| --- | --- | --- |
| `public` | Any cache (browser, CDN, proxy) can store | Static assets, public pages |
| `private` | Only browser cache, not CDN/proxy | User-specific content, authenticated pages |
| `max-age=N` | Cache is fresh for N seconds | All cacheable responses |
| `s-maxage=N` | CDN/proxy cache duration (overrides max-age) | CDN-cached pages with different browser TTL |
| `no-cache` | Must revalidate with server before using | HTML pages, API responses that change |
| `no-store` | Never cache | Sensitive data, banking pages |
| `immutable` | Never revalidate (used with content-hashed URLs) | Hashed static assets |
| `stale-while-revalidate=N` | Serve stale while fetching fresh in background | API responses, non-critical data |

### Caching Strategy by Resource Type

| Resource | Cache-Control | ETag | Rationale |
| --- | --- | --- | --- |
| HTML pages | `no-cache` or `max-age=0, must-revalidate` | Yes | Always check for fresh content |
| Hashed JS/CSS (`app.a1b2c3.js`) | `public, max-age=31536000, immutable` | No | Content-hash guarantees correctness |
| Unhashed JS/CSS | `public, max-age=3600` | Yes | Short TTL with revalidation |
| Images (hashed) | `public, max-age=31536000, immutable` | No | Long cache, bust via URL change |
| Images (unhashed) | `public, max-age=86400` | Yes | Daily refresh |
| API responses | `private, max-age=60, stale-while-revalidate=300` | Yes | Fresh data with background refresh |
| Fonts | `public, max-age=31536000, immutable` | No | Fonts rarely change |

### ETag and Conditional Requests

When `max-age` expires, the browser sends a conditional request:

```
GET /styles.css
If-None-Match: "abc123"     <- ETag from previous response

Server response (if unchanged):
304 Not Modified             <- No body transferred, saves bandwidth
```

ETags enable efficient revalidation without re-downloading unchanged resources.

### Content-Hashed URLs

The most effective caching pattern: include a content hash in the filename.

```
/assets/app.a1b2c3d4.js    <- Hash changes when content changes
/assets/vendor.e5f6g7h8.js
/assets/styles.i9j0k1l2.css
```

Set `Cache-Control: public, max-age=31536000, immutable`. The hash guarantees the browser fetches a new URL when content changes. No cache invalidation needed.

All modern bundlers (Webpack, Vite, Rollup) generate content-hashed filenames by default.

## Compression

### Brotli vs Gzip

| Aspect | Brotli | Gzip |
| --- | --- | --- |
| Compression ratio | 15-25% smaller than gzip | Baseline |
| Compression speed | Slower (use static pre-compression) | Fast |
| Decompression speed | Similar to gzip | Fast |
| Browser support | All modern browsers | Universal |
| Requirement | HTTPS only | HTTP or HTTPS |

### Configuration

```nginx
# nginx: Enable both Brotli and gzip
brotli on;
brotli_types text/html text/css application/javascript application/json image/svg+xml;
brotli_comp_level 6;

gzip on;
gzip_types text/html text/css application/javascript application/json image/svg+xml;
gzip_min_length 1024;
```

### Static Pre-Compression

For static assets, compress at build time for maximum compression ratio:

```bash
# Brotli (quality 11 for static files)
brotli --quality=11 dist/assets/*.js dist/assets/*.css

# Gzip
gzip -k -9 dist/assets/*.js dist/assets/*.css
```

Configure the server to serve `.br` or `.gz` files when `Accept-Encoding` matches.

### What to Compress

| Type | Compress? | Rationale |
| --- | --- | --- |
| JavaScript | Yes | Text-based, high compression ratio |
| CSS | Yes | Text-based, high compression ratio |
| HTML | Yes | Text-based |
| JSON | Yes | Text-based |
| SVG | Yes | Text-based XML |
| WOFF2 | No | Already compressed internally |
| JPEG/PNG/WebP/AVIF | No | Already compressed; re-compression wastes CPU |
| Video/Audio | No | Already compressed |

## HTTP/2 and HTTP/3

### HTTP/2 Benefits

| Feature | Impact |
| --- | --- |
| Multiplexing | Multiple requests over one connection, no head-of-line blocking |
| Header compression (HPACK) | Reduces header overhead (especially cookies) |
| Server Push | Server sends resources before browser requests them |
| Stream prioritization | Critical resources get bandwidth first |

### HTTP/2 Implications for Optimization

| Old Advice (HTTP/1.1) | New Advice (HTTP/2+) |
| --- | --- |
| Concatenate all JS into one file | Use smaller, granular chunks |
| Sprite sheets for icons | Individual SVG or icon font |
| Domain sharding (multiple CDN domains) | Single connection is better |
| Inline all CSS | Inline only critical CSS; external is fine |

With HTTP/2, many small files are often better than few large files because multiplexing eliminates the per-request overhead.

### HTTP/3 (QUIC)

Built on UDP instead of TCP. Benefits:
- Zero round-trip connection establishment (0-RTT)
- No head-of-line blocking at transport layer
- Better performance on lossy networks (mobile)
- Faster connection migration (switching from Wi-Fi to cellular)

Enable by setting the `Alt-Svc` header:

```
Alt-Svc: h3=":443"; ma=86400
```

## CDN Strategy

### What to CDN-Cache

| Content | CDN? | TTL | Rationale |
| --- | --- | --- | --- |
| Static assets (JS, CSS, images) | Yes | Long (1 year with hash) | Immutable, serve from edge |
| HTML pages (static/SSG) | Yes | Short (60s) with revalidation | Serve from edge, revalidate frequently |
| API responses (public) | Yes | Short (10-60s) with stale-while-revalidate | Reduce origin load |
| API responses (private) | No | N/A | User-specific data must not be shared |
| Dynamic HTML (SSR) | Depends | Short or stale-while-revalidate | Edge caching reduces TTFB |

### CDN Cache Invalidation

```bash
# Purge specific URL
curl -X POST https://cdn.example.com/purge \
  -d '{"url": "https://example.com/index.html"}'

# Purge by cache tag
curl -X POST https://cdn.example.com/purge \
  -d '{"tags": ["product-123"]}'
```

Use cache tags (Surrogate-Key / Cache-Tag headers) for granular invalidation without purging everything.

## Service Workers

### Caching Strategies

| Strategy | Behavior | Use For |
| --- | --- | --- |
| Cache First | Serve from cache, fallback to network | Static assets, fonts, images |
| Network First | Try network, fallback to cache | HTML pages, API data |
| Stale While Revalidate | Serve from cache, update in background | Non-critical API data, feeds |
| Network Only | Always network, no caching | Authentication, real-time data |
| Cache Only | Only cache, never network | Offline-first static content |

### Cache First Implementation

```javascript
// service-worker.js
const CACHE_NAME = 'static-v1';
const STATIC_ASSETS = [
  '/app.js',
  '/styles.css',
  '/offline.html',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.destination === 'image' ||
      event.request.url.includes('/assets/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        return cached || fetch(event.request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        });
      })
    );
  }
});
```

### Stale While Revalidate Implementation

```javascript
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        const fetchPromise = fetch(event.request).then(response => {
          const clone = response.clone();
          caches.open('api-cache').then(cache =>
            cache.put(event.request, clone)
          );
          return response;
        });
        return cached || fetchPromise;
      })
    );
  }
});
```

## Third-Party Script Management

### Audit Framework

For every third-party script, answer:

1. **Is it necessary?** Can the feature be removed or built in-house?
2. **What is the cost?** Size, main-thread time, network requests it spawns.
3. **Can it be deferred?** Load after critical content.
4. **Can it use a facade?** Show a static placeholder until user interaction.

### Loading Strategies by Priority

| Priority | Strategy | Example |
| --- | --- | --- |
| Critical (blocks revenue) | `async` in `<head>` | Payment SDK, A/B testing |
| Important (enhances UX) | `defer` in `<head>` | Analytics, error tracking |
| Non-essential (nice to have) | Load on interaction or idle | Chat widget, feedback tool |
| Below-fold embed | Facade + lazy load | YouTube, Google Maps |

### Facade Pattern

Replace heavy third-party embeds with a lightweight placeholder. Load the real embed on interaction.

```html
<!-- Facade: static thumbnail, loads real player on click -->
<div class="youtube-facade" data-video-id="dQw4w9WgXcQ">
  <img src="/thumbs/dQw4w9WgXcQ.webp" alt="Video title"
       width="560" height="315" loading="lazy">
  <button aria-label="Play video">Play</button>
</div>

<script>
document.querySelectorAll('.youtube-facade').forEach(facade => {
  facade.addEventListener('click', () => {
    const iframe = document.createElement('iframe');
    iframe.src = `https://www.youtube.com/embed/${facade.dataset.videoId}?autoplay=1`;
    iframe.width = 560;
    iframe.height = 315;
    iframe.allow = 'autoplay; encrypted-media';
    facade.replaceWith(iframe);
  }, { once: true });
});
</script>
```

A YouTube facade saves ~500 KB of JavaScript per embed.

### Delayed Loading

Load non-critical scripts after user interaction or during idle time:

```javascript
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Load on first user interaction
['click', 'scroll', 'keydown', 'touchstart'].forEach(event => {
  window.addEventListener(event, () => {
    loadScript('https://chat-widget.com/sdk.js');
    loadScript('https://feedback.com/widget.js');
  }, { once: true });
});
```
