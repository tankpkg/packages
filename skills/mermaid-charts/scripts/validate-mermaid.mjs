#!/usr/bin/env node
// validate-mermaid.mjs — validate Mermaid diagrams using the official parser.
//
// Modes:
//   node validate-mermaid.mjs <path> [<path> ...]    Walk paths; lint mermaid
//                                                    blocks in .md/.mdx files,
//                                                    or treat .mmd files as
//                                                    raw mermaid text.
//   node validate-mermaid.mjs --stdin                Read raw mermaid text on
//                                                    stdin and validate it.
//
// Why this approach:
//   - mermaid.parse() is the SAME grammar that renders on GitHub, GitLab,
//     Notion, Obsidian, and mermaid.live. "Passes here" == "renders there".
//   - jsdom is required because the mermaid package loads DOMPurify at import
//     time. We give it a minimal DOM. No Puppeteer / Chromium needed.
//   - Line numbers in error output are offset back to the source file so
//     editors can jump straight to the offending line.
//
// Exit codes:
//   0  all diagrams valid
//   1  at least one parse error
//   2  validator itself crashed (bad args, missing deps, etc.)
//
// Reference pattern: NVIDIA/OpenShell lint-mermaid.mjs and GitLab
// check_mermaid.mjs. Both use the same mermaid.parse() + jsdom approach.

import { readdir, readFile, stat } from 'node:fs/promises';
import { join, relative, resolve, extname } from 'node:path';

// ---- Set up DOM shim BEFORE importing mermaid (DOMPurify runs at import) ----
let JSDOM;
try {
  ({ JSDOM } = await import('jsdom'));
} catch {
  console.error(
    'validate-mermaid: missing dependency `jsdom`.\n' +
      '  Run `npm install` in the scripts/ directory first.',
  );
  process.exit(2);
}
const dom = new JSDOM('');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.DOMParser = dom.window.DOMParser;
globalThis.Node = dom.window.Node;
globalThis.HTMLElement = dom.window.HTMLElement;

let mermaid;
try {
  ({ default: mermaid } = await import('mermaid'));
} catch (err) {
  console.error(
    'validate-mermaid: failed to load `mermaid`.\n' +
      '  Run `npm install` in the scripts/ directory first.\n' +
      `  Underlying error: ${err?.message || err}`,
  );
  process.exit(2);
}

// ---- Markdown fence extraction ----
const EXCLUDE_DIRS = new Set([
  'node_modules',
  '.git',
  '.cache',
  'dist',
  'build',
  '_build',
  'target',
  '.venv',
  '.next',
  '.turbo',
]);
const MD_EXTENSIONS = new Set(['.md', '.mdx', '.markdown']);
const RAW_EXTENSIONS = new Set(['.mmd', '.mermaid']);
const OPEN_FENCE_RE = /^[ \t]*(`{3,}|~{3,})(.*)$/;

function parseFenceOpen(line) {
  const m = line.match(OPEN_FENCE_RE);
  if (!m) return null;
  const marker = m[1][0];
  const length = m[1].length;
  const info = m[2].trim();
  // Inline code fences (backticks within info string) are not block fences.
  if (marker === '`' && info.includes('`')) return null;
  const language = info.split(/\s+/)[0].toLowerCase();
  return { marker, length, isMermaid: language === 'mermaid' };
}

function isFenceClose(line, fence) {
  const trimmed = line.trim();
  if (trimmed.length < fence.length) return false;
  // A closing fence is N+ of the same marker char, nothing else.
  return [...trimmed].every((ch) => ch === fence.marker);
}

function extractBlocks(text) {
  const lines = text.split('\n');
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const fence = parseFenceOpen(lines[i]);
    if (!fence) {
      i++;
      continue;
    }
    const startLine = i + 1; // 1-indexed; +1 again below offsets into body
    const body = [];
    i++;
    while (i < lines.length && !isFenceClose(lines[i], fence)) {
      if (fence.isMermaid) body.push(lines[i]);
      i++;
    }
    if (fence.isMermaid) {
      blocks.push({ startLine: startLine + 1, body: body.join('\n') });
    }
    i++; // skip closing fence
  }
  return blocks;
}

// ---- Error formatting ----
function formatError(err, file, blockStartLine) {
  const msg = err?.message || String(err);
  // Mermaid surfaces "Parse error on line N" (Jison) and
  // "Lexical error on line N" — extract for jump-to-line.
  const m = msg.match(/(?:Parse|Lexical|Syntax) error on line (\d+)/i);
  const relLine = m ? parseInt(m[1], 10) : 1;
  const sourceLine = (blockStartLine ?? 1) + relLine - 1;
  const head = msg.split('\n').slice(0, 8).join('\n  ');
  return file
    ? `${file}:${sourceLine}: mermaid parse error\n  ${head}`
    : `<stdin>:${relLine}: mermaid parse error\n  ${head}`;
}

// ---- Validation primitives ----
async function validateText(text) {
  // suppressErrors: false (default) — we WANT it to throw on bad input.
  await mermaid.parse(text);
}

async function lintMarkdownFile(file) {
  const text = await readFile(file, 'utf8');
  const blocks = extractBlocks(text);
  const errors = [];
  for (const block of blocks) {
    try {
      await validateText(block.body);
    } catch (err) {
      errors.push(formatError(err, file, block.startLine));
    }
  }
  return { file, blockCount: blocks.length, errors };
}

async function lintRawFile(file) {
  const text = await readFile(file, 'utf8');
  try {
    await validateText(text);
    return { file, blockCount: 1, errors: [] };
  } catch (err) {
    return { file, blockCount: 1, errors: [formatError(err, file, 1)] };
  }
}

async function lintStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const text = Buffer.concat(chunks).toString('utf8');
  if (!text.trim()) {
    console.error('validate-mermaid: --stdin given but stdin was empty');
    process.exit(2);
  }
  try {
    await validateText(text);
    console.log('mermaid: stdin diagram is valid');
    process.exit(0);
  } catch (err) {
    console.error(formatError(err, null, 1));
    process.exit(1);
  }
}

// ---- File system walking ----
async function* walk(root) {
  let entries;
  try {
    entries = await readdir(root, { withFileTypes: true });
  } catch (err) {
    console.error(`validate-mermaid: cannot read ${root}: ${err.message}`);
    return;
  }
  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.') continue;
    if (EXCLUDE_DIRS.has(entry.name)) continue;
    const p = join(root, entry.name);
    if (entry.isDirectory()) {
      yield* walk(p);
    } else {
      const ext = extname(entry.name).toLowerCase();
      if (MD_EXTENSIONS.has(ext) || RAW_EXTENSIONS.has(ext)) yield p;
    }
  }
}

async function collectFiles(roots) {
  const files = [];
  for (const root of roots) {
    const abs = resolve(root);
    let entry;
    try {
      entry = await stat(abs);
    } catch (err) {
      console.error(`validate-mermaid: cannot read ${root}: ${err.message}`);
      process.exitCode = 1;
      continue;
    }
    if (entry.isDirectory()) {
      for await (const f of walk(abs)) files.push(f);
    } else {
      const ext = extname(abs).toLowerCase();
      if (MD_EXTENSIONS.has(ext) || RAW_EXTENSIONS.has(ext)) {
        files.push(abs);
      } else {
        console.error(
          `validate-mermaid: ${root} has unsupported extension; expected .md/.mdx/.markdown/.mmd/.mermaid`,
        );
        process.exitCode = 1;
      }
    }
  }
  return files;
}

// ---- CLI entry ----
function printUsage() {
  console.error(
    'Usage:\n' +
      '  validate-mermaid <path> [<path> ...]   Walk paths; lint mermaid in .md/.mdx, or treat .mmd as raw\n' +
      '  validate-mermaid --stdin               Read raw mermaid text on stdin\n' +
      '  validate-mermaid --help                Print this help\n',
  );
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help') || args.includes('-h')) {
    printUsage();
    process.exit(0);
  }
  if (args.includes('--stdin')) {
    await lintStdin();
    return;
  }
  if (args.length === 0) {
    printUsage();
    process.exit(2);
  }

  const files = await collectFiles(args);
  if (files.length === 0) {
    console.error('validate-mermaid: no .md/.mdx/.mmd files found in given paths');
    process.exit(process.exitCode || 1);
  }

  const results = [];
  for (const file of files) {
    const ext = extname(file).toLowerCase();
    if (RAW_EXTENSIONS.has(ext)) {
      results.push(await lintRawFile(file));
    } else {
      results.push(await lintMarkdownFile(file));
    }
  }

  const allErrors = results.flatMap((r) => r.errors);
  const totalBlocks = results.reduce((n, r) => n + r.blockCount, 0);
  const filesWithErrors = results.filter((r) => r.errors.length > 0).length;

  if (allErrors.length > 0) {
    for (const e of allErrors) console.error(e);
    console.error(
      `\nmermaid: ${allErrors.length} error(s) across ${filesWithErrors} file(s); ` +
        `scanned ${files.length} file(s), ${totalBlocks} diagram(s)`,
    );
    process.exit(1);
  }

  console.log(
    `mermaid: scanned ${files.length} file(s), validated ${totalBlocks} diagram(s) — all valid`,
  );
}

main().catch((err) => {
  console.error('validate-mermaid: unexpected error');
  console.error(err);
  process.exit(2);
});
