import { chromium } from 'playwright';
import { instance as createViz } from '@viz-js/viz';
import katex from 'katex';
import { unified } from 'unified';
import rehypeParse from 'rehype-parse';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import rehypeStringify from 'rehype-stringify';
import { visit } from 'unist-util-visit';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const mermaidScriptPath = path.resolve(__dirname, '../node_modules/mermaid/dist/mermaid.min.js');

const BASE_STYLE = `
  :root {
    color-scheme: light dark;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  }

  body {
    margin: 0;
    padding: 2rem;
    line-height: 1.6;
    background: #ffffff;
    color: #0f172a;
  }

  main {
    max-width: 72rem;
    margin: 0 auto;
  }

  pre {
    overflow-x: auto;
    padding: 1rem;
    border-radius: 0.75rem;
    background: #f8fafc;
  }

  code {
    font-family: ui-monospace, SFMono-Regular, SFMono, Menlo, Consolas, monospace;
  }

  .mdr-render-block {
    margin: 1.5rem 0;
  }

  .mdr-render-block svg {
    max-width: 100%;
    height: auto;
  }

  .mdr-source {
    display: none;
  }

  .mdr-render-block[data-render-state="failed"] {
    border: 1px solid #dc2626;
    border-radius: 0.75rem;
    padding: 1rem;
  }
`;

const SVG_TAGS = [
  'svg',
  'g',
  'path',
  'circle',
  'ellipse',
  'rect',
  'line',
  'polyline',
  'polygon',
  'text',
  'tspan',
  'defs',
  'marker',
  'pattern',
  'clipPath',
  'title',
  'desc'
];

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function createSanitizeSchema() {
  const tagNames = [...new Set([...(defaultSchema.tagNames || []), ...SVG_TAGS])];
  const globalAttributes = [...(defaultSchema.attributes?.['*'] || []), 'className', 'data*'];

  return {
    ...defaultSchema,
    tagNames,
    attributes: {
      ...defaultSchema.attributes,
      '*': globalAttributes,
      div: [...(defaultSchema.attributes?.div || []), 'data*', ['className', /^mdr-/]],
      pre: [...(defaultSchema.attributes?.pre || []), ['className', /^mdr-/]],
      span: ['className', 'ariaHidden'],
      svg: ['viewBox', 'xmlns', 'role', 'ariaLabel', 'ariaHidden', 'focusable', 'width', 'height'],
      g: ['fill', 'stroke', 'strokeWidth', 'transform'],
      path: ['d', 'fill', 'stroke', 'strokeWidth', 'transform'],
      circle: ['cx', 'cy', 'r', 'fill', 'stroke', 'strokeWidth'],
      ellipse: ['cx', 'cy', 'rx', 'ry', 'fill', 'stroke', 'strokeWidth'],
      rect: ['x', 'y', 'width', 'height', 'rx', 'ry', 'fill', 'stroke', 'strokeWidth'],
      line: ['x1', 'x2', 'y1', 'y2', 'stroke', 'strokeWidth'],
      polyline: ['points', 'fill', 'stroke', 'strokeWidth'],
      polygon: ['points', 'fill', 'stroke', 'strokeWidth'],
      text: ['x', 'y', 'dx', 'dy', 'fill', 'textAnchor'],
      tspan: ['x', 'y', 'dx', 'dy', 'fill', 'textAnchor'],
      marker: ['id', 'markerWidth', 'markerHeight', 'refX', 'refY', 'orient'],
      pattern: ['id', 'width', 'height', 'patternUnits'],
      clipPath: ['id'],
      title: [],
      desc: []
    },
    protocols: {
      ...defaultSchema.protocols,
      href: ['http', 'https', 'mailto'],
      src: ['http', 'https']
    },
    strip: [...(defaultSchema.strip || []), 'script']
  };
}

async function graphvizSvg(dotSource) {
  const viz = await createViz();
  return viz.renderString(dotSource, { format: 'svg', engine: 'dot' });
}

function renderKatexHtml(source, displayMode) {
  return katex.renderToString(source, {
    displayMode,
    output: 'html',
    throwOnError: false,
    strict: 'ignore'
  });
}

function remarkRendererExtensions() {
  return async function transform(tree) {
    const replacements = [];

    visit(tree, (node, index, parent) => {
      if (!parent || index === undefined) {
        return;
      }

      if (node.type === 'inlineMath') {
        replacements.push({
          parent,
          index,
          replacement: {
            type: 'html',
            value: renderKatexHtml(node.value, false)
          }
        });
        return;
      }

      if (node.type === 'math') {
        replacements.push({
          parent,
          index,
          replacement: {
            type: 'html',
            value: renderKatexHtml(node.value, true)
          }
        });
        return;
      }

      if (node.type !== 'code') {
        return;
      }

      const lang = node.lang?.toLowerCase();
      if (!lang) {
        return;
      }

      if (lang === 'mermaid') {
        replacements.push({
          parent,
          index,
          replacement: {
            type: 'html',
            value: `<div class="mdr-render-block" data-render-kind="mermaid" data-render-state="pending"><pre class="mdr-source">${escapeHtml(node.value)}</pre></div>`
          }
        });
        return;
      }

      if (lang === 'dot' || lang === 'graphviz') {
        replacements.push({
          parent,
          index,
          replacement: {
            type: 'html',
            value: ''
          },
          dotSource: node.value
        });
        return;
      }
    });

    for (const item of replacements) {
      if (item.dotSource) {
        item.parent.children[item.index] = {
          type: 'html',
          value: `<div class="mdr-render-block" data-render-kind="graphviz" data-render-state="rendered">${await graphvizSvg(item.dotSource)}</div>`
        };
        continue;
      }

      item.parent.children[item.index] = item.replacement;
    }
  };
}

async function renderFragment(markdown) {
  const processor = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkMath)
    .use(remarkRendererExtensions)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeSanitize, createSanitizeSchema())
    .use(rehypeStringify);

  const file = await processor.process(markdown);
  return String(file);
}

async function sanitizeRenderedFragment(fragment) {
  const processor = unified()
    .use(rehypeParse, { fragment: true })
    .use(rehypeSanitize, createSanitizeSchema())
    .use(rehypeStringify);

  const file = await processor.process(fragment);
  return String(file);
}

function wrapDocument(fragment, title = 'Markdown Renderer Prototype') {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(title)}</title>
    <style>${BASE_STYLE}</style>
  </head>
  <body>
    <main>${fragment}</main>
  </body>
</html>`;
}

export async function renderToHtmlDocument(markdown, options = {}) {
  const fragment = await renderFragment(markdown);
  return wrapDocument(fragment, options.title);
}

async function executeMermaid(page) {
  await page.addScriptTag({ path: mermaidScriptPath });
  await page.evaluate(async () => {
    const blocks = Array.from(document.querySelectorAll('[data-render-kind="mermaid"]'));
    if (blocks.length === 0) {
      return;
    }

    const mermaid = window.mermaid;
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });

    for (const [index, block] of blocks.entries()) {
      const source = block.querySelector('.mdr-source')?.textContent || '';

      try {
        const { svg, bindFunctions } = await mermaid.render(`mdr-mermaid-${index}`, source);
        block.innerHTML = svg;
        block.setAttribute('data-render-state', 'rendered');
        if (bindFunctions) {
          bindFunctions(block);
        }
      } catch (error) {
        block.setAttribute('data-render-state', 'failed');
        block.textContent = error instanceof Error ? error.message : String(error);
      }
    }
  });
}

export async function renderToStaticHtmlDocument(markdown, options = {}) {
  const clientHtml = await renderToHtmlDocument(markdown, options);
  let browser;
  let page;

  try {
    browser = await chromium.launch();
    page = await browser.newPage();
    await page.route('**/*', (route) => route.abort());
    await page.setContent(clientHtml, { waitUntil: 'load' });
    await executeMermaid(page);
    await page.evaluate(() => {
      for (const script of document.querySelectorAll('script')) {
        script.remove();
      }
    });
    const finalFragment = await page.locator('main').innerHTML();
    const sanitizedFragment = await sanitizeRenderedFragment(finalFragment);
    return wrapDocument(sanitizedFragment, options.title);
  } finally {
    await page?.close();
    await browser?.close();
  }
}
