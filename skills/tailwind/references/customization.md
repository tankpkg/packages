# Customization and Theming

Sources: Tailwind CSS docs.

## Extend vs override
Prefer extend to keep defaults; override only with a full system.
```js
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{ts,tsx,js,jsx,html}"],
  theme: {
    extend: {
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem"
      },
      borderRadius: {
        "xl": "1rem"
      }
    }
  }
}
```

## Full override example
```js
// tailwind.config.js
module.exports = {
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      slate: {
        50: "#f8fafc",
        900: "#0f172a"
      }
    },
    fontFamily: {
      sans: ["Inter", "ui-sans-serif", "system-ui"]
    }
  }
}
```

## Custom color palette with CSS variables
Use CSS variables for light/dark switching.
```css
:root {
  --color-bg: 255 255 255;
  --color-fg: 15 23 42;
  --color-primary: 15 23 42;
}
[data-theme="dark"] {
  --color-bg: 15 23 42;
  --color-fg: 248 250 252;
  --color-primary: 148 163 184;
}
```
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        fg: "rgb(var(--color-fg) / <alpha-value>)",
        primary: "rgb(var(--color-primary) / <alpha-value>)"
      }
    }
  }
}
```

## Custom spacing scale and fonts
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      spacing: {
        "72": "18rem",
        "84": "21rem",
        "96": "24rem"
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular"]
      }
    }
  }
}
```

## Custom border radius
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.5rem"
      }
    }
  }
}
```

## Simple utility plugin
```js
// tailwind.config.js
const plugin = require("tailwindcss/plugin");
module.exports = {
  plugins: [
    plugin(function({ addUtilities }) {
      addUtilities({
        ".text-shadow-sm": {
          textShadow: "0 1px 2px rgb(0 0 0 / 0.2)"
        },
        ".text-shadow-none": {
          textShadow: "none"
        }
      });
    })
  ]
}
```

## Component plugin
```js
// tailwind.config.js
const plugin = require("tailwindcss/plugin");
module.exports = {
  plugins: [
    plugin(function({ addComponents, theme }) {
      addComponents({
        ".btn": {
          padding: `${theme("spacing.2")} ${theme("spacing.4")}`,
          borderRadius: theme("borderRadius.md"),
          fontWeight: theme("fontWeight.medium")
        },
        ".btn-primary": {
          backgroundColor: theme("colors.slate.900"),
          color: theme("colors.white")
        }
      });
    })
  ]
}
```

## Arbitrary values
Use for edge cases only, document the reason.
```html
<div class="bg-[#1a1a2e] text-white">Custom background</div>
<div class="w-[calc(100%-2rem)]">Computed width</div>
<div class="shadow-[0_8px_30px_rgb(0_0_0/0.12)]">Custom shadow</div>
```

## CSS variable integration
```html
<div class="bg-[rgb(var(--color-bg))] text-[rgb(var(--color-fg))]">
  Uses CSS variables inside Tailwind utilities.
</div>
```

## Animation utilities
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        "fade-up": "fade-up 300ms ease-out"
      }
    }
  }
}
```
```html
<div class="animate-fade-up">Animated block</div>
```

## Gradients
```html
<div class="bg-gradient-to-r from-slate-900 via-slate-700 to-slate-500 text-white">
  Gradient banner
</div>
```

## Dark mode toggle
Class-based dark mode with data attribute.
```js
// tailwind.config.js
module.exports = {
  darkMode: ["class", "[data-theme='dark']"]
}
```
```html
<button id="themeToggle" class="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white">Toggle</button>
<script>
  const toggle = document.getElementById("themeToggle");
  toggle.addEventListener("click", () => {
    const root = document.documentElement;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
  });
</script>
```

## Performance and content config
Ensure all templates are scanned.
```js
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{ts,tsx,js,jsx,html}",
    "./index.html"
  ],
  safelist: ["bg-slate-900", "text-white"]
}
```

## Presets
Share base config across apps.
```js
// tailwind.config.js
const base = require("./tailwind.base.js");
module.exports = {
  presets: [base]
}
```

## Anti-patterns
```html
<!-- Anti-pattern: custom CSS for common utilities -->
<style>
  .card { padding: 18px; border-radius: 10px; }
</style>
<div class="card">Manual styles</div>
<!-- Prefer: tailwind tokens -->
<div class="rounded-lg border border-slate-200 p-4">Tokenized</div>
```

| Anti-pattern | Fix |
| --- | --- |
| Overriding theme for small tweaks | Use `extend` |
| Shadow values in CSS | Use `shadow-*` or document arbitrary |
| Missing content paths | JIT will purge classes |
| One-off colors | Use tokens and CSS variables |
| Duplicated plugin utilities | Centralize in one plugin |
