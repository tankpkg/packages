import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test, expect } from '@playwright/test';
import { renderToHtmlDocument, renderToStaticHtmlDocument } from '../src/index.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function fixture(name) {
  return readFile(path.join(__dirname, 'fixtures', name), 'utf8');
}

test('static export renders markdown, mermaid, math, svg, and dot', async ({ page }) => {
  const markdown = await fixture('sample.md');
  const html = await renderToStaticHtmlDocument(markdown);

  expect(html).toContain('<svg');

  await page.setContent(html, { waitUntil: 'load' });

  await expect(page.locator('h1')).toHaveText('Markdown Renderer Demo');
  await expect(page.locator('.katex').first()).toBeVisible();
  await expect(page.locator('[data-render-kind="mermaid"] svg')).toHaveCount(1);
  await expect(page.locator('[data-render-kind="graphviz"] svg')).toHaveCount(1);
  await expect(page.locator('svg[aria-label="Trusted example SVG"]')).toHaveCount(1);
});

test('client render keeps executable placeholders before static export', async () => {
  const markdown = await fixture('sample.md');
  const html = await renderToHtmlDocument(markdown);

  expect(html).toContain('data-render-kind="mermaid"');
  expect(html).toContain('data-render-state="pending"');
});

test('unsafe raw content is sanitized', async ({ page }) => {
  const markdown = await fixture('unsafe.md');
  const html = await renderToStaticHtmlDocument(markdown);

  expect(html).not.toContain('<script>');
  expect(html).not.toContain('onclick=');
  expect(html).not.toContain('onload=');

  await page.setContent(html, { waitUntil: 'load' });
  const dangerousHandles = await page.locator('script').count();
  expect(dangerousHandles).toBe(0);
});
