# Configuration and Dev Server

Sources: Vite official documentation (vitejs.dev), Rollup documentation, esbuild documentation

Covers vite.config.ts structure, resolve aliases, define constants, conditional
configuration, dev server options, HMR, proxy configuration, HTTPS, and custom middleware.

## Config File Basics

Vite reads `vite.config.ts` (or `.js`, `.mjs`) from the project root. Use `defineConfig`
for type hints.

### Static Config

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: '.', // project root (where index.html lives)
  base: '/', // public base path for deployment
  publicDir: 'public', // static assets copied as-is
  cacheDir: 'node_modules/.vite', // pre-bundling cache
})
```

### Conditional Config (by mode)

Export a function to access `mode`, `command`, and `isSsrBuild`:

```ts
import { defineConfig } from 'vite'

export default defineConfig(({ command, mode, isSsrBuild }) => {
  const isDev = command === 'serve'
  const isProd = mode === 'production'

  return {
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    },
    build: {
      sourcemap: isDev ? 'inline' : false,
      minify: isProd ? 'esbuild' : false,
    },
  }
})
```

`command` is `'serve'` during dev and `'build'` during production build.
`mode` defaults to `'development'` for serve, `'production'` for build.
Override mode with `--mode staging`.

### Async Config

The function can be async for dynamic setup (reading files, network calls):

```ts
export default defineConfig(async ({ mode }) => {
  const secrets = await loadSecrets(mode)
  return {
    define: {
      __API_KEY__: JSON.stringify(secrets.apiKey),
    },
  }
})
```

## Resolve Configuration

### Aliases

Map import paths to filesystem locations:

```ts
import { resolve } from 'path'

export default defineConfig({
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@utils': resolve(__dirname, 'src/utils'),
    },
  },
})
```

For ESM config files where `__dirname` is unavailable:

```ts
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
```

Update `tsconfig.json` paths to match aliases for TypeScript resolution:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"]
    }
  }
}
```

### Resolve Extensions and Conditions

```ts
export default defineConfig({
  resolve: {
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json'], // defaults
    conditions: ['import', 'module', 'browser', 'default'], // package.json conditions
    mainFields: ['browser', 'module', 'jsnext:main', 'jsnext'], // defaults
  },
})
```

## Define: Compile-Time Constants

Replace expressions at build time. Values are inlined as-is, so wrap strings
with `JSON.stringify`:

```ts
export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify('1.2.3'),
    __DEV__: JSON.stringify(true),
    'process.env.NODE_ENV': JSON.stringify('production'), // for legacy libs
    'import.meta.env.CUSTOM': JSON.stringify('value'),
  },
})
```

Access in code: `if (__DEV__) { ... }` -- the expression is replaced at build time,
and dead code is eliminated by the minifier.

## Dev Server Configuration

### Basic Options

```ts
export default defineConfig({
  server: {
    host: '0.0.0.0',     // expose to network (default: 'localhost')
    port: 3000,           // default: 5173
    strictPort: true,     // fail if port taken (default: false, auto-increment)
    open: true,           // open browser on start
    cors: true,           // enable CORS
  },
})
```

### Proxy Configuration

Route API requests to a backend server to avoid CORS during development:

```ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8080',
        ws: true,
      },
      // Regex-based matching
      '^/api/v[12]/.*': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
```

`changeOrigin: true` rewrites the `Host` header to match the target, required
for virtual-hosted backends.

### HTTPS

```ts
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [basicSsl()],
  server: {
    https: true,
  },
})
```

For custom certificates:

```ts
import fs from 'fs'

export default defineConfig({
  server: {
    https: {
      key: fs.readFileSync('certs/localhost-key.pem'),
      cert: fs.readFileSync('certs/localhost.pem'),
    },
  },
})
```

Generate local certs with `mkcert`: `mkcert -install && mkcert localhost`.

### HMR Configuration

HMR works automatically with framework plugins. Custom HMR config is needed
when behind a reverse proxy or in containers:

```ts
export default defineConfig({
  server: {
    hmr: {
      protocol: 'ws',       // 'ws' or 'wss'
      host: 'localhost',
      port: 5173,
      clientPort: 443,       // when behind reverse proxy
      overlay: true,         // show error overlay (default: true)
    },
  },
})
```

### HMR Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| Full page reload instead of HMR | Module not accepting updates | Ensure framework plugin is loaded |
| HMR timeout | Firewall/proxy blocking WebSocket | Configure `server.hmr.clientPort` and `protocol` |
| Changes not detected | File outside project root | Move file or configure `server.watch.paths` |
| Circular dependency breaks HMR | Propagation cannot resolve cycle | Break the circular import |
| CSS changes cause full reload | CSS module imported conditionally | Import CSS statically at module top level |

### Custom Middleware

Use `configureServer` hook in a plugin to add Express-compatible middleware:

```ts
function apiMockPlugin(): Plugin {
  return {
    name: 'api-mock',
    configureServer(server) {
      server.middlewares.use('/api/health', (req, res) => {
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ status: 'ok' }))
      })
    },
  }
}
```

### File System Watching

```ts
export default defineConfig({
  server: {
    watch: {
      usePolling: true,    // needed for Docker/WSL
      interval: 1000,      // polling interval in ms
      ignored: ['**/node_modules/**', '**/.git/**'],
    },
  },
})
```

## Dependency Pre-Bundling (optimizeDeps)

Vite pre-bundles dependencies with esbuild during dev for two reasons:
1. Convert CJS to ESM
2. Consolidate many small modules into one request

### Configuration

```ts
export default defineConfig({
  optimizeDeps: {
    include: [
      'lodash-es',           // force pre-bundle ESM deps
      'react',               // force pre-bundle for faster dev startup
      'linked-dep > nested', // pre-bundle nested dep of a linked package
    ],
    exclude: [
      'my-local-package',    // skip pre-bundling (must be valid ESM)
    ],
    esbuildOptions: {
      target: 'esnext',
      plugins: [],           // esbuild plugins for pre-bundling
    },
  },
})
```

### When to Use

| Symptom | Action |
| --- | --- |
| CJS dependency fails in browser | Add to `include` |
| Linked local package rebuilds slowly | Add to `exclude` |
| Dependency has many internal modules (lodash-es) | Add to `include` to reduce requests |
| Pre-bundling keeps re-running on start | Check for non-deterministic imports; pin with `include` |

### Force Re-optimization

Delete `node_modules/.vite` or run `vite --force` to clear the pre-bundle cache.

## Multi-Page Configuration

```ts
import { resolve } from 'path'

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        admin: resolve(__dirname, 'admin/index.html'),
        login: resolve(__dirname, 'login/index.html'),
      },
    },
  },
})
```

Each HTML entry point gets its own chunk tree.

## Project Structure Conventions

```
project-root/
  index.html          <- entry point (must be in root)
  public/             <- static assets (copied as-is, no processing)
  src/
    main.ts           <- application entry
    assets/            <- processed assets (images, fonts imported in code)
    components/
  vite.config.ts
  .env                <- default env
  .env.local          <- local overrides (gitignored)
  .env.production     <- production env
```

`index.html` is the true entry point. Vite resolves `<script type="module" src="/src/main.ts">`
from it. This is fundamentally different from Webpack where a JS file is the entry.
