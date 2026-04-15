# Plugin Development

Sources: Vite official documentation (vitejs.dev), Rollup documentation, Vite plugin API reference

Covers Vite plugin anatomy, Rollup-compatible hooks, Vite-specific hooks, virtual
modules, the transform pipeline, enforce ordering, HMR API, and plugin testing.

## Plugin Anatomy

A Vite plugin is an object with a `name` and one or more hooks. It extends Rollup's
plugin interface with Vite-specific additions.

```ts
import type { Plugin } from 'vite'

function myPlugin(options?: { debug?: boolean }): Plugin {
  return {
    name: 'vite-plugin-my-plugin', // required, used in warnings and errors
    enforce: 'pre', // optional: 'pre' | 'post' (default: normal)
    apply: 'build', // optional: 'build' | 'serve' (default: both)

    // Vite-specific hooks
    config(config, env) { /* modify config */ },
    configResolved(config) { /* read final config */ },
    configureServer(server) { /* add dev middleware */ },
    transformIndexHtml(html) { /* modify index.html */ },
    handleHotUpdate(ctx) { /* custom HMR handling */ },

    // Rollup-compatible hooks
    resolveId(source, importer) { /* resolve imports */ },
    load(id) { /* provide module content */ },
    transform(code, id) { /* transform module code */ },
  }
}

export default myPlugin
```

### Plugin Naming Convention

Use the prefix `vite-plugin-` for npm packages. For framework-specific plugins,
use `vite-plugin-vue-`, `vite-plugin-react-`, etc.

## Hook Execution Order

### Build Pipeline

```
1. config            (Vite: modify config before resolution)
2. configResolved    (Vite: read final resolved config)
3. options           (Rollup: modify Rollup options)
4. buildStart        (Rollup: build has started)
5. resolveId         (Rollup: resolve each import)
6. load              (Rollup: load module content)
7. transform         (Rollup: transform module code)
8. buildEnd          (Rollup: build has finished)
9. closeBundle       (Rollup: bundle is written)
```

### Dev Server Pipeline

```
1. config
2. configResolved
3. configureServer   (Vite: add dev server middleware)
4. buildStart
5. transformIndexHtml (Vite: on each HTML request)
6. resolveId -> load -> transform (on each module request)
7. handleHotUpdate   (Vite: on file change)
```

## Enforce Ordering

Plugins run in this order:

1. Alias resolution (Vite internal)
2. Plugins with `enforce: 'pre'`
3. Vite core plugins (resolve, CSS, esbuild transform)
4. Plugins without `enforce` (normal)
5. Vite build plugins (minify, manifest, reporting)
6. Plugins with `enforce: 'post'`

| Use Case | Enforce |
| --- | --- |
| Need to run before all transforms (raw source) | `'pre'` |
| Default behavior, after Vite core | omit (normal) |
| Need to process final output | `'post'` |
| Only during dev | `apply: 'serve'` |
| Only during build | `apply: 'build'` |

```ts
function myPrePlugin(): Plugin {
  return {
    name: 'my-pre-plugin',
    enforce: 'pre',
    transform(code, id) {
      // Runs before Vite's own transforms
      // `code` is the raw source
    },
  }
}
```

## Vite-Specific Hooks

### config

Modify the Vite config before it is resolved. Return a partial config to merge:

```ts
config(config, { command, mode }) {
  if (command === 'build') {
    return {
      build: {
        sourcemap: true,
      },
    }
  }
}
```

### configResolved

Read the final, resolved config. Do not mutate it. Store references for later hooks:

```ts
let resolvedConfig: ResolvedConfig

configResolved(config) {
  resolvedConfig = config
}
```

### configureServer

Add custom middleware to the dev server. The `server` object exposes the
Connect middleware stack:

```ts
configureServer(server) {
  // Runs before Vite's internal middleware
  server.middlewares.use((req, res, next) => {
    if (req.url === '/api/mock') {
      res.end(JSON.stringify({ data: 'mock' }))
    } else {
      next()
    }
  })
}
```

Return a function to add middleware AFTER Vite's internals (post-middleware):

```ts
configureServer(server) {
  return () => {
    server.middlewares.use((req, res, next) => {
      // Runs after Vite serves static files
      // Useful for SPA fallback
    })
  }
}
```

### transformIndexHtml

Transform the `index.html` file. Receives the HTML string and returns
modified HTML or an array of tag descriptors:

```ts
transformIndexHtml(html, ctx) {
  return html.replace('__TITLE__', 'My App')
}

// Or inject tags:
transformIndexHtml() {
  return [
    {
      tag: 'script',
      attrs: { src: '/analytics.js', defer: true },
      injectTo: 'head',
    },
    {
      tag: 'meta',
      attrs: { name: 'version', content: '1.0.0' },
      injectTo: 'head-prepend',
    },
  ]
}
```

Injection positions: `'head'`, `'head-prepend'`, `'body'`, `'body-prepend'`.

### handleHotUpdate

Custom HMR logic when files change:

```ts
handleHotUpdate({ file, server, modules, timestamp }) {
  if (file.endsWith('.custom')) {
    // Notify all connected clients
    server.ws.send({
      type: 'custom',
      event: 'custom-update',
      data: { file, timestamp },
    })
    return [] // prevent default HMR for this file
  }
  // Return undefined to use default HMR behavior
}
```

## Virtual Modules

Virtual modules exist only in memory. Use the `\0` prefix convention to signal
that a module is virtual (prevents other plugins from resolving it):

```ts
const VIRTUAL_MODULE_ID = 'virtual:my-config'
const RESOLVED_VIRTUAL_ID = '\0' + VIRTUAL_MODULE_ID

function virtualConfigPlugin(data: Record<string, unknown>): Plugin {
  return {
    name: 'virtual-config',
    resolveId(id) {
      if (id === VIRTUAL_MODULE_ID) {
        return RESOLVED_VIRTUAL_ID
      }
    },
    load(id) {
      if (id === RESOLVED_VIRTUAL_ID) {
        return `export default ${JSON.stringify(data)}`
      }
    },
  }
}
```

Usage in application code:

```ts
import config from 'virtual:my-config'
console.log(config) // the data object
```

Add type declarations:

```ts
// src/vite-env.d.ts or env.d.ts
declare module 'virtual:my-config' {
  const config: Record<string, unknown>
  export default config
}
```

### Dynamic Virtual Modules

Generate content based on the file system or external data:

```ts
function routeManifestPlugin(): Plugin {
  return {
    name: 'route-manifest',
    resolveId(id) {
      if (id === 'virtual:routes') return '\0virtual:routes'
    },
    async load(id) {
      if (id === '\0virtual:routes') {
        const files = await glob('src/pages/**/*.tsx')
        const routes = files.map(f => ({
          path: fileToRoutePath(f),
          component: f,
        }))
        return `export default ${JSON.stringify(routes)}`
      }
    },
  }
}
```

## Transform Pipeline

The `transform` hook processes every module. It receives source code and must
return transformed code (or null to skip):

```ts
transform(code, id) {
  // Only process specific files
  if (!id.endsWith('.md')) return null

  const html = markdownToHtml(code)
  return {
    code: `export default ${JSON.stringify(html)}`,
    map: null, // provide source map if possible
  }
}
```

### Filtering Modules

Use `createFilter` from `@rollup/pluginutils` for efficient include/exclude:

```ts
import { createFilter } from '@rollup/pluginutils'

function myTransformPlugin(opts?: { include?: string[]; exclude?: string[] }): Plugin {
  const filter = createFilter(opts?.include ?? ['**/*.custom'], opts?.exclude)

  return {
    name: 'my-transform',
    transform(code, id) {
      if (!filter(id)) return null
      return transformCustomSyntax(code)
    },
  }
}
```

### Source Maps

Always provide source maps when transforming code. Use `magic-string` for
efficient string manipulation with automatic source map generation:

```ts
import MagicString from 'magic-string'

transform(code, id) {
  if (!id.endsWith('.ts')) return null

  const s = new MagicString(code)
  s.replace('__TIMESTAMP__', Date.now().toString())

  return {
    code: s.toString(),
    map: s.generateMap({ hires: true }),
  }
}
```

## HMR API (Client-Side)

Modules can accept their own updates using `import.meta.hot`:

```ts
if (import.meta.hot) {
  import.meta.hot.accept((newModule) => {
    // Handle the updated module
    if (newModule) {
      updateUI(newModule.default)
    }
  })

  // Cleanup before module is replaced
  import.meta.hot.dispose(() => {
    clearInterval(timer)
  })

  // Store state across HMR updates
  import.meta.hot.data.count = import.meta.hot.data.count ?? 0

  // Listen for custom events from plugins
  import.meta.hot.on('custom-update', (data) => {
    console.log('Custom update:', data)
  })
}
```

### HMR Guard Pattern

Wrap HMR code so it is tree-shaken in production:

```ts
if (import.meta.hot) {
  // This entire block is removed in production builds
}
```

## Plugin Testing

### Unit Testing Hooks

Test individual hooks by calling them directly:

```ts
import { describe, it, expect } from 'vitest'
import myPlugin from './my-plugin'

describe('myPlugin', () => {
  const plugin = myPlugin({ debug: true })

  it('resolves virtual module', () => {
    const result = (plugin.resolveId as Function)('virtual:my-config', undefined)
    expect(result).toBe('\0virtual:my-config')
  })

  it('loads virtual module content', () => {
    const result = (plugin.load as Function)('\0virtual:my-config')
    expect(result).toContain('export default')
  })

  it('ignores non-virtual imports', () => {
    const result = (plugin.resolveId as Function)('./real-file.ts', undefined)
    expect(result).toBeUndefined()
  })
})
```

### Integration Testing with Vite

Use `vite.build` programmatically:

```ts
import { build } from 'vite'

it('produces expected output', async () => {
  const result = await build({
    root: fixture('basic'),
    plugins: [myPlugin()],
    build: { write: false },
  })

  const output = (result as any).output[0]
  expect(output.code).toContain('expected-string')
})
```

## Plugin Composition

Plugins can return arrays for logical grouping:

```ts
function myFrameworkPlugin(): Plugin[] {
  return [
    myResolvePlugin(),
    myTransformPlugin(),
    myDevServerPlugin(),
  ]
}
```

Vite flattens nested arrays in the plugins config, so this works seamlessly.
