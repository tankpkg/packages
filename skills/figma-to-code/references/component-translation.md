# Component Translation

Sources: Figma Component API (2024), WAI-ARIA Authoring Practices, React/Vue/Angular Component Best Practices

## Component-First Approach
Prioritize reuse over creation to maintain a clean codebase and consistent design system. Before translating any Figma node into code, verify if a matching component already exists in the project library. Search for atomic elements first, then build up to complex organisms. This "Component-First" mindset prevents fragmentation and reduces technical debt in the production environment.

## Layer Hierarchy Parity

Component internal layers should match Figma structure, not just final appearance.

- Preserve parent/child nesting intent from Figma nodes (container, content, media, label, icon).
- Keep wrapper boundaries that control spacing, clipping, and effects in Figma.
- Keep state-specific sublayers (for example, loading overlay, focus ring layer, badge layer) as distinct code layers when they are distinct in Figma.
- Do not flatten multiple semantic layers into one div unless behavior and rendering remain provably identical.

Minimum translation check per component:
1. Node tree shape matches Figma's logical hierarchy.
2. Layer responsibilities match (layout layer vs visual effect layer vs content layer).
3. Hidden/conditional Figma layers map to explicit conditional rendering in code.

### Existing Component Identification
- Directory Scan: Check the local `/components`, `/ui`, or `/shared` directories for naming matches using fuzzy search tools.
- Pattern Discovery: Use content search tools to find UI patterns similar to the Figma node (e.g., search for "button", "input", "modal", "card").
- API Analysis: Inspect existing component props and types to see if they can handle the Figma variants through configuration rather than duplication.
- Extension Protocol: If a component exists but lacks a required Figma variant, extend its API (e.g., add a new value to a `size` enum or a new optional boolean prop) instead of creating a duplicate component file.
- Documentation Check: Reference the project's Storybook or internal documentation to understand the full capabilities of existing UI components.

## Figma Variant Mapping to Code Props
Figma components utilize properties to define visual and functional variations. Translating these properties into strongly-typed props ensures design-to-code parity and high developer ergonomics.

### Variant Type (Enums and Union Types)
Map multi-choice Figma variants to string union types in TypeScript or enums in other languages. These represent discrete styles, sizes, or orientations.
- Figma Variant: "Size" [Small, Medium, Large] -> Prop: `size: "sm" | "md" | "lg"`
- Figma Variant: "Style" [Primary, Secondary, Outline, Ghost] -> Prop: `variant: "primary" | "secondary" | "outline" | "ghost"`
- Figma Variant: "Position" [Top, Bottom, Left, Right] -> Prop: `position: "top" | "bottom" | "left" | "right"`
- Figma Variant: "Corner Radius" [Round, Square, Pill] -> Prop: `shape: "rounded" | "square" | "pill"`
- Figma Variant: "Alignment" [Start, Center, End] -> Prop: `align: "start" | "center" | "end"`

### Boolean Type (Flags)
Map Figma toggle switches to boolean flags. These control visibility, logical states, or optional features within the component architecture.
- Figma Toggle: "Disabled" -> Prop: `disabled: boolean`
- Figma Toggle: "Loading" -> Prop: `isLoading: boolean`
- Figma Toggle: "Has Label" -> Prop: `withLabel: boolean`
- Figma Toggle: "Inverse" -> Prop: `isInverse: boolean`
- Figma Toggle: "Checkmark" -> Prop: `showCheckmark: boolean`
- Figma Toggle: "Border" -> Prop: `hasBorder: boolean`
- Figma Toggle: "Shadow" -> Prop: `withShadow: boolean`

### Text Type (Content Overrides)
Map Figma text overrides to string props. This separates content from presentation and allows components to be truly dynamic.
- Figma Override: "Button Label" -> Prop: `children: string` or `label: string`
- Figma Override: "Placeholder" -> Prop: `placeholder: string`
- Figma Override: "Helper Text" -> Prop: `helperText: string`
- Figma Override: "Value" -> Prop: `value: string`
- Figma Override: "Description" -> Prop: `description: string`

### Instance Swap Type (Composition)
Map Figma instance swaps to component injection, slot patterns, or render functions.
- Figma Swap: "Leading Icon" -> Prop: `leadingIcon: ReactNode` or `<template #leading-icon>`
- Figma Swap: "Avatar" -> Prop: `avatar: ReactNode`
- Figma Swap: "Action Area" -> Prop: `renderAction: () => ReactNode`
- Figma Swap: "Custom Content Slot" -> Prop: `children: ReactNode`

## Interactive State Mapping
Figma often represents states as discrete variants. In code, these must be mapped to dynamic CSS pseudo-classes, state variables, and ARIA attributes to ensure the component feels responsive and accessible.

### Default State
The baseline styling for a component. Use the values from the "Default" or "Resting" variant in Figma. Ensure all spacing, typography, and color values use established design tokens rather than hardcoded hex values to maintain consistency.

### Hover State
Triggered by mouse interaction. Implement using the `:hover` pseudo-class for CSS-only changes or `onMouseEnter`/`onMouseLeave` for complex JS-driven logic.
- Visual Feedback: Subtle background color shifts, shadow elevation increases, or cursor changes.
- Implementation: `hover:bg-primary-dark` (Tailwind) or `.btn:hover { background: var(--color-primary-dark); }`.
- Requirement: Always ensure `cursor: pointer` is applied to all interactive elements to signify clickability.

### Active and Pressed States
Triggered during the click event. Use the `:active` pseudo-class for immediate tactile feedback.
- Visual Feedback: Subtle scaling (e.g., `transform: scale(0.98)`), background darkening, or inset shadows.
- Pacing: Ensure the transition is quick (under 100ms) to provide immediate feedback to the user's action.

### Focused State
Crucial for keyboard accessibility and power users. Use `:focus-visible` to ensure focus indicators only appear for keyboard navigation, avoiding visual noise for mouse users.
- Mandatory: Visible focus rings must meet a minimum 3:1 contrast ratio against the background.
- Implementation: `focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none`.
- Rule: Never remove focus outlines without providing a visible, high-contrast alternative.

### Disabled State
A state where the component is visible but non-interactive, often due to missing prerequisites.
- Visual Cues: Desaturated colors, reduced opacity (usually 50%), and `cursor: not-allowed`.
- Attributes: Set the `disabled` attribute for native elements or `aria-disabled="true"` for custom div-based elements.
- Logic: Explicitly prevent event propagation and execution of click handlers in the component controller.

### Loading State
Indicates an ongoing background process, API call, or data fetch.
- UI Design: Replace text with a spinner, apply a skeleton overlay, or disable the button while showing a "Loading..." label.
- A11y: Set `aria-busy="true"` and `aria-live="polite"` on the component container to inform assistive technologies of the state change.
- Feedback: For longer operations, consider using a progress bar or percentage indicator if the data is available.

### Error and Validation States
Indicates incorrect input, field requirements, or system failure.
- UI Design: Border color change (usually red-500/600), error icon, and descriptive helper text.
- A11y: Set `aria-invalid="true"` on the input element. Use `aria-describedby` to link the error message element ID to the input field for screen reader context.

## Accessibility (A11y) Requirements
Accessibility is not an optional feature; it is a core functional requirement for production-grade code. Every translated component must meet WCAG AA standards.

### Semantic Foundation
- Action Triggers: Always use `<button type="button">` or `<button type="submit">` for actions. Avoid `<div>` with click handlers unless building complex non-native widgets.
- Navigation: Use `<a>` tags with valid `href` attributes for page transitions. Wrap global navigation blocks in a `<nav>` element.
- Data Entry: Use appropriate `<input>` types (email, tel, password) with associated `<label>` elements. Use `id` and `for` attributes for explicit linking.
- Headings: Maintain a logical heading hierarchy (`<h1>` through `<h6>`) to allow screen reader users to navigate the page structure.

### ARIA Roles and Labels
- Custom UI: If building a custom widget (like a switch, slider, or menu), apply the correct `role` attribute.
- Icon Buttons: Always provide an `aria-label` describing the action (e.g., `aria-label="Close modal"`) for buttons containing only an SVG icon.
- Decoration: Apply `aria-hidden="true"` to decorative icons, illustrations, or elements that provide no semantic value to screen readers.
- Live Regions: Use `aria-live="assertive"` for critical alerts and `aria-live="polite"` for non-disruptive updates.

### Focus Management
- Tab Sequence: Ensure the focus order matches the logical visual layout flow (top-to-bottom, left-to-right).
- Focus Trapping: For modals, drawers, and full-screen overlays, use a focus trap to keep keyboard navigation within the active container.
- Restoration: When an overlay closes, programmatically return focus to the element that originally triggered it.

### Color and Contrast
- Text Contrast: Minimum 4.5:1 ratio for body text; 3:1 for large text (over 18pt bold or 24pt regular).
- UI Elements: Borders, icons, and state indicators must have at least 3:1 contrast against their background.
- Color Dependence: Never use color as the sole indicator of meaning; always provide a secondary cue like an icon or label.

### Keyboard Navigation Patterns
- Buttons/Links: Support activation via `Enter`. Buttons must also support the `Space` key.
- Modals/Overlays: Must close when the `Escape` key is pressed.
- Menus/Tabs: Use arrow keys to move between items within a group.
- Tooltips: Should appear on focus and disappear on blur or the `Escape` key.

## Asset and Media Management
Translate Figma assets into optimized, high-performance web resources.

### Image Optimization
- Localhost Reference: Reference images using the localhost URLs provided by the Figma MCP during extraction.
- Cumulative Layout Shift (CLS): Always define an `aspect-ratio` or explicit width/height in CSS to reserve space for images before they load.
- Lazy Loading: Apply `loading="lazy"` to all images below the fold to improve initial page load performance.
- Responsive Images: Use `srcset` and `sizes` attributes for 2x/3x exports to ensure sharpness on high-density displays.

### Icon Implementation
- SVG Components: Prefer inlining SVGs as functional components rather than using icon fonts or `<img>` tags.
- Design for Scale: SVGs must include a `viewBox` and avoid hardcoded dimensions inside the path data.
- Color Control: Set `fill="currentColor"` or `stroke="currentColor"` on the main paths to allow icons to be styled using parent CSS.
- Accessibility: Apply `focusable="false"` to SVGs to prevent them from receiving focus in legacy browsers, and use `aria-hidden="true"` if decorative.

## Framework Translation Patterns
Standardize component architecture to match the conventions of the target tech stack.

### React: Functional Components
- Typing: Use TypeScript interfaces or types for prop definitions.
- Components:
```tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = ({ 
  label, 
  variant = 'primary', 
  size = 'md', 
  isLoading, 
  className,
  ...props 
}: ButtonProps) => {
  return (
    <button 
      className={cn("btn", `btn-${variant}`, `btn-${size}`, className)}
      disabled={props.disabled || isLoading}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? <Spinner /> : label}
    </button>
  );
};
```

### Vue: Single File Components (SFC)
- Script Setup: Use `<script setup>` with `defineProps` and `defineEmits`.
- Template Binding:
```vue
<script setup lang="ts">
interface Props {
  label: string;
  variant?: 'primary' | 'secondary';
  isLoading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  isLoading: false
});
</script>

<template>
  <button 
    class="btn" 
    :class="[`btn-${variant}`, { 'is-loading': isLoading }]"
    :disabled="isLoading"
  >
    <slot name="icon" />
    <span>{{ label }}</span>
  </button>
</template>
```

### Angular Implementation
- Decorators: Use `@Input()` for props and `@Output()` for events.
- Template:
```typescript
@Component({
  selector: 'app-button',
  standalone: true,
  template: `
    <button [class]="'btn ' + variant" [disabled]="disabled">
      <ng-content></ng-content>
    </button>
  `
})
export class ButtonComponent {
  @Input() variant: string = 'primary';
  @Input() disabled: boolean = false;
}
```

### Tailwind CSS Strategies
- Variant Management: Use `class-variance-authority` (CVA) or `tailwind-merge` to handle complex variant logic.
- Utility Extraction: Avoid long utility strings in templates; group related utilities into logical components.
- Theme Sync: Ensure Tailwind `colors`, `spacing`, and `fontFamily` in `tailwind.config.js` match design tokens exactly.

## Responsive Component Behavior
Figma static designs must become fluid and adaptive in the browser environment.

### Container Queries
Use container queries (`@container`) for component-level responsiveness. This allows a component to adapt its internal layout based on the space available in its parent container rather than the entire screen viewport.

### Breakpoint Integration
- Mobile-First: Start with base styles for mobile viewports and use `min-width` media queries for larger screens.
- Consistency: Align code breakpoints (sm, md, lg, xl) with the design team's grid system definitions.

### Fluid Layouts
- Units: Use `rem`, `em`, and percentages instead of fixed `px` for dimensions and spacing.
- Viewport Scaling: Use `clamp(min, preferred, max)` for typography and padding to create smooth scaling transitions.

## Advanced Composition and Overrides
Handle complex Figma hierarchies with scalable code architectures.

### Instance Overrides
In Figma, instances can have deep overrides of nested components. In code, handle this using:
1. Composition Pattern: Passing child components as props or using slots/children.
2. Render Props: For complex logic-sharing between components.
3. Compound Components: Breaking the component into sub-components (e.g., `Select.Option`, `Card.Header`).

### Auto Layout to CSS Layout
- Stacks: Map directly to `display: flex` with `flex-direction: row` or `column`.
- Spacing: Use the `gap` property for consistent spacing between children.
- Alignment: Map Figma alignment to `justify-content` and `align-items`.
- Constraints: 
    - Hug Contents: `width: fit-content` or `flex-basis: auto`.
    - Fill Container: `width: 100%`, `flex-grow: 1`, or `align-self: stretch`.
    - Fixed Size: Hardcoded `width` and `height` values.

### Nested Composition Boundaries
Maintain clear boundaries between parent and child components. Do not flatten the DOM structure just to simplify the code; preserve the semantic hierarchy shown in Figma to ensure style isolation and reusability. Use CSS modules or scoped styles to prevent leakage between nested component levels.

## Testing and Quality Assurance
Verify that the translated component functions correctly and matches the design intent.

### Visual Regression
- Parity Check: Compare screenshots of the implemented component against the original Figma export using visual diffing tools.
- State Verification: Test every variant and state (hover, focus, disabled) visually to ensure parity.

### Functional Testing
- Interaction: Ensure click handlers, change events, and other interactive behaviors execute as expected.
- Prop Validation: Verify that changing a prop correctly updates the component's appearance and behavior.

### Accessibility Auditing
- Automated Scans: Use tools like Axe or Lighthouse to identify common accessibility issues.
- Manual Testing: Navigate the component using only a keyboard and verify screen reader announcements.

## State Management and Component Logic
Decouple visual states from business logic to ensure components remain reusable and testable.

### Internal vs. External State
- Local State: Use internal state (e.g., `useState` in React, `data` in Vue) for purely UI concerns like "is the dropdown open?" or "is the hover active?".
- Managed State: Use props to receive data from parent components or global stores. This allows the component to be controlled by the application logic.
- Controlled Components: Prefer controlled patterns for inputs where the value and change handlers are passed down from a parent.

### Event Handling
- Standard Naming: Use standard event names for props (e.g., `onClick`, `onChange`, `onSubmit`) to match native HTML behavior.
- Event Bubbling: Ensure events bubble correctly or are explicitly handled to prevent unexpected behavior in complex layouts.
- Throttling and Debouncing: Apply performance optimizations to frequent events like scroll, resize, or fast typing in search inputs.

## Performance and Optimization
Ensure components perform efficiently, especially when used in large lists or complex views.

### Memoization
- React: Use `React.memo`, `useMemo`, and `useCallback` to prevent unnecessary re-renders of components with expensive computation or deep prop trees.
- Vue: Use computed properties to cache derived data and avoid redundant calculations in the template.

### Resource Loading
- Code Splitting: For large components like complex data tables or heavy modals, use dynamic imports (e.g., `React.lazy`) to load the component only when needed.
- CSS Optimization: Avoid loading styles for variants that are not being used in the current view. Use modular CSS or utility-first frameworks to minimize bundle size.

## Component Documentation
Documentation ensures the component remains usable by other developers and aligns with the design system's evolution.

### Prop Documentation
- Comments: Use JSDoc comments for every prop to provide helpful tooltips in modern IDEs.
- Examples: Provide usage examples in the component's header or an associated `.stories` file.
- Defaults: Explicitly document default values for all optional props.

### Maintenance and Deprecation
- Versioning: Use semantic versioning if the components are part of a shared library.
- Deprecation Warnings: Use console warnings to notify developers when they are using an outdated prop or variant, pointing them toward the new implementation.
