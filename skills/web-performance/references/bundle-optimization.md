# Bundle Optimization and Tree-Shaking

Sources: Webpack documentation (v5), Vite/Rollup documentation, web.dev bundle optimization guides, Osmani (JavaScript performance patterns), bundlephobia.com methodology

Covers: Tree-shaking mechanics, code splitting strategies, chunk optimization,
bundle analysis tools, dependency auditing, and performance budgets in CI.
For Vite-specific build configuration (Rollup options, manual chunks, CSS splitting),
see `@tank/vite-mastery` references/build-optimization.md.

## Tree-Shaking

Tree-shaking eliminates dead code (unused exports) from the final bundle. It requires ES module syntax (`import`/`export`) and a bundler that performs static analysis.

### Requirements for Effective Tree-Shaking

| Requirement | Why | Common Failure |
| --- | --- | --- |
| ES module syntax | Static analysis needs static imports | CommonJS `require()` is dynamic, cannot tree-shake |
| `sideEffects: false` in package.json | Tells bundler unused files can be dropped | Missing flag causes entire library to be included |
| No side effects at module level | Top-level code runs on import | `console.log`, DOM manipulation, global mutation at top level |
| Named exports over default | Default export wraps everything | `export default { a, b, c }` defeats tree-shaking |
| Granular imports | Import only what you use | `import _ from 'lodash'` pulls everything |

### Configuring sideEffects

In your application's `package.json`:

```json
{
  "sideEffects": [
    "*.css",
    "*.scss",
    "./src/polyfills.js"
  ]
}
```

This tells the bundler: "All files except these can be safely dropped if their exports are unused."

For libraries: set `"sideEffects": false` if the library is pure (no global side effects).

### Import Patterns and Their Impact

```javascript
// BAD: Imports entire library (~70 KB for lodash)
import _ from 'lodash';
_.debounce(fn, 300);

// BETTER: Named import from ESM build
import { debounce } from 'lodash-es';

// BEST: Cherry-pick the specific module
import debounce from 'lodash-es/debounce';
```

### Verifying Tree-Shaking

1. Build in production mode with source maps.
2. Open the bundle in `source-map-explorer` or `webpack-bundle-analyzer`.
3. Search for known unused exports. If they appear, tree-shaking failed.
4. Check the bundler output for warnings about CommonJS fallbacks.

## Code Splitting Strategies

### Split by Route

Each page/route gets its own chunk. Users only download code for the page they visit.

```
entry.js (shared runtime + framework)
  -> home-chunk.js
  -> dashboard-chunk.js
  -> settings-chunk.js
```

This is the highest-impact split. Implement first.

### Split by Feature

Heavy features that are not always used get their own chunks.

| Feature | Trigger | Chunk |
| --- | --- | --- |
| Rich text editor | User clicks "Edit" | `editor-chunk.js` |
| Chart library | Dashboard page load | `charts-chunk.js` |
| PDF export | User clicks "Export" | `pdf-chunk.js` |
| Admin panel | Admin route | `admin-chunk.js` |

### Split by Vendor

Separate third-party code from application code. Vendors change less frequently, enabling long-term caching.

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Group large dependencies into named chunks
            if (id.includes('recharts') || id.includes('d3')) {
              return 'charts-vendor';
            }
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-vendor';
            }
            return 'vendor';
          }
        },
      },
    },
  },
};
```

### Avoiding Over-Splitting

Too many small chunks cause HTTP overhead (even with HTTP/2).

| Guideline | Target |
| --- | --- |
| Minimum chunk size | 20 KB (compressed) |
| Maximum initial chunks | 5-8 parallel requests |
| Shared code threshold | Extract if used by 2+ routes and > 10 KB |

Webpack: use `optimization.splitChunks.minSize` (default 20 KB).
Vite: Rollup handles this automatically but `manualChunks` overrides it.

## Bundle Analysis

### Tools

| Tool | Bundler | Output |
| --- | --- | --- |
| `webpack-bundle-analyzer` | Webpack | Interactive treemap, searchable |
| `vite-bundle-visualizer` | Vite | Treemap for Rollup output |
| `source-map-explorer` | Any | Treemap from source maps |
| `bundlephobia.com` | N/A (web) | Size/download cost of npm packages |
| `pkg-size.dev` | N/A (web) | Bundle size with tree-shaking simulation |
| `size-limit` | Any | Budget enforcement in CI |

### Running Bundle Analysis

```bash
# Webpack
npx webpack-bundle-analyzer dist/stats.json

# Generate stats.json
webpack --profile --json > dist/stats.json

# Vite
npx vite-bundle-visualizer

# Source map explorer (any bundler)
npx source-map-explorer dist/assets/*.js
```

### Reading a Treemap

1. **Largest rectangles** = largest modules. Attack these first.
2. **node_modules** section: identify heavy dependencies. Question each one.
3. **Duplicate modules**: same library appearing in multiple chunks. Configure shared chunk extraction.
4. **Unexpected inclusions**: modules you did not import directly. Trace the import chain.

## Dependency Auditing

### The Replacement Checklist

Before adding a dependency, check:

1. **Size**: What is the minified + gzipped cost? Check bundlephobia.com.
2. **Tree-shakeable**: Does it export ESM? Does it set `sideEffects: false`?
3. **Alternatives**: Can a native API replace it?
4. **Usage scope**: Is it used in one place or throughout the app?

### Common Heavy Dependencies and Alternatives

| Heavy Library | Size (min+gz) | Alternative | Size (min+gz) |
| --- | --- | --- | --- |
| `moment` | 72 KB | `date-fns` (tree-shakeable) | 2-8 KB (per function) |
| `lodash` | 71 KB | `lodash-es` (tree-shakeable) | 1-3 KB (per function) |
| `lodash` | 71 KB | Native JS (Array methods, structuredClone) | 0 KB |
| `axios` | 13 KB | Native `fetch` | 0 KB |
| `classnames` | 1 KB | Template literals or `clsx` | 0.5 KB |
| `uuid` | 3 KB | `crypto.randomUUID()` | 0 KB |
| `numeral` | 16 KB | `Intl.NumberFormat` | 0 KB |

### Detecting Duplicates

```bash
# Webpack: check for duplicate versions of the same package
npx webpack --stats-modules-space 999 | grep -E "^\s+.*node_modules"

# npm: list duplicate dependencies
npm ls --all | grep -E "deduped|UNMET"

# pnpm: why is a package included?
pnpm why <package-name>
```

## Performance Budgets

### Defining Budgets

| Budget Type | Metric | Recommended |
| --- | --- | --- |
| Total JS (compressed) | Transfer size | < 200 KB |
| Total CSS (compressed) | Transfer size | < 50 KB |
| Largest single chunk | Transfer size | < 100 KB |
| Total page weight | Transfer size | < 500 KB |
| Third-party JS | Transfer size | < 50 KB |
| Main thread JS execution | Time | < 2s on mid-tier mobile |

### Enforcing in CI with size-limit

```json
// package.json
{
  "size-limit": [
    { "path": "dist/assets/*.js", "limit": "200 KB", "gzip": true },
    { "path": "dist/assets/*.css", "limit": "50 KB", "gzip": true },
    { "path": "dist/assets/index-*.js", "limit": "80 KB", "gzip": true }
  ]
}
```

```bash
npx size-limit
```

Integrate into CI: fail the build if any budget is exceeded.

### Enforcing with Bundler Limits

```javascript
// webpack.config.js
module.exports = {
  performance: {
    maxAssetSize: 200 * 1024,     // 200 KB per asset
    maxEntrypointSize: 300 * 1024, // 300 KB per entry
    hints: 'error',                // Fail build on violation
  },
};
```

## Advanced: Differential Serving

Serve modern bundles to modern browsers, legacy bundles to old browsers.

```html
<!-- Modern browsers: smaller, faster -->
<script type="module" src="/app.modern.js"></script>

<!-- Legacy browsers: polyfills included -->
<script nomodule src="/app.legacy.js"></script>
```

Modern bundles skip transpilation of async/await, optional chaining, nullish coalescing, and other modern syntax. This saves 10-20% bundle size.

### Browserslist Configuration

```
# .browserslistrc
# Modern: targets for type="module" browsers
[modern]
last 2 Chrome versions
last 2 Firefox versions
last 2 Safari versions
last 2 Edge versions

# Legacy: IE11 and older
[legacy]
> 0.5%
not dead
IE 11
```

## Monitoring Bundle Size Over Time

Track bundle sizes across commits. Alert on regressions.

```bash
# CI step: record size and compare to baseline
CURRENT=$(stat -f%z dist/assets/index*.js | paste -sd+ | bc)
BASELINE=$(cat .bundle-baseline 2>/dev/null || echo 0)
DIFF=$((CURRENT - BASELINE))

if [ $DIFF -gt 10240 ]; then
  echo "Bundle grew by $((DIFF / 1024)) KB. Investigate."
  exit 1
fi
```

Integrate with GitHub PR comments to surface size changes in code review.
