# Build Optimization

Sources: Vite official documentation (vitejs.dev), Rollup documentation, esbuild documentation, community optimization guides

Covers Vite-specific build configuration: Rollup output options, manual chunks,
minification (esbuild vs terser), CSS code splitting, asset inlining thresholds,
and build performance profiling. For framework-agnostic code splitting concepts
and bundle analysis tools, see `@tank/web-performance` references/bundle-optimization.md.

## Build Defaults

Vite's production build uses Rollup with sensible defaults:

```ts
export default defineConfig({
  build: {
    target: 'modules',          // browsers supporting native ESM
    outDir: 'dist',             // output directory
    assetsDir: 'assets',        // nested directory for generated assets
    sourcemap: false,           // true | 'inline' | 'hidden'
    minify: 'esbuild',         // 'esbuild' (fast) | 'terser' (smaller) | false
    cssMinify: 'esbuild',      // separate from JS minify since Vite 5
    cssCodeSplit: true,         // split CSS per async chunk
    assetsInlineLimit: 4096,   // bytes; smaller files inlined as base64
    chunkSizeWarningLimit: 500, // kB; warning threshold
    emptyOutDir: true,          // clean outDir before build
  },
})
```

## Code Splitting Strategies

Vite automatically code-splits at dynamic import boundaries. Manual intervention
is needed when automatic splitting produces suboptimal chunks.

### Automatic Splitting via Dynamic Imports

```ts
// Route-based splitting (most common)
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))

// Feature-based splitting
const heavyChart = () => import('./components/HeavyChart')
```

Every `import()` call creates a new chunk. Shared dependencies between chunks
are automatically extracted into a common chunk by Rollup.

### Manual Chunks

Override Rollup's automatic chunking when you need control:

```ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Group by domain
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-popover'],
          'chart-vendor': ['recharts', 'd3-scale', 'd3-shape'],
        },
      },
    },
  },
})
```

### Function-Based Manual Chunks

For dynamic logic, use the function form:

```ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Split node_modules by top-level package
            const parts = id.split('node_modules/')[1].split('/')
            const pkg = parts[0].startsWith('@') ? `${parts[0]}/${parts[1]}` : parts[0]

            // Group large frameworks
            if (['react', 'react-dom', 'react-router-dom'].includes(pkg)) {
              return 'react-vendor'
            }
            if (pkg.startsWith('@radix-ui') || pkg === 'class-variance-authority') {
              return 'ui-vendor'
            }
            // Everything else in a general vendor chunk
            return 'vendor'
          }
          // Return undefined to let Rollup handle non-vendor modules
        },
      },
    },
  },
})
```

Return `undefined` (not a string) to let Rollup apply its default strategy for
that module. Never return an empty string.

### Manual Chunks Pitfalls

| Pitfall | Consequence | Prevention |
| --- | --- | --- |
| Putting everything in one vendor chunk | No cache granularity; any dep update invalidates all | Split by update frequency |
| One chunk per dependency | HTTP request waterfall | Group by domain (max 5-8 chunks) |
| Circular chunk dependencies | Runtime errors or duplicate code | Verify with visualizer |
| Forgetting transitive deps | Module appears in multiple chunks | Include the full dependency subgraph |
| Not returning `undefined` for unmatched modules | Empty chunk or misplaced code | Always handle the fallback case |

### Recommended Chunk Strategy

| Chunk | Contents | Update Frequency |
| --- | --- | --- |
| `framework` | React/Vue/Svelte runtime | Rare (months) |
| `ui-vendor` | UI library (Radix, Headless UI) | Low (weeks) |
| `vendor` | All other node_modules | Medium |
| Route chunks (auto) | Per-route application code | High (every deploy) |
| `shared` | Shared application utilities | High |

## Minification

### esbuild (default)

Fastest option. Handles most code correctly. Default since Vite 2.

```ts
export default defineConfig({
  build: {
    minify: 'esbuild',
    target: 'es2020', // controls syntax lowering
  },
})
```

### terser

Slower but produces slightly smaller output. Required for specific transformations.

```ts
export default defineConfig({
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,       // remove console.* calls
        drop_debugger: true,      // remove debugger statements
        pure_funcs: ['console.log'], // mark as side-effect-free
      },
      mangle: {
        safari10: true,           // work around Safari 10 bugs
      },
      format: {
        comments: false,          // remove all comments
      },
    },
  },
})
```

Install terser separately: `npm i -D terser`

### When to Use Which

| Scenario | Choice |
| --- | --- |
| Default / fastest builds | esbuild |
| Need `drop_console` | terser (or use `define` to replace `console.log` with no-op) |
| Need property mangling | terser |
| Class names must be preserved (ORM, serialization) | terser with `keep_classnames: true` |
| Build time is critical (CI/CD) | esbuild |

### esbuild Alternative for Console Removal

Instead of terser, use `esbuild.drop`:

```ts
export default defineConfig({
  esbuild: {
    drop: ['console', 'debugger'],
  },
})
```

This is faster than terser and achieves the same result for console removal.

## CSS Code Splitting

When `build.cssCodeSplit` is `true` (default), CSS imported by an async chunk
is extracted into its own file and loaded alongside the chunk.

```ts
export default defineConfig({
  build: {
    cssCodeSplit: true, // default
  },
})
```

Disable only when you need a single CSS file (rare):

```ts
export default defineConfig({
  build: {
    cssCodeSplit: false, // all CSS in one file
  },
})
```

### CSS Processing Pipeline

1. PostCSS (if `postcss.config.js` exists) - autoprefixer, nesting, etc.
2. CSS Modules (files named `*.module.css`)
3. Pre-processors (Sass, Less, Stylus) - install the preprocessor, no config needed
4. Minification (esbuild or Lightning CSS)

```bash
# Install preprocessors as needed (no plugin required)
npm i -D sass
npm i -D less
npm i -D stylus
```

### Lightning CSS (experimental)

```ts
export default defineConfig({
  css: {
    transformer: 'lightningcss',
    lightningcss: {
      targets: browserslistToTargets(browserslist('>= 0.25%')),
    },
  },
  build: {
    cssMinify: 'lightningcss',
  },
})
```

## Asset Handling

### Inline Threshold

Files smaller than `assetsInlineLimit` are inlined as base64 data URIs:

```ts
export default defineConfig({
  build: {
    assetsInlineLimit: 4096, // 4kB default
  },
})
```

| Threshold | Trade-off |
| --- | --- |
| Lower (1024) | More HTTP requests, smaller HTML/JS, better caching |
| Default (4096) | Balanced |
| Higher (8192+) | Fewer requests, larger bundle, no individual caching |

SVG files are never inlined by default (they can be imported as components instead).

### Output File Names

```ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) return 'css/[name]-[hash].css'
          if (/\.(png|jpe?g|gif|svg|webp|avif)$/.test(assetInfo.name ?? '')) {
            return 'images/[name]-[hash][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        },
      },
    },
  },
})
```

## Tree-Shaking

Rollup performs tree-shaking by default. Ensure it works:

1. Use ESM imports/exports exclusively. CJS defeats tree-shaking.
2. Mark packages as side-effect-free in `package.json`:
   ```json
   { "sideEffects": false }
   ```
   Or specify files with side effects:
   ```json
   { "sideEffects": ["*.css", "./src/polyfills.ts"] }
   ```
3. Avoid barrel files that re-export everything (`index.ts` with `export * from`).
4. Import specific paths when available: `import debounce from 'lodash-es/debounce'`.

### Verifying Tree-Shaking

Use the visualizer to confirm unused exports are eliminated:

```ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
      filename: 'stats.html',
    }),
  ],
})
```

Run `vite build` and inspect the generated `stats.html`.

## Build Performance

### Profiling the Build

```bash
# Measure build time
time npx vite build

# Detailed Rollup timing
VITE_CJS_TRACE=true npx vite build

# Generate bundle stats
npx vite-bundle-visualizer
```

### Build Speed Optimizations

| Optimization | Impact | How |
| --- | --- | --- |
| Use esbuild minification | High | Default; do not switch to terser unless needed |
| Reduce source maps | Medium | `sourcemap: false` in prod (or `'hidden'`) |
| Limit Rollup plugins | Medium | Remove dev-only plugins from prod build |
| Increase Node memory | Low | `NODE_OPTIONS='--max-old-space-size=8192'` |
| Use SWC-based React plugin | Medium | `@vitejs/plugin-react-swc` instead of Babel-based |

### Target Configuration

The `build.target` option controls which syntax features are preserved:

```ts
export default defineConfig({
  build: {
    target: 'es2020',     // specific ES version
    // OR
    target: 'chrome100',  // specific browser
    // OR
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
  },
})
```

Higher targets produce smaller output because fewer syntax transformations are needed.

## Chunk Analysis Checklist

After every significant dependency change:

1. Run `npx vite build` and check warnings for oversized chunks.
2. Generate a visualizer report.
3. Verify no duplicate modules appear across chunks.
4. Confirm lazy-loaded routes produce separate chunks.
5. Check that vendor chunks are stable (same hash when app code changes).
6. Validate gzipped sizes: aim for < 50kB initial JS, < 200kB total initial load.
