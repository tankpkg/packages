# Visual Verification

Sources: Playwright Visual Comparison API (2024), Percy Visual Testing Documentation, Chromatic CI/CD Patterns

Code-only validation is insufficient. Even when CSS properties match Figma values numerically, rendering engine differences, browser defaults, and CSS inheritance cause visual drift. If a side-by-side pixel comparison shows any discrepancy, the implementation is incomplete. Always verify visually.

"Close enough" is unacceptable. Replicate every pixel, shadow, and spacing value with absolute precision. Verify every component using the side-by-side comparison workflow below.

### Side-by-Side Comparison Workflow

The side-by-side comparison workflow is the primary mechanism for ensuring fidelity. This workflow consists of four repeating steps that must be performed for every component and page section. This iterative process ensures that errors are caught early and fixed before they propagate through the layout.

#### Step 1: Capture the Source of Truth
Take a Figma screenshot via the get_screenshot tool at the specific node level. It is crucial to capture the node in its "rest" state and any interactive states defined in the design file. If the node is part of a larger layout, capture both the isolated component and its context to verify alignment and rhythm. Ensure the Figma zoom level is set to 100% to avoid scaling artifacts that could skew the comparison. 

When capturing the source of truth, pay close attention to the layers. Sometimes a designer uses hidden layers or overlay masks that affect the final visual output but aren't immediately obvious in the code properties. The screenshot captures the final flattened result of all these design decisions. If you are verifying a component with multiple variants (e.g., primary button, secondary button, warning states, loading states), capture each variant as a separate reference image to ensure comprehensive coverage. In complex components, you may also need to capture "hover" and "pressed" states if they are explicitly designed as separate frames or variants in Figma.

#### Step 2: Capture the Implementation
Take a browser screenshot using Playwright or the Playwriter MCP tool. You must ensure the viewport matches the Figma frame dimensions exactly. For a desktop component designed at 1440px width, the browser viewport must be exactly 1440px wide. Use the `screenshotWithAccessibilityLabels` tool in the Playwriter MCP to capture the visual state while simultaneously verifying that the DOM structure is accessible and interactive elements are reachable.

This step requires a clean browser environment. Ensure that no browser chrome, scrollbars, or extension UI elements are visible in the capture. The screenshot should be a pure representation of the HTML and CSS. If the component has a specific height in Figma, ensure the browser screenshot is clipped to that exact height. For components with scrollable areas, capture both the visible area and the full height to verify that internal scrolling doesn't introduce unexpected padding or border clipping. Using a headless browser is often preferred for consistency, but a headed browser can be useful for manual spot checks during the development phase.

#### Step 3: Perform Comparison
Perform a pixel-by-pixel automated comparison using tools like Playwright’s `toHaveScreenshot` or manual visual inspection. For manual inspection, use an overlay technique: place the Figma screenshot at 50% opacity over the browser render using a browser extension or custom CSS. Look for "ghosting" effects—if text or borders appear doubled or blurry, they are out of alignment. Even a 0.5px shift can indicate a box-model error that will compound as the layout grows.

Automated tools like `pixelmatch` are excellent for identifying changes, but they can be sensitive to anti-aliasing. A human eye is often better at identifying if a 1px shift is a critical error or a rendering quirk. However, for large-scale pages, the automated diff image (often highlighting changes in red) is an essential diagnostic tool for spotting global alignment issues. When analyzing a diff, look for blocks of color—solid red blocks usually indicate a missing element or a significant size difference, while thin red outlines often point to 1-2px shifts in padding or margins. Darker regions in the diff usually mean color mismatches, while offset shapes mean alignment issues.

#### Step 4: Iterative Refinement and Correction
Identify discrepancies, adjust the code, and repeat the process. Common adjustments include changing margin to padding, switching from `flex-basis` to `width`, or adding font-smoothing. Do not stop until the implementation and design are indistinguishable in the overlay. Every iteration should reduce the "delta" between the two images.

Keep a log of the changes made during each iteration. This helps in identifying recurring patterns and improving the initial code generation phase in future tasks. If a fix for one component breaks another, it indicates a lack of component isolation in the CSS architecture. This is a common issue with global styles or leaky selectors, and it should be addressed by refining the CSS scoping or using CSS Modules/Tailwind utility classes more strictly. Ensure that your fixes are based on systematic logic rather than "quick fixes" that might introduce technical debt.

### Tooling and Configuration

Playwright provides a built-in visual comparison API that uses the pixelmatch library. Use this for automated regression testing and initial validation. The configuration should be strict but allow for minor anti-aliasing differences that are inherent to browser rendering engines.

```typescript
import { test, expect } from '@playwright/test';

test('verify component fidelity', async ({ page }) => {
  await page.goto('http://localhost:3000/component-preview');
  
  // Set the viewport to match the Figma frame exactly
  // This is the most critical part of visual testing setup
  await page.setViewportSize({ width: 1440, height: 900 });
  
  // Wait for stability across all layers
  await page.waitForLoadState('networkidle');
  await page.evaluateHandle(() => document.fonts.ready);
  
  // Global CSS to normalize rendering for screenshots
  // Transitions and animations are non-deterministic and must be killed
  await page.addStyleTag({
    content: `
      * {
        transition: none !important;
        animation: none !important;
        caret-color: transparent !important;
      }
    `
  });

  // Perform the visual comparison with tight thresholds
  await expect(page.locator('#target-component')).toHaveScreenshot('reference.png', {
    maxDiffPixels: 100,      // Total allowed pixel difference (cumulative)
    threshold: 0.1,          // Sensitivity to color variation (0.1 = high sensitivity)
    animations: 'disabled',  // Stop CSS animations from triggering mid-shot
    scale: 'css'             // Use CSS pixels to ensure consistency across devices
  });
});
```

When using the Playwriter MCP for manual or agent-led browser verification, leverage the `screenshotWithAccessibilityLabels` tool. This tool captures the visual state and generates a metadata map of interactive elements. This is vital for verifying that the "visual" button is actually a "functional" button with the correct hit area and labels.

### Detailed Fidelity Checklist

The fidelity checklist is your mandatory roadmap for inspection. Evaluate every component against these expanded criteria:

#### 1. Layout and Spacing
- **Gaps and Gutters:** Check that the `gap` property in Flexbox or Grid matches the Auto Layout 'item spacing' in Figma.
- **Padding vs. Margin:** Verify that internal whitespace is handled by padding and external whitespace by margins to prevent layout collapse.
- **Alignment:** Use the browser's "Inspect Element" ruler to verify that the horizontal and vertical centers of components match Figma.
- **Sizing Policy:** Ensure that 'Fixed' sizing in Figma becomes fixed pixels, 'Hug' becomes `fit-content` or auto-sizing, and 'Fill' becomes `flex: 1` or `width: 100%`.
- **Z-Index:** Verify that overlapping elements (modals, tooltips, dropdowns) have the correct stacking order.
- **Box-Sizing:** Ensure `box-sizing: border-box` is applied globally to prevent border widths from expanding element sizes beyond Figma specs.

#### 2. Typography and Text Rendering
- **Font Weight Optical Match:** Figma’s rendering of font weights (e.g., Medium 500) can appear thicker than the browser's default rendering.
- **Line Height:** Figma often uses percentage-based line-height. In CSS, use unitless values (e.g., 150% in Figma = 1.5 in CSS) for better inheritance.
- **Letter Spacing:** Convert Figma tracking (percentage) to `em` or `px` in CSS. Formula: `(Tracking % / 100) * FontSize = letter-spacing in px`.
- **Text Case:** Ensure `text-transform: uppercase` or `capitalize` is used rather than hardcoding the case in the HTML.
- **Antialiasing:** Browser text can look jagged compared to Figma. Always apply font-smoothing CSS.
- **Font Feature Settings:** If using high-end typefaces, enable ligatures and kerning with `font-feature-settings: 'liga' 1, 'kern' 1`.

#### 3. Colors, Gradients, and Opacity
- **Color Accuracy:** Use the eye-dropper tool in the browser to verify the computed hex code.
- **Opacity Stacking:** If an element has 50% opacity in Figma and sits on a 50% opacity background, ensure the CSS reflects this layered transparency.
- **Gradients:** Figma linear gradients often need an angle adjustment. CSS gradients start from the bottom by default, while Figma starts from the top.
- **Color Space:** Be aware that P3 color profiles in Figma might look desaturated in browsers limited to sRGB.
- **Variable Use:** Verify that colors are being pulled from the designated design system tokens/variables rather than being hardcoded.

#### 4. Effects, Shadows, and Borders
- **Shadows:** Figma 'Blur' is a diameter. CSS `box-shadow` blur-radius is a radius. Always divide the Figma blur value by 2.
- **Shadow Spread:** Ensure the spread value (the 4th value in `box-shadow`) is included if present in Figma.
- **Border Alignment:** Figma allows strokes to be 'Inside', 'Outside', or 'Center'. CSS borders are always 'Inside' the box model for `border-box`.
- **Border Radius:** Check individual corner radii. Figma can have independent values for each corner (e.g., `8px 8px 0 0`).
- **Multiple Shadows:** Figma supports multiple drop shadows on a single layer; ensure these are translated to a comma-separated list in CSS.

#### 5. Assets, Icons, and Media
- **Icon Fidelity:** SVGs must be exported without unnecessary wrappers that could add phantom padding.
- **Image Resolution:** Verify that `srcset` is used to provide @2x and @3x versions of images for high-DPI screens.
- **Vector Paths:** Check that complex vector shapes haven't been distorted during export or implementation.
- **Object-Fit:** For images that must fill a specific area, ensure `object-fit: cover` or `contain` is used to match Figma's cropping intent.

### Common Failure Patterns and Technical Fixes

#### Pattern: Text weight mismatch
Text looks heavier in the browser than in the Figma mockup, even with the correct `font-weight`.
Fix: Apply the following CSS properties to the root or text elements:
```css
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
text-rendering: optimizeLegibility;
```
This forces the browser to use a more precise rendering method that closely matches Figma’s Quartz or ClearType rendering.

#### Pattern: Spacing discrepancies
Spacing between items is off by 1-4 pixels, leading to a "loose" or "tight" feel.
Fix: Check for default browser margins on `p`, `h1-h6`, and `ul` elements and reset them to `margin: 0`. Verify that `line-height` isn't adding extra vertical space that isn't present in Figma's bounded text boxes.

#### Pattern: Inaccurate Shadow Rendering
Shadows look too harsh, too large, or are missing their "glow" effect.
Fix: Divide the Figma blur by 2. For multiple shadows, stack them in the `box-shadow` property using commas. Maintain the exact order from Figma (top-most shadow in Figma should be first in the CSS list).

#### Pattern: Incorrect Gradient Angles
The gradient flows in the wrong direction (e.g., horizontally instead of vertically).
Fix: Add 90 degrees to the Figma value. If Figma says 0°, use `90deg` in CSS. Alternatively, use keywords like `to right` or `to bottom` to match the visual direction observed in Figma.

#### Pattern: Border-Radius clipping issues
Borders or backgrounds are bleeding out of rounded corners.
Fix: Add `overflow: hidden` to containers with a `border-radius`. If using an 'Outside' stroke in Figma, simulate it with `outline` or an `inset box-shadow` to avoid affecting the box-model dimensions.

#### Pattern: Image distortion or blur
Images look stretched or lack detail on high-density displays.
Fix: Use `image-set` or `srcset` for responsive images. Ensure the aspect ratio matches Figma exactly using the `aspect-ratio` CSS property or explicit width/height values.

### Scenario-Based Verification Cases

#### Scenario: Verifying a Complex Data Table
Data tables are prone to misalignments because of cell content variability.
1. Capture the Figma table at its most complex state (longest cell content, all status icons visible).
2. Implementation must use `table-layout: fixed` if Figma specifies rigid column widths.
3. Check cell padding: Figma text boxes inside cells often have implicit padding. Match this with CSS cell padding.
4. Vertical alignment: Figma nodes inside a frame are often centered. Use `vertical-align: middle` in CSS to match.
5. Row borders: Verify if borders are on the `tr` or `td` and ensure they don't double up at intersections.
6. Hover states: Take a separate screenshot with a row in the hover state to verify background color change and transition speed.

#### Scenario: Verifying a Responsive Hero Section
Hero sections often use complex Auto Layout combinations (e.g., center-aligned on mobile, left-aligned on desktop).
1. Capture Figma frames for each breakpoint (375px, 768px, 1440px).
2. Implementation must use media queries or container queries to trigger layout shifts.
3. Check font-size scaling: Designers often scale down headings on mobile. Use `clamp()` or media queries to match.
4. Background positioning: If the hero has a background image, verify that the `background-position` (e.g., `center`, `top right`) matches the design's focal point.
5. Content constraints: Verify that text containers have the correct `max-width` to prevent line-lengths from becoming unreadable on ultra-wide screens.

#### Scenario: Verifying a Navigation Menu with Dropdowns
Interactive menus require verifying states that are often ephemeral.
1. Capture the "closed" and "open" states in Figma.
2. In the browser, trigger the dropdown (e.g., via `hover` or `click`) and capture the state.
3. Verify the dropdown positioning relative to the trigger. Figma often uses absolute positioning for dropdown menus; ensure the CSS `top` and `left` match the node offsets.
4. Check the shadow and border-radius of the dropdown menu container.
5. Verify the hover states of individual menu items within the dropdown.

### Step-by-Step Tutorial: Verifying a Card Component

To solidify the process, follow this walkthrough for a standard UI card:
1. **Initial Code Review:** Ensure the card uses `flex-col` and matches Figma's Auto Layout direction.
2. **Visual Snapshot:** Take a `get_screenshot` of the card node.
3. **Browser Render:** Navigate to the component in Playwright and capture a screenshot at the exact same width as the Figma node.
4. **Overlay Test:** Use a tool like "PerfectPixel" to overlay the images. Notice the title is 2px too high.
5. **Root Cause Analysis:** Inspect the title element. You find that Figma's text box has a `line-height` that adds 1px of whitespace at the top, which isn't present in your CSS.
6. **Correction:** Adjust the `margin-top` or `padding-top` of the title, or refine the `line-height` value to match the bounding box optically.
7. **Re-Verification:** Capture a new browser screenshot and confirm the overlay ghosting is gone.

### Debugging Sub-Pixel Rendering and Anti-Aliasing

Sub-pixel rendering can cause 0.5px differences that trigger false negatives in visual tests.
- **Fractional Dimensions:** If a container width is 33.33%, the actual pixel width might vary by browser. Prefer exact pixel values if the design specifies them.
- **Font Kerning:** Different browsers use different kerning algorithms. If text length differs by 1-2px, check `font-kerning: normal`.
- **Image Smoothing:** Use `image-rendering: -webkit-optimize-contrast` to ensure that icons and crisp vectors don't get softened by the browser's interpolation.
- **Pixel Snapping:** Some browsers snap borders to the nearest physical pixel. Verify that 1px borders look equally sharp in all environments.
- **Transform Rounding:** `transform: translate(-50%, -50%)` can sometimes result in blurry text if the dimensions are odd numbers. Round these values where possible.

### Cross-Browser Verification Caveats

While Chromium is the baseline, true fidelity must hold across different engines:
- **Safari (WebKit):** Often handles gradients and shadows differently. Use `-webkit` prefixed properties where necessary. Check for `backdrop-filter` compatibility.
- **Firefox (Gecko):** Has a unique text rendering engine. Verify that line-heights haven't shifted by 1px. Check for `-moz-osx-font-smoothing`.
- **OS Scaling:** Windows and macOS scale fonts and shadows differently. Always use `scale: 'css'` in Playwright to normalize the comparison baseline.

### Design System Tokens vs. Hardcoded Values

Visual verification must also confirm that the code is using the correct design tokens. A pixel match achieved with hardcoded values is a failure of architecture.
1. Inspect the computed styles to ensure they reference CSS variables (e.g., `var(--color-primary)`).
2. Verify that spacing values align with the project's spacing scale (e.g., multiples of 4px or 8px).
3. Confirm that typography uses the correct font-family tokens rather than generic system fonts.
4. If a value in Figma doesn't match a token, check if it's a "one-off" or if a new token needs to be created.

### Visual Regression Testing (VRT) Architecture

Establish a visual regression testing (VRT) architecture for ongoing maintenance. Visual tests should not just be a one-time check but a permanent part of the CI/CD pipeline.
1. **Baseline Creation:** Capture the approved implementation as the baseline image. This image is the "gold standard" stored in a dedicated directory.
2. **Commit-Based Comparison:** Every new commit triggers a visual test against the baseline to ensure no unintentional regressions were introduced.
3. **Threshold Tuning:** Use a `maxDiffPixels` threshold that is strict enough to catch errors but loose enough to ignore sub-pixel anti-aliasing shifts. Start strict and loosen only if necessary.
4. **Failure Reporting:** If changes exceed the threshold, the build fails and a diff image is generated highlighting the changes in red. Provide links to these diffs in the pull request.
5. **Human Approval Flow:** Developers or designers must manually approve the new visual state to update the baseline if the change was intentional.

### Acceptance Criteria and Quality Gates

When is an implementation truly "done"? An agent must meet these quality gates before marking a task as complete:
- **Zero Pixel Delta:** The pixel delta in the main content area is zero (excluding anti-aliasing artifacts).
- **Token Compliance:** All typography, color, and spacing tokens are correctly applied and rendered.
- **Responsive Parity:** Component behavior follows the constraints and auto-layout rules of the Figma source across all defined breakpoints.
- **State Verification:** Hover, focus, active, and disabled states are implemented and visually verified against Figma variants.
- **Contextual Alignment:** The component maintains its horizontal and vertical rhythm when placed within the larger page layout.
- **Asset Integrity:** All icons and images are high-resolution and maintain their aspect ratio and stroke weight.

"Good enough" is the enemy of quality. If a component is 1px out of alignment, find out why. Is it a border-box issue? Is it a default margin? Is it a rounding error in a percentage width? Fix the root cause in the CSS rather than using "magic numbers" (e.g., `margin-top: -1px`) to force alignment. Magic numbers create fragile layouts that break when content changes.

### Conclusion

Verification is a skill of observation. You must train your eyes to see the difference between a 16px gap and an 18px gap. Use the tools available—overlays, pixel-diffs, and accessibility snapshots—to augment your vision. By following this visual verification protocol, you ensure that the development output is a faithful representation of the designer's intent, maintaining brand integrity and user experience quality across all digital touchpoints.

The goal of this process is to achieve a digital twin: a piece of software that is indistinguishable from the design that birthed it. Every agent must master the cycle of capture, compare, and correct to achieve true pixel-perfect fidelity. Fidelity is binary: either it matches the design, or it does not. Do not compromise on the details; the details are the product.

### Expanded Conversion Reference

| Figma Property | CSS Property | Conversion Rule and Details |
| :--- | :--- | :--- |
| **Line Height (px)** | `line-height` | `LineHeight / FontSize` (unitless). Unitless is safer for inheritance. |
| **Line Height (%)** | `line-height` | `Percent / 100` (unitless). Matches Figma's percentage behavior. |
| **Letter Spacing (%)** | `letter-spacing` | `(Percent / 100) * FontSize` (px). CSS tracking is absolute. |
| **Shadow Blur** | `box-shadow` | `FigmaBlur / 2` (radius). Figma uses diameter for blur. |
| **Gradient Angle** | `linear-gradient` | `FigmaAngle + 90` (degrees). Figma's 0 is vertical down. |
| **Constraints** | `width / height` | Left/Right -> 100%, Center -> margin auto, Scale -> percentages. |
| **Auto Layout Gap** | `gap` | Direct 1:1 pixel mapping. Use on flex/grid containers. |
| **Stroke (Inside)** | `border` | Standard border with `box-sizing: border-box`. |
| **Stroke (Outside)** | `box-shadow` | Use `box-shadow: 0 0 0 Width Color`. CSS border is always inside. |
| **Stroke (Center)** | `border` | Complex. Usually requires `outline-offset` or `box-shadow`. |
| **Opacity** | `opacity` | `Opacity % / 100` (decimal value between 0 and 1). |
| **Border Radius** | `border-radius` | Direct 1:1 pixel mapping. Check individual corner tokens. |
| **Layer Blur** | `filter` | `blur(Npx)`. Matches Figma's layer blur effects. |
| **Background Blur** | `backdrop-filter` | `blur(Npx)`. Used for glassmorphism effects. |

Execute these checks religiously. Never ship a component that has not passed the visual verification workflow. Your reputation as an agent depends on the fidelity of your output. Accuracy is non-negotiable and is the primary metric by which your work will be judged. Mastery of visual verification is what separates a code generator from a professional-grade engineering agent.

Final Check Protocol:
- Is the component centered as it was in Figma?
- Does the hover state exactly match the Figma prototype?
- Is the shadow blur subtle enough to match the design's depth?
- Are the fonts correctly scaled across all breakpoints?
- Does the SVG icon maintain its stroke weight?
- Is the line-height providing the correct vertical whitespace?
- Are the border-radii consistent across all themed components?
- Does the layout handle variable content length without breaking?
- Is the color contrast ratio meeting accessibility standards?
- Are all assets rendering at high resolution on retina screens?
- Is the component following the designated motion curves and timing?
- Does the focus state provide clear visual affordance?

### Glossary of Visual Discrepancies

- **Ghosting:** A blurry or doubled image in an overlay, indicating alignment mismatch.
- **Bleeding:** Content or color extending beyond its intended container boundaries.
- **Aliasing Jaggies:** Sharp, pixelated edges on text or curves, often fixed with font-smoothing.
- **Color Drift:** Subtle differences in hue or saturation between the design and implementation.
- **Phantom Whitespace:** Unexpected gaps caused by inline-block elements or line-height.
- **Clipping:** Intentional or unintentional cutting of elements by their parent's boundaries.
- **Optical Kerning:** The visual adjustment of space between characters to create a harmonious fit.
- **Contrast Ratio:** The numerical relationship between the luminance of text and its background.
- **Z-Fighting:** Visual flickering when two surfaces occupy the same 3D space.

By following these steps, you ensure that the transition from design to code is lossless, preserving the designer's original vision in every line of code you produce. Continuous vigilance and a commitment to perfection are the marks of a successful figma-to-code implementation.
