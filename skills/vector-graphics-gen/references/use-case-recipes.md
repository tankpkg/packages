# Use Case Recipes

Sources: fal.ai documentation, production implementations (2025-2026)

Covers: complete end-to-end code for common vector graphics tasks. Copy and adapt directly.

## Shared Setup

All recipes use this boilerplate. Install: `npm install @fal-ai/client @quiverai/sdk svgo`.

```javascript
import { fal } from "@fal-ai/client";
import QuiverAI from "@quiverai/sdk";
import { optimize } from "svgo";
import fs from "fs/promises";

fal.config({ credentials: process.env.FAL_KEY });
const quiver = new QuiverAI({ apiKey: process.env.QUIVER_API_KEY });

const svgoConfig = {
  multipass: true,
  plugins: [
    { name: "preset-default", params: { overrides: { removeViewBox: false } } },
    { name: "convertPathData", params: { floatPrecision: 1 } },
  ],
};

async function fetchSvg(url) {
  const text = await fetch(url).then((r) => r.text());
  return optimize(text, svgoConfig).data;
}
```

**Highest quality** (QuiverAI Arrow — premium generation):
`QuiverAI Arrow` → SVGO

**Native SVG (fal.ai)** (Recraft V4 — one step):
`fal-ai/recraft/v4/text-to-vector` → SVGO

**Styled SVG (fal.ai)** (Recraft V3 — raster-style, then vectorize):
`fal-ai/recraft/v3/text-to-image` → `fal-ai/recraft/vectorize` → SVGO

---

## Recipe 1: App Icon Set

Generate a single icon at multiple sizes with PNG fallbacks for all platforms.

**Model**: `fal-ai/recraft/v4/text-to-vector` — true SVG, scales to any size.
**Extra dep**: `npm install sharp`

```javascript
import sharp from "sharp";

async function generateAppIconSet(appName, description, brandColor) {
  const result = await fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
    input: {
      prompt: `App icon for ${appName}: ${description}. Flat design, single centered symbol, minimal geometric shapes, solid colors only, white background, no text, no gradients`,
      image_size: "square_hd",
      colors: [brandColor],
      background_color: { r: 255, g: 255, b: 255 },
    },
    logs: true,
    onQueueUpdate: (u) => u.status === "IN_PROGRESS" && u.logs.forEach((l) => console.log(l.message)),
  });

  const svg = await fetchSvg(result.data.images[0].url);
  const outDir = `./icons/${appName.toLowerCase()}`;
  await fs.mkdir(outDir, { recursive: true });
  await fs.writeFile(`${outDir}/icon.svg`, svg);

  for (const size of [16, 32, 64, 128, 512]) {
    await sharp(Buffer.from(svg)).resize(size, size).png().toFile(`${outDir}/icon-${size}.png`);
  }
}

await generateAppIconSet("Taskflow", "checkmark inside a circle", { r: 99, g: 102, b: 241 });
```

**Integration**: Use `icon.svg` inline for crisp rendering at any size. Use `icon-512.png` for app store submissions, `icon-32.png` for favicons.

**Alternative (QuiverAI Arrow)**: Use Arrow for highest-quality output when budget allows.

```javascript
const arrowResult = await quiver.arrow.generate({
  prompt: `App icon for ${appName}: ${description}. Flat design, single centered symbol, minimal geometric shapes, solid colors only, white background, no text`,
  output_format: "svg",
});
const svg = optimize(arrowResult.svg, svgoConfig).data;
await fs.writeFile(`./icons/${appName.toLowerCase()}/icon.svg`, svg);
```

---

## Recipe 2: Logo Generation with Variants

Generate a brand logo and produce four standard variants: full lockup, icon-only, monochrome, reversed.

**Model**: `fal-ai/recraft/v4/text-to-vector` — color palette control, true SVG.

```javascript
async function generateLogoVariants({ name, tagline, primaryColor, secondaryColor }) {
  const [fullResult, iconResult] = await Promise.all([
    fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
      input: {
        prompt: `Professional logo for "${name}" — ${tagline}. Symbol left, company name right. Clean vector, flat, minimal, 2 colors, white background`,
        image_size: { width: 800, height: 300 },
        colors: [primaryColor, secondaryColor],
        background_color: { r: 255, g: 255, b: 255 },
      },
      logs: false,
    }),
    fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
      input: {
        prompt: `Logo symbol only for "${name}" — ${tagline}. No text, centered symbol, flat vector, white background`,
        image_size: "square_hd",
        colors: [primaryColor],
        background_color: { r: 255, g: 255, b: 255 },
      },
      logs: false,
    }),
  ]);

  const outDir = `./logos/${name.toLowerCase().replace(/\s+/g, "-")}`;
  await fs.mkdir(outDir, { recursive: true });

  const fullSvg = await fetchSvg(fullResult.data.images[0].url);
  const iconSvg = await fetchSvg(iconResult.data.images[0].url);

  await fs.writeFile(`${outDir}/logo-full.svg`, fullSvg);
  await fs.writeFile(`${outDir}/logo-icon.svg`, iconSvg);
  await fs.writeFile(`${outDir}/logo-mono.svg`, iconSvg.replace(/fill="[^"]*"/g, 'fill="#1a1a1a"'));
  await fs.writeFile(`${outDir}/logo-reversed.svg`, iconSvg.replace(/fill="[^"]*"/g, 'fill="white"'));
}

await generateLogoVariants({
  name: "Meridian", tagline: "navigation software",
  primaryColor: { r: 14, g: 165, b: 233 }, secondaryColor: { r: 15, g: 23, b: 42 },
});
```

**Integration**: Use `logo-full.svg` in the site header. Use `logo-icon.svg` for favicons. Apply `logo-reversed.svg` on dark backgrounds.

**Alternative (QuiverAI Arrow)**: Arrow produces cleaner path structure for logos that will be used at large print sizes.

```javascript
const arrowResult = await quiver.arrow.generate({
  prompt: `Professional logo for "${name}" — ${tagline}. Symbol left, company name right. Clean vector, flat, minimal, 2 colors, white background`,
  output_format: "svg",
});
const svg = optimize(arrowResult.svg, svgoConfig).data;
await fs.writeFile(`./logos/${name.toLowerCase().replace(/\s+/g, "-")}/logo-full.svg`, svg);
```

---

## Recipe 3: Hero Illustration

Generate a large illustration for a landing page hero, optimized for web delivery.

**Model**: `fal-ai/recraft/v4/pro/text-to-vector` — highest-quality native SVG, no vectorize step needed.

```javascript
async function generateHeroIllustration(concept, palette) {
  const result = await fal.subscribe("fal-ai/recraft/v4/pro/text-to-vector", {
    input: {
      prompt: `${concept}. Flat vector illustration, editorial style, bold shapes, limited color palette, no text, no gradients, clean composition`,
      image_size: "landscape_16_9",
      colors: palette,
    },
    logs: true,
    onQueueUpdate: (u) => u.status === "IN_PROGRESS" && u.logs.forEach((l) => console.log(l.message)),
  });

  const svg = await fetchSvg(result.data.images[0].url);
  await fs.writeFile("./hero-illustration.svg", svg);
  console.log(`SVG: ${(svg.length / 1024).toFixed(1)}KB`);
}

await generateHeroIllustration(
  "Team collaborating around a glowing dashboard, modern office, diverse people",
  [{ r: 99, g: 102, b: 241 }, { r: 236, g: 72, b: 153 }, { r: 248, g: 250, b: 252 }]
);
```

**Note**: For specific V3 sub-style control (e.g., `emotional_flat`, `editorial`), use the V3 + vectorize pipeline instead: `fal-ai/recraft/v3/text-to-image` with `style: "vector_illustration"` → `fal-ai/recraft/vectorize`.

**Integration**:

```html
<img src="/hero-illustration.svg" alt="Team collaborating" width="1200" height="675"
     loading="eager" fetchpriority="high" />
```

---

## Recipe 4: Icon Library with Sprite Sheet and React Component

Batch-generate a consistent icon set, merge into a sprite, and expose as a typed React component.

**Model**: `fal-ai/recraft/v4/text-to-vector` — consistent style across batch.

```javascript
const ICONS = [
  { id: "home", prompt: "house outline, minimal" },
  { id: "search", prompt: "magnifying glass, minimal" },
  { id: "settings", prompt: "gear/cog wheel, 8 teeth" },
  { id: "user", prompt: "person silhouette, head and shoulders" },
  { id: "bell", prompt: "notification bell, minimal" },
  { id: "mail", prompt: "envelope, closed, minimal" },
  { id: "chart", prompt: "bar chart, 3 ascending bars" },
  { id: "lock", prompt: "padlock, closed, minimal" },
  { id: "star", prompt: "5-point star, minimal" },
  { id: "trash", prompt: "trash can with lid, minimal" },
];

async function generateIconLibrary(brandColor) {
  const iconData = [];
  for (let i = 0; i < ICONS.length; i += 5) {
    const batch = ICONS.slice(i, i + 5);
    const results = await Promise.all(
      batch.map((icon) =>
        fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
          input: {
            prompt: `Icon: ${icon.prompt}. 24x24 grid, centered, flat vector, line art, stroke only, white background`,
            image_size: "square_hd",
            colors: [brandColor],
          },
          logs: false,
        })
      )
    );
    for (let j = 0; j < batch.length; j++) {
      const svg = await fetchSvg(results[j].data.images[0].url);
      const inner = svg.replace(/<\?xml[^>]*\?>/, "").replace(/<svg[^>]*>/, "").replace(/<\/svg>/, "").trim();
      iconData.push({ id: batch[j].id, inner });
    }
  }

  await fs.mkdir("./icons", { recursive: true });

  const symbols = iconData
    .map(({ id, inner }) => `  <symbol id="icon-${id}" viewBox="0 0 24 24">\n    ${inner}\n  </symbol>`)
    .join("\n");
  await fs.writeFile("./icons/sprite.svg",
    `<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n${symbols}\n</svg>`
  );

  const iconIds = iconData.map((i) => `"${i.id}"`).join(" | ");
  await fs.writeFile("./icons/Icon.tsx",
`import React from "react";
type IconId = ${iconIds};
interface IconProps { name: IconId; size?: number; className?: string; "aria-label"?: string; }
export function Icon({ name, size = 24, className, "aria-label": label }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-label={label} aria-hidden={!label}>
      <use href={\`/icons/sprite.svg#icon-\${name}\`} />
    </svg>
  );
}`);
}

await generateIconLibrary({ r: 99, g: 102, b: 241 });
```

**Integration**: Include `sprite.svg` once at the page root, then use `<Icon name="home" size={20} />` anywhere.

---

## Recipe 5: Seamless Tileable Pattern

Generate a pattern tile and output as a CSS background.

**Model**: `fal-ai/recraft/v3/text-to-image` with `style: "vector_illustration"`, `substyle: "segmented_colors"`.

```javascript
async function generateSeamlessPattern(theme, colors) {
  const rasterResult = await fal.subscribe("fal-ai/recraft/v3/text-to-image", {
    input: {
      prompt: `Seamless repeating pattern: ${theme}. Flat vector, geometric, elements near edges for seamless tiling, no central focal point, white background`,
      style: "vector_illustration",
      substyle: "segmented_colors",
      image_size: "square_hd",
      colors,
    },
    logs: false,
  });

  const vectorResult = await fal.subscribe("fal-ai/recraft/vectorize", {
    input: { image_url: rasterResult.data.images[0].url },
    logs: false,
  });

  const svg = await fetchSvg(vectorResult.data.images[0].url);
  await fs.writeFile("./pattern-tile.svg", svg);

  const dataUri = `data:image/svg+xml,${encodeURIComponent(svg)}`;
  await fs.writeFile("./pattern.css",
    `.pattern-bg { background-image: url("${dataUri}"); background-repeat: repeat; background-size: 200px 200px; }`
  );
}

await generateSeamlessPattern("small leaves and botanical elements", [
  { r: 34, g: 197, b: 94 }, { r: 240, g: 253, b: 244 },
]);
```

**Note**: The `seamless_pattern` sub-style requires V3. V4 does not support sub-styles, so the two-step pipeline is mandatory here. For a generic geometric tile without seamless-specific styling, `fal-ai/recraft/v4/text-to-vector` with a tiling prompt works as a simpler alternative.

**Integration**: Apply `.pattern-bg` to any container. Adjust `background-size` to control tile density.

---

## Recipe 6: Photo to Clean Vector

Convert an existing photo or screenshot to an optimized SVG.

**Model**: `fal-ai/image2svg` ($0.005) for simple images; `fal-ai/recraft/vectorize` ($0.01) for higher fidelity.

```javascript
async function photoToVector(inputPath, outputPath, highFidelity = false) {
  const imageBuffer = await fs.readFile(inputPath);
  const ext = inputPath.split(".").pop().toLowerCase();
  const file = new File([imageBuffer], `input.${ext}`, { type: ext === "png" ? "image/png" : "image/jpeg" });
  const uploadedUrl = await fal.storage.upload(file);

  const endpoint = highFidelity ? "fal-ai/recraft/vectorize" : "fal-ai/image2svg";
  const result = await fal.subscribe(endpoint, {
    input: { image_url: uploadedUrl },
    logs: true,
    onQueueUpdate: (u) => u.status === "IN_PROGRESS" && u.logs.forEach((l) => console.log(l.message)),
  });

  const svg = await fetchSvg(result.data.images[0].url);
  await fs.writeFile(outputPath, svg);
  console.log(`${(imageBuffer.length / 1024).toFixed(1)}KB → ${(svg.length / 1024).toFixed(1)}KB SVG`);
}

await photoToVector("./logo-photo.png", "./logo-vector.svg", true);
```

**Note**: If the output SVG exceeds 50KB, the source image is too complex for clean vectorization. Regenerate from a prompt with `fal-ai/recraft/v4/text-to-vector` instead.

---

## Recipe 7: Badge and Sticker Set

Generate a matching set of gamification badges with consistent visual style.

**Model**: `fal-ai/recraft/v4/text-to-vector` — native SVG, no vectorize step needed. Saves $0.01/badge vs V3 + vectorize.

```javascript
const BADGES = [
  { id: "beginner", symbol: "seedling sprout", color: { r: 34, g: 197, b: 94 } },
  { id: "explorer", symbol: "compass rose", color: { r: 59, g: 130, b: 246 } },
  { id: "builder", symbol: "hammer and wrench crossed", color: { r: 245, g: 158, b: 11 } },
  { id: "expert", symbol: "lightning bolt", color: { r: 168, g: 85, b: 247 } },
  { id: "master", symbol: "crown with gems", color: { r: 239, g: 68, b: 68 } },
];

async function generateBadgeSet() {
  const outDir = "./badges";
  await fs.mkdir(outDir, { recursive: true });

  const results = await Promise.all(
    BADGES.map((b) =>
      fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
        input: {
          prompt: `Achievement badge: ${b.symbol}. Circular badge shape, bold stroke outline, flat vector, centered symbol, no text, white background`,
          image_size: "square_hd",
          colors: [b.color, { r: 255, g: 255, b: 255 }],
        },
        logs: false,
      }).then((r) => ({ badge: b, url: r.data.images[0].url }))
    )
  );

  for (const { badge, url } of results) {
    const svg = await fetchSvg(url);
    await fs.writeFile(`${outDir}/${badge.id}.svg`, svg);
  }
}

await generateBadgeSet();
```

**Integration**:

```jsx
function AchievementBadge({ id, label, earned }) {
  return (
    <div className={`badge ${earned ? "earned" : "locked"}`}>
      <img src={`/badges/${id}.svg`} alt={label} width={64} height={64} />
      <span>{label}</span>
    </div>
  );
}
```

---

## Recipe 8: Decorative Dividers and Ornamental Elements

Generate section dividers and wave separators for landing pages.

**Model**: `fal-ai/recraft/v4/text-to-vector` — native SVG, single step.

```javascript
const DIVIDERS = [
  { id: "wave", prompt: "Smooth wave divider, single continuous wave path, horizontal" },
  { id: "zigzag", prompt: "Zigzag border, sharp geometric teeth, horizontal strip" },
  { id: "floral", prompt: "Ornamental floral divider, symmetrical botanical motif, centered, horizontal" },
];

async function generateDividerSet(accentColor) {
  const outDir = "./dividers";
  await fs.mkdir(outDir, { recursive: true });

  for (const divider of DIVIDERS) {
    const result = await fal.subscribe("fal-ai/recraft/v4/text-to-vector", {
      input: {
        prompt: `${divider.prompt}. Flat vector, no gradients, white background`,
        image_size: "landscape_16_9",
        colors: [accentColor, { r: 255, g: 255, b: 255 }],
      },
      logs: false,
    });

    const svg = await fetchSvg(result.data.images[0].url);
    await fs.writeFile(`${outDir}/${divider.id}.svg`, svg);
  }
}

await generateDividerSet({ r: 99, g: 102, b: 241 });
```

**Note**: For hairline or ultra-thin stroke dividers, use the V3 pipeline with `substyle: "thin"`: `fal-ai/recraft/v3/text-to-image` → `fal-ai/image2svg`. V4 does not expose the `thin` sub-style.

**Integration**:

```html
<section class="hero">...</section>
<div style="width:100%; overflow:hidden; line-height:0;">
  <img src="/dividers/wave.svg" alt="" aria-hidden="true" style="display:block; width:100%;" />
</div>
<section class="features">...</section>
```

For prompt engineering patterns that improve output quality across all recipes, see `references/prompt-engineering.md`. For SVGO configuration details, see `references/svg-optimization.md`. For model selection guidance, see `references/fal-api-reference.md`.
