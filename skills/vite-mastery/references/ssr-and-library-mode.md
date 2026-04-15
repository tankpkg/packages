# SSR and Library Mode

Sources: Vite official documentation (vitejs.dev), Rollup documentation, Vite SSR guide

Covers SSR entry points, externalization strategy, streaming SSR, client hydration,
library mode configuration, external dependencies, multiple output formats, and
CSS extraction for libraries.

## SSR Overview

Vite provides low-level SSR primitives. Frameworks (Nuxt, SvelteKit, Remix) build
on these. Use raw Vite SSR when building a custom framework or when existing
frameworks do not fit.

### SSR Architecture

```
Browser Request
     |
     v
Node.js Server
     |
     +--> vite.ssrLoadModule('./src/entry-server.ts')  [dev]
     |    OR import('./dist/server/entry-server.js')   [prod]
     |
     v
Render HTML string
     |
     v
Inject into index.html template
     |
     v
Send to browser
     |
     v
Browser loads client bundle -> hydration
```

### Project Structure for SSR

```
src/
  entry-client.ts    <- browser entry (hydration)
  entry-server.ts    <- server entry (renderToString)
  App.tsx            <- shared application root
  pages/
server.ts            <- Node.js HTTP server
index.html           <- HTML template with placeholders
vite.config.ts
```

## SSR Entry Points

### Server Entry

```ts
// src/entry-server.ts
import { renderToString } from 'react-dom/server'
import { App } from './App'

export async function render(url: string) {
  const html = renderToString(<App url={url} />)
  return { html }
}
```

### Client Entry

```ts
// src/entry-client.ts
import { hydrateRoot } from 'react-dom/client'
import { App } from './App'

hydrateRoot(document.getElementById('app')!, <App url={window.location.pathname} />)
```

### HTML Template

```html
<!DOCTYPE html>
<html>
  <head><!--head-tags--></head>
  <body>
    <div id="app"><!--app-html--></div>
    <script type="module" src="/src/entry-client.ts"></script>
  </body>
</html>
```

## Development Server for SSR

Use `vite.createServer` in middleware mode:

```ts
import express from 'express'
import { createServer as createViteServer } from 'vite'

async function startServer() {
  const app = express()

  const vite = await createViteServer({
    server: { middlewareMode: true },
    appType: 'custom', // disable Vite's built-in HTML serving
  })

  // Use Vite's middleware for HMR and module serving
  app.use(vite.middlewares)

  app.use('*', async (req, res) => {
    const url = req.originalUrl

    // 1. Read and transform the HTML template
    let template = await fs.readFile('index.html', 'utf-8')
    template = await vite.transformIndexHtml(url, template)

    // 2. Load the server entry module (with HMR support)
    const { render } = await vite.ssrLoadModule('/src/entry-server.ts')

    // 3. Render the app
    const { html: appHtml } = await render(url)

    // 4. Inject into template
    const html = template.replace('<!--app-html-->', appHtml)

    res.status(200).set({ 'Content-Type': 'text/html' }).end(html)
  })

  app.listen(3000)
}

startServer()
```

`vite.ssrLoadModule` loads modules through Vite's transform pipeline with HMR
support. Changes to any module trigger instant updates without server restart.

## SSR Externalization

In SSR mode, Vite externalizes dependencies by default (they are `require`d at
runtime instead of bundled). Configure exceptions:

```ts
export default defineConfig({
  ssr: {
    // Force-bundle these packages (needed for ESM-only deps)
    noExternal: [
      'my-esm-only-package',
      /^@my-scope\/.*/,  // regex matching
    ],

    // Force-externalize (override noExternal)
    external: [
      'legacy-cjs-package',
    ],

    // SSR build target
    target: 'node', // 'node' | 'webworker'
  },
})
```

### When to Use noExternal

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ERR_REQUIRE_ESM` during SSR | CJS server trying to require ESM package | Add to `ssr.noExternal` |
| CSS import fails in SSR | External package has CSS imports | Add to `ssr.noExternal` |
| Package uses `import.meta` | Not supported in CJS context | Add to `ssr.noExternal` |
| Browser-only APIs in SSR | Package references `window`/`document` | Guard with `typeof window` checks |

## Streaming SSR

Use `renderToPipeableStream` (React) or equivalent for streaming:

```ts
// src/entry-server.ts (React streaming)
import { renderToPipeableStream } from 'react-dom/server'
import { App } from './App'

export function render(url: string, res: ServerResponse) {
  const { pipe } = renderToPipeableStream(<App url={url} />, {
    onShellReady() {
      res.statusCode = 200
      res.setHeader('Content-Type', 'text/html')
      pipe(res)
    },
    onError(error) {
      console.error(error)
      res.statusCode = 500
      res.end('Internal Server Error')
    },
  })
}
```

### SSR Production Build

```ts
// vite.config.ts
export default defineConfig({
  build: {
    ssr: true,
    rollupOptions: {
      input: 'src/entry-server.ts',
    },
  },
})
```

Or use two separate builds:

```bash
# Build client
vite build --outDir dist/client

# Build server
vite build --outDir dist/server --ssr src/entry-server.ts
```

## Library Mode

Build reusable libraries with `build.lib`:

```ts
import { resolve } from 'path'
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'MyLib',        // global variable name for UMD/IIFE
      fileName: 'my-lib',   // output file name (without extension)
      formats: ['es', 'cjs'], // output formats
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'react/jsx-runtime'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
      },
    },
  },
})
```

### Output Formats

| Format | Extension | Use Case |
| --- | --- | --- |
| `es` | `.mjs` | Modern bundlers, ESM environments |
| `cjs` | `.cjs` | Node.js, legacy bundlers |
| `umd` | `.umd.js` | Browser `<script>` tags, AMD loaders |
| `iife` | `.iife.js` | Direct browser inclusion |

### Multiple Entry Points

```ts
export default defineConfig({
  build: {
    lib: {
      entry: {
        index: resolve(__dirname, 'src/index.ts'),
        utils: resolve(__dirname, 'src/utils.ts'),
        hooks: resolve(__dirname, 'src/hooks/index.ts'),
      },
      formats: ['es', 'cjs'],
    },
  },
})
```

### package.json for Libraries

Configure entry points for consumers:

```json
{
  "name": "my-lib",
  "version": "1.0.0",
  "type": "module",
  "main": "./dist/my-lib.cjs",
  "module": "./dist/my-lib.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/my-lib.mjs",
      "require": "./dist/my-lib.cjs",
      "types": "./dist/index.d.ts"
    },
    "./utils": {
      "import": "./dist/utils.mjs",
      "require": "./dist/utils.cjs",
      "types": "./dist/utils.d.ts"
    }
  },
  "files": ["dist"],
  "sideEffects": false
}
```

### External Dependencies

Externalize everything that consumers will provide. The library should not bundle
peer dependencies or framework runtimes:

```ts
export default defineConfig({
  build: {
    rollupOptions: {
      external: [
        'react',
        'react-dom',
        'react/jsx-runtime',
        /^@radix-ui/,     // regex for scoped packages
      ],
    },
  },
})
```

Rule: If it is in `peerDependencies`, it must be in `external`.

### CSS Handling in Libraries

By default, CSS is injected via JS. For libraries, extract CSS to a separate file:

```ts
export default defineConfig({
  build: {
    lib: { /* ... */ },
    cssCodeSplit: false, // combine all CSS into one file
  },
})
```

Consumers import the CSS separately:

```ts
import 'my-lib/dist/style.css'
import { Button } from 'my-lib'
```

For CSS Modules or CSS-in-JS, the styles are typically bundled with the component
and no separate import is needed.

### Type Generation

Vite does not generate `.d.ts` files. Use one of:

```bash
# tsc directly
tsc --emitDeclarationOnly --outDir dist

# vite-plugin-dts (recommended)
npm i -D vite-plugin-dts
```

```ts
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [dts({ rollupTypes: true })],
  build: {
    lib: { /* ... */ },
  },
})
```

`rollupTypes: true` bundles all declarations into a single `.d.ts` file.

## Library Mode Checklist

Before publishing a library built with Vite:

1. All peer dependencies are listed in `external`.
2. `package.json` exports map is correct for all formats.
3. `types` field points to generated `.d.ts` files.
4. `sideEffects` field is set (usually `false`, or `["*.css"]` if CSS exists).
5. CSS is extracted (not injected via JS) unless using CSS-in-JS.
6. Tree-shaking works: verify with a test consumer project.
7. Bundle does not include React/Vue/framework runtime.
8. Source maps are generated (`sourcemap: true`).

## SSR vs Library Mode Comparison

| Aspect | SSR Mode | Library Mode |
| --- | --- | --- |
| Purpose | Server-rendered application | Reusable npm package |
| Entry config | `build.ssr` or `--ssr` flag | `build.lib` |
| Externals | Auto-externalized node_modules | Manual via `rollupOptions.external` |
| Output | Single server bundle | Multiple formats (ESM, CJS, UMD) |
| CSS | Injected or collected | Extracted to separate file |
| Types | Not needed (internal) | Required (public API) |
| HTML | Template-based injection | Not applicable |
