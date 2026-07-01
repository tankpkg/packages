# UI Sizing Rules

Sources: Apple HIG (2025), Material Design 3 spec, WCAG 2.2, Tailwind CSS v3, Carbon Design System (IBM), shadcn/ui source, Radix UI Themes source, MUI source, Ant Design tokens, Wathan/Schoger (Refactoring UI)

Covers: exact component dimensions (buttons, inputs, navbars, sidebars, modals, cards, avatars), padding-to-element ratios, icon sizing, container and layout widths, aspect ratios, section spacing, cross-system sizing data. All values are concrete numbers — no theory, only lookup tables.

> **For the 4pt spacing grid, z-index scale, touch targets, and modular type scales, see `references/design-foundations.md`.** This file covers component-level sizing that builds on that foundation.

---

## Button Dimensions

Height is fixed; vertical centering via flexbox. Horizontal padding is the primary variable.

### Standard Button Sizes

| Size | Height | Padding X | Padding Y | Font | Icon | Use |
|------|--------|-----------|-----------|------|------|-----|
| XS | 24px | 8px | 4px | 12px | 12px | Dense tables, tags |
| SM | 32px | 12px | 6px | 13–14px | 14px | Toolbars, secondary |
| **MD** | **36–40px** | **16px** | **8–10px** | **14px** | **16px** | **Default UI** |
| LG | 44–48px | 20px | 10–12px | 15–16px | 16px | Primary CTAs, touch |
| XL | 56px | 24px | 14px | 16px | 20px | Hero CTAs |
| 2XL | 64–80px | 32px | 20px | 18px | 24px | Marketing |

### Cross-System Button Heights

| System | XS | SM | MD (default) | LG |
|--------|----|----|-------------|-----|
| shadcn/ui (base-vega) | 24px (`h-6`) | 32px (`h-8`) | 36px (`h-9`) | 40px (`h-10`) |
| shadcn/ui (compact) | 20px (`h-5`) | 24px (`h-6`) | 28px (`h-7`) | 32px (`h-8`) |
| Radix UI Themes | 24px (size-1) | 32px (size-2) | 40px (size-3) | 48px (size-4) |
| MUI | — | — | 36px | — |
| Ant Design | — | 24px | 32px | 40px |
| Carbon (IBM) | 24px | 32px | 40px | 48px |

### Button Padding Formula

**Horizontal padding = 2–3x vertical padding.** Horizontal padding to height ratio = 0.3–0.5x.

| Size | Height | PX | PY | H:V Ratio | PX/Height |
|------|--------|----|----|-----------|-----------|
| XS | 24px | 8px | 4px | 2:1 | 0.33 |
| SM | 32px | 12px | 6px | 2:1 | 0.38 |
| MD | 40px | 16px | 8px | 2:1 | 0.40 |
| LG | 48px | 20px | 10px | 2:1 | 0.42 |
| XL | 56px | 24px | 14px | 1.7:1 | 0.43 |

**Derive PY from height:** `PY = (height - line-height) / 2`. For 40px button with 14px font at 1.5 line-height (21px): `(40 - 21) / 2 = 10px`.

### shadcn/ui Button Padding (from source)

| Size | Height | px-horiz | Font | Icon gap |
|------|--------|----------|------|----------|
| xs | `h-6` (24px) | `px-2` (8px) | `text-xs` (12px) | `gap-1` (4px) |
| sm | `h-8` (32px) | `px-2.5` (10px) | `text-sm` (14px) | `gap-1` (4px) |
| default | `h-9` (36px) | `px-2.5` (10px) | `text-sm` (14px) | `gap-1.5` (6px) |
| lg | `h-10` (40px) | `px-4` (16px) | `text-sm` (14px) | `gap-1.5` (6px) |
| icon | `h-9 w-9` (36x36px) | — | — | — |

---

## Input & Form Field Dimensions

Match input height to default button height — if buttons are 40px, inputs are 40px.

### Standard Input Sizes

| Size | Height | Padding X | Padding Y | Font |
|------|--------|-----------|-----------|------|
| SM | 32px | 10–12px | 6px | 13px |
| **MD** | **36–40px** | **12–16px** | **8–10px** | **14–16px** |
| LG | 44–48px | 16px | 10–12px | 16px |

### Cross-System Input Heights

| System | SM | MD (default) | LG |
|--------|----|--------------|----|
| shadcn/ui (base-vega) | — | 36px (`h-9`) | — |
| shadcn/ui (compact) | — | 28px (`h-7`) | — |
| Radix UI Themes | 24px (size-1) | 32px (size-2) | 40px (size-3) |
| MUI | 40px (small) | 56px (medium) | — |
| Ant Design | 24px | 32px | 40px |

### Form Spacing

| Context | Gap |
|---------|-----|
| Label to input | 4–6px |
| Input to input (stacked) | 16–24px (`gap-4` to `gap-6`) |
| Form group to form group | 24–32px |
| Inline buttons | 8–12px (`gap-2` to `gap-3`) |

---

## Navigation Components

### Heights

| Component | Height |
|-----------|--------|
| Top navbar (mobile) | 44–56px |
| Top navbar (desktop, compact) | 48–56px |
| **Top navbar (desktop, standard)** | **56–64px** |
| Top navbar (marketing) | 72–80px |
| Bottom tab bar (iOS) | 49pt |
| Bottom tab bar (Android) | 56dp |
| Breadcrumb row | 32–40px |
| Tab bar (desktop) | 36–44px |

### Sidebar Widths

| Type | Width | Tailwind |
|------|-------|---------|
| Collapsed (icon-only) | 48–64px | `w-12` to `w-16` |
| Narrow | 200–220px | `w-[220px]` |
| **Standard** | **240–260px** | **`w-60` to `w-64`** |
| Wide | 280–320px | `w-72` to `w-80` |
| Extra wide (with previews) | 360–400px | `w-[360px]` |
| Mobile drawer | 280–320px | `w-72` to `w-80` |

---

## Modal & Dialog Dimensions

### Widths

| Size | Width | Use |
|------|-------|-----|
| SM | 384–480px | Confirmations, alerts |
| **MD** | **448–640px** | **Forms, standard dialogs** |
| LG | 720–800px | Complex forms, editors |
| XL | 900–1024px | Full editors, settings |
| Full | 100vw | Mobile sheets |

### Cross-System Modal Widths

| System | SM | MD (default) | LG |
|--------|----|--------------|----|
| shadcn/ui (base-vega) | — | 448px (`max-w-md`) | — |
| shadcn/ui (compact) | 384px (`max-w-sm`) | — | — |
| Radix UI Themes | 600px (all sizes) | 600px | 600px |
| MUI | 444px (xs) | 600px (sm) | 900px (md) |

### Modal Properties

| Property | Value |
|----------|-------|
| Padding (SM) | 16px (`p-4`) |
| **Padding (MD)** | **24px (`p-6`)** |
| Padding (LG) | 32px (`p-8`) |
| Header height | 56–64px |
| Footer height | 56–72px |
| Max height | 85–90vh |
| Backdrop opacity | 40–60% black (`bg-black/50`) |
| Border radius | `rounded-lg` (8px) to `rounded-xl` (12px) |

---

## Card Dimensions

### Padding by Density

| Type | Padding | Tailwind | Gap |
|------|---------|---------|-----|
| Compact (data-dense) | 12px | `p-3` | 8px |
| **Standard** | **16–20px** | **`p-4` to `p-5`** | **12–16px** |
| Comfortable | 24px | `p-6` | 16px |
| Spacious / marketing | 32–48px | `p-8` to `p-12` | 24px |

### shadcn/ui Card (from source)

| Element | Padding | Font |
|---------|---------|------|
| Card body | `py-4 px-4` (16px) | — |
| CardHeader | `px-4` (16px) | — |
| Card sections gap | `gap-4` (16px) | — |
| CardTitle | — | 14px (`text-sm`) |
| CardDescription | — | 12px (`text-xs`) |

### Card Grid Gaps

| Density | Gap |
|---------|-----|
| Tight | 16px (`gap-4`) |
| **Standard** | **24px (`gap-6`)** |
| Spacious | 32px (`gap-8`) |

---

## Avatar Sizes

### Standard Sizes

| Size | Diameter | Fallback Font | Use |
|------|----------|---------------|-----|
| XS | 24px | 12px | Comment threads, dense lists |
| SM | 32px | 14px | Nav items, compact cards |
| **MD** | **40px** | **16px** | **User cards, profile sections** |
| LG | 48px | 18px | Profile headers |
| XL | 64px | 24px | Profile pages, team grids |
| 2XL | 80–96px | 28px | Account settings, hero |
| 3XL | 128–160px | 35–60px | Large profile display |

**Fallback font ratio:** font-size = 0.45–0.5x diameter.

### Radix UI Avatar Scale (9 sizes)

| Size | Diameter | 1-char font | 2-char font |
|------|----------|-------------|-------------|
| 1 | 24px | 14px | 12px |
| 2 | 32px | 16px | 14px |
| 3 | 40px | 18px | 16px |
| 4 | 48px | 20px | 18px |
| 5 | 64px | 24px | — |
| 6 | 80px | 28px | — |
| 7 | 96px | 28px | — |
| 8 | 128px | 35px | — |
| 9 | 160px | 60px | — |

---

## Icon Sizing

### Standard Icon Grid

| Size | Use | Tailwind |
|------|-----|---------|
| 12px | Inline with 10–11px text | `w-3 h-3` |
| 14px | Inline with 12–13px text | `w-3.5 h-3.5` |
| **16px** | **Default inline** — with 14–16px text | **`w-4 h-4`** |
| 20px | Medium UI — with 16–18px text | `w-5 h-5` |
| **24px** | **Standard UI** — nav, toolbar, standalone | **`w-6 h-6`** |
| 32px | Feature icons, empty states | `w-8 h-8` |
| 48px | Illustration-scale, onboarding | `w-12 h-12` |
| 64px | Hero icons, empty state graphics | `w-16 h-16` |

### Icon-to-Text Pairing

Icon should match the cap-height of adjacent text (1.0–1.25x the font size):

| Text Size | Icon Size | Ratio |
|-----------|-----------|-------|
| 12px | 12–14px | 1.0–1.17x |
| 14px | 14–16px | 1.0–1.14x |
| 16px | 16–20px | 1.0–1.25x |
| 20px | 20–24px | 1.0–1.2x |

### Icon Button Sizing

Visual icon inside larger touch target:

```html
<!-- 20px icon, 44px touch target -->
<button class="w-11 h-11 flex items-center justify-center">
  <svg class="w-5 h-5" />
</button>
```

### Lucide / Heroicons Conventions

- ViewBox: 24x24px
- Stroke width: 1.5px
- Minimum render: 16px (strokes blur below this)
- Shipped sizes: 16, 20, 24 (Heroicons)

---

## Container & Layout Widths

### Page Containers by Use Case

| Use Case | Max Width | Tailwind |
|----------|-----------|---------|
| Blog / article content | 680–760px | `max-w-2xl` to `max-w-3xl` |
| Documentation content | 800–900px | `max-w-4xl` |
| SaaS app | 1280–1440px | `max-w-7xl` |
| **Standard page container** | **1280px** | **`max-w-7xl`** |
| Dashboard | 1440–1920px | Often no max-width |
| Marketing / landing | 1200–1440px | `max-w-7xl` |
| Auth pages (centered card) | 400–480px | `max-w-md` |

### Tailwind Max-Width Scale (Key Values)

| Class | Value | px |
|-------|-------|----|
| `max-w-sm` | 24rem | 384px |
| `max-w-md` | 28rem | 448px |
| `max-w-lg` | 32rem | 512px |
| `max-w-xl` | 36rem | 576px |
| `max-w-2xl` | 42rem | 672px |
| `max-w-3xl` | 48rem | 768px |
| `max-w-4xl` | 56rem | 896px |
| `max-w-5xl` | 64rem | 1024px |
| `max-w-7xl` | 80rem | 1280px |
| `max-w-prose` | 65ch | ~640px |

### Breakpoints

| Name | Tailwind | Common Devices |
|------|----------|----------------|
| SM | 640px | Large phones |
| MD | 768px | Tablets (portrait) |
| LG | 1024px | Tablets (landscape), small laptops |
| XL | 1280px | Laptops, desktops |
| 2XL | 1536px | Large monitors |

---

## Section & Page Spacing

### Vertical Section Padding

| Section Type | Padding Y | Tailwind |
|-------------|-----------|---------|
| Hero | 80–160px | `py-20` to `py-40` |
| Feature grid | 64–96px | `py-16` to `py-24` |
| CTA band | 64–80px | `py-16` to `py-20` |
| Testimonials | 64–96px | `py-16` to `py-24` |
| Footer | 48–64px top, 32–48px bottom | `pt-12 pb-8` |

### Horizontal Page Padding

| Viewport | Padding | Tailwind |
|----------|---------|---------|
| Mobile | 16px | `px-4` |
| Tablet | 24–32px | `px-6` to `px-8` |
| Desktop | 32–48px | `px-8` to `px-12` |

### Content-to-Whitespace Ratios

| Context | Content | Whitespace |
|---------|---------|------------|
| Data-dense tables | 70–80% | 20–30% |
| Standard forms | 55–65% | 35–45% |
| Marketing pages | 40–50% | 50–60% |
| Landing hero | 30–40% | 60–70% |

---

## Table Cell Padding

### Cross-System Table Cells

| System | Cell Padding | Row Height | Font |
|--------|-------------|------------|------|
| shadcn/ui | 8px (`p-2`) | auto | 12px |
| Radix size-1 | 8px | 36px | 14px |
| Radix size-2 | 12px | 44px | 14px |
| Radix size-3 | 12px x 16px | 48px | 16px |
| MUI normal | 16px | auto | 14px |
| MUI dense | 6px x 16px | auto | 12px |

---

## Aspect Ratios

### Standard Ratios

| Ratio | Decimal | Primary Use |
|-------|---------|-------------|
| **16:9** | 1.778 | Video, hero images, YouTube thumbnails |
| 4:3 | 1.333 | Slides, product images |
| **3:2** | 1.5 | Photography, blog hero images |
| 2:1 | 2.0 | Wide hero banners |
| **1:1** | 1.0 | Avatars, social posts, product thumbnails |
| 3:4 | 0.75 | Portrait photos, mobile cards |
| 9:16 | 0.5625 | TikTok, Reels, Stories |
| 1.91:1 | 1.91 | OG/social preview (1200x630px) |

### Component-to-Ratio Mapping

| Component | Ratio |
|-----------|-------|
| Video embed | 16:9 |
| Hero (desktop) | 16:9 or 2:1 |
| Hero (mobile) | 4:3 or 1:1 |
| Blog card image | 16:9 or 3:2 |
| Product card | 1:1 or 4:3 |
| Avatar | 1:1 |
| Social preview (OG) | 1.91:1 (1200x630px) |

```css
/* Tailwind */
aspect-video   /* 16:9 */
aspect-square  /* 1:1 */
aspect-[4/3]   /* arbitrary */
```

---

## Quick-Reference Cheat Sheet

```
BUTTON HEIGHTS     XS:24  SM:32  MD:36-40  LG:44-48  XL:56
INPUT HEIGHTS      SM:32  MD:36-40  LG:44-48
NAVBAR HEIGHT      Mobile:44-56  Desktop:56-64
SIDEBAR WIDTH      Collapsed:48-64  Standard:240-260  Wide:280-320
MODAL WIDTHS       SM:384-480  MD:448-640  LG:720-800
AVATAR SIZES       XS:24  SM:32  MD:40  LG:48  XL:64  2XL:80-96
ICON SIZES         Inline:16  Standard:24  Feature:32  Hero:48-64
CARD PADDING       Compact:12  Standard:16-20  Spacious:24-32
PAGE CONTAINER     Standard:max-w-7xl(1280px)
READING WIDTH      max-w-prose(65ch~640px)
AUTH CARD WIDTH    max-w-md(448px)

BUTTON PADDING     PX = 2-3x PY.  PX/Height = 0.3-0.5
AVATAR FONT        = 0.45-0.5x diameter
ICON vs TEXT       Icon = 1.0-1.25x font-size

SECTION PADDING    Hero:py-20-40  Features:py-16-24  CTA:py-16-20
PAGE HORIZ PAD     Mobile:px-4  Tablet:px-6-8  Desktop:px-8-12

ASPECT RATIOS      Video:16/9  Photo:3/2  Avatar:1/1  Story:9/16
```
