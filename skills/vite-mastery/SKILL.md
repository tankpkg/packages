---
name: "@tank/vite-mastery"
description: |
  Comprehensive Vite build tool mastery. Covers vite.config.ts authoring
  (resolve aliases, define, env variables, conditional config), development
  server (HMR, proxy, HTTPS, custom middleware), build optimization (Rollup
  options, manual chunks, code splitting, minification, CSS splitting, asset
  inlining), plugin development (hooks, virtual modules, transform pipeline,
  enforce ordering), SSR (entry, externalization, streaming, hydration),
  library mode (build.lib, externals, multiple formats, CSS extraction),
  PWA via vite-plugin-pwa (workbox, manifest, offline), environment and
  mode configuration (.env, import.meta.env), and performance profiling
  (rollup-plugin-visualizer, optimizeDeps, pre-bundling). Synthesizes
  Vite official documentation (vitejs.dev), Rollup documentation, esbuild
  documentation, Evan You (Vite design philosophy), and community
  optimization guides.

  Trigger phrases: "vite", "vite config", "vite.config.ts", "vite build",
  "vite dev server", "vite HMR", "vite proxy", "vite plugin", "vite SSR",
  "vite library mode", "build.lib", "rollup options", "manual chunks",
  "code splitting vite", "vite optimize", "optimizeDeps", "vite PWA",
  "vite-plugin-pwa", "import.meta.env", "vite env variables", "vite resolve alias",
  "vite chunk splitting", "vite bundle size", "bundle too large",
  "vite performance", "rollup-plugin-visualizer", "vite define",
  "vite CSS splitting", "vite asset inlining", "virtual module vite",
  "vite conditional config", "vite HTTPS", "vite middleware"
---

# Vite Mastery

Configure, optimize, and extend Vite builds for any frontend project.

## Core Philosophy

1. **Unbundled dev, bundled prod.** Dev uses native ESM for speed; prod uses Rollup for optimization. Understand both pipelines.
2. **Convention over configuration.** Vite works out of the box. Only configure what you measured needs changing.
3. **Measure before splitting.** Never add manual chunks, change minifiers, or adjust thresholds without profiling first.
4. **Plugins are Rollup hooks + Vite extras.** Master Rollup's plugin interface and Vite's extensions on top of it.
5. **Environment isolation is non-negotiable.** Env variables must never leak between modes or between client and server.

## Quick-Start: Common Problems

### "Bundle too large"

1. Run `npx vite-bundle-visualizer` or add `rollup-plugin-visualizer` to see what's in the bundle.
2. Check for accidentally bundled server-only code or dev dependencies.
3. Apply manual chunks for large vendor libraries.
   -> See `references/build-optimization.md` for chunk splitting strategies.

### "HMR not working"

1. Verify the file is within the project root (files outside root bypass HMR).
2. Check for circular imports — Vite's HMR propagation fails on cycles.
3. Ensure the framework plugin is loaded (`@vitejs/plugin-react`, `@vitejs/plugin-vue`).
4. Check `server.hmr` config if behind a reverse proxy.
   -> See `references/configuration-and-dev-server.md` for proxy and HMR config.

### "Module not found / resolve errors"

1. Check `resolve.alias` paths — use `path.resolve(__dirname, ...)` or `fileURLToPath`.
2. Verify `optimizeDeps.include` for CJS dependencies that fail pre-bundling.
3. Check `ssr.noExternal` for SSR builds that need to bundle specific packages.
   -> See `references/configuration-and-dev-server.md` for resolve configuration.

### "Env variables undefined"

1. Confirm the variable is prefixed with `VITE_` (only `VITE_*` vars are exposed to client).
2. Use `import.meta.env.VITE_*` — not `process.env`.
3. Verify the `.env` file matches the current mode (`.env.production`, `.env.staging`).
   -> See `references/environment-pwa-tooling.md` for env and mode configuration.

## Configuration Decision Trees

| Signal | Recommendation |
| --- | --- |
| Need path shortcuts | `resolve.alias` with absolute paths |
| CJS dependency fails in dev | Add to `optimizeDeps.include` |
| Need compile-time constants | `define` with `JSON.stringify` |
| Need different config per mode | Export a function: `export default defineConfig(({ mode }) => ...)` |
| API calls hit CORS in dev | `server.proxy` with `changeOrigin: true` |
| Bundle > 500kB gzipped | Profile with visualizer, apply manual chunks |
| Building a library | Use `build.lib` with external dependencies |
| Need SSR | Configure `ssr.entry` and `ssr.noExternal` |
| Need offline support | Add `vite-plugin-pwa` with workbox strategies |

## Build Optimization Decision Tree

| Symptom | Diagnostic | Fix |
| --- | --- | --- |
| Large single chunk | No code splitting | Add dynamic imports at route boundaries |
| Vendor chunk > 250kB | Single vendor bundle | Split with `manualChunks` by domain |
| Duplicate modules across chunks | Shared deps not extracted | Rollup handles this automatically; verify with visualizer |
| Slow minification | Using terser | Switch to esbuild (default) unless terser features needed |
| Large CSS bundle | All CSS in one file | Enable `build.cssCodeSplit` (default true) |
| Small assets bloating requests | Too many HTTP requests for tiny files | Increase `build.assetsInlineLimit` (default 4096 bytes) |

## Plugin Selection Guide

| Need | Plugin | Notes |
| --- | --- | --- |
| React Fast Refresh | `@vitejs/plugin-react` | Uses Babel. Use `@vitejs/plugin-react-swc` for speed. |
| Vue SFC support | `@vitejs/plugin-vue` | Required for `.vue` files |
| Svelte support | `@sveltejs/vite-plugin-svelte` | Required for `.svelte` files |
| Legacy browser support | `@vitejs/plugin-legacy` | Generates polyfilled chunks |
| PWA / service worker | `vite-plugin-pwa` | Workbox integration |
| Bundle analysis | `rollup-plugin-visualizer` | Add in build only |
| SVG as components | `vite-plugin-svgr` (React) | Framework-specific |
| Environment validation | `@t3-oss/env-core` | Validates env at build time |

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
| --- | --- | --- |
| Importing `process.env` in client code | Undefined in browser; Vite uses `import.meta.env` | Replace with `import.meta.env.VITE_*` |
| Using `__dirname` in vite.config.ts | Fails with ESM config format | Use `fileURLToPath(new URL('.', import.meta.url))` |
| Splitting every dependency into its own chunk | Creates waterfall of HTTP requests | Group by domain (e.g., `react-vendor`, `ui-vendor`) |
| Disabling pre-bundling globally | Breaks dev server performance | Only exclude specific packages with `optimizeDeps.exclude` |
| Putting secrets in `VITE_*` env vars | Exposed in client bundle | Only prefix public values with `VITE_` |
| Running terser in dev | Destroys dev server speed | Terser is prod-only by default; never change this |
| Giant `vite.config.ts` with all logic inline | Unmaintainable | Extract plugin factories and helper functions |
| Ignoring `build.rollupOptions.output.manualChunks` return value | Orphaned modules in wrong chunks | Always return a string or `undefined`, never skip |

## Reference Index

| File | Contents |
| --- | --- |
| `references/configuration-and-dev-server.md` | vite.config.ts structure, resolve aliases, define, conditional config, dev server, HMR, proxy, HTTPS, middleware |
| `references/build-optimization.md` | Rollup options, manual chunks, code splitting strategies, minification, CSS code splitting, asset inlining, tree-shaking |
| `references/plugin-development.md` | Plugin hooks, virtual modules, transform pipeline, enforce ordering, HMR API, plugin testing |
| `references/ssr-and-library-mode.md` | SSR entry, externalization, streaming, client hydration, build.lib, external deps, multiple formats, CSS extraction |
| `references/environment-pwa-tooling.md` | .env files, import.meta.env, mode config, vite-plugin-pwa, workbox strategies, rollup-plugin-visualizer, optimizeDeps |
