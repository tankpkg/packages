# Image and Media Optimization

Sources: Google web.dev image optimization guides, MDN Web Docs (responsive images, lazy loading), Squoosh documentation, Chromium image decoding architecture, HTTP Archive annual reports

Covers: Modern image formats (AVIF, WebP, JPEG, PNG), responsive images with srcset and sizes, lazy loading, Low-Quality Image Placeholders (LQIP), video replacement for animated content, and image CDN transforms.

## Format Selection

### Format Comparison

| Format | Best For | Compression | Browser Support | Alpha | Animation |
| --- | --- | --- | --- | --- | --- |
| AVIF | Photos, illustrations | Best (50% smaller than JPEG) | Chrome, Firefox, Safari 16.4+ | Yes | Yes |
| WebP | Photos, illustrations | Good (25-35% smaller than JPEG) | All modern browsers | Yes | Yes |
| JPEG | Photos (fallback) | Good | Universal | No | No |
| PNG | Graphics needing transparency | Lossless | Universal | Yes | No |
| SVG | Icons, logos, illustrations | Vector (scales infinitely) | Universal | Yes | Yes (CSS/SMIL) |
| GIF | Simple animations (legacy) | Poor | Universal | Binary only | Yes |

### Decision Tree

| Content | Primary Format | Fallback |
| --- | --- | --- |
| Hero photograph | AVIF | WebP, then JPEG |
| Product photo | AVIF or WebP | JPEG |
| Icon or logo | SVG | PNG (for raster fallback) |
| Screenshot with text | WebP (lossless) or PNG | PNG |
| Animated content (short) | Animated WebP or `<video>` | GIF (last resort) |
| Animated content (long) | `<video>` (MP4/WebM) | Never use GIF |
| Decorative background | CSS gradient or WebP | JPEG |
| Thumbnail / placeholder | Tiny AVIF/WebP or CSS blur | Solid color |

### Quality Settings

| Format | Recommended Quality | Notes |
| --- | --- | --- |
| AVIF | 50-65 | Excellent quality at low values |
| WebP | 75-85 | Good balance of size and quality |
| JPEG | 75-85 | Below 70 shows visible artifacts |
| PNG | Lossless | Use pngquant for lossy PNG-8 if size matters |

Test quality with A/B comparison. Audience tolerance varies by content type.

## The `<picture>` Element

Serve modern formats with automatic fallback:

```html
<picture>
  <!-- AVIF for browsers that support it -->
  <source type="image/avif"
          srcset="/img/hero.avif 1x, /img/hero@2x.avif 2x">

  <!-- WebP fallback -->
  <source type="image/webp"
          srcset="/img/hero.webp 1x, /img/hero@2x.webp 2x">

  <!-- JPEG for everything else -->
  <img src="/img/hero.jpg"
       alt="Hero image description"
       width="1200" height="600"
       loading="eager"
       fetchpriority="high"
       decoding="async">
</picture>
```

The browser selects the first `<source>` it supports. The `<img>` is always required as the final fallback.

## Responsive Images

### srcset with Width Descriptors

Let the browser choose the optimal image size based on viewport and device pixel ratio:

```html
<img src="/img/product-800.jpg"
     srcset="/img/product-400.jpg 400w,
            /img/product-800.jpg 800w,
            /img/product-1200.jpg 1200w,
            /img/product-1600.jpg 1600w"
     sizes="(max-width: 600px) 100vw,
            (max-width: 1200px) 50vw,
            33vw"
     alt="Product name"
     width="800" height="600"
     loading="lazy"
     decoding="async">
```

### How `sizes` Works

| sizes Value | Meaning |
| --- | --- |
| `100vw` | Image fills the full viewport width |
| `50vw` | Image fills half the viewport |
| `(max-width: 600px) 100vw, 50vw` | Full width on mobile, half on desktop |
| `(max-width: 600px) calc(100vw - 32px), 400px` | Accounting for padding, or fixed width |

The browser uses `sizes` to calculate which `srcset` entry to download before layout.

### Breakpoint Strategy

Generate image sizes at common layout breakpoints:

| Breakpoint | Typical Image Width | srcset Entry |
| --- | --- | --- |
| Mobile (< 600px) | 400-600px | `400w`, `600w` |
| Tablet (600-1024px) | 600-800px | `800w` |
| Desktop (1024-1440px) | 800-1200px | `1200w` |
| Large desktop (> 1440px) | 1200-1600px | `1600w` |
| Retina (2x) | 2x of layout width | Already handled by `w` descriptors |

Do not generate more than 4-6 sizes. The marginal benefit of more sizes does not justify the build complexity and CDN storage.

### Art Direction

Use `<picture>` with `media` attributes when the image composition changes at breakpoints:

```html
<picture>
  <!-- Cropped vertical for mobile -->
  <source media="(max-width: 600px)"
          srcset="/img/hero-mobile.avif" type="image/avif">
  <source media="(max-width: 600px)"
          srcset="/img/hero-mobile.webp" type="image/webp">

  <!-- Wide landscape for desktop -->
  <source srcset="/img/hero-desktop.avif" type="image/avif">
  <source srcset="/img/hero-desktop.webp" type="image/webp">

  <img src="/img/hero-desktop.jpg" alt="Hero" width="1600" height="600">
</picture>
```

## Lazy Loading

### Native Lazy Loading

```html
<!-- Lazy load below-fold images -->
<img src="/img/product.webp" loading="lazy" alt="Product"
     width="400" height="300" decoding="async">

<!-- Do not lazy load above-fold / LCP images — they need eager loading -->
<img src="/img/hero.webp" loading="eager" alt="Hero"
     width="1200" height="600" fetchpriority="high">
```

### Rules

| Position | loading | fetchpriority | decoding |
| --- | --- | --- | --- |
| Above fold, LCP candidate | `eager` (or omit) | `high` | `async` |
| Above fold, not LCP | `eager` (or omit) | `auto` | `async` |
| Below fold | `lazy` | `auto` | `async` |
| Far below fold (gallery) | `lazy` | `low` | `async` |

### Intersection Observer (Custom Lazy Loading)

For more control or older browser support:

```javascript
const imageObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        if (img.dataset.srcset) img.srcset = img.dataset.srcset;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  },
  { rootMargin: '300px' } // Start loading 300px before visible
);

document.querySelectorAll('img[data-src]').forEach(img => {
  imageObserver.observe(img);
});
```

## LQIP (Low-Quality Image Placeholder)

Show a blurred tiny image while the full image loads. Prevents layout shift and improves perceived performance.

### Inline Base64 LQIP

```html
<div class="lqip-container" style="aspect-ratio: 16/9;">
  <!-- Tiny blurred placeholder (< 1 KB inline) -->
  <img class="lqip-placeholder"
       src="data:image/webp;base64,UklGRlYAAABXRUJQVlA4IEoAAADQAQCdASoQAAkAAkA..."
       style="filter: blur(20px); width: 100%; height: 100%; object-fit: cover;"
       alt="" aria-hidden="true">

  <!-- Full image (replaces placeholder on load) -->
  <img class="lqip-full"
       src="/img/hero.webp"
       loading="lazy"
       onload="this.previousElementSibling.remove(); this.style.opacity=1;"
       style="opacity: 0; transition: opacity 0.3s;"
       alt="Hero image" width="1200" height="675">
</div>
```

### CSS Gradient Placeholder

Even simpler: extract the dominant color and use it as background:

```html
<div style="background: #2a4858; aspect-ratio: 16/9;">
  <img src="/img/landscape.webp"
       loading="lazy"
       style="opacity: 0; transition: opacity 0.3s;"
       onload="this.style.opacity=1"
       alt="Landscape" width="1200" height="675">
</div>
```

### BlurHash

Encode images into a compact string that renders as a blurred preview on the client. Libraries: `blurhash`, `thumbhash`.

```javascript
// Server: encode during image processing
import { encode } from 'blurhash';
const hash = encode(imageData, width, height, 4, 3);
// Store "LKO2?U%2Tw=w]~RBVZRi};RPxuwH" in database

// Client: decode and render as canvas
import { decode } from 'blurhash';
const pixels = decode(hash, 32, 32);
// Render pixels to a small canvas, display as background
```

## Replacing GIFs with Video

Animated GIFs are 5-20x larger than equivalent video. Replace them.

```html
<!-- Replaces an animated GIF -->
<video autoplay loop muted playsinline
       width="600" height="400"
       poster="/img/animation-poster.webp">
  <source src="/video/animation.webm" type="video/webm">
  <source src="/video/animation.mp4" type="video/mp4">
</video>
```

Conversion:

```bash
# Convert GIF to WebM (VP9)
ffmpeg -i animation.gif -c:v libvpx-vp9 -b:v 0 -crf 40 animation.webm

# Convert GIF to MP4 (H.264)
ffmpeg -i animation.gif -movflags +faststart -pix_fmt yuv420p animation.mp4
```

Typical size reduction: 80-95%.

## Image CDN Transforms

Use an image CDN (Cloudinary, Imgix, Cloudflare Images, Vercel OG) to transform images on the fly.

```html
<!-- Cloudinary: auto format, auto quality, resize to 800px -->
<img src="https://res.cloudinary.com/demo/image/upload/f_auto,q_auto,w_800/sample.jpg"
     alt="Sample" width="800" height="600" loading="lazy">

<!-- Imgix: WebP auto, quality 75, width 800 -->
<img src="https://example.imgix.net/photo.jpg?auto=format&q=75&w=800"
     alt="Photo" width="800" height="600" loading="lazy">
```

Benefits:
- No build-time image processing pipeline
- Automatic format negotiation (AVIF/WebP/JPEG)
- On-the-fly resize and crop
- Global CDN delivery
- Reduces origin storage (one source image, infinite variants)

## Performance Impact Summary

| Optimization | Typical LCP Improvement | Effort |
| --- | --- | --- |
| Serve AVIF/WebP instead of JPEG/PNG | 30-50% smaller images | Low (build pipeline change) |
| Responsive images with srcset | 40-60% savings on mobile | Medium |
| Lazy load below-fold images | Faster initial load | Low |
| LQIP placeholders | Better perceived speed, zero CLS | Medium |
| Replace GIFs with video | 80-95% smaller files | Low |
| Image CDN | All of the above, automated | Low (service integration) |
| fetchpriority="high" on LCP image | 100-300ms LCP improvement | Trivial |
