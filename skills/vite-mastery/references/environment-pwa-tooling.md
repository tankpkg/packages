# Environment, PWA, and Tooling Integration

Sources: Vite official documentation (vitejs.dev), vite-plugin-pwa documentation, Workbox documentation, rollup-plugin-visualizer documentation

Covers .env files, import.meta.env, mode-based configuration, environment
validation, vite-plugin-pwa setup, workbox caching strategies, offline support,
bundle analysis with rollup-plugin-visualizer, and optimizeDeps tuning.

## Environment Variables

### .env File Hierarchy

Vite loads `.env` files in this order (later files override earlier):

```
.env                  <- always loaded
.env.local            <- always loaded, gitignored
.env.[mode]           <- loaded for specific mode
.env.[mode].local     <- loaded for specific mode, gitignored
```

Default modes: `development` (vite serve), `production` (vite build).
Custom modes: `vite build --mode staging` loads `.env.staging`.

### Client-Side Variables

Only variables prefixed with `VITE_` are exposed to client code:

```bash
# .env
VITE_API_URL=https://api.example.com
VITE_APP_TITLE=My App
SECRET_KEY=never-exposed           # NOT available in client code
DATABASE_URL=postgres://...        # NOT available in client code
```

Access in code:

```ts
const apiUrl = import.meta.env.VITE_API_URL    // "https://api.example.com"
const mode = import.meta.env.MODE              // "development" | "production"
const isProd = import.meta.env.PROD            // boolean
const isDev = import.meta.env.DEV              // boolean
const baseUrl = import.meta.env.BASE_URL       // from `base` config
const ssrFlag = import.meta.env.SSR            // boolean (true during SSR)
```

### TypeScript Support

Augment the `ImportMeta` interface for type safety:

```ts
// src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_FEATURE_FLAGS: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

### Environment Variable Validation

Validate env vars at build time to catch missing configuration early:

```ts
// src/env.ts
function getEnvVar(key: string): string {
  const value = import.meta.env[key]
  if (value === undefined) {
    throw new Error(`Missing required environment variable: ${key}`)
  }
  return value
}

export const env = {
  apiUrl: getEnvVar('VITE_API_URL'),
  appTitle: getEnvVar('VITE_APP_TITLE'),
} as const
```

For schema-based validation, use `@t3-oss/env-core` or `zod`:

```ts
import { z } from 'zod'

const envSchema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_APP_TITLE: z.string().min(1),
  VITE_FEATURE_FLAGS: z.string().transform(s => s.split(',')),
})

export const env = envSchema.parse(import.meta.env)
```

### Server-Side Environment Variables

In SSR or server routes, access all env vars via `process.env` (no `VITE_` prefix
required for server-only code):

```ts
// server.ts (not bundled by Vite client build)
const dbUrl = process.env.DATABASE_URL
const secret = process.env.SECRET_KEY
```

### Custom Env Prefix

Change the prefix from `VITE_` to something else:

```ts
export default defineConfig({
  envPrefix: 'APP_', // exposes APP_* variables instead of VITE_*
})
```

Multiple prefixes:

```ts
export default defineConfig({
  envPrefix: ['VITE_', 'APP_'],
})
```

### Mode-Based Configuration Pattern

```ts
// vite.config.ts
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory
  const env = loadEnv(mode, process.cwd(), '')

  return {
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL),
    },
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_URL,
          changeOrigin: true,
        },
      },
    },
  }
})
```

`loadEnv(mode, root, prefix)` loads env files and returns an object.
Pass `''` as prefix to load ALL variables (not just `VITE_*`).

## PWA with vite-plugin-pwa

### Installation and Basic Setup

```bash
npm i -D vite-plugin-pwa
```

```ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate', // auto-update service worker
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'mask-icon.svg'],
      manifest: {
        name: 'My App',
        short_name: 'App',
        description: 'My application description',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        scope: '/',
        start_url: '/',
        icons: [
          { src: 'pwa-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: 'pwa-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
    }),
  ],
})
```

### Registration Types

| Type | Behavior | Use Case |
| --- | --- | --- |
| `'autoUpdate'` | New SW activates immediately, page reloads | Most apps |
| `'prompt'` | Shows update prompt, user decides | Apps where data loss on reload is a concern |

### Prompt Registration

```ts
VitePWA({
  registerType: 'prompt',
  // In your app, use the virtual module:
})
```

```ts
// In your application code
import { useRegisterSW } from 'virtual:pwa-register/react'

function App() {
  const {
    needRefresh: [needRefresh],
    updateServiceWorker,
  } = useRegisterSW()

  return (
    <>
      {needRefresh && (
        <div>
          <span>New version available!</span>
          <button onClick={() => updateServiceWorker(true)}>Update</button>
        </div>
      )}
    </>
  )
}
```

### Workbox Caching Strategies

```ts
VitePWA({
  workbox: {
    // Pre-cache app shell
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],

    // Runtime caching for API calls
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/api\.example\.com\/.*/i,
        handler: 'NetworkFirst',
        options: {
          cacheName: 'api-cache',
          expiration: {
            maxEntries: 100,
            maxAgeSeconds: 60 * 60 * 24, // 24 hours
          },
          cacheableResponse: {
            statuses: [0, 200],
          },
        },
      },
      {
        urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
        handler: 'CacheFirst',
        options: {
          cacheName: 'image-cache',
          expiration: {
            maxEntries: 50,
            maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
          },
        },
      },
      {
        urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'google-fonts',
          expiration: {
            maxEntries: 20,
          },
        },
      },
    ],
  },
})
```

### Workbox Strategy Selection

| Strategy | Behavior | Best For |
| --- | --- | --- |
| `CacheFirst` | Cache, fallback to network | Static assets, images, fonts |
| `NetworkFirst` | Network, fallback to cache | API calls, dynamic data |
| `StaleWhileRevalidate` | Cache immediately, update in background | Frequently updated static resources |
| `NetworkOnly` | Network only, no caching | Auth endpoints, real-time data |
| `CacheOnly` | Cache only, no network | Pre-cached app shell |

### Offline Fallback Page

```ts
VitePWA({
  workbox: {
    navigateFallback: '/offline.html',
    navigateFallbackDenylist: [/^\/api/],
  },
})
```

Create `public/offline.html` for the fallback page.

### Development

Enable PWA in dev mode for testing (disabled by default):

```ts
VitePWA({
  devOptions: {
    enabled: true,
    type: 'module',
  },
})
```

## Bundle Analysis

### rollup-plugin-visualizer

```bash
npm i -D rollup-plugin-visualizer
```

```ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    visualizer({
      open: true,             // auto-open in browser
      filename: 'stats.html', // output file
      gzipSize: true,         // show gzipped sizes
      brotliSize: true,       // show brotli sizes
      template: 'treemap',    // 'treemap' | 'sunburst' | 'network'
    }),
  ],
})
```

Run `vite build` to generate the report.

### Alternative: vite-bundle-visualizer

Zero-config alternative:

```bash
npx vite-bundle-visualizer
```

### Reading the Visualizer Output

| Pattern | Meaning | Action |
| --- | --- | --- |
| One huge block | Single large dependency | Consider lazy loading or a lighter alternative |
| Many small blocks | Over-split chunks | Consolidate with manual chunks |
| Duplicate blocks | Same module in multiple chunks | Check manual chunks configuration |
| Unexpected packages | Transitive dependency bloat | Audit with `npm ls <package>` |
| Large polyfills | Legacy browser support | Review `@vitejs/plugin-legacy` targets |

## Dependency Pre-Bundling Tuning

### Force Include

Pre-bundle dependencies that cause issues during dev:

```ts
export default defineConfig({
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'lodash-es',              // many internal modules
      'my-lib > nested-dep',    // nested dependency
    ],
  },
})
```

### Force Exclude

Skip pre-bundling for dependencies that must remain as-is:

```ts
export default defineConfig({
  optimizeDeps: {
    exclude: [
      'my-wasm-package',        // WASM packages
    ],
  },
})
```

### Troubleshooting Pre-Bundling

| Issue | Cause | Fix |
| --- | --- | --- |
| `Pre-bundling re-optimized` on every start | Dynamic imports discovered at runtime | Add discovered deps to `include` |
| CJS module fails | Not pre-bundled | Add to `include` |
| WASM module fails | Pre-bundling strips WASM | Add to `exclude` |
| Linked package not updating | Cached pre-bundle | Run `vite --force` |

### Cache Control

```ts
export default defineConfig({
  cacheDir: 'node_modules/.vite', // default location
  optimizeDeps: {
    force: true, // always re-bundle (slow, use for debugging only)
  },
})
```

Clear cache: delete `node_modules/.vite` or run `vite --force`.

## Performance Profiling Workflow

1. Measure baseline: `time npx vite build` and record the output size.
2. Generate report: add `rollup-plugin-visualizer` and rebuild.
3. Identify targets: look for the largest modules in the treemap.
4. Apply fixes: dynamic imports, manual chunks, lighter alternatives.
5. Verify improvement: rebuild, compare sizes and load times.
6. Monitor ongoing: add size budget checks to CI to prevent regressions.
