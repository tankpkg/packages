import { renderToStaticHtmlDocument } from './index.js';

export async function staticExport(markdown, options = {}) {
  return renderToStaticHtmlDocument(markdown, options);
}
