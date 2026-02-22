# Colors and Effects

Sources: Figma Paint/Effect API (2024), CSS Color Level 4 Specification, MDN Visual Effects Reference

## Color Format Conversion

### RGBA Transformation
Figma represents colors using a floating-point system from 0 to 1 for each channel (R, G, B, A). CSS requires integer values from 0 to 255 for R, G, and B.

To convert Figma RGBA to CSS:
1. Multiply the Figma R, G, and B values by 255.
2. Round the result to the nearest integer.
3. Keep the Alpha (A) value as a floating-point number between 0 and 1.

Example:
Figma: `{r: 0.48, g: 0.38, b: 0.94, a: 1.0}`
Calculation:
R: 0.48 * 255 = 122.4 → 122
G: 0.38 * 255 = 96.9 → 97
B: 0.94 * 255 = 239.7 → 240
CSS: `rgba(122, 97, 240, 1)`

### Hex with Alpha
When Figma provides a hex string and a separate opacity value, convert to CSS Hex Alpha (#RRGGBBAA) or `rgba()`.

Mapping:
- Hex #FFFFFF + 50% opacity → `#FFFFFF80` (where 80 is 0.5 * 255 in hex)
- Hex #000000 + 10% opacity → `rgba(0, 0, 0, 0.1)`

### Selection Logic
- Use **Hex** for solid colors without transparency.
- Use **RGBA** when alpha is required and high compatibility is needed.
- Use **HSL** when color manipulation (lightness/saturation shifts) is required in code.
- Use **OKLCH** for modern projects requiring perceptually uniform color gradients and wide gamuts (P3).

## Gradient Translation

### Linear Gradients
Figma and CSS handle gradient angles differently. Figma angles are based on the unit circle where 0° is to the right, while CSS `linear-gradient` 0° is to the top.

Formula: `CSS_Angle = (Figma_Angle + 90) % 360`

| Figma Angle | CSS Direction | CSS Angle |
|-------------|---------------|-----------|
| 0° (Right)  | to right      | 90deg     |
| 90° (Down)  | to bottom     | 180deg    |
| 180° (Left) | to left       | 270deg    |
| 270° (Up)   | to top        | 0deg      |

Gradient stops translation:
Figma stop position (0 to 1) must be converted to percentage (0% to 100%).

### Radial Gradients
Translate `RADIAL_GRADIENT` to `radial-gradient()`.
- Identify the focal point from Figma's `gradientHandlePositions`.
- CSS syntax: `radial-gradient(circle at center, color1 0%, color2 100%)`.

### Angular (Conic) Gradients
Translate `ANGULAR_GRADIENT` to `conic-gradient()`.
- Normalize the start angle.
- Syntax: `conic-gradient(from 0deg at 50% 50%, color1, color2)`.

### Diamond Gradients
CSS has no native `diamond-gradient`. Approximate using a `conic-gradient` rotated 45 degrees or a complex `radial-gradient` with specific stops. For pixel-perfect requirements, export as an SVG or high-resolution PNG.

## Shadows

### Box Shadows
Figma's `DROP_SHADOW` and `INNER_SHADOW` map directly to the CSS `box-shadow` property.

Property Mapping:
- `color`: Map RGBA channels to `rgba()`.
- `offset.x`: `offsetX`.
- `offset.y`: `offsetY`.
- `radius`: `blurRadius`.
- `spread`: `spreadRadius`.

Syntax:
`box-shadow: <offsetX> <offsetY> <blurRadius> <spreadRadius> <color>;`

Inner Shadows:
Add the `inset` keyword at the start of the value.
`box-shadow: inset <offsetX> <offsetY> <blurRadius> <spreadRadius> <color>;`

### Multiple Shadows
Figma allows stacking multiple effects. In CSS, stack them using a comma-separated list.
**Order is critical**: The first shadow in the CSS list is the top-most visual layer. This matches Figma's layer order from top to bottom.

Example:
```css
box-shadow:
  0 4px 6px -1px rgba(0, 0, 0, 0.1),
  0 2px 4px -1px rgba(0, 0, 0, 0.06);
```

### Text Shadows
Figma applied shadows on text layers should use `text-shadow`.
Note: `text-shadow` does **not** support `spread`. If Figma includes a spread value on text shadows, ignore it or use a SVG filter for accuracy.

Syntax:
`text-shadow: <offsetX> <offsetY> <blurRadius> <color>;`

## Blur Effects

### Layer Blur
Figma `LAYER_BLUR` applies to the element itself.
**Conversion Rule**: CSS `blur()` uses the radius, while Figma uses the diameter.
**Formula**: `CSS_Blur = Figma_Radius / 2`

CSS Property: `filter: blur(Npx);`

### Background Blur
Figma `BACKGROUND_BLUR` applies to the content behind the element.
**Formula**: `CSS_Blur = Figma_Radius / 2`

CSS Property: `backdrop-filter: blur(Npx);`
Required Companion: Elements with background blur usually require a semi-transparent background color (e.g., `background: rgba(255, 255, 255, 0.3)`) to make the effect visible.

## Opacity Stacking

### Element vs Fill Opacity
- **Layer Opacity**: Applies to the entire element and its children. Use `opacity: 0.5;`.
- **Fill Opacity**: Applies only to the background color. Use alpha channel in the color definition (`rgba(..., 0.5)`).

### Multiplicative Logic
When both layer and fill opacity are present, the visual result is multiplicative.
`Visual_Alpha = Layer_Opacity * Fill_Opacity`

When translating to code, prefer merging opacity into the color's alpha channel if the element doesn't have children that should also be transparent. This avoids creating new stacking contexts.

## Blend Modes

Figma `blendMode` must be mapped to the `mix-blend-mode` CSS property (or `background-blend-mode` if applying to multiple background layers).

| Figma Mode    | CSS mix-blend-mode |
|---------------|-------------------|
| PASS_THROUGH  | normal            |
| NORMAL        | normal            |
| DARKEN        | darken            |
| MULTIPLY      | multiply          |
| COLOR_BURN    | color-burn        |
| LIGHTEN       | lighten           |
| SCREEN        | screen            |
| COLOR_DODGE   | color-dodge       |
| OVERLAY       | overlay           |
| SOFT_LIGHT    | soft-light        |
| HARD_LIGHT    | hard-light        |
| DIFFERENCE    | difference        |
| EXCLUSION     | exclusion         |
| HUE           | hue               |
| SATURATION    | saturation        |
| COLOR         | color             |
| LUMINOSITY    | luminosity        |

## Strokes and Borders

### Weight and Width
Figma `strokeWeight` maps directly to `border-width`.

### Stroke Alignment
Figma supports three alignment modes. CSS `border` only supports one (equivalent to center-aligned, but affecting the box model as if inside-aligned when `box-sizing: border-box` is used).

1. **INSIDE**: Use `box-sizing: border-box`. The border is drawn inside the defined width/height.
2. **OUTSIDE**: Use `outline` or `box-shadow` (with 0 blur and a spread equal to stroke weight). Standard CSS borders increase the element's visual size.
3. **CENTER**: Standard CSS border behavior. The border straddles the edge of the element.

### Dash Patterns
Figma's `dashPattern` array maps to `border-style: dashed`.
For exact dash/gap control, use `border-image` or an SVG stroke with `stroke-dasharray`.

## Solid and Image Fills

### Solid Fills
Translate to `background-color`. If multiple fills exist, only the top-most visible fill is usually necessary unless blend modes are applied.

### Image Fills
Map Figma `imageRef` or URL to CSS `background-image`.
- **FILL**: Use `background-size: cover; background-position: center;`
- **FIT**: Use `background-size: contain; background-repeat: no-repeat; background-position: center;`
- **TILE**: Use `background-repeat: repeat;`
- **CROP**: Use `background-size` and `background-position` percentage offsets.

## CSS Custom Properties (Tokens)

Always prefer CSS variables for colors and effects to ensure themeability.

### Naming Conventions
- **Semantic**: `--color-action-primary`, `--shadow-modal`
- **Primitive**: `--color-blue-600`, `--effect-blur-md`

### Implementation
Define variables in `:root` and use them in component styles.

```css
:root {
  --color-primary: #7C3AED;
  --color-primary-alpha-10: rgba(124, 58, 237, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.card {
  background-color: var(--color-primary);
  box-shadow: var(--shadow-lg);
}
```

## Advanced Techniques

### Gradient Text

CSS `color` only accepts solid values. Apply gradients to text using `background-clip`:

```css
.gradient-text {
  background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent; /* fallback */
}
```

Shadows on gradient-text elements render incorrectly. Wrap the text in a container and apply `text-shadow` or `filter: drop-shadow()` on the wrapper instead.

### Per-Stop Opacity in Gradients

Figma gradient stops carry individual alpha values. The paint itself also has an `opacity` property. CSS gradients have no global opacity, so bake it into each stop:

```
Final_Stop_Alpha = Paint.opacity * Stop.color.a
```

Example: Paint opacity 0.8, stop color `{r: 1, g: 0, b: 0, a: 0.5}` → CSS stop `rgba(255, 0, 0, 0.4)`.

### Elliptical Radial Gradients

Figma uses a transform matrix for non-uniform radial gradients. Approximate in CSS:

```css
background: radial-gradient(ellipse 80% 50% at 30% 40%, #7C3AED 0%, transparent 100%);
```

Extract the ellipse dimensions from the `gradientTransform` matrix. If the matrix includes rotation, use a rotated pseudo-element.

### Gradient Strokes

CSS `border` does not support gradients. Simulate with `border-image`:

```css
.gradient-border {
  border: 2px solid transparent;
  border-image: linear-gradient(90deg, #7C3AED, #EC4899) 1;
}
```

For rounded corners with gradient borders, use a pseudo-element approach:

```css
.gradient-border-rounded {
  position: relative;
  border-radius: 12px;
}
.gradient-border-rounded::before {
  content: "";
  position: absolute;
  inset: -2px;
  border-radius: 14px;
  background: linear-gradient(90deg, #7C3AED, #EC4899);
  z-index: -1;
}
```

### SVG Filter Fallbacks

When CSS cannot replicate a Figma effect (diamond gradients, complex blurs with clipping), extract as SVG filter:

```html
<svg width="0" height="0">
  <filter id="custom-blur">
    <feGaussianBlur in="SourceGraphic" stdDeviation="4 8" />
  </filter>
</svg>
```

```css
.complex-blur {
  filter: url(#custom-blur);
}
```

Use `feGaussianBlur` with separate X/Y deviations for directional blurs that CSS `blur()` cannot express.

### Color Space Considerations

Figma defaults to sRGB but some designs use Display P3. When targeting wide gamut:

```css
.wide-gamut {
  color: color(display-p3 0.48 0.38 0.94);
  background: oklch(65% 0.25 290);
}
```

Use `@supports (color: color(display-p3 0 0 0))` for progressive enhancement with sRGB fallbacks.

### Dynamic Color Adjustments

Map Figma tint/shade token operations to CSS `color-mix()`:

```css
.darkened {
  background: color-mix(in srgb, var(--color-primary), black 20%);
}
.lightened {
  background: color-mix(in srgb, var(--color-primary), white 30%);
}
```

### Performance Considerations

- Large `blur()` and `backdrop-filter` values are GPU-intensive. Limit blur radius to 40px when possible.
- `will-change: transform` or `transform: translateZ(0)` can create new stacking contexts that affect blur rendering.
- `backdrop-filter` requires the element to have a semi-transparent or transparent background.
- Elements with `filter: blur()` may clip overflowing shadows. Set `overflow: visible` or add padding.

## Implementation Checklist

1. Extract all `fills` and `effects` arrays from the Figma node JSON.
2. Convert RGBA channels: multiply R, G, B by 255, round to integer, keep A as float.
3. Apply gradient angle offset: `CSS_Angle = (Figma_Angle + 90) % 360`.
4. Divide Figma blur values by 2 for CSS `filter: blur()` and `backdrop-filter: blur()`.
5. Stack multiple shadows as comma-separated values, matching Figma top-to-bottom order.
6. Add `inset` keyword for inner shadows.
7. Use `text-shadow` for text layers (no spread support — ignore Figma spread on text).
8. Map blend modes using the translation table. Apply `mix-blend-mode` or `background-blend-mode`.
9. Handle stroke alignment: inside → `border-box`, outside → `outline` or `box-shadow`, center → standard `border`.
10. Compute multiplicative opacity: `Visual_Alpha = Layer_Opacity * Fill_Opacity`.
11. Bake per-stop opacity into gradient color stops.
12. Map image fills: FILL → `cover`, FIT → `contain`, TILE → `repeat`, CROP → manual positioning.
13. Replace all hardcoded color values with CSS custom properties.
14. Validate rendered output against the Figma screenshot.
