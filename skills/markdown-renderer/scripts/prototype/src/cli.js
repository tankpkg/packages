import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

function parseArgs(argv) {
  const result = { mode: 'client' };
  for (let index = 0; index < argv.length; index += 1) {
    const current = argv[index];
    const next = argv[index + 1];

    if (current === '--in') {
      result.input = next;
      index += 1;
      continue;
    }

    if (current === '--out') {
      result.output = next;
      index += 1;
      continue;
    }

    if (current === '--mode') {
      result.mode = next;
      index += 1;
    }
  }

  return result;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input || !args.output) {
    throw new Error('Usage: node src/cli.js --in <file.md> --out <file.html> [--mode client|static]');
  }

  if (args.mode !== 'client' && args.mode !== 'static') {
    throw new Error(`Invalid mode: ${args.mode}. Expected client or static.`);
  }

  const { renderToHtmlDocument, renderToStaticHtmlDocument } = await import('./index.js');

  const markdown = await readFile(path.resolve(args.input), 'utf8');
  const html = args.mode === 'static'
    ? await renderToStaticHtmlDocument(markdown)
    : await renderToHtmlDocument(markdown);

  await writeFile(path.resolve(args.output), html, 'utf8');
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exitCode = 1;
});
