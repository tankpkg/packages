# Layout and Spacing

Sources: Figma Auto Layout Documentation (2024), CSS Flexbox/Grid Specifications, 8-Point Grid System

Translate Figma layout properties to CSS with high fidelity by mapping the underlying Auto Layout engine to Flexbox and Grid primitives. Follow these precise mapping tables and logic rules to ensure pixel-perfect implementation of layouts, sizing, and responsive constraints.

## Auto Layout to CSS Flexbox Mapping

Figma Auto Layout is functionally equivalent to CSS Flexbox. Use the following mapping table to translate Auto Layout properties directly to CSS declarations. This table provides the foundation for all layout translations.

| Figma Property | Figma Value | CSS Property | CSS Value |
| :--- | :--- | :--- | :--- |
| layoutMode | HORIZONTAL | flex-direction | row |
| layoutMode | VERTICAL | flex-direction | column |
| layoutMode | GRID | display | grid |
| layoutMode | NONE | display | block / relative |
| primaryAxisAlignItems | MIN | justify-content | flex-start |
| primaryAxisAlignItems | CENTER | justify-content | center |
| primaryAxisAlignItems | MAX | justify-content | flex-end |
| primaryAxisAlignItems | SPACE_BETWEEN | justify-content | space-between |
| counterAxisAlignItems | MIN | align-items | flex-start |
| counterAxisAlignItems | CENTER | align-items | center |
| counterAxisAlignItems | MAX | align-items | flex-end |
| counterAxisAlignItems | BASELINE | align-items | baseline |
| layoutWrap | NO_WRAP | flex-wrap | nowrap |
| layoutWrap | WRAP | flex-wrap | wrap |
| itemSpacing | [Number]px | gap | [Number]px |

### Primary and Counter Axis Logic

In Flexbox, the primary axis depends on the flex-direction. Correctly identifying the axis is critical for proper alignment.
- If layoutMode is HORIZONTAL, primary axis is horizontal. Use `justify-content` for primary alignment and `align-items` for counter (vertical) alignment.
- If layoutMode is VERTICAL, primary axis is vertical. Use `justify-content` for primary alignment and `align-items` for counter (horizontal) alignment.

### Padding and Spacing Calculations

Auto Layout padding properties map directly to CSS padding. Use shorthand notation whenever possible to minimize code bloat.
- paddingLeft, paddingRight, paddingTop, paddingBottom map to their respective CSS properties.
- If paddingLeft equals paddingRight and paddingTop equals paddingBottom, use `padding: [top]px [left]px`.
- If all four values are identical, use `padding: [value]px`.
- In cases where padding is asymmetrical, prioritize the `padding: [top] [right] [bottom] [left]` shorthand.

### Gap and Item Spacing

The `itemSpacing` property in Figma is equivalent to the CSS `gap` property. 
- For HORIZONTAL layouts, this is effectively `column-gap`.
- For VERTICAL layouts, this is effectively `row-gap`.
- For GRID layouts, `itemSpacing` applies to both rows and columns unless specified otherwise in Figma's Advanced Layout settings.

## Sizing Modes and Flex Behavior

Figma uses specific sizing modes for width and height that dictate how a layer behaves relative to its content and its parent. These must be translated to the correct combinations of `width`, `height`, `flex-grow`, `flex-shrink`, and `flex-basis`.

### Horizontal Sizing (layoutSizingHorizontal)

- FIXED: The width is a specific pixel value. Map to `width: [N]px`. If the element is in a flex container, also set `flex-shrink: 0` to prevent compression.
- HUG: The container shrinks to fit its children. Map to `width: fit-content`. For flex items, this often means setting `flex-grow: 0` and `flex-shrink: 0`.
- FILL: The container stretches to fill available space. Map to `width: 100%` if the element is a block level, or `flex-grow: 1` if it is a flex item.

### Vertical Sizing (layoutSizingVertical)

- FIXED: The height is a specific pixel value. Map to `height: [N]px`.
- HUG: The container shrinks to fit its children. Map to `height: fit-content`.
- FILL: The container stretches to fill available space. Map to `height: 100%` or `flex-grow: 1` depending on the parent layout mode.

### Deep Dive: FILL Sizing in Flexbox

When a child is set to FILL along the primary axis of an Auto Layout parent:
- Set `flex-grow: 1`.
- Set `flex-shrink: 1`.
- Set `flex-basis: 0` (or `0%`) to ensure the element's initial size is not factored into the distribution of remaining space.
- Combined shorthand: `flex: 1 1 0`.

When a child is set to FILL along the counter axis:
- Set the dimension (width or height) to `100%`.
- Alternatively, if the parent uses `align-items: stretch` (which is the CSS default), the FILL child will naturally stretch to match the parent's size unless it has a fixed dimension.

### layoutGrow Property

- layoutGrow: 0 maps to `flex-grow: 0`. This is the default for FIXED and HUG items.
- layoutGrow: 1 maps to `flex-grow: 1`. This is required for FILL items in a horizontal or vertical container.

## Constraints and Positioning

Figma constraints define how layers behave when their parent frame is resized. Use these rules when a layer is not governed by Auto Layout or when it uses Absolute Position within an Auto Layout frame.

### Absolute Positioning Logic

Any layer in Figma with "Absolute Position" toggled on must be translated using `position: absolute`. Its parent container must have `position: relative` (unless it is already another positioned element).

### Horizontal Constraints Mapping

- LEFT: Fixes distance from the left. Map to `left: [N]px`.
- RIGHT: Fixes distance from the right. Map to `right: [N]px`.
- CENTER: Keeps layer centered. Map to `left: 50%` and `transform: translateX(-50%)`.
- LEFT_RIGHT: Stretches layer between edges. Map to `left: [L]px` and `right: [R]px`. This creates a responsive width that maintains margins.
- SCALE: Percentage-based positioning. Map to `left: [N]%` and `width: [M]%`.

### Vertical Constraints Mapping

- TOP: Fixes distance from the top. Map to `top: [N]px`.
- BOTTOM: Fixes distance from the bottom. Map to `bottom: [N]px`.
- CENTER: Keeps layer centered. Map to `top: 50%` and `transform: translateY(-50%)`.
- TOP_BOTTOM: Stretches layer between edges. Map to `top: [T]px` and `bottom: [B]px`.
- SCALE: Percentage-based positioning. Map to `top: [N]%` and `height: [M]%`.

## Min/Max Dimensions and Overflow

Figma provides explicit fields for minimum and maximum width/height. These are essential for preventing layout collapse or excessive expansion in responsive environments.

- minWidth maps to `min-width: [N]px`.
- maxWidth maps to `max-width: [N]px`.
- minHeight maps to `min-height: [N]px`.
- maxHeight maps to `max-height: [N]px`.

### Handling Overflow and Clipping

The "Clip Content" property on Figma frames determines if content outside the frame's bounds is visible.
- Clip Content: Checked → `overflow: hidden`.
- Clip Content: Unchecked → `overflow: visible`.
- For scrollable areas, use `overflow: auto` or `overflow-y: scroll` as appropriate for the component's intent.

## The 8-Point Grid and Spacing Systems

Systematic spacing ensures visual rhythm and developer efficiency. Use a consistent scale based on the project's design tokens.

### Common Spacing Scales

| Step | 4px Base | 8px Base | Tailwind Class (Approx) |
| :--- | :--- | :--- | :--- |
| 1 | 4px | 8px | space-1 / p-1 |
| 2 | 8px | 16px | space-2 / p-2 |
| 3 | 12px | 24px | space-3 / p-3 |
| 4 | 16px | 32px | space-4 / p-4 |
| 5 | 20px | 40px | space-5 / p-5 |
| 6 | 24px | 48px | space-6 / p-6 |
| 8 | 32px | 64px | space-8 / p-8 |
| 10 | 40px | 80px | space-10 / p-10 |
| 12 | 48px | 96px | space-12 / p-12 |

### Spacing Normalization

If a Figma design contains values outside the defined scale (e.g., a 7px margin), normalize it to the nearest scale step (8px) unless the value is intentional for a specific visual effect. Consistent use of a spacing scale reduces code complexity and improves maintainability.

## Advanced Layout Techniques

### CSS Grid for Complex Structures

When Auto Layout logic results in deep nesting (3+ levels), consider flattening the structure using CSS Grid. 
- Use `display: grid` for components with distinct rows and columns.
- Define columns with `grid-template-columns: repeat([Count], 1fr)`.
- Use `grid-column: span [N]` for elements that span multiple columns.
- Grid is the preferred method for cards, galleries, and complex dashboard layouts.

### Container Queries for Components

Container queries allow components to adapt to the size of their immediate parent container rather than the viewport. This is the modern standard for modular UI development.
- Parent: `container-type: inline-size`.
- Child: Use `@container (min-width: [N]px)` to trigger layout changes.
- This effectively replicates Figma's "responsive" behavior within various parent containers.

## Z-Index and Layer Stacking

The order of layers in Figma (bottom to top in the layer panel) determines their stacking order in the browser.

- Elements appearing later in the DOM will naturally appear on top of earlier elements.
- For overlapping elements (especially with absolute positioning), use the `z-index` property.
- Assign `z-index` values starting from 1 for the first overlapping layer.
- Avoid using excessively large `z-index` values (e.g., 9999) unless creating modals or tooltips.

## Visual Properties Related to Layout

### Border Radius Mapping

Figma's corner radius properties must be mapped accurately to ensure the correct shape.
- Single value: `border-radius: [N]px`.
- Multiple values: `border-radius: [TL]px [TR]px [BR]px [BL]px`.
- Use `50%` for circles where width and height are equal.

### Aspect Ratio Control

To maintain the proportions of images or media containers:
- Calculate the aspect ratio from Figma dimensions (Width / Height).
- Use `aspect-ratio: [Width] / [Height]`.
- This ensures the element scales predictably in responsive layouts without stretching.

### Border/Stroke Impact

Figma strokes can be positioned Inside, Outside, or Center.
- INSIDE (Default): The stroke is contained within the element's dimensions. Use `box-sizing: border-box`.
- OUTSIDE: The stroke adds to the element's footprint. CSS `outline` can simulate this, or add the stroke width to the element's margins.
- CENTER: The stroke straddles the boundary. This is rarely used in web development; convert to INSIDE for simplicity and precision.

## Layout Implementation Workflow

Follow this sequence to translate any Figma layout to code:

1. **Analyze Structure**: Identify parent Auto Layout frames and their `layoutMode`.
2. **Define Containers**: Create parent elements with `display: flex` and the correct `flex-direction`.
3. **Map Alignment**: Use `justify-content` and `align-items` based on primary and counter axis alignment.
4. **Set Spacing**: Apply the `gap` property for item spacing and `padding` for container margins.
5. **Determine Item Sizing**: Apply `width`, `height`, and `flex` properties based on HUG, FILL, or FIXED settings.
6. **Handle Absolute Position**: Identify elements that break the flow and apply `position: absolute` with constraint-based offsets.
7. **Apply Constraints**: For responsive frames, use min/max dimensions and percentage-based widths.
8. **Layer Stacking**: Verify the order of elements in the DOM matches the visual stack in Figma.
9. **Final Polishing**: Apply border-radius, overflow: hidden, and aspect-ratio as needed.
10. **Validation**: Compare a browser rendering with a 1:1 overlay of the Figma design.

## Common Layout Patterns

### Centered Hero Section

- Parent: `display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center`.
- Children: `max-width` applied to text elements to prevent line lengths from becoming too long.

### Split Screen / Two Column

- Parent: `display: flex; flex-direction: row`.
- Children: Two elements set to `flex: 1 1 0` or specific percentage widths (e.g., `width: 50%`).

### Responsive Card Grid

- Parent: `display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px`.
- This pattern replaces complex media queries with a fluid, self-organizing layout.

### Sticky Header

- Header: `position: sticky; top: 0; z-index: 100`.
- Parent: Ensure the container allows the sticky element to remain in the viewport.

### Full-Width Footer

- Footer: `width: 100%`.
- Inner Container: `max-width: [PageWidth]px; margin: 0 auto` to keep content aligned with the rest of the layout.

## Decision Tree: Flexbox vs. Grid

Choosing the right layout engine is essential for clean, maintainable code. Use this decision tree when translating Figma structures.

### Use Flexbox (Auto Layout) When:
- The layout is primarily one-dimensional (either a row or a column).
- You need content-driven sizing (elements grow/shrink based on their internal content).
- The alignment is relative to the items themselves (e.g., vertical centering of icons and text).
- You are implementing most standard Auto Layout components like buttons, navbars, and simple lists.

### Use CSS Grid When:
- The layout is two-dimensional (items must align in both rows and columns).
- You have a repeating set of items like a card gallery or image grid.
- You need precise control over the layout footprint regardless of content size.
- You want to reduce the depth of the DOM tree by avoiding nested flex containers.
- The design features overlapping elements that are easier to manage with grid areas.

## Best Practices for Responsive Typography Layout

Typography impact on layout must be handled with care to maintain the designer's intent across devices.

- **Line Length (Measure)**: Limit text container widths to 45-75 characters for readability. Use `max-width` tokens (e.g., `max-width: 65ch`).
- **Fluid Typography**: For headers, consider using `clamp()` to scale font size between a minimum and maximum based on viewport width (e.g., `font-size: clamp(1.5rem, 5vw, 3rem)`).
- **Line Height and Vertical Rhythm**: Use unitless line-heights (e.g., `1.5` instead of `24px`) to ensure the leading scales correctly when font sizes change.
- **Hyphenation and Wrapping**: Use `overflow-wrap: break-word` and `hyphens: auto` for narrow containers to prevent layout breaking on long words.

## Troubleshooting Layout Discrepancies

- **Element shrinking**: Check if `flex-shrink: 0` is missing on fixed-width items. Flex items shrink by default in CSS, unlike Figma's FIXED behavior.
- **Misalignment**: Re-verify the primary vs. counter axis logic for the current `flex-direction`. Remember that `justify-content` always targets the primary axis.
- **Unexpected Gaps**: Check for default browser margins/paddings on tags like `ul`, `p`, or `h1-h6`. These can interfere with Figma's clean-slate layout.
- **Overflow Issues**: Verify if `overflow: hidden` is applied to the correct parent frame. If a child has `FILL` but its parent is `HUG`, it may cause infinite expansion.
- **Stacking Errors**: Check if a parent has a transform or opacity property that creates a new stacking context, affecting `z-index` visibility.
- **Scaling issues**: Ensure `box-sizing: border-box` is applied globally to prevent borders and padding from adding to an element's calculated width/height.
- **Aspect Ratio failure**: Check if a fixed width or height is overriding the aspect-ratio property. Aspect ratio requires at least one dimension to be flexible (e.g., `width: 100%; height: auto`).
- **Container Query Support**: Ensure the browser environment supports `@container` or provide media query fallbacks for older environments.
- **Flex-basis confusion**: If `flex: 1` isn't working as expected, try explicit `flex: 1 1 0%` to reset the basis and ensure equal distribution.
