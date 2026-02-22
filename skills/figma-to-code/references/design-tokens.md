# Design Tokens

Sources: Figma Variables API (2024), Design Tokens W3C Community Group, Tailwind CSS Configuration, Style Dictionary Documentation

Design tokens are the visual atoms of a design system. They represent the smallest repeatable values—such as colors, spacing, and typography—that ensure pixel-perfect implementation and maintainability across platforms. By using tokens instead of hardcoded values, agents create a bridge between Figma's design intent and the final codebase, allowing for systematic updates and consistency.

## Extracting Tokens from Figma

Extraction is the first step in translating design intent to code. Agents must use the available Figma MCP tools to identify and catalog these values.

### The get_variable_defs Tool
This is the primary tool for extracting structured design tokens. It returns a JSON object of key-value pairs representing the variables defined in the Figma file.
- Format: `{'category/type/variant': 'value'}`
- Example: `{'color/primary/default': '#3B82F6', 'spacing/md': '16px'}`
- Use this tool to get the "source of truth" for variables before inspecting individual nodes. It reveals the underlying system that might not be obvious from looking at a single element's CSS.

### Figma Variables API Structure
Figma organizes variables into collections and modes.
- Collections: Groups of related variables (e.g., "Brand", "Functional", "Primitive"). Professional files often separate "Primitives" (raw values) from "Semantic" tokens (usage-based).
- Modes: Different values for the same variable set (e.g., "Light Mode", "Dark Mode", "Condensed"). Modes are critical for implementing themes systematically.
- Variable Types:
    * COLOR: Hex or RGBA values for fills, strokes, and effects.
    * FLOAT: Numeric values for spacing, radius, opacity, and font sizes.
    * STRING: Content strings or font family names.
    * BOOLEAN: Logic for visibility or variant switching.

### Variable Aliasing
In Figma, a semantic variable (e.g., `color-text-primary`) might alias a primitive variable (e.g., `blue-900`).
- When extracting, prioritize the semantic name.
- If the tool returns raw values, attempt to map them back to the semantic structure identified in the `get_variable_defs` JSON.

### Manual Identification from Metadata
When formal variables are missing, agents must identify tokens manually using `get_design_context` and `get_metadata`.
- Search for repeated hex codes or numeric values across multiple nodes.
- Patterns like `gap: 16`, `padding: 16`, and `margin-bottom: 16` indicate a `--spacing-md` or `--spacing-4` token.
- Consistent font sizes (e.g., 14px, 16px, 18px) indicate a typographic scale.
- Look for common opacity levels like 0.1, 0.5, or 0.8 to define an opacity scale.

## Token Tier Architecture

A robust token system uses three distinct layers to balance flexibility and control.

### 1. Primitive Tokens (Options)
The raw values of the design system. They have no semantic meaning and describe what the value is.
- `blue-500`: #3B82F6
- `gray-900`: #111827
- `spacing-4`: 16px

### 2. Semantic Tokens (Decisions)
These tokens describe how a primitive value is used. They refer to primitives rather than hardcoded values.
- `color-primary`: var(--blue-500)
- `color-background-body`: var(--white)
- `spacing-container-padding`: var(--spacing-6)

### 3. Component Tokens (Overrides)
Specific to a single component, used to handle unique overrides or complex states.
- `button-primary-background`: var(--color-primary)
- `input-border-error`: var(--color-danger)

## Token Naming Conventions

Naming must be semantic and systematic. Avoid describing the value (e.g., `blue-500`) in favor of the function (e.g., `primary`).

### Figma Naming Parity Rule

Token names should stay as close as possible to Figma variable names.

- Prefer direct carry-over from Figma names when technically possible.
- If project syntax requires normalization (for example, `/` to `-`, lowercase conversion, prefixing), preserve the semantic path.
- Do not silently rename tokens into unrelated names.

If a rename is unavoidable, publish a mapping table in the implementation notes:

| Figma Variable | Code Token | Reason |
|----------------|------------|--------|
| `color/primary/default` | `--color-primary-default` | CSS variable syntax normalization |
| `spacing/container/lg` | `--spacing-container-lg` | Slash-to-dash conversion |

When this mapping is introduced, explicitly state that Figma names should be updated to match the chosen naming scheme if long-term parity is required.

### Category-Type-Variant-State Pattern
For complex systems, use a hierarchical structure to prevent naming collisions and improve discoverability.
- Structure: `[category]-[type]-[item]-[variant]-[state]`
- Example: `color-background-button-primary-hover`
- Example: `color-text-input-secondary-disabled`
- Example: `border-width-card-focus`

### Scale Tokens
Scales provide a range of values for layout and typography.
- Spacing Scale: `spacing-1` (4px) through `spacing-16` (64px).
- Font Size Scale: `font-size-xs` through `font-size-9xl`.
- Weight Scale: `font-weight-light`, `font-weight-normal`, `font-weight-bold`.

## CSS Custom Properties Implementation

Implement tokens as CSS Custom Properties (CSS variables) in the `:root` element. This makes them accessible globally and allows for runtime overrides (e.g., theme switching).

```css
:root {
  /* Colors - Primitives */
  --color-blue-50: #EFF6FF;
  --color-blue-100: #DBEAFE;
  --color-blue-200: #BFDBFE;
  --color-blue-300: #93C5FD;
  --color-blue-400: #60A5FA;
  --color-blue-500: #3B82F6;
  --color-blue-600: #2563EB;
  --color-blue-700: #1D4ED8;
  --color-blue-800: #1E40AF;
  --color-blue-900: #1E3A8A;

  --color-gray-50: #F9FAFB;
  --color-gray-100: #F3F4F6;
  --color-gray-200: #E5E7EB;
  --color-gray-300: #D1D5DB;
  --color-gray-400: #9CA3AF;
  --color-gray-500: #6B7280;
  --color-gray-600: #4B5563;
  --color-gray-700: #374151;
  --color-gray-800: #1F2937;
  --color-gray-900: #111827;

  /* Colors - Semantic */
  --color-primary: var(--color-blue-500);
  --color-primary-hover: var(--color-blue-600);
  --color-primary-active: var(--color-blue-700);
  --color-background: var(--color-white);
  --color-surface: var(--color-gray-50);
  --color-border: var(--color-gray-200);
  --color-text-primary: var(--color-gray-900);
  --color-text-secondary: var(--color-gray-600);
  --color-text-disabled: var(--color-gray-400);
  --color-error: #EF4444;

  /* Typography - Families */
  --font-family-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-family-mono: 'JetBrains Mono', monospace;

  /* Typography - Sizes */
  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */
  --font-size-4xl: 2.25rem;  /* 36px */

  /* Typography - Line Heights */
  --line-height-none: 1;
  --line-height-tight: 1.25;
  --line-height-snug: 1.375;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.625;

  /* Spacing Scale (4px base) */
  --spacing-1: 0.25rem;  /* 4px */
  --spacing-2: 0.5rem;   /* 8px */
  --spacing-3: 0.75rem;  /* 12px */
  --spacing-4: 1rem;     /* 16px */
  --spacing-5: 1.25rem;  /* 20px */
  --spacing-6: 1.5rem;   /* 24px */
  --spacing-8: 2rem;     /* 32px */
  --spacing-10: 2.5rem;  /* 40px */
  --spacing-12: 3rem;    /* 48px */
  --spacing-16: 4rem;    /* 64px */

  /* Border Radius */
  --radius-none: 0px;
  --radius-sm: 0.125rem; /* 2px */
  --radius-md: 0.375rem; /* 6px */
  --radius-lg: 0.5rem;   /* 8px */
  --radius-xl: 0.75rem;  /* 12px */
  --radius-2xl: 1rem;    /* 16px */
  --radius-full: 9999px;

  /* Shadows (Elevation) */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

  /* Opacity Tokens */
  --opacity-subtle: 0.08;
  --opacity-medium: 0.5;
  --opacity-strong: 0.8;

  /* Transitions */
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
}
```

## Tailwind CSS Configuration Bridging

Bridge CSS variables into the Tailwind configuration to maintain the utility-first workflow while using the design token system.

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          active: 'var(--color-primary-active)',
        },
        surface: 'var(--color-surface)',
        border: 'var(--color-border)',
        text: {
          primary: 'var(--color-text-primary)',
          secondary: 'var(--color-text-secondary)',
          disabled: 'var(--color-text-disabled)',
        },
        error: 'var(--color-error)',
      },
      spacing: {
        '1': 'var(--spacing-1)',
        '2': 'var(--spacing-2)',
        '3': 'var(--spacing-3)',
        '4': 'var(--spacing-4)',
        '5': 'var(--spacing-5)',
        '6': 'var(--spacing-6)',
        '8': 'var(--spacing-8)',
        '10': 'var(--spacing-10)',
        '12': 'var(--spacing-12)',
        '16': 'var(--spacing-16)',
      },
      borderRadius: {
        'sm': 'var(--radius-sm)',
        'md': 'var(--radius-md)',
        'lg': 'var(--radius-lg)',
        'xl': 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
      },
      boxShadow: {
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-xl)',
      },
      fontFamily: {
        sans: 'var(--font-family-sans)',
        mono: 'var(--font-family-mono)',
      },
      fontSize: {
        'xs': 'var(--font-size-xs)',
        'sm': 'var(--font-size-sm)',
        'base': 'var(--font-size-base)',
        'lg': 'var(--font-size-lg)',
        'xl': 'var(--font-size-xl)',
        '2xl': 'var(--font-size-2xl)',
      },
    },
  },
  plugins: [],
}
```

## Advanced Token Patterns

### Dark Mode Implementation
Manage dark mode tokens by overriding semantic variables within a `.dark` class or a media query. This allows the UI logic to remain unchanged while the theme swaps underneath.

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: var(--color-gray-900);
    --color-text-primary: #FFFFFF;
    --color-text-secondary: var(--color-gray-400);
    --color-surface: rgba(255, 255, 255, 0.05);
    --color-border: var(--color-gray-800);
  }
}

/* Or using a class-based approach */
.dark {
  --color-background: var(--color-gray-900);
  --color-text-primary: #FFFFFF;
  --color-text-secondary: var(--color-gray-400);
  --color-surface: rgba(255, 255, 255, 0.05);
  --color-border: var(--color-gray-800);
}
```

### Typographic Modular Scales
Use modular scales to ensure visual harmony in typography. A modular scale uses a consistent ratio to generate sizes.
- Minor Third (1.125): Subtle growth, good for dense data-heavy UIs.
- Major Third (1.25): Clear hierarchy, standard for most web applications.
- Perfect Fourth (1.333): Bold, dramatic differences, excellent for creative or minimal sites.
- Calculation: `base * ratio ^ step`. For example, with a 16px base and 1.25 ratio, steps are 16, 20, 25, 31.25, 39.06.

### Spacing Scales (4px Base)
The 4px grid is the industry standard for digital interfaces because most display resolutions are multiples of 4.
- Base unit: 4px.
- Small increments (4, 8, 12, 16) for internal component spacing (padding inside buttons, gaps between icons and text).
- Large increments (24, 32, 48, 64) for section layout and page margins.
- Avoid using odd numbers or non-multiples of 4 to prevent "blurred" edges caused by sub-pixel rendering.

### Systematic Color Palettes
Generate systematic palettes using HSL manipulation rather than arbitrary hex picking. This ensures that shades feel like they belong to the same family.
- Hue: Constant for the palette (e.g., 220 for blue).
- Saturation: Usually peaks in the middle (500-600) and decreases slightly at extremes.
- Lightness: Distributed from 95% (shade 50) down to 10% (shade 900).
- HSL formula: `hsl(hue, saturation, lightness)`.

### Responsive Tokens with clamp()
Use `clamp()` to create fluid tokens that adapt to viewport size without media queries. This results in cleaner CSS and fewer layout shifts.
- Formula: `clamp(minSize, preferredValue, maxSize)`
- Example: `font-size: clamp(1rem, 2vw + 1rem, 1.5rem);`
- Apply this to spacing (e.g., `--container-padding`) and heading sizes to ensure readability on all devices.

## Interactive State Tokens

State tokens ensure that interactions like hover, focus, and active states are consistent across all interactive elements.

### Hover and Active States
Usually implemented as a lightness shift of the base color.
- Hover: 10% lighter or darker than base.
- Active: 20% darker than base.

### Focus Ring Tokens
Crucial for accessibility.
- `focus-ring-width`: 2px or 3px.
- `focus-ring-color`: Usually a semi-transparent version of the primary color or a high-contrast color like blue.
- `focus-ring-offset`: 2px (to create a gap between the element and the ring).

## Token Documentation and Management

### Variable Comments and Metadata
Include comments in the CSS file to explain the intent and usage of tokens. This helps other developers (and agents) understand the system.
```css
/* @token Primary Brand Color - Used for buttons, active states, and links */
--color-primary: #3B82F6;

/* @token Base Spacing Unit - The core of the 4px grid system */
--spacing-1: 0.25rem;
```

### Style Dictionary Integration
For multi-platform projects (Web, iOS, Android), use Style Dictionary to transform JSON token definitions into platform-specific formats.
- Source: A central `tokens.json` file exported from Figma.
- Output: `variables.css` (Web), `colors.xml` (Android), `Theme.swift` (iOS).
- Benefit: A single change in Figma propagates to all platforms, preventing synchronization errors.

### Verification Workflow
Agents should follow this checklist for token implementation:
1. Run `get_variable_defs` to identify existing tokens in the Figma file.
2. Cross-reference identified values with `get_design_context` output to see where they are applied.
3. Replace hardcoded values in generated components with the appropriate semantic CSS variables.
4. If a value doesn't match a token, check if it's a specific override or if the token system needs expansion.
5. Verify visual parity using `get_screenshot` to ensure the tokens render correctly.

Design tokens are not just variables; they are the contract between design and development. Implement them with rigor to ensure a scalable, maintainable, and robust frontend architecture.
