# Figma Extraction Workflow

Sources: Figma Dev Mode API (2024-2025), figma-desktop MCP server documentation

## Figma URL Parsing

Correct extraction begins with accurate URL parsing. Agents must extract the `fileKey` and `nodeId` to target specific design elements.

### Standard Design URLs
Format: `https://figma.com/design/:fileKey/:fileName?node-id=:nodeId`
- **fileKey**: The unique alphanumeric identifier following `/design/`.
- **nodeId**: Extracted from the `node-id` query parameter. Convert the hyphen to a colon (e.g., `1-2` becomes `1:2`).

### Branch URLs
Format: `https://figma.com/design/:fileKey/branch/:branchKey/:fileName?node-id=:nodeId`
- **Logic**: Use the `branchKey` as the `fileKey` for all MCP tool calls. Targeting the main `fileKey` on a branch URL will result in stale or missing data.

### URL Transformation Table
| Source URL Component | Extracted Identifier | Conversion Rule |
|----------------------|----------------------|-----------------|
| `node-id=101-456`    | `101:456`            | Replace `-` with `:` |
| `/design/ABC123/`    | `ABC123`             | Use directly |
| `/branch/XYZ789/`    | `XYZ789`             | Use as fileKey |

## The Mandatory 6-Step Extraction Workflow

Implementations must follow this exact sequence to ensure parity and maintainability.

### 1. get_design_context
Invoke this tool first to retrieve AI-generated code. This provides the primary structure, Tailwind classes, and initial layout logic. Specify the `artifactType` correctly to align the generated code with project architecture.

### 2. get_metadata
Call this tool if `get_design_context` is truncated due to size or if the node is extremely complex. Metadata provides the exact XML tree with IDs, positions, and sizes, serving as a fallback for structural gaps.

### 3. get_screenshot
ALWAYS capture a screenshot of the target node. This is the source of truth for visual validation. Use the resulting PNG to verify margins, paddings, and alignment that may be ambiguous in code.

### 4. Download Assets
Identify `imageRef` IDs in the design context or metadata. Use the MCP server's ability to serve these assets via `localhost` URLs. Download or reference these directly rather than searching for external icon packages.

### 5. Translate to Project Conventions
Generated code from `get_design_context` is generic. Manually map hardcoded values (colors, spacing, typography) to the project's design tokens and reusable components.

### 6. Validate Parity
Run the implemented code in a local environment and compare it side-by-side with the Figma screenshot. Ensure 1:1 visual match before concluding the task.

## Tool Reference: get_design_context

This is the primary tool for code generation. It translates Figma node data into functional code.

### Required Parameters
- `nodeId`: The target element ID.
- `artifactType`: Controls the scope of the generated code.
- `clientFrameworks`: e.g., "react", "vue".
- `clientLanguages`: e.g., "typescript", "html,css".

### Artifact Types
| Type | Usage Scenario |
|------|----------------|
| `WEB_PAGE_OR_APP_SCREEN` | Full page layouts with headers and footers. |
| `COMPONENT_WITHIN_A_WEB_PAGE_OR_APP_SCREEN` | Specific sections like Hero or Pricing tables. |
| `REUSABLE_COMPONENT` | Atomic units like Buttons, Inputs, or Cards. |
| `DESIGN_SYSTEM` | Global styles, typography sets, and color palettes. |

### Example Invocation
```javascript
figma_get_design_context({
  nodeId: "12:34",
  artifactType: "COMPONENT_WITHIN_A_WEB_PAGE_OR_APP_SCREEN",
  clientFrameworks: "react",
  clientLanguages: "typescript",
  reasoning: "Extracting the Hero section component structure"
})
```

## Tool Reference: get_metadata

Use `get_metadata` for structural analysis and when handling massive nodes.

### Data Returned
- **XML Structure**: A hierarchical view of all child nodes.
- **Node IDs**: Unique identifiers for every sub-element (useful for drilling down).
- **Geometric Data**: Precise X, Y coordinates and Width/Height in pixels.
- **Layer Types**: Distinguishes between `FRAME`, `TEXT`, `VECTOR`, and `INSTANCE`.

### Implementation Pattern
Use metadata to verify z-index ordering and absolute positioning logic that might be obscured in the flex-heavy output of `get_design_context`.

## Tool Reference: get_screenshot

Visual verification is non-negotiable.

### Capture Rules
- **Consistency**: Capture at 2x scale if high-density assets are present.
- **Context**: Ensure the screenshot captures the entire node, including outer shadows and overflow elements.
- **Validation**: Compare the PNG output against the local browser rendering using a split-view or overlay.

### Example Invocation
```javascript
figma_get_screenshot({
  nodeId: "12:34",
  reasoning: "Visual reference for pixel-perfect alignment validation"
})
```

## Tool Reference: get_variable_defs

Retrieve design tokens directly from Figma's variable system.

### Data Structure
Returns an object of key-value pairs representing the document's variables.
```json
{
  "brand/primary": "#3B82F6",
  "spacing/md": "16px",
  "radius/lg": "8px"
}
```

### Mapping Strategy
Agent must map these variables to the project's theme configuration (e.g., `tailwind.config.js` or CSS variables). Never use the raw hex values if a corresponding variable exists.

## Token Limit Management

Figma nodes can be extremely heavy. Large extractions often fail or truncate.

### Extraction Limits
- **Threshold**: Aim for 50,000 to 100,000 tokens per call.
- **Avoidance**: NEVER select a top-level "Page" or "Artboard" containing multiple full-page screens.

### Fragmentation Strategy
1. Select the top-level Frame for the specific screen.
2. If `get_design_context` returns truncated code, use `get_metadata` to identify child component IDs.
3. Extract each component (Header, Main, Footer) individually.
4. Assemble the parts in the local codebase.

## Asset Handling & Localhost URLs

The figma-desktop MCP server provides direct access to images and icons.

### Image References
Images in Figma are represented as `imageRef` IDs. The MCP server provides a local endpoint to fetch these assets.

### Icons and Vectors
- **Recommendation**: Do not search for "Lucide" or "FontAwesome" equivalents unless specified. 
- **Action**: Extract vectors as SVG code directly from the design context or metadata.
- **localhost URLs**: Use the served asset URLs during development for immediate visual feedback.

### Asset Pipeline
1. Locate `imageRef` or vector node.
2. Request asset export via MCP if not included in design context.
3. Save SVGs to `public/icons/` or similar directory.
4. Reference local files in the implementation.

## Node Selection Strategy

Precise targeting reduces noise and improves code quality.

### Top-Down Approach
- Start with the outer container Frame to establish the layout grid or flex container.
- Use `get_metadata` on the parent to see how children relate spatially.

### Bottom-Up Approach
- Extract atomic components (Buttons, Chips, Icons) first.
- Ensure these atomics use the project's design tokens.
- Nest these atomics into larger organisms extracted later.

### Selection Matrix
| Element Size | Tool Choice | Strategy |
|--------------|-------------|----------|
| Atomic (Button) | get_design_context | Full generation |
| Complex (Table) | get_design_context + get_metadata | Structural verification |
| Screen (Dashboard) | get_metadata | Identification of child IDs |
| Group of Screens | BLOCKED | Refine selection to single screen |

## Metadata-Only vs Full Design Context

Deciding which tool to lead with determines extraction efficiency.

### Use Full Design Context When:
- The node is a single component or a small section.
- You need functional Tailwind/CSS code immediately.
- The node size is under 50k tokens.

### Use Metadata-Only When:
- The node is an entire page or a complex dashboard.
- You need to map existing components to Figma nodes.
- You want to see the hierarchy without the weight of property definitions.
- `get_design_context` consistently fails or times out.

## Implementation Workflow (Step-by-Step)

### Phase A: Discovery
1. Identify the Figma URL from the task description.
2. Parse `fileKey` and `nodeId`.
3. Call `figma_get_variable_defs` to understand the token system.

### Phase B: Extraction
1. Call `figma_get_design_context` for the primary node.
2. Immediately call `figma_get_screenshot` for visual reference.
3. If code is truncated, call `figma_get_metadata` and identify sub-node IDs for fragmented extraction.

### Phase C: Refinement
1. Audit the generated code for hardcoded values.
2. Replace hardcoded HEX codes with theme variables.
3. Replace hardcoded pixel spacing with spacing tokens (e.g., `mb-4` instead of `margin-bottom: 16px`).
4. Ensure typography matches the project's font scale.

### Phase D: Verification
1. Compare the local browser preview with the Figma screenshot.
2. Use browser dev tools to inspect computed values against Figma metadata.
3. Verify responsiveness by checking constraints (Fill vs Hug) in metadata.

## Practical Patterns

### Component Extraction Example
```javascript
// Step 1: Get Context
const context = await figma_get_design_context({
  nodeId: "145:202",
  artifactType: "REUSABLE_COMPONENT",
  clientFrameworks: "react",
  clientLanguages: "typescript"
});

// Step 2: Get Screenshot
const screenshot = await figma_get_screenshot({
  nodeId: "145:202"
});

// Step 3: Extract Variable Mappings
const variables = await figma_get_variable_defs();
```

### Fragmented Extraction for Large Screens
```javascript
// 1. Get metadata for whole screen
const screenMetadata = await figma_get_metadata({ nodeId: "200:10" });

// 2. Identify child IDs (e.g., Header: "200:11", Content: "200:15", Sidebar: "200:20")

// 3. Extract Header
const headerCode = await figma_get_design_context({ nodeId: "200:11", artifactType: "COMPONENT_WITHIN_A_WEB_PAGE_OR_APP_SCREEN" });

// 4. Extract Sidebar
const sidebarCode = await figma_get_design_context({ nodeId: "200:20", artifactType: "COMPONENT_WITHIN_A_WEB_PAGE_OR_APP_SCREEN" });
```

### Asset Reference Handling
When encountering `imageRef: "123:456"`, use the dedicated media endpoint provided by the MCP server to retrieve the binary data. Ensure the `alt` text is descriptive based on the layer name found in metadata.

## Anti-Patterns to Avoid

- **Artboard Selection**: Never try to extract a whole Artboard containing 20 screens. It will fail.
- **Ignoring Constraints**: Metadata shows if a layer is "Scale", "Left", or "Center". Ignoring this leads to broken responsiveness.
- **Manual Measurement**: Never "eye-ball" margins. Use the metadata geometric values for exact spacing.
- **Hex Hardcoding**: Hex codes are technical debt. Always use the variable system.
- **Single-Tool Reliance**: Relying only on `get_design_context` leads to missing visual nuances caught by `get_screenshot`.

## Technical Specifications

### Geometric Accuracy
Figma coordinates are relative to the parent frame. When translating absolute positioning, ensure the container has `position: relative`.

### Auto Layout Translation
| Figma Property | CSS Property |
|----------------|--------------|
| layoutMode: HORIZONTAL | flex-direction: row |
| layoutMode: VERTICAL | flex-direction: column |
| primaryAxisAlignItems | justify-content |
| counterAxisAlignItems | align-items |
| itemSpacing | gap |
| paddingLeft/Right/Top/Bottom | padding |

### Font Weight Mapping
Figma "Medium" (500) often requires `font-medium` in Tailwind. Verify the exact numeric weight in metadata property `fontWeight`.

### Sizing Constraints
- **FIXED**: `width: Npx`, `height: Npx`.
- **HUG**: `width: fit-content`.
- **FILL**: `flex: 1 1 0%` or `width: 100%`.

### Opacity and Blending
Figma layer opacity is distinct from fill opacity. Apply `opacity: N` to the container element if layer-level opacity is specified in metadata.

### Effects and Shadows
Shadows in Figma are often stacked. `get_design_context` usually captures this as a comma-separated `box-shadow`. Cross-reference with metadata `effects` array to ensure no subtle inner shadows or blurs are missed.

### Responsive Verification
Check the `layoutAlign` and `layoutGrow` properties in metadata to determine how components should behave in fluid layouts. `STRETCH` maps to `align-self: stretch` or `width: 100%`.

### Exporting SVGs
For nodes of type `VECTOR` or `BOOLEAN_OPERATION`, if the design context does not provide SVG code, use the export functionality of the figma-desktop MCP server to obtain the vector data.

### Variable Mode Handling
Nodes may have different variable modes (e.g., Light vs Dark). If multiple modes exist, call `get_variable_defs` for each relevant mode to ensure correct theme mapping.

### Handling Instances
Instances of components reference a `mainComponentId`. If the instance data is insufficient, use the `mainComponentId` to extract the master component's design context for better structural understanding.

### Text Property Verification
Check `lineHeightPx` and `letterSpacing` in metadata. Figma's default `line-height: normal` varies by font; always use the pixel or unitless value from metadata for precision.

### Handling Gradients
Figma gradient handles (`gradientHandlePositions`) define the start and end points. Translate these to CSS `linear-gradient` degrees or directions. Note that Figma 0 degrees is vertical (bottom to top), whereas CSS 0 degrees is bottom to top but some browsers interpret it differently. Use the 90-degree rotation rule (Figma 0° = CSS 90°).

### Border and Stroke
Metadata distinguishes between `INSIDE`, `OUTSIDE`, and `CENTER` strokes. Standard CSS `border` is `INSIDE`. For `OUTSIDE` or `CENTER`, use `box-shadow` or `outline` to simulate the effect without affecting layout geometry.

### Layer Visibility
Metadata property `visible: false` must be respected. Do not render hidden layers unless they are part of a conditional state (e.g., a hidden mobile menu).

### Z-Index Resolution
While Figma layers are ordered in the tree, absolute positioning requires explicit `z-index`. Use the layer order in metadata to assign appropriate `z-index` values in the implementation.

### Clipping and Overflow
Frames with `clipsContent: true` must have `overflow: hidden` in the implemented CSS.

### Handling Component Sets
For variants (e.g., "Primary", "Secondary", "Disabled"), extract the design context for each variant to understand the property differences, then implement them as props in the final component.
