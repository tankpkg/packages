# Typography Fidelity

Sources: MDN Web Typography (2024), Figma Typography API Reference, Google Fonts Best Practices

To achieve pixel-perfect parity between Figma designs and browser implementations, developers must address the fundamental differences in how desktop design tools and web browsers rasterize type. Figma utilizes grayscale anti-aliasing which results in thinner, lighter glyph representation. Browsers typically default to subpixel rendering which adds weight and "fuzziness" to text. This reference provides the exact CSS properties, mapping tables, and formulas required to bridge this gap.

## Font Rendering and Smoothing

The most critical step in matching Figma typography is normalizing the font smoothing engine. Failure to apply smoothing results in text appearing significantly bolder in the browser than in Figma, even when using the same font weight.

### The Mandatory Smoothing Fix
Apply these properties globally to the root element (e.g., `html` or `body`) to force the browser to use grayscale anti-aliasing, matching Figma rendering engine.

```css
html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}
```

### Optical Weight Perception
Even with font-smoothing applied, there is an optical discrepancy. A Figma weight of 500 (Medium) often appears closer to a browser weight of 400 (Regular). When pixel-perfect match fails after applying smoothing, evaluate shifting weights down by one increment (e.g., Figma 600 → CSS 500).

### Subpixel Rendering Exceptions
While grayscale anti-aliasing matches Figma most closely, some high-contrast light-on-dark (dark mode) designs may require reverting to default smoothing if readability suffers on low-DPI screens. However, for 1:1 design parity validation, the grayscale fix remains mandatory.

## Font Weight Mapping

Figma uses descriptive names for font weights which must be mapped to their numeric CSS equivalents. Use the following table for standardized mapping across all typography tokens.

| Figma Weight Name | CSS font-weight |
|-------------------|-----------------|
| Thin              | 100             |
| Hairline          | 100             |
| Extra Light       | 200             |
| Ultra Light       | 200             |
| Light             | 300             |
| Regular           | 400             |
| Normal            | 400             |
| Medium            | 500             |
| Semi Bold         | 600             |
| Demi Bold         | 600             |
| Bold              | 700             |
| Extra Bold        | 800             |
| Ultra Bold        | 800             |
| Black             | 900             |
| Heavy             | 900             |

## Line Height Conversion

Figma provides line height in multiple formats. The implementation method in CSS differs depending on whether the value is a percentage, a fixed pixel value, or intrinsic.

### Unitless Line Height (Preferred)
Figma often displays line height as a percentage of the font size (e.g., 150%). In CSS, unitless values are preferred as they are relative to the element font-size and prevent inheritance issues.

**Formula:** `lineHeightPercentFontSize / 100`

- Figma: `lineHeightPercentFontSize: 150`
- CSS: `line-height: 1.5;`

### Fixed Pixel Line Height
If Figma specifies an exact pixel value, use it directly in CSS. Note that pixel-based line heights do not scale automatically if the font size is adjusted via media queries.

- Figma: `lineHeightPx: 24`
- CSS: `line-height: 24px;`

### Intrinsic Line Height
When Figma uses "Auto" for line height, it maps to the "normal" value in CSS. This value varies by font but generally falls between 1.1 and 1.3.

- Figma: `lineHeightUnit: "INTRINSIC_%"`
- CSS: `line-height: normal;`

## Letter Spacing (Tracking)

Letter spacing in Figma (Tracking) is expressed as a percentage of the font size. This must be converted to `em` units in CSS to maintain proportionality if the font size changes.

**Formula:** `trackingValue / 100`

- Figma: `letterSpacing: 2%`
- CSS: `letter-spacing: 0.02em;`

If the value is provided in pixels:

- Figma: `letterSpacing: 0.5px`
- CSS: `letter-spacing: 0.5px;`

### Negative Tracking
Negative tracking is common in Figma for large headlines to improve legibility. Ensure the negative sign is preserved in the CSS conversion.

- Figma: `-2%`
- CSS: `letter-spacing: -0.02em;`

## Text Case and Decoration Mapping

Figma text styles include casing and decoration properties that map directly to CSS properties.

### Text Case
| Figma textCase | CSS text-transform      |
|----------------|-------------------------|
| ORIGINAL       | none                    |
| UPPER          | uppercase               |
| LOWER          | lowercase               |
| TITLE          | capitalize              |
| SMALL_CAPS     | font-variant: small-caps|

### Text Decoration
| Figma textDecoration | CSS text-decoration |
|----------------------|----------------------|
| NONE                 | none                 |
| UNDERLINE            | underline            |
| STRIKETHROUGH        | line-through         |

Note: Figma does not support "overline" or "blink", which are available in CSS but rarely used in modern design.

## OpenType Features and Optical Sizing

Modern fonts often contain advanced OpenType features enabled in Figma that must be explicitly declared in CSS to maintain visual fidelity.

### font-feature-settings
Identify the `openTypeFlags` in the Figma node data and map them to the `font-feature-settings` property.

```css
.text-element {
  /* Enable standard ligatures and kerning */
  font-feature-settings: "liga" 1, "kern" 1;
}
```

Common flags:
- `liga`: Standard Ligatures (default in most browsers)
- `clig`: Contextual Ligatures
- `dlig`: Discretionary Ligatures (off by default)
- `tnum`: Tabular Figures (fixed-width numbers, essential for tables)
- `pnum`: Proportional Figures (varied-width numbers)
- `onum`: Oldstyle Figures (numbers with varying heights)
- `lnum`: Lining Figures (numbers with consistent height)
- `salt`: Stylistic Alternates
- `ss01`-`ss20`: Stylistic Sets (font-specific variations)

### font-optical-sizing
For variable fonts, Figma enables optical sizing by default. This adjusts the glyph shapes based on the font size to improve legibility.

```css
.text-element {
  font-optical-sizing: auto;
}
```

## Paragraph Spacing

Figma `paragraphSpacing` defines the gap between paragraphs within a single text node. In web development, this is implemented using margins on paragraph elements.

- Figma: `paragraphSpacing: 16`
- CSS: `p + p { margin-top: 16px; }` or `p { margin-bottom: 16px; }`

### Vertical Rhythm
To maintain the vertical rhythm defined in Figma, ensure that `paragraphSpacing` is consistent with the global spacing scale used in the design system.

## Text Auto-Resize and Dimensions

Figma text nodes have different resize behaviors that dictate how the container behaves relative to its content.

### Width and Height Auto
- Figma: `textAutoResize: "WIDTH_AND_HEIGHT"`
- CSS: `width: fit-content; height: auto; display: inline-block;`

### Height Auto (Fixed Width)
- Figma: `textAutoResize: "HEIGHT"`
- CSS: `width: [fixed_px]; height: auto; display: block;`

### Fixed Size
- Figma: `textAutoResize: "NONE"`
- CSS: `width: [fixed_px]; height: [fixed_px]; overflow: hidden; display: block;`

## Text Truncation and Overflow

Figma provides truncation options that must be handled with specific CSS patterns.

### Single Line Truncation
- Figma: `textTruncation: "ENDING"`
- CSS:
```css
.truncate-single {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block; /* Required for width to be respected */
}
```

### Multi-Line Truncation
For blocks of text, use the `-webkit-line-clamp` utility. This is a non-standard but widely supported property.

```css
.truncate-multi {
  display: -webkit-box;
  -webkit-line-clamp: 3; /* Matches Figma's line limit */
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

## Google Fonts Loading and Performance

When using Google Fonts, adhere to these best practices to ensure fast rendering and prevent layout shifts (CLS).

### Preconnect
Add preconnect hints to the HTML `<head>` to establish early connections to the font domains. This saves approximately 100-300ms in font load time.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

### Font Display
Always use `font-display: swap` in the font-face declaration or the Google Fonts URL parameter to ensure text remains visible during loading. This prevents the "Flash of Invisible Text" (FOIT).

URL: `https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap`

## Variable Fonts Implementation

Variable fonts allow for granular control over axes such as weight, width, and slant using `font-variation-settings`.

### Controlling Axes
Figma allows fine-tuning axes which must be mapped to CSS. Unlike standard font weights (100-900), variable fonts can use any integer within the font's supported range.

```css
.variable-text {
  font-family: "Inter Variable", sans-serif;
  /* wght = weight, wdth = width, slnt = slant, ital = italic */
  font-variation-settings: "wght" 542, "wdth" 100, "slnt" -10;
}
```

## Responsive Typography and Fluid Sizing

Figma designs often provide static font sizes for Mobile, Tablet, and Desktop. Use the `clamp()` function to create fluid typography that interpolates between these sizes without jarring breakpoints.

### Fluid Font Size Formula
```css
font-size: clamp([min_size], [preferred_value], [max_size]);
```

**Example:**
- Mobile: 16px
- Desktop: 24px
- Viewport range: 320px to 1280px

```css
h1 {
  font-size: clamp(1rem, 0.733rem + 1.33vw, 1.5rem);
}
```

## Web Font Loading Strategies

To achieve visual stability, manage how fonts transition from fallback to primary.

### Flash of Unstyled Text (FOUT)
Using `font-display: swap` causes FOUT. To minimize the visual impact, use a fallback font that closely matches the primary font's x-height and width.

```css
@font-face {
  font-family: 'PrimaryFont';
  src: url('primary-font.woff2') format('woff2');
  font-display: swap;
}

body {
  font-family: 'PrimaryFont', 'FallbackFont', sans-serif;
}
```

### CSS Font Loading API
For advanced scenarios, use the Font Loading API to detect when a font has loaded and apply a class to the body.

```javascript
document.fonts.load("1em PrimaryFont").then(() => {
  document.documentElement.classList.add("fonts-loaded");
});
```

## Typography and Accessibility

Pixel perfection must not come at the cost of accessibility.

### Relative Units
Always convert Figma pixel sizes to `rem` units for web implementation to respect user browser font size settings.

**Formula:** `fontSizePx / 16` (assuming default browser base)

- Figma: 32px
- CSS: 2rem

### Contrast Ratio
Verify that the text color defined in Figma meets WCAG 2.1 AA standards (4.5:1 for normal text, 3:1 for large text). Use the design metadata to flags low-contrast colors during code generation.

## Common Font Stacks and Fallbacks

Always provide a robust fallback stack to maintain layout integrity if the primary font fails to load.

### System Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
```

### Popular Google Font Fallbacks
- Inter: `Inter, system-ui, -apple-system, sans-serif;`
- Roboto: `Roboto, "Helvetica Neue", Arial, sans-serif;`
- Playfair Display: `"Playfair Display", Georgia, "Times New Roman", serif;`
- Montserrat: `Montserrat, "Trebuchet MS", sans-serif;`

## Vertical Rhythm and Baseline Grids

Figma designs often use an 8px or 4px baseline grid. To maintain this rhythm in CSS, ensure all typography spacing (line-height, margins, padding) are multiples of the grid base.

```css
:root {
  --grid-base: 4px;
  --spacing-4: calc(var(--grid-base) * 4); /* 16px */
  --spacing-6: calc(var(--grid-base) * 6); /* 24px */
}

h2 {
  line-height: var(--spacing-6);
  margin-bottom: var(--spacing-4);
}
```

## Conversion Formula Summary

Use these formulas when automating the translation of Figma node data to CSS tokens.

1. **Line Height (Ratio):** `lineHeightPx / fontSize`
2. **Letter Spacing (em):** `letterSpacingPx / fontSize`
3. **Paragraph Spacing (rem):** `paragraphSpacingPx / 16`
4. **Font Size (rem):** `fontSizePx / 16`
5. **Tracking (em):** `trackingPercent / 100`

## Checklist for 1:1 Parity

Before marking a typography implementation as complete, verify:
- [ ] Font smoothing (`-webkit-font-smoothing: antialiased`) is applied to the root element.
- [ ] Font weights match the numeric mapping table precisely.
- [ ] Line height is unitless where possible to ensure proper scaling.
- [ ] Letter spacing is converted to `em` units for fluid proportionality.
- [ ] Negative tracking values are correctly preserved.
- [ ] OpenType features (ligatures, kerning, tabular figures) are enabled via `font-feature-settings`.
- [ ] Optical sizing is set to `auto` for variable fonts.
- [ ] Truncation behavior (single vs multi-line) matches the design container constraints.
- [ ] Relative units (`rem`) are used for font sizes and spacing.
- [ ] Fallback fonts are provided to minimize layout shift during loading.
- [ ] Contrast ratios meet minimum accessibility requirements.

Failure to follow these rules will result in visual discrepancies that appear as "incorrect weight" or "shifted layout" during visual regression testing. Precise adherence to font-smoothing and unitless line-heights resolves 90% of typography fidelity issues encountered when moving from Figma to code. Every pixel deviation in typography accumulates across a page, eventually breaking the intended visual hierarchy.
