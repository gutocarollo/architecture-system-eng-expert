// Local MDX adapter of docs-autoagents v2; source stays unchanged.
/** Official-parser adapter, adapted from the Gateway Mermaid verification helper. */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const digest = (value) => createHash('sha256').update(value).digest('hex');

export function extractBlocks(text) {
  const lines = text.split(/(?<=\n)/);
  const blocks = [];
  let fence = null;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (fence) {
      const closing = line.match(/^ {0,3}(`{3,}|~{3,})[ \t]*\r?\n?$/);
      if (closing && closing[1][0] === fence.marker[0] && closing[1].length >= fence.marker.length) {
        if (fence.mermaid) blocks.push({ body: fence.body, line_start: fence.line_start, fence_index: blocks.length + 1 });
        fence = null;
      } else {
        fence.body += line;
      }
      continue;
    }
    const opening = line.match(/^ {0,3}(`{3,}|~{3,})([^\r\n]*)\r?\n?$/);
    if (opening) fence = { marker: opening[1], mermaid: opening[2].trim() === 'mermaid', body: '', line_start: index + 2 };
  }
  if (fence?.mermaid) throw new Error(`MERMAID_UNCLOSED: fence at line ${fence.line_start - 1}`);
  return blocks;
}

async function loadParser(modulePath) {
  const resolved = fs.realpathSync(modulePath);
  const packageRoot = path.resolve(path.dirname(resolved), '..');
  const metadata = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8'));
  if (metadata.name !== 'mermaid') throw new Error('MERMAID_MODULE: module must be a provisioned Mermaid dist module');
  const jsdomPath = path.resolve(packageRoot, '..', 'jsdom/lib/api.js');
  const { JSDOM } = await import(pathToFileURL(jsdomPath));
  const dom = new JSDOM('<!doctype html><html><body></body></html>');
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
  const { default: mermaid } = await import(pathToFileURL(resolved));
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
  await mermaid.parse('flowchart LR\nA --> B');
  let rejected = false;
  try { await mermaid.parse('flowchart LR\nA -?-> B'); } catch { rejected = true; }
  if (!rejected) throw new Error('MERMAID_SELF_TEST: parser accepted the negative control');
  return { mermaid, version: metadata.version, module_sha256: digest(fs.readFileSync(resolved)) };
}

async function main(args) {
  if (args.includes('--help') || args.length < 2) {
    console.log('Usage: node scripts/verify_mermaid.mjs <mermaid/dist/mermaid.esm.mjs> <document.md...> [--out receipt.json] [--mmdc executable --render-dir directory --puppeteer-config file]');
    if (!args.includes('--help')) process.exitCode = 2;
    return;
  }
  const [modulePath, ...rest] = args;
  let output = null;
  let rendererPath = null;
  let renderDirectory = null;
  let browserConfig = null;
  const targets = [];
  for (let index = 0; index < rest.length; index += 1) {
    if (rest[index] === '--out') {
      output = rest[++index];
      if (!output) throw new Error('MERMAID_ARGS: --out requires a path');
    } else if (['--mmdc', '--render-dir', '--puppeteer-config'].includes(rest[index])) {
      const option = rest[index];
      const value = rest[++index];
      if (!value) throw new Error(`MERMAID_ARGS: ${option} requires a path`);
      if (option === '--mmdc') rendererPath = fs.realpathSync(value);
      if (option === '--render-dir') renderDirectory = path.resolve(value);
      if (option === '--puppeteer-config') browserConfig = fs.realpathSync(value);
    } else if (rest[index].startsWith('--')) {
      throw new Error(`MERMAID_ARGS: unknown argument ${rest[index]}`);
    } else targets.push(rest[index]);
  }
  if (output && fs.existsSync(output)) throw new Error('MERMAID_OUTPUT_EXISTS: choose a new receipt path');
  if (Boolean(rendererPath) !== Boolean(renderDirectory)) throw new Error('MERMAID_ARGS: --mmdc and --render-dir must be provided together');
  if (browserConfig && !rendererPath) throw new Error('MERMAID_ARGS: browser configuration requires a renderer');
  let rendererVersion = null;
  if (rendererPath) {
    if (fs.existsSync(renderDirectory) && fs.readdirSync(renderDirectory).length) throw new Error('MERMAID_OUTPUT_EXISTS: render directory must be empty');
    fs.mkdirSync(renderDirectory, { recursive: true });
    rendererVersion = execFileSync(rendererPath, ['--version'], { encoding: 'utf8', timeout: 30000 }).trim();
  }
  const parser = await loadParser(modulePath);
  const receipt = { observed_at: new Date().toISOString(), parser_self_test: 'PASS', syntax_only: !rendererPath,
    module_sha256: parser.module_sha256, blocks_total: 0, blocks: [], errors: [] };
  for (const target of [...new Set(targets.map((item) => path.resolve(item)))].sort()) {
    try {
      const stat = fs.lstatSync(target);
      if (!stat.isFile() || stat.isSymbolicLink() || !target.endsWith('.md') && !target.endsWith('.mdx')) throw new Error('MERMAID_TARGET: supply regular Markdown files explicitly');
      const text = fs.readFileSync(target, 'utf8');
      for (const block of extractBlocks(text)) {
        receipt.blocks_total += 1;
        if (/%%\s*\{|^\s*click\s+|<\s*(?:script|iframe|img|object)\b/im.test(block.body)) throw new Error('MERMAID_UNSAFE: directives and active content are not supported');
        const sourceHash = digest(block.body);
        let phase = 'SYNTAX';
        try {
          await parser.mermaid.parse(block.body);
          let render = { status: 'NOT_RUN', tool: 'none', version: 'none', source_sha256: sourceHash };
          if (rendererPath) {
            phase = 'RENDER';
            const stem = `${digest(target).slice(0, 12)}-${block.fence_index}`;
            const inputPath = path.join(renderDirectory, `${stem}.mmd`);
            const artifactPath = path.join(renderDirectory, `${stem}.png`);
            fs.writeFileSync(inputPath, block.body, { flag: 'wx' });
            const rendererArgs = ['-i', inputPath, '-o', artifactPath, '-b', 'white'];
            if (browserConfig) rendererArgs.push('-p', browserConfig);
            execFileSync(rendererPath, rendererArgs, { encoding: 'utf8', timeout: 30000 });
            if (!fs.statSync(artifactPath).size) throw new Error('MERMAID_RENDER: renderer produced an empty artifact');
            render = { status: 'PASS', tool: 'mmdc', version: rendererVersion, source_sha256: sourceHash,
              artifact_path: artifactPath, artifact_sha256: digest(fs.readFileSync(artifactPath)) };
          }
          receipt.blocks.push({ path: target, document_sha256: digest(text), fence_index: block.fence_index,
            line_start: block.line_start, source_sha256: sourceHash,
            syntax: { status: 'PASS', tool: 'mermaid.parse', version: parser.version, source_sha256: sourceHash },
            render,
            semantic_review: 'NOT_RUN' });
        } catch (error) {
          receipt.errors.push({ code: `MERMAID_${phase}`, path: target, fence_index: block.fence_index, message: String(error.message) });
        }
      }
    } catch (error) {
      receipt.errors.push({ code: String(error.message).split(':')[0], path: target, message: String(error.message) });
    }
  }
  if (!receipt.blocks_total) receipt.errors.push({ code: 'MERMAID_EMPTY', message: 'No Mermaid block was validated.' });
  receipt.status = receipt.errors.length ? 'FAIL' : 'PASS';
  const serialized = JSON.stringify(receipt, null, 2) + '\n';
  if (output) fs.writeFileSync(output, serialized, { flag: 'wx' });
  process.stdout.write(serialized);
  if (receipt.errors.length) process.exitCode = 1;
}

if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  main(process.argv.slice(2)).catch((error) => {
    console.error(JSON.stringify({ status: 'FAIL', error: String(error.message) }));
    process.exitCode = 2;
  });
}
