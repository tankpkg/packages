# Deployment and Configuration

Sources: TanStack Start official docs, Nitro v3 docs, Vercel docs, Cloudflare Workers docs, Netlify docs, Bun docs

## Build System: Vite + Nitro

TanStack Start replaces Next.js's Webpack/Turbopack pipeline with Vite for development and building, and Nitro for universal server output. The Vinxi build layer was dropped in v1.120 (mid-2025) in favor of direct Vite and Nitro plugins.

Current build pipeline:

```
TanStack Start → tanstackStart() Vite plugin → nitro() Vite plugin → Vite 7 → .output/
```

Nitro abstracts all deployment platform differences via H3. The same application code deploys to Node.js, Cloudflare Workers, AWS Lambda, Deno, and Bun without modification — only the build preset changes.

---

## vite.config.ts

`vite.config.ts` replaces `next.config.js` as the central build configuration file.

Standard configuration:

```ts
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { defineConfig } from 'vite'
import tsConfigPaths from 'vite-tsconfig-paths'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { nitro } from 'nitro/vite'

export default defineConfig({
  server: { port: 3000 },
  plugins: [
    tailwindcss(),
    tsConfigPaths({ projects: ['./tsconfig.json'] }),
    tanstackStart({ srcDirectory: 'src' }),
    viteReact(),
    nitro(),
  ],
})
```

Plugin order matters: `tanstackStart()` before `viteReact()`, `nitro()` last.

### next.config.js Feature Mapping

| next.config.js feature | TanStack Start equivalent |
|------------------------|--------------------------|
| `images.domains` | Configure in `@unpic/react` or CDN directly |
| `redirects()` | `redirect()` call inside route `beforeLoad` |
| `rewrites()` | Vite `server.proxy` or server middleware |
| `headers()` | Server middleware or hosting platform config |
| `env` / `publicRuntimeConfig` | Vite `import.meta.env` with `VITE_` prefix |
| `basePath` | Vite `base` option |
| `i18n` | Manual routing with `$locale` path parameter |
| `output: 'standalone'` | Node.js server preset (default) |
| `output: 'export'` | `spa.enabled: true` or `prerender.enabled: true` |
| `webpack()` customization | Vite `plugins` array or `optimizeDeps` |
| `transpilePackages` | Vite handles ESM natively; no equivalent needed |
| `experimental.serverActions` | `createServerFn()` — stable, not experimental |

---

## package.json

```json
{
  "type": "module",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build && tsc --noEmit",
    "preview": "vite preview",
    "start": "node .output/server/index.mjs"
  }
}
```

`"type": "module"` is required. TanStack Start is ESM-first; CommonJS interop is not supported.

### Core Dependencies

```json
{
  "dependencies": {
    "@tanstack/react-router": "^1.167.x",
    "@tanstack/react-start": "^1.166.x",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.6.0",
    "nitro": "^3.0.x-beta",
    "typescript": "^5.7.x",
    "vite": "^7.3.x",
    "vite-tsconfig-paths": "^5.x"
  }
}
```

React 19 is required. TanStack Start uses React 19 APIs including `use()`, `useOptimistic()`, and form actions. React 18 will produce build errors.

---

## tsconfig.json

```json
{
  "compilerOptions": {
    "strict": true,
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "target": "ES2022",
    "baseUrl": ".",
    "paths": { "~/*": ["./src/*"] },
    "noEmit": true
  }
}
```

Use `"moduleResolution": "Bundler"` — not `"node16"` or `"nodenext"`. Bundler mode matches Vite's module resolution and avoids false TypeScript errors on bare specifier imports. Set `"noEmit": true` because Vite handles transpilation; TypeScript is type-checking only.

---

## Deployment Targets via Nitro Presets

Nitro presets are the mechanism for targeting different deployment platforms. The application code does not change between targets — only the preset changes at build time.

### Setting a Preset

**Method 1 — environment variable (recommended for CI/CD):**

```bash
NITRO_PRESET=vercel vite build
```

**Method 2 — config (for fixed targets):**

```ts
nitro({ preset: 'aws-lambda' })
```

Auto-detected platforms require no configuration. When building inside Vercel, Netlify, Cloudflare, AWS Amplify, Azure, or Firebase App Hosting, Nitro detects the platform and applies the correct preset automatically.

### Preset Reference

| Platform | Preset | Notes |
|----------|--------|-------|
| Node.js (default) | `node-server` | `node .output/server/index.mjs` |
| Bun | `bun` | `bun .output/server/index.mjs` |
| Deno | `deno` | Deno Deploy compatible |
| Vercel | `vercel` | Zero-config; auto-detected in CI |
| Cloudflare Workers | Use `@cloudflare/vite-plugin` | Preferred over Nitro preset |
| Cloudflare Pages | `cloudflare-pages` | |
| Netlify | Use `@netlify/vite-plugin-tanstack-start` | First-party plugin |
| AWS Lambda | `aws-lambda` | |
| AWS Lambda Streaming | `aws-lambda-streaming` | For streaming responses |
| Azure Functions | `azure-functions` | |
| Firebase App Hosting | `firebase` | |
| Deno Deploy | `deno-deploy` | |
| DigitalOcean App Platform | `digitalocean` | |
| Fly.io | `node-server` in Docker | No native preset; use Node |
| Railway | `node-server` | No native preset; use Node |

### Platform Comparison: TanStack Start vs Next.js

| Platform | TanStack Start | Next.js |
|----------|---------------|---------|
| Vercel | First-class, auto-detected | Native (Vercel owns Next.js) |
| Cloudflare Workers | First-class via `@cloudflare/vite-plugin` | Edge runtime only; partial support |
| Netlify | First-class via `@netlify/vite-plugin-tanstack-start` | Adapter required |
| AWS Lambda | Nitro preset, no third-party adapter | Requires OpenNext |
| Self-hosted Node.js | Native, `node .output/server/index.mjs` | `next start` |
| Bun | Nitro `bun` preset | Limited; not officially supported |
| Deno | Nitro `deno` preset | Not supported |
| Docker | Node preset in any base image | Supported via standalone output |

---

## Platform-Specific Configurations

### Vercel

No configuration required when deploying from a Vercel-connected Git repository. Nitro auto-detects the environment and applies the `vercel` preset. For manual builds:

```bash
NITRO_PRESET=vercel vite build
```

Output is placed in `.vercel/output/` in the Vercel-compatible format.

### Cloudflare Workers

Cloudflare Workers uses `@cloudflare/vite-plugin` rather than a Nitro preset. The plugin integrates the Cloudflare workerd runtime into the Vite dev server for accurate local emulation.

```bash
npm install --save-dev @cloudflare/vite-plugin
```

`vite.config.ts`:

```ts
import { cloudflare } from '@cloudflare/vite-plugin'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { defineConfig } from 'vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    cloudflare({ viteEnvironment: { name: 'ssr' } }),
    tanstackStart(),
    viteReact(),
  ],
})
```

`wrangler.jsonc`:

```jsonc
{
  "name": "my-app",
  "compatibility_date": "2026-03-17",
  "compatibility_flags": ["nodejs_compat"],
  "main": "@tanstack/react-start/server-entry"
}
```

The `nodejs_compat` flag enables Node.js API compatibility in the Workers runtime. Deploy with `npx wrangler deploy`.

### Netlify

```bash
npm install --save-dev @netlify/vite-plugin-tanstack-start
```

`vite.config.ts`:

```ts
import { netlify } from '@netlify/vite-plugin-tanstack-start'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { defineConfig } from 'vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    netlify(),
    tanstackStart(),
    viteReact(),
  ],
})
```

No `netlify.toml` is required. The plugin handles output directory configuration automatically.

### Bun

To use Bun as the runtime (not just the package manager), update scripts and set the preset:

```json
{
  "scripts": {
    "dev": "bun --bun vite dev",
    "build": "NITRO_PRESET=bun bun --bun vite build",
    "start": "bun .output/server/index.mjs"
  }
}
```

The `--bun` flag forces Bun's runtime for the Vite process itself.

### Docker (Node.js)

Use the default `node-server` preset. Minimal multi-stage Dockerfile:

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
```

`.output/` is self-contained — no `node_modules` needed at runtime.

---

## Environment Variables

TanStack Start uses Vite's standard environment variable system, which differs from Next.js in both prefix convention and access method.

### Access by Context

| Context | Access method | Scope |
|---------|--------------|-------|
| Server functions (`createServerFn`) | `process.env.MY_VAR` | All variables |
| Client-side components | `import.meta.env.VITE_MY_VAR` | `VITE_`-prefixed only |
| `vite.config.ts` | `process.env.MY_VAR` | All variables |
| Nitro server middleware | `process.env.MY_VAR` | All variables |

### .env File

```bash
# Server-only secrets — never exposed to the client bundle
DATABASE_URL=postgresql://user:pass@host:5432/db
JWT_SECRET=supersecret
STRIPE_SECRET_KEY=sk_live_...

# Client-safe values — exposed to the browser via import.meta.env
VITE_APP_NAME=My App
VITE_API_URL=https://api.example.com
VITE_POSTHOG_KEY=phc_...
```

### Migration from Next.js

| Next.js variable | TanStack Start equivalent | Action |
|-----------------|--------------------------|--------|
| `NEXT_PUBLIC_FOO` | `VITE_FOO` | Rename prefix; update all references |
| `process.env.FOO` (server) | `process.env.FOO` | No change |
| `process.env.NEXT_PUBLIC_FOO` (client) | `import.meta.env.VITE_FOO` | Use `import.meta.env` |

### Security: Preventing Secret Leaks

Vite inlines `import.meta.env` values into the client bundle at build time. Variables without the `VITE_` prefix are excluded entirely. If you reference `process.env.SECRET` inside a component, Vite may inline the value and leak it to the browser. Keep all secrets inside `createServerFn()` handlers — their internals are never included in the client bundle:

```ts
import { createServerFn } from '@tanstack/react-start'

const getSecretData = createServerFn().handler(async () => {
  // Safe: this code never runs in the browser
  return db.query(process.env.DATABASE_URL)
})
```

### Cloudflare Bindings

Cloudflare Workers does not use `process.env` for platform bindings (KV, R2, D1, Queues). Access them through `getCloudflareContext()`:

```ts
import { getCloudflareContext } from '@cloudflare/vite-plugin/worker'
import { createServerFn } from '@tanstack/react-start'

const readFromKV = createServerFn().handler(async () => {
  const { env } = getCloudflareContext()
  return env.MY_KV_NAMESPACE.get('some-key')
})
```

Declare bindings in `wrangler.jsonc` under `kv_namespaces`, `d1_databases`, `r2_buckets`, etc. The binding name in `wrangler.jsonc` must match the property accessed on `env`.

---

## Static Prerendering and SPA Mode

### Static Prerendering

Prerendering generates static HTML at build time — equivalent to Next.js `getStaticProps` / `output: 'export'` for specific routes.

```ts
tanstackStart({
  prerender: {
    enabled: true,
    crawlLinks: true,      // follow all <Link> components and prerender them
    failOnError: false,    // continue build if a route fails to prerender
  },
  sitemap: {
    enabled: true,
    host: 'https://mysite.com',
  },
})
```

With `crawlLinks: true`, the build starts from the root and follows all `<Link>` components. Dynamic routes with known parameters can be prerendered by returning them from the route's `loader`.

### SPA Mode

SPA mode disables the server and produces a single `index.html` with a client-side bundle. Use for apps that do not require SSR or server functions.

```ts
tanstackStart({
  spa: {
    enabled: true,
    prerender: { crawlLinks: true },
  },
})
```

SPA mode is incompatible with `createServerFn()`; all data fetching must occur client-side.

## Build Output

Default output directory is `.output/`:

- `.output/server/index.mjs` — Node.js server entry
- `.output/public/assets/` — Hashed JS/CSS bundles
- `.output/public/_build/` — Additional static assets

Add `.output/` to `.gitignore`. The directory is self-contained — copy to any server and run `node .output/server/index.mjs`. For platform presets (Vercel, Cloudflare, Netlify), the output format changes to match the platform's expected structure; source code does not change.

### Build Commands Summary

| Target | Build command | Start command |
|--------|--------------|---------------|
| Node.js | `vite build` | `node .output/server/index.mjs` |
| Bun | `NITRO_PRESET=bun bun --bun vite build` | `bun .output/server/index.mjs` |
| Vercel | `NITRO_PRESET=vercel vite build` | Managed by Vercel |
| Cloudflare Workers | `vite build` (with CF plugin) | `wrangler deploy` |
| Netlify | `vite build` (with Netlify plugin) | Managed by Netlify |
| AWS Lambda | `NITRO_PRESET=aws-lambda vite build` | Deploy `.output/` to Lambda |
| Static / SPA | `vite build` (with `spa.enabled`) | Serve `.output/public/` from CDN |
